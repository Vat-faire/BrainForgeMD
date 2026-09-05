from __future__ import annotations

import json
import sqlite3
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

from brainforgemd.pipeline import Pipeline, PipelineSettings


def _manifest(path: Path) -> dict[str, dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {row["source_path"]: row for row in rows}


def test_every_core_format_preserves_its_unique_marker(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    fixtures = {
        "plain.txt": "CODEX_MARKER_TXT",
        "notes.md": "CODEX_MARKER_MD",
        "program.py": "CODEX_MARKER_SOURCE",
        "config.yaml": "CODEX_MARKER_YAML",
        "settings.toml": "CODEX_MARKER_TOML",
        "values.ini": "CODEX_MARKER_INI",
        "data.json": "CODEX_MARKER_JSON",
        "schema.xml": "CODEX_MARKER_XML",
        "table.csv": "CODEX_MARKER_CSV",
        "table.tsv": "CODEX_MARKER_TSV",
        "page.html": "CODEX_MARKER_HTML",
        "book.ipynb": "CODEX_MARKER_IPYNB",
        "mail.eml": "CODEX_MARKER_EML",
        "captions.srt": "CODEX_MARKER_SRT",
    }
    for name, marker in fixtures.items():
        path = source / name
        suffix = path.suffix
        if suffix == ".json":
            path.write_text(json.dumps({"marker": marker}), encoding="utf-8")
        elif suffix == ".xml":
            path.write_text(f"<root><marker>{marker}</marker></root>", encoding="utf-8")
        elif suffix == ".csv":
            path.write_text(f"name,value\nmarker,{marker}\n", encoding="utf-8")
        elif suffix == ".tsv":
            path.write_text(f"name\tvalue\nmarker\t{marker}\n", encoding="utf-8")
        elif suffix == ".html":
            path.write_text(
                f"<html><body><p>{marker}</p><script>FORBIDDEN_SCRIPT</script></body></html>",
                encoding="utf-8",
            )
        elif suffix == ".ipynb":
            path.write_text(
                json.dumps(
                    {
                        "cells": [{"cell_type": "markdown", "source": [marker]}],
                        "metadata": {},
                        "nbformat": 4,
                        "nbformat_minor": 5,
                    }
                ),
                encoding="utf-8",
            )
        elif suffix == ".eml":
            path.write_text(
                f"From: audit@example.test\nSubject: Audit marker\n\n{marker}\n",
                encoding="utf-8",
            )
        elif suffix == ".srt":
            path.write_text(f"1\n00:00:00,000 --> 00:00:01,000\n{marker}\n", encoding="utf-8")
        else:
            path.write_text(marker, encoding="utf-8")

    database = source / "records.sqlite"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE records (marker TEXT)")
    connection.execute("INSERT INTO records VALUES (?)", ("CODEX_MARKER_SQLITE",))
    connection.commit()
    connection.close()
    fixtures[database.name] = "CODEX_MARKER_SQLITE"

    with zipfile.ZipFile(source / "nested.zip", "w") as archive:
        archive.writestr("inside/zip.txt", "CODEX_MARKER_ZIP")
    fixtures["nested.zip!/inside/zip.txt"] = "CODEX_MARKER_ZIP"

    tar_payload = b"CODEX_MARKER_TAR"
    with tarfile.open(source / "nested.tar", "w") as archive:
        info = tarfile.TarInfo("inside/tar.txt")
        info.size = len(tar_payload)
        archive.addfile(info, BytesIO(tar_payload))
    fixtures["nested.tar!/inside/tar.txt"] = "CODEX_MARKER_TAR"

    output = tmp_path / "output"
    stats = Pipeline().run(source, output, PipelineSettings())
    manifest = _manifest(output / "manifest.jsonl")

    assert stats.failed == 0
    assert stats.unsupported == 0
    assert set(manifest) == set(fixtures)
    for name, marker in fixtures.items():
        markdown = (output / manifest[name]["output_path"]).read_text(encoding="utf-8")
        assert marker in markdown, name
    assert "FORBIDDEN_SCRIPT" not in (
        output / manifest["page.html"]["output_path"]
    ).read_text(encoding="utf-8")
