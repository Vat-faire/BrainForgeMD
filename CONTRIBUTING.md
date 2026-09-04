# Contributing to BrainForgeMD

*Read this in [French / en français](CONTRIBUTING.fr.md).*

Contributions are welcome.

BrainForgeMD is still an early pre-release project. Please read the current limits in [README.md](README.md) and [CHANGELOG.md](CHANGELOG.md) before assuming a missing behavior is already intended to be stable.

Issues and pull requests may be written in English or French.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
ruff check .
```

Before opening a pull request, make sure the tests and Ruff both pass.

## Adding a converter

A new converter should follow the same rules as the existing pipeline:

1. implement `Converter` from `brainforgemd.converters.base`;
2. use a stable `name` and explicit `extensions`;
3. never execute input content;
4. return normalized Markdown plus structured metadata;
5. add tests using synthetic fixtures whenever practical;
6. register the converter in `build_default_registry()`;
7. update format documentation when support changes.

Converters should fail clearly and specifically when they cannot parse a source. The pipeline decides whether the rest of the batch continues.

## Test data

Use synthetic, generated, or otherwise redistributable fixtures.

Do not commit:

- personal documents;
- credentials or API keys;
- customer/client data;
- private email;
- proprietary files without redistribution rights;
- screenshots or metadata containing private information.

## Output compatibility

The generated corpus is part of BrainForgeMD's public contract.

Changes to front matter, JSONL schemas, stable IDs, graph relationships, or output paths should remain backwards-compatible whenever practical. Breaking changes should be intentional, documented, and versioned.

## Security-sensitive changes

Changes involving archive extraction, path handling, SQLite access, file discovery, output paths, or optional parser integration should include refusal/error tests where appropriate.

Security vulnerabilities should not be disclosed in a public issue. See [SECURITY.md](SECURITY.md).

## AI-assisted contributions

BrainForgeMD openly uses AI-assisted development. Contributors are not required to avoid AI tools, but they remain responsible for what they submit.

AI-generated or AI-assisted code must meet the same requirements as manually written code: understandable changes, appropriate tests, valid licensing, no private data, and reviewable behavior.

See [AI_ASSISTANCE.md](AI_ASSISTANCE.md).

## Pull requests

Keep pull requests focused. Explain why the change is needed, add tests for new behavior, and document any change to supported formats or the output contract.
