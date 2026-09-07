# Artifact Production

## Problem solved

The current system can compile context, creative direction, generation packets, outputs, and
evaluations, but it does not define the semantic contract for familiar marketing deliverables.
Artifact production turns World knowledge into typed, reviewable, provider-neutral deliverables
before formatting or publication.

## Artifact domain

Introduce a small `testflight-artifacts` package containing general immutable records and
deterministic lifecycle operations. Keep marketing-specific definitions in a versioned profile
registry or a `testflight-marketing-artifacts` package.

### Core records

- `ArtifactProfile` and immutable `ArtifactProfileRevision`;
- `ArtifactSlot` and `ArtifactRequirement`;
- `ArtifactRequest`;
- `ArtifactContextManifest`;
- `ArtifactProposal`;
- `ArtifactReviewDecision` and immutable `ArtifactVersion`;
- `ArtifactDependencyManifest`;
- `ArtifactEvaluation` and `ArtifactFeedbackProposal`;
- `RenderedArtifact` and `PublicationReceipt`.

The generic package must not import Brand classes, model SDKs, render libraries, or delivery
platforms. Marketing profiles may reference Brand type and relation IDs as configuration.

## Artifact profile

An artifact profile declares:

- profile identity, revision, lifecycle, authority, valid time, and supported locales;
- required and optional slots;
- allowed World types and relationship roles for each slot;
- evidence, authority, rights, and freshness requirements;
- content structure and cardinality;
- artifact-level and slot-level evaluators;
- approval policy;
- supported render formats and channel variants.

A campaign-brief profile could require objective, audience, problem/tension, offering, proposition,
proof, desired response, channels, Creative Field, exclusions, risks, and success metrics. A
newsletter profile would instead require subject, preview, message hierarchy, body blocks, CTA,
links, claims, and compliance blocks.

Profiles are contracts, not prompts. Operator instructions and provider templates are derived
from the selected profile revision.

## Creation operator

Each creation operator accepts only:

```text
ArtifactRequest
+ ArtifactProfileRevision
+ immutable ArtifactContextManifest
+ optional parent ArtifactVersion
+ declared generation configuration
```

It returns a typed `ArtifactProposal` with:

- structured slot values;
- slot-level source and semantic record references;
- assumptions and unresolved questions;
- claims and evidence mappings;
- omitted requirements and explicit disposition;
- operator/provider receipt;
- proposal-only status.

Operators should be artifact-specific where procedures differ, for example
`compose-campaign-brief@1`, `compose-message-matrix@1`, and `compose-newsletter@1`. Shared controls
such as evidence grounding, tone projection, claim handling, and revision preservation should be
composed rather than copied into every prompt.

## Evaluation layers

Run evaluation before approval and again after rendering where applicable:

1. **Schema:** required slots, types, cardinality, character limits.
2. **Provenance:** material fields and claims resolve to the frozen context.
3. **Semantic:** objective, audience, offering, message, and CTA are coherent.
4. **Epistemic:** unsupported claims, contradictions, assumptions, and uncertainty remain visible.
5. **Brand/creative:** voice, visual language, Creative Field, exclusions, and rights.
6. **Channel/format:** accessibility, placement rules, technical constraints, legal hooks.
7. **Continuity:** requested revisions survive context, composition, review, and rendering.

No single score should hide a material failure. Readiness is a typed outcome: ready, partial,
branch, ask, hold, or failed.

## Review and versioning

Review actions are accept, revise, reject, hold, or branch. Acceptance requires an authority grant
and the expected proposal revision. An accepted artifact version freezes content, profile revision,
context manifest, dependencies, evaluation, review records, and creation derivation.

Revision instructions must identify targeted slots and preserve unaffected accepted content. A
model revision is a new proposal, not an in-place mutation. If the governing context changes,
re-resolve it and create a new lineage version rather than silently refreshing fields.

## Relationship to existing Creative Field

Creative Field remains a reviewed source of creative principles, tensions, exclusions, and
modality-aware projection. It should be one input to visual and expressive artifact slots, not the
general artifact lifecycle itself.

Reuse its successful patterns: proposal-only model output, authority-bearing acceptance, immutable
versions, scoped bindings, target-neutral projections, capability-aware packets, invocation
receipts, content-addressed outputs, and post-generation evaluation.

## First profiles

Build only these profiles for the first product slice:

1. Campaign Brief
2. Message Matrix / Copy Deck
3. Social Campaign Pack

The campaign brief becomes the parent artifact. The message matrix references its approved version,
and each social variant references both. This tests dependency, continuity, revision, rendering,
and cross-artifact evaluation without requiring a universal catalog.

