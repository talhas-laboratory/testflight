import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.validate_concept_lab import validate  # noqa: E402


def test_concept_lab_continuity_cases_validate():
    assert not any(validate(REPO_ROOT).values())
