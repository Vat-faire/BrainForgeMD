from __future__ import annotations

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

from brainforgemd.pipeline import Pipeline, PipelineSettings

pytestmark = pytest.mark.skipif(
    os.environ.get("BFMD_RICH_VALIDATION") != "1",
    reason="rich validation runs only in the dedicated integration job",
)


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _make_pdf(path: Path) -> None:
    reportlab_canvas = pytest.importorskip("reportlab.pdfgen.canvas")
    canvas = reportlab_canvas.Canvas(str(path))
    canvas.drawString(72, 720, "BrainForgeMD PDF integration fixture")
    canvas.drawString(72, 700, "This text must survive document conversion.")
    canvas.save()


def _make_docx(path: Path) -> None:
    Document = pytest.importorskip("docx").Document
    doc = Document()
    doc.add_heading("BrainForgeMD DOCX integration fixture", level=1)
    doc.add_paragraph("This paragraph must survive document conversion.")
    doc.add_table(rows=2, cols=2).cell(0, 0).text = "synthetic"
    doc.save(path)


def _make_pptx(path: Path) -> None:
    Presentation = pytest.importorskip("pptx").Presentation
    deck = Presentation()
    slide = deck.slides.add_slide(deck.slide_layouts[1])
    slide.shapes.title.text = "BrainForgeMD PPTX integration fixture"
    slide.placeholders[1].text = "This slide text must survive document conversion."
    deck.save(path)


def _make_xlsx(path: Path) -> None:
    Workbook = pytest.importorskip("openpyxl").Workbook
    book = Workbook()
    sheet = book.active
    sheet.title = "Synthetic"
    sheet.append(["name", "value"])
    sheet.append(["BrainForgeMD", 42])
    book.save(path)


def _make_png(path: Path) -> None:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    image = Image.new("RGB", (1200, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 100), "BrainForgeMD OCR integration fixture 2026", fill="black")
    image.save(path)


def _make_epub(path: Path) -> None:
    container = """<?xml version='1.0'?>
<container version='1.0' xmlns='urn:oasis:names:tc:opendocument:xmlns:container'>
  <rootfiles><rootfile full-path='OEBPS/content.opf' media-type='application/oebps-package+xml'/></rootfiles>
</container>"""
    package = """<?xml version='1.0' encoding='utf-8'?>
<package version='3.0' xmlns='http://www.idpf.org/2007/opf' unique-identifier='id'>
  <metadata xmlns:dc='http://purl.org/dc/elements/1.1/'><dc:identifier id='id'>urn:uuid:brainforgemd</dc:identifier><dc:title>BrainForgeMD EPUB fixture</dc:title><dc:language>en</dc:language></metadata>
  <manifest><item id='chapter' href='chapter.xhtml' media-type='application/xhtml+xml'/></manifest>
  <spine><itemref idref='chapter'/></spine>
</package>"""
    chapter = """<html xmlns='http://www.w3.org/1999/xhtml'><head><title>Fixture</title></head><body><h1>BrainForgeMD EPUB integration fixture</h1><p>This EPUB text must survive conversion.</p></body></html>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/content.opf", package)
        archive.writestr("OEBPS/chapter.xhtml", chapter)


def _make_parquet(path: Path) -> None:
    pa = pytest.importorskip("pyarrow")
    pq = pytest.importorskip("pyarrow.parquet")
    table = pa.table({"name": ["BrainForgeMD", "synthetic"], "value": [42, 7]})
    pq.write_table(table, path)


def _make_audio_and_video(root: Path) -> tuple[Path, Path]:
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    ffmpeg = shutil.which("ffmpeg")
    if not espeak or not ffmpeg:
        pytest.skip("espeak and ffmpeg are required for synthetic media validation")
    wav = root / "speech.wav"
    subprocess.run(
        [espeak, "-w", str(wav), "Brain Forge Markdown audio integration fixture"],
        check=True,
        capture_output=True,
    )
    video = root / "speech.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=640x360:d=4",
            "-i",
            str(wav),
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(video),
        ],
        check=True,
        capture_output=True,
    )
    return wav, video


def _build_rich_corpus(root: Path) -> list[str]:
    root.mkdir()
    _make_pdf(root / "fixture.pdf")
    _make_docx(root / "fixture.docx")
    _make_pptx(root / "fixture.pptx")
    _make_xlsx(root / "fixture.xlsx")
    _make_png(root / "fixture.png")
    _make_epub(root / "fixture.epub")
    _make_parquet(root / "fixture.parquet")
    wav, video = _make_audio_and_video(root)
    return [
        "fixture.pdf",
        "fixture.docx",
        "fixture.pptx",
        "fixture.xlsx",
        "fixture.png",
        "fixture.epub",
        "fixture.parquet",
        wav.name,
        video.name,
    ]


def test_rich_formats_through_real_pipeline(tmp_path: Path) -> None:
    source = tmp_path / "rich"
    out = tmp_path / "context-out"
    expected = _build_rich_corpus(source)

    stats = Pipeline().run(
        source,
        out,
        PipelineSettings(chunk_chars=1200, overlap_chars=100, max_file_mb=128),
    )
    manifest = _jsonl(out / "manifest.jsonl")
    errors = _jsonl(out / "errors.jsonl")
    by_source = {item["source_path"]: item for item in manifest}

    assert stats.unsupported == 0, errors
    assert stats.failed == 0, errors
    assert set(expected) <= set(by_source), (expected, by_source, errors)

    for source_name in expected:
        record = by_source[source_name]
        assert record["parser"] in {"docling", "markitdown", "parquet"}
        markdown = (out / record["output_path"]).read_text(encoding="utf-8")
        assert len(markdown) > 40
        assert record["chunk_count"] >= 1
        assert len(record["sha256"]) == 64

    text_joined = "\n".join(
        (out / by_source[name]["output_path"]).read_text(encoding="utf-8").lower()
        for name in ["fixture.pdf", "fixture.docx", "fixture.pptx", "fixture.xlsx", "fixture.epub"]
    )
    assert "brainforgemd" in text_joined


def test_rich_formats_are_incremental(tmp_path: Path) -> None:
    source = tmp_path / "rich"
    out = tmp_path / "context-out"
    expected = _build_rich_corpus(source)
    settings = PipelineSettings(chunk_chars=1200, overlap_chars=100, max_file_mb=128)

    first = Pipeline().run(source, out, settings)
    manifest_before = (out / "manifest.jsonl").read_bytes()
    second = Pipeline().run(source, out, settings)

    assert first.failed == 0
    assert second.failed == 0
    assert second.converted == 0
    assert second.skipped == len(expected)
    assert (out / "manifest.jsonl").read_bytes() == manifest_before
