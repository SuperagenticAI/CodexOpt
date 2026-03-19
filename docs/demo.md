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

The demo is intended to be runnable without needing to invent your own assets first.

It already includes:

- a sample `AGENTS.md`
- demo skills under `.codex/skills/`
- `tasks.md` for task evidence
- `issues.md` for recurring review themes

### 1. Clone the demo and enter the repo

```bash
git clone https://github.com/SuperagenticAI/codexopt-demo.git
cd codexopt-demo
```

### 2. Create or copy config

```bash
cp codexopt.gepa.example.yaml codexopt.yaml
```

### 3. Run a baseline benchmark

```bash
codexopt --config codexopt.yaml benchmark
```

### 4. Optimize the instruction assets

```bash
codexopt --config codexopt.yaml optimize agents --engine heuristic --file AGENTS.md
codexopt --config codexopt.yaml optimize skills --engine heuristic --glob ".codex/skills/**/SKILL.md"
```

### 5. Review the results

```bash
codexopt --config codexopt.yaml report --output codexopt-report.md
sed -n '1,120p' codexopt-report.md
```

### Optional: try GEPA

```bash
export OPENAI_API_KEY="YOUR_KEY"
codexopt --config codexopt.yaml optimize agents \
  --engine gepa \
  --reflection-model openai/gpt-5-mini \
  --max-metric-calls 20 \
  --file AGENTS.md
```

## Cross-reference

If you are reading the demo first, the main project lives here:

- <https://github.com/SuperagenticAI/CodexOpt>
