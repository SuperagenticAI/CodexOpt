from __future__ import annotations

from typing import Any

from .types import FileScore


def _score_agents(entry: dict[str, Any]) -> FileScore:
    score = 1.0
    issues: list[str] = []
    details: dict[str, Any] = {}
    words = int(entry.get("words", 0))
    tokens = int(entry.get("token_estimate", 0))

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

    details["words"] = words
    details["token_estimate"] = tokens
    return FileScore(
        path=entry["path"],
        kind="agents",
        score=max(0.0, min(1.0, score)),
        issues=issues,
        details=details,
    )


def _score_skill(entry: dict[str, Any]) -> FileScore:
    score = 1.0
    issues: list[str] = []
    details: dict[str, Any] = {}
    words = int(entry.get("words", 0))
    entry_issues = set(entry.get("issues", []))

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

    details["words"] = words
    details["frontmatter_present"] = entry.get("metadata", {}).get("frontmatter_present", False)
    return FileScore(
        path=entry["path"],
        kind="skill",
        score=max(0.0, min(1.0, score)),
        issues=issues,
        details=details,
    )


def score_entry(entry: dict[str, Any]) -> FileScore:
    kind = entry.get("kind")
    if kind == "agents":
        return _score_agents(entry)
    return _score_skill(entry)


def run_benchmark(scan_result: dict[str, Any]) -> dict[str, Any]:
    scores: list[FileScore] = [score_entry(entry) for entry in scan_result["entries"]]
    if scores:
        overall = sum(item.score for item in scores) / len(scores)
    else:
        overall = 0.0

    return {
        "counts": scan_result["counts"],
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
    for file_result in result["files"]:
        issues = ", ".join(file_result["issues"]) if file_result["issues"] else "ok"
        print(f"- {file_result['kind']}: {file_result['path']}")
        print(f"  score={file_result['score']:.4f} issues={issues}")
