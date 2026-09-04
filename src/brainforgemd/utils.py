from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

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


# mimetypes reads the Windows registry and its built-in table changes between Python
# releases, so delegating to it made manifest.jsonl depend on the host. Every format
# BrainForgeMD claims to handle is pinned here so provenance stays reproducible.
_MIME_BY_EXTENSION = {
    ".adoc": "text/asciidoc", ".asciidoc": "text/asciidoc", ".log": "text/plain",
    ".markdown": "text/markdown", ".md": "text/markdown", ".rst": "text/x-rst",
    ".txt": "text/plain",
    ".csv": "text/csv", ".tsv": "text/tab-separated-values",
    ".json": "application/json", ".jsonl": "application/jsonl",
    ".ndjson": "application/x-ndjson", ".ipynb": "application/x-ipynb+json",
    ".xml": "application/xml", ".xsd": "application/xml", ".svg": "image/svg+xml",
    ".html": "text/html", ".htm": "text/html", ".xhtml": "application/xhtml+xml",
    ".yaml": "application/yaml", ".yml": "application/yaml",
    ".toml": "application/toml", ".ini": "text/plain", ".cfg": "text/plain",
    ".conf": "text/plain", ".properties": "text/plain", ".env": "text/plain",
    ".editorconfig": "text/plain", ".gitignore": "text/plain",
    ".gitattributes": "text/plain", ".npmrc": "text/plain", ".dockerignore": "text/plain",
    ".eml": "message/rfc822", ".msg": "application/vnd.ms-outlook",
    ".srt": "application/x-subrip", ".vtt": "text/vtt",
    ".sqlite": "application/vnd.sqlite3", ".sqlite3": "application/vnd.sqlite3",
    ".db": "application/vnd.sqlite3",
    ".parquet": "application/vnd.apache.parquet", ".pq": "application/vnd.apache.parquet",
    ".zip": "application/zip", ".tar": "application/x-tar", ".tgz": "application/gzip",
    ".gz": "application/gzip", ".bz2": "application/x-bzip2", ".xz": "application/x-xz",
    ".pdf": "application/pdf", ".epub": "application/epub+zip",
    ".mobi": "application/x-mobipocket-ebook",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".odt": "application/vnd.oasis.opendocument.text",
    ".ods": "application/vnd.oasis.opendocument.spreadsheet",
    ".odp": "application/vnd.oasis.opendocument.presentation",
    ".bmp": "image/bmp", ".gif": "image/gif", ".jpeg": "image/jpeg", ".jpg": "image/jpeg",
    ".png": "image/png", ".tif": "image/tiff", ".tiff": "image/tiff", ".webp": "image/webp",
    ".aac": "audio/aac", ".flac": "audio/flac", ".m4a": "audio/mp4", ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg", ".wav": "audio/wav",
    ".avi": "video/x-msvideo", ".mkv": "video/x-matroska", ".mov": "video/quicktime",
    ".mp4": "video/mp4", ".webm": "video/webm",
    ".bash": "text/x-shellscript", ".bat": "text/x-batch", ".c": "text/x-c",
    ".cc": "text/x-c++", ".cjs": "text/javascript", ".cmd": "text/x-batch",
    ".cpp": "text/x-c++", ".cs": "text/x-csharp", ".css": "text/css",
    ".cxx": "text/x-c++", ".dart": "text/x-dart", ".dockerfile": "text/x-dockerfile",
    ".erl": "text/x-erlang", ".ex": "text/x-elixir", ".exs": "text/x-elixir",
    ".fish": "text/x-shellscript", ".fs": "text/x-fsharp", ".fsx": "text/x-fsharp",
    ".go": "text/x-go", ".gql": "application/graphql", ".graphql": "application/graphql",
    ".groovy": "text/x-groovy", ".h": "text/x-c", ".hcl": "text/x-hcl",
    ".hpp": "text/x-c++", ".java": "text/x-java", ".js": "text/javascript",
    ".jsx": "text/jsx", ".kt": "text/x-kotlin", ".kts": "text/x-kotlin",
    ".latex": "application/x-latex", ".less": "text/x-less", ".lua": "text/x-lua",
    ".mjs": "text/javascript", ".php": "text/x-php", ".pl": "text/x-perl",
    ".proto": "text/x-protobuf", ".ps1": "text/x-powershell", ".py": "text/x-python",
    ".pyw": "text/x-python", ".r": "text/x-r", ".rb": "text/x-ruby", ".rs": "text/x-rust",
    ".scala": "text/x-scala", ".scss": "text/x-scss", ".sh": "text/x-shellscript",
    ".sol": "text/x-solidity", ".sql": "application/sql", ".svelte": "text/x-svelte",
    ".swift": "text/x-swift", ".tex": "application/x-tex", ".tf": "text/x-hcl",
    ".ts": "text/x-typescript", ".tsx": "text/tsx", ".vue": "text/x-vue",
    ".zsh": "text/x-shellscript",
}


def guess_mime(path: Path) -> str:
    suffix = path.suffix.lower()
    pinned = _MIME_BY_EXTENSION.get(suffix)
    if pinned:
        return pinned
    if path.name.lower().endswith((".tar.gz", ".tar.bz2", ".tar.xz")):
        return "application/x-tar"
    mime, _ = mimetypes.guess_type(path.name)
    if mime:
        return mime
    return "application/octet-stream"


def _decode_with(data: bytes, encoding: str) -> tuple[str, str] | None:
    try:
        return data.decode(encoding), encoding
    except (UnicodeDecodeError, LookupError):
        return None


def decode_text(data: bytes) -> tuple[str, str]:
    # UTF-32 LE starts with the UTF-16 LE BOM, so it has to be tested first.
    for bom, encoding in (
        (b"\xff\xfe\x00\x00", "utf-32"),
        (b"\x00\x00\xfe\xff", "utf-32"),
        (b"\xef\xbb\xbf", "utf-8-sig"),
        (b"\xff\xfe", "utf-16"),
        (b"\xfe\xff", "utf-16"),
    ):
        if data.startswith(bom):
            # A declared BOM is a hint, not a guarantee: fall through to the
            # permissive ladder rather than failing the whole file.
            decoded = _decode_with(data, encoding)
            if decoded is not None:
                return decoded
            break
    for encoding in ("utf-8", "cp1252"):
        # cp1252 covers the most common legacy Western Windows text and is a strict
        # superset of printable Latin-1 for the range where the encodings differ.
        decoded = _decode_with(data, encoding)
        if decoded is not None:
            return decoded
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


def output_filename(relative_source: str, disambiguate: bool = False) -> str:
    """Map a source-relative path to its Markdown filename.

    ``a.txt`` becomes ``a.txt.md`` while ``a.md`` keeps its name, which preserves
    compound names such as ``a.txt`` / ``a.csv``. That rule is two-to-one for the
    single pair ``X`` and ``X.md`` (``README`` and ``README.md``, for instance), so
    the caller sets ``disambiguate`` for the losing source and gets a name derived
    only from the source path, never from discovery order.
    """
    rel = Path(relative_source)
    stem = rel.name if rel.suffix.lower() in {".md", ".markdown"} else rel.name + ".md"
    if not disambiguate:
        return stem
    marker = hashlib.sha256(relative_source.encode("utf-8")).hexdigest()[:8]
    base = stem[: -len(".md")] if stem.lower().endswith(".md") else stem
    return f"{base}-{marker}.md"


def safe_output_path(root: Path, relative_source: str, disambiguate: bool = False) -> Path:
    rel = Path(relative_source)
    filename = output_filename(relative_source, disambiguate)
    target = (root / "documents" / rel.parent / filename).resolve()
    docs_root = (root / "documents").resolve()
    try:
        common = os.path.commonpath([str(target), str(docs_root)])
    except ValueError as exc:
        raise ValueError(f"Unsafe output path: {relative_source}") from exc
    if common != str(docs_root):
        raise ValueError(f"Unsafe output path: {relative_source}")
    return target


def fenced(text: str, language: str = "") -> str:
    # Choose a fence longer than any backtick run in content.
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}\n"
