---
name: prompt-readiness-gate
description: Deterministically lint the first structured ML research/coding prompt before execution. Use at project initialization or when the user explicitly requests revalidation; do not use for ordinary follow-up messages.
---

# Prompt Readiness Gate

Validate before planning or execution:

1. Write the user's specification unchanged to a temporary UTF-8 file.
2. Run `python3 scripts/prompt_lint.py <file>` from this skill directory. Do not replace or override the linter with model judgment.
3. On `NOT_READY`, return its diagnostics and stop. Ask the user to revise the reported locations; never choose a missing high-impact answer.
4. On `READY`, treat the original specification—not an inferred rewrite—as authoritative and continue the task.

The gate proves conformance only to its explicit profile and atomic constraints; it cannot prove that claims match external reality or that omitted domain requirements do not exist. If the user asks how to format a specification, read [references/contract.md](references/contract.md).
