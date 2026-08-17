# Prompt Grammar Constrain

[中文](#中文说明) | [English](#english-readme)

---

# 中文说明

一个面向机器学习研究与 Coding Agent 的轻量级、Human-first Prompt 规范与验证工作流。

> **核心思想：** 在执行 Agent 开始规划、写代码、修改文件、搜索方案或运行实验之前，项目的初始 Prompt 应当足够明确，使 Agent 不需要在用户不知情的情况下，擅自替用户完成尚未解决的高影响决策。

当前仓库包含两个核心部分：

1. **ML Research & Coding Prompt Grammar**：用于机器学习研究、实现、修改、调试和评估任务的结构化 Prompt 模板。
2. **Prompt Readiness Gate**：一个轻量级验证 Skill，用来判断结构化 Prompt 是否已经达到可以交给执行 Agent 的最低充分标准。

本项目并不试图寻找一个适用于所有模型和任务的“最优 Prompt”，也不希望把所有工程规范都写进一个动辄几千甚至上万 token 的大型 Skill。我们的目标是建立一套 **Minimal Sufficient Specification（最小充分规格）**：尽可能用较少的信息明确真正影响执行结果的决策，把高影响决策留在人类手中，把低影响实现细节交给 Agent。

---

## 项目动机

现代 Coding Agent 即使面对不完整的需求，也往往可以继续工作。它们通常不会像编译器一样，因为缺少一个 requirement 就直接失败，而是会基于训练分布和上下文生成一个“看起来合理”的默认选择。

这在探索阶段很方便，但在正式研究和工程执行中存在明显风险。

如果 Prompt 没有明确模型选择、数据处理、实验基线、评价协议、修改范围或其他高影响条件，Agent 很可能会替用户做决定，而且这些决定可能直到项目后期才被发现。

对于机器学习研究，这种问题尤其危险：代码可能完全能够运行，loss 可能正常下降，也可能得到看起来合理的指标，但 Agent 可能已经无意中改变了 dataset split、baseline、preprocessing、evaluation protocol、hyperparameter、checkpoint handling 或实验控制变量。此时工程上“成功运行”的代码，科学上可能已经失去可比性和有效性。

因此，本项目遵循一条核心原则：

> **所有执行所必需的高影响决策，在执行开始前都应该已经被用户明确解决、显式委托给 Agent，或明确声明为不适用。**

我们并不追求“写得越多越好”。过多 requirement 可能增加 token 成本、产生 instruction competition、引入新的冲突并降低 signal-to-noise ratio。目标是保留真正会改变执行路径的信息。

---

## 设计哲学

### 1. Human-first 决策

用户应主要负责定义：

- 要做什么；
- 为什么做；
- 哪些东西不能改变；
- 哪些重要技术或实验决策已经确定；
- 什么条件下任务才算完成。

Agent 则主要负责具体实现方式和低影响工程细节。

这不是限制 Agent 能力，而是把 Agent 的自主性放在更合适的层级。

### 2. 最小充分规格

一个 Prompt 是否优秀，不取决于它有多长，而取决于其中的信息是否有效减少了高影响不确定性。

本项目暂时使用 **Decision Density** 这个概念描述这种性质：Prompt 中每一段信息能够消除多少真正影响执行结果的重要决策不确定性。

因此，Prompt 优化顺序应优先是：

1. 删除无关信息；
2. 删除重复信息；
3. 删除低影响约束；
4. 合并重复 requirement；
5. 明确真正重要的歧义；
6. 最后才考虑格式压缩和 token 级优化。

也就是说，**Semantic Compression 优先于 Syntax Compression**。

### 3. 执行前验证

Prompt Readiness Gate 是一个 **pre-execution validator**，不是 Prompt Generator，也不是 Planning Agent。

它不应该替用户补全缺失的高影响决策。如果 Prompt 中存在阻碍安全执行的未决问题，Validator 应停止执行，把问题暴露给用户，由用户修改后再次验证。

推荐流程：

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

### 4. Hard Gate，而不是主观评分

Validator 不输出类似 `87/100` 的 Prompt 质量分数。

它只返回两个核心状态：

- `READY`：没有发现会阻碍执行的规格缺陷；
- `NOT_READY`：至少存在一个必须在执行前解决的问题。

相比一个难以解释的数值分数，Boolean Gate 更适合工程执行。

---

## 仓库结构

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

### Prompt 模板

`templates/ml-research-coding-prompt.md`

完整的 ML Research & Coding Prompt Grammar，适合正式研究、新实验、重要代码修改或高成本任务。

`templates/ml-research-coding-prompt-compact.md`

精简版本，适合熟悉项目中的日常实现、较小修改和低风险实验。

### Validator Skill

`.agents/skills/prompt-readiness-gate/SKILL.md`

运行时验证规则。它只保留触发条件、验证逻辑、Hard Gate 行为和输出协议，尽量减少正常使用时的 token 开销。

`.agents/skills/prompt-readiness-gate/references/design-basis.md`

保存主要研究依据和设计来源。它与运行时 Skill 分离，避免每次验证都把研究背景加载进 context。

---

## ML Prompt Grammar

当前完整版 Grammar 包含以下语义模块：

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

并不是每个任务都需要填写所有字段。不适用的可选模块应该删除，而不是为了形式完整机械保留。

当前 MODE：

- `RESEARCH`
- `IMPLEMENT`
- `MODIFY`
- `DEBUG`
- `EVALUATE`

不同 MODE 对“READY”的要求不同。

例如，`RESEARCH` 不应该仅仅有 TASK 和 OUTPUT，还应明确 HYPOTHESIS，并且 EXPERIMENT 至少能够识别实验变量、控制变量、评价协议和指标。

`MODIFY` 在可能影响已有代码行为、数据、checkpoint、接口或实验时，应明确 CHANGE_SCOPE 和必须保持不变的边界。

`DEBUG` 应区分 expected behavior 与 observed behavior，并在诊断需要时提供 reproduction condition 或已有 evidence。

---

## Prompt Readiness Gate

当前 Validator 进行七类概念检查。

### 1. Structure

检查必要字段是否存在真正有效的内容，而不是只有标题、placeholder 或空值。同时根据 MODE 检查任务特定的必要信息。

### 2. Atomic Requirement Normalization

对重要的 decision、constraint、prohibition、experimental control 和 acceptance clause，内部按照轻量结构理解：

```text
condition/scope | subject/variable | modality | action/effect | object/value
```

这不是要求用户学习新的形式语言，而是帮助 Validator 把自然语言 requirement 拆成更容易比较的原子语义单元。

典型 modality 包括：

- `MUST`
- `MUST_NOT`
- `DELEGATED/MAY`
- descriptive statement

### 3. Underspecification 与 Determinacy

Validator 的核心问题不是“字段是不是都填了”，而是：

> 当前任务如果继续执行，Agent 是否仍然必须偷偷替用户完成某个高影响决策？

当不同选择可能实质改变以下任意内容时，该决策通常视为高影响：

- 研究有效性；
- 数据或评价可比性；
- 模型或系统架构；
- 公共接口；
- 不可逆项目状态；
- 大量算力或金钱成本。

每个必须解决的高影响决策应处于以下状态之一：

```text
RESOLVED
DELEGATED
NOT_APPLICABLE
UNRESOLVED
```

只要存在 `UNRESOLVED` 的高影响决策，就应判定为 blocker。

Validator 不应为了追求“完整”而强迫用户定义变量命名、helper function 组织等低影响实现细节。

### 4. Ambiguity

并不是所有模糊表达都应该阻塞。

只有当一个 clause 存在多个合理解释，并且这些不同解释会实质改变执行路径时，才应该被视为 blocking ambiguity。

这样可以避免 Validator 因为普通语言风格差异而过度拦截。

### 5. Consistency

Validator 重点比较约束同一 subject、artifact、variable 或 behavior 的 requirement。

当前 Skill 使用 NLI 风格的三分类思路：

```text
ENTAILMENT
NEUTRAL
CONTRADICTION
```

`NEUTRAL` 不等于冲突。

只有当两个 requirement 的条件可以同时成立，并且要求的 action/effect 互相不可兼容时，才应判定为真正的 contradiction。

### 6. Verifiability

`ACCEPTANCE` 必须提供可观察证据，或至少能够形成明确的完成判断条件。

对于研究任务尤其需要区分：

> 实验成功完成，并不等于 hypothesis 必须成立。

只要实验能够有效检验 hypothesis、保持控制条件并产生可解释 evidence，即使实验结果是否定的，也可以认为研究任务成功完成。

### 7. Minimality

冗余、重复或低相关 context 默认只产生 warning，而不是 blocker，除非它们进一步造成歧义或冲突。

这样可以同时避免 underspecification 和 uncontrolled specification growth。

---

## 冲突规避原则

为了让 Prompt 更容易被静态分析，推荐在 Grammar 层尽量遵循以下规则：

1. 一条规则只表达一个 atomic requirement；
2. Hard rule 尽量使用明确 modality，例如 `MUST` / `MUST_NOT`；
3. 条件性规则应显式写出 condition；
4. 同一个项目实体尽量使用统一 canonical identifier；
5. 复杂逻辑关系显式使用 `AND` / `OR` / `NOT`；
6. 可量化约束尽量使用明确数值、范围或枚举值；
7. 真实冲突不通过隐式优先级自动解决，必须由用户明确修改或显式 override。

我们的目标不是在 Prompt 写完之后单纯“让 LLM 看看有没有矛盾”，而是让 Prompt 本身更接近一种可以分析的 requirement specification。

---

## Failure Contract

如果存在 blocker，Skill 返回：

```text
NOT_READY
```

随后按照以下格式列出问题：

```text
[TYPE] location — problem — what the user must clarify, resolve, or explicitly delegate
```

当前 blocker 类型：

- `MISSING`
- `AMBIGUOUS`
- `UNRESOLVED`
- `CONTRADICTION`
- `UNVERIFIABLE`

对于非阻塞的冗余信息可以额外给出 warning。

一个非常重要的行为约束是：**Validator 不允许替用户选择 blocker 的实质答案。**

如果模型、实验路线、架构或其他高影响决策没有解决，Validator 可以指出问题，但不能静默填入一个看似合理的默认答案。

---

## 推荐使用方式

### 完整模板

适合：

- 新 ML 研究项目；
- 正式实验 pipeline；
- 训练或评价逻辑的重要修改；
- 会影响实验可比性的代码变化；
- 高成本、长时间运行实验；
- 不熟悉的代码仓库。

使用：

```text
templates/ml-research-coding-prompt.md
```

删除无关字段，填写剩余内容，将其作为项目初始化 Prompt。

### 精简模板

适合：

- 日常实现；
- 小规模代码修改；
- 熟悉的仓库；
- 大部分高影响决策已经确定的低风险实验。

使用：

```text
templates/ml-research-coding-prompt-compact.md
```

### Validation

项目启动时：

1. 编写结构化 Prompt；
2. 调用 Prompt Readiness Gate；
3. 如果返回 `NOT_READY`，解决或显式委托 blocker；
4. 再次验证；
5. 通过之后，把原始已验证 specification 作为 authoritative task prompt 交给执行 Agent。

Validator 默认只在项目初始化时使用，而不是每一轮对话都重复执行。只有 specification 发生重要变化或用户明确要求 revalidate 时才重新调用。

---

## 优点

### 1. 保留人类对高影响决策的控制权

用户能够明确知道哪些架构、实验和范围决策已经完成，而不是在 Agent 实现结束之后才发现它替自己选择了某条路线。

### 2. 降低 Silent Assumption 风险

LLM 很擅长在要求不完整时生成“看起来合理”的内容。Hard Gate 专门用于在执行前暴露那些会影响项目方向的缺失条件。

### 3. 比通用 Coding Prompt 更适合机器学习研究

Grammar 显式包含 hypothesis、experimental variable、control、baseline、evaluation protocol、metric、reproducibility 和 modification boundary 等研究关键概念。因此保护的不只是代码正确性，还有 experimental validity。

### 4. Runtime Skill 很轻

Skill 本体只保存必要的验证规则，研究背景独立存储。可以减少反复调用时不必要的 context 成本。

### 5. 避免“所有东西都写进去”的陷阱

项目不认为 Prompt 越长越好。低影响决策可以使用 `DELEGATED` 明确交给 Agent；冗余信息只产生 warning，而不是自动阻塞。

### 6. Failure Semantics 清晰

`READY` / `NOT_READY` 比主观质量评分更容易工程化使用，同时 blocker 类型可直接指导修改。

### 7. 为未来确定性验证保留接口

当前 atomic requirement 表示可以逐步演化为：

- schema validation；
- rule-based checking；
- NLI conflict detection；
- formal constraint representation；
- SAT/SMT consistency checking。

也就是说，项目可以逐步从 Prompt-based Validator 迁移到更传统的软件工具链。

### 8. 同时改善研究者自己的实验设计

填写 Grammar 的过程迫使研究者主动明确 hypothesis、experiment、control、output 和 evidence。即使不考虑 Agent，它也可能帮助发现人自身实验设计里的漏洞。

---

## 缺点与当前局限

### 1. V1 的语义验证仍然依赖 LLM

当前 Skill 虽然使用结构化规则判断 ambiguity、determinacy 和 contradiction，但尚未运行独立的 NLI 模型、theorem prover、SAT solver 或 SMT solver。

因此目前不能称为 formal verification，Validator 仍然可能出现 false positive 和 false negative。

### 2. 目前还没有完成专门 Benchmark

设计有研究依据，但尚未在专门测试集上系统验证。未来需要测量 blocker precision/recall、false positive/negative、task success、constraint adherence、retry rate、token overhead 和 cross-model stability。

### 3. “高影响”存在一定主观性

高影响决策取决于具体任务和项目 context。虽然已有原则可以提供边界，但 borderline case 仍可能被不同用户或模型不同判断。

### 4. 存在 Overblocking 风险

如果 Validator 把所有未定义实现细节都视为 blocker，就会失去实际价值。目前通过 `DELEGATED` 和“只有高影响 ambiguity 才阻塞”来降低这一风险，但仍需要真实测试验证。

### 5. 增加项目启动成本

Validation 本身会额外消耗少量 token，并增加一个前置步骤。对于极小任务可能得不偿失，因此更适合错误成本较高、实验昂贵或 Agent 权限较大的场景。

### 6. 结构化模板增加用户负担

该方法主动把部分规划责任重新交给人类。希望 Agent 完全自主完成所有事情的用户可能会觉得它比普通对话式 prompting 更慢。

### 7. 当前 Profile 主要面向 ML

目前 Grammar 优先服务机器学习研究与相关代码任务，而不是一个覆盖所有领域的统一 ontology。未来应该新增不同领域 Profile，而不是无限扩大一个 universal template。

### 8. READY 不代表实现一定正确

`READY` 只代表 Prompt 通过当前 readiness checks，并不保证 Agent 的代码、实验或结论一定正确。仍然需要测试、代码审查、实验追踪等工程手段。

### 9. Validator 不是安全边界

Skill 本质上仍是 instruction-level gate，不能替代 sandbox、权限系统、branch protection、访问控制等真正的安全机制。

### 10. Skill 触发依赖宿主环境

不同 Agent runtime 对 Skill 的发现、加载和调用机制可能不同，需要按照实际运行环境安装和使用。

---

## 当前状态

**Status: experimental V1**

V1 当前包含：

- 完整 ML Prompt Grammar；
- 精简 ML Prompt Grammar；
- 项目初始化 Readiness Gate；
- task-profile 结构检查；
- high-impact decision coverage；
- ambiguity check；
- NLI-inspired contradiction reasoning；
- acceptance verifiability；
- redundancy warning；
- 明确 `READY` / `NOT_READY` 行为。

V1 尚未包含：

- 独立 parser；
- deterministic schema validator；
- 独立训练的 NLI conflict model；
- Requirement AST/IR 实现；
- SAT/SMT solver；
- benchmark suite；
- automatic prompt rewriting；
- automatic high-impact decision selection。

不做自动 Prompt 重写是当前有意的设计：我们的目标是暴露未决决策，而不是用模型生成的默认答案把问题隐藏起来。

---

## Roadmap

### V1 — Prompt-level Gate

当前阶段。目标是先验证这套概念是否真的能改善真实 ML Research/Coding Agent 的项目启动质量。

计划构造和收集：

- 真实项目启动 Prompt；
- 人工制造的 missing requirement；
- conditional contradiction；
- high-impact ambiguity；
- harmless vagueness；
- redundant context；
- READY / NOT_READY 对照样本。

### V2 — Deterministic Structural Validator

把低层结构检查从 LLM 中移出，转成代码，例如：

```text
parser
schema rules
MODE-specific required fields
placeholder detection
duplicate-section detection
basic acceptance checks
```

此时 Skill 本体进一步变薄，只负责 orchestrate validator 和 Gate policy。

### V3 — Requirement Intermediate Representation

把 material requirements 显式表示为结构化对象，例如：

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

用于更系统地进行 contradiction analysis 和 traceability。

### V4 — NLI + Symbolic Consistency Checking

通过 semantic retrieval 找到约束同一对象的 requirement pair，再使用 NLI 或 semantic classifier 判断 entailment / neutral / contradiction。

能够可靠形式化的 constraint 则进一步尝试 SAT/SMT consistency checking 和 unsat-core reporting。

### V5 — Benchmark 与 Task-specific Profiles

构建覆盖多 MODE、多模型的 benchmark，并逐步扩展：

- general software engineering；
- data engineering；
- scientific computing；
- agent design；
- image-generation workflow；
- technical writing。

目标不是建立一个越来越大的 universal Skill，而是为不同任务维护相对独立、低 token、高 decision density 的 Profile。

---

## 参与贡献

当前项目仍处于实验阶段，特别欢迎以下贡献：

- 应该判定为 `READY` / `NOT_READY` 的真实 Prompt；
- adversarial contradiction case；
- Validator 过度拦截的 ambiguity case；
- ML 研究中遗漏的高影响决策类型；
- deterministic structural validator 设计；
- benchmark 与评价方法；
- 不同任务的 Prompt Profile。

新增验证规则时，优先选择：

- 与领域真实风险相关；
- 可以测试；
- 简洁；
- 不容易被形式化填写“骗过”；
- 重要程度足以值得消耗 context。

不要把具体框架知识无限加入 universal Skill。领域知识更适合存放在独立 profile 或 reference 中。

---

## 声明

这是一个实验性的 Prompt Engineering / Requirements Validation 工作流，目前不提供形式正确性保证，也不能替代软件测试、实验追踪、代码审查、权限控制、sandbox 等正常工程保障。

> 完整研究依据与参考文献请查看下方英文版本的 `References`。

---

# English README

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