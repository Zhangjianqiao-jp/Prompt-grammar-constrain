#!/usr/bin/env python3
"""Deterministic linter for the ML Research & Coding Prompt Grammar."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


HEADER_RE = re.compile(r"^([A-Z][A-Z0-9 _/'-]*):\s*(.*)$")
ATOM_RE = re.compile(
    r"^\s*-\s*\[([A-Za-z0-9_*.-]+)\]\s+"
    r"([A-Za-z][A-Za-z0-9_.-]*)\s+"
    r"(not-in|in|!=|<=|>=|=|<|>)\s+(.+?)\s*$"
)
DELEGATED_RE = re.compile(
    r"^\s*-\s*\[([A-Za-z0-9_*.-]+)\]\s+"
    r"([A-Za-z][A-Za-z0-9_.-]*)\s+delegated\s*$",
    re.IGNORECASE,
)
QUESTION_RE = re.compile(
    r"^\s*-\s*\[(HIGH|LOW)\]\s+([A-Za-z][A-Za-z0-9_.-]*)\s*(?:—|:)\s*(.+?)\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourceLine:
    number: int
    text: str


@dataclass
class Section:
    name: str
    parent: str | None
    header_line: int
    lines: list[SourceLine] = field(default_factory=list)


@dataclass(frozen=True)
class Atom:
    scope: str
    subject: str
    op: str
    value: Any
    section: str
    line: int


@dataclass
class Issue:
    kind: str
    line: int
    message: str
    section: str | None = None
    related_lines: list[int] = field(default_factory=list)
    severity: str = "error"


def load_profile(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_document(text: str, profile: dict[str, Any]) -> tuple[dict[str, Section], list[Issue]]:
    top_names = set(profile["top_sections"])
    children = {key: set(value) for key, value in profile["children"].items()}
    all_child_names = {name for values in children.values() for name in values}
    sections: dict[str, Section] = {}
    issues: list[Issue] = []
    current_top: str | None = None
    current: Section | None = None

    for line_number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        match = HEADER_RE.match(stripped)
        if match:
            label, inline = match.groups()
            is_child = current_top is not None and label in children.get(current_top, set())
            is_top = label in top_names and not is_child

            if is_top:
                current_top = label
                parent = None
            elif is_child:
                parent = current_top
            elif label in all_child_names:
                issues.append(Issue(
                    "SYNTAX",
                    line_number,
                    f"{label} is not valid inside {current_top or 'the document root'}",
                    label,
                ))
                current = None
                continue
            elif re.fullmatch(r"[A-Z][A-Z0-9 _/'-]*", label):
                issues.append(Issue("SYNTAX", line_number, f"unknown section {label}", label))
                current = None
                continue
            else:
                match = None

            if match:
                if label in sections:
                    issues.append(Issue(
                        "SYNTAX",
                        line_number,
                        f"duplicate section {label}; first declared at line {sections[label].header_line}",
                        label,
                        [sections[label].header_line],
                    ))
                    current = sections[label]
                else:
                    current = Section(label, parent, line_number)
                    sections[label] = current
                if inline:
                    current.lines.append(SourceLine(line_number, inline))
                continue

        if current is not None:
            current.lines.append(SourceLine(line_number, raw))

    return sections, issues


def strip_bullet(text: str) -> str:
    return re.sub(r"^\s*-\s*", "", text.strip()).strip()


def meaningful(line: SourceLine, none_markers: set[str]) -> bool:
    value = strip_bullet(line.text)
    if not value:
        return False
    if value.startswith("<!--") or value.startswith("#"):
        return False
    if re.fullmatch(r"\[[^\]]*\]", value):
        return False
    if re.fullmatch(r"[^:]{1,60}:\s*", value):
        return False
    return True


def section_lines(
    name: str,
    sections: dict[str, Section],
    profile: dict[str, Any],
) -> list[SourceLine]:
    result = list(sections.get(name, Section(name, None, 0)).lines)
    for child in profile["children"].get(name, []):
        if child in sections and sections[child].parent == name:
            result.extend(sections[child].lines)
    return result


def has_content(
    name: str,
    sections: dict[str, Section],
    profile: dict[str, Any],
    none_markers: set[str],
) -> bool:
    return any(meaningful(line, none_markers) for line in section_lines(name, sections, profile))


def first_content(section: Section | None, none_markers: set[str]) -> SourceLine | None:
    if section is None:
        return None
    for line in section.lines:
        if meaningful(line, none_markers):
            return line
    return None


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite number {value} is not allowed")


def parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    try:
        value = json.loads(raw, parse_constant=reject_json_constant)
    except json.JSONDecodeError:
        if re.fullmatch(r"[A-Za-z0-9_./:+-]+", raw):
            return raw
        raise ValueError("value with spaces must be a JSON string") from None
    if isinstance(value, (dict, list)):
        raise ValueError("scalar operator requires a string, number, boolean, or null")
    return value


def parse_atom(line: SourceLine, section: str) -> Atom:
    match = ATOM_RE.match(line.text)
    if not match:
        raise ValueError("expected '- [scope] subject OP value'")
    scope, subject, op, raw_value = match.groups()
    if op in {"in", "not-in"}:
        try:
            value = json.loads(raw_value, parse_constant=reject_json_constant)
        except json.JSONDecodeError as exc:
            raise ValueError("in/not-in requires a JSON array") from exc
        if not isinstance(value, list) or not value:
            raise ValueError("in/not-in requires a non-empty JSON array")
        if any(isinstance(item, (dict, list)) for item in value):
            raise ValueError("set members must be scalar values")
    else:
        value = parse_scalar(raw_value)
    if op in {"<", "<=", ">", ">="} and (not isinstance(value, (int, float)) or isinstance(value, bool)):
        raise ValueError("ordered comparisons require a numeric value")
    return Atom(scope, subject, op, value, section, line.number)


def canonical(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError("non-finite numbers are not allowed")
        if numeric.is_integer():
            return str(int(numeric))
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def collect_atoms(
    sections: dict[str, Section],
    profile: dict[str, Any],
    none_markers: set[str],
) -> tuple[list[Atom], list[Issue]]:
    atoms: list[Atom] = []
    issues: list[Issue] = []
    for name in profile["atomic_sections"]:
        section = sections.get(name)
        if section is None:
            continue
        for line in section.lines:
            if not meaningful(line, none_markers):
                continue
            value = strip_bullet(line.text).upper()
            if value in none_markers:
                continue
            try:
                atoms.append(parse_atom(line, name))
            except ValueError as exc:
                issues.append(Issue("SYNTAX", line.number, str(exc), name))
    return atoms, issues


def check_structure(
    sections: dict[str, Section],
    profile: dict[str, Any],
    none_markers: set[str],
) -> tuple[str | None, list[Issue]]:
    issues: list[Issue] = []
    mode_line = first_content(sections.get("MODE"), none_markers)
    mode: str | None = None
    if mode_line is None:
        issues.append(Issue("MISSING", sections.get("MODE", Section("MODE", None, 1)).header_line or 1, "MODE has no value", "MODE"))
    else:
        mode = strip_bullet(mode_line.text).upper()
        if mode not in profile["modes"]:
            issues.append(Issue("SYNTAX", mode_line.number, f"MODE must be one of {', '.join(profile['modes'])}", "MODE"))
            mode = None

    required = list(profile["required"])
    if mode:
        required.extend(profile["required_by_mode"].get(mode, []))
    for name in required:
        section = sections.get(name)
        if section is None:
            issues.append(Issue("MISSING", 1, f"required section {name} is absent", name))
        elif not has_content(name, sections, profile, none_markers):
            issues.append(Issue("MISSING", section.header_line, f"required section {name} has no substantive value", name))

    if mode:
        child_rules = profile["required_children_by_mode"].get(mode, {})
        for parent, names in child_rules.items():
            for name in names:
                section = sections.get(name)
                if section is None or section.parent != parent:
                    issues.append(Issue("MISSING", sections.get(parent, Section(parent, None, 1)).header_line or 1, f"{parent} requires {name}", name))
                elif not has_content(name, sections, profile, none_markers):
                    issues.append(Issue("MISSING", section.header_line, f"{name} has no substantive value", name))
        any_rules = profile["require_any_children_by_mode"].get(mode, {})
        for parent, names in any_rules.items():
            if not any(has_content(name, sections, profile, none_markers) for name in names if name in sections):
                issues.append(Issue(
                    "MISSING",
                    sections.get(parent, Section(parent, None, 1)).header_line or 1,
                    f"{parent} requires at least one of {', '.join(names)}",
                    parent,
                ))
    return mode, issues


def check_open_questions(
    sections: dict[str, Section],
    none_markers: set[str],
) -> list[Issue]:
    issues: list[Issue] = []
    section = sections.get("OPEN_QUESTIONS")
    if section is None:
        return issues
    for line in section.lines:
        if not meaningful(line, none_markers):
            continue
        if strip_bullet(line.text).upper() in none_markers:
            continue
        match = QUESTION_RE.match(line.text)
        if not match:
            issues.append(Issue(
                "SYNTAX",
                line.number,
                "open question must be '- [HIGH|LOW] subject — question'",
                "OPEN_QUESTIONS",
            ))
        elif match.group(1).upper() == "HIGH":
            issues.append(Issue(
                "UNRESOLVED",
                line.number,
                f"high-impact question {match.group(2)} is unresolved; resolve it or explicitly delegate it",
                "OPEN_QUESTIONS",
            ))
    return issues


def check_delegated(
    sections: dict[str, Section],
    none_markers: set[str],
) -> list[Issue]:
    issues: list[Issue] = []
    section = sections.get("DELEGATED")
    if section is None:
        return issues
    for line in section.lines:
        if not meaningful(line, none_markers):
            continue
        if strip_bullet(line.text).upper() in none_markers:
            continue
        if not DELEGATED_RE.match(line.text):
            issues.append(Issue(
                "SYNTAX",
                line.number,
                "delegation must be '- [scope] subject delegated'",
                "DELEGATED",
            ))
    return issues


def atom_key(atom: Atom) -> tuple[str, str, str, str]:
    return atom.scope, atom.subject, atom.op, canonical(atom.value)


def check_duplicates(atoms: list[Atom]) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[tuple[str, str, str, str], Atom] = {}
    for atom in atoms:
        key = atom_key(atom)
        if key in seen:
            issues.append(Issue(
                "REDUNDANT",
                atom.line,
                f"duplicate atomic requirement; first declared at line {seen[key].line}",
                atom.section,
                [seen[key].line],
                "warning",
            ))
        else:
            seen[key] = atom
    return issues


def max_lower(current: tuple[float, bool, Atom] | None, candidate: tuple[float, bool, Atom]) -> tuple[float, bool, Atom]:
    if current is None or candidate[0] > current[0]:
        return candidate
    if candidate[0] == current[0] and candidate[1] and not current[1]:
        return candidate
    return current


def min_upper(current: tuple[float, bool, Atom] | None, candidate: tuple[float, bool, Atom]) -> tuple[float, bool, Atom]:
    if current is None or candidate[0] < current[0]:
        return candidate
    if candidate[0] == current[0] and candidate[1] and not current[1]:
        return candidate
    return current


def value_allowed(
    value: Any,
    allowed: set[str] | None,
    denied: set[str],
    lower: tuple[float, bool, Atom] | None,
    upper: tuple[float, bool, Atom] | None,
) -> bool:
    key = canonical(value)
    if allowed is not None and key not in allowed:
        return False
    if key in denied:
        return False
    if lower is not None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        if value < lower[0] or (value == lower[0] and lower[1]):
            return False
    if upper is not None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False
        if value > upper[0] or (value == upper[0] and upper[1]):
            return False
    return True


def contradiction_for_group(atoms: list[Atom]) -> Issue | None:
    equals: dict[str, Atom] = {}
    denied: dict[str, Atom] = {}
    allowed: set[str] | None = None
    allowed_atoms: list[Atom] = []
    lower: tuple[float, bool, Atom] | None = None
    upper: tuple[float, bool, Atom] | None = None

    for atom in atoms:
        if atom.op == "=":
            equals[canonical(atom.value)] = atom
        elif atom.op == "!=":
            denied[canonical(atom.value)] = atom
        elif atom.op == "in":
            values = {canonical(item) for item in atom.value}
            allowed = values if allowed is None else allowed & values
            allowed_atoms.append(atom)
        elif atom.op == "not-in":
            for item in atom.value:
                denied[canonical(item)] = atom
        elif atom.op in {">", ">="}:
            lower = max_lower(lower, (float(atom.value), atom.op == ">", atom))
        elif atom.op in {"<", "<="}:
            upper = min_upper(upper, (float(atom.value), atom.op == "<", atom))

    relevant: list[Atom] = []
    if len(equals) > 1:
        relevant = list(equals.values())
    elif equals:
        eq_atom = next(iter(equals.values()))
        if not value_allowed(eq_atom.value, allowed, set(denied), lower, upper):
            relevant = [eq_atom, *allowed_atoms, *denied.values()]
            if lower:
                relevant.append(lower[2])
            if upper:
                relevant.append(upper[2])
    elif lower is not None and upper is not None:
        if lower[0] > upper[0] or (lower[0] == upper[0] and (lower[1] or upper[1])):
            relevant = [lower[2], upper[2]]
    if not relevant and allowed is not None:
        viable = set(allowed) - set(denied)
        if lower is not None or upper is not None:
            viable = {
                key for key in viable
                if value_allowed(json.loads(key), None, set(), lower, upper)
            }
        if not viable:
            relevant = [*allowed_atoms, *denied.values()]
            if lower:
                relevant.append(lower[2])
            if upper:
                relevant.append(upper[2])

    if not relevant:
        return None
    unique = {atom.line: atom for atom in relevant}
    ordered = [unique[line] for line in sorted(unique)]
    first = ordered[0]
    scope = next((atom.scope for atom in atoms if atom.scope != "*"), "*")
    return Issue(
        "CONTRADICTION",
        first.line,
        f"constraints for {first.subject!r} are unsatisfiable in scope {scope!r}",
        first.section,
        [atom.line for atom in ordered[1:]],
    )


def check_contradictions(atoms: list[Atom]) -> list[Issue]:
    issues: list[Issue] = []
    by_subject: dict[str, list[Atom]] = {}
    for atom in atoms:
        by_subject.setdefault(atom.subject, []).append(atom)
    for subject_atoms in by_subject.values():
        specific_scopes = sorted({atom.scope for atom in subject_atoms if atom.scope != "*"})
        scopes = specific_scopes or ["*"]
        seen_lines: set[tuple[int, ...]] = set()
        for scope in scopes:
            group = [atom for atom in subject_atoms if atom.scope in {"*", scope}]
            issue = contradiction_for_group(group)
            if issue:
                key = tuple(sorted([issue.line, *issue.related_lines]))
                if key not in seen_lines:
                    seen_lines.add(key)
                    issues.append(issue)
    return issues


def check_acceptance(
    sections: dict[str, Section],
    atoms: list[Atom],
    none_markers: set[str],
) -> list[Issue]:
    section = sections.get("ACCEPTANCE")
    if section is None:
        return []
    acceptance_atoms = [atom for atom in atoms if atom.section in {"ENGINEERING", "RESEARCH"}]
    direct_lines = [line for line in section.lines if meaningful(line, none_markers)]
    if direct_lines or not acceptance_atoms:
        line = direct_lines[0].number if direct_lines else section.header_line
        return [Issue(
            "UNVERIFIABLE",
            line,
            "ACCEPTANCE must contain at least one atomic check under ENGINEERING or RESEARCH",
            "ACCEPTANCE",
        )]
    return []


def lint(text: str, profile: dict[str, Any]) -> tuple[list[Issue], list[Atom], str | None]:
    none_markers = {value.upper() for value in profile["none_markers"]}
    sections, issues = parse_document(text, profile)
    mode, structure_issues = check_structure(sections, profile, none_markers)
    issues.extend(structure_issues)
    atoms, atom_issues = collect_atoms(sections, profile, none_markers)
    issues.extend(atom_issues)
    issues.extend(check_delegated(sections, none_markers))
    issues.extend(check_open_questions(sections, none_markers))
    issues.extend(check_acceptance(sections, atoms, none_markers))
    issues.extend(check_duplicates(atoms))
    issues.extend(check_contradictions(atoms))
    issues.sort(key=lambda issue: (issue.severity != "error", issue.line, issue.kind))
    return issues, atoms, mode


def render_text(path: Path, issues: Iterable[Issue]) -> str:
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    lines = ["NOT_READY" if errors else "READY"]
    for issue in errors:
        related = f"; related lines {', '.join(map(str, issue.related_lines))}" if issue.related_lines else ""
        section = f" {issue.section}" if issue.section else ""
        lines.append(f"[{issue.kind}]{section} {path}:{issue.line} — {issue.message}{related}")
    if warnings:
        lines.append("WARNINGS")
        for issue in warnings:
            related = f"; related lines {', '.join(map(str, issue.related_lines))}" if issue.related_lines else ""
            lines.append(f"[{issue.kind}] {path}:{issue.line} — {issue.message}{related}")
    return "\n".join(lines)


def default_profile_path() -> Path:
    return Path(__file__).resolve().parents[1] / "profiles" / "ml-research.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", type=Path, help="structured prompt Markdown file")
    parser.add_argument("--profile", type=Path, default=default_profile_path())
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    try:
        text = args.prompt.read_text(encoding="utf-8")
        profile = load_profile(args.profile)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"prompt-lint: {exc}", file=sys.stderr)
        return 2

    issues, atoms, mode = lint(text, profile)
    errors = [issue for issue in issues if issue.severity == "error"]
    if args.format == "json":
        payload = {
            "status": "NOT_READY" if errors else "READY",
            "mode": mode,
            "issues": [asdict(issue) for issue in issues],
            "atomic_requirement_count": len(atoms),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render_text(args.prompt, issues))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
