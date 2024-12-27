"""The encoder.

    frame -> grayscale -> resize -> blur -> {flow halves, coverage, growth}

Four channels, no state beyond the previous frame. The transform order matters
and is fixed; changing it changes the numbers in every recorded packet, which is
why it lives in one function rather than in a chain of flags.
"""

from __future__ import annotations

import numpy as np

from . import CHANNELS
from .config import Settings

try:  # pragma: no cover - installed in CI, optional at runtime
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


def to_gray(frame: np.ndarray) -> np.ndarray:
    if frame.ndim == 2:
        gray = frame
    elif frame.ndim == 3 and frame.shape[2] in (3, 4):
        gray = frame[:, :, :3].mean(axis=2)
    else:
        raise ValueError("unsupported frame shape: %r" % (frame.shape,))
    return np.asarray(gray, dtype=np.float32)


class OpticalEncoder:
    """Stateless per frame, except for the previous frame it keeps."""

    def __init__(self, settings: Settings | None = None):
        self.settings = (settings or Settings()).validate()
        self._prev: np.ndarray | None = None
        self._prev_coverage: float | None = None
        self.frames = 0

    def reset(self) -> None:
        self._prev = None
        self._prev_coverage = None
        self.frames = 0

    # ---------------------------------------------------------------- helpers
    def _prepare(self, frame: np.ndarray) -> np.ndarray:
        gray = to_gray(frame)
        target = (self.settings.width, self.settings.height)
        if gray.shape[::-1] != target:
            if cv2 is not None:
                gray = cv2.resize(gray, target, interpolation=cv2.INTER_AREA)
            else:
                rows = np.linspace(0, gray.shape[0] - 1, target[1]).astype(int)
                cols = np.linspace(0, gray.shape[1] - 1, target[0]).astype(int)
                gray = gray[np.ix_(rows, cols)]
        if self.settings.blur >= 3:
            k = self.settings.blur
            if cv2 is not None:
                gray = cv2.GaussianBlur(gray, (k, k), 0)
            else:
                pad = k // 2
                padded = np.pad(gray, pad, mode="edge")
                acc = np.zeros_like(gray)
                for dy in range(k):
                    for dx in range(k):
                        acc += padded[dy : dy + gray.shape[0], dx : dx + gray.shape[1]]
                gray = acc / float(k * k)
        return gray

    @staticmethod
    def _mask(gray: np.ndarray) -> np.ndarray | None:
        lo, hi = float(gray.min()), float(gray.max())
        if hi - lo < 8.0:
            return None
        return gray > (lo + 0.5 * (hi - lo))

    def _flow(self, prev: np.ndarray, cur: np.ndarray):
        if cv2 is not None:
            flow = cv2.calcOpticalFlowFarneback(prev, cur, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            return flow[..., 0], flow[..., 1]
        diff = cur - prev
        dx = np.zeros_like(prev)
        dy = np.zeros_like(prev)
        dx[:, 1:] = diff[:, 1:]
        dy[1:, :] = diff[1:, :]
        return dx, dy

    # ----------------------------------------------------------------- update
    def update(self, frame: np.ndarray) -> dict[str, float]:
        gray = self._prepare(frame)
        mask = self._mask(gray)
        coverage = 0.0 if mask is None else float(mask.mean())

        if self._prev is None:
            result = {name: 0.0 for name in CHANNELS}
            result["coverage"] = coverage
            self._prev = gray
            self._prev_coverage = coverage
            self.frames += 1
            return result

        u, v = self._flow(self._prev, gray)
        magnitude = np.sqrt(u * u + v * v)
        half = self.settings.width // 2
        left = float(magnitude[:, :half].mean()) * self.settings.motion_gain
        right = float(magnitude[:, half:].mean()) * self.settings.motion_gain
        growth = (coverage - float(self._prev_coverage or 0.0)) * self.settings.growth_gain

        self._prev = gray
        self._prev_coverage = coverage
        self.frames += 1

        clip = lambda x: float(np.clip(x, -8.0, 8.0))  # noqa: E731
        return {
            "left_motion": clip(left),
            "right_motion": clip(right),
            "coverage": coverage,
            "coverage_growth": clip(growth),
        }
