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

BASE_V2 = """\
GRAMMAR_VERSION: 2
MODE: IMPLEMENT
TASK:
Add a deterministic ML checkpoint cache key.
GOAL:
Prevent collisions between training configurations.
CURRENT_STATE:
The cache currently keys only on model name.
ENTITIES:
- cache.hash : enum aliases ["cache.algorithm"]
- python.version : number
- tests.failed : integer
SCOPES:
- implementation
- result
- implementation excludes result
DECISIONS:
- [implementation] cache.hash = sha256
CONSTRAINTS:
COMPATIBILITY:
- [implementation] python.version >= 3.11
OUTPUT:
Code, tests, and a test report.
ACCEPTANCE:
ENGINEERING:
- [result] tests.failed = 0
VERIFICATION_PLAN:
- [result] tests.failed <- command:"python3 -m unittest"
DELEGATED:
NONE
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
        for atom in (
            "- [*] loss.max <= NaN",
            "- [*] loss.max <= 1e999",
            "- [*] loss.max in [0, 1e999]",
        ):
            with self.subTest(atom=atom):
                text = BASE.replace("- [*] python.version >= 3.11", atom)
                self.assertTrue(
                    any(
                        issue.kind == "SYNTAX" and "non-finite" in issue.message
                        for issue in errors(text)
                    )
                )

    def test_very_large_integer_is_canonicalized_without_float_overflow(self):
        huge = "9" * 1_000
        text = BASE.replace(
            "- [*] cache.hash = sha256",
            f"- [*] batch.tokens = {huge}\n- [*] batch.tokens = {huge}",
        )
        issues, atoms, _ = prompt_lint.lint(text, PROFILE)
        huge_atom = next(atom for atom in atoms if atom.subject == "batch.tokens")
        self.assertEqual(prompt_lint.canonical(huge_atom.value), huge)
        self.assertFalse(any(issue.kind == "CONTRADICTION" for issue in issues))

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

    def test_invalid_profile_returns_usage_error(self):
        with (
            tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8") as prompt,
            tempfile.NamedTemporaryFile(
                "w", suffix=".json", encoding="utf-8"
            ) as profile,
        ):
            prompt.write(BASE)
            prompt.flush()
            profile.write("{}")
            profile.flush()
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = prompt_lint.main([prompt.name, "--profile", profile.name])
        self.assertEqual(code, 2)
        self.assertIn("profile field", stderr.getvalue())

    def test_profile_schema_rejects_invalid_root_and_unknown_atomic_section(self):
        with self.assertRaisesRegex(TypeError, "root"):
            prompt_lint.validate_profile([])
        invalid = dict(PROFILE)
        invalid["atomic_sections"] = [*PROFILE["atomic_sections"], "MISSING_SECTION"]
        with self.assertRaisesRegex(ValueError, "unknown sections"):
            prompt_lint.validate_profile(invalid)

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


class PromptGrammarV2Tests(unittest.TestCase):
    def test_v2_ready(self):
        self.assertEqual(errors(BASE_V2), [])

    def test_aliases_share_one_constraint_domain(self):
        text = BASE_V2.replace(
            "- [implementation] cache.hash = sha256",
            "- [implementation] cache.hash = sha256\n"
            "- [implementation] cache.algorithm = md5",
        )
        self.assertTrue(any(issue.kind == "CONTRADICTION" for issue in errors(text)))

    def test_alias_collision_is_rejected(self):
        text = BASE_V2.replace(
            "- python.version : number",
            '- python.version : number aliases ["cache.algorithm"]',
        )
        self.assertTrue(any(issue.kind == "ALIAS_COLLISION" for issue in errors(text)))

    def test_unknown_entity_is_rejected(self):
        text = BASE_V2.replace("cache.hash = sha256", "cache.digest = sha256")
        self.assertTrue(any(issue.kind == "UNKNOWN_ENTITY" for issue in errors(text)))

    def test_type_mismatch_is_rejected(self):
        text = BASE_V2.replace("python.version >= 3.11", "python.version >= fast")
        self.assertTrue(any(issue.kind == "SYNTAX" for issue in errors(text)))

    def test_integer_rejects_fraction(self):
        text = BASE_V2.replace("tests.failed = 0", "tests.failed = 0.5")
        self.assertTrue(any(issue.kind == "TYPE_MISMATCH" for issue in errors(text)))

    def test_unknown_scope_is_rejected(self):
        text = BASE_V2.replace("[implementation] cache.hash", "[training] cache.hash")
        self.assertTrue(any(issue.kind == "UNKNOWN_SCOPE" for issue in errors(text)))

    def test_unspecified_scope_relation_blocks_possible_alias_conflict(self):
        text = BASE_V2.replace(
            "- implementation excludes result",
            "- training",
        ).replace(
            "- [implementation] cache.hash = sha256",
            "- [implementation] cache.hash = sha256\n"
            "- [training] cache.algorithm = md5",
        )
        self.assertTrue(any(issue.kind == "AMBIGUOUS_SCOPE" for issue in errors(text)))

    def test_overlapping_scopes_are_solved_together(self):
        text = BASE_V2.replace(
            "- implementation excludes result",
            "- implementation overlaps result",
        ).replace(
            "- [result] tests.failed = 0",
            "- [result] tests.failed = 0\n- [result] cache.algorithm = md5",
        )
        self.assertTrue(any(issue.kind == "CONTRADICTION" for issue in errors(text)))

    def test_excluded_scopes_are_independent(self):
        text = BASE_V2.replace(
            "- [result] tests.failed = 0",
            "- [result] tests.failed = 0\n- [result] cache.algorithm = md5",
        )
        self.assertFalse(any(issue.kind == "CONTRADICTION" for issue in errors(text)))

    def test_conflicting_scope_relations_are_rejected(self):
        text = BASE_V2.replace(
            "- implementation excludes result",
            "- implementation excludes result\n- result overlaps implementation",
        )
        self.assertTrue(
            any(issue.kind == "CONTRADICTORY_SCOPE_RELATION" for issue in errors(text))
        )

    def test_acceptance_requires_matching_evidence(self):
        text = BASE_V2.replace("tests.failed <-", "cache.hash <-")
        self.assertTrue(any(issue.kind == "MISSING_EVIDENCE" for issue in errors(text)))

    def test_evidence_alias_is_canonicalized(self):
        text = BASE_V2.replace(
            "- [result] tests.failed = 0",
            "- [result] cache.hash = sha256",
        ).replace("tests.failed <-", "cache.algorithm <-")
        self.assertEqual(errors(text), [])

    def test_unknown_evidence_kind_is_rejected(self):
        text = BASE_V2.replace("<- command:", "<- magic:")
        self.assertTrue(
            any(issue.kind == "UNKNOWN_EVIDENCE_KIND" for issue in errors(text))
        )

    def test_missing_v2_sections_is_rejected(self):
        text = BASE_V2.replace("ENTITIES:\n", "")
        self.assertTrue(
            any(
                issue.kind == "MISSING" and issue.section == "ENTITIES"
                for issue in errors(text)
            )
        )

    def test_unsupported_version_is_rejected(self):
        text = BASE_V2.replace("GRAMMAR_VERSION: 2", "GRAMMAR_VERSION: 99")
        self.assertTrue(
            any(issue.kind == "UNSUPPORTED_VERSION" for issue in errors(text))
        )

    def test_checked_in_v2_examples_are_ready(self):
        repository = SKILL.parents[2]
        for name in ("ml-implement-v2.md", "ml-research-v2.md"):
            with self.subTest(name=name):
                text = (repository / "examples" / name).read_text(encoding="utf-8")
                self.assertEqual(errors(text), [])

    def test_ml_semantic_slot_rejects_misfiled_subject(self):
        repository = SKILL.parents[2]
        text = (repository / "examples" / "ml-research-v2.md").read_text(
            encoding="utf-8"
        )
        text = text.replace("experiment.variable =", "model.variant =").replace(
            "- experiment.variable : enum", "- model.variant : enum"
        )
        self.assertTrue(any(issue.kind == "ML_SEMANTIC_SLOT" for issue in errors(text)))

    def test_invalid_entity_declarations_are_rejected(self):
        invalid = [
            "- cache.hash",
            "- cache.hash : enum aliases []",
            '- cache.hash : enum aliases ["bad alias"]',
            "- cache.hash : enum aliases [not-json]",
        ]
        for declaration in invalid:
            with self.subTest(declaration=declaration):
                text = BASE_V2.replace(
                    '- cache.hash : enum aliases ["cache.algorithm"]', declaration
                )
                self.assertTrue(any(issue.kind == "SYNTAX" for issue in errors(text)))

    def test_duplicate_entity_is_rejected(self):
        text = BASE_V2.replace(
            '- cache.hash : enum aliases ["cache.algorithm"]',
            '- cache.hash : enum aliases ["cache.algorithm"]\n- cache.hash : enum',
        )
        self.assertTrue(any(issue.kind == "DUPLICATE_ENTITY" for issue in errors(text)))

    def test_invalid_scope_declarations_are_rejected(self):
        cases = {
            "self relation": "- implementation overlaps implementation",
            "global declaration": "- *",
            "malformed": "- implementation maybe result",
        }
        for name, declaration in cases.items():
            with self.subTest(name=name):
                text = BASE_V2.replace("- implementation", declaration, 1)
                self.assertTrue(errors(text))

    def test_transitive_overlap_cannot_contain_exclusion(self):
        text = BASE_V2.replace(
            "- implementation\n- result\n- implementation excludes result",
            "- implementation\n"
            "- result\n"
            "- evaluation\n"
            "- implementation overlaps evaluation\n"
            "- evaluation overlaps result\n"
            "- implementation excludes result",
        )
        self.assertTrue(
            any(issue.kind == "CONTRADICTORY_SCOPE_MODEL" for issue in errors(text))
        )

    def test_invalid_verification_entries_are_rejected(self):
        invalid = [
            "- tests.failed by command:pytest",
            "- [result] tests.failed <- command:unquoted locator",
            "- [result] tests.failed <- command:42",
            "- [unknown] tests.failed <- command:pytest",
            "- [result] unknown.subject <- command:pytest",
        ]
        for declaration in invalid:
            with self.subTest(declaration=declaration):
                text = BASE_V2.replace(
                    '- [result] tests.failed <- command:"python3 -m unittest"',
                    declaration,
                )
                self.assertTrue(errors(text))

    def test_duplicate_verification_target_warns(self):
        line = '- [result] tests.failed <- command:"python3 -m unittest"'
        issues, _, _ = prompt_lint.lint(
            BASE_V2.replace(line, f"{line}\n{line}"), PROFILE
        )
        self.assertTrue(
            any(
                issue.kind == "REDUNDANT" and issue.severity == "warning"
                for issue in issues
            )
        )

    def test_empty_grammar_version_is_rejected(self):
        text = BASE_V2.replace("GRAMMAR_VERSION: 2", "GRAMMAR_VERSION:")
        self.assertTrue(
            any(
                issue.kind == "MISSING" and issue.section == "GRAMMAR_VERSION"
                for issue in errors(text)
            )
        )


if __name__ == "__main__":
    unittest.main()
