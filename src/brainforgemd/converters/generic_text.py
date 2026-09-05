from __future__ import annotations

import codecs
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
            with path.open("rb") as source:
                prefix = source.read(4)
                if not prefix:
                    return True
                bom_encoding = next(
                    (
                        encoding
                        for bom, encoding in (
                            (b"\xff\xfe\x00\x00", "utf-32"),
                            (b"\x00\x00\xfe\xff", "utf-32"),
                            (b"\xef\xbb\xbf", "utf-8-sig"),
                            (b"\xff\xfe", "utf-16"),
                            (b"\xfe\xff", "utf-16"),
                        )
                        if prefix.startswith(bom)
                    ),
                    None,
                )
                if bom_encoding is not None:
                    decoder = codecs.getincrementaldecoder(bom_encoding)(errors="strict")
                    source.seek(0)
                    while block := source.read(65536):
                        decoder.decode(block, final=False)
                    decoder.decode(b"", final=True)
                    return True

                source.seek(0)
                controls = 0
                total = 0
                while block := source.read(65536):
                    if b"\x00" in block:
                        return False
                    total += len(block)
                    controls += sum(1 for byte in block if byte < 9 or 13 < byte < 32)
        except OSError:
            return False
        except UnicodeDecodeError:
            return False
        # Reject obviously binary data while accepting UTF-8/legacy text with high bytes.
        return controls / total < 0.01

    def convert(self, path: Path) -> ConversionResult:
        text, encoding = decode_text(path.read_bytes())
        clean = clean_text(text)
        return ConversionResult(
            f"# {path.name}\n\n" + fenced(clean, "text"),
            self.name,
            path.name,
            {"encoding": encoding, "fallback": True},
        )
