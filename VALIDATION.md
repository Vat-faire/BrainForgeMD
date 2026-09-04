# Validation evidence

*Read this in [French / en français](VALIDATION.fr.md).*

BrainForgeMD is tested with synthetic, reproducible data. I do not use private documents or personal corpora as public test fixtures.

This document separates **capabilities that have been exercised end to end** from capabilities that are merely exposed by an installed optional backend. A listed extension is not automatically a claim that every variant of that format has been proven.

## Validation performed on 2026-09-04

### Cross-platform core pipeline

The deep-validation workflow runs the same end-to-end corpus on:

- Ubuntu, Windows, and macOS;
- Python 3.11, 3.12, and 3.13.

The synthetic corpus includes plain and Unicode text, Markdown and local links, source code, JSON/JSONL, YAML, CSV, HTML, Jupyter notebooks, EML email, SRT subtitles, SQLite, and nested ZIP content.

The tests verify more than process exit codes. They check:

- conversion completes with no failed or unsupported source in the corpus;
- `INDEX.md`, `REPORT.md`, `manifest.jsonl`, `chunks.jsonl`, `nodes.jsonl`, `edges.jsonl`, `errors.jsonl`, and incremental state are produced;
- document IDs, chunk IDs, source paths, SHA-256 provenance, parsers, and front matter are present;
- RAG chunks and structural GraphRAG nodes/edges are produced;
- a second unchanged run converts nothing and preserves manifest/chunk/graph files byte for byte;
- a generated output directory placed inside the source tree is not re-ingested.

### Clean package installation

A second 3 × 3 matrix builds the BrainForgeMD wheel, creates a fresh virtual environment, installs the wheel with no project source checkout dependency, and runs the installed CLI against a synthetic file.

This is exercised on Ubuntu, Windows, and macOS with Python 3.11, 3.12, and 3.13.

The smoke test verifies the installed version, command-line conversion, generated Markdown, manifest metadata, parser identity, and incremental state.

### Rich documents, OCR, audio, and video

A dedicated full-stack job installs BrainForgeMD with its optional backends plus the native media/OCR tools required by the test environment. It then generates actual synthetic file containers and sends them through the normal pipeline.

The following formats have been exercised end to end:

| Format | Synthetic fixture | What the test proves |
|---|---|---|
| PDF | ReportLab-generated PDF with text | Document backend converts it and preserves meaningful text |
| DOCX | Generated Word document with heading, paragraph, and table | Office document conversion succeeds |
| PPTX | Generated presentation with title and body text | Presentation conversion succeeds |
| XLSX | Generated workbook with structured cells | Spreadsheet conversion succeeds |
| PNG | Generated image containing text | Image/OCR path produces Markdown output |
| EPUB | Generated valid EPUB container with XHTML chapter | EPUB conversion succeeds |
| Parquet | Generated Arrow table | Native Parquet converter succeeds |
| WAV | Speech synthesized locally with `espeak-ng` | Audio input is accepted and converted by the installed rich backend stack |
| MP4 | Video generated locally with FFmpeg and synthetic speech audio | Video/media input is accepted and converted by the installed rich backend stack |

The rich-format test also performs an unchanged second run and verifies incremental byte stability for the manifest, chunks, nodes, and edges.

At validation time, `brainforgemd doctor` confirmed that Docling, MarkItDown, Outlook MSG support, Parquet support, FFmpeg, and OCR tooling were available in the rich test environment.

## Hostile archive tests

The validation suite attempts archive traversal with ZIP and TAR members such as:

- `../escape.txt`;
- Windows-style `..\\escape.txt`;
- absolute paths;
- drive-qualified Windows paths.

It also tests archive file-count and expanded-size limits. The tests require these inputs to be rejected and verify that no escape file is created outside the extraction directory.

## What is not proven yet

The current validation does **not** claim exhaustive coverage of every format or every real-world variant. In particular:

- legacy binary Office formats such as `.doc`, `.ppt`, and `.xls` are advertised by optional backends but do not yet have dedicated generated fixtures in this suite;
- OpenDocument formats (`.odt`, `.ods`, `.odp`) do not yet have dedicated fixtures;
- Outlook `.msg` support is installed and detected, but a synthetic valid MSG container is not yet generated and validated here;
- every image codec, audio codec, video container, and backend-listed extension is not individually fixture-tested;
- OCR accuracy, transcription accuracy, table reconstruction quality, and layout fidelity vary with source quality and backend behaviour; a successful conversion is not a guarantee of perfect semantic reconstruction;
- encrypted, password-protected, corrupted, unusually large, and adversarial rich documents need broader corpus testing;
- performance at very large corpus sizes has not yet been benchmarked here.

I prefer these limits to remain explicit rather than turn backend capability lists into unsupported promises.

## Reproducing the evidence

The tests are in [`tests/integration/`](tests/integration/) and the GitHub Actions workflow is [`.github/workflows/deep-validation.yml`](.github/workflows/deep-validation.yml).

The important files are:

- `tests/integration/test_core_deep.py` — core end-to-end, incremental, provenance, graph, and hostile-archive tests;
- `tests/integration/smoke_wheel.py` — clean wheel installation and installed-CLI smoke test;
- `tests/integration/test_rich_formats.py` — generated PDF/Office/image/EPUB/Parquet/audio/video validation.

A future release should not weaken these tests simply to obtain a green build. If a capability stops reproducing, the implementation or the public claim should be corrected.
