# ML Research & Coding Prompt Grammar

MODE:
[RESEARCH / IMPLEMENT / MODIFY / DEBUG / EVALUATE]

TASK:
[明确描述本次只需要 AI 完成的具体任务。不要写长期目标。]

GOAL:
[本次任务最终希望达到的结果，或者希望通过本次工作回答的问题。]

HYPOTHESIS:
[如果本次任务属于研究实验，写清楚待验证的假设。]
[推荐结构：If ..., then ..., because ...]
[非研究实验任务可删除本模块。]

CURRENT_STATE:
[只写理解当前任务不可缺少的现状。]
- Current model:
- Current pipeline:
- Current baseline:
- Current performance:
- Relevant files:
- Completed work:
- Known problems:

INPUTS:
[只保留当前任务实际涉及的项目。]
- DATA:
- MODEL:
- CHECKPOINT:
- CONFIG:
- CODE:
- REFERENCES:

DECISIONS:
[填写已经由我确定的高影响决策。AI 不应重新选择或修改这些决策。]
- 
- 

CONSTRAINTS:
[填写当前任务必须遵守的硬性限制。没有相关限制的类别直接删除。]

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
[修改已有项目时使用。新项目可以删除本模块。]

MAY_CHANGE:
- 

MUST_PRESERVE:
- 

EXPERIMENT:
[如果本任务涉及机器学习实验，明确实验设计。非实验任务可以删除。]

VARIABLE:
[本次实验主动改变的变量。]

CONTROL:
[为了保证公平比较，需要保持不变的变量。]

TRAINING:
- Dataset / split:
- Training strategy:
- Hyperparameters:
- Epochs / steps:
- Batch size:
- Optimizer:
- Learning rate:
- Seed:

EVALUATION:
- Evaluation dataset:
- Evaluation protocol:
- Baseline:
- Comparison method:

METRICS:
- Primary metric:
- Secondary metrics:

SEEDS:
- 

OUTPUT:
[明确要求最终交付的 artifact，而不仅仅是“完成任务”。]
- Code:
- Config:
- Script:
- Checkpoint:
- Logs:
- Metrics:
- Tables / figures:
- Report:
- Documentation:

ACCEPTANCE:

ENGINEERING:
[定义工程上什么情况下可以认为任务完成。]
- 
- 
- 

RESEARCH:
[定义什么情况下本次实验足以回答研究问题。实验结果不需要一定优于 baseline。]
- 
- 
- 

DON'T:
[只填写真正危险、不可逆或会污染实验的行为。]
- 
- 

DELEGATED:
[明确知道存在这些决策，但主动授权 AI 自行处理。只放低影响决策。]
- 
- 

OPEN_QUESTIONS:
[填写当前已知但尚未解决的问题。]
- 
- 

EXECUTION_RULE:
Before implementation, verify that all high-impact decisions required for this task are either RESOLVED in this document or explicitly DELEGATED.

Do not silently resolve high-impact ambiguity.

Do not change DECISIONS, CONSTRAINTS, MUST_PRESERVE, experimental controls, dataset splits, evaluation protocols, or baselines unless explicitly authorized.

If a high-impact unresolved issue prevents valid implementation or experimentation, stop and report it instead of making an assumption.

Otherwise, execute the task directly and preserve the experimental validity and reproducibility of the project.
