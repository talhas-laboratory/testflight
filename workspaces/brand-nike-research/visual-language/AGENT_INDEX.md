# Nike visual-language child container

This child container holds modular, versioned visual-language references for the isolated Nike
research workspace. It is a retrieval projection source, not canonical Nike brand guidance.

## Retrieval contract

- Resolve profile bindings by explicit scope and valid time before using semantic retrieval.
- Search exact profile, revision, and reference ids first.
- Use BM25 only for exploratory visual-reference questions within this child.
- Treat `authorized_internal` as production-capable only when rights and approval are present.
- Treat public observations, inferences, and proposals as reference or inspiration only.
- Return `no_hit`, `partial`, or `needs_clarification` when the requested scope is unsupported.

## Contents

- `manifest.json`: immutable references, profile revisions, and scope bindings.
- `AGENT_CONFIG.yaml`: child-container routing and quality rules.
- `README.md`: authoring and maintenance guidance.

