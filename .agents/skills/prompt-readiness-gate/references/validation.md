# Validation Method and Evidence

## Evaluation claim

The current evidence answers this bounded question:

> For first-turn ML prompts that use the declared contract, does the
> deterministic gate enforce the versioned profile, entity/type system, alias
> semantics, scope model, atomic constraints, and acceptance/evidence mapping?

It does not establish accuracy on arbitrary natural-language prompts or prove
that `READY` predicts successful ML work in the field.

## Test strategy

1. **Behavioral and profile tests.** Every mode, blocker family, source-location
   contract, CLI status, typed value, alias rule, scope relation, evidence rule,
   warning, and representative malformed input has an observable assertion.
2. **Compatibility tests.** Legacy prompts without `GRAMMAR_VERSION` retain v1
   semantics. Checked-in v2 examples must remain `READY`.
3. **Independent property oracle.** Five thousand seeded finite-domain systems
   are evaluated by both the production solver and an independent exhaustive
   enumerator.
4. **Metamorphic testing.** Permutation, duplicate insertion, and consistent
   rename must preserve satisfiability. This follows the use of metamorphic
   relations where individual test oracles are expensive:
   [survey](https://eprints.whiterose.ac.uk/id/eprint/110335/),
   [oracle survey](https://discovery.ucl.ac.uk/id/eprint/1471263/).
5. **Robustness testing.** Three thousand seeded random Unicode/ASCII documents
   and a 100,000-character atomic value check determinism and crash resistance.
6. **Mutation benchmark.** Defect operators inject missing fields, malformed
   atoms, constraint contradictions, unresolved questions, alias conflicts,
   type errors, unknown symbols, ambiguous/contradictory scope relations, and
   missing/invalid evidence plans.
7. **Imbalanced classification.** The reproducible benchmark has 2,000 cases and
   5% seeded defects. It reports a confusion matrix, precision, recall, F1,
   specificity, wrong defect kind, and throughput. This mirrors the
   defect-specific reporting used by
   [ALICE](https://link.springer.com/article/10.1007/s10515-024-00452-x).
8. **Coverage and multi-version execution.** Statement coverage is supporting
   evidence, not a quality score. The complete suite runs on two Python minors.
9. **Boundary probes.** Out-of-contract defects are recorded separately so
   in-domain scores are not misrepresented as general language understanding.

## Reproduce

From the repository root:

```bash
python3 -m unittest discover \
  -s .agents/skills/prompt-readiness-gate/tests -v

python3 .agents/skills/prompt-readiness-gate/tests/run_benchmark.py
```

Coverage uses the optional `coverage` package:

```bash
coverage run --source=.agents/skills/prompt-readiness-gate/scripts \
  -m unittest discover -s .agents/skills/prompt-readiness-gate/tests
coverage report -m
```

Static style checks use Ruff:

```bash
ruff check .agents/skills/prompt-readiness-gate
ruff format --check .agents/skills/prompt-readiness-gate
```

## Results — 2026-08-22

- 61 unit/property/metamorphic/fuzz tests passed on Python 3.11.11, 3.12.8,
  and 3.13.1.
- 5,000 generated constraint systems matched the independent exhaustive oracle.
- 3,000 fuzz documents were deterministic and crash-free.
- Core linter statement coverage: 97% (692 statements, 19 missed).
- Ruff lint and format checks passed.
- 2,000-case benchmark at 5% defect prevalence:
  - TP 100, FP 0, TN 1900, FN 0;
  - precision 1.0, recall 1.0, F1 1.0, specificity 1.0;
  - zero wrong defect-kind classifications;
  - approximately 6,024 prompts/second in the recorded local run.

The earlier test campaign exposed and fixed an actual solver defect: the
inclusive singleton interval `x >= 2`, `x <= 2`, followed by `x != 2` was not
recognized as unsatisfiable. Grammar v2 testing additionally closes two explicit
v1 boundary gaps: declared subject aliases are canonicalized, and unknown scope
co-occurrence is blocking.

## Boundary probes

| Probe | v1 | v2 | Reason |
|---|---|---|---|
| contradiction only in free prose | `READY` | `READY` | prose semantics are outside the formal claim |
| conflicting declared aliases | `READY` | `NOT_READY` | v2 has an explicit alias table |
| acceptance without evidence plan | `READY` | `NOT_READY` | v2 requires assertion-to-plan mapping |
| plan points to a nonexistent artifact | n/a | `READY` | the static gate validates the plan, not runtime evidence |

These are expected product boundaries, not hidden exceptions. A runtime verifier
would be required to check commands, artifacts, and observed outcomes after
implementation.

## Threats to validity

- **Constructed benchmark.** The 2,000 cases are generated from known rules and
  mutation operators. Perfect metrics are expected and cannot be advertised as
  real-project accuracy.
- **Rule-author overlap.** Benchmark authors also implemented the rules, creating
  risk of confirmation bias and mutation overfitting.
- **External validity.** No frozen multi-organization corpus of real first-turn
  ML prompts has been evaluated.
- **Label validity.** No blinded human annotation, adjudication protocol, or
  inter-rater agreement study has been completed.
- **Semantic coverage.** Facts, causal validity, prose-only conflicts, missing
  stakeholder intent, units, and undeclared aliases remain outside the solver.
- **Outcome validity.** Static `READY` has not yet been correlated with fewer
  retries, higher constraint adherence, scientific validity, or task success.
- **Performance validity.** Throughput is a single local wall-clock measurement,
  not a controlled benchmark across machines or file sizes.
- **Security validity.** Random-input robustness is not a security audit.

## Evidence required for a production accuracy claim

1. Freeze and version an anonymized corpus of real first-turn ML prompts.
2. Define a reviewer handbook and have at least two ML practitioners label each
   prompt independently.
3. Report Cohen's kappa (or another justified agreement statistic), adjudication,
   class prevalence, per-defect precision/recall, and confidence intervals.
4. Keep a held-out test split unavailable to rule authors during development.
5. Compare no gate, LLM-only review, Grammar v1, and Grammar v2.
6. Measure downstream constraint adherence, clarification count, retry rate,
   experiment reproducibility, and task success.
7. Evaluate false-positive cost: a safe gate that blocks most valid prompts is
   not useful.
8. Have an independent reviewer reproduce the benchmark and inspect failures.

Until that study exists, the correct status is **deterministic contract validator
with strong in-contract regression evidence**, not a universally accurate prompt
judge.
