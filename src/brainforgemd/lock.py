"""Single-writer guard for a corpus directory.

Two runs pointed at one output directory used to interleave silently and leave the
corpus inconsistent: rows in ``chunks.jsonl`` referencing sources absent from
``manifest.jsonl``, documents each run had pruned as the other one's orphans, and
``INDEX.md`` links to files that no longer existed. Nothing in the output contract can
hold under concurrent writers, so a second run is refused rather than allowed to
corrupt the first one's work.
"""

from __future__ import annotations

import contextlib
import json
import os
import socket
import time
from pathlib import Path
from types import TracebackType


class CorpusLocked(RuntimeError):
    """Raised when another BrainForgeMD run already owns this output directory."""


class CorpusLock:
    def __init__(self, output_root: Path) -> None:
        self.path = output_root / ".brainforgemd" / "lock"
        self._held = False

    def _describe_holder(self) -> str:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            started = payload.get("started_at", "an unknown time")
            return f"pid {payload.get('pid')} on {payload.get('host')} since {started}"
        except (OSError, json.JSONDecodeError):
            return "an unknown process"

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "pid": os.getpid(),
                "host": socket.gethostname(),
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            }
        )
        try:
            handle = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise CorpusLocked(
                f"Another BrainForgeMD run is using {self.path.parent.parent} "
                f"({self._describe_holder()}). Wait for it to finish, or delete "
                f"{self.path} if that run was interrupted."
            ) from None
        with os.fdopen(handle, "w", encoding="utf-8") as sink:
            sink.write(payload)
        self._held = True

    def release(self) -> None:
        if not self._held:
            return
        self._held = False
        with contextlib.suppress(OSError):
            self.path.unlink()

    def __enter__(self) -> CorpusLock:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.release()
