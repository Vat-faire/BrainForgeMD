from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATE_VERSION = 1


def load_state(output_root: Path) -> dict[str, Any]:
    path = output_root / ".brainforgemd" / "state.json"
    if not path.exists():
        return {"version": STATE_VERSION, "files": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": STATE_VERSION, "files": {}}
    if payload.get("version") != STATE_VERSION or not isinstance(payload.get("files"), dict):
        return {"version": STATE_VERSION, "files": {}}
    return payload


def save_state(output_root: Path, state: dict[str, Any]) -> None:
    directory = output_root / ".brainforgemd"
    directory.mkdir(parents=True, exist_ok=True)
    tmp = directory / "state.json.tmp"
    final = directory / "state.json"
    tmp.write_text(json.dumps(state, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(final)
