from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ConversionResult


class ConversionUnavailable(RuntimeError):
    """Raised when a converter is recognized but its optional backend is unavailable."""


class UnsupportedFormat(RuntimeError):
    """Raised when no converter can handle a source."""


class Converter(ABC):
    name: str
    extensions: frozenset[str]

    def accepts(self, path: Path) -> bool:
        return path.suffix.lower() in self.extensions

    @abstractmethod
    def convert(self, path: Path) -> ConversionResult:
        raise NotImplementedError
