---
name: prompt-readiness-gate
description: Validate an ML research/coding Prompt Grammar before project execution. Use only when a project is being initialized with a structured prompt specification, or when the user explicitly asks to revalidate it. Do not use after execution has begun unless revalidation is requested.
---

# Prompt Readiness Gate

## Objective

Act only as a pre-execution validator. Block execution if the agent would need to silently make an unresolved high-impact decision. Do not rewrite the specification or choose missing high-impact decisions.

## Gate

1. Validate before planning, coding, searching, editing, or running experiments.
2. If any blocker exists, stop. Return `NOT_READY`, report blockers, and require the user to revise the specification.
3. If no blocker exists, do not emit a validation report. Treat the original specification unchanged as authoritative and continue the requested work.
4. Re-run only on a revised initialization specification or explicit revalidation request.

## Validation

### 1. Structure

Require substantive content for `MODE`, `TASK`, `GOAL`, `CURRENT_STATE`, `CONSTRAINTS`, `OUTPUT`, and `ACCEPTANCE`.

For `RESEARCH`, also require `HYPOTHESIS` and an `EXPERIMENT` definition sufficient to identify the experimental variable, controls, evaluation protocol, and metrics.

For `MODIFY`, require `CHANGE_SCOPE` and preservation boundaries when existing behavior, data, checkpoints, interfaces, or experiments can be affected.

For `DEBUG`, require the specification to distinguish expected behavior from observed behavior and provide reproduction conditions or available evidence when they are necessary to diagnose the problem.

For `EVALUATE`, require the evaluation target, protocol, and metrics.

Conditional fields may be absent only when clearly not applicable.

### 2. Atomic requirements

Normalize each material decision, constraint, prohibition, experimental control, and acceptance clause internally as:

`condition/scope | subject/variable | modality | action/effect | object/value`

Use `MUST`, `MUST_NOT`, `DELEGATED/MAY`, or descriptive modality. Use this representation only for validation; do not expose it unless needed to explain a blocker.

### 3. Underspecification and determinacy

Identify only decisions necessary for valid execution. A decision is high-impact when different choices could materially change research validity, data or evaluation comparability, system architecture or interfaces, irreversible project state, or major compute/cost.

Every required high-impact decision must be `RESOLVED`, explicitly `DELEGATED`, or `NOT_APPLICABLE`. Any `UNRESOLVED` high-impact decision is a blocker.

Do not demand low-impact implementation details. Do not add requirements merely to make the prompt more complete.

### 4. Ambiguity

Block only when a high-impact clause has multiple reasonable interpretations that could materially change execution. Do not block harmless stylistic vagueness.

### 5. Consistency

Compare atomic clauses governing the same subject, variable, artifact, or behavior. Treat two clauses as contradictory only when their conditions can co-occur and their required actions or effects are mutually incompatible.

Use NLI-style reasoning: `ENTAILMENT`, `NEUTRAL`, or `CONTRADICTION`. `NEUTRAL` is not a conflict. Check condition compatibility before declaring a contradiction.

### 6. Verifiability

`ACCEPTANCE` must provide observable evidence or a decidable completion condition. For research, successful completion means the experiment can validly test the hypothesis; it does not require the hypothesis to be supported.

### 7. Minimality

Treat redundant, duplicated, or low-relevance context as a `WARNING`, not a blocker, unless it creates material ambiguity or conflict.

## Failure output

Output:

`NOT_READY`

Then list only blocking issues using:

`[TYPE] location — problem — what the user must clarify, resolve, or explicitly delegate`

Allowed blocker types: `MISSING`, `AMBIGUOUS`, `UNRESOLVED`, `CONTRADICTION`, `UNVERIFIABLE`.

Optionally add `WARNINGS` for non-blocking redundancy.

Do not propose, infer, or select the substantive answer to any blocker.
