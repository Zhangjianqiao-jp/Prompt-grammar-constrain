"""Deterministic linter for the ML Research & Coding Prompt Grammar."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

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
ENTITY_RE = re.compile(
    r"^\s*-\s*([A-Za-z][A-Za-z0-9_.-]*)\s*:\s*"
    r"(integer|number|boolean|string|path|enum|any)"
    r"(?:\s+aliases\s+(\[.*\]))?\s*$"
)
SCOPE_RE = re.compile(r"^\s*-\s*([A-Za-z0-9_.-]+)\s*$")
SCOPE_RELATION_RE = re.compile(
    r"^\s*-\s*([A-Za-z0-9_.-]+)\s+(overlaps|excludes)\s+"
    r"([A-Za-z0-9_.-]+)\s*$"
)
EVIDENCE_RE = re.compile(
    r"^\s*-\s*\[([A-Za-z0-9_*.-]+)\]\s+"
    r"([A-Za-z][A-Za-z0-9_.-]*)\s+<-\s+"
    r"([A-Za-z][A-Za-z0-9_-]*):(.+?)\s*$"
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


@dataclass(frozen=True)
class Entity:
    name: str
    value_type: str
    aliases: tuple[str, ...]
    line: int


@dataclass(frozen=True)
class Evidence:
    scope: str
    subject: str
    kind: str
    locator: str
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
        profile = json.load(handle)
    validate_profile(profile)
    return profile


def validate_profile(profile: Any) -> None:
    if not isinstance(profile, dict):
        raise TypeError("profile root must be a JSON object")
    list_fields = (
        "modes",
        "required",
        "top_sections",
        "atomic_sections",
        "none_markers",
    )
    dict_fields = (
        "required_by_mode",
        "required_children_by_mode",
        "require_any_children_by_mode",
        "children",
    )
    for key in list_fields:
        value = profile.get(key)
        if (
            not isinstance(value, list)
            or not value
            or not all(isinstance(item, str) for item in value)
        ):
            raise ValueError(f"profile field {key!r} must be a non-empty string list")
    for key in dict_fields:
        if not isinstance(profile.get(key), dict):
            raise TypeError(f"profile field {key!r} must be an object")
    version = profile.get("profile_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise ValueError("profile_version must be a positive integer")
    if "MODE" not in profile["top_sections"]:
        raise ValueError("top_sections must contain MODE")
    known_sections = set(profile["top_sections"])
    known_sections.update(
        child
        for children in profile["children"].values()
        if isinstance(children, list)
        for child in children
    )
    unknown_atomic = set(profile["atomic_sections"]) - known_sections
    if unknown_atomic:
        raise ValueError(
            f"atomic_sections contains unknown sections: {', '.join(sorted(unknown_atomic))}"
        )


def parse_document(
    text: str, profile: dict[str, Any]
) -> tuple[dict[str, Section], list[Issue]]:
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
            is_child = current_top is not None and label in children.get(
                current_top, set()
            )
            is_top = label in top_names and not is_child

            if is_top:
                current_top = label
                parent = None
            elif is_child:
                parent = current_top
            elif label in all_child_names:
                issues.append(
                    Issue(
                        "SYNTAX",
                        line_number,
                        f"{label} is not valid inside {current_top or 'the document root'}",
                        label,
                    )
                )
                current = None
                continue
            elif re.fullmatch(r"[A-Z][A-Z0-9 _/'-]*", label):
                issues.append(
                    Issue("SYNTAX", line_number, f"unknown section {label}", label)
                )
                current = None
                continue
            else:
                match = None

            if match:
                if label in sections:
                    issues.append(
                        Issue(
                            "SYNTAX",
                            line_number,
                            f"duplicate section {label}; first declared at line {sections[label].header_line}",
                            label,
                            [sections[label].header_line],
                        )
                    )
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
    if value.startswith(("<!--", "#")):
        return False
    if re.fullmatch(r"\[[^\]]*\]", value):
        return False
    if value.upper() in none_markers:
        return False
    return not re.fullmatch(r"[^:]{1,60}:\s*", value)


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
    return any(
        meaningful(line, none_markers)
        for line in section_lines(name, sections, profile)
    )


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
        raise ValueError("scalar operator requires a string, number, boolean, or null")  # noqa: TRY004
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are not allowed")
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
        if any(isinstance(item, float) and not math.isfinite(item) for item in value):
            raise ValueError("non-finite numbers are not allowed")
    else:
        value = parse_scalar(raw_value)
    if op in {"<", "<=", ">", ">="} and (
        not isinstance(value, (int, float)) or isinstance(value, bool)
    ):
        raise ValueError("ordered comparisons require a numeric value")
    return Atom(scope, subject, op, value, section, line.number)


def canonical(value: Any) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not allowed")
        if value.is_integer():
            return str(int(value))
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def parse_grammar_version(
    sections: dict[str, Section], none_markers: set[str]
) -> tuple[int, list[Issue]]:
    section = sections.get("GRAMMAR_VERSION")
    if section is None:
        return 1, []
    line = first_content(section, none_markers)
    if line is None:
        return 1, [
            Issue(
                "MISSING",
                section.header_line,
                "GRAMMAR_VERSION has no value",
                "GRAMMAR_VERSION",
            )
        ]
    raw = strip_bullet(line.text)
    if raw not in {"1", "2"}:
        return 1, [
            Issue(
                "UNSUPPORTED_VERSION",
                line.number,
                "GRAMMAR_VERSION must be 1 or 2",
                "GRAMMAR_VERSION",
            )
        ]
    return int(raw), []


def parse_entities(
    sections: dict[str, Section], none_markers: set[str]
) -> tuple[dict[str, Entity], dict[str, str], list[Issue]]:
    entities: dict[str, Entity] = {}
    aliases: dict[str, str] = {}
    issues: list[Issue] = []
    section = sections.get("ENTITIES")
    if section is None:
        return entities, aliases, issues
    for line in section.lines:
        if not meaningful(line, none_markers):
            continue
        match = ENTITY_RE.match(line.text)
        if not match:
            issues.append(
                Issue(
                    "SYNTAX",
                    line.number,
                    "entity must be '- subject : TYPE [aliases [\"alias\"]]'",
                    "ENTITIES",
                )
            )
            continue
        name, value_type, raw_aliases = match.groups()
        if name in entities:
            issues.append(
                Issue(
                    "DUPLICATE_ENTITY",
                    line.number,
                    f"entity {name!r} was already declared",
                    "ENTITIES",
                    [entities[name].line],
                )
            )
            continue
        parsed_aliases: list[str] = []
        if raw_aliases:
            try:
                payload = json.loads(raw_aliases)
            except json.JSONDecodeError:
                payload = None
            if (
                not isinstance(payload, list)
                or not payload
                or any(
                    not isinstance(item, str)
                    or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", item)
                    for item in payload
                )
            ):
                issues.append(
                    Issue(
                        "SYNTAX",
                        line.number,
                        "aliases must be a non-empty JSON array of subject identifiers",
                        "ENTITIES",
                    )
                )
                continue
            parsed_aliases = payload
        entities[name] = Entity(name, value_type, tuple(parsed_aliases), line.number)

    for entity in entities.values():
        for symbol in (entity.name, *entity.aliases):
            owner = aliases.get(symbol)
            if owner is not None and owner != entity.name:
                issues.append(
                    Issue(
                        "ALIAS_COLLISION",
                        entity.line,
                        f"subject {symbol!r} maps to both {owner!r} and {entity.name!r}",
                        "ENTITIES",
                        [entities[owner].line],
                    )
                )
            else:
                aliases[symbol] = entity.name
    return entities, aliases, issues


def parse_scopes(
    sections: dict[str, Section], none_markers: set[str]
) -> tuple[set[str], dict[frozenset[str], str], dict[frozenset[str], int], list[Issue]]:
    scopes: set[str] = set()
    relations: dict[frozenset[str], str] = {}
    relation_lines: dict[frozenset[str], int] = {}
    issues: list[Issue] = []
    section = sections.get("SCOPES")
    if section is None:
        return scopes, relations, relation_lines, issues
    for line in section.lines:
        if not meaningful(line, none_markers):
            continue
        relation_match = SCOPE_RELATION_RE.match(line.text)
        declaration_match = SCOPE_RE.match(line.text)
        if relation_match:
            left, relation, right = relation_match.groups()
            if left == "*" or right == "*" or left == right:
                issues.append(
                    Issue(
                        "INVALID_SCOPE_RELATION",
                        line.number,
                        "scope relations require two distinct named scopes; '*' is implicit",
                        "SCOPES",
                    )
                )
                continue
            scopes.update((left, right))
            key = frozenset((left, right))
            previous = relations.get(key)
            if previous is not None and previous != relation:
                issues.append(
                    Issue(
                        "CONTRADICTORY_SCOPE_RELATION",
                        line.number,
                        f"{left!r} and {right!r} cannot both overlap and exclude each other",
                        "SCOPES",
                        [relation_lines[key]],
                    )
                )
            else:
                relations[key] = relation
                relation_lines[key] = line.number
        elif declaration_match:
            scope = declaration_match.group(1)
            if scope == "*":
                issues.append(
                    Issue(
                        "INVALID_SCOPE",
                        line.number,
                        "global scope '*' is implicit and must not be declared",
                        "SCOPES",
                    )
                )
            else:
                scopes.add(scope)
        else:
            issues.append(
                Issue(
                    "SYNTAX",
                    line.number,
                    "scope must be '- name' or '- left overlaps|excludes right'",
                    "SCOPES",
                )
            )
    return scopes, relations, relation_lines, issues


def parse_evidence(
    sections: dict[str, Section],
    none_markers: set[str],
    aliases: dict[str, str],
    allowed_kinds: set[str],
) -> tuple[list[Evidence], list[Issue]]:
    evidence: list[Evidence] = []
    issues: list[Issue] = []
    section = sections.get("VERIFICATION_PLAN")
    if section is None:
        return evidence, issues
    for line in section.lines:
        if not meaningful(line, none_markers):
            continue
        match = EVIDENCE_RE.match(line.text)
        if not match:
            issues.append(
                Issue(
                    "SYNTAX",
                    line.number,
                    "verification must be '- [scope] subject <- KIND:locator'",
                    "VERIFICATION_PLAN",
                )
            )
            continue
        scope, raw_subject, kind, raw_locator = match.groups()
        if kind not in allowed_kinds:
            issues.append(
                Issue(
                    "UNKNOWN_EVIDENCE_KIND",
                    line.number,
                    f"evidence kind must be one of {', '.join(sorted(allowed_kinds))}",
                    "VERIFICATION_PLAN",
                )
            )
            continue
        try:
            locator = parse_scalar(raw_locator)
        except ValueError as exc:
            issues.append(Issue("SYNTAX", line.number, str(exc), "VERIFICATION_PLAN"))
            continue
        if not isinstance(locator, str) or not locator:
            issues.append(
                Issue(
                    "SYNTAX",
                    line.number,
                    "evidence locator must be a non-empty string",
                    "VERIFICATION_PLAN",
                )
            )
            continue
        subject = aliases.get(raw_subject, raw_subject)
        evidence.append(Evidence(scope, subject, kind, locator, line.number))
    return evidence, issues


def normalize_and_typecheck_atoms(
    atoms: list[Atom], entities: dict[str, Entity], aliases: dict[str, str]
) -> tuple[list[Atom], list[Issue]]:
    normalized: list[Atom] = []
    issues: list[Issue] = []
    for atom in atoms:
        subject = aliases.get(atom.subject)
        if subject is None:
            issues.append(
                Issue(
                    "UNKNOWN_ENTITY",
                    atom.line,
                    f"subject {atom.subject!r} is not declared in ENTITIES",
                    atom.section,
                )
            )
            normalized.append(atom)
            continue
        entity = entities[subject]
        values = atom.value if atom.op in {"in", "not-in"} else [atom.value]
        valid = all(value_matches_type(value, entity.value_type) for value in values)
        if atom.op in {"<", "<=", ">", ">="} and entity.value_type not in {
            "integer",
            "number",
        }:
            valid = False
        if not valid:
            issues.append(
                Issue(
                    "TYPE_MISMATCH",
                    atom.line,
                    f"{atom.op} value does not match declared type {entity.value_type!r} for {subject!r}",
                    atom.section,
                    [entity.line],
                )
            )
        normalized.append(
            Atom(atom.scope, subject, atom.op, atom.value, atom.section, atom.line)
        )
    return normalized, issues


def value_matches_type(value: Any, value_type: str) -> bool:
    if value_type == "any":
        return True
    if value_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if value_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if value_type == "boolean":
        return isinstance(value, bool)
    if value_type in {"string", "path", "enum"}:
        return isinstance(value, str)
    return False


def check_ml_semantic_slots(
    atoms: list[Atom],
    sections: dict[str, Section],
    profile: dict[str, Any],
) -> list[Issue]:
    issues: list[Issue] = []
    by_section: dict[str, list[Atom]] = {}
    for atom in atoms:
        by_section.setdefault(atom.section, []).append(atom)
    for section_name, prefixes in profile.get(
        "subject_prefixes_by_section_v2", {}
    ).items():
        if section_name not in sections:
            continue
        section_atoms = by_section.get(section_name, [])
        if section_atoms and not any(
            any(atom.subject.startswith(prefix) for prefix in prefixes)
            for atom in section_atoms
        ):
            issues.append(
                Issue(
                    "ML_SEMANTIC_SLOT",
                    section_atoms[0].line,
                    f"{section_name} requires an ML subject beginning with {', '.join(prefixes)}",
                    section_name,
                )
            )
    return issues


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
            try:
                atoms.append(parse_atom(line, name))
            except ValueError as exc:
                issues.append(Issue("SYNTAX", line.number, str(exc), name))
    return atoms, issues


def check_structure(
    sections: dict[str, Section],
    profile: dict[str, Any],
    none_markers: set[str],
    grammar_version: int = 1,
) -> tuple[str | None, list[Issue]]:
    issues: list[Issue] = []
    mode_line = first_content(sections.get("MODE"), none_markers)
    mode: str | None = None
    if mode_line is None:
        issues.append(
            Issue(
                "MISSING",
                sections.get("MODE", Section("MODE", None, 1)).header_line or 1,
                "MODE has no value",
                "MODE",
            )
        )
    else:
        mode = strip_bullet(mode_line.text).upper()
        if mode not in profile["modes"]:
            issues.append(
                Issue(
                    "SYNTAX",
                    mode_line.number,
                    f"MODE must be one of {', '.join(profile['modes'])}",
                    "MODE",
                )
            )
            mode = None

    required = list(profile["required"])
    if grammar_version >= 2:
        required.extend(profile.get("required_v2", []))
    if mode:
        required.extend(profile["required_by_mode"].get(mode, []))
    for name in required:
        section = sections.get(name)
        if section is None:
            issues.append(
                Issue("MISSING", 1, f"required section {name} is absent", name)
            )
        elif not has_content(name, sections, profile, none_markers):
            issues.append(
                Issue(
                    "MISSING",
                    section.header_line,
                    f"required section {name} has no substantive value",
                    name,
                )
            )

    if mode:
        child_rules = {
            **profile["required_children_by_mode"].get(mode, {}),
            **(
                profile.get("required_children_by_mode_v2", {}).get(mode, {})
                if grammar_version >= 2
                else {}
            ),
        }
        for parent, names in child_rules.items():
            for name in names:
                section = sections.get(name)
                if section is None or section.parent != parent:
                    issues.append(
                        Issue(
                            "MISSING",
                            sections.get(parent, Section(parent, None, 1)).header_line
                            or 1,
                            f"{parent} requires {name}",
                            name,
                        )
                    )
                elif not has_content(name, sections, profile, none_markers):
                    issues.append(
                        Issue(
                            "MISSING",
                            section.header_line,
                            f"{name} has no substantive value",
                            name,
                        )
                    )
        any_rules = profile["require_any_children_by_mode"].get(mode, {})
        for parent, names in any_rules.items():
            if not any(
                has_content(name, sections, profile, none_markers)
                for name in names
                if name in sections
            ):
                issues.append(
                    Issue(
                        "MISSING",
                        sections.get(parent, Section(parent, None, 1)).header_line or 1,
                        f"{parent} requires at least one of {', '.join(names)}",
                        parent,
                    )
                )
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
        match = QUESTION_RE.match(line.text)
        if not match:
            issues.append(
                Issue(
                    "SYNTAX",
                    line.number,
                    "open question must be '- [HIGH|LOW] subject — question'",
                    "OPEN_QUESTIONS",
                )
            )
        elif match.group(1).upper() == "HIGH":
            issues.append(
                Issue(
                    "UNRESOLVED",
                    line.number,
                    f"high-impact question {match.group(2)} is unresolved; resolve it or explicitly delegate it",
                    "OPEN_QUESTIONS",
                )
            )
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
        if not DELEGATED_RE.match(line.text):
            issues.append(
                Issue(
                    "SYNTAX",
                    line.number,
                    "delegation must be '- [scope] subject delegated'",
                    "DELEGATED",
                )
            )
    return issues


def atom_key(atom: Atom) -> tuple[str, str, str, str]:
    return atom.scope, atom.subject, atom.op, canonical(atom.value)


def check_duplicates(atoms: list[Atom]) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[tuple[str, str, str, str], Atom] = {}
    for atom in atoms:
        key = atom_key(atom)
        if key in seen:
            issues.append(
                Issue(
                    "REDUNDANT",
                    atom.line,
                    f"duplicate atomic requirement; first declared at line {seen[key].line}",
                    atom.section,
                    [seen[key].line],
                    "warning",
                )
            )
        else:
            seen[key] = atom
    return issues


def max_lower(
    current: tuple[float, bool, Atom] | None, candidate: tuple[float, bool, Atom]
) -> tuple[float, bool, Atom]:
    if current is None or candidate[0] > current[0]:
        return candidate
    if candidate[0] == current[0] and candidate[1] and not current[1]:
        return candidate
    return current


def min_upper(
    current: tuple[float, bool, Atom] | None, candidate: tuple[float, bool, Atom]
) -> tuple[float, bool, Atom]:
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
        elif lower[0] == upper[0] and canonical(lower[0]) in denied:
            relevant = [lower[2], upper[2], denied[canonical(lower[0])]]
    if not relevant and allowed is not None:
        viable = set(allowed) - set(denied)
        if lower is not None or upper is not None:
            viable = {
                key
                for key in viable
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
        specific_scopes = sorted(
            {atom.scope for atom in subject_atoms if atom.scope != "*"}
        )
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


def check_v2_scopes_and_contradictions(
    atoms: list[Atom],
    scopes: set[str],
    relations: dict[frozenset[str], str],
    relation_lines: dict[frozenset[str], int],
) -> list[Issue]:
    """Validate explicit scope semantics and solve each co-occurrence family.

    `overlaps` is intentionally transitive in Grammar v2: it builds a conservative
    family of contexts that may coexist. `excludes` keeps families independent.
    An undeclared relation is an error when the same subject appears in both scopes.
    """
    issues: list[Issue] = []
    for atom in atoms:
        if atom.scope != "*" and atom.scope not in scopes:
            issues.append(
                Issue(
                    "UNKNOWN_SCOPE",
                    atom.line,
                    f"scope {atom.scope!r} is not declared in SCOPES",
                    atom.section,
                )
            )

    parent = {scope: scope for scope in scopes}

    def find(scope: str) -> str:
        while parent[scope] != scope:
            parent[scope] = parent[parent[scope]]
            scope = parent[scope]
        return scope

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for pair, relation in relations.items():
        if relation == "overlaps":
            left, right = sorted(pair)
            union(left, right)

    for pair, relation in relations.items():
        if relation == "excludes":
            left, right = sorted(pair)
            if find(left) == find(right):
                issues.append(
                    Issue(
                        "CONTRADICTORY_SCOPE_MODEL",
                        relation_lines[pair],
                        f"{left!r} and {right!r} are excluded but belong to the same overlap family",
                        "SCOPES",
                    )
                )

    by_subject: dict[str, list[Atom]] = {}
    for atom in atoms:
        by_subject.setdefault(atom.subject, []).append(atom)

    for subject_atoms in by_subject.values():
        used_scopes = sorted(
            {
                atom.scope
                for atom in subject_atoms
                if atom.scope != "*" and atom.scope in scopes
            }
        )
        for index, left in enumerate(used_scopes):
            for right in used_scopes[index + 1 :]:
                if find(left) == find(right):
                    continue
                if relations.get(frozenset((left, right))) != "excludes":
                    left_line = next(
                        atom.line for atom in subject_atoms if atom.scope == left
                    )
                    right_line = next(
                        atom.line for atom in subject_atoms if atom.scope == right
                    )
                    issues.append(
                        Issue(
                            "AMBIGUOUS_SCOPE",
                            right_line,
                            f"declare whether scopes {left!r} and {right!r} overlap or exclude each other for subject {subject_atoms[0].subject!r}",
                            subject_atoms[0].section,
                            [left_line],
                        )
                    )

        global_atoms = [atom for atom in subject_atoms if atom.scope == "*"]
        families: dict[str, list[Atom]] = {}
        for atom in subject_atoms:
            if atom.scope != "*" and atom.scope in scopes:
                families.setdefault(find(atom.scope), []).append(atom)
        groups = (
            [global_atoms]
            if not families
            else [global_atoms + family for family in families.values()]
        )
        seen_lines: set[tuple[int, ...]] = set()
        for group in groups:
            issue = contradiction_for_group(group)
            if issue:
                key = tuple(sorted((issue.line, *issue.related_lines)))
                if key not in seen_lines:
                    seen_lines.add(key)
                    issues.append(issue)
    return issues


def check_acceptance(
    sections: dict[str, Section],
    atoms: list[Atom],
    none_markers: set[str],
    grammar_version: int = 1,
    evidence: list[Evidence] | None = None,
) -> list[Issue]:
    section = sections.get("ACCEPTANCE")
    if section is None:
        return []
    acceptance_atoms = [
        atom for atom in atoms if atom.section in {"ENGINEERING", "RESEARCH"}
    ]
    direct_lines = [line for line in section.lines if meaningful(line, none_markers)]
    if direct_lines or not acceptance_atoms:
        line = direct_lines[0].number if direct_lines else section.header_line
        return [
            Issue(
                "UNVERIFIABLE",
                line,
                "ACCEPTANCE must contain at least one atomic check under ENGINEERING or RESEARCH",
                "ACCEPTANCE",
            )
        ]
    issues: list[Issue] = []
    if grammar_version >= 2:
        evidence = evidence or []
        for atom in acceptance_atoms:
            matched = any(
                item.subject == atom.subject and item.scope in {"*", atom.scope}
                for item in evidence
            )
            if not matched:
                issues.append(
                    Issue(
                        "MISSING_EVIDENCE",
                        atom.line,
                        f"acceptance check for {atom.subject!r} has no matching VERIFICATION_PLAN entry",
                        atom.section,
                    )
                )
    return issues


def check_evidence_references(
    evidence: list[Evidence], entities: dict[str, Entity], scopes: set[str]
) -> list[Issue]:
    issues: list[Issue] = []
    seen: dict[tuple[str, str], Evidence] = {}
    for item in evidence:
        if item.subject not in entities:
            issues.append(
                Issue(
                    "UNKNOWN_ENTITY",
                    item.line,
                    f"verification subject {item.subject!r} is not declared in ENTITIES",
                    "VERIFICATION_PLAN",
                )
            )
        if item.scope != "*" and item.scope not in scopes:
            issues.append(
                Issue(
                    "UNKNOWN_SCOPE",
                    item.line,
                    f"verification scope {item.scope!r} is not declared in SCOPES",
                    "VERIFICATION_PLAN",
                )
            )
        key = item.scope, item.subject
        if key in seen:
            issues.append(
                Issue(
                    "REDUNDANT",
                    item.line,
                    "duplicate verification target",
                    "VERIFICATION_PLAN",
                    [seen[key].line],
                    "warning",
                )
            )
        else:
            seen[key] = item
    return issues


def lint(
    text: str, profile: dict[str, Any]
) -> tuple[list[Issue], list[Atom], str | None]:
    none_markers = {value.upper() for value in profile["none_markers"]}
    sections, issues = parse_document(text, profile)
    grammar_version, version_issues = parse_grammar_version(sections, none_markers)
    issues.extend(version_issues)
    mode, structure_issues = check_structure(
        sections, profile, none_markers, grammar_version
    )
    issues.extend(structure_issues)
    atoms, atom_issues = collect_atoms(sections, profile, none_markers)
    issues.extend(atom_issues)
    entities: dict[str, Entity] = {}
    aliases: dict[str, str] = {}
    scopes: set[str] = set()
    relations: dict[frozenset[str], str] = {}
    relation_lines: dict[frozenset[str], int] = {}
    evidence: list[Evidence] = []
    if grammar_version >= 2:
        entities, aliases, entity_issues = parse_entities(sections, none_markers)
        issues.extend(entity_issues)
        scopes, relations, relation_lines, scope_issues = parse_scopes(
            sections, none_markers
        )
        issues.extend(scope_issues)
        atoms, type_issues = normalize_and_typecheck_atoms(atoms, entities, aliases)
        issues.extend(type_issues)
        issues.extend(check_ml_semantic_slots(atoms, sections, profile))
        evidence, evidence_issues = parse_evidence(
            sections,
            none_markers,
            aliases,
            set(profile.get("evidence_kinds", [])),
        )
        issues.extend(evidence_issues)
        issues.extend(check_evidence_references(evidence, entities, scopes))
    issues.extend(check_delegated(sections, none_markers))
    issues.extend(check_open_questions(sections, none_markers))
    issues.extend(
        check_acceptance(sections, atoms, none_markers, grammar_version, evidence)
    )
    issues.extend(check_duplicates(atoms))
    if grammar_version >= 2:
        issues.extend(
            check_v2_scopes_and_contradictions(atoms, scopes, relations, relation_lines)
        )
    else:
        issues.extend(check_contradictions(atoms))
    issues.sort(key=lambda issue: (issue.severity != "error", issue.line, issue.kind))
    return issues, atoms, mode


def render_text(path: Path, issues: Iterable[Issue]) -> str:
    errors = [issue for issue in issues if issue.severity == "error"]
    warnings = [issue for issue in issues if issue.severity == "warning"]
    lines = ["NOT_READY" if errors else "READY"]
    for issue in errors:
        related = (
            f"; related lines {', '.join(map(str, issue.related_lines))}"
            if issue.related_lines
            else ""
        )
        section = f" {issue.section}" if issue.section else ""
        lines.append(
            f"[{issue.kind}]{section} {path}:{issue.line} — {issue.message}{related}"
        )
    if warnings:
        lines.append("WARNINGS")
        for issue in warnings:
            related = (
                f"; related lines {', '.join(map(str, issue.related_lines))}"
                if issue.related_lines
                else ""
            )
            lines.append(
                f"[{issue.kind}] {path}:{issue.line} — {issue.message}{related}"
            )
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
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"prompt-lint: {exc}", file=sys.stderr)
        return 2

    issues, atoms, mode = lint(text, profile)
    errors = [issue for issue in issues if issue.severity == "error"]
    if args.format == "json":
        none_markers = {value.upper() for value in profile["none_markers"]}
        sections, _ = parse_document(text, profile)
        grammar_version, _ = parse_grammar_version(sections, none_markers)
        payload = {
            "status": "NOT_READY" if errors else "READY",
            "grammar_version": grammar_version,
            "profile_version": profile.get("profile_version"),
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
