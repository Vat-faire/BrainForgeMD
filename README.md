# BrainForgeMD

BrainForgeMD turns mixed folders of documents, media, source code, data files, email, archives, and notes into a **provenance-preserving Markdown corpus** designed for RAG, GraphRAG, search, knowledge bases, and long-lived context systems.

It is not only a file-to-Markdown converter. It builds a reusable corpus with stable IDs, source hashes, chunk records, a structural graph, an index, and machine-readable manifests.

## What it produces

For an input tree such as:

```text
knowledge/
├── contracts/report.pdf
├── meetings/briefing.mp3
├── photos/whiteboard.jpg
├── data/customers.csv
├── code/parser.py
└── mail/thread.eml
```

BrainForgeMD creates:

```text
context-out/
├── documents/                 # Markdown mirroring the source tree
├── INDEX.md                   # human/agent-friendly corpus index
├── REPORT.md                  # conversion summary
├── manifest.jsonl             # one provenance record per source
├── chunks.jsonl               # stable RAG chunks
├── nodes.jsonl                # structural graph nodes
├── edges.jsonl                # structural graph edges
├── errors.jsonl               # non-fatal conversion failures
└── .brainforgemd/state.json # incremental conversion state
```

Every Markdown document begins with YAML-compatible front matter containing a stable source ID, SHA-256, MIME type, byte size, source-relative path, parser/backend, and extraction metadata.

## Highlights

- **Recursive batch conversion** with mirrored output paths and self-output exclusion.
- **Local-first**. No telemetry and no network calls by BrainForgeMD itself.
- **Deterministic built-in converters** for text, Markdown, code, JSON, JSONL, YAML, TOML, INI, CSV/TSV, XML, HTML, notebooks, email, subtitles, SQLite, and archives.
- **Rich document/media backend** through optional Docling for PDF, Word, PowerPoint, Excel, OpenDocument, images/OCR, audio/video transcription, EPUB, LaTeX, email and additional document formats supported by the installed Docling version.
- **Fallback backend** through optional MarkItDown when Docling cannot convert a supported input.
- **RAG-ready chunks** with stable chunk IDs, section paths, source IDs, approximate token counts, and overlap.
- **GraphRAG-ready structural graph** connecting documents, chunks, sequence relations, local file links, and external URLs. Semantic entity/relation extraction is intentionally left to the downstream GraphRAG layer.
- **Incremental runs** skip unchanged sources when source content and conversion settings match.
- **Safe archive extraction** with path traversal protection, depth/file/expanded-size limits, and recursion.
- **Failure isolation**. One bad file does not destroy the batch unless `--strict` is requested.
- **Repository-aware discovery** skips common VCS/build/cache trees and symlinks by default.
- **Plugin-friendly registry** so new converters can be added without rewriting the pipeline.

## Install

Install the zero-dependency core directly from GitHub, useful for text/code/data/email/notebook/SQLite/archive conversion:

```bash
pip install "brainforgemd @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Install the full local document/media stack:

```bash
pip install "brainforgemd[all] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

For development from source:

```bash
git clone https://github.com/Vat-faire/BrainForgeMD.git
cd BrainForgeMD
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[all,dev]"
```

Some OCR/transcription paths may require models or native media libraries used by the selected backend. Run `brainforgemd doctor` to see what is available on the current machine.

## Quick start

Convert one file:

```bash
brainforgemd convert report.pdf -o context-out
```

Convert an entire knowledge folder recursively:

```bash
brainforgemd convert ./knowledge -o ./context-out
```

Use smaller RAG chunks:

```bash
brainforgemd convert ./knowledge -o ./context-out --chunk-chars 3500 --overlap-chars 400
```

Disable incremental skipping and rebuild everything:

```bash
brainforgemd convert ./knowledge -o ./context-out --no-incremental
```

Inspect supported formats and currently available backends:

```bash
brainforgemd formats
brainforgemd doctor
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

One JSON object per source. This is the provenance ledger and the simplest ingestion point for systems that need document-level metadata.

### `chunks.jsonl`

One JSON object per chunk with:

- `chunk_id`
- `source_id`
- `source_path`
- `ordinal`
- `section_path`
- `text`
- `char_count`
- `approx_tokens`
- `sha256`

Chunk IDs remain stable as long as their source identity, section placement, ordinal, and text remain unchanged.

### `nodes.jsonl` and `edges.jsonl`

The graph is structural rather than speculative. It contains document/chunk/URL nodes and edges such as:

- `contains`
- `next`
- `links_to`
- `references_url`

This gives GraphRAG pipelines an auditable base graph without fabricating semantic entities.

## Built-in formats

The zero-dependency core package directly handles:

- Text: `.txt`, `.md`, `.markdown`, `.rst`, `.log`
- Source code/scripts: common Python, JS/TS, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, shell, PowerShell, SQL and infrastructure/config extensions
- Structured text: `.json`, `.jsonl`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.xml`
- Tabular: `.csv`, `.tsv`
- Web: `.html`, `.htm`
- Notebooks: `.ipynb`
- Email: `.eml`
- Subtitles: `.srt`, `.vtt`
- SQLite: `.sqlite`, `.sqlite3`, `.db`
- Archives: `.zip`, `.tar`, `.tgz`, `.tar.gz`, `.tar.bz2`, `.tar.xz`

With `brainforgemd[all]`, additional rich formats are routed to Docling and then MarkItDown as fallback when available. See [docs/FORMAT_SUPPORT.md](docs/FORMAT_SUPPORT.md).

## Security model

BrainForgeMD treats every input as untrusted. It does not execute source files, macros, notebook cells, embedded scripts, or archive contents. Archive extraction is bounded and path-safe. SQLite files are opened read-only. See [SECURITY.md](SECURITY.md) before processing hostile corpora.

## Philosophy

1. Preserve provenance before optimizing text.
2. Keep conversion deterministic whenever possible.
3. Never silently invent missing content.
4. Prefer partial, clearly marked extraction over opaque failure.
5. Keep semantic inference out of the conversion layer.
6. Make outputs useful to humans and machines at the same time.

## License

MIT. See [LICENSE](LICENSE).
