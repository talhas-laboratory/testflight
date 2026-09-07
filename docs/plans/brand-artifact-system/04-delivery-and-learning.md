# Rendering, Delivery, Outcomes, and Learning

## Problem solved

Customers need usable files and deployed marketing, not only semantic records. The system must
translate approved artifact versions into external representations without allowing provider
formats to become canonical meaning or external actions to bypass authorization.

## Renderer boundary

A renderer consumes an immutable artifact version plus a render profile and emits a
`RenderedArtifact`. It may apply typography, layout, responsive rules, image composition, or file
serialization, but cannot add a new strategic claim or silently repair missing content.

Examples:

- campaign brief to Markdown, PDF, DOCX, or Google Docs;
- newsletter to responsive HTML and plain text;
- message matrix to spreadsheet or presentation;
- social pack to image/caption bundles and platform sizes;
- landing page to a provider-neutral page model and HTML preview.

Renderer outputs record input artifact version, render-profile version, adapter version, asset
hashes, limitations, omissions, and a receipt. Rendered output receives technical and visual QA;
semantic approval remains tied to the canonical artifact version.

## Delivery adapter boundary

A delivery adapter performs an explicitly authorized external action. Platform-specific SDKs,
authentication, IDs, retries, rate limits, and payload rules remain inside the adapter.

Examples include Google Drive, HubSpot, Mailchimp, a CMS, Figma, Canva, Adobe, social schedulers,
and advertising platforms. Delivery requires:

- accepted artifact and render versions;
- target capability manifest;
- permission and disclosure manifest;
- authority grant and idempotency key;
- dry-run or preview support where the target permits it.

The adapter returns a publication receipt containing target identity, external IDs, timestamps,
payload/content hashes, status, limitations, and retry information. Visibility or successful
authentication is not permission to publish.

## Outcome ingestion

Outcome adapters import measurements while preserving platform, placement, campaign, artifact,
variant, audience, time window, metric definition, attribution method, and data limitations.

Identity resolution is mandatory: a platform creative ID must map to a publication receipt and
canonical artifact version. Unresolved IDs remain unlinked measurements instead of being attached
to the nearest campaign by similarity.

## Controlled learning

```text
Measurement
  -> ObservedOutcome
  -> comparison under declared method
  -> LearningProposal
  -> human or policy review
  -> accepted LearningUpdate
  -> input to a later decision/context
```

An outcome may support or weaken a scoped hypothesis. It does not prove that the artifact caused
the result unless an experiment and attribution policy justify that conclusion. Learning remains
bounded to product, audience, market, channel, season, campaign, and time.

Accepted learning never rewrites historical artifacts. It may mark dependent active guidance for
review and become an input to a future artifact request.

## Value telemetry

The product should measure its own operational value separately from campaign-performance claims:

- time from request to approved artifact;
- number and duration of review cycles;
- repeated questions and missing-context holds;
- evidence coverage for material claims;
- context acceptance and correction rate;
- stale or conflicting knowledge caught before delivery;
- reuse of approved artifact versions and modules;
- manual production and agency effort avoided.

This telemetry supports pricing and product improvement without overclaiming revenue causality.

## Failure and recovery

- Renderer capability gap: return partial or hold with the unsupported requirement.
- Delivery failure: retain approved/rendered artifacts and retry idempotently.
- External edit: import as a new representation or revision proposal; do not rewrite canonical data.
- Missing placement identity: preserve measurement but hold attribution.
- Metric-definition change: version the definition and avoid invalid comparisons.
- Provider outage: canonical records and local outputs remain available.

