"""Rendering.

Terminal output that does not need a terminal, and one optional plot. Nothing
here is imported by the encoder, so a robot with no plotting stack can still
stream packets.
"""

from __future__ import annotations

import sys

from . import CHANNELS
from .packets import SensoryPacket

BLOCKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float]) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi - lo < 1e-9:
        return BLOCKS[0] * len(values)
    out = []
    for value in values:
        index = int((value - lo) / (hi - lo) * (len(BLOCKS) - 1))
        out.append(BLOCKS[index])
    return "".join(out)


def bar(value: float, span: float, width: int = 24) -> str:
    """A symmetric bar centred on zero, so sign is visible at a glance."""
    if span <= 0:
        return " " * width
    half = width // 2
    filled = min(int(abs(value) / span * half), half)
    if value >= 0:
        return " " * half + "#" * filled + " " * (half - filled)
    return " " * (half - filled) + "#" * filled + " " * half


def render_reading(channels: dict[str, float], span: float = 4.0) -> str:
    lines = []
    for name in CHANNELS:
        value = float(channels.get(name, 0.0))
        lines.append("%-16s %+7.3f  %s" % (name, value, bar(value, span)))
    return "\n".join(lines)


def render_trace(packets: list[SensoryPacket], channels: tuple[str, ...] = ("left_motion", "right_motion")):
    """A one-screen overview of a session: sparkline per channel."""
    lines = ["%s  %d packets" % (packets[0].source, len(packets))]
    for name in channels:
        values = [p.channels[name] for p in packets]
        lines.append("%-16s %+7.3f .. %+7.3f  %s" % (name, min(values), max(values), sparkline(values)))
    return "\n".join(lines)


def write_json(stats: dict, stream=None) -> None:
    import json

    print(json.dumps(stats, indent=2, sort_keys=True), file=stream or sys.stdout)


def plot_session(packets: list[SensoryPacket], path: str, channels: tuple[str, ...] | None = None) -> str:
    """Optional: needs matplotlib (``pip install -e ".[plot]"``)."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - depends on the environment
        raise SystemExit("plotting needs matplotlib: %s" % exc)

    names = channels or CHANNELS
    t = [p.t_ms / 1000.0 for p in packets]
    fig, axes = plt.subplots(len(names), 1, sharex=True, figsize=(9, 1.6 * len(names) + 1))
    if len(names) == 1:
        axes = [axes]
    for ax, name in zip(axes, names):
        ax.plot(t, [p.channels[name] for p in packets], linewidth=1.2)
        ax.set_ylabel(name, fontsize=8)
        ax.grid(alpha=0.3, linewidth=0.5)
        ax.tick_params(labelsize=8)
    axes[-1].set_xlabel("seconds")
    fig.suptitle("fruitfly-vision session — %s" % packets[0].source, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
