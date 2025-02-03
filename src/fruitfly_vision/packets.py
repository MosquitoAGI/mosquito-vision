"""The packet format.

One JSON object per line. ``spec_version`` comes first so a reader can refuse a
format it does not know instead of misreading it, and the channel set is closed:
an unknown channel name is an error in both directions.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from . import CHANNELS

SPEC_VERSION = "1.0"


class PacketError(ValueError):
    """Raised for anything that does not match the format."""


@dataclass
class SensoryPacket:
    frame: int
    t_ms: float
    source: str
    channels: dict[str, float]
    spec_version: str = SPEC_VERSION

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        if self.spec_version != SPEC_VERSION:
            raise PacketError("unsupported spec_version: %r" % (self.spec_version,))
        if isinstance(self.frame, bool) or not isinstance(self.frame, int) or self.frame < 0:
            raise PacketError("frame must be a non-negative integer")
        if isinstance(self.t_ms, bool) or not isinstance(self.t_ms, (int, float)):
            raise PacketError("t_ms must be a number")
        if not math.isfinite(float(self.t_ms)):
            raise PacketError("t_ms must be finite")
        if not isinstance(self.channels, dict):
            raise PacketError("channels must be an object")
        missing = set(CHANNELS) - set(self.channels)
        if missing:
            raise PacketError("missing channels: %s" % ", ".join(sorted(missing)))
        extra = set(self.channels) - set(CHANNELS)
        if extra:
            raise PacketError("unknown channels: %s" % ", ".join(sorted(extra)))
        for name, value in self.channels.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise PacketError("channel %s must be a number" % name)
            if not math.isfinite(float(value)):
                raise PacketError("channel %s must be finite" % name)

    def to_dict(self) -> dict:
        return {
            "spec_version": self.spec_version,
            "frame": self.frame,
            "t_ms": round(float(self.t_ms), 3),
            "source": self.source,
            "channels": {name: round(float(self.channels[name]), 6) for name in CHANNELS},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SensoryPacket":
        if not isinstance(data, dict):
            raise PacketError("packet must be a JSON object")
        for key in ("spec_version", "frame", "t_ms", "channels"):
            if key not in data:
                raise PacketError("packet is missing %r" % key)
        return cls(
            frame=data["frame"],
            t_ms=data["t_ms"],
            source=str(data.get("source", "unknown")),
            channels=data["channels"],
            spec_version=data["spec_version"],
        )


def write_jsonl(path: str | Path, packets: list[SensoryPacket]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for packet in packets:
            fh.write(json.dumps(packet.to_dict(), separators=(",", ":")) + "\n")
    return out


def read_jsonl(path: str | Path) -> list[SensoryPacket]:
    src = Path(path)
    if not src.exists():
        raise PacketError("session file not found: %s" % src)
    packets: list[SensoryPacket] = []
    with src.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PacketError("%s line %d: invalid JSON (%s)" % (src.name, lineno, exc)) from exc
            try:
                packets.append(SensoryPacket.from_dict(data))
            except PacketError as exc:
                raise PacketError("%s line %d: %s" % (src.name, lineno, exc)) from exc
    if not packets:
        raise PacketError("%s contains no packets" % src.name)
    return packets


def summarise(packets: list[SensoryPacket]) -> dict[str, dict[str, float]]:
    if not packets:
        raise PacketError("no packets to summarise")
    out: dict[str, dict[str, float]] = {}
    for name in CHANNELS:
        values = [float(p.channels[name]) for p in packets]
        out[name] = {"min": min(values), "max": max(values), "mean": sum(values) / len(values)}
    out["_meta"] = {
        "packets": float(len(packets)),
        "duration_s": float(packets[-1].t_ms - packets[0].t_ms) / 1000.0,
        "frame_step": float(
            (packets[-1].t_ms - packets[0].t_ms) / max(len(packets) - 1, 1) / 1000.0
        ),
    }
    return out


def format_summary(path: str, stats: dict[str, dict[str, float]]) -> str:
    meta = stats["_meta"]
    lines = [
        "%s  %d packets  (%.1f s at %.0f fps)"
        % (path, int(meta["packets"]), meta["duration_s"], 1.0 / max(meta["frame_step"], 1e-9)),
    ]
    for name in CHANNELS:
        row = stats[name]
        lines.append(
            "%-16s min %+7.3f  max %+7.3f  mean %+7.3f" % (name, row["min"], row["max"], row["mean"])
        )
    return "\n".join(lines)
