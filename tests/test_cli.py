from __future__ import annotations

from pathlib import Path

from codexopt.benchmark import load_evidence
from codexopt.benchmark import run_benchmark
from codexopt.artifacts import write_json
from codexopt.config import CodexOptConfig
from codexopt.config import load_config
from codexopt.optimizer import optimize_entries
from codexopt.reporter import build_markdown_report
from codexopt.scanner import scan_project
from codexopt.cli import main


def test_cli_end_to_end(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text(("Agent rules. " * 50).strip() + "\n", encoding="utf-8")
    skill_dir = tmp_path / ".codex" / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("Do X then Y.\n", encoding="utf-8")

    assert main(["init"]) == 0
    assert main(["scan"]) == 0
    assert main(["benchmark"]) == 0
    assert main(["optimize", "skills"]) == 0
    assert main(["apply", "--kind", "skills", "--dry-run"]) == 0
    assert main(["report", "--output", "codexopt-report.md"]) == 0
    assert (tmp_path / "codexopt-report.md").exists()


def test_apply_without_optimization_run_returns_2(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    assert main(["apply", "--kind", "agents"]) == 2


def test_benchmark_uses_task_and_issue_evidence(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "# Team Agent Playbook\n\nKeep answers short.\nPrefer minimal edits.\n",
        encoding="utf-8",
    )
    skill_dir = tmp_path / ".codex" / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text("Use this skill for bug triage.\n", encoding="utf-8")
    (tmp_path / "tasks.md").write_text(
        "1. Add tests for malformed dates.\n2. Improve report ordering.\n",
        encoding="utf-8",
    )
    (tmp_path / "issues.md").write_text(
        "- Agents skip tests.\n- Output format drifts.\n",
        encoding="utf-8",
    )
    (tmp_path / "codexopt.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "evidence:",
                "  task_files:",
                "    - tasks.md",
                "  issue_files:",
                "    - issues.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cfg, _ = load_config(tmp_path / "codexopt.yaml")
    scan_result = scan_project(tmp_path, cfg)
    evidence = load_evidence(tmp_path, cfg)
    benchmark_result = run_benchmark(scan_result, evidence=evidence)

    assert benchmark_result["evidence"]["task_paths"]
    assert benchmark_result["evidence"]["issue_paths"]
    agents_result = next(item for item in benchmark_result["files"] if item["kind"] == "agents")
    assert "feedback" in agents_result["details"]
    assert "criteria_scores" in agents_result["details"]


def test_gepa_fallback_is_recorded(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    agents_path = tmp_path / "AGENTS.md"
    agents_path.write_text("Keep answers short.\nKeep answers short.\n", encoding="utf-8")
    cfg = CodexOptConfig()
    scan_result = scan_project(tmp_path, cfg)

    def fail_gepa(*args: object, **kwargs: object) -> object:
        raise RuntimeError("reflection model unavailable")

    monkeypatch.setattr("codexopt.optimizer._optimize_with_gepa", fail_gepa)
    result = optimize_entries(
        entries=scan_result["entries"],
        kind="agents",
        engine="gepa",
        min_delta=0.01,
        reflection_model="dummy/model",
        max_metric_calls=2,
        evidence={},
    )

    assert result["fallback_count"] == 1
    file_result = result["results"][0]
    assert file_result["actual_engine"] == "heuristic_fallback"
    assert "reflection model unavailable" in str(file_result["fallback_reason"])


def test_report_shows_requested_engine_and_fallback_count(tmp_path: Path) -> None:
    output_root = tmp_path / ".codexopt"
    run_dir = output_root / "runs" / "demo-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        run_dir / "optimize.json",
        {
            "kind": "agents",
            "engine": "gepa",
            "requested_engine": "gepa",
            "fallback_count": 1,
            "files_total": 1,
            "files_improved": 1,
            "average_delta": 0.12,
            "results": [],
        },
    )
    write_json(output_root / "state.json", {"latest_optimize_agents_run": "demo-run"})

    report = build_markdown_report(output_root)

    assert "- requested engine: gepa" in report
    assert "- GEPA fallback count: 1" in report
