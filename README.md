# CodexOpt

[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://superagenticai.github.io/CodexOpt/)

CodexOpt: Optimize your Agents.MD and Skills for Codex with GEPA

## Demo Repo

Want to see CodexOpt on a small, intentionally messy repository with sample
`AGENTS.md`, demo skills, `tasks.md`, and `issues.md`?

- Demo: https://github.com/SuperagenticAI/codexopt-demo

## Documentation

- Docs site: https://superagenticai.github.io/CodexOpt/
- Docs source: [`docs/`](/Users/shashi/oss/CodexOpt/docs)

View the published documentation:

- https://superagenticai.github.io/CodexOpt/

CodexOpt is a lightweight Python CLI to improve Codex instruction assets with a repeatable loop:

1. Scan instruction files.
2. Benchmark quality.
3. Generate optimized candidates.
4. Apply only improvements.
5. Produce a report.

It targets:

- `AGENTS.md`
- `.codex/skills/**/SKILL.md`

## Why CodexOpt

Most teams edit `AGENTS.md` and `SKILL.md` manually, but struggle to answer:

- Did quality actually improve?
- Did we increase prompt bloat?
- Did we break skill frontmatter conventions?

CodexOpt turns these edits into measurable runs with artifacts you can inspect and version.

## Features

- Project scan with issue detection for agents and skills.
- Benchmark scoring with sub-scores and natural-language feedback.
- Optional evidence inputs from repo task files and issue exports.
- Optimization engine `heuristic` (default, local and deterministic).
- Optional optimization engine `gepa` (via `gepa.optimize_anything`).
- Explicit reporting when a GEPA-requested run falls back to heuristic optimization.
- Safe apply flow with automatic backups.
- Markdown reporting from latest runs.
- Minimal OSS CI (lint, test, build).

## Installation

### Requirements

- Python `>=3.10`
- `uv` (recommended) or `pip`

### Recommended: uv (full workflow)

```bash
uv sync --extra dev
```

Run commands through the managed environment:

```bash
uv run codexopt --help
```

`uv.lock` is committed to keep dependency resolution reproducible across machines and CI.

### Alternative: pip

```bash
pip install -e ".[dev]"
```

## Quick Start (uv)

```bash
# 1) Create config
uv run codexopt init

# 2) Inspect what will be evaluated
uv run codexopt scan

# 3) Get baseline scores
uv run codexopt benchmark

# 4) Optimize AGENTS.md
uv run codexopt optimize agents --file AGENTS.md

# 5) Optimize skills
uv run codexopt optimize skills --glob ".codex/skills/**/SKILL.md"

# 6) Review apply impact without writing
uv run codexopt apply --kind agents --dry-run

# 7) Apply selected improvements
uv run codexopt apply --kind agents

# 8) Generate markdown summary
uv run codexopt report --output codexopt-report.md
```

## How Teams Use CodexOpt

Developers use CodexOpt in the repository that contains their Codex instruction assets:

- `AGENTS.md`
- `.codex/skills/**/SKILL.md`

Optional evidence can also be added to improve benchmarking and optimization quality:

- task files (`tasks.md`, task lists, or JSON fixtures)
- issue/review exports (`issues.md` or JSON exports)

Typical workflow:

1. Run `scan` and `benchmark` to measure the current instruction assets.
2. Run `optimize agents` and `optimize skills` to generate improved candidates.
3. Review the generated diffs and report artifacts under `.codexopt/runs/`.
4. Run `apply --dry-run` first, then apply accepted changes.
5. Commit the updated instruction files and, if useful, attach the report to a PR.

Example with optional evidence configured in `codexopt.yaml`:

```yaml
evidence:
  task_files:
    - tasks.md
  issue_files:
    - issues.md
```

With that config in place, `benchmark` and `optimize` use:

- static prompt-quality checks
- repo task alignment
- recurring issue/review themes

Today, task and issue files influence scoring and feedback. CodexOpt does not yet execute full agent task simulations.

Use `codexopt.example.yaml` as a starting point for committed team config.

## Command Reference

### Global options

```bash
codexopt --config <path-to-codexopt.yaml> <command>
```

### `init`

Create a default config file.

```bash
codexopt init [--path PATH] [--force]
```

### `scan`

Discover AGENTS/SKILL targets and validate shape.

```bash
codexopt scan
```

### `benchmark`

Score current files using built-in heuristics.

```bash
codexopt benchmark
```

### `optimize agents`

Optimize AGENTS files.

```bash
codexopt optimize agents \
  [--file PATTERN] \
  [--engine heuristic|gepa] \
  [--reflection-model MODEL] \
  [--max-metric-calls N]
```

### `optimize skills`

Optimize SKILL files.

```bash
codexopt optimize skills \
  [--glob PATTERN] \
  [--engine heuristic|gepa] \
  [--reflection-model MODEL] \
  [--max-metric-calls N]
```

### `apply`

Apply best candidates from the latest optimization run (or a provided run id).

```bash
codexopt apply [--kind agents|skills] [--run-id RUN_ID] [--dry-run]
```

### `report`

Generate a markdown report from latest runs in state.

```bash
codexopt report [--output FILE.md]
```

## Configuration

Default `codexopt.yaml`:

```yaml
version: 1
targets:
  agents_files:
    - AGENTS.md
    - "**/AGENTS.md"
    - "**/AGENTS.override.md"
  skills_globs:
    - ".codex/skills/**/SKILL.md"
    - "**/.codex/skills/**/SKILL.md"
  exclude_globs:
    - ".git/**"
    - ".codexopt/**"
    - ".venv/**"
    - "node_modules/**"
    - "reference/**"
output:
  root_dir: ".codexopt"
evidence:
  task_files: []
  issue_files: []
optimization:
  engine: "heuristic"
  min_apply_delta: 0.01
  max_metric_calls: 60
  reflection_model: null
```

Config notes:

- `targets.agents_files`: glob patterns for AGENTS targets.
- `targets.skills_globs`: glob patterns for `SKILL.md` targets.
- `targets.exclude_globs`: paths ignored during scan.
- `output.root_dir`: run artifacts and backups location.
- `evidence.task_files`: optional markdown/json task lists used for repo-alignment scoring.
- `evidence.issue_files`: optional markdown/json issue or review exports used for theme-aware feedback.
- `optimization.engine`: default optimization engine.
- `optimization.min_apply_delta`: minimum score gain required to apply.
- `optimization.max_metric_calls`: GEPA metric budget.
- `optimization.reflection_model`: required when using GEPA engine.

## How Scoring Works

CodexOpt computes a `0.0` to `1.0` score per file.

AGENTS scoring factors include:

- Too short or too long content penalties.
- Token-heaviness estimate penalty.
- Empty file penalty.
- Contradictory guidance penalties.
- Missing workflow / verification / output-format guidance penalties.
- Repo-context and task-alignment signals when evidence files are configured.

SKILL scoring factors include:

- Missing frontmatter penalties.
- Missing `name` / `description` penalties.
- Overly long frontmatter fields penalties.
- Too short or too long content penalties.
- Weak trigger/workflow/verification guidance penalties.
- Repo task alignment signals when evidence files are configured.

Each benchmarked file also includes:

- criterion-level sub-scores
- natural-language feedback
- optional evidence summary from configured task/issue files

## Optimization Behavior

### Heuristic engine

Candidate transforms include:

- Whitespace normalization.
- Blank-line compaction.
- Duplicate adjacent line removal.
- Skill-specific frontmatter synthesis/trimming.

The best candidate is selected by score delta. If delta is below `min_apply_delta`, original content is kept.

### GEPA engine (optional)

CodexOpt can call `gepa.optimize_anything` when `--engine gepa` is selected.

The GEPA path is model-agnostic. In practice, teams can use any reflection model
supported by their GEPA / LiteLLM setup, including OpenAI, Gemini, local models,
or other compatible providers. That means you can ask GEPA to generate feedback
and candidate improvements using whichever model gives you the best quality /
cost tradeoff for your workflow.

Requirements:

- `gepa` installed in the environment.
- A valid reflection model via `--reflection-model` or config.

Common examples:

```yaml
optimization:
  engine: "gepa"
  reflection_model: "openai/gpt-5-mini"
```

```yaml
optimization:
  engine: "gepa"
  reflection_model: "gemini/gemini-2.5-pro"
```

For OpenAI-backed GEPA runs, set:

```bash
export OPENAI_API_KEY="your-openai-key"
```

For Gemini-backed GEPA runs, set:

```bash
export GEMINI_API_KEY="your-gemini-key"
export GOOGLE_API_KEY="$GEMINI_API_KEY"
```

Fallback behavior:

- If GEPA is unavailable or errors, CodexOpt falls back to heuristic optimization.
- Fallbacks are recorded in optimization artifacts, CLI summaries, and reports.

## Artifacts and State

By default, everything is written under `.codexopt/`:

- `runs/<run_id>/scan.json`
- `runs/<run_id>/benchmark.json`
- `runs/<run_id>/optimize.json`
- `runs/<run_id>/apply.json`
- `backups/<timestamp>/...` (created on non-dry-run apply)
- `state.json` (tracks latest run ids per command type)

Run ids are timestamped and namespaced by command kind, for example:

- `20260308T184800123456Z-benchmark`
- `20260308T184812654321Z-optimize-skills`

## Typical Team Workflow

1. Commit current `AGENTS.md` and skills.
2. Run `scan` and `benchmark` to establish baseline.
3. Run `optimize agents` and/or `optimize skills`.
4. Review `optimize.json` and diffs.
5. Run `apply --dry-run` first, then `apply`.
6. Run `report` and attach report to PR.

## Examples

### Example A: `AGENTS.md` cleanup

Before (`AGENTS.md`):

```md
## Coding Rules
Always run tests before commit.
Always run tests before commit.


Keep changes minimal.
```

After optimization (heuristic):

```md
## Coding Rules
Always run tests before commit.

Keep changes minimal.
```

What changed:

- Removed duplicate adjacent line.
- Compacted extra blank lines.

### Example B: `SKILL.md` missing frontmatter

Before (`.codex/skills/my_skill/SKILL.md`):

```md
Use this skill for repository release checks.
Run lint, tests, and changelog validation.
```

After optimization (heuristic):

```md
---
name: my-skill
description: Repository-specific workflow skill.
---

Use this skill for repository release checks.
Run lint, tests, and changelog validation.
```

What changed:

- Added required frontmatter block.
- Generated normalized `name` from folder name.
- Added default `description`.

### Example C: Reproduce end-to-end on a repo

```bash
uv run codexopt init
uv run codexopt scan
uv run codexopt benchmark
uv run codexopt optimize agents --file AGENTS.md
uv run codexopt optimize skills --glob ".codex/skills/**/SKILL.md"
uv run codexopt apply --kind skills --dry-run
uv run codexopt apply --kind skills
uv run codexopt report --output codexopt-report.md
```

Files to inspect after running:

- `.codexopt/runs/*/scan.json`
- `.codexopt/runs/*/benchmark.json`
- `.codexopt/runs/*/optimize.json`
- `.codexopt/runs/*/apply.json`
- `.codexopt/backups/*`

## CI

GitHub Actions workflow is included at `.github/workflows/ci.yml` and runs:

- `uv lock --check` for lockfile consistency.
- `uv sync --extra dev` for environment setup.
- Ruff lint checks.
- Pytest tests.
- Package build (`uv build`).

It does not publish packages.

## Development

```bash
uv lock
uv sync --extra dev
uv run --no-sync ruff check src tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run --no-sync pytest -q
uv build
```

## FAQ / Troubleshooting

### `codexopt apply` says "no optimization run found"

Cause:

- No prior optimization run for the selected kind.
- `state.json` does not contain the expected latest run pointer.

Fix:

```bash
uv run codexopt optimize agents
uv run codexopt apply --kind agents
```

Or pass an explicit run:

```bash
uv run codexopt apply --kind agents --run-id <run_id>
```

### `--engine gepa` did not use GEPA

Cause:

- `gepa` is not installed, or
- `reflection_model` is missing.

Behavior:

- CodexOpt falls back to heuristic optimization when GEPA errors.

Fix:

```bash
uv run codexopt optimize agents --engine gepa --reflection-model <model_name>
```

### `apply --dry-run` says files would be applied, but nothing changed

Expected behavior:

- `--dry-run` reports candidate applications without writing files.

To write changes, run again without `--dry-run`:

```bash
uv run codexopt apply --kind agents
```

### Build fails with network/isolation issues

If your environment blocks dependency resolution in isolated builds, use:

```bash
uv build
```

### Pytest fails due to unrelated external plugins

Some environments auto-load global pytest plugins that can break local tests.
Run with plugin autoload disabled:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 uv run --no-sync pytest -q
```

### Optimization produced no applied changes

Cause:

- Best candidate delta is below `optimization.min_apply_delta`, or
- File content is already equivalent.

Fix:

- Lower `optimization.min_apply_delta` in `codexopt.yaml`, then re-run optimize/apply.

## License

MIT. See `LICENSE`.

## Author

- Shashi (`shashi@super-agentic.ai`)
