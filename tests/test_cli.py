from __future__ import annotations

from pathlib import Path

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
