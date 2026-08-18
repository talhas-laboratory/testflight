# Brand workspace routing

This template is a navigation and policy index. It is not a source of Brand facts.

| Intent | Route | Primary artifacts |
| --- | --- | --- |
| Define a Brand component | `define` | `domains/brand/ontology/`, workspace manifest |
| Ingest source material | `ingest` | evidence envelope and source hash |
| Extract entities/relations | `extract` | semantic proposals and exact spans |
| Review identity or assertion | `review` | hypotheses, evidence, contradictions |
| Explain a Brand relationship | `query` | assertion node plus evidence spans |
| Compare intended and observed layers | `query` | perspective-filtered assertions |
| Rebuild Cognee | `rebuild` | canonical records and projection receipt |
| Certify retrieval | `certify` | certification cases and report |

Route to the smallest task view first. Use lexical retrieval before bounded hybrid retrieval.
Graph traversal is reserved for explicit, maximum-two-hop relationship questions. An unsupported
query returns `NO_HITS`.
