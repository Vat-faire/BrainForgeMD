from __future__ import annotations

from pathlib import Path

from ..models import ConversionResult
from ..utils import clean_text, decode_text, fenced
from .base import Converter


class GenericTextConverter(Converter):
    """Last-resort converter for extensionless or uncommon files that are clearly textual."""

    name = "generic-text"
    extensions = frozenset()

    def accepts(self, path: Path) -> bool:
        try:
            sample = path.read_bytes()[:65536]
        except OSError:
            return False
        if not sample:
            return True
        if b"\x00" in sample:
            return False
        # Reject obviously binary samples while accepting UTF-8/legacy text with some high bytes.
        controls = sum(1 for byte in sample if byte < 9 or 13 < byte < 32)
        return controls / len(sample) < 0.01

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        clean = clean_text(text)
        return ConversionResult(
            f"# {path.name}\n\n" + fenced(clean, "text"),
            self.name,
            path.name,
            {"encoding": encoding, "fallback": True},
        )
