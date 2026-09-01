# Contributing

Prompt Grammar accepts evidence-backed improvements to the machine-learning profile, deterministic validator, tests, templates, and documentation.

## Before opening a change

- Keep the current product scope to first-turn ML research and coding prompts.
- Open an Issue for a grammar meaning change or new hard rule before implementing it.
- Reduce a bug to the smallest prompt that reproduces the behavior.
- Do not add an LLM call as the pass/fail oracle.
- Do not add a silent default for a high-impact ML choice.

## Development checks

Python 3.11 or newer is required; the linter itself uses only the standard library.

```bash
python3 -m unittest discover -s .agents/skills/prompt-readiness-gate/tests -v
python3 .agents/skills/prompt-readiness-gate/tests/run_benchmark.py
python3 .agents/skills/prompt-readiness-gate/scripts/prompt_lint.py examples/ml-research-v2.md
python3 .agents/skills/prompt-readiness-gate/scripts/prompt_lint.py examples/ml-implement-v2.md
python3 scripts/package_plugin.py
```

Run Ruff and the coverage gate used by CI when the tools are installed:

```bash
ruff check .agents/skills/prompt-readiness-gate scripts
ruff format --check .agents/skills/prompt-readiness-gate scripts
coverage run --source=.agents/skills/prompt-readiness-gate/scripts \
  -m unittest discover -s .agents/skills/prompt-readiness-gate/tests
coverage report --fail-under=95
```

## Grammar changes

A hard rule must include:

- normative semantics and a stable diagnostic code;
- at least one accepted and one rejected fixture;
- unit tests and an adversarial or mutation case;
- compatibility behavior for existing grammar versions;
- an update to the contract and validation report;
- an explanation of false-positive risk and context/token cost.

Edit the canonical Skill under `.agents/skills/prompt-readiness-gate`, then run:

```bash
python3 scripts/package_plugin.py --sync
```

CI rejects a pull request when the plugin copy diverges from the canonical Skill.

## Pull requests

Keep each pull request focused. Explain the observed problem, the contract-level behavior, the evidence added, compatibility impact, and any remaining validity threat. Never include private prompts, credentials, proprietary datasets, or identifying information in fixtures.
