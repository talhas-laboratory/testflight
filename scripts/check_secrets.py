#!/usr/bin/env python3
"""Fail on secret-bearing files and common credential assignments."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_NAMES = {".env", "id_rsa", "id_ed25519"}
SECRET = re.compile(
    r"(?i)(?:api[_-]?key|password|private[_-]?key|secret)\s*[:=]\s*['\"]?([^\s'\"${}<]+)"
)
TEXT_SUFFIXES = {"", ".env", ".json", ".md", ".py", ".sh", ".toml", ".ts", ".yaml", ".yml"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / item for item in result.stdout.splitlines() if item]


def main() -> None:
    failures: list[str] = []
    for path in tracked_files():
        if path.resolve() == Path(__file__).resolve():
            continue
        if path.name in FORBIDDEN_NAMES:
            failures.append(f"forbidden credential file: {path.relative_to(ROOT)}")
            continue
        if path.suffix not in TEXT_SUFFIXES or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(content.splitlines(), start=1):
            if SECRET.search(line):
                failures.append(f"possible secret: {path.relative_to(ROOT)}:{line_number}")

    if failures:
        raise SystemExit("\n".join(failures))
    print("secret hygiene check passed")


if __name__ == "__main__":
    main()
