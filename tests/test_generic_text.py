from pathlib import Path

from brainforgemd.converters.generic_text import GenericTextConverter


def test_extensionless_text_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "README"
    path.write_text("plain knowledge", encoding="utf-8")
    converter = GenericTextConverter()
    assert converter.accepts(path)
    assert "plain knowledge" in converter.convert(path).markdown


def test_binary_with_nul_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "blob.bin"
    path.write_bytes(b"abc\x00def")
    assert not GenericTextConverter().accepts(path)
