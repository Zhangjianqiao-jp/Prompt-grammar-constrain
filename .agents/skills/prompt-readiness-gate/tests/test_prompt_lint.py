import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prompt_lint", SKILL / "scripts" / "prompt_lint.py"
)
prompt_lint = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = prompt_lint
assert SPEC.loader is not None
SPEC.loader.exec_module(prompt_lint)
PROFILE = json.loads((SKILL / "profiles" / "ml-research.json").read_text())


BASE = """\
MODE:
IMPLEMENT
TASK:
Add a deterministic cache key.
GOAL:
Avoid collisions between model configurations.
CURRENT_STATE:
The cache currently keys only on model name.
DECISIONS:
- [*] cache.hash = sha256
CONSTRAINTS:
COMPATIBILITY:
- [*] python.version >= 3.11
OUTPUT:
Code and tests.
ACCEPTANCE:
ENGINEERING:
- [result] tests.failed = 0
DELEGATED:
- [implementation] helper.naming delegated
OPEN_QUESTIONS:
NONE
"""


def errors(text: str):
    issues, _, _ = prompt_lint.lint(text, PROFILE)
    return [issue for issue in issues if issue.severity == "error"]


class PromptLintTests(unittest.TestCase):
    def test_ready_implement(self):
        self.assertEqual(errors(BASE), [])

    def test_placeholder_is_missing(self):
        result = errors(BASE.replace("Add a deterministic cache key.", "[what to do]"))
        self.assertTrue(
            any(issue.kind == "MISSING" and issue.section == "TASK" for issue in result)
        )

    def test_conflicting_equalities_report_both_lines(self):
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            "- [*] cache.hash = sha256\n- [*] cache.hash = md5",
        )
        result = errors(text)
        contradiction = next(issue for issue in result if issue.kind == "CONTRADICTION")
        self.assertTrue(contradiction.related_lines)

    def test_disjoint_scopes_do_not_conflict(self):
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            "- [train] precision = fp16\n- [eval] precision = fp32",
        )
        self.assertFalse(any(issue.kind == "CONTRADICTION" for issue in errors(text)))

    def test_global_and_specific_scopes_conflict(self):
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            "- [*] precision = fp16\n- [eval] precision = fp32",
        )
        self.assertTrue(any(issue.kind == "CONTRADICTION" for issue in errors(text)))

    def test_empty_numeric_interval_is_a_conflict(self):
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            "- [*] gpu.count >= 8\n- [*] gpu.count <= 4",
        )
        self.assertTrue(any(issue.kind == "CONTRADICTION" for issue in errors(text)))

    def test_equal_integer_and_float_are_not_a_conflict(self):
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            "- [*] batch.size = 1\n- [*] batch.size = 1.0",
        )
        self.assertFalse(any(issue.kind == "CONTRADICTION" for issue in errors(text)))

    def test_non_finite_number_is_rejected(self):
        text = BASE.replace("- [*] python.version >= 3.11", "- [*] loss.max <= NaN")
        self.assertTrue(
            any(
                issue.kind == "SYNTAX" and "non-finite" in issue.message
                for issue in errors(text)
            )
        )

    def test_set_constraints_can_form_three_line_conflict(self):
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            '- [*] precision in ["fp16", "bf16"]\n'
            "- [*] precision != fp16\n"
            "- [*] precision != bf16",
        )
        contradiction = next(
            issue for issue in errors(text) if issue.kind == "CONTRADICTION"
        )
        self.assertEqual(len(contradiction.related_lines), 2)

    def test_high_impact_open_question_blocks(self):
        text = BASE.replace("NONE\n", "- [HIGH] data.split — Which dataset split?\n", 1)
        self.assertTrue(any(issue.kind == "UNRESOLVED" for issue in errors(text)))

    def test_unlabelled_open_question_is_syntax_error(self):
        text = BASE.replace("NONE\n", "- Which dataset split?\n", 1)
        self.assertTrue(any(issue.kind == "SYNTAX" for issue in errors(text)))

    def test_natural_language_constraint_is_rejected(self):
        text = BASE.replace("- [*] python.version >= 3.11", "- Must run on Python 3.11")
        self.assertTrue(
            any(
                issue.kind == "SYNTAX" and issue.section == "COMPATIBILITY"
                for issue in errors(text)
            )
        )

    def test_acceptance_requires_atomic_check(self):
        text = BASE.replace("- [result] tests.failed = 0", "All tests should pass.")
        result = errors(text)
        self.assertTrue(any(issue.kind == "UNVERIFIABLE" for issue in result))

    def test_research_profile_requires_experiment_fields(self):
        text = BASE.replace("IMPLEMENT", "RESEARCH", 1)
        result = errors(text)
        required = {issue.section for issue in result if issue.kind == "MISSING"}
        self.assertTrue(
            {"HYPOTHESIS", "EXPERIMENT", "VARIABLE", "CONTROL", "EVALUATION", "METRICS"}
            <= required
        )

    def test_debug_profile_accepts_reproduction(self):
        addition = """\
DEBUG_SPEC:
EXPECTED:
Requests return HTTP 200.
OBSERVED:
Requests return HTTP 500.
REPRODUCTION:
Run the documented request once.
"""
        text = BASE.replace("IMPLEMENT", "DEBUG", 1).replace(
            "OUTPUT:\n", addition + "OUTPUT:\n"
        )
        self.assertEqual(errors(text), [])

    def test_modify_profile_accepts_explicit_scope(self):
        addition = """\
CHANGE_SCOPE:
MAY_CHANGE:
- [implementation] cache.key = sha256
MUST_PRESERVE:
- [*] public_api.changed = false
"""
        text = BASE.replace("IMPLEMENT", "MODIFY", 1).replace(
            "OUTPUT:\n", addition + "OUTPUT:\n"
        )
        self.assertEqual(errors(text), [])

    def test_evaluate_profile_accepts_atomic_protocol(self):
        addition = """\
EVALUATION_SPEC:
TARGET:
- [eval] evaluation.target = checkpoint-v2
PROTOCOL:
- [eval] evaluation.protocol = official-v1
METRICS:
- [eval] metric.primary = accuracy
"""
        text = BASE.replace("IMPLEMENT", "EVALUATE", 1).replace(
            "OUTPUT:\n", addition + "OUTPUT:\n"
        )
        self.assertEqual(errors(text), [])

    def test_json_cli_contract(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8") as handle:
            handle.write(BASE)
            handle.flush()
            output = io.StringIO()
            with redirect_stdout(output):
                code = prompt_lint.main([handle.name, "--format", "json"])
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "READY")
        self.assertGreater(payload["atomic_requirement_count"], 0)

    def test_duplicate_section_is_rejected(self):
        text = BASE + "TASK:\nA second task.\n"
        self.assertTrue(
            any(
                issue.kind == "SYNTAX" and "duplicate" in issue.message
                for issue in errors(text)
            )
        )

    def test_child_section_in_wrong_parent_is_rejected(self):
        text = BASE.replace(
            "TASK:\n", "VARIABLE:\n- [*] experiment.variable = x\nTASK:\n"
        )
        self.assertTrue(
            any(
                issue.kind == "SYNTAX" and issue.section == "VARIABLE"
                for issue in errors(text)
            )
        )

    def test_inline_mode_value_is_supported(self):
        text = BASE.replace("MODE:\nIMPLEMENT", "MODE: IMPLEMENT")
        self.assertEqual(errors(text), [])

    def test_comments_headings_and_empty_labels_are_not_values(self):
        text = BASE.replace(
            "Add a deterministic cache key.",
            "<!-- comment -->\n# heading\nLabel:\nAdd a deterministic cache key.",
        )
        self.assertEqual(errors(text), [])

    def test_invalid_scalar_and_set_shapes_are_rejected(self):
        invalid_lines = [
            "- [*] model.name = unquoted value",
            '- [*] model.config = {"layers": 2}',
            "- [*] model.layers = [1, 2]",
            "- [*] precision in fp16",
            "- [*] precision in []",
            '- [*] precision in [["fp16"]]',
            "- [*] precision <= fast",
        ]
        for invalid in invalid_lines:
            with self.subTest(invalid=invalid):
                text = BASE.replace("- [*] cache.hash = sha256", invalid)
                self.assertTrue(any(issue.kind == "SYNTAX" for issue in errors(text)))

    def test_missing_cli_input_returns_usage_error(self):
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = prompt_lint.main(["/definitely/not/a/prompt.md"])
        self.assertEqual(code, 2)
        self.assertIn("prompt-lint:", stderr.getvalue())

    def test_text_cli_reports_not_ready_and_warnings(self):
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            "- [*] cache.hash = sha256\n- [*] cache.hash = sha256\n- [*] cache.hash = md5",
        )
        with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            output = io.StringIO()
            with redirect_stdout(output):
                code = prompt_lint.main([handle.name])
        self.assertEqual(code, 1)
        self.assertIn("NOT_READY", output.getvalue())
        self.assertIn("WARNINGS", output.getvalue())


if __name__ == "__main__":
    unittest.main()
