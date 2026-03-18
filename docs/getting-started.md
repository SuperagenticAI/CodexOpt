# Getting Started

## Requirements

- Python `>=3.10`
- `uv` recommended, or `pip`

## Install

=== "uv"

    ```bash
    uv sync --extra dev
    uv run codexopt --help
    ```

=== "pip"

    ```bash
    pip install codexopt
    codexopt --help
    ```

## Standard Workflow

Run CodexOpt in the repository that contains your Codex instruction assets.

```bash
codexopt init
codexopt scan
codexopt benchmark
codexopt optimize agents --file AGENTS.md
codexopt optimize skills --glob ".codex/skills/**/SKILL.md"
codexopt apply --kind agents --dry-run
codexopt report --output codexopt-report.md
```

## What Developers Usually Provide

At minimum:

- `AGENTS.md`
- one or more `SKILL.md` files

Optional evidence:

- `tasks.md`
- `issues.md`
- JSON exports of tasks, reviews, or issue summaries

## Output Location

By default CodexOpt writes all artifacts under:

```text
.codexopt/
```

Important files:

- `runs/<run_id>/scan.json`
- `runs/<run_id>/benchmark.json`
- `runs/<run_id>/optimize.json`
- `runs/<run_id>/apply.json`
- `state.json`

