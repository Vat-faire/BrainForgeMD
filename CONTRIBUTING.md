# Contributing

Contributions are welcome.

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
mypy src/brainforgemd
```

## Adding a converter

1. Implement `Converter` from `brainforgemd.converters.base`.
2. Give it a stable `name` and explicit `extensions`.
3. Never execute input content.
4. Return Markdown plus structured metadata.
5. Add unit tests with synthetic fixtures.
6. Register it in `build_default_registry()`.

Converters should fail loudly and specifically when content cannot be parsed. The pipeline decides whether a batch continues.

## Pull requests

Keep changes focused, add tests, and document new formats or output-contract changes. Output schema changes should be backwards-compatible or clearly versioned.
