# Compact ML Research & Coding Prompt Template

MODE:
[RESEARCH / IMPLEMENT / MODIFY / DEBUG / EVALUATE]

TASK:
[这次具体要 AI 做什么]

GOAL:
[最终希望达到什么结果]

HYPOTHESIS:
[如果是研究实验：If X, then Y, because Z]
[非研究任务删除]

CURRENT_STATE:
[只写当前任务不可缺少的背景、baseline、相关文件和已知问题]

INPUTS:
[数据 / 模型 / checkpoint / config / 代码 / 参考资料]

DECISIONS:
[已经确定、不允许 AI 重新选择的高影响决策]

CONSTRAINTS:
[算力、数据、模型、环境、兼容性、时间等硬限制]

CHANGE_SCOPE:
[允许修改什么；必须保持什么]
[新项目可删除]

EXPERIMENT:
[研究实验时填写]
- VARIABLE:
- CONTROL:
- METRICS:
- EVALUATION:
- SEED:

OUTPUT:
[最终必须交付什么]

ACCEPTANCE:
[什么条件下工程任务或实验才算完成，并且应尽量可验证]

DON'T:
[禁止的高风险行为]

DELEGATED:
[明确授权 AI 自行决定的低影响事项]

OPEN_QUESTIONS:
[尚未解决的问题；如果会影响实验有效性或高影响决策，则不能直接执行]

RULE:
Do not silently make unresolved high-impact decisions. Preserve all declared decisions, constraints, controls, baselines, and evaluation conditions. If a high-impact ambiguity remains, stop and report it; otherwise execute directly.
