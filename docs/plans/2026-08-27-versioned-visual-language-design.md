# Versioned Visual Language System

**Status:** Proposed design  
**Date:** 2026-08-27  
**Scope:** Provider-neutral Brand world, Cognee projection, and Context Intelligence integration

## 1. Purpose

Add a modular visual-language layer to each Brand world so an agent can retrieve the right visual direction for a particular time and context. The system must support current and historical languages, global defaults, and overlays for products, campaigns, offers, audience segments, channels, geographies, and occasions.

The system must distinguish:

- a reusable visual reference;
- a visual-language profile;
- an immutable profile revision;
- the context in which a revision applies;
- observed public patterns from authorized rules;
- source evidence from a generated projection;
- retrieval from interpretation and creative generation.

Cognee remains a rebuildable retrieval projection. Versioned YAML records and referenced assets in the workspace remain the source of truth.

## 2. Considered approaches

### A. One complete document per context and version

Store a complete visual-language document for every campaign, product, audience, and period.

This is easy to understand initially but duplicates shared colors, typography, imagery, and constraints. Corrections become inconsistent, and the number of documents grows combinatorially.

### B. Reusable reference modules plus scoped versioned profiles — recommended

Store atomic visual references once, assemble them into immutable profile revisions, and bind each revision to explicit context selectors. A resolver deterministically composes the smallest applicable set.

This provides reuse, history, clean retrieval, and bounded context packets without requiring a new container for every campaign or audience.

### C. Fully graph-native rules

Represent every token, exception, inheritance rule, scope, and version as graph nodes and edges.

This is maximally flexible but makes authoring, validation, diffing, and deterministic replay unnecessarily difficult for the first implementation. Graph relationships remain useful for exploration, but must not be the sole source of profile resolution.

## 3. Semantic model

### 3.1 Visual reference

An immutable, reusable unit of visual information. References may be machine-actionable, human-facing, or both.

Examples:

- a color token or palette;
- a typography role and typeface specification;
- a grid or spacing scale;
- a photography or illustration reference;
- a logo or symbol asset;
- a motion example;
- an icon family;
- a UI component pattern;
- a composition principle;
- a prohibited example.

Each reference has a stable identity and immutable revision. Binary media is stored outside YAML and addressed by a content hash plus a repository or object-store URI.

### 3.2 Visual-language profile

A stable identity for a named language, such as `Nike global public expression`, `Nike Membership digital`, or `Campaign X launch language`.

A profile identity is not a mutable document. It has a lineage of immutable revisions.

### 3.3 Profile revision

An immutable snapshot that selects visual-reference revisions and declares how they combine. It contains:

- profile identity and revision ID;
- parent revision or revisions;
- branch;
- valid time and recorded time;
- authority and lifecycle status;
- module selections;
- merge behavior;
- evidence and derivation references;
- replacement, deprecation, and conflict information.

### 3.4 Scope binding

A separate record declaring where and when a profile revision applies. Supported selectors are:

- brand;
- product or product family;
- campaign;
- offer or service;
- audience segment;
- channel;
- geography;
- occasion;
- valid time interval.

Separating scope bindings from profile content allows the same revision to be reused in multiple compatible contexts without duplication.

### 3.5 Compiled visual-language packet

A generated, disposable view resolved for one agent request. It is never canonical source state. It includes the selected revisions, actionable modules, conflicts, omissions, provenance, and resolution receipt.

## 4. Extensible reference contract

All visual references share a small envelope:

```yaml
id: VR-NIKE-TYPO-DISPLAY-001
revision: 2
kind: typography.role
schema_version: 1
label: Public campaign display typography observation
payload: {}
asset_refs: []
authority: observed_public
epistemic_status: observed
status: proposed
source_ids: [SRC-NIKE-...]
evidence_ids: [EVID-NIKE-...]
valid_from: 2025-09-04
valid_until: null
recorded_at: 2026-08-27T00:00:00Z
last_verified_at: 2026-08-27
rights:
  permitted_use: analysis_and_reference
  generation_use: inspiration_only
limitations: []
```

`kind` is namespaced and extensible. A registry maps each known kind to a payload schema and compiler. Unknown kinds must round-trip without data loss but are not treated as machine-actionable until a validator is registered.

Initial reference kinds:

- `color.token`, `color.palette`, `color.relationship`;
- `typography.family`, `typography.role`, `typography.scale`;
- `layout.grid`, `layout.spacing`, `layout.composition`;
- `imagery.photography`, `imagery.illustration`, `imagery.art_direction`;
- `symbol.logo`, `symbol.graphic_device`, `symbol.iconography`;
- `motion.principle`, `motion.example`;
- `ui.component`, `ui.pattern`;
- `expression.voice`, `expression.headline`;
- `constraint.required`, `constraint.prohibited`;
- `reference.example`.

This registry is configuration, not a closed ontology. New visual-reference types can be added without changing the profile resolver.

## 5. Versioning and time

The source is append-only. A correction or update creates a new reference revision, profile revision, or scope-binding revision; it never edits historical meaning in place.

Every revision preserves four times when available:

- `valid_from` and `valid_until`: when it applied in the Brand world;
- `recorded_at`: when Testflight stored it;
- `source_published_at`: when the source was published;
- `derived_at`: when a compiled projection was produced.

Every revision also carries:

- stable lineage ID;
- monotonic revision number;
- immutable content hash;
- branch;
- expected prior revision for optimistic concurrency;
- `supersedes`, `corrects`, or `derived_from` links;
- lifecycle status: `draft`, `observed`, `approved`, `deprecated`, `archived`;
- authority: `authorized_internal`, `official_public`, `observed_public`, `inferred`, or `generated_proposal`.

“Latest” never means “most authoritative.” Resolution filters by valid time and scope first, then authority and explicit precedence.

## 6. Deterministic scope resolution

The resolver receives a normalized request:

```text
brand + product + campaign + offer + audience segment + channel +
geography + occasion + valid time + workflow stage
```

Resolution proceeds as follows:

1. Require brand, valid time, and workflow stage.
2. Filter bindings by exact brand and valid-time overlap.
3. Reject bindings with a conflicting explicit selector.
4. Rank remaining bindings by explicit priority, scope specificity, authority, and revision policy.
5. Select the global base and compatible overlays.
6. Compose modules using declared behavior: `replace`, `extend`, or `disable`.
7. Return a conflict when equally authoritative overlays attempt incompatible replacement.
8. Return `partial` when a base exists but requested scopes lack a matching overlay.
9. Return `needs_clarification` when two valid interpretations would materially change the output.
10. Return `no_hit` when no authorized visual language applies.

Default overlay order:

```text
global brand
  -> product or offer
  -> campaign
  -> audience segment
  -> channel
  -> geography and occasion
```

This order is only a default. Explicit priority and module-level merge behavior are stored in the binding rather than inferred from graph distance.

## 7. Storage and container topology

### Canonical workspace files

```text
domains/brand/visual-reference-types/
  registry.yaml
  color.palette.schema.yaml
  typography.role.schema.yaml
  ...

workspaces/<brand>/visual-language/
  profiles.yaml
  profile-revisions/
  scope-bindings.yaml
  references/
  assets/
  derivations/
  compiled/
    current-public-visual-language.yaml
```

`compiled/` is generated and rebuilt from the immutable source records. It must never be edited manually.

### Cognee topology

Create one visual-language child container per Brand workspace, not one container per profile or audience:

```text
world://workspace/brand/<brand>
  └── world://workspace/brand/<brand>/visual-language
```

The child contains profile manifests, revision metadata, scope bindings, reference text, and content-addressed asset metadata. Binary assets stay in repository or object storage and are referenced by URI and hash.

All records retain the existing metadata contract plus visual-language fields for `reference_kind`, `profile_id`, `revision_id`, scope selectors, authority, rights, and time.

## 8. Retrieval route

Add a dedicated `visual-language` route.

1. Resolve applicable profile revisions deterministically from structured metadata.
2. Fetch exact profile, binding, and reference IDs.
3. Use BM25 within the visual-language child only for exploratory reference requests.
4. Use bounded hybrid retrieval in the same child only after an in-domain lexical no-hit.
5. Use graph traversal only when the user explicitly asks for lineage, relationships, or historical evolution; limit to two hops.
6. Never use semantic similarity to decide which version governs an artifact.

The intelligence model interprets the resolved references after retrieval. It does not choose the governing version.

## 9. Context packet extension

Extend `ContextRequest` with optional structured selectors:

- `productId`;
- `campaignId`;
- `offerId`;
- `audienceSegmentIds`;
- `visualLanguageProfileId`;
- `visualLanguageRevisionId`.

Add a `visualLanguage` section to `ContextPacket`:

```text
resolution status
selected profile revisions
scope bindings and precedence
actionable tokens and principles
reference assets and thumbnails
required and prohibited usage
authority and rights
conflicts, omissions, and clarification questions
citations
resolution receipt
```

For `brief`, return high-level expression direction and known gaps. For `concept`, return relevant references and creative boundaries. For `production`, return only machine-actionable specifications with sufficient authority, while labeling observed or proposal-only material. For `review`, return the exact version against which the artifact should be checked.

## 10. Implementation work packages

### WP1 — Architecture decision and schemas

- Record the source-of-truth, versioning, scope, and resolution decisions in an ADR.
- Add provider-neutral Pydantic models for references, profiles, revisions, bindings, asset references, rights, and compiled packets.
- Add the extensible reference-kind registry and initial payload schemas.
- Add `scoped_to`, `supersedes`, `corrects`, and `references` relationship definitions only where they express world meaning; keep storage lineage out of the ontology when it is merely implementation metadata.

### WP2 — Validation and authoring

- Validate IDs, hashes, time intervals, revision lineage, expected revisions, source anchors, rights metadata, and registered payload schemas.
- Reject in-place mutation, overlapping contradictory bindings without precedence, missing source URLs, and unresolved asset hashes.
- Provide a scaffold command for adding a profile, revision, reference module, or binding.

### WP3 — Nike visual-language pack

- Create the visual-language directory and resource-registry entries.
- Populate only evidence-backed public references initially.
- Keep colors, typography, and other unknown internal rules as explicit gaps until researched or supplied by an authorized source.
- Create at least one global public-observation profile and one Nike Membership digital overlay to validate composition.

### WP4 — Cognee projection

- Add an idempotent visual-language projection builder.
- Create and populate the visual-language child container.
- Preserve exact IDs, scope metadata, source anchors, hashes, authority, rights, and all time fields.
- Rebuild projections when source hashes, schemas, bindings, or profile revisions change.

### WP5 — Deterministic resolver

- Implement profile resolution as a provider-neutral package.
- Support current and historical `validTime` queries.
- Implement explicit precedence and `replace`/`extend`/`disable` composition.
- Return `ready`, `partial`, `needs_clarification`, or `no_hit` without model involvement.

### WP6 — Context intelligence integration

- Add structured visual scope fields to the request contract.
- Call the resolver before lexical retrieval for `concept`, `production`, and `review` workflows.
- Fetch exact resolved references from Cognee.
- Compile a bounded visual-language packet for the separate intelligence model.
- Record selected, retrieved, used, and excluded profile/reference revisions in the trace.

### WP7 — DeepSeek Harness plugin integration

- Include the visual-language packet in automatic context injection.
- Add `inspect_visual_language_resolution` and historical inspection support.
- Preserve the existing separation between the intelligence model and main agent.
- Never send binary media as unbounded prompt content; provide selected thumbnails or asset URIs according to rights and token budget.

### WP8 — Provenance continuity

- Produce an optional artifact-side provenance manifest.
- Map generated claims, tokens, components, and creative inferences back to profile revisions and reference IDs.
- Preserve the exact visual-language version used so a later review can replay the same context.

### WP9 — Certification and operations

- Add exact-profile, current-time, historical-time, audience-overlay, campaign-overlay, conflicting-overlay, unknown-kind, prohibited-rights, adversarial, and no-hit probes.
- Add refresh and drift triggers.
- Certify before enabling automatic production-stage injection.

## 11. Quality gates

Release requires:

- 100% profile revision lineage replay;
- 100% evidence and asset-hash resolution;
- no silent in-place history changes;
- no version selected through embedding similarity;
- no cross-brand or incompatible-scope leakage;
- deterministic resolution for identical inputs;
- conflict detection for equally authoritative incompatible overlays;
- correct time-travel results before, during, and after a revision interval;
- unknown reference kinds preserved without being treated as actionable;
- rights-prohibited assets excluded from generation packets;
- top-1 precision at least 0.90;
- routing error at most 0.03;
- adversarial and out-of-domain `NO_HITS` correctness of 1.0;
- trace coverage for selected, retrieved, used, excluded, and governing versions.

## 12. Migration and rollout

1. Introduce schemas and resolver behind a disabled feature flag.
2. Represent the existing seven Nike Expression entities as legacy references without changing their meaning.
3. Populate a small public-observation pilot for global Nike and Nike Membership.
4. Run certification and compare context packets with the current system.
5. Enable visual-language context for `concept` only.
6. Enable `production` after authority and rights filtering passes.
7. Enable `review` with exact-version replay and provenance-manifest checks.
8. Keep the existing asset-context route as fallback during migration.

## 13. Initial end-to-end acceptance scenario

Given:

- Brand: Nike;
- offer: Nike Membership;
- audience: prospective Nike Members;
- channel: nike.com;
- geography: global;
- valid time: 2026-08-25;
- workflow: concept;

the resolver must return:

- the applicable global base revision;
- the Nike Membership overlay revision;
- any audience and web-channel overlays that exist;
- exact reference revisions and evidence;
- explicit gaps for missing typography, palette, and proprietary rules;
- no football, women-athlete, youth-campaign, or historical language unless explicitly compatible;
- a reproducible resolution receipt.

The generated artifact must then preserve a provenance manifest showing which retrieved modules influenced it and which choices were independent creative inference.

## 14. Reasoning contracts

This design is governed by:

- `world://operator/guardrail/ontology-conflation@1`;
- `world://operator/guardrail/version-state-conflation@1`;
- `world://operator/guardrail/retrieval-reasoning-conflation@1`.

Required evaluator outcomes are typed consistency, replayable lineage, deterministic resolution, complete citation resolution, and bounded retrieval.
