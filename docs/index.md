# CodexOpt

CodexOpt helps teams benchmark and optimize Codex instruction assets with a repeatable workflow.

It focuses on two repo-local files:

- `AGENTS.md`
- `.codex/skills/**/SKILL.md`

CodexOpt gives developers a practical loop:

1. scan instruction assets
2. benchmark their quality
3. generate improved candidates
4. review diffs and reports
5. apply only validated improvements

## Why CodexOpt?

Most teams maintain `AGENTS.md` and `SKILL.md` manually. Over time these files drift:

- duplicated rules
- contradictory instructions
- missing verification guidance
- weak skill triggers
- prompt bloat

CodexOpt makes those problems measurable and easier to improve safely.

## What It Does

- scans a repo for agent and skill instruction files
- benchmarks them with static checks plus optional task / issue evidence
- optimizes them with either heuristic transforms or optional GEPA-backed search
- records artifacts under `.codexopt/`
- generates markdown reports for review and PR discussion

## Demo Repository

If you want a small example repo with intentionally messy instructions, use the companion demo:

- Demo repo: <https://github.com/SuperagenticAI/codexopt-demo>

## Try It

```bash
uv sync --extra dev
uv run codexopt init
uv run codexopt benchmark
uv run codexopt optimize agents --file AGENTS.md
uv run codexopt optimize skills --glob ".codex/skills/**/SKILL.md"
uv run codexopt report --output codexopt-report.md
```

