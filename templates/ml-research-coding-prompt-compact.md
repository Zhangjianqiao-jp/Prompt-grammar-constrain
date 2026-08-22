# ML Prompt Grammar v2 · Compact IMPLEMENT Contract

GRAMMAR_VERSION: 2
MODE: IMPLEMENT

TASK:
[单一任务]

GOAL:
[可观察结果]

CURRENT_STATE:
[必要 baseline、文件和已知行为]

ENTITIES:
- tests.failed : integer

SCOPES:
- result

DECISIONS:
NONE

CONSTRAINTS:
NONE

OUTPUT:
[文件或 artifact]

ACCEPTANCE:
ENGINEERING:
- [result] tests.failed = 0

VERIFICATION_PLAN:
- [result] tests.failed <- command:"python3 -m unittest"

DELEGATED:
NONE

OPEN_QUESTIONS:
NONE

RULE:
Run the deterministic Prompt Readiness Gate before execution. Preserve the validated specification unchanged.
