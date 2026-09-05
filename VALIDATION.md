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
| PNG | Generated image containing text | **Superseded**: the independent audit could not reproduce this. PNG OCR returned empty Markdown; see below. |
| EPUB | Generated valid EPUB container with XHTML chapter | EPUB conversion succeeds |
| Parquet | Generated Arrow table | Native Parquet converter succeeds |
| WAV | Speech synthesized locally with `espeak-ng` | **Superseded**: this held only in a CI job with extra native tooling. `brainforgemd[all]` alone cannot transcribe audio; `[asr]` is required. |
| MP4 | Video generated locally with FFmpeg and synthetic speech audio | **Superseded**: same as WAV — the audio track needs the `[asr]` extra. |

The rich-format suite keeps document/OCR checks independent from media tooling, so a
missing speech synthesizer cannot skip PDF, Office, EPUB, Parquet, and image assertions.
It also performs an unchanged second document run and verifies incremental byte
stability for the manifest, chunks, nodes, and edges. Media is checked separately: a
working ASR backend must preserve synthesized speech, while `[all]` without `[asr]`
must report the missing transcription backend explicitly.

At validation time, `brainforgemd doctor` confirmed that Docling, MarkItDown, Outlook MSG support, Parquet support, FFmpeg, and OCR tooling were available in the rich test environment.

## Hostile archive tests

The validation suite attempts archive traversal with ZIP and TAR members such as:

- `../escape.txt`;
- Windows-style `..\\escape.txt`;
- absolute paths;
- drive-qualified Windows paths.

It also tests archive file-count and expanded-size limits. The tests require these inputs to be rejected and verify that no escape file is created outside the extraction directory.

## Independent audit, 2026-09-04

An independent audit re-tested every claim on this page against generated fixtures
rather than against the existing suite. Its findings, method and measurements are in
[INDEPENDENT_AUDIT_REPORT.md](INDEPENDENT_AUDIT_REPORT.md). The results below replace
the earlier summary where the two disagreed.

### Formats proven end to end, with content verified

Each of these was generated locally, converted through the ordinary pipeline, and
checked for a marker string that had to survive into the Markdown. "Converted without
raising" was not accepted as evidence.

PDF (multi-page, Unicode, tables, embedded image, image-only/scanned via OCR, 300-page),
DOCX (headings, lists, table, image, header/footer, Unicode), XLSX (multiple sheets,
formulas, empty cells, 500x10 grid), PPTX (multiple slides, speaker notes, table, image),
ODT, ODS, ODP, legacy binary `.xls` (a real BIFF8 workbook, via MarkItDown), EPUB,
Parquet, Outlook `.msg` (a hand-built CFB container), and OCR of JPEG, WEBP and BMP.

### Formats that do not work, and why

| Format | Status |
|---|---|
| Audio (`.wav`, `.mp3`, `.flac`, `.ogg`, `.m4a`) | Fails with `brainforgemd[all]`. Needs `brainforgemd[asr]`, which pulls a speech model. |
| Video (`.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`) | Same: the audio track is transcribed, so the same extra is required. |
| PNG and TIFF OCR | The same rendered text that OCRs correctly as JPEG, WEBP and BMP produced empty Markdown as PNG and TIFF with the Docling and MarkItDown versions tested. Reported as a failure, never fabricated. |
| Legacy `.doc` and `.ppt` | Not verified. Docling routes them through LibreOffice, which was not available. Not claimed. |
| Encrypted PDF | Reported as a failure, which is the intended behaviour. |

The earlier claim that WAV and MP4 were "exercised end to end" held only in a CI job
that installed extra native tooling; a plain `pip install brainforgemd[all]` never
supported them. OpenDocument was listed but the reader was missing until `odfdo` was
added to the `all` extra.

### Behaviour under hostile and malformed input

43 generated fixtures plus a battery of malformed, truncated, deceptive and
adversarial inputs produced **no pipeline crash and no fabricated content**. Corrupt
DOCX/PNG/PDF, an encrypted PDF, a text-free image, a low-contrast image and a
nearly-empty PDF are all reported in `errors.jsonl` rather than converted.

Archive traversal was retested with 21 payload shapes, including Windows trailing-dot
and trailing-space variants, drive-qualified and UNC paths, percent-encoded traversal,
and tar symlink and hardlink members. **No payload escaped the extraction directory.**

### Measured performance

Windows 11, i9-9900K, Python 3.11, mixed synthetic corpus:

| Files | Source | Cold | Throughput | Second (unchanged) run | Peak RSS | Corpus size |
|---|---|---|---|---|---|---|
| 100 | 0.16 MB | 0.74 s | 136 files/s | 0.76 s | 29 MB | 0.6 MB |
| 1 000 | 1.59 MB | 5.8 s | 173 files/s | 6.9 s | 41 MB | 6.0 MB |
| 10 000 | 15.9 MB | 59 s | 170 files/s | 72 s | 147 MB | 59.9 MB |

Three measured properties users should plan around:

- **A second unchanged run is not faster than the first.** It re-reads every converted
  document back from disk to rebuild the chunks and graph; profiling attributes about
  70% of its time to that. Incremental conversion currently buys stability, not speed.
- **Memory scales with total corpus size, not with the largest file**, because every
  document's Markdown and every chunk's text are held for the whole run. A 100 MB text
  file peaked at 609 MB RSS. Budget roughly 6x the source size.
- Output is roughly **2.4x** the source for large text files and up to **3.8x** for many
  small ones, because `chunks.jsonl` duplicates the text alongside `documents/`.

Rich-format conversion is far slower than the core: a 300-page PDF took 311 s
(about 1 s/page) and each OCR'd image took 3-7 s.

## What is still not proven

- legacy `.doc` and `.ppt`, which need LibreOffice on PATH;
- audio and video transcription quality, only its availability under `[asr]`;
- OCR accuracy in general, and PNG/TIFF OCR does not currently work at all;
- every image codec, audio codec, video container and backend-listed extension;
- password-protected and adversarial rich documents beyond the cases above;
- behaviour on corpora larger than 10 000 files or 100 MB single files;
- macOS and Linux for the audit findings specifically: the audit ran on Windows 11,
  while the CI matrix continues to cover all three platforms for the core suite.

I prefer these limits to remain explicit rather than turn backend capability lists into
unsupported promises.

## Reproducing the evidence

The tests are in [`tests/integration/`](tests/integration/) and the GitHub Actions workflow is [`.github/workflows/deep-validation.yml`](.github/workflows/deep-validation.yml).

The important files are:

- `tests/integration/test_core_deep.py` — core end-to-end, incremental, provenance, graph, and hostile-archive tests;
- `tests/integration/smoke_wheel.py` — clean wheel installation and installed-CLI smoke test;
- `tests/integration/test_rich_formats.py` — generated PDF/Office/image/EPUB/Parquet/audio/video validation;
- `tests/test_audit_regressions.py` — one regression test per defect found by the audit;
- `tests/test_audit_properties.py` — property-based tests for the output contract;
- `audit/gen_fixtures.py`, `audit/make_msg.py`, `audit/run_formats.py`, `audit/benchmark.py`
  and `audit/check_corpus.py` — the fixture generators, the per-format harness, the
  benchmark, and a standalone corpus integrity checker.

A future release should not weaken these tests simply to obtain a green build. If a capability stops reproducing, the implementation or the public claim should be corrected.
