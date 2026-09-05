from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

STATE_VERSION = 2
MAX_STATE_BYTES = 256 * 1024 * 1024


def load_state(output_root: Path) -> dict[str, Any]:
    path = output_root / ".brainforgemd" / "state.json"
    if not path.exists():
        return {"version": STATE_VERSION, "files": {}}
    try:
        if path.stat().st_size > MAX_STATE_BYTES:
            return {"version": STATE_VERSION, "files": {}}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, AttributeError):
        return {"version": STATE_VERSION, "files": {}}
    if (
        not isinstance(payload, dict)
        or payload.get("version") != STATE_VERSION
        or not isinstance(payload.get("files"), dict)
    ):
        return {"version": STATE_VERSION, "files": {}}
    return payload


def save_state(output_root: Path, state: dict[str, Any]) -> None:
    directory = output_root / ".brainforgemd"
    directory.mkdir(parents=True, exist_ok=True)
    # Per-process name: two runs sharing one output directory used to collide on
    # a single temporary file and abort with a rename error.
    tmp = directory / f"state.json.{os.getpid()}.tmp"
    final = directory / "state.json"
    tmp.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(final)
