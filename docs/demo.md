# Demo Repository

The companion demo repo is available here:

- <https://github.com/SuperagenticAI/codexopt-demo>

It contains:

- a noisy and contradictory `AGENTS.md`
- several intentionally messy `SKILL.md` files
- `tasks.md` for task evidence
- `issues.md` for recurring feedback themes

## Why Use the Demo?

The demo shows CodexOpt on a small repo where instruction problems are easy to see:

- duplicate rules
- contradiction
- missing frontmatter
- unnecessary verbosity

## Typical Demo Flow

```bash
cd /path/to/codexopt-demo
codexopt --config codexopt.gepa.example.yaml benchmark
codexopt --config codexopt.gepa.example.yaml optimize agents --engine heuristic --file AGENTS.md
codexopt --config codexopt.gepa.example.yaml optimize skills --engine heuristic --glob ".codex/skills/**/SKILL.md"
codexopt --config codexopt.gepa.example.yaml report --output codexopt-report.md
```

## Cross-reference

If you are reading the demo first, the main project lives here:

- <https://github.com/SuperagenticAI/CodexOpt>

