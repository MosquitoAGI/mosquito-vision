"""Sweep every preset through the encoder and render the result.

    python examples/sweep_demo.py --out assets

Prints a table of what each preset produces (that table is the source of the
numbers quoted in docs/VALIDATION.md) and, with matplotlib installed, writes
`sweeps.png` and `sweep-demo.gif`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from fruitfly_vision.encoder import OpticalEncoder
from fruitfly_vision.sources import SyntheticConfig, SyntheticSource

PRESETS = ("quiet", "left", "right", "both", "loom")


def collect(sweep: str, frames: int = 120):
    source = SyntheticSource(SyntheticConfig(sweep=sweep, blob_speed=3.0, seed=0))
    encoder = OpticalEncoder()
    frames_out = []
    readings = []
    for _ in range(frames):
        frame = source.read()
        frames_out.append(frame)
        readings.append(encoder.update(frame))
    return frames_out, readings


def table(rows) -> str:
    head = "%-7s %9s %9s %9s %9s %9s %9s" % (
        "sweep", "mean L", "mean R", "max grw", "min grw", "mean cov", "mean cx",
    )
    lines = [head, "-" * len(head)]
    for sweep, readings in rows:
        left = np.mean([r["left_motion"] for r in readings])
        right = np.mean([r["right_motion"] for r in readings])
        growth = [r["coverage_growth"] for r in readings]
        cov = np.mean([r["coverage"] for r in readings])
        cx = np.mean([r["centroid_x"] for r in readings])
        lines.append(
            "%-7s %9.3f %9.3f %9.3f %9.3f %9.4f %9.3f"
            % (sweep, left, right, max(growth), min(growth), cov, cx)
        )
    return "\n".join(lines)


def render(rows, frames, out_dir: Path) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover
        print("skipping renders (matplotlib unavailable: %s)" % exc)
        return

    # 1. the preset comparison
    fig, axes = plt.subplots(len(rows), 1, sharex=True, figsize=(8, 1.3 * len(rows) + 1))
    for ax, (sweep, readings) in zip(axes, rows):
        t = np.arange(len(readings)) / 30.0
        ax.plot(t, [r["left_motion"] for r in readings], linewidth=1.0, label="left")
        ax.plot(t, [r["right_motion"] for r in readings], linewidth=1.0, label="right")
        ax.set_ylabel(sweep, fontsize=8)
        ax.grid(alpha=0.3, linewidth=0.5)
        ax.tick_params(labelsize=7)
    axes[0].legend(fontsize=7, ncol=2, loc="upper right")
    axes[-1].set_xlabel("seconds")
    fig.suptitle("fruitfly-vision — encoder response per sweep preset", fontsize=10)
    fig.tight_layout()
    fig.savefig(out_dir / "sweeps.png", dpi=120)
    plt.close(fig)

    # 2. the animation: the both-sweep, frame and channels together
    both = dict(rows)["both"]
    fig, (ax_frame, ax_trace) = plt.subplots(
        2, 1, figsize=(6, 4.2), gridspec_kw={"height_ratios": [3, 2]}
    )
    images = []

    def draw(index):
        ax_frame.clear()
        ax_trace.clear()
        ax_frame.imshow(frames[index], cmap="gray", vmin=0, vmax=255)
        half = frames[index].shape[1] // 2
        ax_frame.axvline(half, color="#4da3ff", linewidth=0.8)
        ax_frame.set_title("frame %d  (blue line: the split between the halves)" % index, fontsize=8)
        ax_frame.set_xticks([])
        ax_frame.set_yticks([])
        window = both[: index + 1]
        t = np.arange(len(window)) / 30.0
        ax_trace.plot(t, [r["left_motion"] for r in window], color="#4da3ff", label="left_motion")
        ax_trace.plot(t, [r["right_motion"] for r in window], color="#37d399", label="right_motion")
        ax_trace.set_xlim(0, len(both) / 30.0)
        ax_trace.set_ylim(-0.5, 8.0)
        ax_trace.grid(alpha=0.3, linewidth=0.5)
        ax_trace.legend(fontsize=7, ncol=2, loc="upper right")
        ax_trace.tick_params(labelsize=7)
        fig.tight_layout()

    for index in range(0, len(frames), 2):
        draw(index)
        fig.canvas.draw()
        images.append(
            np.asarray(fig.canvas.buffer_rgba()).copy()
        )
    plt.close(fig)

    from PIL import Image

    gif_frames = [Image.fromarray(image) for image in images]
    gif_frames[0].save(
        out_dir / "sweep-demo.gif",
        save_all=True,
        append_images=gif_frames[1:],
        duration=int(1000 / 15),
        loop=0,
    )
    print("wrote %s and %s" % (out_dir / "sweeps.png", out_dir / "sweep-demo.gif"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames", type=int, default=120)
    parser.add_argument("--out", default="assets")
    args = parser.parse_args()

    rows = []
    frames_cache = {}
    for sweep in PRESETS:
        frames, readings = collect(sweep, args.frames)
        rows.append((sweep, readings))
        frames_cache[sweep] = frames
    print(table(rows))
    render(rows, frames_cache["both"], Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
