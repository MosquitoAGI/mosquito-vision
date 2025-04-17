"""Map field cells to input rates for sensory neurons."""
import numpy as np


def receptor_rates(field, repeats=8, scale=1.0):
    """Every cell becomes a small group of rate-coded input neurons."""
    data = field.flat() if hasattr(field, "flat") else np.asarray(field).reshape(-1)
    rates = np.clip(data, 0.0, 1.0) * scale
    return np.repeat(rates, repeats)
