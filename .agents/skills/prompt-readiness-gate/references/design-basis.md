# Design Basis

This gate uses a compiler-like boundary: only properties represented in an explicit grammar are claimed as deterministic. The runtime Skill delegates validation to code; it does not ask the same model that will execute the task to judge whether its input is good enough.

## Why a controlled contract

CNL-P describes a two-stage linter that parses controlled prompt text into an AST-like representation and then traverses it for semantic checks. That is the closest direct precedent for treating prompts as statically analyzable interfaces:

- https://arxiv.org/abs/2508.06942

Work on prompt underspecification shows why a gate is useful but also why “add every possible requirement” is not a safe solution: omitted requirements are unstable across model or prompt changes, while instruction competition can make longer prompts worse. This motivates mode-specific minimum fields and a compact atomic notation:

- https://arxiv.org/abs/2505.13360

ALICE and requirements-engineering NLI work show that contradiction detection benefits from decomposing requirements and distinguishing true incompatibility from mere semantic difference:

- https://link.springer.com/article/10.1007/s10515-024-00452-x
- https://arxiv.org/abs/2405.05135

## Implemented deterministic pipeline

    Markdown contract
      -> section lexer with source locations
      -> MODE/profile schema checks
      -> typed atomic requirements
      -> per-subject/per-scope constraint domains
      -> READY or line-addressed NOT_READY diagnostics

The profile implements conditional required fields in the same general spirit as JSON Schema's conditional and dependent validation:

- https://json-schema.org/understanding-json-schema/reference/conditionals

Atomic requirements use the form [scope] subject operator value.

The solver intersects equality, exclusion, numeric-bound, and finite-set constraints. It detects pairwise and multi-line empty domains and returns the contributing source lines. This is deterministic, offline, and has no model or third-party runtime dependency.

## Deliberate limits

READY means:

- the document parses under the selected profile;
- mode-specific required information is present;
- machine-checked material clauses are well typed;
- no represented constraint domain is empty;
- no high-impact question is explicitly left open;
- acceptance contains at least one atomic observable condition.

It does **not** prove:

- that factual claims are true;
- that the user identified every domain requirement;
- that two opaque prose passages are semantically equivalent;
- that differently named subjects refer to the same real entity;
- that implementation will satisfy the contract.

Those claims require external evidence, a project-specific ontology, or probabilistic semantic models. The validator reports unsupported syntax instead of silently converting free prose into formal constraints. This avoids disguising model interpretation as formal verification.

For richer arithmetic or Boolean conditions, the atomic IR can later be compiled to SMT. Z3 supports satisfiability checks and unsatisfiable cores, which could preserve the current line-addressed diagnostic model:

- https://microsoft.github.io/z3guide/docs/logic/basiccommands/
- https://microsoft.github.io/z3guide/programming/Parameters/

An optional NLI stage may later propose candidate pairs or canonical subjects, but its output should remain advisory until confirmed or converted into explicit atoms. It must not weaken the deterministic hard gate.

This reference is retained for provenance and future development. Normal validation does not load it into model context.
