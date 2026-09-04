from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SourceInfo:
    path: Path
    relative_path: str
    source_id: str
    source_version_id: str
    sha256: str
    size_bytes: int
    extension: str
    mime_type: str


@dataclass(slots=True)
class ConversionResult:
    markdown: str
    parser: str
    title: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    source_id: str
    source_path: str
    ordinal: int
    section_path: list[str]
    text: str
    char_count: int
    approx_tokens: int
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ErrorRecord:
    source_path: str
    stage: str
    error_type: str
    message: str
    sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PipelineStats:
    discovered: int = 0
    converted: int = 0
    skipped: int = 0
    unsupported: int = 0
    failed: int = 0
    chunks: int = 0
