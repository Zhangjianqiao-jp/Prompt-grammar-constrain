# ML Research & Coding Prompt Contract

MODE:
[RESEARCH / IMPLEMENT / MODIFY / DEBUG / EVALUATE]

TASK:
[本次只要求 Agent 完成的任务。]

GOAL:
[期望结果或本次工作要回答的问题。]

HYPOTHESIS:
[仅 RESEARCH：If X, then Y, because Z。]

CURRENT_STATE:
[仅保留理解任务所必需的现状、baseline、相关文件和已知问题。]

INPUTS:
[数据、模型、checkpoint、config、代码或参考资料。无则删除。]

DECISIONS:
[每行：- [scope] subject OP value。已确定且不得重新选择的高影响决策。]
-

CONSTRAINTS:
[无约束可写 NONE；否则保留下列相关类别并使用原子语法。]

COMPUTE:
-

DATA:
-

MODEL:
-

ENVIRONMENT:
-

COMPATIBILITY:
-

REPRODUCIBILITY:
-

TIME / COST:
-

CHANGE_SCOPE:
[仅 MODIFY；必须填写 MAY_CHANGE 与 MUST_PRESERVE。]

MAY_CHANGE:
-

MUST_PRESERVE:
-

EXPERIMENT:
[仅 RESEARCH；以下 material requirement 使用原子语法。]

VARIABLE:
-

CONTROL:
-

TRAINING:
-

EVALUATION:
-

METRICS:
-

SEEDS:
-

DEBUG_SPEC:
[仅 DEBUG。EXPECTED/OBSERVED 写事实；REPRODUCTION/EVIDENCE 至少保留一个。]

EXPECTED:
[预期行为。]

OBSERVED:
[实际行为。]

REPRODUCTION:
[可复现条件。]

EVIDENCE:
[已有日志、错误或观察。]

EVALUATION_SPEC:
[仅 EVALUATE。]

TARGET:
[使用原子语法表达评价对象。]

PROTOCOL:
[使用原子语法表达评价协议。]

METRICS:
-

OUTPUT:
[最终交付的 artifact。]

ACCEPTANCE:
[至少一个可判定的原子检查；result scope 推荐用于最终状态。]

ENGINEERING:
- [result] tests.failed = 0

RESEARCH:
-

DON'T:
[用原子约束表达禁止状态，例如：- [*] data.split != test。]
-

DELEGATED:
[每行：- [scope] subject delegated。]
-

OPEN_QUESTIONS:
[每行：- [HIGH|LOW] subject — question。HIGH 会阻塞执行；无问题写 NONE。]
-

EXECUTION_RULE:
Run the deterministic Prompt Readiness Gate before execution. Do not silently resolve high-impact ambiguity or change declared decisions, constraints, controls, baselines, or evaluation conditions.
