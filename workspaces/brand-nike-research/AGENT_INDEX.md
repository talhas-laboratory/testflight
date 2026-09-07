# Nike research workspace routing

This index routes retrieval. It is not evidence and must not be returned as the answer to a
non-navigation query.

| Intent | Smallest route | Primary artifacts | Retrieval |
| --- | --- | --- | --- |
| Find or verify a public source | `research` | `source-catalog.yaml`, `evidence-notes.yaml` | BM25 |
| Find Nike identity, offering, audience, or other entity | `entity` | `entity-inventory.yaml` | BM25, bounded hybrid on in-domain no-hit |
| Explain a Brand relationship | `relationship` | `relationship-inventory.yaml`, evidence notes | BM25 or explicit graph, maximum two hops |
| Compile context for an asset workflow | `asset-context` | `asset-workflow-context.yaml`, entity and relation inventories | deterministic stage route, then BM25 |
| Resolve a scoped world view | `world-modeling` | `world-modeling.yaml` | exact context + branch compiler; source-grounded record lookup only |
| Compare intended and observed Brand layers | `review` | entity and relationship inventories | perspective-filtered BM25 |
| Inspect conflict, uncertainty, or source limitations | `review` | evidence notes, relationship inventory | BM25 |
| Refresh or rebuild the isolated projection | `maintenance` | workspace manifest, source catalog | exact artifact |

Route to the smallest relevant child container first. Use BM25 before bounded hybrid retrieval.
Use graph retrieval only when the query explicitly asks for a relationship or path, and stop at two
hops. Never broaden an out-of-domain lexical no-hit into semantic retrieval; return `NO_HITS`.

The subject boundary is the NIKE Brand. NIKE, Inc. is its governing company; Jordan Brand and
Converse are related portfolio brands and must not be silently merged with NIKE Brand identity.
