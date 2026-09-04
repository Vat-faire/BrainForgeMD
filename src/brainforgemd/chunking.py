from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Chunk
from .utils import sha256_text, stable_id

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(slots=True)
class ChunkSettings:
    target_chars: int = 5000
    overlap_chars: int = 500
    min_chars: int = 200

    def validate(self) -> None:
        if self.target_chars < 500:
            raise ValueError("target_chars must be >= 500")
        if self.overlap_chars < 0:
            raise ValueError("overlap_chars must be >= 0")
        # Each window advances by target - overlap, so an overlap close to the target
        # advances a few characters at a time and duplicates the document hundreds of
        # times over. Half the target caps total chunk text at roughly twice the source.
        if self.overlap_chars > self.target_chars // 2:
            raise ValueError("overlap_chars must be at most half of target_chars")


def _sections(markdown: str) -> list[tuple[list[str], str]]:
    stack: list[str] = []
    current: list[str] = []
    body: list[str] = []
    output: list[tuple[list[str], str]] = []

    def flush() -> None:
        nonlocal body
        text = "\n".join(body).strip()
        if text:
            output.append((current.copy(), text))
        body = []

    for line in markdown.splitlines():
        match = _HEADING_RE.match(line)
        if match:
            flush()
            level = len(match.group(1))
            title = match.group(2).strip()
            stack[:] = stack[: level - 1]
            while len(stack) < level - 1:
                stack.append("")
            if len(stack) == level - 1:
                stack.append(title)
            else:
                stack[level - 1] = title
            current = [part for part in stack if part]
            body.append(line)
        else:
            body.append(line)
    flush()
    return output or [([], markdown.strip())]


def _split_window(text: str, target: int, overlap: int) -> list[str]:
    if len(text) <= target:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        hard_end = min(start + target, len(text))
        end = hard_end
        if hard_end < len(text):
            # Prefer paragraph, then line, then whitespace boundary.
            for marker in ("\n\n", "\n", " "):
                pos = text.rfind(marker, start + target // 2, hard_end)
                if pos > start:
                    end = pos + len(marker)
                    break
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_markdown(
    markdown: str,
    source_id: str,
    source_path: str,
    settings: ChunkSettings,
) -> list[Chunk]:
    settings.validate()
    raw: list[tuple[list[str], str]] = []
    for path, section in _sections(markdown):
        for piece in _split_window(section, settings.target_chars, settings.overlap_chars):
            # A blank source used to yield one zero-length chunk, which is pure noise
            # for a retrieval index.
            if piece.strip():
                raw.append((path, piece))

    # Merge tiny adjacent chunks from the same section when safe.
    merged: list[tuple[list[str], str]] = []
    for path, text in raw:
        if (
            merged
            and len(text) < settings.min_chars
            and merged[-1][0] == path
            and len(merged[-1][1]) + 2 + len(text) <= settings.target_chars
        ):
            prev_path, prev_text = merged[-1]
            merged[-1] = (prev_path, f"{prev_text}\n\n{text}")
        else:
            merged.append((path, text))

    chunks: list[Chunk] = []
    for ordinal, (section_path, text) in enumerate(merged):
        digest = sha256_text(text)
        chunk_id = stable_id(
            "chk",
            source_id,
            "/".join(section_path),
            str(ordinal),
            digest,
        )
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                source_id=source_id,
                source_path=source_path,
                ordinal=ordinal,
                section_path=section_path,
                text=text,
                char_count=len(text),
                approx_tokens=max(1, (len(text) + 3) // 4),
                sha256=digest,
            )
        )
    return chunks
