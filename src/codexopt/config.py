from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


DEFAULT_CONFIG_FILENAME = "codexopt.yaml"


@dataclass
class TargetsConfig:
    agents_files: list[str] = field(
        default_factory=lambda: ["AGENTS.md", "**/AGENTS.md", "**/AGENTS.override.md"]
    )
    skills_globs: list[str] = field(
        default_factory=lambda: [".codex/skills/**/SKILL.md", "**/.codex/skills/**/SKILL.md"]
    )
    exclude_globs: list[str] = field(
        default_factory=lambda: [
            ".git/**",
            ".codexopt/**",
            ".venv/**",
            "node_modules/**",
            "reference/**",
        ]
    )


@dataclass
class OutputConfig:
    root_dir: str = ".codexopt"


@dataclass
class EvidenceConfig:
    task_files: list[str] = field(default_factory=list)
    issue_files: list[str] = field(default_factory=list)


@dataclass
class OptimizationConfig:
    engine: str = "heuristic"
    min_apply_delta: float = 0.01
    max_metric_calls: int = 60
    reflection_model: str | None = None


@dataclass
class CodexOptConfig:
    version: int = 1
    targets: TargetsConfig = field(default_factory=TargetsConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    evidence: EvidenceConfig = field(default_factory=EvidenceConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)


def default_config() -> CodexOptConfig:
    return CodexOptConfig()


def _merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def _config_to_dict(cfg: CodexOptConfig) -> dict[str, Any]:
    return {
        "version": cfg.version,
        "targets": {
            "agents_files": cfg.targets.agents_files,
            "skills_globs": cfg.targets.skills_globs,
            "exclude_globs": cfg.targets.exclude_globs,
        },
        "output": {"root_dir": cfg.output.root_dir},
        "evidence": {
            "task_files": cfg.evidence.task_files,
            "issue_files": cfg.evidence.issue_files,
        },
        "optimization": {
            "engine": cfg.optimization.engine,
            "min_apply_delta": cfg.optimization.min_apply_delta,
            "max_metric_calls": cfg.optimization.max_metric_calls,
            "reflection_model": cfg.optimization.reflection_model,
        },
    }


def _dict_to_config(data: dict[str, Any]) -> CodexOptConfig:
    targets = data.get("targets", {})
    output = data.get("output", {})
    evidence = data.get("evidence", {})
    optimization = data.get("optimization", {})
    return CodexOptConfig(
        version=int(data.get("version", 1)),
        targets=TargetsConfig(
            agents_files=list(targets.get("agents_files", TargetsConfig().agents_files)),
            skills_globs=list(targets.get("skills_globs", TargetsConfig().skills_globs)),
            exclude_globs=list(targets.get("exclude_globs", TargetsConfig().exclude_globs)),
        ),
        output=OutputConfig(root_dir=str(output.get("root_dir", ".codexopt"))),
        evidence=EvidenceConfig(
            task_files=list(evidence.get("task_files", [])),
            issue_files=list(evidence.get("issue_files", [])),
        ),
        optimization=OptimizationConfig(
            engine=str(optimization.get("engine", "heuristic")),
            min_apply_delta=float(optimization.get("min_apply_delta", 0.01)),
            max_metric_calls=int(optimization.get("max_metric_calls", 60)),
            reflection_model=optimization.get("reflection_model"),
        ),
    )


def load_config(path: Path | None = None) -> tuple[CodexOptConfig, Path]:
    cfg_path = path or Path.cwd() / DEFAULT_CONFIG_FILENAME
    cfg = default_config()
    if not cfg_path.exists():
        return cfg, cfg_path
    if yaml is None:
        raise RuntimeError("PyYAML is required to read codexopt.yaml")

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    merged = _merge_dict(_config_to_dict(cfg), raw)
    return _dict_to_config(merged), cfg_path


def write_default_config(path: Path, force: bool = False) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; pass --force to overwrite")
    if yaml is None:
        raise RuntimeError("PyYAML is required to write codexopt.yaml")

    data = _config_to_dict(default_config())
    rendered = yaml.safe_dump(data, sort_keys=False)
    path.write_text(rendered, encoding="utf-8")
