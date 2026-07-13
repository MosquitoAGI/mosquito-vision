"""One call: screenshot to receptor rates."""
from downscale import load_image, downscale, to_array
from luminance import luminance
from contrast import normalize
from sensory_field import SensoryField
from receptors import receptor_rates


def field_from_screenshot(src, size=(32, 32), gamma=1.0):
    img = downscale(load_image(src), size=size)
    plane = luminance(to_array(img), gamma=gamma)
    return SensoryField(plane, contrast=normalize(plane))


def rates_from_screenshot(src, repeats=8, **kwargs):
    field = field_from_screenshot(src, **kwargs)
    return receptor_rates(field, repeats=repeats)
