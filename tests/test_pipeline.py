import json
import zipfile
from pathlib import Path

from brainforgemd.pipeline import Pipeline, PipelineSettings


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_pipeline_builds_complete_corpus_and_incremental_state(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("# Hello\n\nThis is knowledge.\n", encoding="utf-8")
    (source / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    out = tmp_path / "out"
    settings = PipelineSettings(chunk_chars=1000, overlap_chars=100)
    stats1 = Pipeline().run(source, out, settings)
    assert stats1.converted == 2
    assert (out / "INDEX.md").exists()
    assert len(read_jsonl(out / "manifest.jsonl")) == 2
    assert len(read_jsonl(out / "chunks.jsonl")) >= 2
    stats2 = Pipeline().run(source, out, settings)
    assert stats2.skipped == 2
    assert stats2.converted == 0


def test_archive_is_extracted_safely_and_converted(tmp_path: Path) -> None:
    source = tmp_path / "archive.zip"
    with zipfile.ZipFile(source, "w") as zf:
        zf.writestr("nested/readme.txt", "hello archive")
    out = tmp_path / "out"
    stats = Pipeline().run(source, out, PipelineSettings(chunk_chars=1000, overlap_chars=100))
    assert stats.converted == 1, (out / "errors.jsonl").read_text(encoding="utf-8")
    manifest = read_jsonl(out / "manifest.jsonl")
    assert manifest[0]["source_path"].endswith("archive.zip!/nested/readme.txt")


def test_archive_path_traversal_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "bad.zip"
    with zipfile.ZipFile(source, "w") as zf:
        zf.writestr("../escape.txt", "bad")
    out = tmp_path / "out"
    stats = Pipeline().run(source, out, PipelineSettings())
    assert stats.failed == 1
    errors = read_jsonl(out / "errors.jsonl")
    assert "traversal" in errors[0]["message"].lower()


def test_output_inside_source_is_not_reingested(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("hello", encoding="utf-8")
    out = source / "context-out"
    first = Pipeline().run(source, out, PipelineSettings(chunk_chars=1000, overlap_chars=100))
    second = Pipeline().run(source, out, PipelineSettings(chunk_chars=1000, overlap_chars=100))
    assert first.converted == 1
    assert second.discovered == 1
    assert second.skipped == 1


def test_common_build_directories_are_ignored(tmp_path: Path) -> None:
    source = tmp_path / "source"
    (source / "node_modules" / "pkg").mkdir(parents=True)
    (source / "node_modules" / "pkg" / "index.js").write_text("ignored", encoding="utf-8")
    (source / "keep.txt").write_text("kept", encoding="utf-8")
    stats = Pipeline().run(source, tmp_path / "out", PipelineSettings())
    assert stats.discovered == 1
    assert stats.converted == 1
