"""Run every generated fixture through the real BrainForgeMD pipeline, one file at a time,
and report exactly which formats genuinely convert and whether expected content survives.

Usage: python audit/run_formats.py <fixture-dir> <work-dir>
"""

from __future__ import annotations

import json
import shutil
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from brainforgemd.pipeline import Pipeline, PipelineSettings

FIXTURES = Path(sys.argv[1])
WORK = Path(sys.argv[2])

# fixture name -> substring that must appear in the produced Markdown for the
# conversion to count as genuinely successful (not just "did not raise").
EXPECT = {
    "pdf_multipage.pdf": "MARKER_PAGE_3",
    "pdf_unicode.pdf": "MARKER_UNICODE_PDF",
    "pdf_table.pdf": "MARKER_TABLE_PDF",
    "pdf_image.pdf": "MARKER_PDF_WITH_IMAGE",
    "pdf_large.pdf": "MARKER_LARGE",
    "pdf_encrypted.pdf": "MARKER_ENCRYPTED_PDF",
    "docx_rich.docx": "MARKER_DOCX_BODY",
    "xlsx_rich.xlsx": "MARKER_XLSX",
    "pptx_rich.pptx": "MARKER_TITLE",
    "odt_doc.odt": "MARKER_ODT_BODY",
    "ods_sheet.ods": "MARKER_ODS",
    "odp_deck.odp": "MARKER_SLIDE",
    "legacy_book.xls": "MARKER_LEGACY_XLS",
    "book.epub": "MARKER_BODY",
    "data.parquet": "id",
    "img_text.png": "OCR MARKER",
    "img_text.jpg": "OCR MARKER",
    "img_text.tiff": "OCR MARKER",
    "img_text.webp": "OCR MARKER",
    "img_text.bmp": "OCR MARKER",
    "pdf_scanned.pdf": "SCANNED TEXT",
}

# fixtures where the *correct* behaviour is a reported failure, not a conversion
EXPECT_FAILURE = {"pdf_corrupt.pdf", "docx_corrupt.docx", "img_corrupt.png"}


def main() -> None:
    fixtures = sorted(p for p in FIXTURES.iterdir() if p.is_file() and not p.name.startswith("_"))
    WORK.mkdir(parents=True, exist_ok=True)
    rows = []
    for fx in fixtures:
        out = WORK / ("out_" + fx.name.replace(".", "_"))
        if out.exists():
            shutil.rmtree(out)
        t0 = time.time()
        status = parser = detail = ""
        md = ""
        try:
            stats = Pipeline().run(fx, out, PipelineSettings(chunk_chars=5000, overlap_chars=500))
            elapsed = time.time() - t0
            manifest = [
                json.loads(line)
                for line in (out / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line
            ]
            errors = [
                json.loads(line)
                for line in (out / "errors.jsonl").read_text(encoding="utf-8").splitlines()
                if line
            ]
            if manifest:
                parser = manifest[0]["parser"]
                md = (out / manifest[0]["output_path"]).read_text(encoding="utf-8")
                body = md.split("---\n\n", 1)[-1]
                # Backends escape Markdown metacharacters (Docling emits MARKER\_PAGE\_3),
                # so compare against an unescaped copy or every underscore looks missing.
                probe = body.replace("\\", "")
                marker = EXPECT.get(fx.name)
                if marker is None:
                    status = "CONVERTED"
                    detail = f"{len(body)} md chars"
                elif marker.lower() in probe.lower():
                    status = "CONVERTED+VERIFIED"
                    detail = f"marker {marker!r} present, {len(body)} md chars"
                else:
                    status = "CONVERTED-BUT-CONTENT-MISSING"
                    detail = f"marker {marker!r} ABSENT; body[:90]={body[:90]!r}"
            elif errors:
                status = "REPORTED-FAILURE"
                parser = "-"
                detail = f"{errors[0]['error_type']}: {errors[0]['message'][:110]}"
            else:
                status = "NO-OUTPUT"
                detail = str(stats)
        except Exception:
            elapsed = time.time() - t0
            status = "PIPELINE-CRASH"
            detail = traceback.format_exc(limit=1).strip().splitlines()[-1][:130]
        rows.append((fx.name, fx.stat().st_size, status, parser, round(elapsed, 2), detail))

    width = max(len(r[0]) for r in rows)
    lines = [f"{'fixture':<{width}}  {'bytes':>9}  {'status':<30} {'parser':<12} {'sec':>7}  detail"]
    for name, size, status, parser, sec, detail in rows:
        lines.append(f"{name:<{width}}  {size:>9}  {status:<30} {parser:<12} {sec:>7}  {detail}")

    ok = [r for r in rows if r[2] == "CONVERTED+VERIFIED"]
    weak = [r for r in rows if r[2] == "CONVERTED"]
    lost = [r for r in rows if r[2] == "CONVERTED-BUT-CONTENT-MISSING"]
    failed = [r for r in rows if r[2] == "REPORTED-FAILURE"]
    crash = [r for r in rows if r[2] == "PIPELINE-CRASH"]
    lines += [
        "",
        f"SUMMARY: verified={len(ok)} converted_unverified={len(weak)} "
        f"content_missing={len(lost)} reported_failure={len(failed)} pipeline_crash={len(crash)}",
    ]
    if crash:
        lines.append("PIPELINE CRASHES (failure isolation broken):")
        lines += [f"  {r[0]}: {r[5]}" for r in crash]

    report = "\n".join(lines) + "\n"
    (WORK / "FORMAT_RESULTS.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
