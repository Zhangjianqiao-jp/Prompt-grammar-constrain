# Prompt Grammar Constrain

A lightweight, human-first prompt specification and validation workflow for machine-learning research and coding agents.

> **Core idea:** before an execution agent starts planning, coding, editing, searching, or running experiments, the initial project prompt should be explicit enough that the agent does not need to silently make unresolved high-impact decisions.

This repository currently contains two related components:

1. **ML Research & Coding Prompt Grammar** — reusable prompt templates for machine-learning research, implementation, modification, debugging, and evaluation tasks.
2. **Prompt Readiness Gate** — a small validation Skill that checks whether a structured project prompt is ready to be handed to an execution agent.

The project is intentionally lightweight. It does not attempt to find a universally optimal prompt, nor does it try to encode an entire engineering methodology inside a large persistent Skill. Instead, it aims to establish a **minimal sufficient specification standard** that keeps important decisions under human control while using the agent primarily for execution.

---

## Motivation

Modern coding agents can often continue working even when requirements are incomplete. This is useful, but it also creates a subtle reliability problem: unlike a compiler or a traditional program, an LLM usually does not fail immediately when a requirement is missing. It produces a plausible continuation and may silently choose an architecture, model, dataset policy, evaluation protocol, file modification scope, or other consequential detail on behalf of the user.

For exploratory conversation this behavior can be convenient. For research and engineering execution, it can be dangerous.

In machine-learning work in particular, a task can appear technically successful while becoming scientifically invalid. A script may run, loss may decrease, and metrics may be produced, while an agent has unintentionally changed the dataset split, baseline, preprocessing path, evaluation protocol, hyperparameters, checkpoint handling, or another experimental condition. Such failures are often more damaging than syntax errors because they can remain unnoticed.

This repository therefore follows a simple principle:

> **High-impact decisions should be resolved by the user, explicitly delegated, or declared not applicable before execution begins.**

The objective is not maximal detail. Excessive instructions can increase token cost, introduce competing requirements, and reduce signal-to-noise ratio. The target is a compact specification containing the information that materially changes execution.

---

## Design Philosophy

### 1. Human-first decision making

The user should remain responsible for the parts of the task that define what the project means:

- what is being done;
- why it is being done;
- what must remain unchanged;
- which important design decisions have already been made;
- what constitutes valid completion.

The execution agent is then given more freedom over low-impact implementation details.

This is not an attempt to reduce agent capability. It is an attempt to place autonomy at the correct layer.

### 2. Minimal sufficient specification

A good prompt is not necessarily long or short. The relevant question is whether the information in the prompt removes important uncertainty.

This repository informally describes this property as **Decision Density**: the amount of high-impact uncertainty removed by the information placed into the prompt.

The preferred optimization order is therefore:

1. remove irrelevant information;
2. remove duplicated information;
3. remove low-impact constraints;
4. merge redundant requirements;
5. clarify important ambiguous requirements;
6. only then optimize formatting or syntax.

Semantic compression is more important than simply shortening labels or punctuation.

### 3. Validation before execution

The Prompt Readiness Gate is a **pre-execution validator**, not a prompt generator and not a planning agent.

It should not silently repair an incomplete specification. If an unresolved high-impact decision exists, it should block execution and return the issue to the user.

The intended workflow is:

```text
Explore
  ↓
Decide
  ↓
Fill Prompt Grammar
  ↓
Validate
  ↓
READY / NOT_READY
  ↓
Execute
  ↓
Evaluate
  ↓
Refine
```

### 4. Hard gate, not quality score

The validator does not assign an arbitrary score such as `87/100`.

It returns one of two states:

- `READY` — no blocking specification defect was found;
- `NOT_READY` — at least one blocking defect must be resolved before execution.

This is intentionally simpler than an opaque quality score.

---

## Repository Structure

```text
Prompt-grammar-constrain/
├── README.md
├── templates/
│   ├── ml-research-coding-prompt.md
│   └── ml-research-coding-prompt-compact.md
└── .agents/
    └── skills/
        └── prompt-readiness-gate/
            ├── SKILL.md
            └── references/
                └── design-basis.md
```

### Templates

`templates/ml-research-coding-prompt.md`

The full ML research and coding specification template. It includes fields for research hypotheses, experiment controls, change scope, reproducibility, acceptance criteria, delegated decisions, and open questions.

`templates/ml-research-coding-prompt-compact.md`

A shorter version for routine use. It preserves the core semantic fields while reducing prompt overhead.

### Validator Skill

`.agents/skills/prompt-readiness-gate/SKILL.md`

The runtime validation policy. It is intentionally compact and contains the trigger boundary, validation rules, hard-gate behavior, and output contract.

`.agents/skills/prompt-readiness-gate/references/design-basis.md`

A short provenance document listing the primary research directions that motivated the validator design. It is separated from the runtime instructions so that normal validation does not require loading the research discussion into context.

---

## Prompt Grammar

The full ML grammar currently uses the following semantic modules:

- `MODE`
- `TASK`
- `GOAL`
- `HYPOTHESIS`
- `CURRENT_STATE`
- `INPUTS`
- `DECISIONS`
- `CONSTRAINTS`
- `CHANGE_SCOPE`
- `EXPERIMENT`
- `OUTPUT`
- `ACCEPTANCE`
- `DON'T`
- `DELEGATED`
- `OPEN_QUESTIONS`

Not every module is required for every task. Unused optional sections should normally be removed instead of left empty.

The current task modes are:

- `RESEARCH`
- `IMPLEMENT`
- `MODIFY`
- `DEBUG`
- `EVALUATE`

The main distinction is that different task types require different evidence of readiness.

For example, a research task is not sufficiently specified merely because it has a `TASK` and `OUTPUT`. It should normally identify a hypothesis and an experiment sufficiently clearly to distinguish the experimental variable, controls, evaluation protocol, and metrics.

A modification task should define change scope and preservation boundaries when existing behavior, data, checkpoints, interfaces, or experiments may be affected.

A debugging task should distinguish expected behavior from observed behavior and include reproduction conditions or available evidence when those are necessary for diagnosis.

---

## Prompt Readiness Gate

The current validator performs seven conceptual checks.

### 1. Structure

Required fields must contain substantive information rather than only labels or placeholders.

Task-specific requirements are also checked. For example, `RESEARCH`, `MODIFY`, `DEBUG`, and `EVALUATE` require different supporting information.

### 2. Atomic requirement normalization

Material statements are internally interpreted in a lightweight structured form:

```text
condition/scope | subject/variable | modality | action/effect | object/value
```

The purpose is not to expose a formal language to the user. The representation is used as a reasoning aid for comparing constraints and detecting contradictions.

Typical modalities include:

- `MUST`
- `MUST_NOT`
- `DELEGATED/MAY`
- descriptive statements

### 3. Underspecification and determinacy

The validator asks whether valid execution still depends on an unresolved high-impact decision.

A decision is treated as high-impact when different choices could materially change one or more of the following:

- research validity;
- dataset or evaluation comparability;
- model or system architecture;
- public interfaces;
- irreversible project state;
- major compute or monetary cost.

Each required high-impact decision should effectively be in one of four states:

```text
RESOLVED
DELEGATED
NOT_APPLICABLE
UNRESOLVED
```

An `UNRESOLVED` high-impact decision is a blocker.

Low-impact implementation details should not be demanded simply to make the prompt appear more complete.

### 4. Ambiguity

Not every vague phrase is a blocker.

Ambiguity becomes blocking only when a clause has multiple reasonable interpretations and those interpretations could materially change execution.

This distinction is intended to reduce false positives. Stylistic vagueness is not treated the same way as ambiguity in a dataset split, evaluation target, model choice, or modification boundary.

### 5. Consistency

The validator compares requirements that govern the same subject, artifact, variable, or behavior.

The current Skill uses an NLI-inspired distinction:

```text
ENTAILMENT
NEUTRAL
CONTRADICTION
```

`NEUTRAL` is not considered a contradiction.

Two statements should be treated as contradictory only when their conditions can co-occur and their required effects are mutually incompatible.

### 6. Verifiability

`ACCEPTANCE` must provide observable evidence or a decidable completion condition.

For research tasks, an important distinction is enforced:

> A successful experiment does not require the hypothesis to be supported.

A research task may be successfully completed when the experiment validly tests the hypothesis, preserves the intended controls, and produces interpretable evidence, even if the result is negative.

### 7. Minimality

Redundant, duplicated, or low-relevance context is treated as a warning rather than an automatic blocker unless it creates ambiguity or conflict.

This follows the project's broader principle that both underspecification and uncontrolled specification growth can be harmful.

---

## Failure Contract

When a blocker exists, the Skill returns:

```text
NOT_READY
```

followed by blocking issues in the form:

```text
[TYPE] location — problem — what the user must clarify, resolve, or explicitly delegate
```

Current blocker types are:

- `MISSING`
- `AMBIGUOUS`
- `UNRESOLVED`
- `CONTRADICTION`
- `UNVERIFIABLE`

The validator may additionally return warnings for non-blocking redundancy.

A critical behavioral rule is that the validator must **not select the substantive answer to a blocker on the user's behalf**.

If a model choice, experimental design decision, architecture decision, or other high-impact issue is unresolved, the validator may identify the missing decision but should not silently fill it.

---

## Recommended Usage

### Full specification

Use the full template for:

- new ML research projects;
- experimental pipelines;
- important changes to training or evaluation logic;
- modifications that can affect scientific comparability;
- long-running or expensive experiments;
- unfamiliar repositories.

Start from:

```text
templates/ml-research-coding-prompt.md
```

Delete irrelevant optional sections, fill the remaining fields, and submit the resulting specification as the first execution prompt.

### Compact specification

Use the compact template for:

- routine implementation;
- small code modifications;
- familiar repositories;
- low-risk experiments where most high-impact decisions are already known.

Start from:

```text
templates/ml-research-coding-prompt-compact.md
```

### Validation

At project initialization:

1. write the structured prompt;
2. run the Prompt Readiness Gate;
3. if it returns `NOT_READY`, resolve or explicitly delegate the blocking decisions;
4. validate again;
5. once ready, use the original validated specification as the authoritative task prompt.

The validator is intentionally designed to run at project initialization rather than every turn. Revalidation is appropriate when the user explicitly requests it or when the specification materially changes.

---

## Advantages

### 1. Preserves human control over high-impact decisions

The central advantage is epistemic control. The user can see which architectural, experimental, or scope decisions have actually been made rather than discovering them only after the agent has already implemented a solution.

### 2. Reduces silent assumption risk

LLMs are capable of producing plausible outputs even when requirements are missing. The hard gate is designed specifically to surface consequential missing decisions before execution.

### 3. Better suited to ML research than generic coding prompts

The grammar explicitly represents concepts that are particularly important in machine learning:

- hypothesis;
- experimental variable;
- controls;
- baseline;
- evaluation protocol;
- metrics;
- reproducibility;
- modification boundaries.

This helps protect experimental validity, not only software correctness.

### 4. Lightweight runtime design

The Skill is deliberately small. Research rationale is kept in a separate reference document instead of being embedded in runtime instructions.

This reduces recurring context overhead and follows the idea of progressive disclosure: load only what is necessary for the current task.

### 5. Avoids the "specify everything" trap

The project does not assume that longer prompts are always better.

Low-impact implementation details may be explicitly delegated, and redundant context produces warnings rather than automatically blocking execution.

### 6. Clear failure semantics

`READY` / `NOT_READY` is easier to reason about than an arbitrary numeric quality score.

Blocking defect types are explicit and intended to be actionable.

### 7. Compatible with future deterministic validation

The current atomic requirement model can later support more deterministic components such as:

- schema validation;
- rule-based checks;
- NLI-based conflict detection;
- formal constraint representation;
- SAT/SMT consistency checking.

The V1 Skill therefore provides a migration path from prompt-based validation toward more conventional software tooling.

### 8. Encourages better research practice

Writing the prompt grammar itself forces the researcher to articulate the relationship between hypothesis, experiment, controls, outputs, and evidence.

The benefit is therefore not limited to improving agent behavior. The specification process can also expose weaknesses in the human's own experimental design.

---

## Limitations and Disadvantages

### 1. V1 semantic validation is still LLM-based

The current Skill uses structured instructions to reason about ambiguity, determinacy, and contradiction, but it does **not** yet run an independent NLI model, theorem prover, SAT solver, or SMT solver.

Therefore, this repository should not currently be described as formal verification.

The validator itself remains probabilistic and can produce false positives or false negatives.

### 2. No benchmark has been completed yet

The current design is research-informed but not yet empirically validated on a dedicated benchmark.

Claims such as reduced failure rate, lower retry cost, or higher constraint adherence still need to be tested against real agent sessions and controlled baselines.

A future evaluation should measure at least:

- blocker precision and recall;
- false-positive rate;
- false-negative rate;
- task success rate;
- constraint adherence;
- retry rate;
- token overhead;
- cross-model stability.

### 3. High-impact classification is partly subjective

Whether a decision is "high impact" depends on the task and project context.

The current definition provides a principled boundary, but different users or models may classify borderline cases differently.

A future domain profile or decision ontology may reduce this variance.

### 4. Risk of overblocking

A strict validator can become counterproductive if it treats every unspecified implementation detail as a blocker.

The Skill attempts to prevent this through the `DELEGATED` concept and by requiring ambiguity to be high-impact before blocking, but overblocking remains a practical risk.

### 5. Additional initialization cost

Validation consumes tokens and adds one step before execution.

For trivial tasks, the cost may outweigh the benefit. The workflow is most useful when errors are expensive, experiments are long-running, or the agent has broad modification authority.

### 6. Structured templates impose user effort

The method deliberately shifts some planning responsibility back to the human.

Users who want maximum autonomy from the agent may find the workflow slower than ordinary conversational prompting.

That trade-off is intentional: this project prioritizes explicit specification over convenience for high-impact work.

### 7. ML-oriented profiles are not universally complete

The current grammar is optimized for machine-learning research and coding tasks. It is not yet a universal ontology for software engineering, scientific research, image generation, writing, or other agent workloads.

Additional domain-specific profiles should be created rather than continuously expanding one global template.

### 8. Prompt validation cannot guarantee implementation correctness

`READY` means that the specification has passed the current readiness checks. It does **not** mean that the agent will implement the project correctly.

Implementation still requires testing, review, experiment tracking, and ordinary engineering safeguards.

### 9. Prompt validation is not a security boundary

The Skill is an instruction-level gate. It is not a sandbox, permission system, access-control layer, or substitute for repository protections and infrastructure-level safety controls.

### 10. Trigger behavior depends on the host agent environment

Skill discovery and invocation behavior can differ between products and agent runtimes. Users should follow the skill installation conventions of the environment in which they run the validator.

---

## Current Status

**Status: experimental V1**

The current project intentionally favors a small, auditable design over a large feature set.

V1 includes:

- full ML prompt grammar;
- compact ML prompt grammar;
- project-initialization readiness gate;
- structural/task-profile checks;
- high-impact decision coverage;
- ambiguity checks;
- NLI-inspired contradiction reasoning;
- acceptance verifiability;
- redundancy warnings;
- explicit `READY` / `NOT_READY` behavior.

V1 does **not** yet include:

- standalone parser;
- deterministic schema validator;
- trained NLI conflict model;
- requirement AST/IR implementation;
- SAT/SMT solver;
- benchmark suite;
- automatic prompt rewriting;
- automatic high-impact decision selection.

The absence of automatic rewriting is intentional. The system is designed to reveal unresolved decisions rather than hide them behind plausible generated defaults.

---

## Roadmap

### V1 — Prompt-level gate

Current stage.

Goal: determine whether the conceptual gate improves real ML research and coding workflows before increasing implementation complexity.

Planned testing:

- collect real project-start prompts;
- introduce controlled missing requirements;
- introduce conditional contradictions;
- introduce high-impact ambiguity;
- introduce harmless vagueness;
- introduce redundant context;
- measure false positives and false negatives.

### V2 — Deterministic structural validator

Move low-level checks out of LLM reasoning and into code.

Possible components:

```text
parser
schema rules
MODE-specific required fields
placeholder detection
duplicate-section detection
basic acceptance checks
```

The Skill would then become a thin orchestration policy that calls the deterministic validator.

### V3 — Requirement intermediate representation

Represent material requirements as explicit structured objects, for example:

```text
Requirement {
  condition
  scope
  subject
  modality
  action
  object
  value
}
```

This would make contradiction analysis and traceability more systematic.

### V4 — NLI and symbolic consistency checking

Use semantic retrieval to identify requirement pairs governing the same subject, then apply NLI or another semantic classifier.

Where requirements can be translated reliably into formal constraints, test SAT/SMT-based consistency checking and unsatisfiable-core reporting.

### V5 — Evaluation and task-specific profiles

Develop a benchmark covering multiple task modes and multiple models.

Potential future profiles include:

- general software engineering;
- data engineering;
- scientific computing;
- agent design;
- image-generation workflows;
- technical writing.

The objective is not to create a single giant universal Skill. Each profile should remain narrow enough to preserve high decision density and low context overhead.

---

## Research Basis

The design is primarily informed by four research directions.

### Structured prompt languages and linting

CNL-P treats natural-language prompts more like software interfaces by defining grammar and semantic norms, and introduces linting based on static-analysis ideas. This supports the general direction of `Prompt → structured representation → lint`.

### Prompt underspecification

Work on prompt underspecification shows that LLMs can sometimes infer missing requirements, but that this behavior is fragile across prompt or model changes. The same work also shows that naively adding all possible requirements is not a guaranteed solution because models have finite instruction-following capacity and requirements can compete or conflict.

### Natural Language Inference for Requirements Engineering

Requirements Engineering research has investigated NLI for requirement classification, defect identification, and stakeholder requirement conflict detection. This motivates separating entailment, neutrality, and contradiction rather than treating semantic difference as conflict.

### Hybrid logical contradiction detection

ALICE demonstrates a stricter requirements-analysis direction in which natural-language requirements are decomposed into structured condition/effect and variable/action information before contradiction reasoning is applied. This motivates the validator's rule that contradictory wording alone is insufficient: the relevant conditions must be compatible and the required effects must actually be mutually exclusive.

---

## References

1. Zhenchang Xing, Yang Liu, Zhuo Cheng, Qing Huang, Dehai Zhao, Daniel Sun, and Chenhua Liu. **When Prompt Engineering Meets Software Engineering: CNL-P as Natural and Robust "APIs" for Human-AI Interaction.** arXiv:2508.06942.  
   https://arxiv.org/abs/2508.06942

2. Chenyang Yang, Yike Shi, Qianou Ma, Michael Xieyang Liu, Christian Kästner, and Tongshuang Wu. **What Prompts Don't Say: Understanding and Managing Underspecification in LLM Prompts.** Findings of ACL 2026.  
   https://aclanthology.org/2026.findings-acl.441/  
   https://arxiv.org/abs/2505.13360

3. Mohamad Fazelnia, Viktoria Koscinski, Spencer Herzog, and Mehdi Mirakhorli. **Lessons from the Use of Natural Language Inference (NLI) in Requirements Engineering Tasks.** arXiv:2405.05135.  
   https://arxiv.org/abs/2405.05135

4. Alexander Elenga Gärtner and Dietmar Göhlich. **Automated requirement contradiction detection through formal logic and LLMs.** Automated Software Engineering, 31, Article 49 (2024).  
   https://link.springer.com/article/10.1007/s10515-024-00452-x

5. Zhenpeng Chen, Chong Wang, Weisong Sun, Xuanzhe Liu, Jie M. Zhang, and Yang Liu. **Promptware Engineering: Software Engineering for Prompt-Enabled Systems.** arXiv:2503.02400.  
   https://arxiv.org/abs/2503.02400

6. OpenAI. **Using skills.** OpenAI Academy.  
   https://openai.com/academy/skills/

7. GitHub. **Spec Kit.**  
   https://github.github.com/spec-kit/

8. GitHub. **Spec Kit Quick Start.**  
   https://github.github.com/spec-kit/quickstart.html

9. Martin Fowler / Birgitta Böckeler. **Understanding Spec-Driven-Development: Kiro, spec-kit, and Tessl.**  
   https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html

10. OpenAI. **Using PLANS.md for multi-hour problem solving.**  
    https://developers.openai.com/cookbook/articles/codex_exec_plans

11. **Kiro Specs.**  
    https://kiro.dev/docs/specs/

12. Microsoft. **Prompt Orchestration Markup Language (POML).**  
    https://arxiv.org/abs/2508.13948  
    https://github.com/microsoft/POML

13. **Structured Prompt Language: Declarative Context Management for LLMs.**  
    https://arxiv.org/abs/2602.21257

14. Jules White et al. **A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT.**  
    https://arxiv.org/abs/2302.11382

15. **Does Prompt Formatting Have Any Impact on LLM Performance?**  
    https://arxiv.org/abs/2411.10541

16. **Guidelines to Prompt Large Language Models for Code Generation: An Empirical Characterization.**  
    https://arxiv.org/abs/2601.13118

17. **From Prompts to Templates: A Systematic Prompt Template Analysis for Real-world LLMapps.**  
    https://arxiv.org/abs/2504.02052

18. Huiqiang Jiang et al. **LLMLingua: Compressing Prompts for Accelerated Inference of Large Language Models.**  
    https://arxiv.org/abs/2310.05736

19. **Prompt Compression for Large Language Models: A Survey.**  
    https://arxiv.org/abs/2410.12388

20. **TOON — Token-Oriented Object Notation.**  
    https://github.com/toon-format  
    https://github.com/toon-format/spec

21. **Notation Matters: A Benchmark Study of Token-Optimized Formats in Agentic AI Systems.**  
    https://arxiv.org/abs/2605.29676

22. **Token-Oriented Object Notation vs JSON: A Benchmark of Plain and Constrained Decoding Generation.**  
    https://arxiv.org/abs/2603.03306

23. **Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs (MIPRO).**  
    https://arxiv.org/abs/2406.11695

24. **DSPy.**  
    https://dspy.ai/

25. Microsoft. **PromptWizard: Task-Aware Prompt Optimization Framework.**  
    https://arxiv.org/abs/2405.18369  
    https://microsoft.github.io/PromptWizard/

26. **AutoPDL: Automatic Prompt Optimization for LLM Agents.**  
    https://arxiv.org/abs/2504.04365

27. Anthropic. **Effective context engineering for AI agents.**  
    https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

28. Anthropic. **Building Effective AI Agents.**  
    https://www.anthropic.com/engineering/building-effective-agents

29. Anthropic. **Code execution with MCP: building more efficient AI agents.**  
    https://www.anthropic.com/engineering/code-execution-with-mcp

---

## Contributing

This project is still experimental. Useful contributions include:

- real examples of prompts that should be `READY` or `NOT_READY`;
- adversarial contradiction cases;
- ambiguity cases where the validator overblocks;
- missing high-impact decision categories for ML research;
- proposals for deterministic structural validation;
- evaluation methodology;
- task-specific prompt profiles.

When proposing new validation rules, prefer rules that are:

- domain-relevant;
- testable;
- concise;
- difficult to satisfy accidentally;
- important enough to justify their context cost.

Avoid expanding the universal Skill with narrow framework-specific advice. Domain knowledge should preferably live in a separate profile or reference module.

---

## Disclaimer

This project is an experimental prompt-engineering and requirements-validation workflow. It does not provide formal correctness guarantees and should not replace software testing, experiment tracking, code review, access controls, sandboxing, or other engineering safeguards.
