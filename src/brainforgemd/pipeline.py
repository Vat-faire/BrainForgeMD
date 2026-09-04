from __future__ import annotations

import contextlib
import hashlib
import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from . import __version__
from .archive import ArchiveBudget, ArchiveLimits, extract_archive, is_archive
from .chunking import ChunkSettings, chunk_markdown
from .frontmatter import render_front_matter
from .graph import build_graph
from .lock import CorpusLock
from .models import Chunk, ErrorRecord, PipelineStats, SourceInfo
from .registry import ConverterRegistry, build_default_registry
from .state import load_state, save_state
from .utils import (
    atomic_write_text,
    guess_mime,
    jsonl_write,
    safe_output_path,
    sha256_file,
    stable_id,
)


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
        # An output directory that contains the source excludes every source through the
        # "never re-ingest the corpus" filter, so `convert ./docs -o .` used to report
        # discovered=0, write an empty corpus and exit 0.
        if output_root in input_path.parents:
            raise ValueError(
                f"Output directory {output_root} contains the source directory {input_path}; "
                "every source would be excluded as part of the corpus. Choose an output "
                "directory outside the source tree, or a subdirectory of it."
            )
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

    @staticmethod
    def _claim_output_path(output_root: Path, relative_path: str, claimed: dict[str, str]) -> Path:
        """Give this source an output path no other source in the run owns.

        ``a.txt`` maps to ``a.txt.md`` while ``a.md`` keeps its name, which is a
        two-to-one mapping for the pair ``X`` / ``X.md`` — ``README`` and ``README.md``
        both wanted ``documents/README.md``, so one source was silently overwritten and
        its manifest row described the other one's text. The loser now gets a filename
        derived from its own source path, and since discovery is sorted the winner is
        always the lexicographically smaller path, independent of what else is present.
        """
        logical = relative_path.replace("!", "__archive__")
        candidate = safe_output_path(output_root, logical)
        key = candidate.relative_to(output_root).as_posix()
        owner = claimed.get(key)
        if owner is None or owner == relative_path:
            claimed[key] = relative_path
            return candidate
        candidate = safe_output_path(output_root, logical, disambiguate=True)
        key = candidate.relative_to(output_root).as_posix()
        claimed[key] = relative_path
        return candidate

    @staticmethod
    def _prune_orphan_documents(output_root: Path, keep: set[str]) -> int:
        """Delete Markdown left behind by sources that no longer exist.

        The README tells consumers to treat ``documents/**/*.md`` as the corpus, so
        stale files for deleted or renamed sources were served as live content.
        """
        documents_root = (output_root / "documents").resolve()
        if not documents_root.is_dir():
            return 0
        removed = 0
        for path in sorted(documents_root.rglob("*"), reverse=True):
            if path.is_dir():
                try:
                    next(path.iterdir())
                except StopIteration:
                    with contextlib.suppress(OSError):
                        path.rmdir()
                except OSError:
                    pass
                continue
            relative = path.relative_to(output_root).as_posix()
            if relative in keep:
                continue
            with contextlib.suppress(OSError):
                path.unlink()
                removed += 1
        return removed

    def run(self, input_path: Path, output_root: Path, settings: PipelineSettings) -> PipelineStats:
        output_root = output_root.resolve()
        full_scan = Path(input_path).resolve().is_dir()
        source_root, discovered = self._discover(input_path, settings.include_hidden, output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        # Nothing in the output contract survives two writers, and each run prunes what
        # it considers the other's orphans, so a concurrent run is refused up front.
        with CorpusLock(output_root):
            return self._run_locked(
                source_root, discovered, output_root, settings, full_scan
            )

    def _run_locked(
        self,
        source_root: Path,
        discovered: list[Path],
        output_root: Path,
        settings: PipelineSettings,
        full_scan: bool,
    ) -> PipelineStats:
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
        archive_budget = ArchiveBudget(archive_limits.max_files, archive_limits.max_expanded_bytes)
        # output_path -> source relative_path, so a second source that maps to a name
        # another source already owns is given a distinct, path-derived filename.
        claimed: dict[str, str] = {}

        queue: list[tuple[Path, str, int]] = [(path, path.relative_to(source_root).as_posix(), 0) for path in discovered]
        archive_tempdirs: list[tempfile.TemporaryDirectory[str]] = []
        try:
            while queue:
                path, logical_relative, depth = queue.pop(0)
                try:
                    size_bytes = path.stat().st_size
                except OSError as exc:
                    stats.failed += 1
                    errors.append(ErrorRecord(logical_relative, "discover", type(exc).__name__, str(exc)))
                    if settings.strict:
                        raise
                    continue
                if size_bytes > max_bytes:
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
                        extracted = extract_archive(path, Path(tempdir.name), archive_limits, archive_budget)
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

                try:
                    source = self._source_info(path, source_root, logical_relative)
                    output_path = self._claim_output_path(output_root, source.relative_path, claimed)
                except (OSError, ValueError) as exc:
                    stats.failed += 1
                    errors.append(ErrorRecord(logical_relative, "output", type(exc).__name__, str(exc)))
                    if settings.strict:
                        raise
                    continue

                previous = previous_files.get(source.relative_path, {})
                if (
                    settings.incremental
                    and previous.get("sha256") == source.sha256
                    and previous.get("config_hash") == config_hash
                    and previous.get("output_path") == output_path.relative_to(output_root).as_posix()
                    and output_path.exists()
                ):
                    # Re-read existing Markdown so indexes/graph/chunks can still be rebuilt consistently.
                    try:
                        full_md = output_path.read_text(encoding="utf-8")
                    except OSError as exc:
                        stats.failed += 1
                        errors.append(ErrorRecord(source.relative_path, "cache", type(exc).__name__, str(exc), source.sha256))
                        if settings.strict:
                            raise
                        continue
                    body = full_md.split("---\n\n", 1)[-1] if full_md.startswith("---\n") else full_md
                    title = previous.get("title", path.stem)
                    parser = previous.get("parser", "cached")
                    stats.skipped += 1
                else:
                    try:
                        stamp_before = path.stat()
                        result = self.registry.convert(path)
                        stamp_after = path.stat()
                    except Exception as exc:
                        message = str(exc)
                        unsupported = message.startswith("No converter registered")
                        stats.unsupported += int(unsupported)
                        stats.failed += int(not unsupported)
                        errors.append(ErrorRecord(source.relative_path, "convert", type(exc).__name__, message, source.sha256))
                        if settings.strict:
                            raise
                        continue
                    if (stamp_before.st_mtime_ns, stamp_before.st_size) != (
                        stamp_after.st_mtime_ns,
                        stamp_after.st_size,
                    ):
                        # The whole point of the ledger is that sha256 describes the bytes
                        # the stored Markdown came from. If the source was rewritten while
                        # it was being read, that guarantee no longer holds, so report the
                        # file instead of publishing a hash for text it never contained.
                        stats.failed += 1
                        errors.append(
                            ErrorRecord(
                                source.relative_path,
                                "convert",
                                "SourceChangedDuringRead",
                                "Source was modified while it was being converted; "
                                "its recorded hash would not describe the extracted text",
                                source.sha256,
                            )
                        )
                        if settings.strict:
                            raise RuntimeError(errors[-1].message)
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
                    # Writing one document can fail on its own (a Windows path over
                    # MAX_PATH, a permission problem, a full disk). That must isolate the
                    # document, not abandon the corpus and its incremental state.
                    try:
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        tmp = output_path.with_suffix(output_path.suffix + ".tmp")
                        tmp.write_text(full_md, encoding="utf-8", newline="\n")
                        tmp.replace(output_path)
                    except OSError as exc:
                        stats.failed += 1
                        errors.append(ErrorRecord(source.relative_path, "write", type(exc).__name__, str(exc), source.sha256))
                        if settings.strict:
                            raise
                        continue
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

        if full_scan:
            # Only a whole-tree scan knows the complete set of live documents; a
            # single-file run must never delete the rest of an existing corpus.
            self._prune_orphan_documents(output_root, {doc["output_path"] for doc in documents})

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
            # An unescaped destination breaks the link: a ")" in the filename closes it
            # early and a "#" turns the rest into a fragment, so documents/paren(1).txt.md
            # resolved to "documents/paren(1".
            target = quote(doc["output_path"], safe="/")
            label = doc["source_path"].replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
            lines.append(f"- [{label}]({target}) — `{doc['parser']}` — {doc['chunk_count']} chunks")
        atomic_write_text(output_root / "INDEX.md", "\n".join(lines) + "\n")

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
        atomic_write_text(output_root / "REPORT.md", "\n".join(lines) + "\n")
