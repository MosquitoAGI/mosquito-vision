"""Frame sources.

Three of them, one interface: ``read()`` returns a frame or ``None`` when the
source is finished. The synthetic source is the important one — it is
deterministic, so tests can assert on encoder behaviour without a camera, a file
or a fixed recording.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SWEEPS = ("both", "left", "right", "quiet", "loom")

# Where the blob travels, per sweep, as a fraction of the frame width. The
# presets exist so a calibration session can mean one thing at a time: a blob
# that stays inside one half is what makes "right_motion > left_motion" a
# meaningful assertion.
SWEEP_RANGES = {
    "both": (0.08, 0.92),
    "left": (0.05, 0.45),
    "right": (0.55, 0.95),
    "quiet": (0.48, 0.52),
    "loom": (0.40, 0.60),
}


@dataclass
class SyntheticConfig:
    width: int = 320
    height: int = 240
    blob_speed: float = 3.0  # pixels per frame, in original frame units
    blob_radius: int = 22
    blob_drift: float = 0.0  # vertical pixels per frame
    loom_every: int = 0  # frames between approach cycles; 0 disables
    noise: float = 0.0  # gaussian sigma added to the frame
    sweep: str = "both"
    seed: int = 0

    def validate(self) -> "SyntheticConfig":
        if self.sweep not in SWEEPS:
            raise ValueError("sweep must be one of %s" % (", ".join(SWEEPS),))
        if self.blob_speed < 0:
            raise ValueError("blob_speed must be >= 0")
        if not 2 <= self.blob_radius <= min(self.width, self.height) // 2:
            raise ValueError("blob_radius does not fit the frame")
        if self.noise < 0:
            raise ValueError("noise must be >= 0")
        if self.loom_every < 0:
            raise ValueError("loom_every must be >= 0")
        return self


class SyntheticSource:
    """A bright blob on a dark field, with named knobs instead of surprises."""

    def __init__(self, cfg: SyntheticConfig | None = None):
        self.cfg = (cfg or SyntheticConfig()).validate()
        self.index = 0
        self._rng = np.random.default_rng(self.cfg.seed)
        self._direction = 1.0

    def read(self) -> np.ndarray:
        cfg = self.cfg
        lo, hi = SWEEP_RANGES[cfg.sweep]
        width = cfg.width
        height = cfg.height

        travel = (hi - lo) * width
        span = max(travel, 1.0)
        if cfg.sweep in ("quiet",):
            position = lo * width
        else:
            offset = (self.index * cfg.blob_speed) % (2 * span)
            offset = 2 * span - offset if offset > span else offset
            position = lo * width + offset

        cy = height / 2.0 if not cfg.blob_drift else (self.index * cfg.blob_drift) % height
        radius = float(cfg.blob_radius)
        if cfg.loom_every and cfg.sweep == "loom":
            phase = (self.index % cfg.loom_every) / float(cfg.loom_every)
            radius = cfg.blob_radius * (0.6 + 0.8 * phase)

        frame = np.zeros((height, width), dtype=np.float32)
        yy, xx = np.ogrid[:height, :width]
        mask = (xx - position) ** 2 + (yy - cy) ** 2 <= radius**2
        frame[mask] = 220.0
        if cfg.noise:
            frame += self._rng.normal(0.0, cfg.noise, size=frame.shape)
        self.index += 1
        return np.clip(frame, 0, 255).astype(np.uint8)

    def close(self) -> None:  # interface parity with the camera sources
        return None


class VideoSource:
    def __init__(self, path: str, width: int, height: int):
        import cv2

        self.cap = cv2.VideoCapture(int(path) if path.isdigit() else path)
        if not self.cap.isOpened():
            raise SystemExit("could not open video source: %s" % path)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    def read(self) -> np.ndarray | None:
        ok, frame = self.cap.read()
        return frame if ok else None

    def close(self) -> None:
        self.cap.release()


def make_source(kind: str, width: int = 320, height: int = 240, **kw):
    """Build a source by name. ``webcam`` and ``video`` need OpenCV."""
    if kind == "synthetic":
        cfg = SyntheticConfig(width=width, height=height, **kw)
        return SyntheticSource(cfg)
    if kind == "webcam":
        return VideoSource(str(kw.get("camera", 0)), width, height)
    if kind == "video":
        path = kw.get("video")
        if not path:
            raise SystemExit("--video is required when --source video")
        return VideoSource(str(path), width, height)
    raise SystemExit("unknown source: %r" % (kind,))
