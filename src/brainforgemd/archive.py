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


def extract_archive(path: Path, destination: Path, limits: ArchiveLimits) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    total = 0
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > limits.max_files:
                raise ValueError(f"Archive contains {len(infos)} members; limit is {limits.max_files}")
            for info in infos:
                if info.is_dir():
                    continue
                total += info.file_size
                if total > limits.max_expanded_bytes:
                    raise ValueError("Archive expanded-size limit exceeded")
                target = _safe_target(destination, info.filename)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as sink:
                    shutil.copyfileobj(source, sink)
                files.append(target)
        return files
    if tarfile.is_tarfile(path):
        with tarfile.open(path, "r:*") as archive:
            members = [m for m in archive.getmembers() if m.isfile()]
            if len(members) > limits.max_files:
                raise ValueError(f"Archive contains {len(members)} files; limit is {limits.max_files}")
            for member in members:
                total += member.size
                if total > limits.max_expanded_bytes:
                    raise ValueError("Archive expanded-size limit exceeded")
                target = _safe_target(destination, member.name)
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    continue
                with source, target.open("wb") as sink:
                    shutil.copyfileobj(source, sink)
                files.append(target)
        return files
    raise ValueError(f"Unsupported archive: {path.name}")
