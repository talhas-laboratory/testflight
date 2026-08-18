"""Stable identifiers for semantic records and rebuildable projections."""

from uuid import NAMESPACE_URL, UUID, uuid5


def stable_id(kind: str, *parts: object) -> UUID:
    """Derive a deterministic identifier from meaning-affecting inputs."""

    if not kind.strip():
        raise ValueError("kind must not be empty")
    normalized = ":".join(str(part) for part in parts)
    return uuid5(NAMESPACE_URL, f"testflight:{kind}:{normalized}")


__all__ = ["stable_id"]
