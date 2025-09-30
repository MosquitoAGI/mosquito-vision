<div align="center">

# FruitFlyVision

**The front end: camera frames in, sensory numbers out.**

![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-79cce8?style=flat-square)
![Tests](https://img.shields.io/badge/tests-42_passing-38c172?style=flat-square)
[![License: MIT](https://img.shields.io/badge/License-MIT-60dfb3?style=flat-square)](LICENSE)

</div>

This package is the eye of the fruitfly-brain bridge, extracted so it can be
calibrated on its own. It deliberately does not classify anything: no
detections, no tracking, no labels — small sensory numbers per frame, each with
a name and a unit.

Personal bench project. It runs on this desk before it runs anywhere else.

## What it does

- Three sources behind one interface: synthetic, webcam, video file.
- Motion in the left and right half of the field, and covered-area growth.
- Packets are JSONL, one line per frame, with a `spec_version` first.
- Strict reading: an unknown format is an error, not a skipped line.

## Quick start

Requires Python 3.11+.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python examples/sweep_demo.py
```

## Current limitations

- No absolute scale: the numbers are relative to the frame.
- No temporal filter: one reading per frame.
- No hardware validation; synthetic frames and recorded video only.

## License

MIT — see [LICENSE](LICENSE).
