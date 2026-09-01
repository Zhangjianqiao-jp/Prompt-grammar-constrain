# Distribution and Publishing

This document separates what the repository can guarantee from what requires an external platform review.

## Distribution layers

| Layer | Status | Discovery / installation path |
|---|---|---|
| Repository project Skill | Ready | `.agents/skills/prompt-readiness-gate` |
| Direct GitHub Skill install | Ready after merge to `main` | Give the directory URL to `$skill-installer` |
| Repo/team Codex marketplace | Ready | Add the repository root, then install `prompt-readiness-gate@prompt-grammar` |
| Tagged plugin ZIP | Automated | GitHub Releases workflow on `v*` tags |
| Universal ChatGPT/Codex plugin directory | External review required | OpenAI Platform submission portal |

The distributable plugin is intentionally skills-only. It has no MCP server, remote API, account connection, authentication secret, or runtime network dependency. Its Python linter reads local input and a local JSON profile; text in `VERIFICATION_PLAN` is data and is never executed by the gate.

## Local and team installation

```bash
git clone https://github.com/Zhangjianqiao-jp/Prompt-grammar-constrain.git
cd Prompt-grammar-constrain
python3 scripts/package_plugin.py
codex plugin marketplace add "$(pwd)"
codex plugin add prompt-readiness-gate@prompt-grammar
```

Start a new Codex task after installation. The explicit invocation is `$prompt-readiness-gate`. The Skill may also be selected implicitly for an eligible first structured ML prompt because `policy.allow_implicit_invocation` is enabled.

## Maintainer release process

1. Change the canonical Skill only under `.agents/skills/prompt-readiness-gate`.
2. Run `python3 scripts/package_plugin.py --sync`.
3. Run the full CI commands and `python3 scripts/package_plugin.py`.
4. Bump `plugins/prompt-readiness-gate/.codex-plugin/plugin.json` with strict semantic versioning.
5. Merge through a green pull request.
6. Create an annotated `vX.Y.Z` tag matching the plugin version and push it.
7. Confirm the GitHub Release contains `prompt-readiness-gate-vX.Y.Z.zip` and its SHA-256 checksum.

Never hand-edit the plugin's copied Skill. The packaging check compares every non-generated file byte-for-byte and fails on missing, stale, or changed files.

## Universal directory submission checklist

Repository work alone cannot publish a plugin to the universal directory. The publisher must complete these steps in the OpenAI Platform submission flow:

- hold an organization role with Apps Management write access;
- complete the required publisher identity verification;
- choose and approve the public developer/publisher name;
- provide a production website and support contact;
- provide reviewed privacy-policy and terms-of-service URLs;
- confirm an open-source license for repository reuse and add it to the repository and manifest;
- prepare the public listing name, short/long descriptions, category, icon/logo, and starter prompts;
- submit representative happy-path and rejection-path test prompts;
- complete platform review and address reviewer feedback.

This repository already contains draft technical listing metadata, brand assets, deterministic tests, and a no-network security description. Publisher identity, legal text/license selection, support commitments, platform credentials, and review approval are intentionally not fabricated or automated.

## Suggested listing copy

**Name:** ML Prompt Readiness Gate

**Short description:** Validate ML prompts before an agent starts work.

**Long description:** Deterministically checks the first structured machine-learning research or coding prompt for grammar completeness, typed constraints, internal contradictions, unresolved high-impact decisions, and acceptance-to-evidence mappings. Returns `READY` or line-addressed `NOT_READY` diagnostics without using an LLM as the validation oracle.

**Category:** Productivity

**Search terms:** machine learning, ML prompt, prompt validation, prompt grammar, contradiction detection, requirements engineering, static analysis, Codex skill.

## Submission test prompts

Positive cases:

- invoke the Skill on `examples/ml-research-v2.md` and expect `READY`;
- invoke it on `examples/ml-implement-v2.md` and expect `READY`;
- ask to explain the output without modifying the user's specification.

Negative cases:

- remove a required ML semantic slot and expect a line-addressed `MISSING` or `ML_SEMANTIC_SLOT` issue;
- add conflicting atomic constraints and expect `CONTRADICTION` with related lines;
- leave a `[HIGH]` question unresolved and expect `UNRESOLVED`;
- use the Skill on a non-ML task and expect it not to gate the task.

## Official references

- [Build skills](https://developers.openai.com/plugins/build/skills)
- [Package a plugin](https://developers.openai.com/plugins/build/plugins)
- [Submit plugins](https://developers.openai.com/plugins/deploy/submission)
