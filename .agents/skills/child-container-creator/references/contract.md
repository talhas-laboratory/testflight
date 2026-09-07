# Child container contract

Read this reference when populating or certifying a child container.

## Canonical pack

A child scaffold contains:

```text
<child>/
├── AGENT_INDEX.md
├── AGENT_CONFIG.yaml
├── WORKSPACE.yaml
├── artifacts/
│   └── source_manifest.yaml
├── certification_cases/
│   └── probes.yaml
└── resource_registry.json
```

The parent must separately register the child in its topology and register any child sources its
own contract requires. Generated vector, graph, cache, database, model, and `.data/` files are not
canonical artifacts.

## Required source metadata

Every resource record must contain non-empty values for:

- `module`
- `unit`
- `task_view`
- `tool`
- `doc_type`
- `evidence_tier`
- `experience_type`
- `difficulty`
- `canonical`
- `last_verified_at`
- `source_url`

Add domain-specific identity, authority, rights, scope, valid-time, and hash fields when the child
contract needs them. A reachable source is not automatically authoritative or permitted.

## Retrieval contract

1. Resolve workspace, permissions, branch, scope, time, and requested evidence.
2. Route to the smallest applicable child.
3. Use exact lookup for known IDs or artifacts; otherwise use BM25.
4. Use bounded hybrid retrieval only after an in-domain lexical no-hit and only in the same child.
5. Traverse the graph only for explicit relationship/path requests, with `max_hops <= 2`.
6. Return an honest no-hit rather than retrieving unrelated parent material.

Always reject `AGENT_INDEX.md` as an ordinary answer unless the request is navigational. Reject
`AGENT_CONFIG.yaml` unless the request is about configuration or policy.

## Certification gates

Certification requires source-bearing records and these probe classes:

- `exact_artifact`
- `intent_route`
- `adversarial_navigation`
- `out_of_domain_no_hit`

Recommended minimums are top-1 precision `>= 0.90`, routing error `<= 0.03`, query failure
`<= 0.005`, and no-hit correctness `1.0`. Structural validation alone leaves the child in `draft`
or `candidate` status.

## Parent registration receipt

Record:

- parent and child workspace IDs;
- canonical child path;
- staging dataset;
- route and explicit child container IDs;
- parent files updated;
- source registry hashes;
- validation and certification results;
- whether live population was requested and performed.

