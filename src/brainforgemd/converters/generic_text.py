from __future__ import annotations

from pathlib import Path

from ..archive import ARCHIVE_SUFFIXES
from ..models import ConversionResult
from ..utils import clean_text, decode_text, fenced
from .base import Converter
from .rich import RICH_EXTENSIONS

# Formats that have a dedicated binary backend. When that backend is missing the right
# answer is a reported failure, not a text dump: a small uncompressed PDF is mostly
# printable ASCII, so this converter used to "succeed" on it and write PDF object syntax
# into the corpus as if it were the document's prose, with failed=0 and parser
# "generic-text". That is the fabricated extraction the project sets out to avoid.
BINARY_EXTENSIONS = (
    RICH_EXTENSIONS
    | frozenset(ARCHIVE_SUFFIXES)
    | frozenset({".sqlite", ".sqlite3", ".db", ".parquet", ".pq", ".gz", ".bz2", ".xz"})
)


class GenericTextConverter(Converter):
    """Last-resort converter for extensionless or uncommon files that are clearly textual."""

    name = "generic-text"
    extensions = frozenset()

    def accepts(self, path: Path) -> bool:
        name = path.name.lower()
        if path.suffix.lower() in BINARY_EXTENSIONS or any(
            name.endswith(suffix) for suffix in ARCHIVE_SUFFIXES
        ):
            return False
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
