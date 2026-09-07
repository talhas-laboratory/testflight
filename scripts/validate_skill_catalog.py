#!/usr/bin/env python3
"""Validate the repo-local smart skill catalog and discoverable skill packages."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / ".agents" / "skills"
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a mapping")
    return value


def load_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} is missing YAML frontmatter")
    try:
        block = text.split("---\n", 2)[1]
    except IndexError as error:
        raise ValueError(f"{path} has incomplete YAML frontmatter") from error
    value = yaml.safe_load(block)
    if not isinstance(value, dict):
        raise ValueError(f"{path} frontmatter must be a mapping")
    return value


def main() -> int:
    config = load_yaml(SKILLS_ROOT / "AGENT_CONFIG.yaml")
    catalog = load_yaml(SKILLS_ROOT / "catalog.yaml")
    categories = set(config.get("categories", []))
    statuses = set(config.get("statuses", []))
    entries = catalog.get("skills")
    if not isinstance(entries, list):
        raise SystemExit("catalog skills must be an array")

    errors: list[str] = []
    seen: set[str] = set()
    catalog_paths: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"catalog entry {index} must be a mapping")
            continue
        skill_id = entry.get("id")
        path_value = entry.get("path")
        if not isinstance(skill_id, str) or not NAME_PATTERN.fullmatch(skill_id):
            errors.append(f"catalog entry {index} has invalid id")
            continue
        if skill_id in seen:
            errors.append(f"duplicate skill id: {skill_id}")
        seen.add(skill_id)
        if path_value != skill_id:
            errors.append(f"skill {skill_id} path must equal its id for flat discovery")
            continue
        catalog_paths.add(path_value)
        if entry.get("category") not in categories:
            errors.append(f"skill {skill_id} has unknown category")
        if entry.get("status") not in statuses:
            errors.append(f"skill {skill_id} has unknown status")
        if not entry.get("triggers"):
            errors.append(f"skill {skill_id} must declare triggers")

        skill_dir = SKILLS_ROOT / path_value
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"skill {skill_id} is missing SKILL.md")
            continue
        frontmatter = load_frontmatter(skill_file)
        if frontmatter.get("name") != skill_id:
            errors.append(f"skill {skill_id} frontmatter name does not match")
        if not frontmatter.get("description"):
            errors.append(f"skill {skill_id} frontmatter description is required")

        openai_path = skill_dir / "agents" / "openai.yaml"
        if openai_path.exists():
            openai = load_yaml(openai_path)
            default_prompt = openai.get("interface", {}).get("default_prompt", "")
            if f"${skill_id}" not in default_prompt:
                errors.append(f"skill {skill_id} default_prompt must mention ${skill_id}")

    discovered_paths = {
        path.parent.relative_to(SKILLS_ROOT).as_posix() for path in SKILLS_ROOT.glob("*/SKILL.md")
    }
    for path_value in sorted(discovered_paths - catalog_paths):
        errors.append(f"uncatalogued skill directory: {path_value}")
    for path_value in sorted(catalog_paths - discovered_paths):
        errors.append(f"catalog path is not discoverable: {path_value}")

    if errors:
        raise SystemExit("skill catalog validation failed:\n- " + "\n- ".join(errors))
    print(f"validated {len(entries)} repo-local skills across {len(categories)} categories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
