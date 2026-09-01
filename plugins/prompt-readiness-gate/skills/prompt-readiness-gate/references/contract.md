# ML Prompt Grammar v2 Contract

Prompt Grammar is a controlled Markdown contract for first-turn machine-learning
research and coding tasks. Free text carries intent and context. Every material
decision, constraint, prohibition, and acceptance condition is represented as a
typed atom that the linter can check without an LLM.

## Document model

`GRAMMAR_VERSION: 2` enables the strict contract. Omitting the section selects
legacy v1 behavior.

All section labels are uppercase and end in `:`. The selected `MODE` is one of
`RESEARCH`, `IMPLEMENT`, `MODIFY`, `DEBUG`, or `EVALUATE`. Every mode requires
`TASK`, `GOAL`, `CURRENT_STATE`, `OUTPUT`, and atomic `ACCEPTANCE`.

Additional mode requirements:

- `RESEARCH`: `HYPOTHESIS`; `VARIABLE`, `CONTROL`, `TRAINING`, `EVALUATION`,
  `METRICS`, and `SEEDS` under `EXPERIMENT`.
- `MODIFY`: `MAY_CHANGE` and `MUST_PRESERVE` under `CHANGE_SCOPE`.
- `DEBUG`: `EXPECTED`, `OBSERVED`, and at least one of `REPRODUCTION` or
  `EVIDENCE` under `DEBUG_SPEC`.
- `EVALUATE`: `TARGET`, `PROTOCOL`, and `METRICS` under `EVALUATION_SPEC`.

`NONE`, `N/A`, `NOT_APPLICABLE`, bracketed template hints, comments, and empty
bullets are not substantive values. Delete mode-specific sections that do not
apply.

## Compact grammar

```ebnf
entity      = "-", subject, ":", type, ["aliases", json_string_array] ;
scope       = "-", scope_name
            | "-", scope_name, ("overlaps" | "excludes"), scope_name ;
atom        = "-", "[", scope_name | "*", "]", subject, op, value ;
delegation  = "-", "[", scope_name | "*", "]", subject, "delegated" ;
question    = "-", "[", "HIGH" | "LOW", "]", subject, "—", text ;
verification= "-", "[", scope_name | "*", "]", subject,
              "<-", evidence_kind, ":", string ;
subject     = letter, { letter | digit | "_" | "." | "-" } ;
op          = "=" | "!=" | "<" | "<=" | ">" | ">=" | "in" | "not-in" ;
type        = "integer" | "number" | "boolean" | "string" | "path"
            | "enum" | "any" ;
evidence_kind = "command" | "artifact" | "metric" | "observation" ;
```

Values are JSON scalars or bare identifiers without spaces. `in` and `not-in`
require a non-empty JSON array of scalar values. Ordered comparisons require a
numeric value and an entity declared as `integer` or `number`.

## Entities and aliases

Every atomic subject and verification target must be declared:

```text
ENTITIES:
- data.split : enum aliases ["dataset.partition"]
- gpu.count : integer
- tests.failed : integer
```

Aliases are canonicalized before duplicate and contradiction checks. An alias
collision, undeclared subject, or type mismatch is a blocking diagnostic. The
linter never guesses that two undeclared names mean the same thing.

## Scope semantics

`*` is an implicit global scope and combines with every named scope. All named
scopes must be declared:

```text
SCOPES:
- train
- eval
- result
- train excludes eval
- eval overlaps result
```

`overlaps` means the contexts may coexist and their constraints are solved in
one conservative constraint family. This relation is transitive in v2.
`excludes` means the contexts cannot coexist and their constraints are solved
independently. If the same canonical subject occurs in two scopes and neither
relationship is known, the linter returns `AMBIGUOUS_SCOPE` instead of assuming.

## Atomic semantics

```text
DECISIONS:
- [*] data.split = official-test

CONSTRAINTS:
COMPUTE:
- [train] gpu.count <= 4
MODEL:
- [train] precision in ["fp16", "bf16"]

DON'T:
- [*] data.test_leakage = false
```

For each canonical subject and co-occurring scope family, the solver intersects
equalities, exclusions, numeric intervals, and finite sets. An empty domain is a
`CONTRADICTION`; diagnostics identify the first and related source lines.

## Acceptance and evidence plans

Acceptance declares the desired future state. `VERIFICATION_PLAN` declares how
that state will be observed:

```text
ACCEPTANCE:
ENGINEERING:
- [result] tests.failed = 0
- [result] metric.accuracy >= 0.90

VERIFICATION_PLAN:
- [result] tests.failed <- command:"python3 -m unittest"
- [result] metric.accuracy <- artifact:"artifacts/metrics.json"
```

Each acceptance atom needs a verification entry for the same subject and the
same scope (or global `*`). The linter validates the plan; it deliberately does
not execute commands, open artifacts, or claim that results already satisfy the
assertions. Runtime verification is a separate phase.

## Questions and delegation

```text
DELEGATED:
- [implementation] helper.naming delegated

OPEN_QUESTIONS:
- [HIGH] data.split — Which split is authoritative?
- [LOW] logging.format — JSON or text?
```

An unresolved `HIGH` question blocks execution. A `LOW` question is recorded but
does not block. Delegation must be explicit and does not silently resolve an
open high-impact question.

## Status and CLI

```text
python3 scripts/prompt_lint.py prompt.md [--format text|json]
```

- Exit `0`: `READY` under the declared grammar/profile.
- Exit `1`: `NOT_READY`; revise the source locations in diagnostics.
- Exit `2`: input/profile could not be read.

`READY` proves structural completeness, represented consistency, explicit
high-impact decisions/questions, and a verification plan. It does not prove
external facts, detect contradictions hidden only in prose, infer omitted ML
requirements, or predict that implementation will pass acceptance checks.
