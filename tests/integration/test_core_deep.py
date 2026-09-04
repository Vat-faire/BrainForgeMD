from __future__ import annotations

import json
import sqlite3
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

import pytest

from brainforgemd.archive import ArchiveLimits, extract_archive
from brainforgemd.pipeline import Pipeline, PipelineSettings


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _make_core_corpus(root: Path) -> None:
    (root / "nested").mkdir(parents=True)
    (root / "plain.txt").write_text("BrainForgeMD plain text\nSecond paragraph.\n", encoding="utf-8")
    (root / "unicode.txt").write_bytes("Café — Québec — 日本語".encode("utf-16"))
    (root / "notes.md").write_text("# Notes\n\nSee [nested note](nested/note.txt).\n", encoding="utf-8")
    (root / "nested" / "note.txt").write_text("Nested knowledge.\n", encoding="utf-8")
    (root / "code.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    (root / "data.json").write_text('{"name":"BrainForgeMD","ok":true}', encoding="utf-8")
    (root / "rows.jsonl").write_text('{"id":1}\n{"id":2}\n', encoding="utf-8")
    (root / "config.yaml").write_text("enabled: true\nname: BrainForgeMD\n", encoding="utf-8")
    (root / "table.csv").write_text("name,value\nalpha,1\nbeta,2\n", encoding="utf-8")
    (root / "page.html").write_text(
        "<html><head><title>Fixture</title></head><body><h1>Hello</h1><p>Useful text.</p></body></html>",
        encoding="utf-8",
    )
    notebook = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Notebook fixture\n"]},
            {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["print('safe')\n"]},
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (root / "notebook.ipynb").write_text(json.dumps(notebook), encoding="utf-8")
    (root / "mail.eml").write_text(
        "From: sender@example.test\nTo: receiver@example.test\nSubject: Synthetic message\n"
        "Content-Type: text/plain; charset=utf-8\n\nThis is synthetic email content.\n",
        encoding="utf-8",
    )
    (root / "captions.srt").write_text(
        "1\n00:00:00,000 --> 00:00:02,000\nSynthetic subtitle line.\n",
        encoding="utf-8",
    )
    db = sqlite3.connect(root / "sample.sqlite")
    try:
        db.execute("create table facts (id integer primary key, value text)")
        db.execute("insert into facts(value) values (?)", ("synthetic row",))
        db.commit()
    finally:
        db.close()
    with zipfile.ZipFile(root / "bundle.zip", "w") as archive:
        archive.writestr("inside/archive-note.txt", "Knowledge extracted from a safe ZIP archive.\n")


def test_core_corpus_end_to_end_contract(tmp_path: Path) -> None:
    source = tmp_path / "knowledge"
    out = tmp_path / "context-out"
    source.mkdir()
    _make_core_corpus(source)

    stats = Pipeline().run(source, out, PipelineSettings(chunk_chars=500, overlap_chars=50))

    assert stats.failed == 0
    assert stats.unsupported == 0
    assert stats.converted >= 15
    assert stats.chunks >= stats.converted

    required = {
        "INDEX.md",
        "REPORT.md",
        "manifest.jsonl",
        "chunks.jsonl",
        "nodes.jsonl",
        "edges.jsonl",
        "errors.jsonl",
        ".brainforgemd/state.json",
    }
    for relative in required:
        assert (out / relative).is_file(), relative

    manifest = _jsonl(out / "manifest.jsonl")
    chunks = _jsonl(out / "chunks.jsonl")
    nodes = _jsonl(out / "nodes.jsonl")
    edges = _jsonl(out / "edges.jsonl")
    errors = _jsonl(out / "errors.jsonl")

    assert errors == []
    assert len(manifest) == stats.converted
    assert len(chunks) == stats.chunks
    assert any(item["source_path"] == "bundle.zip!/inside/archive-note.txt" for item in manifest)
    assert any(item["source_path"] == "unicode.txt" for item in manifest)
    assert all(item["source_id"].startswith("src_") for item in manifest)
    assert all(len(item["sha256"]) == 64 for item in manifest)
    assert all(item["chunk_count"] >= 1 for item in manifest)
    assert any(node["type"] == "document" for node in nodes)
    assert any(node["type"] == "chunk" for node in nodes)
    assert any(edge["type"] == "contains" for edge in edges)

    for item in manifest:
        markdown = (out / item["output_path"]).read_text(encoding="utf-8")
        assert markdown.startswith("---\n")
        assert f'source_id: "{item["source_id"]}"' in markdown
        assert f'sha256: "{item["sha256"]}"' in markdown
        assert "parser:" in markdown

    report = (out / "REPORT.md").read_text(encoding="utf-8")
    assert "Failed: **0**" in report
    assert "Unsupported: **0**" in report


def test_incremental_second_run_is_byte_stable(tmp_path: Path) -> None:
    source = tmp_path / "knowledge"
    out = tmp_path / "context-out"
    source.mkdir()
    _make_core_corpus(source)
    settings = PipelineSettings(chunk_chars=500, overlap_chars=50)

    first = Pipeline().run(source, out, settings)
    snapshots = {
        name: (out / name).read_bytes()
        for name in ["manifest.jsonl", "chunks.jsonl", "nodes.jsonl", "edges.jsonl"]
    }
    second = Pipeline().run(source, out, settings)

    assert first.failed == 0
    assert second.failed == 0
    assert second.converted == 0
    assert second.skipped == first.converted
    for name, before in snapshots.items():
        assert (out / name).read_bytes() == before, name


def test_output_tree_is_not_reingested(tmp_path: Path) -> None:
    source = tmp_path / "knowledge"
    source.mkdir()
    (source / "one.txt").write_text("one", encoding="utf-8")
    out = source / "context-out"

    first = Pipeline().run(source, out, PipelineSettings())
    second = Pipeline().run(source, out, PipelineSettings())

    assert first.discovered == 1
    assert second.discovered == 1
    assert second.skipped == 1
    assert all("context-out" not in item["source_path"] for item in _jsonl(out / "manifest.jsonl"))


@pytest.mark.parametrize("member", ["../escape.txt", "..\\escape.txt", "/escape.txt", "C:\\escape.txt"])
def test_zip_path_traversal_is_rejected(tmp_path: Path, member: str) -> None:
    archive_path = tmp_path / "hostile.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(member, "escape attempt")
    destination = tmp_path / "extract"

    with pytest.raises(ValueError, match="Archive"):
        extract_archive(archive_path, destination, ArchiveLimits())
    assert not (tmp_path / "escape.txt").exists()


def test_tar_path_traversal_is_rejected(tmp_path: Path) -> None:
    archive_path = tmp_path / "hostile.tar"
    payload = b"escape attempt"
    with tarfile.open(archive_path, "w") as archive:
        info = tarfile.TarInfo("../escape.txt")
        info.size = len(payload)
        archive.addfile(info, BytesIO(payload))

    with pytest.raises(ValueError, match="Archive"):
        extract_archive(archive_path, tmp_path / "extract", ArchiveLimits())
    assert not (tmp_path / "escape.txt").exists()


def test_archive_file_count_and_expanded_size_limits(tmp_path: Path) -> None:
    archive_path = tmp_path / "limits.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("one.txt", "12345")
        archive.writestr("two.txt", "67890")

    with pytest.raises(ValueError, match="members"):
        extract_archive(archive_path, tmp_path / "count", ArchiveLimits(max_files=1))
    with pytest.raises(ValueError, match="expanded-size"):
        extract_archive(archive_path, tmp_path / "size", ArchiveLimits(max_expanded_bytes=6))
