"""Downscale a screenshot to a small fixed-size grid."""
from PIL import Image
import numpy as np


def load_image(src):
    """Accept a path, bytes or a raw RGB array."""
    if isinstance(src, (str, bytes)):
        return Image.open(src)
    return Image.fromarray(np.asarray(src, dtype=np.uint8))


def downscale(img, size=(32, 32)):
    return img.convert("RGB").resize(size, Image.BILINEAR)


def to_array(img):
    return np.asarray(img, dtype=np.float64) / 255.0
