# Project skills

This is the repo-local skill discovery root. Skills stay as direct child directories so Codex and
other agents can discover them without knowing a category hierarchy.

Use [`catalog.yaml`](catalog.yaml) for machine-readable routing. Use
[`AGENT_CONFIG.yaml`](AGENT_CONFIG.yaml) for folder and lifecycle policy.

## Routing

- Create or register a specialized child knowledge container:
  [`child-container-creator`](child-container-creator/SKILL.md).

Categories are metadata, not folders. Add a new skill at `.agents/skills/<skill-name>/`, then add
one matching entry to `catalog.yaml` and run:

```bash
uv run python scripts/validate_skill_catalog.py
```

