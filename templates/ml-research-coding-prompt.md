# ML Prompt Grammar v2 · Full Contract

GRAMMAR_VERSION: 2

MODE:
[RESEARCH / IMPLEMENT / MODIFY / DEBUG / EVALUATE]

TASK:
[本次只要求 Agent 完成的一项任务。]

GOAL:
[期望的可观察结果，或本次实验要回答的问题。]

HYPOTHESIS:
[仅 RESEARCH：If X, then Y, because Z。]

CURRENT_STATE:
[baseline、相关代码/配置、已知行为；只保留理解任务所必需的事实。]

INPUTS:
[数据集、split、模型/checkpoint、config、代码或参考资料；无则删除本节。]

ENTITIES:
[声明下文所有原子约束使用的 subject。语法：- subject : TYPE aliases ["alias"]。]
[TYPE = integer | number | boolean | string | path | enum | any；无别名可省略 aliases。]
- tests.failed : integer

SCOPES:
[逐行声明所用命名 scope；* 为隐式全局 scope，不声明。]
[同一 subject 出现在两个 scope 时，必须声明：- a overlaps b 或 - a excludes b。]
- result

DECISIONS:
[已确定且不得重新选择的高影响决策；原子语法：- [scope] subject OP value。无则 NONE。]
NONE

CONSTRAINTS:
[保留适用子节；每行一个原子约束。]

COMPUTE:
NONE

DATA:
NONE

MODEL:
NONE

ENVIRONMENT:
NONE

COMPATIBILITY:
NONE

REPRODUCIBILITY:
NONE

TIME / COST:
NONE

CHANGE_SCOPE:
[仅 MODIFY；必须填写 MAY_CHANGE 与 MUST_PRESERVE，否则删除本组。]

MAY_CHANGE:
- [implementation] component.change = allowed

MUST_PRESERVE:
- [*] public_api.changed = false

EXPERIMENT:
[仅 RESEARCH；v2 必须显式给出以下六项，包括“不训练”等负事实。]

VARIABLE:
- [experiment] experiment.variable = treatment-name

CONTROL:
- [experiment] experiment.control = baseline-name

TRAINING:
- [train] training.performed = false

EVALUATION:
- [eval] evaluation.protocol = protocol-id

METRICS:
- [eval] metric.primary = accuracy

SEEDS:
- [experiment] reproducibility.seeds in [17, 23, 42]

DEBUG_SPEC:
[仅 DEBUG。EXPECTED/OBSERVED 必填；REPRODUCTION/EVIDENCE 至少保留一项。]

EXPECTED:
[预期行为。]

OBSERVED:
[实际行为。]

REPRODUCTION:
[最小复现步骤与环境。]

EVIDENCE:
[已有错误、日志或观察。]

EVALUATION_SPEC:
[仅 EVALUATE。]

TARGET:
- [eval] evaluation.target = checkpoint-id

PROTOCOL:
- [eval] evaluation.protocol = protocol-id

METRICS:
- [eval] metric.primary = accuracy

OUTPUT:
[最终交付的文件、报告、模型或数据 artifact。]

ACCEPTANCE:
[至少一个可判定的原子断言；每个断言必须在 VERIFICATION_PLAN 中有同 scope 或 * 的证据计划。]

ENGINEERING:
- [result] tests.failed = 0

RESEARCH:
NONE

VERIFICATION_PLAN:
[语法：- [scope] subject <- KIND:locator。KIND = command | artifact | metric | observation。]
[这里只声明如何验证，不会执行命令，也不声称 artifact 已存在。]
- [result] tests.failed <- command:"python3 -m unittest"

DON'T:
[用原子约束表达禁止状态，例如：- [*] data.test_leakage = false。无则 NONE。]
NONE

DELEGATED:
[语法：- [scope] subject delegated。无则 NONE。]
NONE

OPEN_QUESTIONS:
[语法：- [HIGH|LOW] subject — question。HIGH 会阻塞执行；无问题写 NONE。]
NONE

EXECUTION_RULE:
Run the deterministic Prompt Readiness Gate before execution. Preserve the validated specification; never infer a missing high-impact ML decision.
