from pathlib import Path

from brainforgemd.cli import main


def test_cli_version(capsys) -> None:
    assert main(["version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_cli_convert(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "note.txt").write_text("hello", encoding="utf-8")
    out = tmp_path / "out"
    assert main(["convert", str(source), "-o", str(out), "--chunk-chars", "1000", "--overlap-chars", "100"]) == 0
    assert (out / "manifest.jsonl").exists()
