# Relational content

## Mission

Develop bounded theories of how people, self, brand, product, and shared fields of engagement relate, without asserting customer facts or publishing content

## Scope

This child is bounded to `world://workspace/concept-lab/relational-content`. It develops theories
of relational content engagement: person, self, field of engagement, brand, and product. It has no
imported Biotic source records and must not infer customer beliefs, biological mechanisms, or
publication authority.

## Retrieval

Use exact lookup or BM25 first inside this child. Use bounded same-child hybrid retrieval only
after an in-domain lexical no-hit. Use graph traversal only for explicit path questions with at
most two hops. Return `NO_HITS` for unsupported or out-of-domain requests.

## Navigation

- `AGENT_CONFIG.yaml`: retrieval and quality policy.
- `WORKSPACE.yaml`: identity and parent topology.
- `artifacts/source_manifest.yaml`: intentionally empty until an explicit bridge or scoped source
  record is added.
- `resource_registry.json`: source metadata and provenance.
- `certification_cases/probes.yaml`: retrieval certification cases.
