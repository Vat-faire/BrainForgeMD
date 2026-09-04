from __future__ import annotations

import importlib.util
from pathlib import Path

from ..models import ConversionResult
from .base import ConversionUnavailable, Converter

RICH_EXTENSIONS = frozenset({
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".odt", ".ods", ".odp",
    ".epub", ".mobi", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp",
    ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".mp4", ".mkv", ".mov", ".avi",
    ".webm", ".msg", ".latex", ".tex",
})


class DoclingConverter(Converter):
    name = "docling"
    extensions = RICH_EXTENSIONS

    def available(self) -> bool:
        return importlib.util.find_spec("docling") is not None

    def convert(self, path: Path) -> ConversionResult:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise ConversionUnavailable("Docling backend is not installed") from exc
        try:
            result = DocumentConverter().convert(path)
            markdown = result.document.export_to_markdown()
        except Exception as exc:
            raise RuntimeError(f"Docling failed: {exc}") from exc
        if not markdown.strip():
            raise RuntimeError("Docling returned empty Markdown")
        return ConversionResult(markdown.rstrip() + "\n", self.name, path.stem, {"backend": "docling"})


class MarkItDownConverter(Converter):
    name = "markitdown"
    extensions = RICH_EXTENSIONS | frozenset({".zip"})

    def available(self) -> bool:
        return importlib.util.find_spec("markitdown") is not None

    def convert(self, path: Path) -> ConversionResult:
        try:
            from markitdown import MarkItDown
        except ImportError as exc:
            raise ConversionUnavailable("MarkItDown backend is not installed") from exc
        try:
            result = MarkItDown().convert(str(path))
        except Exception as exc:
            raise RuntimeError(f"MarkItDown failed: {exc}") from exc
        markdown = getattr(result, "text_content", "") or ""
        if not markdown.strip():
            raise RuntimeError("MarkItDown returned empty Markdown")
        return ConversionResult(markdown.rstrip() + "\n", self.name, path.stem, {"backend": "markitdown"})
