GRAMMAR_VERSION: 2
MODE: RESEARCH

TASK:
Compare LoRA ranks 8 and 16 on the frozen validation protocol.

GOAL:
Determine whether rank 16 improves validation accuracy by at least 0.01.

HYPOTHESIS:
If LoRA rank increases from 8 to 16, validation accuracy increases because the
adapter has more capacity.

CURRENT_STATE:
Rank 8 is the registered baseline. The dataset and checkpoint are immutable.

INPUTS:
Dataset `acme/classification-v3`, split `validation`, checkpoint `base-v2`.

ENTITIES:
- experiment.variable : enum
- experiment.control : enum
- training.performed : boolean
- training.epochs : integer
- evaluation.protocol : enum
- metric.primary : enum
- metric.accuracy : number
- reproducibility.seed : integer
- data.split : enum aliases ["dataset.partition"]
- data.test_leakage : boolean

SCOPES:
- experiment
- train
- eval
- result
- eval overlaps result

DECISIONS:
- [*] data.split = validation

CONSTRAINTS:
DATA:
- [*] data.test_leakage = false

EXPERIMENT:
VARIABLE:
- [experiment] experiment.variable = lora-rank-16

CONTROL:
- [experiment] experiment.control = lora-rank-8

TRAINING:
- [train] training.performed = true
- [train] training.epochs = 3

EVALUATION:
- [eval] evaluation.protocol = frozen-v3

METRICS:
- [eval] metric.primary = accuracy

SEEDS:
- [experiment] reproducibility.seed in [17, 23, 42]

OUTPUT:
Metrics JSON, per-seed report, aggregate comparison, and changed code.

ACCEPTANCE:
ENGINEERING:
NONE

RESEARCH:
- [result] metric.accuracy >= 0.90

VERIFICATION_PLAN:
- [result] metric.accuracy <- artifact:"artifacts/metrics.json"

DON'T:
NONE

DELEGATED:
NONE

OPEN_QUESTIONS:
NONE

EXECUTION_RULE:
Run the deterministic Prompt Readiness Gate before execution and preserve this
experiment contract unchanged.
