# Independent technical audit — BrainForgeMD

**Verdict: `READY_WITH_KNOWN_LIMITATIONS`**

This audit did not set out to confirm that BrainForgeMD works. It set out to break it.
The README, `VALIDATION.md` and the existing test suite were treated as claims to verify
independently, not as evidence. Every format listed below was proven by generating a
file, converting it through the ordinary pipeline, and requiring a marker string to
survive into the Markdown — "the converter did not raise" was never accepted as proof.

---

## 1. Environment

| Item | Value |
|---|---|
| Date | 2026-09-04 |
| OS | Windows 11 Pro, 10.0.26200 (`Windows-10-10.0.26200-SP0`) |
| CPU | Intel Core i9-9900K @ 3.60 GHz — 8 cores / 16 threads |
| RAM | 31.92 GB total, 17.38 GB free at start |
| Disk free | 277 GB |
| Python | 3.11.9 (CPython, 64-bit) |
| Long paths | `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem\LongPathsEnabled = 0` (MAX_PATH enforced) |
| Starting commit | `29f27d5` (`test: add reproducible deep validation suite`) |
| Final commit | `70afb71` |
| Branch | `audit/independent-validation` |

### Dependency versions used

| Package | Version | Package | Version |
|---|---|---|---|
| docling | 2.126.0 | markitdown | 0.1.7 |
| extract-msg | 0.56.1 | pyarrow | 23.0.1 |
| odfdo | 3.24.7 | rapidocr | 3.9.2 |
| torch | 2.14.0 | pytest | 8.4.2 |
| ruff | 0.16.6 | hypothesis | 6.167.1 |
| PyYAML | 6.0.3 | setuptools | 84.0.0 |
| ffmpeg | 8.1 (essentials build) | build | 1.6.0 |

Fixture generators: reportlab 5.0.1, python-docx 1.2.0, python-pptx 1.0.2,
openpyxl 3.1.5, pillow 12.3.0, odfpy 1.4.1, xlwt 1.3.0.

**Not available on this host:** tesseract, espeak-ng, LibreOffice, `openai-whisper`.
Each blocked test is named in §3 and §9 rather than silently omitted.

---

## 2. What was executed

| Activity | Result |
|---|---|
| Full pytest suite (final) | **101 passed, 1 skipped, 0 failed** |
| Ruff | Clean across `src/`, `tests/`, `audit/` |
| Coverage of `src/brainforgemd` | **85%** (1368 statements, 204 missed) |
| Wheel + sdist build | Succeeds; wheel is code-only, 29 entries |
| Clean-venv wheel install | Core installs with **zero third-party dependencies**, as documented |
| Project's own `smoke_wheel.py` | Passes |
| CLI (`--help`, `version`, `formats`, `doctor`, `convert` file, `convert` dir) | All pass from a neutral CWD in a clean venv |
| Generated format fixtures | 44 built; 43 through the batch harness, the `.msg` verified separately |
| Hostile / malformed input battery | ~70 cases |
| Archive traversal payloads | 21 shapes, ZIP + TAR |
| Property-based tests (Hypothesis) | 13 properties, ~2000 generated cases |
| Benchmarks | 100 / 1 000 / 10 000 files, plus 5 / 25 / 100 MB single files |
| Corpus integrity checker | Independent re-validation of the published output contract |

**Test counts by file (102 collected):**

| File | Tests |
|---|---|
| `tests/test_audit_regressions.py` (new) | 59 |
| `tests/test_audit_properties.py` (new) | 13 |
| `tests/integration/test_core_deep.py` | 9 |
| `tests/test_converters.py` | 6 |
| `tests/test_pipeline.py` | 5 |
| `tests/test_utils.py` | 3 |
| `tests/test_cli.py`, `tests/test_generic_text.py` | 2 each |
| `tests/test_chunking.py`, `tests/test_graph.py`, `tests/integration/test_rich_formats.py` | 1 each |

The single skip is `test_rich_formats.py`, which gates itself on `espeak` being present.

The pre-existing suite (29 tests) passed against the unmodified code. **It did not detect
any of the 24 defects below.** All 24 were found by testing the project against its own
public claims instead.

---

## 3. Formats actually verified

Every row was generated locally, converted through `Pipeline.run`, and checked for a
marker string in the resulting Markdown.

### Verified end to end (18)

| Format | Fixture | Backend |
|---|---|---|
| PDF multi-page | 5 pages, per-page markers | docling |
| PDF Unicode | TrueType-embedded accents | docling |
| PDF tables | ReportLab platypus table | docling |
| PDF with image | Raster image + text layer | docling |
| PDF scanned | **Image-only, no text layer** — genuine OCR | docling + RapidOCR |
| PDF large | 300 pages / 9 000 lines | docling |
| DOCX | Headings, bullets, numbering, table, image, header/footer, Unicode | docling |
| XLSX | 3 sheets, formula, empty cells, Unicode, 500x10 grid | docling |
| PPTX | 3 slides, speaker notes, table, image, Unicode | docling |
| ODT / ODS / ODP | OpenDocument text, sheet, presentation | docling + odfdo |
| Legacy `.xls` | **Real BIFF8 binary workbook** (xlwt), not a renamed XLSX | markitdown |
| EPUB | Hand-built EPUB 3 container | docling |
| Parquet | 300-row Arrow table, Unicode column | pyarrow (core) |
| Outlook `.msg` | **Hand-built CFB/OLE2 container** with MAPI property streams | extract-msg |
| Image OCR | JPEG, WEBP, BMP — rendered text recovered | docling + RapidOCR |

Core deterministic formats were verified in the same way: TXT, MD, RST, source code,
JSON, JSONL, YAML, TOML, INI, CSV, TSV, XML, SVG, HTML, IPYNB, EML, SRT, VTT, SQLite,
ZIP, TAR, TGZ, TAR.GZ, and nested archives.

### Correctly reported as failures (never fabricated)

Corrupt DOCX, corrupt PNG, corrupt PDF, encrypted PDF, nearly-empty PDF, text-free
image, low-contrast image, empty ZIP, 1-byte ZIP, truncated ZIP, unsupported binary.

### Proven NOT to work

| Format | Finding |
|---|---|
| All audio (`.wav`, `.mp3`, `.flac`, `.ogg`, `.m4a`) | `brainforgemd[all]` cannot transcribe: `whisper is not installed`. Requires the new `[asr]` extra. |
| All video (`.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`) | Same cause — the audio track is transcribed. |
| PNG and TIFF OCR | The **same rendered text** that OCRs correctly as JPEG, WEBP and BMP returns empty Markdown as PNG and TIFF. Reproducible; a backend defect, correctly surfaced as a failure. |

### Could not be verified (environment blockers)

| Format | Blocker |
|---|---|
| Legacy `.doc`, `.ppt` | Docling requires LibreOffice on PATH: `RuntimeError: LibreOffice is required to convert a .xls file to .xlsx`. Installing it needs administrator rights. No pure-Python writer for these formats exists either, so no fixture could be generated. |
| Audio/video transcription **quality** | Availability proven blocked; quality untestable without the multi-GB `[asr]` stack. |
| macOS / Linux | The audit ran on Windows 11 only. CI still covers all three for the core suite. |

---

## 4. Defects found

**24 HIGH/MEDIUM defects**, plus 5 LOW and 5 INFO items.

- **21 HIGH/MEDIUM fixed in code**, each with a regression test that fails on `29f27d5`
  and passes afterwards.
- **2 reported and deliberately left open** (H-8, M-15) — see §4.4.
- **1 (M-16) is an upstream backend defect** that BrainForgeMD already handles correctly
  by reporting the failure; only the documentation was corrected.
- Of the LOW items, 4 were fixed and 1 (L-5) left open. The INFO items are recorded, not
  fixed.

Every fix was verified to fail before and pass after.

### 4.1 HIGH

**H-1 — Script and CSS bodies were never stripped from HTML and email** *(fixed, `545790e`)*
The pattern was written `r"...</\\1>"`. Inside a raw string `\\1` is a literal backslash
and a one, not a backreference, so it never matched. Every `<script>` and `<style>` body
was emitted into the corpus as document prose — in the HTML converter and again in the
EML converter. For a RAG corpus this injects JavaScript source and CSS as retrievable
text, and it is a plausible prompt-injection carrier. `FORMAT_SUPPORT.md` claimed "text
and visible structure without executing scripts".

**H-2 — One malformed Markdown link aborted the entire corpus build** *(fixed, `350afa4`)*
`urlparse` raises `ValueError` on an unterminated IPv6 literal, e.g. `[x](http://[nothost/page)`.
The graph stage was unguarded, so a single document killed the run **after**
`manifest.jsonl` and `chunks.jsonl` had been written and **before** `nodes.jsonl`,
`edges.jsonl`, `INDEX.md`, `REPORT.md` and the state file. The result was a half-written
corpus and no incremental state, so the next run repeated the whole thing and failed
again. Directly contradicts the "failure isolation" design principle.

**H-3 — Colliding output paths destroyed one source and mis-attributed the other** *(fixed, `53616af`)*
`a.txt` maps to `a.txt.md` while `a.md` keeps its name. That is two-to-one for the pair
`X` / `X.md`. `README` and `README.md` in the same directory — an everyday situation, as
are `LICENSE`/`LICENSE.md` and `CHANGELOG`/`CHANGELOG.md` — both claimed
`documents/README.md`. One source's text was silently overwritten; `manifest.jsonl`
listed both with distinct `source_id`s pointing at the same file. On the next incremental
run the cached branch re-read that one file for **both** sources, so `chunks.jsonl`
attributed one document's text to the other document's provenance. For a tool whose
entire premise is provenance, this is the most serious defect found.

**H-4 — Any per-file write error aborted the whole run** *(fixed, `53616af`)*
The output path is always longer than the source path (it gains `documents/` and `.md`).
On Windows a source at 245 characters — comfortably inside MAX_PATH — produced an output
over 260 and raised `FileNotFoundError` out of the loop, abandoning the corpus and its
state. Nothing hostile is required. Stat, output-path selection, cached reads and writes
are now each isolated and reported in `errors.jsonl`.

**H-5 — Missing backends caused fabricated document content** *(fixed, `b445db6`)*
An uncompressed PDF is mostly printable ASCII. With no rich backend installed,
`GenericTextConverter` accepted it and wrote raw PDF object syntax (`/Type /Page`, xref
tables, stream operators) into the corpus as the document's prose — counted as
**converted**, `failed=0`, `parser: generic-text`. Design principles 3 and 4 say the
opposite must happen. Verified in a clean core-only venv.

**H-6 — Concurrent or interrupted runs corrupted the corpus** *(fixed, `bf6e533`)*
Measured with three concurrent processes over 400 files: 112 chunks referencing sources
absent from the manifest, **166 documents deleted** by one run as another run's orphans,
164 broken `INDEX.md` links. Two causes: the index files were opened with mode `"w"`
(truncate-first, so any interruption left an unparseable file), and nothing prevented two
writers. Index files are now written atomically and a second concurrent run is refused
with a message naming the lock holder. The same test now yields one complete, fully
consistent corpus and two clean refusals.

**H-7 — `brainforgemd[all]` never supported audio, video or OpenDocument** *(fixed, `36c25ff`)*
Every audio and video fixture failed with `whisper is not installed`; every ODF fixture
failed with `The 'odfdo' package is required`. `FORMAT_SUPPORT.md` listed both families
and `brainforgemd formats` advertised the extensions. `odfdo` is now in `all` (all three
ODF formats then convert with content intact) and a new `[asr]` extra covers media,
kept out of `all` because it pulls a multi-gigabyte model stack.

**H-8 — Incremental conversion is not faster than a full conversion** *(reported, not fixed — see §4.4)*

### 4.2 MEDIUM

**M-1 — UTF-32 was always decoded as UTF-16** *(fixed, `57624ae`)*
The UTF-32 BOM test sat *after* the UTF-16 test, and a UTF-32 LE BOM begins with the
UTF-16 LE BOM, so the UTF-32 branch was unreachable. BMP characters survived by accident
(the interleaved NULs are stripped later); non-BMP characters were corrupted and the
recorded encoding was wrong. Separately, a BOM-declared decode that raised aborted the
file entirely instead of falling through to the permissive ladder that ends at latin-1.

**M-2 — Blank documents produced a zero-length chunk** *(fixed, `350afa4`)*
`char_count: 0`, `approx_tokens: 1` — pure noise in a retrieval index.

**M-3 — XML/SVG entity expansion was unbounded** *(fixed, `545790e`)*
`xml.etree` hands documents to expat, which expands internal entities with no size cap.
A few hundred bytes of `.xml` or `.svg` can be inflated into gigabytes (billion laughs).
Confirmed with a bounded 50 KB expansion. Well-formedness is now checked on expat
directly with entity declarations and external references refused; external entities
(an XXE/SSRF surface) are refused too.

**M-4 — CSV quoted newlines glued words together** *(fixed, `545790e`)*
Rows were parsed from `text.splitlines()`, which strips the newline inside a quoted
multi-line cell, so `"line one\nline two"` became `line oneline two` — a token matching
neither word.

**M-5 — Chunk overlap could inflate a document ~500x** *(fixed, `350afa4`)*
`validate()` only required `overlap < target`. With `--chunk-chars 500 --overlap-chars 499`
each window advanced one character: a 200 KB document produced **199 501 chunks and
99.7 MB of chunk text**. Overlap is now capped at half the target.

**M-6 — Deleted and renamed sources left orphan documents** *(fixed, `53616af`)*
`documents/` kept Markdown for sources that no longer existed. The README tells consumers
to treat `documents/**/*.md` as the corpus, so deleted content was served as live. A full
directory scan now prunes; a single-file run never prunes.

**M-7 — `mime_type` was not reproducible across hosts** *(fixed, `57624ae`)*
`guess_mime` delegated to `mimetypes`, which reads the Windows registry and whose table
changes between Python releases. On this host `.md` → `application/octet-stream`,
`.ts` → `video/vnd.dlna.mpeg-tts`, `.zip` → `application/x-zip-compressed`. The same
corpus therefore produced different `manifest.jsonl` bytes on different machines,
defeating the point of a provenance ledger. Every declared format now has a pinned type.

**M-8 — Nested archives multiplied their budget** *(fixed, `53616af`)*
Limits applied per archive, so each nested archive received a fresh allowance. A **7 KB**
nested ZIP produced a **115 MB** corpus — amplification ×15 892 — while staying under the
nominal 2 GB limit. A single budget now spans the whole run.

**M-9 — Adjacent HTML cells and inline elements fused into meaningless tokens** *(fixed, `462295c`)*
Remaining tags were replaced with the empty string, so a table row emitted `AlphaBeta`
and adjacent spans emitted `LeftRight`. The `<title>` was also duplicated into the first
line of the body.

**M-10 — Control characters in a title produced invalid YAML front matter** *(fixed, `0d96f75`)*
Found by property testing the "YAML-compatible front matter" claim. `json.dumps` escapes
code points below 0x20 but leaves DEL, the C1 block, U+2028/U+2029 and a BOM raw, and
YAML rejects those even inside a quoted scalar. Reachable from an email subject, an HTML
`<title>` or a POSIX filename.

**M-11 — INDEX.md links broke on ordinary filenames** *(fixed, `eefb188`)*
Only `[` and `]` were escaped in the label; the destination was raw. `paren(1).txt.md`
resolved to `documents/paren(1` and `hash#3.txt.md` turned the rest into a fragment.

**M-12 — A source changed mid-read published a hash for text it never contained** *(fixed, `eefb188`)*
The ledger's central promise is that `sha256` describes the bytes the stored Markdown
came from. A source rewritten between hashing and conversion broke that silently.
Detected via size and mtime and reported as `SourceChangedDuringRead`.

**M-13 — An output directory above the source silently produced an empty corpus** *(fixed, `70afb71`)*
Only `input == output` was guarded. If the output directory *contained* the source —
`convert ./docs -o .`, a plausible mistake — every file was excluded by the "never
re-ingest the corpus" filter, and the run reported `discovered=0, converted=0`, wrote an
empty corpus and **exited 0**. The user got a success message and nothing else.

**M-14 — Case-clashing archive members silently mis-attributed content** *(fixed, `70afb71`)*
Archive member names are case-sensitive; Windows and macOS filesystems are not. A ZIP
written on Linux holding both `Report.txt` and `report.txt` extracted into a single file.
One member's content was discarded, and `manifest.jsonl` then listed **both** source paths
with the same hash and the same surviving text. Members resolving to the same file on the
host are now reported rather than silently merged.

**M-15 — Memory scales with total corpus size** *(reported, not fixed — see §4.4)*

**M-16 — PNG and TIFF OCR do not work** *(documented)*
Backend defect in the tested Docling/MarkItDown/RapidOCR versions, not in BrainForgeMD.
The failure is reported correctly and nothing is fabricated. `VALIDATION.md` previously
listed PNG OCR as proven; that row is now marked superseded.

### 4.3 LOW / INFO

| ID | Finding | Status |
|---|---|---|
| L-1 | A run where **every** source failed still exited 0, so CI could not detect it. | Fixed: added `--fail-on-error` (exit 3). Default exit code deliberately unchanged for compatibility. |
| L-2 | `brainforgemd formats` listed every rich extension even when its backend was absent, while the docs call it "the practical authority on a target machine". | Fixed: unavailable converters are marked `!`. |
| L-3 | An archive member whose name is illegal on the host raised a bare `OSError` from inside extraction instead of the documented `ValueError`. | Fixed. |
| L-4 | The sdist omitted every document except `README.md` and the whole `tests/integration/` tree that `VALIDATION.md` cites as its evidence. | Fixed via `MANIFEST.in`. |
| L-5 | A tampered `state.json` can inject an arbitrary `title` and `parser` into `manifest.jsonl` and `INDEX.md` (`output_path` is correctly recomputed and not trusted). | Open. Requires write access to the corpus directory, which is already a compromised position. |
| I-1 | Dispatch is purely extension-based. A PDF renamed `.txt` still yields binary garbage as "text". | By design; now mitigated for known binary families under their real extensions. |
| I-2 | A malformed `.json`/`.xml`/`.ipynb` silently degrades to `generic-text` with no `errors.jsonl` entry, so `failed=0` overstates health. | Open, documented. Content is preserved faithfully, so this is graceful degradation rather than fabrication. |
| I-3 | `stats.discovered` counts only top-level files, not archive members, so `discovered` can be lower than `converted`. | Open, cosmetic. |
| I-4 | `.zip` is listed in MarkItDown's extension set but archives are intercepted earlier, so it is dead configuration. | Open, cosmetic. |
| I-5 | SQLite caps rows per table (200) but not the number of tables. 4 000 tables → 373 KB of Markdown in 1.4 s. | Open; growth is linear and modest. |

### 4.4 Deliberately left open

Two findings are real, measured and reported, but I did not change the code. Both are
architectural decisions that belong to the maintainer, and a rushed change at the end of
an audit would risk the byte-stability guarantees the rest of this work verifies.

**H-8 — Incremental conversion is not faster than a full conversion.**
Measured speedup: **0.97x at 100 files, 0.84x at 1 000, 0.81x at 10 000** — that is,
consistently *slower*. `cProfile` over a 3 000-file corpus attributes **18.69 s of the
26.85 s warm run (70%) to `read_text`**: the cached branch reads every already-converted
document back from disk to re-chunk it and rebuild the graph, and still hashes every
source. The cold path writes that Markdown (buffered, cheap); the warm path reads all of
it back. The README promises that incremental conversion makes "repeated ingestion stable
and auditable", which it does — but users will reasonably expect a speed benefit and
there is none.
*Recommendation:* cache each document's chunk records and extracted links so an unchanged
file needs neither a re-read nor a re-chunk; or short-circuit the whole run when the
discovered file set and config hash exactly match the stored state.

**M-15 — Peak memory scales with total corpus size, not with the largest file.**
`documents` retains every document's full Markdown and `all_chunks` retains every chunk's
text for the entire run. Measured peak RSS: 29 MB at 100 files, 41 MB at 1 000, **147 MB
at 10 000** (15.9 MB of source), and **609 MB for a single 100 MB text file** — roughly 6x
the source. A 2 GB corpus would need well over 12 GB of RAM.
*Recommendation:* drop `markdown` from the retained document records once the links and
URLs have been extracted, which removes the dominant term; stream `chunks.jsonl` and sort
externally if ordering must be preserved.

---

## 5. Security assessment

### Verified sound — no defect found

| Area | Evidence |
|---|---|
| **Archive path traversal** | 21 payload shapes tested: `../`, `..\`, absolute POSIX, `C:\`, `C:relative`, UNC `\\server\share`, mid-path `a/b/../../../`, percent-encoded `%2e%2e`, and the Windows trailing-dot and trailing-space bypasses (`.. /`, `..  /`, `... /`, `..\u00a0/`). **Nothing escaped the extraction directory.** No sentinel file was ever created outside it. |
| **Archive symlinks** | Tar symlink and hardlink members (including `../../../../etc/passwd` and `C:/Windows/win.ini` targets) are skipped; no symlink is created on disk. ZIP symlinks are written as ordinary files containing the link text. |
| **Zip bombs** | A 1026:1 compression-ratio member is refused by the expanded-size budget. A forged (under-declared) `file_size` is caught by CRC validation (`BadZipFile`), so the write stays bounded by the declaration. |
| **Filesystem symlinks** | File symlinks, directory symlinks and broken symlinks are all skipped during discovery, so a directory symlink cannot cause duplicate ingestion or a traversal loop. |
| **SQLite** | Opened read-only; a write attempt raises `attempt to write a readonly database`. Table names are correctly quote-escaped — tables named `tab"le`, `ta'ble`, `ta--ble`, `ta;ble` and `日本語テーブル` all convert with no SQL error and no injection. The URI path is percent-encoded. |
| **No code execution** | Notebook cells are never executed (verified with a cell that would raise). No `subprocess`, `eval`, `exec`, `os.system` or shell invocation exists anywhere in `src/`. FFmpeg and OCR are reached only through backend libraries, never through a constructed command line. |
| **Output path containment** | `safe_output_path` rejects anything resolving outside `documents/`; property-tested over 200 generated names. |
| **Self-ingestion** | An output directory placed inside the source tree is never re-ingested, including with `--include-hidden` across three consecutive runs. |
| **Temporary files** | Archive extraction uses `tempfile.TemporaryDirectory`, cleaned in a `finally`. |

### Defects fixed during this audit

| Severity | Issue |
|---|---|
| MEDIUM | **XML entity expansion (billion laughs)** and external entity resolution were unbounded for `.xml`, `.xsd` and `.svg` — a memory-exhaustion and XXE surface on a tool that explicitly treats sources as untrusted. Now refused. |
| MEDIUM | **Nested-archive amplification ×15 892** — per-archive budgets multiplied with depth; a 7 KB input produced a 115 MB corpus. Now a single run-wide budget. |
| MEDIUM | **Script/CSS injection into the corpus** (H-1) — arguably the highest-impact security-adjacent finding, since it silently places attacker-controlled JavaScript into text destined for an LLM context window. |
| MEDIUM | **Corpus corruption from concurrent writers** (H-6) — including deletion of another run's documents. |
| MEDIUM | **Case-clashing archive members** silently merged into one file on Windows and macOS, mis-attributing content to a source path that never held it. Now reported. |
| LOW | Archive members with host-illegal names escaped as untyped `OSError`. |

### Residual risks

1. **Optional backends are a large, unaudited attack surface.** Docling and MarkItDown
   pull torch, ONNX runtime, pdfminer, olefile and more. This audit verified BrainForgeMD's
   own handling; it did not audit those parsers. The README's advice to process hostile
   files in an isolated environment remains correct and necessary.
2. **Extraction budgets are per run, not per system.** Ten separate runs still consume ten
   budgets. Disk and memory quotas belong to the operator.
3. **The lock is advisory and does not survive a crash.** An interrupted run leaves a lock
   file that must be deleted manually. The error message says exactly which file.
4. **`state.json` is trusted for `title` and `parser`** (L-5).
5. **Corpora inherit the sensitivity of their sources.** Unchanged and correctly documented.

---

## 6. Benchmarks

Windows 11, i9-9900K, Python 3.11, mixed synthetic corpus (text, Markdown, Python, JSON,
CSV, HTML, YAML). Reproduce with `python audit/benchmark.py <work-dir>`.

### Scaling

| Files | Source | Cold | Files/s | CPU | 2nd run | Speedup | Peak RSS | Corpus | Chunks |
|---|---|---|---|---|---|---|---|---|---|
| 100 | 0.16 MB | 0.74 s | 136 | 0.47 s | 0.76 s | **0.97x** | 29 MB | 0.6 MB | 129 |
| 1 000 | 1.59 MB | 5.77 s | 173 | 3.02 s | 6.87 s | **0.84x** | 41 MB | 6.0 MB | 1 286 |
| 10 000 | 15.87 MB | 58.98 s | 170 | 34.06 s | 72.38 s | **0.81x** | 147 MB | 59.9 MB | 12 857 |

Throughput is flat from 100 to 10 000 files — the pipeline scales linearly with no
degradation. Both listed defects (H-8, M-15) are visible in the speedup and RSS columns.

### Single large files

| Size | Time | MB/s | Chunks | Peak RSS | Corpus |
|---|---|---|---|---|---|
| 5 MB | 0.23 s | 22 | 1 200 | 155 MB | 12.1 MB |
| 25 MB | 1.08 s | 23 | 6 000 | 200 MB | 60.4 MB |
| 100 MB | 4.04 s | 25 | 23 986 | **609 MB** | 241.3 MB |

### Rich formats (single file, cold)

| Fixture | Time |
|---|---|
| 300-page PDF | **311 s** (≈1 s/page) |
| 5-page PDF | 7.9 s |
| Image OCR (each) | 3.5 – 7.3 s |
| XLSX / PPTX / DOCX / ODF | 0.11 – 0.42 s |
| Parquet | 0.04 s |

Rich-document conversion is two to three orders of magnitude slower than the core.
Anyone planning a PDF-heavy corpus should budget roughly one second per page.

### Output size

Plan for **2.4x** the source for large text files and up to **3.8x** for many small ones.
`chunks.jsonl` duplicates the document text (plus overlap) alongside `documents/`, and
front matter adds a fixed ~400 bytes per document.

---

## 7. Corpus integrity (RAG / GraphRAG)

`audit/check_corpus.py` re-validates the published contract independently of the code
that produced it. Run against a rich corpus (24 sources including nested archives,
Unicode and emoji names, colliding names, parentheses and `#` in filenames, a hostile
archive and an empty file):

```
manifest=23 chunks=37 nodes=63 edges=57 errors=2
verified front matter and chunk provenance for 23 documents
All corpus integrity checks passed.
```

Verified properties:

- every `source_id`, `source_path`, `output_path`, `chunk_id` and node id is unique;
- every chunk references a real manifest source — **no orphans**;
- chunk ordinals are dense and ordered per source, and agree with `chunk_count`;
- every edge endpoint exists — **no dangling edges**;
- document and chunk node sets exactly match the manifest and `chunks.jsonl`;
- edge types are confined to `contains`, `next`, `links_to`, `references_url` —
  **no speculative or inferred relation is emitted**;
- `documents/` on disk matches the manifest exactly, in both directions;
- front matter parses as YAML and agrees with the manifest on `source_id`, `sha256` and
  `source_path`;
- **every chunk's text is literally present in its own document's body** — nothing invented;
- `INDEX.md` links all resolve, and it lists every document.

Link and URL handling was checked specifically: relative Markdown links resolve across
directories (`../data/table.csv` from `notes/index.md`), percent-encoded links now
resolve, a link to a non-existent file correctly produces **no** edge, and bare URLs plus
`<...>` autolinks both become `url` nodes.

The same integrity checks are enforced continuously by the Hypothesis property suite over
randomly generated trees.

---

## 8. Documentation corrections made

| Document | Correction |
|---|---|
| `VALIDATION.md` / `.fr.md` | PNG, WAV and MP4 rows marked **superseded** — PNG OCR does not reproduce, and audio/video only ever worked in a CI job with extra native tooling, never via `pip install brainforgemd[all]`. Added the 18 verified formats, the formats proven not to work, the hostile-input results and the measured benchmarks. |
| `README.md` / `.fr.md` | Audio/video documented as requiring the separate `[asr]` extra. Added measured limits: incremental is not faster, memory tracks total corpus size, corpora are 2.4–3.8x their sources, one writer per output directory. |
| `docs/FORMAT_SUPPORT.md` / `.fr.md` | Documented the `odf` and `asr` extras, the PNG/TIFF OCR gap, the LibreOffice requirement for legacy `.doc`/`.ppt`, and that `formats` now marks missing backends. |

No claim was strengthened. Everything added is backed by a reproducible artifact in
`audit/` or a test in `tests/`.

---

## 9. Limitations of this audit

- **Single platform.** Windows 11 only. The fixes are platform-neutral and the CI matrix
  still covers Ubuntu and macOS, but the findings were not re-confirmed there.
- **Single Python version.** 3.11.9. The MIME determinism fix (M-7) specifically removes a
  cross-version hazard, but 3.12/3.13 were not re-run locally.
- **Backend versions are a moving target.** The PNG/TIFF OCR failure and the ODF and
  whisper requirements are properties of docling 2.126.0 / markitdown 0.1.7 and may change.
- **Legacy `.doc` and `.ppt` remain unproven.** No pure-Python writer exists and
  LibreOffice needs administrator rights to install.
- **The `.msg` fixture is minimal.** Subject, sender and body were verified; recipient
  parsing needs richer MAPI recipient storages than the hand-built container provides.
- **Ceiling of 10 000 files / 100 MB.** Larger corpora were not benchmarked; the memory
  finding (M-15) implies the practical limit is memory-bound.
- **Concurrency was tested with 3 processes**, not under sustained load.
- Fuzzing used Hypothesis with bounded example counts, not a long-running campaign.

---

## 10. Recommendations before v0.1.0

**Should block the tag:**

1. Nothing. Every HIGH defect except the two design findings in §4.4 is fixed and covered
   by a regression test, and no CRITICAL defect was found.

**Strongly recommended:**

2. Address **H-8**. Incremental conversion being slower than a full run undercuts a
   headline feature; §4.4 gives two concrete approaches.
3. Address **M-15**, or document the memory ceiling in the README's limits table more
   prominently than it is now.
4. Run this audit's suite on Ubuntu and macOS and on Python 3.12/3.13 before tagging. The
   new tests are platform-neutral and should be added to the CI matrix.
5. Re-test PNG/TIFF OCR against a newer Docling and remove the caveat if it is fixed
   upstream — PNG is the most common screenshot format.

**Worth doing:**

6. Record a warning in `errors.jsonl` when a specific converter fails and the run falls
   back to `generic-text` (I-2), so `failed=0` cannot overstate corpus health.
7. Count archive members in `stats.discovered` (I-3).
8. Decide whether `--fail-on-error` should become the default in a future major version.
9. Consider stale-lock detection so an interrupted run does not require manual cleanup.
10. Drop `.zip` from the MarkItDown extension set (I-4).

---

## 11. Verdict

### `READY_WITH_KNOWN_LIMITATIONS`

**Not `NOT_READY`.** The architecture is sound and the defects found were implementation
errors, not design failures. Where the design is tested hardest it holds up well: archive
traversal resisted 21 payload shapes including the Windows-specific bypasses; SQLite is
genuinely read-only and genuinely quote-safe; notebooks are genuinely never executed;
symlinks are genuinely skipped; the graph emits only factual relations and invents
nothing; chunk text is always literally present in its own document. Determinism is real
— two independent runs over the same sources produce byte-identical output, and a
metadata-only change is correctly ignored. The core installs with zero third-party
dependencies exactly as advertised. Nothing in the corpus is ever fabricated: across ~70
malformed, truncated, deceptive and adversarial inputs there was no crash and no invented
content, and the one place where fabrication *was* happening (H-5) is fixed.

**Not `READY_FOR_V0.1.0`.** Two measured properties contradict what a user would
reasonably infer from the documentation, and I chose to report rather than redesign them:
incremental conversion is *slower* than a full conversion (0.81–0.97x), and peak memory
tracks total corpus size rather than the largest file (609 MB for a 100 MB input). Neither
is a correctness bug, but a v0.1.0 that ships with the docs now corrected is honest, while
one that ships claiming an incremental speed benefit would not be. Beyond that, the audit
covered one OS and one Python version, PNG and TIFF OCR do not work at all with the
current backends, and legacy `.doc`/`.ppt` remain entirely unverified.

The gap between the two verdicts is narrow and consists of known, documented, measured
limitations rather than unknown risk. The project's most valuable property — that it
tells the truth about what it did and did not extract — survived this audit intact, and
the documentation now matches what the code actually does.

---

## 12. Reproducing this audit

```bash
git checkout audit/independent-validation
python -m venv .venv && .venv/Scripts/activate      # or source .venv/bin/activate
pip install -e ".[all,dev]"
pip install hypothesis pyyaml psutil                 # property tests and benchmark
pip install reportlab python-docx python-pptx openpyxl pillow odfpy xlwt  # fixtures

pytest -q                                            # 101 passed, 1 skipped
ruff check .

python audit/gen_fixtures.py build/fixtures          # 43 format fixtures
python audit/make_msg.py build/fixtures/mail.msg     # valid Outlook .msg
python audit/run_formats.py build/fixtures build/fmt # per-format verification
python audit/benchmark.py build/bench                # scaling + memory
python audit/check_corpus.py <a corpus directory>    # independent integrity check
```

| Artifact | Purpose |
|---|---|
| `tests/test_audit_regressions.py` | 59 tests, one or more per defect; all fail on `29f27d5` |
| `tests/test_audit_properties.py` | 13 Hypothesis properties over the output contract |
| `audit/gen_fixtures.py` | Generates 43 fixtures across every claimed format family |
| `audit/make_msg.py` | Builds a valid CFB/OLE2 Outlook `.msg` from scratch |
| `audit/run_formats.py` | Converts each fixture and requires marker content to survive |
| `audit/benchmark.py` | Reproducible scaling, memory and incremental benchmark |
| `audit/check_corpus.py` | Standalone corpus integrity checker, usable on any corpus |
