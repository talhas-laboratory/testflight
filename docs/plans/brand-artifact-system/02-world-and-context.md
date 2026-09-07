# World and Context Resolution

## Problem solved

Artifact generation fails when the system uses the right entity with the wrong definition, time,
market, audience, campaign, policy, or authority. The World must preserve stable identity while the
context resolver selects exact effective revisions for one request.

## Identity, state, revision, branch, and context

Use these concepts differently:

| Concept | Meaning | Example |
| --- | --- | --- |
| Entity identity | Persistent referent | `offering:nike-app` |
| Definition/state revision | What was applicable or believed at a time | Nike App product definition revision 3 |
| Context | Conditions under which knowledge applies | Germany, first-time runners, winter 2026 |
| Branch | Concurrent alternative interpretation or scenario | confidence-first versus performance-first positioning |
| Relationship frame | Qualified situation binding several roles | campaign + offering + audience + channel + objective |
| Artifact snapshot | Exact resolved inputs frozen for reproduction | revision manifest used by newsletter 42 |

Do not create a new Product entity every time positioning changes. Create a new product-definition
or state revision. Create a new entity only when the referent or segmentation identity materially
changes. Do not represent winter as a product revision; treat it as a time/occasion selector,
campaign, or contextual state.

## Structured artifact request

The resolver should extend the current request with:

- workspace and Brand identity;
- artifact profile and workflow stage;
- campaign or relationship-frame ID;
- product/offering, audience, market, locale, channel, occasion, and geography selectors;
- effective time and optional recorded-time cutoff;
- branch and perspectives;
- permissions, evidence classes, disclosure policy, and record budget;
- optional explicit overrides with authority and expiry.

The preferred entry point is a campaign or task `RelationshipFrame`. Its named roles bind offering,
audience, campaign, objective, market, channel, owner, approval, and constraints. Explicit request
selectors may narrow the frame but must not silently contradict it.

## Deterministic applicability resolution

1. Validate workspace and permissions.
2. Resolve stable identities and campaign-frame roles.
3. Resolve branch ancestry and explicit deltas.
4. Filter candidate revisions by valid time and recorded-time cutoff.
5. Reject candidates with conflicting selectors.
6. Rank by explicit precedence, scope specificity, authority, and revision policy.
7. Compose compatible base and overlays using declared replace/extend/disable behavior.
8. Preserve equally applicable conflicts and missing required roles.
9. Resolve Creative Field and verbal/visual language revisions separately.
10. Return a structured view and applicability receipt before model synthesis.

The reusable default overlay order is:

```text
Brand base
  -> product or offering
  -> campaign
  -> audience
  -> channel
  -> geography, locale, season, and occasion
```

Explicit priority and per-module merge rules override this default. Semantic similarity must never
select a governing version.

## `ArtifactContextManifest`

The artifact compiler converts the resolved World view into an immutable manifest containing:

- artifact request and profile revision;
- selected entity identities and exact state/definition revision IDs;
- relationship-frame, branch, context, language, and Creative Field revisions;
- slot-to-record mappings;
- material claims and evidence references;
- decisions, authority, constraints, rights, and permissions;
- unresolved conflicts, assumptions, omissions, and held requirements;
- valid/recorded time, expiry, policy/ontology versions, and derivation receipt.

The manifest is a disposable projection, not canonical truth, but it must be persisted with the
artifact proposal so the result can be replayed exactly.

## Dependency invalidation

Every proposal and accepted artifact version records dependencies on exact revisions. When a
source is corrected, a claim is retracted, a product definition changes, or a policy expires, the
system marks affected context manifests and artifacts `potentially_stale`. It does not rewrite or
regenerate them automatically.

A reviewer may keep the existing version, re-resolve context and create a new artifact version, or
branch the artifact when both old and new interpretations remain valid.

## Current code to extend

- `testflight-semantic`: strengthen version lineage, bitemporal metadata, and dependency impact.
- `WorldViewRequest` / `ResolvedWorldView`: add structured selectors and exact revision manifest.
- `testflight-context-intelligence`: compile the selected records, not choose governing versions.
- visual-language resolver: reuse its deterministic scope/precedence pattern.
- Creative Field binding/projection: supply creative context without becoming the whole artifact.

