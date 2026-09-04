from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Any, Iterable

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_id(prefix: str, *parts: str, length: int = 24) -> str:
    raw = "\x1f".join(parts)
    return f"{prefix}_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:length]}"


def guess_mime(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    if mime:
        return mime
    if path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
        return "application/vnd.sqlite3"
    return "application/octet-stream"


def decode_text(data: bytes) -> tuple[str, str]:
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8-sig"
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16"
    if data.startswith((b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        return data.decode("utf-32"), "utf-32"
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    # cp1252 covers the most common legacy Western Windows text and is a strict
    # superset of printable Latin-1 for the range where the encodings differ.
    try:
        return data.decode("cp1252"), "cp1252"
    except UnicodeDecodeError:
        return data.decode("latin-1"), "latin-1"


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CONTROL_RE.sub("", text)
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines).strip() + "\n"


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def jsonl_write(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json_dumps(record))
            handle.write("\n")


def safe_relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def safe_output_path(root: Path, relative_source: str) -> Path:
    rel = Path(relative_source)
    # Preserve compound names and avoid collisions such as a.txt / a.csv.
    filename = rel.name if rel.suffix.lower() in {".md", ".markdown"} else rel.name + ".md"
    target = (root / "documents" / rel.parent / filename).resolve()
    docs_root = (root / "documents").resolve()
    if os.path.commonpath([str(target), str(docs_root)]) != str(docs_root):
        raise ValueError(f"Unsafe output path: {relative_source}")
    return target


def fenced(text: str, language: str = "") -> str:
    # Choose a fence longer than any backtick run in content.
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}\n"
