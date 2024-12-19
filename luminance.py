"""Collapse an RGB plane to a single intensity grid."""
import numpy as np

# Rec. 709 coefficients
LUMA = np.array([0.2126, 0.7152, 0.0722])


def luminance(rgb):
    """rgb: float array in [0, 1] with shape (h, w, 3)."""
    arr = np.asarray(rgb, dtype=np.float64)
    if arr.max() > 1.0:
        arr = arr / 255.0
    return arr @ LUMA
