---
name: prompt-readiness-gate
description: Deterministically validate the user's first structured machine-learning (ML) research or coding prompt for completeness, syntax, internal contradictions, unresolved high-impact decisions, and verifiable acceptance criteria. Use before planning/execution or on explicit revalidation; do not use for ordinary follow-ups or non-ML domains.
---

# Prompt Readiness Gate

Validate before planning or execution:

1. Write the user's first-turn ML specification unchanged to a temporary UTF-8 file.
2. Run `python3 scripts/prompt_lint.py <file>` from this skill directory. Do not replace or override the linter with model judgment.
3. On `NOT_READY`, return its diagnostics and stop. Ask the user to revise the reported locations; never choose a missing high-impact answer.
4. On `READY`, treat the original specification—not an inferred rewrite—as authoritative and continue the task.

`READY` proves only conformance to the versioned ML profile; it does not prove external facts, hidden prose semantics, or implementation success. For formatting or diagnostics, read [references/contract.md](references/contract.md).
