"""Extensible creative dimension registry."""

from pathlib import Path
from typing import Any

import yaml

from .models import FieldDimension


def load_dimension_registry(path: Path) -> tuple[FieldDimension, ...]:
    payload: Any = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict) or not isinstance(payload.get("dimensions"), list):
        raise ValueError(f"dimension registry must contain a dimensions list: {path}")
    dimensions = tuple(FieldDimension.model_validate(item) for item in payload["dimensions"])
    ids = [item.dimension_id for item in dimensions]
    if len(ids) != len(set(ids)):
        raise ValueError("dimension registry contains duplicate IDs")
    return dimensions


__all__ = ["load_dimension_registry"]
