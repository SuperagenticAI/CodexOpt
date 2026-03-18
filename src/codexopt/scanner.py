from __future__ import annotations

import fnmatch
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from .config import CodexOptConfig
from .quality import analyze_instruction_text
from .types import ScanEntry


def _is_excluded(path: Path, root: Path, exclude_globs: list[str]) -> bool:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return True
    return any(fnmatch.fnmatch(rel, pattern) for pattern in exclude_globs)


def _extract_frontmatter(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    if not lines:
        return None
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return None
    return "\n".join(lines[1:end]).strip()


def _parse_skill_frontmatter(frontmatter: str) -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    parsed: dict[str, Any] = {}
    if not frontmatter:
        return parsed, ["missing_frontmatter"]
    if yaml is not None:
        try:
            parsed = yaml.safe_load(frontmatter) or {}
        except Exception as exc:
            return {}, [f"invalid_yaml:{exc}"]
    else:
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()

    name = str(parsed.get("name", "")).strip()
    description = str(parsed.get("description", "")).strip()
    if not name:
        issues.append("missing_name")
    if not description:
        issues.append("missing_description")
    if len(name) > 64:
        issues.append("name_too_long")
    if len(description) > 1024:
        issues.append("description_too_long")
    return parsed, issues


def _build_entry(path: Path, kind: str) -> ScanEntry:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    words = len(text.split())
    token_est = int(words * 1.33)
    issues: list[str] = []
    metadata: dict[str, Any] = {}
    metadata.update(analyze_instruction_text(text))

    if kind == "skill":
        frontmatter = _extract_frontmatter(text)
        parsed, fm_issues = _parse_skill_frontmatter(frontmatter or "")
        issues.extend(fm_issues)
        metadata["frontmatter"] = parsed
        metadata["frontmatter_present"] = frontmatter is not None
        metadata["has_body"] = bool(text.strip())

    if kind == "agents":
        if not text.strip():
            issues.append("empty_agents")
        if token_est > 6000:
            issues.append("agents_too_large")
        if metadata.get("contradictions"):
            issues.append("contradictory_guidance")
        if metadata.get("duplicate_nonempty_line_count", 0) > 0:
            issues.append("duplicate_lines")

    return ScanEntry(
        path=str(path),
        kind=kind,
        bytes=path.stat().st_size,
        lines=len(lines),
        words=words,
        token_estimate=token_est,
        issues=issues,
        metadata=metadata,
    )


def scan_project(
    cwd: Path,
    config: CodexOptConfig,
    agents_files: list[str] | None = None,
    skills_globs: list[str] | None = None,
) -> dict[str, Any]:
    agent_patterns = agents_files or config.targets.agents_files
    skill_patterns = skills_globs or config.targets.skills_globs
    exclude = config.targets.exclude_globs

    found_agents: set[Path] = set()
    found_skills: set[Path] = set()

    for pattern in agent_patterns:
        for path in cwd.glob(pattern):
            if path.is_file() and not _is_excluded(path, cwd, exclude):
                found_agents.add(path.resolve())

    for pattern in skill_patterns:
        for path in cwd.glob(pattern):
            if path.is_file() and path.name == "SKILL.md" and not _is_excluded(path, cwd, exclude):
                found_skills.add(path.resolve())

    entries: list[ScanEntry] = []
    for path in sorted(found_agents):
        entries.append(_build_entry(path, "agents"))
    for path in sorted(found_skills):
        entries.append(_build_entry(path, "skill"))

    return {
        "cwd": str(cwd),
        "counts": {
            "agents": sum(1 for item in entries if item.kind == "agents"),
            "skills": sum(1 for item in entries if item.kind == "skill"),
            "issues": sum(len(item.issues) for item in entries),
        },
        "entries": [
            {
                "path": item.path,
                "kind": item.kind,
                "bytes": item.bytes,
                "lines": item.lines,
                "words": item.words,
                "token_estimate": item.token_estimate,
                "issues": item.issues,
                "metadata": item.metadata,
            }
            for item in entries
        ],
    }


def print_scan_summary(result: dict[str, Any]) -> None:
    counts = result["counts"]
    print(f"agents: {counts['agents']}")
    print(f"skills: {counts['skills']}")
    print(f"issues: {counts['issues']}")
    for entry in result["entries"]:
        issues = ", ".join(entry["issues"]) if entry["issues"] else "ok"
        print(f"- {entry['kind']}: {entry['path']} [{issues}]")
