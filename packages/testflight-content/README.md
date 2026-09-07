# Testflight Content

Provider-independent, immutable contracts for the normalized Content substrate between source
evidence and domain interpretation. This package intentionally contains no platform adapters,
model/provider SDKs, retrieval/index code, persistence implementation, or UI code.

The package distinguishes:

```text
SourceEnvelope
  → ContentUnit + MediaTrack + ContentSegment
  → PerceptualObservation + CrossModalRelation
  → ContentOccurrence + PatternCandidate
  → InterpretationFrame + TransformationRecipe
  → ContentInterpretation
```

`ContentBundle` performs deterministic cross-record validation for source, unit, anchor, temporal,
scope, and independent-recurrence references. It does not determine semantic truth or promote any
interpretation into the Brand World. Module packages and adapters compose these records by stable
IDs and retain their own semantics outside this package.

The source of truth for the semantic planes and legal handoffs is
`docs/contracts/content-semantic-planes.md`; the architecture decision is ADR 0006.
