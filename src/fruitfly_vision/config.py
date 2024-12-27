"""Encoder settings.

Deliberately flat: six knobs, all of them in one dataclass, so a session can be
reproduced from a printed line.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


class SettingsError(ValueError):
    """Raised for a setting outside its allowed range."""


@dataclass
class Settings:
    width: int = 160
    height: int = 120
    blur: int = 3
    motion_gain: float = 6.0
    growth_gain: float = 12.0
    centroid_min_pixels: int = 12

    def validate(self) -> "Settings":
        if self.width < 16 or self.height < 16:
            raise SettingsError("frame must be at least 16x16")
        if self.blur < 0 or (self.blur and self.blur % 2 == 0):
            raise SettingsError("blur must be 0 or an odd number")
        if self.motion_gain <= 0 or self.growth_gain <= 0:
            raise SettingsError("gains must be positive")
        if self.centroid_min_pixels < 1:
            raise SettingsError("centroid_min_pixels must be >= 1")
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "Settings":
        data = data or {}
        allowed = set(cls.__dataclass_fields__)
        extra = set(data) - allowed
        if extra:
            raise SettingsError("unknown settings: %s" % ", ".join(sorted(extra)))
        return cls(**data).validate()

    def describe(self) -> str:
        return " ".join("%s=%s" % item for item in sorted(self.to_dict().items()))
