"""Local contrast normalization over the field."""
import numpy as np


def normalize(field, eps=1e-6):
    """Zero mean, unit variance, then squash back into [0, 1]."""
    field = np.asarray(field, dtype=np.float64)
    mean = float(field.mean())
    std = float(field.std())
    out = (field - mean) / (std + eps)
    return np.clip(out * 0.25 + 0.5, 0.0, 1.0)
