# Cross-domain Porting Notes

Status: design note for future work. The shipped validator is intentionally
limited to machine-learning research and coding tasks.

## Reusable kernel

The following mechanisms are domain-independent and should remain in the core:

1. Markdown section lexer with source locations and stable diagnostics.
2. Versioned profiles and conditional required sections.
3. Typed entities, explicit aliases, and canonical identifiers.
4. Named scopes with explicit `overlaps` / `excludes` semantics.
5. Atomic equality, exclusion, numeric-bound, and finite-set constraints.
6. High/low open questions and explicit delegation.
7. Acceptance assertions separated from verification plans.
8. JSON output, deterministic exit codes, property tests, fuzzing, and mutation
   benchmarks.

These components define a small validation engine. They do not define what a
complete prompt means in a new domain.

## Domain-owned components

Every new domain needs an independently reviewed profile containing:

- task modes and mode-specific required slots;
- a canonical entity vocabulary and alias policy;
- allowed evidence kinds and observability rules;
- domain invariants that can be compiled to atomic constraints;
- templates and valid/invalid examples;
- a labeled evaluation corpus created by domain reviewers;
- downstream outcome metrics that test whether `READY` predicts useful work.

Copying the ML profile and renaming headings is not sufficient. For example,
medical tasks need patient-safety and evidence provenance rules; finance needs
time, jurisdiction, and risk semantics; data engineering needs schema, lineage,
freshness, and idempotency. Those are ontology and validation-policy changes,
not presentation changes.

## Recommended porting sequence

1. Freeze the core grammar version and create a new profile file.
2. Interview at least two practitioners and collect real first-turn prompts.
3. Define domain modes, high-impact omissions, entities, and observable outputs.
4. Write the profile and templates before adding new solver operators.
5. Label a held-out corpus with multiple reviewers; report agreement.
6. Add unit, property, metamorphic, fuzz, mutation, and regression tests.
7. Measure both static defect detection and downstream task outcomes.
8. Publish capability boundaries separately from benchmark results.

## Extension points not yet implemented

- project-provided entity catalogs layered over a domain profile;
- Boolean conditions and implication (`if`, `only if`) compiled to SMT;
- unit-aware quantities and dimensional analysis;
- traceability IDs across spec, plan, implementation, and evidence;
- optional NLI suggestions that propose aliases or suspicious prose pairs but
  never override the deterministic hard gate;
- runtime evidence adapters that execute approved checks after implementation.

## Compatibility rule

Core changes must not silently alter an existing profile's meaning. Introduce a
new grammar/profile version, preserve stable diagnostic codes where possible,
and keep migration fixtures for every previously supported version.
