# Design Basis and Related Work

## Engineering position

There is no deterministic procedure that can prove an arbitrary natural-language
prompt is factually correct, complete for every unstated user intention, and
non-contradictory. This project therefore validates a smaller, explicit claim:

> A first-turn ML prompt conforms to a versioned controlled contract, contains
> the profile's required ML slots, has no contradiction in the represented
> constraint system, has no unresolved high-impact question, and maps every
> acceptance assertion to a declared verification method.

Free text remains available for intent and rationale, but it is not presented as
formally verified.

## Prompt languages and static analysis

- [CNL-P](https://arxiv.org/abs/2508.06942) uses a compiler-like two-stage
  pipeline: controlled prompt text is parsed into an AST-like representation and
  traversed for program checks. Prompt Grammar uses the same architectural
  boundary while choosing a compact Markdown surface.
- [IBM Prompt Declaration Language](https://github.com/IBM/prompt-declaration-language)
  demonstrates schema-first structured prompts, a typed AST, a parser, linter,
  generated JSON Schema, and examples exercised in CI. This motivated the
  separation between syntax, normalized IR, profiles, and diagnostics.
- [Microsoft POML](https://github.com/microsoft/poml) shows the value of semantic
  prompt components and dedicated tooling, while also separating content from
  presentation. Prompt Grammar deliberately handles readiness constraints rather
  than prompt rendering or orchestration.
- Research on [prompt underspecification](https://arxiv.org/abs/2505.13360)
  reports that omitted requirements are unstable and that simply lengthening a
  prompt can introduce competing instructions. This supports mode-specific slots
  and a short atomic notation instead of a maximal prose checklist.

## Requirements engineering

- EARS introduced a small set of controlled requirement patterns to reduce
  ambiguity, complexity, and vagueness: Mavin et al.,
  [DOI 10.1109/RE.2009.9](https://doi.org/10.1109/RE.2009.9). Prompt Grammar's
  named scopes play the role of explicit conditions, while each atom carries one
  effect.
- [RFC 2119](https://datatracker.ietf.org/doc/rfc2119/) established explicit
  normative keywords. In this grammar, section placement and operators encode
  normative force so that prose such as “should probably” cannot weaken a hard
  constraint.
- The [NASA Systems Engineering Handbook](https://www.nasa.gov/reference/systems-engineering-handbook/)
  requires good requirements to be clear, complete, consistent, verifiable, and
  traceable. Prompt Grammar operationalizes the subset that a local static gate
  can check and keeps factual completeness outside its claim.
- [ALICE](https://link.springer.com/article/10.1007/s10515-024-00452-x) and
  requirements [NLI research](https://arxiv.org/abs/2405.05135) show the value of
  decomposed condition/effect representations and defect-specific evaluation.
  They also reinforce that semantic difference is not automatically a logical
  contradiction.
- [Gherkin](https://cucumber.io/docs/gherkin/reference/) treats examples as
  executable specifications and requires expected outcomes to be observable.
  This motivated the split between an `ACCEPTANCE` assertion and its
  `VERIFICATION_PLAN`.

## Specification-driven workflows

[GitHub Spec Kit](https://github.github.com/spec-kit/) uses an explicit
Spec → Plan → Tasks → Implement flow and cross-artifact analysis. Prompt Grammar
is a smaller pre-plan gate: it decides whether the initial ML contract is ready
to enter such a workflow. It does not replace planning or implementation.

## Deterministic pipeline

```text
Markdown contract
  → section lexer + source locations
  → versioned ML profile checks
  → typed entity and alias table
  → atomic requirement IR
  → explicit scope co-occurrence model
  → constraint-domain intersection
  → acceptance/evidence-plan matching
  → READY or line-addressed NOT_READY
```

The finite-domain solver handles equality, inequality, ordered numeric bounds,
membership, and exclusion. It detects pairwise and multi-line empty domains. A
future Boolean/implication extension could compile to SMT and preserve source
locations through unsatisfiable cores; see the
[Z3 guide](https://microsoft.github.io/z3guide/docs/logic/basiccommands/).

## Why aliases and scopes are declarations

An LLM or embedding model can propose that `data.split` and
`dataset.partition` are similar, but similarity is not identity. Grammar v2
requires the author/profile to declare aliases. The linter then canonicalizes
them deterministically.

Likewise, different conditions may coexist or be mutually exclusive. Grammar v1
treated different named scopes as independent and could miss a conflict. Grammar
v2 requires `overlaps` or `excludes` when the same canonical subject crosses
scopes; an unknown relationship is a blocking ambiguity.

## Deliberate limits

`READY` does not prove:

- facts in `CURRENT_STATE` or `INPUTS` are true;
- prose-only instructions are mutually consistent;
- the author included every ML-specific risk or stakeholder intention;
- a command is safe, an artifact exists, or an acceptance assertion passes;
- implementation will comply with the contract.

An optional semantic model may later emit advisory suggestions, but it must not
silently rewrite the source, invent high-impact decisions, or weaken the
deterministic hard gate.
