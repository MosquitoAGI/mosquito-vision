import numpy as np
from downscale import to_array, downscale
from luminance import luminance
from contrast import normalize
from sensory_field import SensoryField
from receptors import receptor_rates
from PIL import Image


def test_downscale_is_deterministic():
    img = Image.new("RGB", (200, 120), (128, 64, 32))
    a = to_array(downscale(img))
    b = to_array(downscale(img))
    assert a.shape == (32, 32, 3)
    assert np.allclose(a, b)


def test_field_bounds():
    rng = np.random.default_rng(0)
    plane = rng.uniform(0, 1, (32, 32))
    field = SensoryField(normalize(plane))
    assert field.data.min() >= 0.0
    assert field.data.max() <= 1.0
    assert field.flat().shape == (1024,)


def test_rates_are_finite_on_blank_field():
    blank = np.zeros((32, 32))
    rates = receptor_rates(SensoryField(blank))
    assert np.isfinite(rates).all()
    assert rates.sum() == 0.0
