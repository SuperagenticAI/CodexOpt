from __future__ import annotations

import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


STATE_FILENAME = "state.json"


def ensure_output_dirs(root_dir: Path) -> None:
    (root_dir / "runs").mkdir(parents=True, exist_ok=True)
    (root_dir / "backups").mkdir(parents=True, exist_ok=True)


def load_state(root_dir: Path) -> dict[str, Any]:
    state_path = root_dir / STATE_FILENAME
    if not state_path.exists():
        return {}
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(root_dir: Path, state: dict[str, Any]) -> None:
    state_path = root_dir / STATE_FILENAME
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def new_run_dir(root_dir: Path, kind: str) -> tuple[str, Path]:
    ensure_output_dirs(root_dir)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_id = f"{stamp}-{kind}"
    run_dir = root_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_id, run_dir


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def set_latest_run(root_dir: Path, state_key: str, run_id: str) -> None:
    state = load_state(root_dir)
    state[state_key] = run_id
    save_state(root_dir, state)


def resolve_run_id(root_dir: Path, state_key: str, explicit_run_id: str | None) -> str | None:
    if explicit_run_id:
        return explicit_run_id
    state = load_state(root_dir)
    value = state.get(state_key)
    if isinstance(value, str):
        return value
    return None
