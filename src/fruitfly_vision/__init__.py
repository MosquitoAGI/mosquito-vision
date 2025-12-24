"""FruitFlyVision — the sensory front end.

Frames in, six named channels out. No detection, no tracking, no labels: the
consumer of these packets decides what they mean.
"""

__version__ = "0.3.1"

CHANNELS: tuple[str, ...] = (
    "left_motion",
    "right_motion",
    "coverage",
    "coverage_growth",
    "centroid_x",
    "centroid_y",
)

__all__ = ["__version__", "CHANNELS"]
