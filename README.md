# mosquito-vision

The visual system of Mosquito AI.

A screen is not handed to the nervous system as a full-resolution image.
It is downscaled to a small field (48x48, working down toward 32x32),
normalized, and encoded as receptor rates for sensory neurons.

    SCREENSHOT -> DOWNSCALE -> LUMINANCE -> CONTRAST -> FIELD -> RATES

## Quickstart

    pip install -r requirements.txt
    python3 -m tests.test_downscale

Part of the Mosquito AI project.
