"""The canonical sensory field.

32x32 is a deliberate limit: the nervous system works with a low-bandwidth
view of the world, not a full-resolution screenshot.
"""
import numpy as np

FIELD_SIZE = (32, 32)


class SensoryField:
    def __init__(self, data):
        data = np.asarray(data, dtype=np.float64)
        if data.shape != FIELD_SIZE:
            raise ValueError("expected %s, got %s" % (FIELD_SIZE, data.shape))
        self.data = np.clip(data, 0.0, 1.0)

    def flat(self):
        return self.data.reshape(-1)
