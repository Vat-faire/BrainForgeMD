# Format support

Format support has two layers.

## Core, dependency-light converters

| Family | Extensions | Notes |
|---|---|---|
| Plain text | txt, md, markdown, rst, log | Encoding detection and normalization |
| Source/config | py, js, ts, java, c/cpp, cs, go, rs, rb, php, swift, kt, sh, ps1, sql, Dockerfile-style and many config extensions | Wrapped in fenced code blocks with language hints |
| Structured | json, jsonl, yaml/yml, toml, ini/cfg/conf, xml | Pretty/safe textual representation |
| Tables | csv, tsv | Markdown table with width/row limits |
| Web | html, htm | Text/structure extraction without executing scripts |
| Notebook | ipynb | Markdown and code cells; outputs are preserved as text, never executed |
| Email | eml | Headers plus text/html body and attachment inventory |
| Subtitles | srt, vtt | Timestamped transcript |
| SQLite | sqlite, sqlite3, db | Read-only schema and bounded table rows |
| Archives | zip, tar, tgz, tar.gz, tar.bz2, tar.xz | Safe recursive extraction |

## Optional rich backends

`pip install "brainforgemd[docling]"` enables the formats supported by the installed Docling release. Current Docling releases include families such as PDF, Word, PowerPoint, Excel, OpenDocument, images/OCR, HTML/Markdown, multiple XML document dialects, audio/video, VTT, LaTeX, email, EPUB and other specialized formats.

`pip install "brainforgemd[markitdown]"` enables MarkItDown as a fallback backend for formats it recognizes, including common Office files, PDF, images/OCR, audio transcription, HTML, structured text, ZIP and EPUB.

Because backend capabilities evolve, `brainforgemd formats` and `brainforgemd doctor` are the authority for the installed machine.

## Binary formats that cannot become meaningful text

Some files are inherently binary or application-specific. BrainForgeMD does not fabricate a transcription. Unsupported inputs are reported in `errors.jsonl` with their path, MIME guess, hash and reason so a plugin can be added later without losing provenance.
