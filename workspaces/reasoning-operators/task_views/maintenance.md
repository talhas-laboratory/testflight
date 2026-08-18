# Maintenance task view

## Goal

Refresh or rebuild the workspace projection without drifting from the
canonical operator contracts.

## Procedure

1. Validate `WORKSPACE.yaml`, the canonical operator catalog, and metadata.
2. Compare source hashes against the last population report.
3. Rebuild Cognee derived state when an operator/version/source/policy changes.
4. Run exact, intent, adversarial, and no-hit probes.
5. Record the revision, dataset name, statuses, omissions, and diagnostics.

Never edit generated Cognee data as a substitute for changing the canonical
operator YAML or workspace policy in Git.
