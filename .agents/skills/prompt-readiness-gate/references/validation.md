# Validation Method and Current Evidence

## Evaluation question

The current evidence answers a narrow question:

> For prompts that follow the declared contract, does the deterministic gate correctly enforce its profile and atomic-constraint semantics?

It does not yet answer whether arbitrary real-world prompts contain every necessary decision or are factually correct.

## Method

The evaluation follows the parts of requirements-engineering validation that apply to a deterministic linter:

1. **Labeled, imbalanced classification benchmark.** ALICE evaluates contradiction detection with manually labeled reference and real-world datasets, confusion matrices, precision, recall, accuracy, and runtime. This project mirrors the metric design with a reproducible 1,000-case benchmark containing 5% seeded defects.
   - https://link.springer.com/article/10.1007/s10515-024-00452-x
2. **Behavioral unit and profile tests.** Tests cover every MODE, each blocker class, source locations, CLI exit codes, typed values, scopes, warnings, and malformed syntax. Assertions target observable status and semantic invariants rather than wording.
3. **Independent property oracle.** Five thousand seeded finite-domain constraint systems are evaluated both by the production solver and by a separate exhaustive enumerator.
4. **Metamorphic testing.** Constraint permutation, duplication, and consistent subject renaming must preserve satisfiability; different named scopes must remain independent. Metamorphic testing is a standard response to cases where individual expected outputs are costly to enumerate.
   - https://eprints.whiterose.ac.uk/id/eprint/110335/
   - https://discovery.ucl.ac.uk/id/eprint/1471263/
5. **Robustness testing.** Three thousand seeded random Unicode/ASCII documents and a 100,000-character atomic value check parser determinism and crash resistance.
6. **Coverage.** The suite measures statement coverage, but coverage is treated as supporting evidence rather than a quality score.
7. **Boundary probes.** Deliberately out-of-contract semantic defects are recorded separately so that in-domain metrics are not misrepresented as general natural-language understanding.

## Reproduce

From the repository root:

    python3 -m unittest discover -s .agents/skills/prompt-readiness-gate/tests -v
    python3 .agents/skills/prompt-readiness-gate/tests/run_benchmark.py

Coverage requires the optional coverage package:

    python3 -m coverage run --source=.agents/skills/prompt-readiness-gate/scripts \
      -m unittest discover -s .agents/skills/prompt-readiness-gate/tests
    python3 -m coverage report -m

## Results on 2026-08-22

- 33 behavioral/property/metamorphic/fuzz tests passed.
- 5,000 generated constraint systems matched the independent finite-domain oracle.
- 3,000 fuzz documents were deterministic and crash-free.
- The complete suite passed on Python 3.12.13 and 3.13.1.
- Core linter statement coverage: 96% (404 statements, 17 missed).
- Imbalanced benchmark: TP 50, FP 0, TN 950, FN 0.
- In-contract precision, recall, F1, specificity, and accuracy: 1.0.
- Throughput in the measured local run: approximately 6,286 prompts/second.

One real solver defect was exposed and fixed during this evaluation: an inclusive singleton numeric interval followed by exclusion of that sole value was previously missed.

## Known boundary probes

The following intentionally return READY:

- a contradiction expressed only across prose fields;
- conflicting values written under different subject aliases;
- an atomic acceptance claim referring to evidence that does not exist.

These are not false negatives relative to the declared deterministic contract, but they are false negatives if READY is interpreted as “the complete natural-language prompt is accurate.” The Skill and contract must retain this distinction.

## Threats to validity

- **Constructed benchmark:** The 1,000 cases are generated from known defect operators and are not an independent real-project corpus. Perfect metrics are expected and must not be advertised as external accuracy.
- **External validity:** The profile is ML/coding-specific and has not been evaluated on prompts from multiple organizations, authors, languages, or model ecosystems.
- **Label validity:** No blinded human annotation or inter-rater agreement study has been completed.
- **Semantic coverage:** Facts, omissions not represented by the profile, entity aliasing, condition co-occurrence beyond named scopes, and evidence existence remain outside the solver.
- **Mutation adequacy:** The defect operators cover current rules but are not a comprehensive mutation-testing campaign.

## Next evidence needed

Before claiming general prompt-readiness accuracy:

1. freeze a held-out corpus of real first-turn prompts;
2. have at least two domain reviewers label defects independently and report agreement;
3. preserve natural class imbalance and publish per-defect precision/recall with confidence intervals;
4. compare against the previous LLM-only gate and a no-gate baseline;
5. test whether READY predicts downstream constraint adherence, retry rate, and task success;
6. keep benchmark authors separate from rule changes to reduce overfitting.
