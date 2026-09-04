from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from . import __version__
from .archive import ArchiveLimits, extract_archive, is_archive
from .chunking import ChunkSettings, chunk_markdown
from .frontmatter import render_front_matter
from .graph import build_graph
from .models import Chunk, ErrorRecord, PipelineStats, SourceInfo
from .registry import ConverterRegistry, build_default_registry
from .state import load_state, save_state
from .utils import guess_mime, jsonl_write, safe_output_path, sha256_file, stable_id


@dataclass(slots=True)
class PipelineSettings:
    chunk_chars: int = 5000
    overlap_chars: int = 500
    min_chunk_chars: int = 200
    max_file_mb: int = 512
    incremental: bool = True
    strict: bool = False
    include_hidden: bool = False
    archive_depth: int = 3
    archive_max_files: int = 5000
    archive_max_expanded_mb: int = 2048

    def config_hash(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256((__version__ + "\x1f" + payload).encode("utf-8")).hexdigest()


class Pipeline:
    DEFAULT_IGNORED_DIRS = frozenset({
        ".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__",
        "dist", "build", "target", ".tox", ".nox", ".mypy_cache", ".pytest_cache",
        ".ruff_cache", ".idea", ".vscode",
    })

    def __init__(self, registry: ConverterRegistry | None = None) -> None:
        self.registry = registry or build_default_registry()

    @staticmethod
    def _hidden(path: Path, root: Path) -> bool:
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            parts = path.parts
        return any(part.startswith(".") and part not in {".", ".."} for part in parts)

    def _discover(
        self, input_path: Path, include_hidden: bool, output_root: Path
    ) -> tuple[Path, list[Path]]:
        input_path = input_path.resolve()
        output_root = output_root.resolve()
        if input_path.is_file():
            return input_path.parent, [input_path]
        if not input_path.is_dir():
            raise FileNotFoundError(str(input_path))
        if input_path == output_root:
            raise ValueError("Output directory cannot be the same as the input directory")
        files: list[Path] = []
        for path in input_path.rglob("*"):
            if path.is_symlink():
                continue
            if any(part in self.DEFAULT_IGNORED_DIRS for part in path.relative_to(input_path).parts[:-1]):
                continue
            if not path.is_file():
                continue
            if not include_hidden and self._hidden(path, input_path):
                continue
            try:
                path.resolve().relative_to(output_root)
                continue
            except ValueError:
                pass
            files.append(path)
        files.sort(key=lambda p: p.relative_to(input_path).as_posix().lower())
        return input_path, files

    @staticmethod
    def _source_info(path: Path, source_root: Path, logical_relative: str | None = None) -> SourceInfo:
        relative = logical_relative or path.resolve().relative_to(source_root.resolve()).as_posix()
        digest = sha256_file(path)
        return SourceInfo(
            path=path,
            relative_path=relative,
            source_id=stable_id("src", relative),
            source_version_id=stable_id("ver", relative, digest),
            sha256=digest,
            size_bytes=path.stat().st_size,
            extension=path.suffix.lower(),
            mime_type=guess_mime(path),
        )

    def run(self, input_path: Path, output_root: Path, settings: PipelineSettings) -> PipelineStats:
        output_root = output_root.resolve()
        source_root, discovered = self._discover(input_path, settings.include_hidden, output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        stats = PipelineStats(discovered=len(discovered))
        errors: list[ErrorRecord] = []
        documents: list[dict[str, Any]] = []
        all_chunks: list[Chunk] = []
        old_state = load_state(output_root)
        new_state: dict[str, Any] = {"version": 1, "config_hash": settings.config_hash(), "files": {}}
        previous_files = old_state.get("files", {}) if settings.incremental else {}
        config_hash = settings.config_hash()
        max_bytes = settings.max_file_mb * 1024 * 1024
        chunk_settings = ChunkSettings(settings.chunk_chars, settings.overlap_chars, settings.min_chunk_chars)
        archive_limits = ArchiveLimits(settings.archive_depth, settings.archive_max_files, settings.archive_max_expanded_mb * 1024 * 1024)

        queue: list[tuple[Path, str, int]] = [(path, path.relative_to(source_root).as_posix(), 0) for path in discovered]
        archive_tempdirs: list[tempfile.TemporaryDirectory[str]] = []
        try:
            while queue:
                path, logical_relative, depth = queue.pop(0)
                if path.stat().st_size > max_bytes:
                    stats.failed += 1
                    errors.append(ErrorRecord(logical_relative, "limits", "FileTooLarge", f"File exceeds {settings.max_file_mb} MiB limit"))
                    if settings.strict:
                        raise RuntimeError(errors[-1].message)
                    continue

                if is_archive(path):
                    if depth >= archive_limits.max_depth:
                        stats.failed += 1
                        errors.append(ErrorRecord(logical_relative, "archive", "ArchiveDepthExceeded", f"Archive nesting exceeds limit {archive_limits.max_depth}"))
                        if settings.strict:
                            raise RuntimeError(errors[-1].message)
                        continue
                    tempdir = tempfile.TemporaryDirectory(prefix="brainforgemd-")
                    archive_tempdirs.append(tempdir)
                    try:
                        extracted = extract_archive(path, Path(tempdir.name), archive_limits)
                        prefix = logical_relative + "!"
                        for child in sorted(extracted, key=lambda p: p.as_posix().lower()):
                            child_rel = child.relative_to(Path(tempdir.name)).as_posix()
                            queue.append((child, f"{prefix}/{child_rel}", depth + 1))
                    except Exception as exc:
                        stats.failed += 1
                        errors.append(ErrorRecord(logical_relative, "archive", type(exc).__name__, str(exc), sha256_file(path)))
                        if settings.strict:
                            raise
                    continue

                source = self._source_info(path, source_root, logical_relative)
                output_path = safe_output_path(output_root, source.relative_path.replace("!", "__archive__"))
                previous = previous_files.get(source.relative_path, {})
                if (
                    settings.incremental
                    and previous.get("sha256") == source.sha256
                    and previous.get("config_hash") == config_hash
                    and output_path.exists()
                ):
                    # Re-read existing Markdown so indexes/graph/chunks can still be rebuilt consistently.
                    full_md = output_path.read_text(encoding="utf-8")
                    body = full_md.split("---\n\n", 1)[-1] if full_md.startswith("---\n") else full_md
                    title = previous.get("title", path.stem)
                    parser = previous.get("parser", "cached")
                    stats.skipped += 1
                else:
                    try:
                        result = self.registry.convert(path)
                    except Exception as exc:
                        message = str(exc)
                        unsupported = message.startswith("No converter registered")
                        stats.unsupported += int(unsupported)
                        stats.failed += int(not unsupported)
                        errors.append(ErrorRecord(source.relative_path, "convert", type(exc).__name__, message, source.sha256))
                        if settings.strict:
                            raise
                        continue
                    title = result.title or path.stem
                    parser = result.parser
                    fields = {
                        "brainforgemd": __version__,
                        "source_id": source.source_id,
                        "source_path": source.relative_path,
                        "source_version_id": source.source_version_id,
                        "source_name": path.name,
                        "source_extension": source.extension,
                        "mime_type": source.mime_type,
                        "size_bytes": source.size_bytes,
                        "sha256": source.sha256,
                        "parser": parser,
                        "title": title,
                        "extraction": result.metadata,
                    }
                    body = result.markdown.rstrip() + "\n"
                    full_md = render_front_matter(fields) + body
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    tmp = output_path.with_suffix(output_path.suffix + ".tmp")
                    tmp.write_text(full_md, encoding="utf-8", newline="\n")
                    tmp.replace(output_path)
                    stats.converted += 1

                chunks = chunk_markdown(body, source.source_id, source.relative_path, chunk_settings)
                stats.chunks += len(chunks)
                all_chunks.extend(chunks)
                record = {
                    "source_id": source.source_id,
                    "source_path": source.relative_path,
                    "source_version_id": source.source_version_id,
                    "output_path": output_path.relative_to(output_root).as_posix(),
                    "title": title,
                    "parser": parser,
                    "sha256": source.sha256,
                    "size_bytes": source.size_bytes,
                    "mime_type": source.mime_type,
                    "chunk_count": len(chunks),
                }
                documents.append({**record, "markdown": body})
                new_state["files"][source.relative_path] = {
                    "sha256": source.sha256,
                    "config_hash": config_hash,
                    "output_path": record["output_path"],
                    "source_id": source.source_id,
                    "title": title,
                    "parser": parser,
                }
        finally:
            for tempdir in archive_tempdirs:
                tempdir.cleanup()

        documents.sort(key=lambda d: d["source_path"].lower())
        all_chunks.sort(key=lambda c: (c.source_path.lower(), c.ordinal))
        manifest = [{k: v for k, v in doc.items() if k != "markdown"} for doc in documents]
        jsonl_write(output_root / "manifest.jsonl", manifest)
        jsonl_write(output_root / "chunks.jsonl", (chunk.to_dict() for chunk in all_chunks))
        jsonl_write(output_root / "errors.jsonl", (record.to_dict() for record in errors))
        nodes, edges = build_graph(documents, all_chunks)
        jsonl_write(output_root / "nodes.jsonl", nodes)
        jsonl_write(output_root / "edges.jsonl", edges)
        self._write_index(output_root, documents)
        self._write_report(output_root, stats, errors)
        save_state(output_root, new_state)
        return stats

    @staticmethod
    def _write_index(output_root: Path, documents: list[dict[str, Any]]) -> None:
        lines = ["# BrainForgeMD corpus index", "", f"Documents: {len(documents)}", ""]
        for doc in documents:
            target = doc["output_path"]
            label = doc["source_path"].replace("[", "\\[").replace("]", "\\]")
            lines.append(f"- [{label}]({target}) — `{doc['parser']}` — {doc['chunk_count']} chunks")
        (output_root / "INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    @staticmethod
    def _write_report(output_root: Path, stats: PipelineStats, errors: list[ErrorRecord]) -> None:
        lines = [
            "# Conversion report", "",
            f"- Discovered: **{stats.discovered}**",
            f"- Converted: **{stats.converted}**",
            f"- Incremental skips: **{stats.skipped}**",
            f"- Unsupported: **{stats.unsupported}**",
            f"- Failed: **{stats.failed}**",
            f"- Chunks: **{stats.chunks}**",
            "",
        ]
        if errors:
            lines.extend(["## Errors", ""])
            for error in errors:
                lines.append(f"- `{error.source_path}` — **{error.error_type}**: {error.message}")
        else:
            lines.append("No conversion errors.")
        (output_root / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
