# FAQ

## Why only `AGENTS.md` and `SKILL.md`?

CodexOpt is intentionally narrow. These are the repo-local instruction assets that
developers most commonly maintain for Codex workflows.

## Does CodexOpt execute full task simulations?

Not yet. Task and issue files currently shape scoring and feedback rather than
running end-to-end agent executions.

## Do I need GEPA?

No. Heuristic mode works without GEPA and is the default.

## Do I need prompt-learning as a dependency?

No. CodexOpt does not depend on the prompt-learning library. It uses some of the
same ideas around natural-language feedback, but the implementation is native to CodexOpt.

## Which models can I use with GEPA?

CodexOpt's GEPA path is model-agnostic. You can use OpenAI, Gemini, local models,
or other GEPA / LiteLLM-compatible providers.

## What if a GEPA run fails?

CodexOpt falls back to heuristic optimization and records that fallback in artifacts
and reports.

