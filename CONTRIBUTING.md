# Contributing

Same rules as the bridge: small scoped pull requests, tests for anything that
touches the encoder or the packet format, and an honest note in `docs/VALIDATION.md`
when a change alters the numbers.

```bash
pip install -e ".[dev,plot]"
pytest -q
ruff check .
python examples/sweep_demo.py --frames 60
```
