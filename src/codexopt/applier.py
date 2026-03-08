from __future__ import annotations

from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any


def apply_optimization_result(
    optimization_result: dict[str, Any],
    repo_root: Path,
    backup_root: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = backup_root / timestamp
    applied: list[str] = []
    skipped: list[str] = []

    if not dry_run:
        backup_dir.mkdir(parents=True, exist_ok=True)

    for item in optimization_result.get("results", []):
        path = Path(item["path"])
        if item.get("delta", 0.0) <= 0.0:
            skipped.append(f"{path} (no improvement)")
            continue
        if not path.exists():
            skipped.append(f"{path} (missing)")
            continue

        new_content = str(item.get("best_content", ""))
        current = path.read_text(encoding="utf-8", errors="replace")
        if current == new_content:
            skipped.append(f"{path} (no changes)")
            continue

        if dry_run:
            applied.append(str(path))
            continue

        try:
            rel = path.resolve().relative_to(repo_root.resolve())
        except Exception:
            rel = Path(path.name)
        backup_path = backup_dir / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(current, encoding="utf-8")
        path.write_text(new_content, encoding="utf-8")
        applied.append(str(path))

    return {
        "dry_run": dry_run,
        "backup_dir": str(backup_dir),
        "applied_count": len(applied),
        "skipped_count": len(skipped),
        "applied": applied,
        "skipped": skipped,
    }


def print_apply_summary(result: dict[str, Any]) -> None:
    print(f"dry_run: {result['dry_run']}")
    print(f"applied_count: {result['applied_count']}")
    print(f"skipped_count: {result['skipped_count']}")
    if not result["dry_run"]:
        print(f"backup_dir: {result['backup_dir']}")
    for item in result["applied"]:
        print(f"- applied: {item}")
    for item in result["skipped"]:
        print(f"- skipped: {item}")
