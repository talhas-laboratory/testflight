# Brand World Canvas

A standalone, read-only semantic canvas for navigating a Brand through the eight canonical Brand
ontology systems. The initial workspace is Biotic / Hellobiotic.

Run from the repository root:

```bash
make serve-brand-world
```

Then open <http://127.0.0.1:8792>.

The server projects canonical workspace records at request time. System assignments for
supplemental graph vocabularies are presentation-only and remain visible in each record's detail
card; the application does not write to the Brand workspace.

The world map is served from `/api/world`. Selecting a record loads a bounded dossier from
`/api/records/{record_id}` with separate assertion, interpretation, permitted-use, scope,
constraint, unknown, relation, evidence, and source fields.

Biotic's source policy prohibits storing full webpage bodies. The dossier therefore preserves the
available bounded excerpt, paraphrased findings, limitations, provenance, and a link to the live
original. It does not present a paraphrase or excerpt as full text.
