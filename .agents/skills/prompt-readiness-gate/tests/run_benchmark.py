"""Run a reproducible, imbalanced readiness benchmark and print JSON metrics."""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass

from test_prompt_lint import BASE, PROFILE, prompt_lint


@dataclass(frozen=True)
class Case:
    name: str
    prompt: str
    has_defect: bool
    expected_kind: str | None = None


def mutation_cases() -> list[Case]:
    mutations = [
        (
            "missing-task",
            lambda text: text.replace("Add a deterministic cache key.", "[missing]"),
            "MISSING",
        ),
        (
            "invalid-mode",
            lambda text: text.replace("IMPLEMENT", "DEPLOY", 1),
            "SYNTAX",
        ),
        (
            "opaque-material-constraint",
            lambda text: text.replace(
                "- [*] python.version >= 3.11", "- Must use Python 3.11"
            ),
            "SYNTAX",
        ),
        (
            "conflicting-equality",
            lambda text: text.replace(
                "- [*] cache.hash = sha256",
                "- [*] cache.hash = sha256\n- [*] cache.hash = md5",
            ),
            "CONTRADICTION",
        ),
        (
            "unresolved-high-question",
            lambda text: text.replace(
                "OPEN_QUESTIONS:\nNONE",
                "OPEN_QUESTIONS:\n- [HIGH] data.split — Which split?",
            ),
            "UNRESOLVED",
        ),
        (
            "unverifiable-acceptance",
            lambda text: text.replace(
                "- [result] tests.failed = 0", "All tests should pass."
            ),
            "UNVERIFIABLE",
        ),
        (
            "duplicate-section",
            lambda text: text + "\nTASK:\nA second task.\n",
            "SYNTAX",
        ),
        (
            "bad-delegation",
            lambda text: text.replace(
                "- [implementation] helper.naming delegated",
                "- Let the agent choose helper naming",
            ),
            "SYNTAX",
        ),
        (
            "excluded-singleton-domain",
            lambda text: text.replace(
                "- [*] cache.hash = sha256",
                "- [*] workers >= 2\n- [*] workers <= 2\n- [*] workers != 2",
            ),
            "CONTRADICTION",
        ),
        (
            "unknown-section",
            lambda text: text.replace("OUTPUT:\n", "UNSUPPORTED:\nvalue\nOUTPUT:\n"),
            "SYNTAX",
        ),
    ]
    cases = []
    for repeat in range(5):
        for name, mutate, expected_kind in mutations:
            cases.append(Case(f"{name}-{repeat}", mutate(BASE), True, expected_kind))
    return cases


def ready_cases(count: int) -> list[Case]:
    cases = []
    for index in range(count):
        prompt = BASE.replace("sha256", f"sha256-v{index}")
        if index % 3 == 0:
            prompt = prompt.replace(
                "- [*] python.version >= 3.11",
                "- [*] python.version >= 3.11\n- [*] python.version < 4",
            )
        if index % 5 == 0:
            prompt = prompt.replace(
                "OPEN_QUESTIONS:\nNONE",
                "OPEN_QUESTIONS:\n- [LOW] logging.format — JSON or text?",
            )
        cases.append(Case(f"ready-{index}", prompt, False))
    return cases


def predict(prompt: str) -> tuple[bool, set[str]]:
    issues, _, _ = prompt_lint.lint(prompt, PROFILE)
    errors = [issue for issue in issues if issue.severity == "error"]
    return bool(errors), {issue.kind for issue in errors}


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def boundary_probes() -> dict[str, str]:
    probes = {
        "contradiction-only-in-prose": BASE.replace(
            "Avoid collisions between model configurations.",
            "Do not change the cache key, although TASK requires changing it.",
        ),
        "subject-aliasing": BASE.replace(
            "- [*] cache.hash = sha256",
            "- [*] data.split = official\n- [*] dataset.partition = custom",
        ),
        "acceptance-not-executed": BASE.replace(
            "- [result] tests.failed = 0",
            "- [result] nonexistent.test_suite.failed = 0",
        ),
    }
    return {
        name: "NOT_READY" if predict(prompt)[0] else "READY"
        for name, prompt in probes.items()
    }


def main() -> int:
    cases = ready_cases(950) + mutation_cases()
    random.Random(20260822).shuffle(cases)
    tp = tn = fp = fn = wrong_kind = 0
    start = time.perf_counter()
    for case in cases:
        predicted_defect, kinds = predict(case.prompt)
        if case.has_defect and predicted_defect:
            tp += 1
            if case.expected_kind not in kinds:
                wrong_kind += 1
        elif case.has_defect:
            fn += 1
        elif predicted_defect:
            fp += 1
        else:
            tn += 1
    elapsed = time.perf_counter() - start
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    result = {
        "seed": 20260822,
        "cases": len(cases),
        "defect_prevalence": ratio(tp + fn, len(cases)),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "metrics": {
            "accuracy": ratio(tp + tn, len(cases)),
            "precision": precision,
            "recall": recall,
            "f1": ratio(2 * precision * recall, precision + recall),
            "specificity": ratio(tn, tn + fp),
        },
        "wrong_defect_kind": wrong_kind,
        "elapsed_seconds": round(elapsed, 6),
        "cases_per_second": round(ratio(len(cases), elapsed), 1),
        "known_boundary_probes": boundary_probes(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if fp == fn == wrong_kind == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
