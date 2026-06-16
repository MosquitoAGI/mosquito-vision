"""The canonical sensory field: raw and normalized planes."""
import numpy as np

FIELD_SIZE = (32, 32)
FIELD_SIZE_WIDE = (48, 48)


class SensoryField:
    """A small grid of intensities plus its normalized view.

    raw  - direct luminance values, clamped to [0, 1]
    norm - contrast-normalized plane, what receptors actually consume
    """

    def __init__(self, data, contrast=None):
        data = np.asarray(data, dtype=np.float64)
        if data.shape not in (FIELD_SIZE, FIELD_SIZE_WIDE):
            raise ValueError("expected %s or %s, got %s" % (FIELD_SIZE, FIELD_SIZE_WIDE, data.shape))
        self.raw = np.clip(data, 0.0, 1.0)
        self.contrast = contrast

    @property
    def data(self):
        return self.contrast if self.contrast is not None else self.raw

    def flat(self):
        return self.data.reshape(-1)

    def ascii(self, chars=" .:-=+*#%@"):
        lines = []
        lo, hi = float(self.raw.min()), float(self.raw.max())
        span = (hi - lo) or 1.0
        for row in self.raw:
            line = "".join(chars[min(int((v - lo) / span * (len(chars) - 1)), len(chars) - 1)] for v in row)
            lines.append(line)
        return "\n".join(lines)
