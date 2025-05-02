"""Command line.

    fruitfly-vision run --source synthetic --sweep right --frames 300 --export right.jsonl
    fruitfly-vision summary right.jsonl
    fruitfly-vision calibrate quiet.jsonl right.jsonl --out calibration.json
    fruitfly-vision ascii --source synthetic --frames 60 --every 10

Every subcommand is a thin wrapper: the work happens in the modules, so the CLI
can be exercised in tests without a subprocess.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .calibration import Calibration, CalibrationError, calibrate
from .config import Settings
from .encoder import OpticalEncoder
from .packets import PacketError, SensoryPacket, read_jsonl, write_jsonl
from .sources import SWEEPS, make_source
from .visualize import render_reading, render_trace

__all__ = ["build_parser", "run_cli", "main"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fruitfly-vision", description=__doc__)
    parser.add_argument("--version", action="version", version="fruitfly-vision %s" % __version__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="capture a session")
    run.add_argument("--source", default="synthetic", choices=["synthetic", "webcam", "video"])
    run.add_argument("--frames", type=int, default=240)
    run.add_argument("--sweep", default="both", choices=list(SWEEPS))
    run.add_argument("--camera", type=int, default=0)
    run.add_argument("--video")
    run.add_argument("--fps", type=float, default=30.0)
    run.add_argument("--speed", type=float, default=3.0, help="synthetic blob speed, px/frame")
    run.add_argument("--blob-radius", type=float, default=22.0, help="synthetic blob radius, px")
    run.add_argument("--blob-drift", type=float, default=0.0, help="synthetic vertical drift, px/frame")
    run.add_argument("--loom-every", type=int, default=0, help="synthetic approach cycle, frames")
    run.add_argument("--noise", type=float, default=0.0)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--export")
    run.add_argument("--calibration")
    run.add_argument("--every", type=int, default=0, help="print a reading every N frames")
    run.add_argument("--quiet", action="store_true")

    summary = sub.add_parser("summary", help="summarise a recorded session")
    summary.add_argument("session")

    cal = sub.add_parser("calibrate", help="build a calibration from sessions")
    cal.add_argument("quiet")
    cal.add_argument("sweep", nargs="?")
    cal.add_argument("--out", default="calibration.json")

    ascii_cmd = sub.add_parser("ascii", help="print readings as they are produced")
    ascii_cmd.add_argument("--source", default="synthetic", choices=["synthetic", "webcam", "video"])
    ascii_cmd.add_argument("--frames", type=int, default=60)
    ascii_cmd.add_argument("--every", type=int, default=10)
    ascii_cmd.add_argument("--sweep", default="both", choices=list(SWEEPS))

    return parser


def _capture(args) -> list:
    settings = Settings().validate()
    kwargs = {"sweep": getattr(args, "sweep", "both")}
    if args.source == "synthetic":
        kwargs.update(
            blob_speed=getattr(args, "speed", 3.0),
            blob_radius=int(getattr(args, "blob_radius", 22.0)),
            blob_drift=getattr(args, "blob_drift", 0.0),
            noise=getattr(args, "noise", 0.0),
            seed=getattr(args, "seed", 0),
            loom_every=int(getattr(args, "loom_every", 0)),
        )
    elif args.source == "video":
        kwargs["video"] = getattr(args, "video", None)
    else:
        kwargs["camera"] = getattr(args, "camera", 0)
    source = make_source(args.source, width=320, height=240, **kwargs)
    encoder = OpticalEncoder(settings)
    calibration = Calibration.load(args.calibration) if getattr(args, "calibration", None) else None
    packets = []
    period_ms = 1000.0 / max(getattr(args, "fps", 30.0) or 30.0, 1e-6)
    try:
        for index in range(args.frames):
            frame = source.read()
            if frame is None:
                break
            channels = encoder.update(frame)
            if calibration is not None:
                channels = calibration.apply(channels)
            if args.every and index % args.every == 0:
                print("frame %5d\n%s\n" % (index, render_reading(channels)))
            packets.append(
                SensoryPacket(
                    frame=index,
                    t_ms=index * period_ms,
                    source=args.source,
                    channels=channels,
                )
            )
    finally:
        source.close()
    return packets


def cmd_run(args) -> int:

    packets = _capture(args)
    if not packets:
        print("no frames were captured", file=sys.stderr)
        return 2
    if args.export:
        path = write_jsonl(args.export, packets)
        print("wrote %s (%d packets)" % (path, len(packets)))
    if not args.quiet:
        print(render_trace(packets))
        print()
        print(render_reading(packets[-1].channels))
    return 0


def cmd_summary(args) -> int:
    from .packets import format_summary, summarise

    try:
        packets = read_jsonl(args.session)
    except PacketError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    print(format_summary(Path(args.session).name, summarise(packets)))
    return 0


def cmd_calibrate(args) -> int:

    try:
        quiet = read_jsonl(args.quiet)
        sweep = read_jsonl(args.sweep) if args.sweep else None
        calibration = calibrate(quiet, sweep)
    except (PacketError, CalibrationError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    path = calibration.save(args.out)
    print("wrote %s" % path)
    for key, value in sorted(calibration.to_dict().items()):
        if key != "thresholds":
            print("  %-14s %s" % (key, value))
    for key, value in sorted(calibration.thresholds.items()):
        print("  threshold.%-6s %s" % (key, value))
    return 0


def cmd_ascii(args) -> int:
    packets = _capture(args)
    if not packets:
        return 2
    for index, packet in enumerate(packets):
        if index % max(args.every, 1) == 0:
            print("frame %4d  t=%.2fs" % (packet.frame, packet.t_ms / 1000.0))
            print(render_reading(packet.channels))
    return 0


def run_cli(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"run": cmd_run, "summary": cmd_summary, "calibrate": cmd_calibrate, "ascii": cmd_ascii}
    return handlers[args.command](args)


def main(argv: list[str] | None = None) -> int:
    return run_cli(argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
