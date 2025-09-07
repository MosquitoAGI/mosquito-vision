"""FruitFlyVision — the sensory front end.

Frames in, four named channels out. No detection, no tracking, no labels: the
consumer of these packets decides what they mean.
"""

__version__ = "0.2.0"

CHANNELS: tuple[str, ...] = (
    "left_motion",
    "right_motion",
    "coverage",
    "coverage_growth",
)

__all__ = ["__version__", "CHANNELS"]
