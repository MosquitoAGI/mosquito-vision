"""Calibration.

Two sessions, two facts:

1. A quiet session gives the noise floor — how much the channels move when
   nothing is happening. Anything below three times the floor is treated as
   nothing.
2. A sweep session gives the observed response to a known motion, which is used
   to scale the motion and growth channels into the units the bridge expects.

Both refusals matter more than the maths: a calibration built on 12 frames of
noise is worse than no calibration at all, so ``calibrate`` raises instead of
writing one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .packets import SensoryPacket

MIN_PACKETS = 30
EXPECTED_SWEEP_MOTION = 3.0  # units the bridge expects from a full-speed sweep
FLOOR_MULTIPLIER = 3.0


class CalibrationError(ValueError):
    """Raised when a session cannot support a calibration."""


@dataclass
class Calibration:
    noise_floor: float
    motion_gain: float
    growth_gain: float
    thresholds: dict[str, float] = field(default_factory=dict)
    spec_version: str = "1.0"
    source: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "spec_version": self.spec_version,
            "source": self.source,
            "noise_floor": round(self.noise_floor, 6),
            "motion_gain": round(self.motion_gain, 6),
            "growth_gain": round(self.growth_gain, 6),
            "thresholds": {k: round(v, 6) for k, v in sorted(self.thresholds.items())},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Calibration":
        if not isinstance(data, dict):
            raise CalibrationError("calibration must be a JSON object")
        if data.get("spec_version") != "1.0":
            raise CalibrationError("unsupported calibration spec_version")
        for key in ("noise_floor", "motion_gain", "growth_gain"):
            if key not in data:
                raise CalibrationError("calibration is missing %r" % key)
            if not isinstance(data[key], (int, float)):
                raise CalibrationError("%s must be a number" % key)
            if data[key] <= 0:
                raise CalibrationError("%s must be positive" % key)
        return cls(
            noise_floor=float(data["noise_floor"]),
            motion_gain=float(data["motion_gain"]),
            growth_gain=float(data["growth_gain"]),
            thresholds={str(k): float(v) for k, v in (data.get("thresholds") or {}).items()},
            source=str(data.get("source", "unknown")),
        )

    def save(self, path: str | Path) -> Path:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return out

    @classmethod
    def load(cls, path: str | Path) -> "Calibration":
        src = Path(path)
        if not src.exists():
            raise CalibrationError("calibration file not found: %s" % src)
        return cls.from_dict(json.loads(src.read_text(encoding="utf-8")))

    def apply(self, channels: dict[str, float]) -> dict[str, float]:
        """Scale and gate a reading with this calibration."""
        out = dict(channels)
        floor = max(self.thresholds.get("motion", 0.0), 0.0)
        for name in ("left_motion", "right_motion"):
            value = out.get(name, 0.0) / self.motion_gain
            out[name] = 0.0 if abs(value) < floor else value
        out["coverage_growth"] = out.get("coverage_growth", 0.0) / self.growth_gain
        return out


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise CalibrationError("no values")
    ordered = sorted(values)
    index = min(int(fraction * (len(ordered) - 1)), len(ordered) - 1)
    return ordered[index]


def noise_floor(quiet: list[SensoryPacket]) -> float:
    if len(quiet) < MIN_PACKETS:
        raise CalibrationError(
            "quiet session has %d packets, need at least %d" % (len(quiet), MIN_PACKETS)
        )
    motion = [abs(p.channels["left_motion"]) for p in quiet]
    motion += [abs(p.channels["right_motion"]) for p in quiet]
    growth = [abs(p.channels["coverage_growth"]) for p in quiet]
    floor = max(_percentile(motion, 0.95), _percentile(growth, 0.95) / 3.0)
    if floor <= 0.0:
        return 1e-3
    return float(floor)


def calibrate(quiet: list[SensoryPacket], sweep: list[SensoryPacket] | None = None) -> Calibration:
    """Estimate a calibration from a quiet session and an optional sweep."""
    floor = noise_floor(quiet)

    motion_gain = 1.0
    growth_gain = 1.0
    if sweep is not None:
        if len(sweep) < MIN_PACKETS:
            raise CalibrationError(
                "sweep session has %d packets, need at least %d" % (len(sweep), MIN_PACKETS)
            )
        peak = max(max(abs(p.channels["left_motion"]), abs(p.channels["right_motion"])) for p in sweep)
        if peak <= floor:
            raise CalibrationError(
                "sweep shows no motion above the noise floor (peak %.4f, floor %.4f)" % (peak, floor)
            )
        motion_gain = peak / EXPECTED_SWEEP_MOTION
        growth_peak = max(abs(p.channels["coverage_growth"]) for p in sweep)
        growth_gain = max(growth_peak, 1e-3) / 1.0

    thresholds = {
        "motion": round(floor * FLOOR_MULTIPLIER, 6),
        "growth": round(floor * FLOOR_MULTIPLIER / 3.0, 6),
    }
    return Calibration(
        noise_floor=floor,
        motion_gain=motion_gain,
        growth_gain=growth_gain,
        thresholds=thresholds,
        source=sweep[0].source if sweep else quiet[0].source,
    )
