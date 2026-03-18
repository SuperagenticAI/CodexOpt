from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .applier import apply_optimization_result
from .applier import print_apply_summary
from .artifacts import new_run_dir
from .artifacts import read_json
from .artifacts import resolve_run_id
from .artifacts import set_latest_run
from .artifacts import write_json
from .benchmark import load_evidence
from .benchmark import print_benchmark_summary
from .benchmark import run_benchmark
from .config import DEFAULT_CONFIG_FILENAME
from .config import load_config
from .config import write_default_config
from .optimizer import optimize_entries
from .optimizer import print_optimization_summary
from .reporter import build_markdown_report
from .scanner import print_scan_summary
from .scanner import scan_project


def _resolve_config(config_path: str | None) -> tuple[Any, Path]:
    path = Path(config_path).resolve() if config_path else None
    return load_config(path)


def cmd_init(args: argparse.Namespace) -> int:
    path = Path(args.path or DEFAULT_CONFIG_FILENAME).resolve()
    write_default_config(path, force=args.force)
    print(f"wrote {path}")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    cfg, _cfg_path = _resolve_config(args.config)
    cwd = Path.cwd()
    result = scan_project(cwd, cfg)

    output_root = Path(cfg.output.root_dir)
    run_id, run_dir = new_run_dir(output_root, "scan")
    write_json(run_dir / "scan.json", result)
    set_latest_run(output_root, "latest_scan_run", run_id)

    print_scan_summary(result)
    print(f"run_id: {run_id}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    cfg, _cfg_path = _resolve_config(args.config)
    cwd = Path.cwd()
    scan_result = scan_project(cwd, cfg)
    evidence = load_evidence(cwd, cfg)
    benchmark_result = run_benchmark(scan_result, evidence=evidence)

    output_root = Path(cfg.output.root_dir)
    run_id, run_dir = new_run_dir(output_root, "benchmark")
    write_json(run_dir / "scan.json", scan_result)
    write_json(run_dir / "benchmark.json", benchmark_result)
    set_latest_run(output_root, "latest_scan_run", run_id)
    set_latest_run(output_root, "latest_benchmark_run", run_id)

    print_benchmark_summary(benchmark_result)
    print(f"run_id: {run_id}")
    return 0


def _optimize(args: argparse.Namespace, kind: str) -> int:
    cfg, _cfg_path = _resolve_config(args.config)
    cwd = Path.cwd()

    agents_patterns = args.file if kind == "agents" and args.file else None
    skills_patterns = args.glob if kind == "skill" and args.glob else None

    scan_result = scan_project(
        cwd=cwd,
        config=cfg,
        agents_files=agents_patterns,
        skills_globs=skills_patterns,
    )
    evidence = load_evidence(cwd, cfg)
    result = optimize_entries(
        entries=scan_result["entries"],
        kind=kind,
        engine=args.engine or cfg.optimization.engine,
        min_delta=cfg.optimization.min_apply_delta,
        reflection_model=args.reflection_model or cfg.optimization.reflection_model,
        max_metric_calls=args.max_metric_calls or cfg.optimization.max_metric_calls,
        evidence=evidence,
    )

    output_root = Path(cfg.output.root_dir)
    run_label = "optimize-agents" if kind == "agents" else "optimize-skills"
    run_id, run_dir = new_run_dir(output_root, run_label)
    write_json(run_dir / "scan.json", scan_result)
    write_json(run_dir / "optimize.json", result)
    key = "latest_optimize_agents_run" if kind == "agents" else "latest_optimize_skills_run"
    set_latest_run(output_root, key, run_id)

    print_optimization_summary(result)
    print(f"run_id: {run_id}")
    return 0


def cmd_optimize_agents(args: argparse.Namespace) -> int:
    return _optimize(args, "agents")


def cmd_optimize_skills(args: argparse.Namespace) -> int:
    return _optimize(args, "skill")


def cmd_apply(args: argparse.Namespace) -> int:
    cfg, _cfg_path = _resolve_config(args.config)
    output_root = Path(cfg.output.root_dir)

    if args.kind == "agents":
        state_key = "latest_optimize_agents_run"
    else:
        state_key = "latest_optimize_skills_run"

    run_id = resolve_run_id(output_root, state_key, args.run_id)
    if not run_id:
        print("no optimization run found", file=sys.stderr)
        return 2

    run_dir = output_root / "runs" / run_id
    optimize_path = run_dir / "optimize.json"
    if not optimize_path.exists():
        print(f"missing optimize artifact: {optimize_path}", file=sys.stderr)
        return 2
    optimize_result = read_json(optimize_path)
    apply_result = apply_optimization_result(
        optimization_result=optimize_result,
        repo_root=Path.cwd(),
        backup_root=output_root / "backups",
        dry_run=args.dry_run,
    )

    apply_run_id, apply_run_dir = new_run_dir(output_root, "apply")
    write_json(apply_run_dir / "apply.json", apply_result)
    set_latest_run(output_root, "latest_apply_run", apply_run_id)

    print_apply_summary(apply_result)
    print(f"source_run_id: {run_id}")
    print(f"run_id: {apply_run_id}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    cfg, _cfg_path = _resolve_config(args.config)
    output_root = Path(cfg.output.root_dir)
    report = build_markdown_report(output_root)
    if args.output:
        out = Path(args.output)
        out.write_text(report, encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codexopt", description="Optimize Codex AGENTS.md and SKILL.md")
    parser.add_argument("--config", help="Path to codexopt.yaml", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Write codexopt.yaml template")
    p_init.add_argument("--path", default=None, help="Output config path")
    p_init.add_argument("--force", action="store_true", help="Overwrite if exists")
    p_init.set_defaults(func=cmd_init)

    p_scan = sub.add_parser("scan", help="Scan AGENTS and SKILL files")
    p_scan.set_defaults(func=cmd_scan)

    p_bench = sub.add_parser("benchmark", help="Benchmark current instruction assets")
    p_bench.set_defaults(func=cmd_benchmark)

    p_opt = sub.add_parser("optimize", help="Optimize instruction assets")
    opt_sub = p_opt.add_subparsers(dest="target", required=True)

    p_opt_agents = opt_sub.add_parser("agents", help="Optimize AGENTS files")
    p_opt_agents.add_argument(
        "--file",
        action="append",
        help="AGENTS glob pattern (can be repeated). Defaults from config.",
    )
    p_opt_agents.add_argument("--engine", choices=["heuristic", "gepa"], default=None)
    p_opt_agents.add_argument("--reflection-model", default=None)
    p_opt_agents.add_argument("--max-metric-calls", type=int, default=None)
    p_opt_agents.set_defaults(func=cmd_optimize_agents)

    p_opt_skills = opt_sub.add_parser("skills", help="Optimize SKILL files")
    p_opt_skills.add_argument(
        "--glob",
        action="append",
        help="SKILL glob pattern (can be repeated). Defaults from config.",
    )
    p_opt_skills.add_argument("--engine", choices=["heuristic", "gepa"], default=None)
    p_opt_skills.add_argument("--reflection-model", default=None)
    p_opt_skills.add_argument("--max-metric-calls", type=int, default=None)
    p_opt_skills.set_defaults(func=cmd_optimize_skills)

    p_apply = sub.add_parser("apply", help="Apply best optimized candidates")
    p_apply.add_argument("--kind", choices=["agents", "skills"], default="agents")
    p_apply.add_argument("--run-id", default=None, help="Optimization run id to apply")
    p_apply.add_argument("--dry-run", action="store_true")
    p_apply.set_defaults(func=cmd_apply)

    p_report = sub.add_parser("report", help="Render markdown report from latest runs")
    p_report.add_argument("--output", default=None, help="Optional output markdown file")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
