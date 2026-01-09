"""Collapse an RGB plane to a single intensity grid."""
import numpy as np

# Rec. 709 coefficients
LUMA = np.array([0.2126, 0.7152, 0.0722])


def luminance(rgb, gamma=1.0):
    """rgb: float array in [0, 1] with shape (h, w, 3).

    gamma < 1 brightens midtones; gamma > 1 darkens them. Pages with a
    washed-out background (white on white) get gamma 1.4 so structure
    survives downscaling.
    """
    arr = np.asarray(rgb, dtype=np.float64)
    if arr.max() > 1.0:
        arr = arr / 255.0
    if gamma != 1.0:
        arr = np.power(np.clip(arr, 0.0, 1.0), gamma)
    return arr @ LUMA
