## What this changes

## How it was tested

- [ ] `pytest -q` passes locally
- [ ] `ruff check .` is clean
- [ ] `python examples/sweep_demo.py` runs

## Notes

Anything that changes the encoder's transform order, the channel set, or the
packet format needs a line in `docs/VALIDATION.md` explaining what the numbers
did.
