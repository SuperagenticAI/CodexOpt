# Configuration

CodexOpt reads `codexopt.yaml` by default.

## Example Config

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

## Sections

### `targets`

Controls where CodexOpt looks for instruction assets.

- `agents_files`: glob patterns for `AGENTS.md`
- `skills_globs`: glob patterns for `SKILL.md`
- `exclude_globs`: paths to ignore during discovery

### `output`

Controls artifact location.

- `root_dir`: where runs, state, and backups are written

### `evidence`

Optional files that improve benchmarking and optimization quality.

- `task_files`: markdown or JSON task lists
- `issue_files`: markdown or JSON issue / review exports

These do not yet execute full task simulations. They influence scoring and feedback.

### `optimization`

- `engine`: `heuristic` or `gepa`
- `min_apply_delta`: minimum score gain required to keep a candidate
- `max_metric_calls`: GEPA search budget
- `reflection_model`: required when using GEPA

## Using a Non-default Config

`--config` is a global option and must appear before the subcommand:

```bash
codexopt --config codexopt.yaml benchmark
codexopt --config codexopt.yaml optimize agents --file AGENTS.md
```

