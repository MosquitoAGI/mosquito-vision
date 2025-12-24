# Changelog

All notable changes to this project are recorded here. Dates live in the
build log (docs/LOG.md); versions live here.

## [0.3.1]

- `calibrate` refuses sessions shorter than 30 packets instead of writing a
  calibration built on noise.
- Documented the two refusals in `docs/CALIBRATION.md`.

## [0.3.0]

- Added the `centroid_x` / `centroid_y` channels to the encoder.
- Added the `--sweep` presets.

## [0.2.0]

- Added the CLI (`run`, `summary`, `replay`), JSONL export and the
  calibration maths.
- Added the ASCII channel view.
- The synthetic source became configurable (speed, radius, drift, loom, noise).

## [0.1.0]

- First extraction from `fruitfly-brain`: the encoder, the three sources and
  the packet format, with 31 tests.
- Packets carry a `spec_version`; readers refuse unknown versions.
