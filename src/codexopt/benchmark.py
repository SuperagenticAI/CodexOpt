from __future__ import annotations

from pathlib import Path
from typing import Any

from .types import FileScore
from .quality import build_feedback
from .quality import extract_keywords
from .quality import load_issue_texts
from .quality import load_task_statements
from .quality import resolve_evidence_paths
from .quality import summarize_text_themes
from .quality import task_keyword_coverage


def load_evidence(cwd: Any, config: Any) -> dict[str, Any]:
    task_paths = resolve_evidence_paths(cwd, list(getattr(config.evidence, "task_files", [])))
    issue_paths = resolve_evidence_paths(cwd, list(getattr(config.evidence, "issue_files", [])))
    task_statements = load_task_statements(task_paths)
    issue_texts = load_issue_texts(issue_paths)
    return {
        "task_paths": [str(path) for path in task_paths],
        "issue_paths": [str(path) for path in issue_paths],
        "task_statements": task_statements,
        "task_keywords": extract_keywords(task_statements),
        "task_themes": summarize_text_themes(task_statements),
        "issue_themes": summarize_text_themes(issue_texts),
    }


def _load_entry_text(entry: dict[str, Any]) -> str:
    if isinstance(entry.get("text"), str):
        return str(entry["text"])
    path = Path(str(entry.get("path", "")))
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _score_agents(entry: dict[str, Any], evidence: dict[str, Any] | None = None) -> FileScore:
    score = 1.0
    issues: list[str] = []
    details: dict[str, Any] = {}
    words = int(entry.get("words", 0))
    tokens = int(entry.get("token_estimate", 0))
    metadata = dict(entry.get("metadata", {}))
    flags = dict(metadata.get("instruction_flags", {}))
    contradictions = list(metadata.get("contradictions", []))
    duplicate_count = int(metadata.get("duplicate_nonempty_line_count", 0))
    evidence = evidence or {}
    task_coverage = task_keyword_coverage(_load_entry_text(entry), evidence.get("task_keywords", []))

    if words < 80:
        score -= 0.2
        issues.append("too_short")
    if words > 2400:
        score -= min(0.35, (words - 2400) / 10000.0)
        issues.append("too_long")
    if tokens > 7000:
        score -= 0.15
        issues.append("token_heavy")
    if "empty_agents" in entry.get("issues", []):
        score -= 0.6
        issues.append("empty")
    if contradictions:
        score -= min(0.25, 0.08 * len(contradictions))
        issues.append("contradictions")
    if duplicate_count:
        score -= min(0.12, 0.03 * duplicate_count)
        issues.append("duplicate_lines")
    if not flags.get("has_role"):
        score -= 0.08
        issues.append("missing_role")
    if not flags.get("has_constraints"):
        score -= 0.1
        issues.append("missing_constraints")
    if not flags.get("has_workflow"):
        score -= 0.1
        issues.append("missing_workflow")
    if not flags.get("has_verification"):
        score -= 0.14
        issues.append("missing_verification")
    if not flags.get("has_output_contract"):
        score -= 0.08
        issues.append("missing_output_contract")
    if not flags.get("has_repo_context"):
        score -= 0.06
        issues.append("missing_repo_context")
    if task_coverage < 0.2 and evidence.get("task_keywords"):
        score -= 0.08
        issues.append("weak_task_alignment")

    details["words"] = words
    details["token_estimate"] = tokens
    details["criteria_scores"] = {
        "clarity": round(max(0.0, 1.0 - (0.16 if contradictions else 0.0) - (0.05 if duplicate_count else 0.0)), 4),
        "safety": round(max(0.0, 1.0 - (0.2 if not flags.get("has_constraints") else 0.0)), 4),
        "workflow": round(max(0.0, 1.0 - (0.18 if not flags.get("has_workflow") else 0.0)), 4),
        "verification": round(max(0.0, 1.0 - (0.22 if not flags.get("has_verification") else 0.0)), 4),
        "output_contract": round(max(0.0, 1.0 - (0.18 if not flags.get("has_output_contract") else 0.0)), 4),
        "repo_specificity": round(max(0.0, 0.5 + min(task_coverage, 0.5) - (0.1 if not flags.get("has_repo_context") else 0.0)), 4),
        "token_efficiency": round(max(0.0, min(1.0, 1.0 - max(0, words - 2400) / 4000.0)), 4),
    }
    details["task_keyword_coverage"] = round(task_coverage, 4)
    details["feedback"] = build_feedback(
        kind="agents",
        metadata=metadata,
        task_themes=evidence.get("task_themes", {}),
        issue_themes=evidence.get("issue_themes", {}),
        task_coverage=task_coverage,
    )
    return FileScore(
        path=entry["path"],
        kind="agents",
        score=max(0.0, min(1.0, score)),
        issues=issues,
        details=details,
    )


def _score_skill(entry: dict[str, Any], evidence: dict[str, Any] | None = None) -> FileScore:
    score = 1.0
    issues: list[str] = []
    details: dict[str, Any] = {}
    words = int(entry.get("words", 0))
    entry_issues = set(entry.get("issues", []))
    metadata = dict(entry.get("metadata", {}))
    flags = dict(metadata.get("instruction_flags", {}))
    duplicate_count = int(metadata.get("duplicate_nonempty_line_count", 0))
    evidence = evidence or {}
    task_coverage = task_keyword_coverage(_load_entry_text(entry), evidence.get("task_keywords", []))

    if "missing_frontmatter" in entry_issues:
        score -= 0.6
        issues.append("missing_frontmatter")
    if "missing_name" in entry_issues:
        score -= 0.2
        issues.append("missing_name")
    if "missing_description" in entry_issues:
        score -= 0.2
        issues.append("missing_description")
    if "name_too_long" in entry_issues:
        score -= 0.15
        issues.append("name_too_long")
    if "description_too_long" in entry_issues:
        score -= 0.15
        issues.append("description_too_long")
    if words < 40:
        score -= 0.15
        issues.append("too_short")
    if words > 1800:
        score -= min(0.25, (words - 1800) / 10000.0)
        issues.append("too_long")
    if duplicate_count:
        score -= min(0.12, 0.03 * duplicate_count)
        issues.append("duplicate_lines")
    if not flags.get("has_trigger_phrase"):
        score -= 0.1
        issues.append("missing_trigger")
    if not flags.get("has_workflow"):
        score -= 0.08
        issues.append("missing_workflow")
    if not flags.get("has_verification"):
        score -= 0.1
        issues.append("missing_verification")
    if task_coverage < 0.15 and evidence.get("task_keywords"):
        score -= 0.06
        issues.append("weak_task_alignment")

    details["words"] = words
    details["frontmatter_present"] = entry.get("metadata", {}).get("frontmatter_present", False)
    details["criteria_scores"] = {
        "metadata": round(max(0.0, 1.0 - (0.3 if "missing_frontmatter" in entry_issues else 0.0)), 4),
        "trigger_clarity": round(max(0.0, 1.0 - (0.2 if not flags.get("has_trigger_phrase") else 0.0)), 4),
        "workflow": round(max(0.0, 1.0 - (0.16 if not flags.get("has_workflow") else 0.0)), 4),
        "verification": round(max(0.0, 1.0 - (0.2 if not flags.get("has_verification") else 0.0)), 4),
        "token_efficiency": round(max(0.0, min(1.0, 1.0 - max(0, words - 1800) / 3000.0)), 4),
        "repo_specificity": round(max(0.0, 0.5 + min(task_coverage, 0.5)), 4),
    }
    details["task_keyword_coverage"] = round(task_coverage, 4)
    details["feedback"] = build_feedback(
        kind="skill",
        metadata=metadata,
        task_themes=evidence.get("task_themes", {}),
        issue_themes=evidence.get("issue_themes", {}),
        task_coverage=task_coverage,
    )
    return FileScore(
        path=entry["path"],
        kind="skill",
        score=max(0.0, min(1.0, score)),
        issues=issues,
        details=details,
    )


def score_entry(entry: dict[str, Any], evidence: dict[str, Any] | None = None) -> FileScore:
    kind = entry.get("kind")
    if kind == "agents":
        return _score_agents(entry, evidence=evidence)
    return _score_skill(entry, evidence=evidence)


def run_benchmark(scan_result: dict[str, Any], evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    scores: list[FileScore] = [score_entry(entry, evidence=evidence) for entry in scan_result["entries"]]
    if scores:
        overall = sum(item.score for item in scores) / len(scores)
    else:
        overall = 0.0

    return {
        "counts": scan_result["counts"],
        "evidence": evidence or {},
        "overall_score": round(overall, 4),
        "files": [
            {
                "path": item.path,
                "kind": item.kind,
                "score": round(item.score, 4),
                "issues": item.issues,
                "details": item.details,
            }
            for item in scores
        ],
    }


def print_benchmark_summary(result: dict[str, Any]) -> None:
    print(f"overall_score: {result['overall_score']:.4f}")
    evidence = result.get("evidence", {})
    if evidence.get("task_paths"):
        print(f"task_files: {len(evidence['task_paths'])}")
    if evidence.get("issue_paths"):
        print(f"issue_files: {len(evidence['issue_paths'])}")
    for file_result in result["files"]:
        issues = ", ".join(file_result["issues"]) if file_result["issues"] else "ok"
        print(f"- {file_result['kind']}: {file_result['path']}")
        print(f"  score={file_result['score']:.4f} issues={issues}")
