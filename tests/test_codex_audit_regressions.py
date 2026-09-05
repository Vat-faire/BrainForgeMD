from __future__ import annotations

import json
import os
import unicodedata
import zipfile
from pathlib import Path

import brainforgemd.pipeline as pipeline_module
from brainforgemd.archive import ArchiveLimits, extract_archive
from brainforgemd.pipeline import Pipeline, PipelineSettings
from brainforgemd.utils import sha256_file


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
