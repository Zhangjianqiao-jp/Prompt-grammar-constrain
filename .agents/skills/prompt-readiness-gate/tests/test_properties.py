import random
import string
import unittest

from test_prompt_lint import BASE, PROFILE, prompt_lint

DOMAIN = (-2, -1, 0, 1, 2)


def satisfied(candidate, atom):
    if atom.op == "=":
        return candidate == atom.value
    if atom.op == "!=":
        return candidate != atom.value
    if atom.op == "<":
        return candidate < atom.value
    if atom.op == "<=":
        return candidate <= atom.value
    if atom.op == ">":
        return candidate > atom.value
    if atom.op == ">=":
        return candidate >= atom.value
    if atom.op == "in":
        return candidate in atom.value
    if atom.op == "not-in":
        return candidate not in atom.value
    raise AssertionError(f"unsupported oracle operator: {atom.op}")


def oracle_unsat(atoms):
    return not any(
        all(satisfied(candidate, atom) for atom in atoms) for candidate in DOMAIN
    )


def generated_case(rng, size):
    atoms = [prompt_lint.Atom("*", "x", "in", list(DOMAIN), "DECISIONS", 1)]
    for line in range(2, size + 2):
        op = rng.choice(("=", "!=", "<", "<=", ">", ">=", "in", "not-in"))
        if op in {"in", "not-in"}:
            count = rng.randint(1, len(DOMAIN))
            value = rng.sample(DOMAIN, count)
        else:
            value = rng.choice(DOMAIN)
        atoms.append(prompt_lint.Atom("*", "x", op, value, "DECISIONS", line))
    return atoms


class ConstraintProperties(unittest.TestCase):
    def test_solver_matches_independent_finite_domain_oracle(self):
        rng = random.Random(20260822)
        for case_number in range(5000):
            atoms = generated_case(rng, rng.randint(0, 9))
            expected = oracle_unsat(atoms)
            actual = prompt_lint.contradiction_for_group(atoms) is not None
            self.assertEqual(
                actual,
                expected,
                f"case={case_number} atoms={atoms}",
            )

    def test_permutation_does_not_change_satisfiability(self):
        rng = random.Random(99173)
        for case_number in range(1000):
            atoms = generated_case(rng, rng.randint(1, 12))
            expected = prompt_lint.contradiction_for_group(atoms) is not None
            rng.shuffle(atoms)
            actual = prompt_lint.contradiction_for_group(atoms) is not None
            self.assertEqual(actual, expected, f"case={case_number}")

    def test_duplicate_constraint_does_not_change_satisfiability(self):
        rng = random.Random(441)
        for case_number in range(1000):
            atoms = generated_case(rng, rng.randint(1, 12))
            expected = prompt_lint.contradiction_for_group(atoms) is not None
            atoms.append(rng.choice(atoms))
            actual = prompt_lint.contradiction_for_group(atoms) is not None
            self.assertEqual(actual, expected, f"case={case_number}")

    def test_consistent_subject_rename_does_not_change_result(self):
        atoms = generated_case(random.Random(7), 12)
        renamed = [
            prompt_lint.Atom(
                atom.scope,
                "renamed.subject",
                atom.op,
                atom.value,
                atom.section,
                atom.line,
            )
            for atom in atoms
        ]
        self.assertEqual(
            bool(prompt_lint.check_contradictions(atoms)),
            bool(prompt_lint.check_contradictions(renamed)),
        )

    def test_singleton_numeric_domain_excluded_is_unsatisfiable(self):
        atoms = [
            prompt_lint.Atom("*", "workers", ">=", 2, "CONSTRAINTS", 1),
            prompt_lint.Atom("*", "workers", "<=", 2, "CONSTRAINTS", 2),
            prompt_lint.Atom("*", "workers", "!=", 2, "CONSTRAINTS", 3),
        ]
        self.assertIsNotNone(prompt_lint.contradiction_for_group(atoms))

    def test_different_named_scopes_are_independent(self):
        atoms = [
            prompt_lint.Atom("train", "precision", "=", "fp16", "DECISIONS", 1),
            prompt_lint.Atom("eval", "precision", "=", "fp32", "DECISIONS", 2),
        ]
        self.assertEqual(prompt_lint.check_contradictions(atoms), [])


class ParserRobustnessProperties(unittest.TestCase):
    def test_seeded_fuzz_inputs_never_crash_and_are_deterministic(self):
        rng = random.Random(8675309)
        alphabet = string.ascii_letters + string.digits + "[]{}:-_*/'\n\t 中文🙂"
        for case_number in range(3000):
            text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 800)))
            first = prompt_lint.lint(text, PROFILE)
            second = prompt_lint.lint(text, PROFILE)
            self.assertEqual(first, second, f"case={case_number}")

    def test_very_long_atomic_value_does_not_crash(self):
        text = BASE.replace("sha256", "a" * 100_000)
        issues, atoms, mode = prompt_lint.lint(text, PROFILE)
        self.assertEqual(mode, "IMPLEMENT")
        self.assertTrue(atoms)
        self.assertFalse(any(issue.kind == "CONTRADICTION" for issue in issues))


if __name__ == "__main__":
    unittest.main()
