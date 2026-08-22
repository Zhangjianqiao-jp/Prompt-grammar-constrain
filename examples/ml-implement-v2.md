GRAMMAR_VERSION: 2
MODE: IMPLEMENT

TASK:
Add deterministic checkpoint cache keys that include the model revision.

GOAL:
Prevent two revisions of the same model from sharing a cache entry.

CURRENT_STATE:
The cache key includes model name but omits revision.

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
Implementation, unit tests, and a test report.

ACCEPTANCE:
ENGINEERING:
- [result] tests.failed = 0

VERIFICATION_PLAN:
- [result] tests.failed <- command:"python3 -m unittest"

DELEGATED:
NONE

OPEN_QUESTIONS:
NONE

EXECUTION_RULE:
Run the deterministic Prompt Readiness Gate before execution and preserve the
validated contract unchanged.
