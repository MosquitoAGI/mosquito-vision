# MOSQUITO AI - VISION

**The low-bandwidth eye.**

`mosquito-vision` turns a screenshot into a small sensory field and hands it
to the nervous system as receptor rates. It is the first sense: no reading,
no DOM, no text extraction - just a coarse view of the world.

> It receives signals.
> Light. Motion. Heat. Chemical gradients.

## The pipeline

    SCREENSHOT
        |
    DOWNSCALE        32x32 grid (48x48 optional)
        |
    LUMINANCE         RGB -> intensity plane
        |
    CONTRAST          local normalization
        |
    SENSORY FIELD     canonical layout for the brain
        |
    RECEPTOR RATES    one group of input neurons per cell

## Why it is small on purpose

A 1920x1080 screenshot is not sensory input, it is a database. The field is
32x32 because the nervous system is supposed to live in a low-bandwidth view
of the world - enough to carry structure and motion, not enough to read.

The field feeds [`mosquito-brain`](https://github.com/MosquitoAGI/mosquito-brain)
input populations directly. The brain never sees the page.

## Layout

| file | role |
| --- | --- |
| `downscale.py` | load an image, reduce to the field grid |
| `luminance.py` | RGB -> intensity, optional gamma |
| `contrast.py` | local contrast normalization |
| `sensory_field.py` | canonical field container (raw + normalized) |
| `receptors.py` | field -> input rates, patch pooling |
| `pipeline.py` | one call: screenshot -> rates |
| `tools/ascii_field.py` | dump a field as ascii, for debugging |
| `config.yaml` | resolution, gamma, clamps |

## Quickstart

    git clone https://github.com/MosquitoAGI/mosquito-vision
    cd mosquito-vision
    pip install -r requirements.txt

    python3 tools/ascii_field.py path/to/screenshot.png
    python3 -c "from pipeline import field_from_screenshot; print(field_from_screenshot('shot.png')['field'].shape)"

## Status

v0.4.0

- [x] downscale with deterministic bilinear sampling
- [x] luminance + gamma option
- [x] local contrast normalization
- [x] 32x32 and 48x48 field presets
- [x] receptor rate encoding
- [ ] motion channel from frame pairs (lives in `mosquito-sensors`)
- [ ] color-opponent channel (experimental)

## Where it fits

| repo | role |
| --- | --- |
| [`mosquito-brain`](https://github.com/MosquitoAGI/mosquito-brain) | consumes receptor rates |
| [`mosquito-sensors`](https://github.com/MosquitoAGI/mosquito-sensors) | motion, heat, chemical channels |
| [`mosquito-browser`](https://github.com/MosquitoAGI/mosquito-browser) | produces the screenshots |
| [`mosquito-motor`](https://github.com/MosquitoAGI/mosquito-motor) | turns spikes into cursor movement |

## License

MIT - see `LICENSE`.
