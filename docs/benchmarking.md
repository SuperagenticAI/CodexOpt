# Benchmarking

CodexOpt computes a `0.0` to `1.0` score per file and records detailed feedback.

## What Gets Scored

### `AGENTS.md`

Signals include:

- too short or too long
- token heaviness
- empty files
- contradictory guidance
- duplicate lines
- missing workflow guidance
- missing verification guidance
- missing output-format guidance
- weak repo or task alignment

### `SKILL.md`

Signals include:

- missing frontmatter
- missing `name` or `description`
- overly long frontmatter fields
- weak trigger clarity
- weak workflow guidance
- weak verification guidance
- weak repo or task alignment

## Evidence-aware Feedback

If `task_files` or `issue_files` are configured, benchmark output includes:

- task file count
- issue file count
- criterion-level sub-scores
- natural-language feedback

## Example

```bash
codexopt --config codexopt.yaml benchmark
```

Typical output:

```text
overall_score: 0.6150
task_files: 1
issue_files: 1
- agents: /path/to/AGENTS.md
  score=0.4700 issues=contradictions, duplicate_lines, missing_output_contract
```

