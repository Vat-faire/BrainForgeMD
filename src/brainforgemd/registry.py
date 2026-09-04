from __future__ import annotations

from pathlib import Path

from .converters.base import ConversionUnavailable, Converter, UnsupportedFormat
from .converters.email import EmlConverter
from .converters.generic_text import GenericTextConverter
from .converters.msg import MsgConverter
from .converters.notebook import NotebookConverter
from .converters.parquet import ParquetConverter
from .converters.rich import DoclingConverter, MarkItDownConverter
from .converters.sqlite import SqliteConverter
from .converters.subtitles import SubtitleConverter
from .converters.text import (
    CodeConverter,
    CsvConverter,
    HtmlConverter,
    JsonConverter,
    PlainTextConverter,
    XmlConverter,
)
from .models import ConversionResult


class ConverterRegistry:
    def __init__(self, converters: list[Converter]) -> None:
        self.converters = converters

    def matching(self, path: Path) -> list[Converter]:
        return [converter for converter in self.converters if converter.accepts(path)]

    def convert(self, path: Path) -> ConversionResult:
        matches = self.matching(path)
        if not matches:
            raise UnsupportedFormat(f"No converter registered for {path.suffix or path.name}")
        unavailable: list[str] = []
        errors: list[str] = []
        for converter in matches:
            try:
                return converter.convert(path)
            except ConversionUnavailable as exc:
                unavailable.append(f"{converter.name}: {exc}")
            except Exception as exc:
                errors.append(f"{converter.name}: {type(exc).__name__}: {exc}")
        details = errors + unavailable
        raise RuntimeError("; ".join(details) if details else "All matching converters failed")

    def format_rows(self) -> list[tuple[str, str, bool]]:
        """Name, extensions, and whether the converter can actually run here.

        The documentation points at ``brainforgemd formats`` as the authority for a
        given machine, but the listing used to show every rich extension even when the
        backend behind it was not installed and every one of those files would fail.
        """
        rows: list[tuple[str, str, bool]] = []
        for converter in self.converters:
            rows.append(
                (converter.name, ", ".join(sorted(converter.extensions)), converter.available())
            )
        return rows


def build_default_registry() -> ConverterRegistry:
    # Specific deterministic converters first; rich backends last as fallbacks.
    return ConverterRegistry([
        PlainTextConverter(),
        CodeConverter(),
        JsonConverter(),
        CsvConverter(),
        XmlConverter(),
        HtmlConverter(),
        NotebookConverter(),
        EmlConverter(),
        SubtitleConverter(),
        SqliteConverter(),
        ParquetConverter(),
        MsgConverter(),
        DoclingConverter(),
        MarkItDownConverter(),
        GenericTextConverter(),
    ])
