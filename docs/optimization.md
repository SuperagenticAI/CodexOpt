# Optimization

CodexOpt supports two optimization engines.

## Heuristic Engine

The heuristic engine is local, fast, and deterministic.

It currently applies safe transforms such as:

- whitespace normalization
- blank-line compaction
- duplicate adjacent line removal
- skill frontmatter synthesis and trimming

Use it when you want predictable cleanup with no model dependency.

## GEPA Engine

CodexOpt can optionally use GEPA for reflection-driven optimization.

GEPA in CodexOpt is model-agnostic. Teams can use OpenAI, Gemini, local models,
or other reflection models supported by their GEPA / LiteLLM setup.

### OpenAI Example

```bash
export OPENAI_API_KEY="your-openai-key"
codexopt --config codexopt.yaml optimize agents \
  --engine gepa \
  --reflection-model openai/gpt-5-mini \
  --file AGENTS.md
```

### Gemini Example

```bash
export GEMINI_API_KEY="your-gemini-key"
export GOOGLE_API_KEY="$GEMINI_API_KEY"
codexopt --config codexopt.yaml optimize agents \
  --engine gepa \
  --reflection-model gemini/gemini-2.5-pro \
  --max-metric-calls 20 \
  --file AGENTS.md
```

## Fallback Behavior

If a GEPA-requested run cannot execute, CodexOpt falls back to heuristic optimization.

This is reported in:

- `optimize.json`
- CLI optimization summary
- markdown report

Look for:

- `fallback_count`
- `actual_engine`
- `GEPA fallback count` in reports

