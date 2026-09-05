from __future__ import annotations

import json
import os
import unicodedata
import zipfile
from pathlib import Path

import pytest

import brainforgemd.pipeline as pipeline_module
from brainforgemd import cli
from brainforgemd.archive import ArchiveLimits, extract_archive
from brainforgemd.converters.generic_text import GenericTextConverter
from brainforgemd.pipeline import Pipeline, PipelineSettings
from brainforgemd.utils import jsonl_write, sha256_file


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _portable_path_key(path: Path) -> str:
    return unicodedata.normalize("NFC", path.as_posix()).casefold()


def test_tampered_cached_document_is_reconverted(tmp_path: Path) -> None:
    """Cached Markdown is derived data, not a trusted substitute for the source."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("AUTHENTIC_SOURCE_MARKER", encoding="utf-8")
    output = tmp_path / "output"
    settings = PipelineSettings()

    assert Pipeline().run(source, output, settings).converted == 1
    record = _jsonl(output / "manifest.jsonl")[0]
    document = output / record["output_path"]
    document.write_text("---\n\nTAMPERED_CACHE_MARKER\n", encoding="utf-8")

    replay = Pipeline().run(source, output, settings)

    assert replay.converted == 1
    assert replay.skipped == 0
    markdown = document.read_text(encoding="utf-8")
    assert "AUTHENTIC_SOURCE_MARKER" in markdown
    assert "TAMPERED_CACHE_MARKER" not in markdown
    state = json.loads((output / ".brainforgemd" / "state.json").read_text(encoding="utf-8"))
    assert state["files"]["note.txt"]["output_sha256"] == sha256_file(document)


def test_malformed_cache_entry_is_invalidated_instead_of_crashing(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("CACHE_STATE_MARKER", encoding="utf-8")
    output = tmp_path / "output"
    settings = PipelineSettings()
    Pipeline().run(source, output, settings)

    state_path = output / ".brainforgemd" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["files"]["note.txt"] = ["hostile", "shape"]
    state_path.write_text(json.dumps(state), encoding="utf-8")

    replay = Pipeline().run(source, output, settings)

    assert replay.converted == 1
    assert replay.failed == 0
    assert "CACHE_STATE_MARKER" in next((output / "documents").rglob("*.md")).read_text(
        encoding="utf-8"
    )


def test_source_change_between_hash_and_conversion_is_rejected(
    tmp_path: Path, monkeypatch
) -> None:
    """A mutation after the provenance hash but before conversion must not be published."""
    source = tmp_path / "source"
    source.mkdir()
    document = source / "race.txt"
    document.write_text("ORIGINAL_MARKER", encoding="utf-8")
    original_stat = document.stat()
    real_sha256_file = pipeline_module.sha256_file
    mutated = False

    def hash_then_mutate(path: Path, *args, **kwargs) -> str:
        nonlocal mutated
        digest = real_sha256_file(path, *args, **kwargs)
        if path == document and not mutated:
            mutated = True
            document.write_text("MUTATED__MARKER", encoding="utf-8")
            os.utime(
                document,
                ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
            )
        return digest

    monkeypatch.setattr(pipeline_module, "sha256_file", hash_then_mutate)
    output = tmp_path / "output"
    stats = Pipeline().run(source, output, PipelineSettings())

    assert stats.failed == 1
    assert stats.converted == 0
    assert _jsonl(output / "manifest.jsonl") == []
    assert _jsonl(output / "errors.jsonl")[0]["error_type"] == "SourceChangedDuringRead"


def test_portable_source_name_collisions_get_distinct_output_paths(tmp_path: Path) -> None:
    """A Linux corpus must remain representable on case-insensitive/NFD filesystems."""
    claimed: dict[str, str] = {}
    outputs = [
        Pipeline._claim_output_path(tmp_path, name, claimed)
        for name in ("Report.txt", "report.txt", "caf\u00e9.txt", "cafe\u0301.txt")
    ]
    portable = [_portable_path_key(path) for path in outputs]
    assert len(portable) == len(set(portable))


def test_archive_trailing_dot_collision_is_rejected_portably(tmp_path: Path) -> None:
    archive_path = tmp_path / "collision.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("folder/report.txt", "FIRST_MARKER")
        archive.writestr("folder/report.txt.", "SECOND_MARKER")

    try:
        extract_archive(archive_path, tmp_path / "extract", ArchiveLimits())
    except ValueError as exc:
        assert "same portable file identity" in str(exc)
    else:
        raise AssertionError("Windows-equivalent archive members were both accepted")


def test_single_file_run_cannot_corrupt_a_multi_source_corpus(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("SOURCE_A", encoding="utf-8")
    (source / "b.txt").write_text("SOURCE_B", encoding="utf-8")
    output = tmp_path / "output"
    Pipeline().run(source, output, PipelineSettings())
    artifacts = {
        name: (output / name).read_bytes()
        for name in ("manifest.jsonl", "chunks.jsonl", "nodes.jsonl", "edges.jsonl")
    }

    (source / "a.txt").write_text("SOURCE_A_CHANGED", encoding="utf-8")
    with pytest.raises(ValueError, match="single-file run"):
        Pipeline().run(source / "a.txt", output, PipelineSettings())

    for name, before in artifacts.items():
        assert (output / name).read_bytes() == before


def test_global_artifacts_roll_back_as_one_generation(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    document = source / "a.txt"
    document.write_text("ORIGINAL_GENERATION", encoding="utf-8")
    output = tmp_path / "output"
    Pipeline().run(source, output, PipelineSettings())
    tracked = (
        "manifest.jsonl",
        "chunks.jsonl",
        "nodes.jsonl",
        "edges.jsonl",
        "INDEX.md",
        ".brainforgemd/state.json",
    )
    before = {name: (output / name).read_bytes() for name in tracked}
    original_jsonl_write = pipeline_module.jsonl_write

    def fail_while_staging_chunks(path: Path, records) -> None:
        if path.name == "chunks.jsonl":
            raise OSError("simulated full disk")
        original_jsonl_write(path, records)

    document.write_text("REPLACEMENT_GENERATION", encoding="utf-8")
    monkeypatch.setattr(pipeline_module, "jsonl_write", fail_while_staging_chunks)
    with pytest.raises(OSError, match="simulated full disk"):
        Pipeline().run(source, output, PipelineSettings())

    for name, original in before.items():
        assert (output / name).read_bytes() == original
    published = next((output / "documents").rglob("*.md")).read_text(encoding="utf-8")
    assert "ORIGINAL_GENERATION" in published
    assert "REPLACEMENT_GENERATION" not in published


def test_text_fallback_detects_binary_payload_after_the_first_64k(tmp_path: Path) -> None:
    path = tmp_path / "deceptive.unknown"
    path.write_bytes(b"apparently ordinary prose\n" * 3000 + b"\x00\x01\x02" * 30_000)
    assert not GenericTextConverter().accepts(path)


def test_jsonl_writer_streams_records_into_its_temporary_file(tmp_path: Path) -> None:
    target = tmp_path / "large.jsonl"

    def records():
        for index in range(3):
            assert list(tmp_path.glob("large.jsonl.*.tmp"))
            yield {"index": index, "payload": "x" * 1000}

    jsonl_write(target, records())
    assert [row["index"] for row in _jsonl(target)] == [0, 1, 2]


def test_doctor_and_formats_disclose_missing_asr(monkeypatch, capsys) -> None:
    real_module = cli._module
    monkeypatch.setattr(cli, "_module", lambda name: False if name == "whisper" else real_module(name))

    assert cli.main(["doctor"]) == 0
    doctor = capsys.readouterr().out
    assert "ASR transcription" in doctor
    assert "not found" in doctor
    assert "documents/OCR/media" not in doctor

    assert cli.main(["formats"]) == 0
    formats = capsys.readouterr().out
    assert "audio/video require the [asr] extra" in formats
