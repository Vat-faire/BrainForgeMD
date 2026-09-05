from __future__ import annotations

import contextlib
import os
import shutil
import uuid
from pathlib import Path


class CorpusTransaction:
    """Stage and publish a corpus generation with rollback on replacement failure."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        transaction_root = self.root / ".brainforgemd" / "transactions"
        transaction_root.mkdir(parents=True, exist_ok=True)
        self.work = transaction_root / f"{os.getpid()}-{uuid.uuid4().hex}"
        self.staged = self.work / "staged"
        self.backup = self.work / "backup"
        self.staged.mkdir(parents=True)
        self._preserve_recovery = False

    def _relative(self, target: Path) -> Path:
        clean_transaction = True
        try:
            return target.absolute().relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"Transaction target escapes corpus: {target}") from exc

    def stage_path(self, target: Path) -> Path:
        path = self.staged / self._relative(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def stage_text(self, target: Path, text: str) -> None:
        self.stage_path(target).write_text(text, encoding="utf-8", newline="\n")

    def commit(self, deletions: list[Path] | None = None) -> None:
        staged = {
            path.relative_to(self.staged): path
            for path in self.staged.rglob("*")
            if path.is_file()
        }
        delete_relatives = {
            self._relative(path) for path in (deletions or []) if self._relative(path) not in staged
        }
        affected = sorted(set(staged) | delete_relatives, key=lambda path: path.as_posix())
        moved: list[tuple[Path, Path | None]] = []
        try:
            for relative in affected:
                target = self.root / relative
                backup = self.backup / relative
                previous: Path | None = None
                if os.path.lexists(target):
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    target.replace(backup)
                    previous = backup
                moved.append((target, previous))
                staged_path = staged.get(relative)
                if staged_path is not None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    staged_path.replace(target)
        except BaseException as commit_error:
            rollback_errors: list[str] = []
            for target, previous in reversed(moved):
                with contextlib.suppress(OSError):
                    if os.path.lexists(target):
                        target.unlink()
                if previous is not None and os.path.lexists(previous):
                    try:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        previous.replace(target)
                    except OSError as exc:
                        rollback_errors.append(f"{target}: {exc}")
            if rollback_errors:
                clean_transaction = False
                self._preserve_recovery = True
                raise RuntimeError(
                    f"Corpus commit and rollback failed; recovery files are preserved in "
                    f"{self.backup}: {'; '.join(rollback_errors)}"
                ) from commit_error
            raise
        finally:
            if clean_transaction:
                self.abort()

    def abort(self) -> None:
        if not self._preserve_recovery:
            shutil.rmtree(self.work, ignore_errors=True)

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.abort()
