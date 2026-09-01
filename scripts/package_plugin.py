#!/usr/bin/env python3
"""Synchronize and validate the distributable skill copy inside the plugin."""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / ".agents" / "skills" / "prompt-readiness-gate"
DESTINATION = (
    REPO_ROOT / "plugins" / "prompt-readiness-gate" / "skills" / "prompt-readiness-gate"
)
IGNORED_PARTS = {"__pycache__", ".DS_Store"}


def files(root: Path) -> dict[Path, Path]:
    return {
        path.relative_to(root): path
        for path in root.rglob("*")
        if path.is_file()
        and not any(part in IGNORED_PARTS for part in path.relative_to(root).parts)
        and path.suffix not in {".pyc", ".pyo"}
    }


def differences() -> list[str]:
    source_files = files(SOURCE)
    destination_files = files(DESTINATION) if DESTINATION.exists() else {}
    messages = [
        f"missing from plugin: {path}"
        for path in sorted(source_files.keys() - destination_files.keys())
    ]
    messages.extend(
        f"stale in plugin: {path}"
        for path in sorted(destination_files.keys() - source_files.keys())
    )
    messages.extend(
        f"content differs: {path}"
        for path in sorted(source_files.keys() & destination_files.keys())
        if not filecmp.cmp(source_files[path], destination_files[path], shallow=False)
    )
    return messages


def sync() -> None:
    source_files = files(SOURCE)
    destination_files = files(DESTINATION) if DESTINATION.exists() else {}
    for relative, source in source_files.items():
        destination = DESTINATION / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for relative in destination_files.keys() - source_files.keys():
        (DESTINATION / relative).unlink()
    for directory in sorted(DESTINATION.rglob("*"), reverse=True):
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()


def validate_manifests() -> list[str]:
    problems: list[str] = []
    plugin_path = (
        REPO_ROOT
        / "plugins"
        / "prompt-readiness-gate"
        / ".codex-plugin"
        / "plugin.json"
    )
    marketplace_path = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
    try:
        plugin = json.loads(plugin_path.read_text(encoding="utf-8"))
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"distribution manifest is unreadable: {error}"]

    if plugin.get("name") != "prompt-readiness-gate":
        problems.append("plugin name must be prompt-readiness-gate")
    if plugin.get("skills") != "./skills/":
        problems.append("plugin skills path must be ./skills/")
    entries = [
        entry
        for entry in marketplace.get("plugins", [])
        if entry.get("name") == plugin.get("name")
    ]
    if len(entries) != 1:
        problems.append("marketplace must contain exactly one matching plugin entry")
    elif entries[0].get("source", {}).get("path") != "./plugins/prompt-readiness-gate":
        problems.append("marketplace plugin source path is incorrect")
    metadata = SOURCE / "agents" / "openai.yaml"
    if not metadata.is_file() or "$prompt-readiness-gate" not in metadata.read_text(
        encoding="utf-8"
    ):
        problems.append(
            "skill invocation metadata is missing or has no explicit $skill example"
        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sync", action="store_true", help="copy the canonical skill into the plugin"
    )
    args = parser.parse_args()
    if args.sync:
        sync()
    problems = differences() + validate_manifests()
    if problems:
        print("Distribution validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("Distribution validation passed: canonical skill and plugin package match")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
