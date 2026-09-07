# ADR 0006: Add a Multimodal Content Substrate and Explicit World Compilation Boundary

## Status

Accepted for phased implementation — 2026-09-04

## Context

The completed Moodboard / Creative Field vertical slice can retain references, extract bounded
features, propose interpretations, synthesize a reviewed Creative Field, bind it to a project, and
compile target-specific packets. The semantic kernel can preserve evidence, states, perspectives,
branches, relationship frames, hypotheses, outcomes, and bounded World views.

The next use case begins earlier and spans more domains: ingest authorized social profiles and
reels multimodally, determine their internal content structure, find recurring visual/audio/textual
and semantic patterns, interpret expressed brand behavior, project suitable proposals into the
World, and use selected knowledge to steer later reasoning.

Without a new boundary, implementation could:

- make provider payloads or model output the ontology;
- mix perception with interpretation;
- treat repeated frames from one reel as independent pattern evidence;
- insert social-analysis vocabulary directly into the shared World;
- turn retrieval rank or model confidence into semantic truth;
- inject entire content corpora into prompts;
- let generated outputs reinforce their own inferred rules;
- couple shared records to Instagram or one model provider.

## Decision

Add a general, provider-independent Content substrate between immutable source evidence and the
shared World.

The architecture has four semantic movements and three principal compiler boundaries:

```text
authorized source
  -> immutable evidence
  -> Multimodal Content Compiler
  -> normalized Content observations and structure
  -> Interpretation and Module Compiler
  -> module-local proposals and pattern candidates
  -> World Projection Compiler
  -> reviewed World/Creative Field proposals and versions
  -> Context/Steering Compiler
  -> bounded reasoning context
```

The implementation must keep these planes distinct:

1. evidence;
2. observation;
3. normalized Content;
4. interpretation;
5. module-local knowledge;
6. World projection proposal;
7. accepted World state;
8. retrieval selection;
9. reasoning steering;
10. authorized action and observed outcome.

`packages/testflight-content` will own provider-independent records for source envelopes, content
units, media tracks, segments, perceptual observations, cross-modal relations, occurrences, pattern
candidates, interpretation frames, transformation recipes, and derivation receipts.

Domain packages such as a future `testflight-social-analysis` will interpret Content through their
own versioned ontology. A versioned mapping registry will compile module-local records into exact,
conditional, lossy, local-only, unsupported, or ontology-extension World proposals. Compilation
will never imply promotion.

`testflight-context-intelligence` will compose already-typed Content and World records into bounded
reasoning steering packets. It will not own perception or interpretation. Retrieval selects
evidence; a downstream operator reasons over the selected packet.

Generated outputs may re-enter the Content pipeline for evaluation, but feedback remains a proposal
until reviewed or supported by an explicit experiment/learning policy.

Instagram-specific acquisition, authentication, rate limits, source IDs, and transport behavior
will remain inside an adapter. The initial adapter must use an authorized route and may return
`partial`, `no_hit`, or `hold`. Visibility alone is not treated as permission.

## Invariants

- Every material observation resolves to immutable source anchors.
- Observations do not contain unsupported intent or brand identity.
- Interpretations retain alternatives, counterevidence, scope, time, and epistemic status.
- Pattern generalization counts independent content occurrences and preserves counterexamples.
- Source identity, semantic identity, actor authority, workspace, version, and derivation remain
  distinct.
- Module-to-World mappings do not add unrecorded semantic meaning.
- Schema success, semantic acceptance, persistence, and action authorization remain separate.
- Accepted World state changes only through an authority-bearing review or policy-controlled commit.
- Steering context cannot grant authority that its sources do not possess.
- Derived indexes and projections remain rebuildable from canonical source and derivation records.

## Consequences

- A new shared Content package and later module-specific social-analysis package are required.
- Existing Creative Field observation and interpretation contracts can be reused by projection or
  composition, but do not become the universal Content schema.
- Existing blob storage, append-oriented persistence, operator runtime, evidence links, World views,
  and context packet behavior should be reused through ports.
- A deterministic synthetic fixture path must precede live multimodal/provider integration.
- World mapping and reasoning steering receive separate test and review gates.
- The first vertical slice can operate on an owner-provided or synthetic profile bundle without
  solving arbitrary public-profile acquisition.

## Rejected alternatives

### Put social observations directly into the Brand ontology

Rejected because a platform-local content reading is not automatically a Brand-world fact and
because unmappable concepts need a legitimate local home.

### Extend only `ReferenceAsset` and `ObservedFeature`

Rejected as the universal model because synchronized tracks, segmentation revisions, cross-modal
relations, occurrence independence, and reusable interpretations need explicit contracts. Creative
Field remains a consumer and projection target.

### Store one model-generated profile dossier

Rejected because it hides source anchors, alternatives, counterexamples, derivation, mapping loss,
and review status inside prose.

### Use embeddings as the normalized Content layer

Rejected because embeddings are provider/version-dependent retrieval features, not inspectable
semantic records or evidence.

### Feed all normalized Content into every reasoning request

Rejected because it violates bounded retrieval, increases disclosure and noise, and lets untrusted
source content influence operator instructions.

## Related artifacts

- `docs/plans/2026-09-03-multimodal-content-world-compilation-design.md`
- `docs/contracts/content-semantic-planes.md`
- ADR 0003 — Brand canonical model and Cognee projection.
- ADR 0005 — Moodboard / Creative Field application profile.
- `reasoning/README.md`
- `packages/testflight-creative-field/README.md`
- `packages/testflight-context-intelligence/README.md`

