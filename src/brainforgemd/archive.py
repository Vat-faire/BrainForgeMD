from __future__ import annotations

import os
import shutil
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ARCHIVE_SUFFIXES = (".zip", ".tar", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz")


@dataclass(slots=True)
class ArchiveLimits:
    max_depth: int = 3
    max_files: int = 5000
    max_expanded_bytes: int = 2 * 1024 * 1024 * 1024


@dataclass(slots=True)
class ArchiveBudget:
    """Run-wide extraction allowance.

    The limits used to be applied per archive, so every nested archive received a
    fresh allowance and the totals multiplied with depth: a 7 KB nested ZIP expanded
    into a 115 MB corpus. A single budget threaded through the whole run bounds the
    real cost instead of the cost of one container.
    """

    max_files: int
    max_expanded_bytes: int
    files_used: int = 0
    bytes_used: int = 0

    def take_file(self, name: str) -> None:
        self.files_used += 1
        if self.files_used > self.max_files:
            raise ValueError(
                f"Archive member budget exhausted at {self.max_files} files (while reading {name})"
            )

    def take_bytes(self, size: int, name: str) -> None:
        self.bytes_used += size
        if self.bytes_used > self.max_expanded_bytes:
            raise ValueError(
                f"Archive expanded-size budget exhausted at {self.max_expanded_bytes} bytes "
                f"(while reading {name})"
            )


def is_archive(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in ARCHIVE_SUFFIXES)


def _safe_target(root: Path, member_name: str) -> Path:
    # Archive member names are logically POSIX paths. Normalize backslashes too so
    # a Windows-style traversal payload is rejected on every host OS. Avoid
    # Path.resolve() here: macOS /var aliases and Windows 8.3 aliases can make
    # equivalent paths stringify differently and produce false traversal errors.
    normalized = member_name.replace("\\", "/")
    member = PurePosixPath(normalized)
    parts = [part for part in member.parts if part not in {"", "."}]
    if member.is_absolute() or any(part == ".." for part in parts):
        raise ValueError(f"Archive path traversal rejected: {member_name}")
    if parts and ":" in parts[0]:
        raise ValueError(f"Archive absolute/drive path rejected: {member_name}")

    target = root.joinpath(*parts)
    root_abs = os.path.normcase(os.path.abspath(root))
    target_abs = os.path.normcase(os.path.abspath(target))
    try:
        common = os.path.commonpath([root_abs, target_abs])
    except ValueError as exc:
        raise ValueError(f"Archive path traversal rejected: {member_name}") from exc
    if common != root_abs:
        raise ValueError(f"Archive path traversal rejected: {member_name}")
    return target


def _write_member(target: Path, source, name: str) -> None:
    """Copy one member out, turning host filesystem rejections into the ValueError that
    callers of this module already expect. A member name that is legal in the archive
    but illegal on the host (trailing dots on Windows, for instance) used to escape as
    a bare OSError."""
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as sink:
            shutil.copyfileobj(source, sink)
    except OSError as exc:
        raise ValueError(f"Archive member cannot be written on this host: {name} ({exc})") from exc


def extract_archive(
    path: Path,
    destination: Path,
    limits: ArchiveLimits,
    budget: ArchiveBudget | None = None,
) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    if budget is None:
        budget = ArchiveBudget(limits.max_files, limits.max_expanded_bytes)
    files: list[Path] = []
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > limits.max_files:
                raise ValueError(f"Archive contains {len(infos)} members; limit is {limits.max_files}")
            for info in infos:
                if info.is_dir():
                    continue
                budget.take_file(info.filename)
                budget.take_bytes(info.file_size, info.filename)
                target = _safe_target(destination, info.filename)
                with archive.open(info) as source:
                    _write_member(target, source, info.filename)
                files.append(target)
        return files
    if tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as archive:
            members = [m for m in archive.getmembers() if m.isfile()]
            if len(members) > limits.max_files:
                raise ValueError(f"Archive contains {len(members)} files; limit is {limits.max_files}")
            for member in members:
                budget.take_file(member.name)
                budget.take_bytes(member.size, member.name)
                target = _safe_target(destination, member.name)
                source = archive.extractfile(member)
                if source is None:
                    continue
                with source:
                    _write_member(target, source, member.name)
                files.append(target)
        return files
    raise ValueError(f"Unsupported archive: {path.name}")
