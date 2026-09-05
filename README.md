# BrainForgeMD

*Read this in [French / en français](README.fr.md).*

**BrainForgeMD turns mixed files into a traceable Markdown corpus for RAG, GraphRAG, search, knowledge bases, and long-lived AI context.**

> ## Status: early pre-release
>
> The repository currently declares version **0.1.0**, but there is **no tagged GitHub release and no PyPI publication yet**.
>
> The core pipeline has been verified in GitHub Actions on **Windows, macOS, and Linux with Python 3.11, 3.12, and 3.13**. The current suite covers the deterministic core, archive handling, corpus generation, graph packaging, and CLI behavior. Rich PDF/Office/OCR/audio/video paths rely on optional external backends and are **not yet exhaustively validated with a large real-world fixture corpus**.
>
> Treat the project as usable experimental software, not as a finished production ingestion platform.

## Author and maintenance

BrainForgeMD is an original project by **Vat-faire**.

- Author and maintainer: **Vat-faire** — https://github.com/Vat-faire
- License: [MIT](LICENSE) — © 2026 Vat-faire
- Product direction, priorities, approvals, and final decisions: **Vat-faire**
- Development: **AI-assisted** — see [AI_ASSISTANCE.md](AI_ASSISTANCE.md)

The project does not claim that every line was typed by hand. OpenAI ChatGPT was used as a development tool for architecture, implementation, testing, review, documentation, and repository work under Vat-faire's direction. No AI system is the owner or maintainer of BrainForgeMD, and use of an AI tool implies no affiliation with or endorsement by OpenAI.

## Why BrainForgeMD exists

Real knowledge folders are messy. They contain PDFs, Office documents, source code, email, spreadsheets, databases, archives, images, audio, video, notes, exports, and many other formats.

For AI context systems, converting a file to plain text is only part of the problem. A durable corpus should also preserve:

- where information came from;
- the exact source version;
- stable document and chunk identities;
- extraction metadata;
- chunk boundaries;
- explicit document relationships;
- enough structure to update the corpus without rebuilding its identity every time.

BrainForgeMD is intended to provide that ingestion and normalization layer before a vector database, search engine, graph database, RAG framework, or GraphRAG pipeline.

## What it produces

Given a source tree such as:

```text
knowledge/
├── contracts/report.pdf
├── meetings/briefing.mp3
├── photos/whiteboard.jpg
├── data/customers.csv
├── code/parser.py
└── mail/thread.eml
```

BrainForgeMD produces a corpus such as:

```text
context-out/
├── documents/                  # normalized Markdown mirroring the source tree
├── INDEX.md                    # human/agent-friendly corpus index
├── REPORT.md                   # conversion summary
├── manifest.jsonl              # source-level provenance ledger
├── chunks.jsonl                # stable RAG chunks
├── nodes.jsonl                 # structural graph nodes
├── edges.jsonl                 # structural graph edges
├── errors.jsonl                # isolated conversion failures
└── .brainforgemd/state.json    # incremental conversion state
```

Every generated Markdown document begins with YAML-compatible front matter containing provenance such as the source-relative path, stable IDs, SHA-256 hash, MIME type, file size, parser/backend, and extraction metadata.

## Design principles

BrainForgeMD is built around a few explicit rules:

1. **Preserve provenance before optimizing text.**
2. **Keep deterministic formats deterministic whenever possible.**
3. **Do not silently invent missing content.**
4. **Prefer a clearly reported unsupported file over fabricated extraction.**
5. **Keep semantic inference outside the conversion layer.**
6. **Treat source files as untrusted input.**
7. **Keep outputs useful to both humans and machines.**
8. **Make repeated ingestion stable and auditable.**

## Core capabilities

- Recursive batch conversion with mirrored output paths.
- Stable source, version, and chunk IDs.
- SHA-256 provenance.
- YAML-compatible Markdown front matter.
- `manifest.jsonl` source ledger.
- `chunks.jsonl` for RAG ingestion.
- `nodes.jsonl` and `edges.jsonl` for a factual structural graph.
- Incremental conversion state.
- Safe bounded archive extraction.
- Read-only SQLite inspection.
- Failure isolation for damaged or unsupported files.
- Common VCS/build/cache/environment directory exclusions.
- Symlink skipping by default.
- Single-writer locking of the output directory.
- Transactional publication and rollback of corpus artifacts.
- Extensible converter registry.
- Optional Docling and MarkItDown rich-document/media backends.

## Installation

### Core directly from GitHub

The core has no mandatory third-party runtime dependency.

```bash
pip install "brainforgemd @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

### Full optional document/media stack

```bash
pip install "brainforgemd[all] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

`[all]` covers PDF, Office, OpenDocument, EPUB, images/OCR, Outlook `.msg` and Parquet.

**Audio and video are not in `[all]`.** Transcription needs a speech model, which adds
several gigabytes, so it is a separate extra:

```bash
pip install "brainforgemd[all,asr] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Without it every `.wav`, `.mp3`, `.mp4` and similar file is reported as a failure rather
than converted.

### Development setup

```bash
git clone https://github.com/Vat-faire/BrainForgeMD.git
cd BrainForgeMD
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[all,dev]"
pytest
ruff check .
```

Optional OCR/transcription backends may require their own models or native libraries.

Check the target machine with:

```bash
brainforgemd doctor
brainforgemd formats
```

## Quick start

Convert one file:

```bash
brainforgemd convert report.pdf -o context-out
```

A single-file run may create or refresh a corpus containing only that file (or that
archive). To protect the global manifest, chunks, graph, and state from becoming a
partial view, BrainForgeMD refuses to apply a single-file run to an existing corpus
that contains other sources; rerun the containing source directory instead.

Convert an entire folder recursively:

```bash
brainforgemd convert ./knowledge -o ./context-out
```

Use smaller RAG chunks:

```bash
brainforgemd convert ./knowledge -o ./context-out --chunk-chars 3500 --overlap-chars 400
```

Force a complete rebuild:

```bash
brainforgemd convert ./knowledge -o ./context-out --no-incremental
```

## Corpus contract

### Markdown front matter

A converted document begins with fields similar to:

```yaml
---
brainforgemd: "0.1.0"
source_id: "src_..."
source_path: "contracts/report.pdf"
source_version_id: "ver_..."
source_name: "report.pdf"
source_extension: ".pdf"
mime_type: "application/pdf"
size_bytes: 482193
sha256: "..."
parser: "docling"
title: "report"
---
```

### `manifest.jsonl`

One JSON object per source. This is the source-level provenance ledger and a convenient document-level ingestion point.

### `chunks.jsonl`

One JSON object per retrieval chunk, including:

- `chunk_id`
- `source_id`
- `source_path`
- `ordinal`
- `section_path`
- `text`
- `char_count`
- `approx_tokens`
- `sha256`

Chunk IDs remain stable while their source identity, section placement, ordinal, and chunk text remain unchanged.

### `nodes.jsonl` and `edges.jsonl`

The graph is deliberately structural rather than speculative. It represents explicit relationships such as:

- `contains`
- `next`
- `links_to`
- `references_url`

Semantic entity extraction, embeddings, community detection, inferred relations, and generated summaries belong to downstream systems.

## Supported format families

The dependency-light core directly handles text, Markdown, common source/config files, JSON/JSONL, YAML, TOML, INI, CSV/TSV, XML, HTML, Jupyter notebooks, EML email, SRT/VTT subtitles, SQLite, and common ZIP/TAR archive families.

Optional backends extend support toward PDF, Office documents, OpenDocument, images/OCR, EPUB, LaTeX, and other formats supported by the installed backend versions. Audio and video transcription needs the separate `[asr]` extra.

`brainforgemd formats` marks any converter whose backend is missing on the current machine.

See [docs/FORMAT_SUPPORT.md](docs/FORMAT_SUPPORT.md).

## RAG and GraphRAG integration

A typical ingestion flow is:

1. read `manifest.jsonl` for source-level provenance and upserts;
2. embed or index `chunks.jsonl` for retrieval;
3. load `nodes.jsonl` and `edges.jsonl` when a graph is useful;
4. retain `documents/**/*.md` as the normalized human-readable corpus.

See [docs/RAG_OUTPUTS.md](docs/RAG_OUTPUTS.md).

## Security and privacy

BrainForgeMD treats every source as potentially malformed or hostile.

The core does not intentionally execute source code, shell commands, macros, notebook cells, or embedded scripts. SQLite is opened read-only. Archive extraction is bounded and rejects traversal attempts. Optional parsers bring their own dependency and security surfaces.

Generated corpora may contain all textual content and metadata present in the source files. They should be protected with the same care as the originals.

See [SECURITY.md](SECURITY.md) and [PRIVACY.md](PRIVACY.md).

## Known limits of the current version

| Area | Current limit |
|---|---|
| Release status | No tagged GitHub release and no PyPI package yet. |
| Rich media validation | Optional PDF/Office/OCR/audio/video backends are integrated but not yet exhaustively benchmarked on a broad real-world corpus. |
| Semantic graph | BrainForgeMD emits structural relationships only; it does not perform entity inference or semantic relation generation. |
| Token counts | `approx_tokens` is a heuristic, not a model-specific tokenizer result. |
| Incremental speed | Incremental conversion buys stability and auditability, not speed. A second unchanged run re-reads every converted document to rebuild the chunks and graph, so it is not faster than the first. |
| Memory | Peak memory scales with total corpus size, not with the largest file. Budget roughly 6x the source size. |
| Output size | A corpus is roughly 2.4x-3.8x the size of its sources, because `chunks.jsonl` duplicates the text alongside `documents/`. |
| Concurrency | One writer per output directory. A second concurrent run is refused rather than allowed to corrupt the first. |
| Audio and video | Not covered by `[all]`; they need the `[asr]` extra. |
| PNG and TIFF OCR | Does not currently work with the tested backends, while JPEG, WEBP and BMP do. |
| OCR/transcription | Availability and quality depend on optional backends, models, native libraries, hardware, and the source material. |
| Unsupported binaries | BrainForgeMD reports them rather than fabricating text. |
| Security | Hostile files should still be processed in an isolated environment, especially through optional parsers. |

These limits are intentional disclosures, not hidden claims of completeness.

## Public documentation

- [Project vision](PROJECT_VISION.md)
- [AI assistance disclosure](AI_ASSISTANCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Format support](docs/FORMAT_SUPPORT.md)
- [RAG / GraphRAG outputs](docs/RAG_OUTPUTS.md)
- [Security policy](SECURITY.md)
- [Privacy](PRIVACY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

English is the primary public documentation language. French translations are provided alongside the English documentation.

## Contributing

Contributions are welcome. Please keep changes focused, add tests for new behavior, and document output-contract or format-support changes.

See [CONTRIBUTING.md](CONTRIBUTING.md).

## AI-assisted development

BrainForgeMD is an original project by **Vat-faire**. The idea, product direction, requirements, priorities, approvals, and final decisions are attributed to Vat-faire.

Development has been **AI-assisted**. OpenAI ChatGPT has been used for architecture, implementation, tests, audits, documentation, and GitHub repository work under Vat-faire's direction.

This is not a claim that every line was manually typed. It is also not a claim that an AI system owns or maintains the project. Final project responsibility and maintenance rest with **Vat-faire**.

See [AI_ASSISTANCE.md](AI_ASSISTANCE.md) for the full disclosure.

## License

MIT. See [LICENSE](LICENSE).

Copyright (c) 2026 **Vat-faire**.
