# Design Basis

This validator is intentionally designed as a thin pre-execution gate. Its rules draw on four related research directions:

1. CNL-P: structured prompt grammar plus syntactic and semantic linting using software-engineering static-analysis ideas.
   - https://arxiv.org/abs/2508.06942

2. Prompt underspecification: unspecified requirements may be guessed correctly by LLMs but are less robust, while naively adding every possible requirement can create competing instructions.
   - https://arxiv.org/abs/2505.13360

3. Natural Language Inference for Requirements Engineering: NLI has been studied for requirement defects and stakeholder requirement conflicts.
   - https://arxiv.org/abs/2405.05135

4. ALICE: contradiction detection based on decomposition of requirements into conditions/effects and variables/actions, combining formal reasoning with LLM-based semantic judgments.
   - https://link.springer.com/article/10.1007/s10515-024-00452-x

The runtime `SKILL.md` does not require this reference file to be loaded. It is retained for provenance and future validator development without increasing normal validation context.
