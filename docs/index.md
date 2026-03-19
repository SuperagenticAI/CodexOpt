<section class="codexopt-hero">
  <h1>CodexOpt</h1>
  <p class="codexopt-lead">
    Benchmark and optimize <code>AGENTS.md</code> and <code>SKILL.md</code> for Codex with a repeatable developer workflow.
  </p>
  <p>
    <a class="md-button md-button--primary" href="getting-started/">Get Started</a>
    <a class="md-button" href="https://github.com/SuperagenticAI/codexopt-demo">View Demo Repo</a>
  </p>
</section>

<div class="codexopt-grid">
  <div class="codexopt-card">
    <strong>Targeted</strong>
    Focused on repo-local Codex assets: <code>AGENTS.md</code> and <code>SKILL.md</code>.
  </div>
  <div class="codexopt-card">
    <strong>Measurable</strong>
    Score instruction quality, attach evidence, and review artifact-backed changes.
  </div>
  <div class="codexopt-card">
    <strong>Practical</strong>
    Scan, benchmark, optimize, review, apply, and report from a single CLI.
  </div>
</div>

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

## Why Developers Use It

Instruction files tend to drift long before teams notice:

- duplicated rules
- contradictory constraints
- weak testing guidance
- vague skill triggers
- prompt bloat

CodexOpt gives developers a way to improve those files with something closer to a normal engineering loop than ad hoc prompt editing.

## Demo Repository

If you want a small example repo with intentionally messy instructions, use the companion demo:

- Demo repo: <https://github.com/SuperagenticAI/codexopt-demo>
- Demo guide: [Open the demo walkthrough](demo.md)

## Try It

```bash
uv sync --extra dev
uv run codexopt init
uv run codexopt benchmark
uv run codexopt optimize agents --file AGENTS.md
uv run codexopt optimize skills --glob ".codex/skills/**/SKILL.md"
uv run codexopt report --output codexopt-report.md
```

If you want a guided example with sample inputs, evidence files, and ready-made commands,
start with the [demo walkthrough](demo.md).
