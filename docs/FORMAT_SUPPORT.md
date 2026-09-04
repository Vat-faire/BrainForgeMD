# Format Support

*Read this in [French / en français](FORMAT_SUPPORT.fr.md).*

BrainForgeMD has two format-support layers: a lightweight deterministic core and optional rich-document/media backends.

## Core converters

The core aims to stay small and predictable. It directly handles formats where useful Markdown can be produced without a heavy external parser.

| Family | Extensions / examples | Behavior |
|---|---|---|
| Plain text | txt, md, markdown, rst, log | Decoded and normalized text |
| Source/config | py, js, ts, java, c/cpp, cs, go, rs, rb, php, swift, kt, sh, ps1, sql, Dockerfile-style and common config files | Source text in fenced code blocks with language hints |
| Structured data | json, jsonl, yaml/yml, toml, ini/cfg/conf, xml | Readable structured representation |
| Tables | csv, tsv | Bounded Markdown tables |
| Web | html, htm | Text and visible structure without executing scripts |
| Notebooks | ipynb | Markdown cells, code cells, and textual outputs; cells are never executed |
| Email | eml | Headers, body content, and attachment inventory |
| Subtitles | srt, vtt | Timestamped transcript content |
| SQLite | sqlite, sqlite3, db | Read-only schema and bounded row samples |
| Parquet | parquet | Structured tabular content when the optional dependency is available |
| Archives | zip, tar, tgz, tar.gz, tar.bz2, tar.xz | Safe bounded recursive extraction |

## Optional Docling backend

Install the Docling extra with:

```bash
pip install "brainforgemd[docling] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Depending on the installed Docling version and environment, this can extend support to families such as PDF, Word, PowerPoint, Excel, OpenDocument, images/OCR, HTML/Markdown, XML document dialects, VTT, LaTeX, email, EPUB, and other formats supported by that Docling release.

Two capabilities Docling advertises need extras that `[docling]` alone does not install:

- **OpenDocument** needs `odfdo`, which is included in `brainforgemd[all]` and
  `brainforgemd[odf]`. Without it `.odt`, `.ods` and `.odp` fail.
- **Audio and video transcription** needs a speech model, installed by
  `brainforgemd[asr]`. It is deliberately excluded from `[all]` because it adds several
  gigabytes. Without it every audio and video file is reported as a failure.

## Optional MarkItDown fallback

Install MarkItDown as an additional fallback with:

```bash
pip install "brainforgemd[markitdown] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Its capabilities depend on the installed release and optional dependencies. It can provide additional conversion paths for common Office documents, PDF, images/OCR, audio, HTML, structured text, ZIP, EPUB, and related formats.

## Full optional stack

```bash
pip install "brainforgemd[all] @ git+https://github.com/Vat-faire/BrainForgeMD.git"
```

Because optional backend capabilities evolve independently from BrainForgeMD, the project does not claim that every backend version supports exactly the same formats.

The practical authority on a target machine is:

```bash
brainforgemd formats
brainforgemd doctor
```

`brainforgemd formats` prefixes a converter with `!` when its backend is not installed
on the current machine, so a listed extension can be told apart from a usable one.

## Current validation level

The deterministic core is covered by the project's automated test suite and cross-platform CI matrix.

An independent audit converted generated fixtures for PDF (multi-page, Unicode, tables,
images, scanned/OCR, 300-page), DOCX, XLSX, PPTX, ODT, ODS, ODP, legacy `.xls`, EPUB,
Parquet, Outlook `.msg`, and JPEG/WEBP/BMP OCR, and verified that expected content
survived into the Markdown. See [VALIDATION.md](../VALIDATION.md).

Known gaps in the tested backend versions:

- **PNG and TIFF OCR return empty Markdown**, while the same rendered text OCRs
  correctly as JPEG, WEBP and BMP. These are reported as failures, not fabricated.
- **Legacy `.doc` and `.ppt`** route through LibreOffice, which must be on PATH.
- Audio and video need the `[asr]` extra as described above.

Support exposed by an installed optional backend should not be confused with a
guarantee of identical extraction quality for every file.

## Files that do not meaningfully convert to Markdown

Not every binary or application-specific format has a meaningful textual representation. BrainForgeMD does not fabricate one merely to claim support.

When no converter can produce useful content, the source is reported instead of silently discarded. The error record preserves enough information to identify the file and add a specialized converter later.

**Unsupported is preferable to invented content.**
