# Prompt Contract

The linter accepts the repository's Markdown templates. A section is a known uppercase label followed by `:`. Delete optional sections that do not apply; use `NONE`, `N/A`, or `NOT_APPLICABLE` only when an included section is intentionally empty. Bracketed template instructions and empty bullets do not count as values.

## Atomic requirements

Material decisions, constraints, controls, prohibitions, and acceptance checks use one line per requirement:

```text
- [scope] subject OP value
```

- `scope`: `*` for global, or a stable phase name such as `train`, `eval`, or `result`. Global requirements combine with every named scope; different named scopes are checked independently.
- `subject`: a stable dotted identifier such as `data.split` or `gpu.count`.
- `OP`: `=`, `!=`, `<`, `<=`, `>`, `>=`, `in`, or `not-in`.
- `value`: a number, boolean, `null`, a bare identifier, a JSON string, or—only for `in`/`not-in`—a non-empty JSON array.

Examples:

```text
- [*] data.split = official-test
- [train] gpu.count <= 4
- [train] precision in ["fp16", "bf16"]
- [result] tests.failed = 0
```

Use the same subject and scope for requirements that must hold together. Do not hide a condition in prose; encode it as a named scope. The linter detects incompatible equalities, exclusions, numeric bounds, and finite-set constraints, including contradictions formed by more than two lines.

## Delegation and questions

```text
DELEGATED:
- [implementation] helper.naming delegated

OPEN_QUESTIONS:
- [HIGH] data.split — Which split is authoritative?
- [LOW] logging.format — JSON or text?
```

Any `HIGH` question blocks execution. Questions without an impact label are syntax errors.

## Mode rules

- All modes require `TASK`, `GOAL`, `CURRENT_STATE`, `OUTPUT`, and atomic `ACCEPTANCE` evidence.
- `RESEARCH` requires `HYPOTHESIS` plus `EXPERIMENT` fields `VARIABLE`, `CONTROL`, `EVALUATION`, and `METRICS`.
- `MODIFY` requires `CHANGE_SCOPE` with `MAY_CHANGE` and `MUST_PRESERVE`.
- `DEBUG` requires `DEBUG_SPEC` with `EXPECTED`, `OBSERVED`, and at least one of `REPRODUCTION` or `EVIDENCE`.
- `EVALUATE` requires `EVALUATION_SPEC` with `TARGET`, `PROTOCOL`, and `METRICS`.

## CLI contract

```text
python3 scripts/prompt_lint.py prompt.md [--format text|json]
```

Exit `0` means `READY`, `1` means `NOT_READY`, and `2` means the linter could not read its inputs. Diagnostics include the source line and related conflicting lines.
