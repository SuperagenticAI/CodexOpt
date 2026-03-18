from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "planning": ("plan", "planning", "think", "workflow", "sequence"),
    "context": ("context", "repository", "repo", "codebase", "file", "path"),
    "tooling": ("tool", "command", "shell", "cli", "script"),
    "verification": ("test", "tests", "verify", "validation", "regression", "check"),
    "format": ("format", "output", "response", "json", "markdown", "schema"),
    "safety": ("safe", "safety", "destructive", "permission", "overwrite", "secret"),
    "review": ("review", "risk", "finding", "regression"),
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "if",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "so",
    "that",
    "the",
    "their",
    "then",
    "this",
    "to",
    "use",
    "when",
    "with",
    "without",
    "your",
}

CONTRADICTION_RULES: tuple[tuple[str, tuple[str, str]], ...] = (
    (
        "response_length_conflict",
        ("keep answers short", "keep answers very detailed"),
    ),
    (
        "edit_scope_conflict",
        ("prefer minimal edits", "prefer broad refactors"),
    ),
    (
        "workflow_conflict",
        ("change code immediately", "plan before changing code"),
    ),
    (
        "reading_conflict",
        ("read files quickly", "read files thoroughly"),
    ),
)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_evidence_paths(cwd: Path, patterns: list[str]) -> list[Path]:
    found: set[Path] = set()
    for pattern in patterns:
        for path in cwd.glob(pattern):
            if path.is_file():
                found.add(path.resolve())
    return sorted(found)


def load_task_statements(paths: list[Path]) -> list[str]:
    statements: list[str] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".json":
            try:
                payload = json.loads(_read_text(path))
            except Exception:
                continue
            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, str) and item.strip():
                        statements.append(item.strip())
                    elif isinstance(item, dict):
                        title = str(item.get("title", "")).strip()
                        desc = str(item.get("description", "")).strip()
                        text = ": ".join(part for part in (title, desc) if part)
                        if text:
                            statements.append(text)
            continue

        for raw_line in _read_text(path).splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if re.match(r"^\d+\.\s+", line):
                statements.append(re.sub(r"^\d+\.\s+", "", line).strip())
                continue
            if re.match(r"^[-*]\s+", line):
                statements.append(re.sub(r"^[-*]\s+", "", line).strip())
    return statements


def load_issue_texts(paths: list[Path]) -> list[str]:
    texts: list[str] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix in {".md", ".txt"}:
            texts.append(_read_text(path))
            continue
        if suffix != ".json":
            continue
        try:
            payload = json.loads(_read_text(path))
        except Exception:
            continue

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in {"title", "body", "name", "summary"} and isinstance(item, str):
                        texts.append(item)
                    else:
                        walk(item)
            elif isinstance(value, list):
                for item in value:
                    walk(item)

        walk(payload)
    return texts


def summarize_text_themes(texts: list[str]) -> dict[str, int]:
    joined = "\n".join(texts).lower()
    themes: dict[str, int] = {}
    for theme, keywords in THEME_KEYWORDS.items():
        count = sum(joined.count(keyword) for keyword in keywords)
        if count:
            themes[theme] = count
    return themes


def extract_keywords(texts: list[str], limit: int = 24) -> list[str]:
    counter: Counter[str] = Counter()
    for text in texts:
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", text.lower()):
            if token in STOPWORDS:
                continue
            counter[token] += 1
    return [word for word, _count in counter.most_common(limit)]


def analyze_instruction_text(text: str) -> dict[str, Any]:
    normalized = text.lower()
    nonempty_lines = [line.strip() for line in text.splitlines() if line.strip()]
    counts = Counter(nonempty_lines)
    repeated_lines = sorted(line for line, count in counts.items() if count > 1)

    flags = {
        "has_role": any(token in normalized for token in ("you are", "assistant", "agent", "playbook")),
        "has_constraints": any(
            token in normalized
            for token in ("must", "must not", "never", "do not", "avoid", "prefer", "always")
        ),
        "has_workflow": any(
            token in normalized for token in ("workflow", "step", "steps", "first", "then", "before")
        ),
        "has_verification": any(
            token in normalized for token in ("test", "tests", "verify", "validation", "check")
        ),
        "has_output_contract": any(
            token in normalized for token in ("output", "response", "format", "markdown", "json", "summary")
        ),
        "has_repo_context": any(
            token in normalized for token in ("repository", "repo", "codebase", "file", "path")
        ),
        "has_examples": "example" in normalized or "for example" in normalized,
        "has_trigger_phrase": any(
            token in normalized
            for token in ("use this skill when", "use this skill for", "when the user asks", "trigger")
        ),
    }

    contradictions = [
        name for name, (left, right) in CONTRADICTION_RULES if left in normalized and right in normalized
    ]

    return {
        "heading_count": len(re.findall(r"(?m)^#{1,6}\s+", text)),
        "bullet_count": len(re.findall(r"(?m)^\s*(?:[-*]|\d+\.)\s+", text)),
        "duplicate_nonempty_lines": repeated_lines,
        "duplicate_nonempty_line_count": len(repeated_lines),
        "contradictions": contradictions,
        "instruction_flags": flags,
    }


def task_keyword_coverage(text: str, task_keywords: list[str]) -> float:
    if not task_keywords:
        return 1.0
    normalized = text.lower()
    hits = sum(1 for keyword in task_keywords if keyword in normalized)
    return hits / len(task_keywords)


def build_feedback(
    kind: str,
    metadata: dict[str, Any],
    task_themes: dict[str, int],
    issue_themes: dict[str, int],
    task_coverage: float,
) -> list[str]:
    flags = dict(metadata.get("instruction_flags", {}))
    contradictions = list(metadata.get("contradictions", []))
    duplicate_count = int(metadata.get("duplicate_nonempty_line_count", 0))
    feedback: list[str] = []

    if contradictions:
        feedback.append(
            "Resolve contradictory guidance so the agent has one clear policy for the same decision."
        )
    if duplicate_count:
        feedback.append("Remove repeated non-empty lines to reduce noise and token waste.")
    if not flags.get("has_role"):
        feedback.append("State the agent role or operating stance explicitly near the top.")
    if not flags.get("has_constraints"):
        feedback.append("Document hard constraints and prohibitions more clearly.")
    if not flags.get("has_workflow"):
        feedback.append("Add a concrete working sequence so the agent knows what to do first.")
    if not flags.get("has_verification"):
        feedback.append("Add verification guidance so changes are tested or checked before completion.")
    if not flags.get("has_output_contract"):
        feedback.append("Define the expected response format more explicitly.")
    if kind == "agents" and not flags.get("has_repo_context"):
        feedback.append("Mention repository/context-loading expectations so the agent grounds work locally.")
    if kind == "skill" and not flags.get("has_trigger_phrase"):
        feedback.append("Clarify when this skill should be invoked and what it owns.")
    if task_themes.get("verification", 0) and not flags.get("has_verification"):
        feedback.append("Task evidence emphasizes testing and validation; mirror that in the instructions.")
    if issue_themes.get("safety", 0) and not flags.get("has_constraints"):
        feedback.append("Issue evidence suggests safety gaps; tighten approval and destructive-action rules.")
    if issue_themes.get("format", 0) and not flags.get("has_output_contract"):
        feedback.append("Issue evidence suggests formatting drift; specify output shape more concretely.")
    if task_coverage < 0.25:
        feedback.append("Repository task vocabulary is weakly reflected; add more repo-specific guidance.")
    if not feedback:
        feedback.append("Instruction asset is structurally solid under current checks.")
    return feedback

