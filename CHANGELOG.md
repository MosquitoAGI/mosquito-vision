# Changelog

All notable changes to this project are recorded here. Dates live in the
build log (docs/LOG.md); versions live here.

## [0.1.0]

- First extraction from `fruitfly-brain`: the encoder, the three sources and
  the packet format, with 31 tests.
- Packets carry a `spec_version`; readers refuse unknown versions.
