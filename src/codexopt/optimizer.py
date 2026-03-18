from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from .benchmark import score_entry
from .quality import analyze_instruction_text
from .types import FileOptimizationResult
from .types import OptimizeCandidate


def _extract_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    if not text.startswith("---"):
        return None, text
    lines = text.splitlines()
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        return None, text
    raw = "\n".join(lines[1:end]).strip()
    if yaml is None:
        return None, text
    try:
        parsed = yaml.safe_load(raw) or {}
    except Exception:
        return None, text
    body = "\n".join(lines[end + 1 :]).lstrip("\n")
    return parsed, body


def _compose_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    if yaml is None:
        return body
    rendered = yaml.safe_dump(frontmatter, sort_keys=False).strip()
    if not body.endswith("\n"):
        body = f"{body}\n"
    return f"---\n{rendered}\n---\n\n{body}"


def _normalize_whitespace(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip() + "\n"


def _compact_blank_lines(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text.strip()) + "\n"


def _dedupe_identical_lines(text: str) -> str:
    out: list[str] = []
    prev: str | None = None
    for line in text.splitlines():
        if prev is not None and line == prev and line.strip():
            continue
        out.append(line)
        prev = line
    return "\n".join(out).strip() + "\n"


def _ensure_skill_frontmatter(path: Path, text: str) -> str:
    frontmatter, body = _extract_frontmatter(text)
    if frontmatter is None:
        name = path.parent.name.lower().replace("_", "-")
        name = re.sub(r"[^a-z0-9-]", "-", name)
        name = re.sub(r"-{2,}", "-", name).strip("-") or "skill"
        frontmatter = {
            "name": name[:64],
            "description": "Repository-specific workflow skill.",
        }
        return _compose_frontmatter(frontmatter, body if body != text else text)
    return text


def _trim_skill_frontmatter_fields(text: str) -> str:
    frontmatter, body = _extract_frontmatter(text)
    if frontmatter is None:
        return text

    if "name" in frontmatter:
        name = str(frontmatter["name"]).strip().lower().replace("_", "-")
        name = re.sub(r"[^a-z0-9-]", "-", name)
        frontmatter["name"] = re.sub(r"-{2,}", "-", name).strip("-")[:64]
    if "description" in frontmatter:
        frontmatter["description"] = str(frontmatter["description"]).strip()[:1024]
    return _compose_frontmatter(frontmatter, body)


def _build_entry_for_scoring(path: Path, kind: str, text: str) -> dict[str, Any]:
    words = len(text.split())
    token_estimate = int(words * 1.33)
    issues: list[str] = []
    metadata: dict[str, Any] = analyze_instruction_text(text)
    if kind == "skill":
        fm, _ = _extract_frontmatter(text)
        metadata["frontmatter_present"] = fm is not None
        metadata["frontmatter"] = fm or {}
        if fm is None:
            issues.append("missing_frontmatter")
        else:
            name = str((fm or {}).get("name", "")).strip()
            desc = str((fm or {}).get("description", "")).strip()
            if not name:
                issues.append("missing_name")
            if not desc:
                issues.append("missing_description")
            if len(name) > 64:
                issues.append("name_too_long")
            if len(desc) > 1024:
                issues.append("description_too_long")
    if kind == "agents":
        if not text.strip():
            issues.append("empty_agents")
        if token_estimate > 6000:
            issues.append("agents_too_large")
        if metadata.get("contradictions"):
            issues.append("contradictory_guidance")
        if metadata.get("duplicate_nonempty_line_count", 0) > 0:
            issues.append("duplicate_lines")
    return {
        "path": str(path),
        "kind": kind,
        "text": text,
        "bytes": len(text.encode("utf-8")),
        "lines": len(text.splitlines()),
        "words": words,
        "token_estimate": token_estimate,
        "issues": issues,
        "metadata": metadata,
    }


def _score_text(path: Path, kind: str, text: str, evidence: dict[str, Any] | None = None) -> float:
    entry = _build_entry_for_scoring(path, kind, text)
    return score_entry(entry, evidence=evidence).score


def _generate_heuristic_candidates(
    path: Path,
    kind: str,
    original: str,
    evidence: dict[str, Any] | None = None,
) -> list[OptimizeCandidate]:
    variants: list[tuple[str, str]] = [
        ("original", original),
        ("normalize_whitespace", _normalize_whitespace(original)),
        ("compact_blank_lines", _compact_blank_lines(original)),
        ("dedupe_identical_lines", _dedupe_identical_lines(original)),
    ]
    if kind == "skill":
        variants.extend(
            [
                ("ensure_frontmatter", _ensure_skill_frontmatter(path, original)),
                ("trim_frontmatter_fields", _trim_skill_frontmatter_fields(original)),
            ]
        )

    dedup: dict[str, str] = {}
    for name, content in variants:
        dedup.setdefault(content, name)

    candidates: list[OptimizeCandidate] = []
    for content, name in dedup.items():
        candidates.append(
            OptimizeCandidate(
                name=name,
                score=_score_text(path, kind, content, evidence=evidence),
                content=content,
            )
        )
    return sorted(candidates, key=lambda item: item.score, reverse=True)


def _optimize_with_gepa(
    path: Path,
    kind: str,
    original: str,
    reflection_model: str | None,
    max_metric_calls: int,
    evidence: dict[str, Any] | None = None,
) -> OptimizeCandidate:
    try:
        from gepa.optimize_anything import EngineConfig
        from gepa.optimize_anything import GEPAConfig
        from gepa.optimize_anything import ReflectionConfig
        from gepa.optimize_anything import optimize_anything
    except Exception as exc:
        raise RuntimeError(f"GEPA not available: {exc}") from exc

    if not reflection_model:
        raise RuntimeError("GEPA engine requires --reflection-model or config.optimization.reflection_model")

    def evaluator(candidate_text: str) -> tuple[float, dict[str, Any]]:
        score = _score_text(path, kind, candidate_text, evidence=evidence)
        details = score_entry(_build_entry_for_scoring(path, kind, candidate_text), evidence=evidence).details
        side_info = {
            "scores": {"quality": score},
            "Input": {"path": str(path), "kind": kind},
            "Feedback": details.get("feedback", []),
            "Criteria": details.get("criteria_scores", {}),
        }
        return score, side_info

    result = optimize_anything(
        seed_candidate=original,
        evaluator=evaluator,
        objective=f"Improve {kind} instruction quality while keeping semantics and reducing unnecessary tokens.",
        config=GEPAConfig(
            engine=EngineConfig(max_metric_calls=max_metric_calls),
            reflection=ReflectionConfig(reflection_lm=reflection_model),
        ),
    )
    best = result.best_candidate
    if isinstance(best, dict):
        if "current_candidate" in best:
            best_text = str(best["current_candidate"])
        else:
            best_text = str(next(iter(best.values())))
    else:
        best_text = str(best)
    return OptimizeCandidate(
        name="gepa_best",
        score=_score_text(path, kind, best_text, evidence=evidence),
        content=best_text,
    )


def optimize_entries(
    entries: list[dict[str, Any]],
    kind: str,
    engine: str,
    min_delta: float,
    reflection_model: str | None,
    max_metric_calls: int,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    file_results: list[FileOptimizationResult] = []
    fallback_count = 0
    for entry in entries:
        if entry["kind"] != kind:
            continue
        path = Path(entry["path"])
        if not path.exists():
            continue
        original = path.read_text(encoding="utf-8", errors="replace")
        baseline = _score_text(path, kind, original, evidence=evidence)

        actual_engine = engine
        fallback_reason: str | None = None
        if engine == "gepa":
            try:
                candidates = [OptimizeCandidate("original", baseline, original)]
                candidates.append(
                    _optimize_with_gepa(
                        path,
                        kind,
                        original,
                        reflection_model,
                        max_metric_calls,
                        evidence=evidence,
                    )
                )
                candidates = sorted(candidates, key=lambda item: item.score, reverse=True)
            except Exception as exc:
                candidates = _generate_heuristic_candidates(path, kind, original, evidence=evidence)
                actual_engine = "heuristic_fallback"
                fallback_reason = str(exc)
                fallback_count += 1
        else:
            candidates = _generate_heuristic_candidates(path, kind, original, evidence=evidence)

        best = candidates[0]
        delta = best.score - baseline
        if delta < min_delta:
            best = OptimizeCandidate("original", baseline, original)
            delta = 0.0

        diff = "".join(
            difflib.unified_diff(
                original.splitlines(keepends=True),
                best.content.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )
        )
        file_results.append(
            FileOptimizationResult(
                path=str(path),
                kind=kind,
                baseline_score=round(baseline, 4),
                best_score=round(best.score, 4),
                delta=round(delta, 4),
                actual_engine=actual_engine,
                best_candidate_name=best.name,
                best_content=best.content,
                diff=diff,
                fallback_reason=fallback_reason,
                candidates=[
                    {"name": cand.name, "score": round(cand.score, 4)}
                    for cand in candidates
                ],
            )
        )

    improved = [item for item in file_results if item.delta > 0]
    return {
        "kind": kind,
        "engine": engine,
        "requested_engine": engine,
        "fallback_count": fallback_count,
        "files_total": len(file_results),
        "files_improved": len(improved),
        "average_delta": round(
            (sum(item.delta for item in file_results) / len(file_results)) if file_results else 0.0,
            4,
        ),
        "results": [
            {
                "path": item.path,
                "kind": item.kind,
                "baseline_score": item.baseline_score,
                "best_score": item.best_score,
                "delta": item.delta,
                "actual_engine": item.actual_engine,
                "best_candidate_name": item.best_candidate_name,
                "best_content": item.best_content,
                "diff": item.diff,
                "fallback_reason": item.fallback_reason,
                "candidates": item.candidates,
            }
            for item in file_results
        ],
    }


def print_optimization_summary(result: dict[str, Any]) -> None:
    print(f"kind: {result['kind']}")
    print(f"engine: {result['engine']}")
    if result.get("fallback_count", 0):
        print(f"fallback_count: {result['fallback_count']}")
    print(f"files_total: {result['files_total']}")
    print(f"files_improved: {result['files_improved']}")
    print(f"average_delta: {result['average_delta']:.4f}")
    for item in result["results"]:
        suffix = ""
        if item.get("actual_engine") == "heuristic_fallback":
            suffix = " actual_engine=heuristic_fallback"
        print(f"- {item['path']} delta={item['delta']:.4f} best={item['best_candidate_name']}{suffix}")
