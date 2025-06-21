import numpy as np
from downscale import to_array, downscale
from PIL import Image


def test_downscale_is_deterministic():
    img = Image.new("RGB", (200, 120), (128, 64, 32))
    a = to_array(downscale(img))
    b = to_array(downscale(img))
    assert a.shape == (32, 32, 3)
    assert np.allclose(a, b)
