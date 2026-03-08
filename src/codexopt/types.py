from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any


def dataclass_to_dict(value: Any) -> dict[str, Any]:
    return asdict(value)


@dataclass
class ScanEntry:
    path: str
    kind: str
    bytes: int
    lines: int
    words: int
    token_estimate: int
    issues: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FileScore:
    path: str
    kind: str
    score: float
    issues: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizeCandidate:
    name: str
    score: float
    content: str


@dataclass
class FileOptimizationResult:
    path: str
    kind: str
    baseline_score: float
    best_score: float
    delta: float
    best_candidate_name: str
    best_content: str
    diff: str
    candidates: list[dict[str, Any]] = field(default_factory=list)
