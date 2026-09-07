"""Dependency-free adapter descriptor and health probe."""

descriptor = {
    "name": "testflight-adapter-creative-connectors",
    "capability": "creative-target-connectors",
    "upstream": None,
    "writesKnowledge": False,
    "writesCanonicalState": False,
}


def health_probe() -> bool:
    """Return whether the provider-neutral connector boundary can be imported."""

    return True


__all__ = ["descriptor", "health_probe"]
