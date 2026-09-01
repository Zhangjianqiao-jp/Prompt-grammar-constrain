# Security Policy

## Supported versions

Security fixes are applied to the latest code on `main`. Tagged releases are immutable; a fix is shipped in a new release.

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature for this repository when available. If it is unavailable, contact the repository owner privately through the contact method on the GitHub profile. Do not open a public Issue with exploit details before a fix is available.

Include the affected revision, minimal reproducer, expected impact, and whether untrusted input or a custom profile is required. Please remove secrets and identifying prompt content.

## Trust boundaries

- The linter reads a prompt file and a local JSON profile.
- It does not execute commands or artifact locators present in a prompt.
- It does not require a network connection or credentials.
- A custom profile is trusted configuration and should be pinned and code-reviewed.
- `READY` is a conformance result, not proof that external facts, artifacts, or generated code are safe.

Prompt files may contain sensitive experiment information. Operators are responsible for filesystem permissions, retention, redaction, and any agent or model data-handling policy surrounding the linter.
