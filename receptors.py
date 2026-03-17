"""Map field cells to input rates for sensory neurons."""
import numpy as np


def receptor_rates(field, repeats=8, scale=1.0):
    """Every cell becomes a small group of rate-coded input neurons.

    Blank fields are legal input (a white page, a dark room). The rate vector
    is clamped and finite; downstream neurons should see zeros, not NaNs.
    """
    data = field.flat() if hasattr(field, "flat") else np.asarray(field).reshape(-1)
    data = np.nan_to_num(data, nan=0.0, posinf=1.0, neginf=0.0)
    rates = np.clip(data, 0.0, 1.0) * scale
    return np.repeat(rates, repeats)


def pooled_rates(field, patch=2, repeats=4):
    """Average pool the field into patches before rate coding."""
    data = field.data if hasattr(field, "data") else np.asarray(field)
    h, w = data.shape[0] // patch * patch, data.shape[1] // patch * patch
    view = data[:h, :w].reshape(h // patch, patch, w // patch, patch)
    pooled = view.mean(axis=(1, 3))
    return np.repeat(pooled.reshape(-1), repeats)
