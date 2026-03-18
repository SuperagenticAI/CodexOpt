from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import read_json
from .artifacts import resolve_run_id


def _load_optional_run(
    root_dir: Path,
    state_key: str,
    preferred_filename: str,
) -> tuple[str, dict[str, Any]] | None:
    run_id = resolve_run_id(root_dir, state_key, None)
    if not run_id:
        return None
    run_dir = root_dir / "runs" / run_id
    if not run_dir.exists():
        return None
    preferred = run_dir / preferred_filename
    if preferred.exists():
        return run_id, read_json(preferred)
    for fallback in ["scan.json", "benchmark.json", "optimize.json", "apply.json"]:
        p = run_dir / fallback
        if p.exists():
            return run_id, read_json(p)
    return None


def build_markdown_report(root_dir: Path) -> str:
    scan = _load_optional_run(root_dir, "latest_scan_run", "scan.json")
    benchmark = _load_optional_run(root_dir, "latest_benchmark_run", "benchmark.json")
    opt_agents = _load_optional_run(root_dir, "latest_optimize_agents_run", "optimize.json")
    opt_skills = _load_optional_run(root_dir, "latest_optimize_skills_run", "optimize.json")
    apply = _load_optional_run(root_dir, "latest_apply_run", "apply.json")

    lines: list[str] = ["# codexopt report", ""]
    if scan:
        run_id, data = scan
        lines.extend(
            [
                "## scan",
                f"- run: `{run_id}`",
                f"- agents: {data['counts']['agents']}",
                f"- skills: {data['counts']['skills']}",
                f"- issues: {data['counts']['issues']}",
                "",
            ]
        )
    if benchmark:
        run_id, data = benchmark
        evidence = data.get("evidence", {})
        lines.extend(
            [
                "## benchmark",
                f"- run: `{run_id}`",
                f"- overall score: {data['overall_score']}",
                f"- task files: {len(evidence.get('task_paths', []))}",
                f"- issue files: {len(evidence.get('issue_paths', []))}",
                "",
            ]
        )
        top_feedback: list[str] = []
        for file_result in data.get("files", []):
            top_feedback.extend(file_result.get("details", {}).get("feedback", [])[:1])
        if top_feedback:
            lines.append("### feedback highlights")
            for item in top_feedback[:5]:
                lines.append(f"- {item}")
            lines.append("")
    if opt_agents:
        run_id, data = opt_agents
        lines.extend(
            [
                "## optimize agents",
                f"- run: `{run_id}`",
                f"- requested engine: {data.get('requested_engine', data.get('engine', 'unknown'))}",
                f"- GEPA fallback count: {data.get('fallback_count', 0)}",
                f"- files improved: {data['files_improved']}/{data['files_total']}",
                f"- average delta: {data['average_delta']}",
                "",
            ]
        )
    if opt_skills:
        run_id, data = opt_skills
        lines.extend(
            [
                "## optimize skills",
                f"- run: `{run_id}`",
                f"- requested engine: {data.get('requested_engine', data.get('engine', 'unknown'))}",
                f"- GEPA fallback count: {data.get('fallback_count', 0)}",
                f"- files improved: {data['files_improved']}/{data['files_total']}",
                f"- average delta: {data['average_delta']}",
                "",
            ]
        )
    if apply:
        run_id, data = apply
        lines.extend(
            [
                "## apply",
                f"- run: `{run_id}`",
                f"- applied: {data['applied_count']}",
                f"- skipped: {data['skipped_count']}",
                "",
            ]
        )
    if len(lines) == 2:
        lines.append("No runs found.")
    return "\n".join(lines).rstrip() + "\n"
