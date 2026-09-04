import json
import sqlite3
from email.message import EmailMessage
from pathlib import Path

from brainforgemd.converters.email import EmlConverter
from brainforgemd.converters.notebook import NotebookConverter
from brainforgemd.converters.sqlite import SqliteConverter
from brainforgemd.converters.text import CodeConverter, CsvConverter, JsonConverter


def test_csv_converter(tmp_path: Path) -> None:
    path = tmp_path / "data.csv"
    path.write_text("name,value\nalpha,1\nbeta,2\n", encoding="utf-8")
    result = CsvConverter().convert(path)
    assert "| name | value |" in result.markdown
    assert result.metadata["rows_emitted"] == 3


def test_json_converter(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text('{"b": 1, "a": 2}', encoding="utf-8")
    result = JsonConverter().convert(path)
    assert '"a": 2' in result.markdown


def test_code_converter(tmp_path: Path) -> None:
    path = tmp_path / "hello.py"
    path.write_text("print('hello')\n", encoding="utf-8")
    result = CodeConverter().convert(path)
    assert "```python" in result.markdown


def test_notebook_never_executes_cells(tmp_path: Path) -> None:
    path = tmp_path / "sample.ipynb"
    notebook = {
        "cells": [{"cell_type": "code", "source": ["raise RuntimeError('must not run')"], "outputs": [], "metadata": {}, "execution_count": None}],
        "metadata": {}, "nbformat": 4, "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook), encoding="utf-8")
    result = NotebookConverter().convert(path)
    assert "must not run" in result.markdown


def test_eml_converter(tmp_path: Path) -> None:
    message = EmailMessage()
    message["Subject"] = "Test mail"
    message["From"] = "sender@example.com"
    message["To"] = "receiver@example.com"
    message.set_content("Hello from email")
    path = tmp_path / "mail.eml"
    path.write_bytes(message.as_bytes())
    result = EmlConverter().convert(path)
    assert "# Test mail" in result.markdown
    assert "Hello from email" in result.markdown


def test_sqlite_read_only_extract(tmp_path: Path) -> None:
    path = tmp_path / "data.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE things(id INTEGER, name TEXT)")
    conn.execute("INSERT INTO things VALUES (1, 'alpha')")
    conn.commit()
    conn.close()
    result = SqliteConverter().convert(path)
    assert "Table `things`" in result.markdown
    assert "alpha" in result.markdown
