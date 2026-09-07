# System Map

## End-to-end module flow

```text
[1 Intake surfaces]
        |
        v
[2 Evidence and Content substrate]
        |
        v
[3 Elicitation, extraction, identity and mapping operators]
        |
        v
[4 Review, promotion and ontology-gap governance]
        |
        v
[5 Canonical Brand World + append-oriented persistence]
        |
        v
[6 Applicability and version resolver]
        |
        v
[7 Artifact context compiler] <--- [Creative Field projection]
        |
        v
[8 Artifact profile + creation operator]
        |
        v
[9 Artifact evaluator + review/versioning]
        |
        v
[10 Renderer] -> [11 Delivery adapter]
                         |
                         v
                 [12 Outcomes and learning]
                         |
                         +---- reviewable proposal ----> [5]
```

## Module inventory

| Module | What it solves | Current status | Primary implementation home |
| --- | --- | --- | --- |
| Intake surfaces | Cold start and tacit employee knowledge | New | `apps/brand-intake/` |
| Evidence capture | Preserves source, speaker, time, rights, and raw wording | Strong base | `testflight-content`, `testflight-semantic`, SQLite/blob adapters |
| Elicitation operators | Finds important gaps and asks focused follow-ups | New | reasoning contracts + operator runtime |
| Extraction and identity | Produces grounded claim/entity proposals without noun-phrase explosion | Partial base | semantic kernel + new ingestion workflows |
| World mapping | Maps local concepts into Brand types without forced ontology changes | Partial base | `testflight-brand` + new mapping registry |
| Review and promotion | Prevents model proposals becoming accepted knowledge | Existing pattern | Creative Field lifecycle; generalize for World intake |
| Ontology-gap governance | Keeps customer vocabulary while controlling shared ontology evolution | New | Brand domain registry and certification workflow |
| Canonical Brand World | Stores accepted entities, states, frames, branches, decisions, and learning | Implemented base | `testflight-semantic`, `testflight-brand` |
| Applicability resolver | Selects correct product, audience, campaign, locale, time, and branch | Partial | World-view compiler and context intelligence |
| Creative Field | Supplies reviewed creative principles, tensions, and exclusions | Implemented vertical slice | `testflight-creative-field` |
| Artifact profiles | Defines required fields, rules, evaluators, and formats | New | `testflight-artifacts` + marketing profile registry |
| Artifact context compiler | Maps exact World revisions into artifact slots | New/extension | artifact package composed with context intelligence |
| Artifact composer | Creates a typed provider-neutral artifact proposal | New | artifact operators executed by operator runtime |
| Artifact evaluation | Checks evidence, semantics, brand, channel, and format fitness | Partial creative base | artifact evaluators + Creative Field evaluator |
| Artifact review/versioning | Produces immutable approved artifact versions | New/generalized | `testflight-artifacts` |
| Renderers | Creates PDF, DOCX, HTML, images, slides, or video packages | New | renderer adapters |
| Delivery adapters | Sends approved outputs to external systems | New | upstream-specific adapters |
| Outcome ingestion | Connects artifacts to measurements and observed results | Semantic base only | analytics adapters + semantic learning records |
| Product application | Makes the whole workflow usable by non-technical teams | Partial UI base | future Campaign Studio |

## Boundary contracts

Every connection must have a typed handoff:

| From | To | Required handoff |
| --- | --- | --- |
| Intake | Evidence | `IntakeSession`, source envelope, speaker turns, attachments, rights |
| Evidence | Extraction | bounded source spans and permitted operator context |
| Extraction | Review | entity, assertion, state, frame, and mapping proposals with derivations |
| Review | World | authority-bearing acceptance/rejection decision |
| World | Resolver | structured selectors, effective time, recorded-time cutoff, branch, permissions |
| Resolver | Artifact compiler | `ResolvedWorldView` plus exact revision manifest and conflicts |
| Artifact compiler | Composer | immutable `ArtifactContextManifest` and profile revision |
| Composer | Evaluator | typed `ArtifactProposal` with slot-level provenance |
| Review | Renderer | immutable accepted `ArtifactVersion` |
| Renderer | Delivery | rendered output, provider manifest, disclosure and authorization |
| Delivery | Outcome | publication receipt and stable artifact/placement identity |
| Outcome | World | evidence-bearing learning proposal, never automatic truth mutation |

## Current architectural fit

The proposition extends the existing architecture rather than replacing it. The semantic kernel,
Brand domain, Content contracts, context intelligence, Creative Field, operator runtime,
append-oriented persistence, target packet, and evaluation patterns are reusable. The missing
center is a general Artifact domain and an intake-to-World workflow.

The main current limitation is that `WorldViewRequest` resolves an exact `context_id`, branch, and
record set, but does not yet carry enough structured applicability selectors or freeze the exact
effective revision of each selected product, audience, campaign, policy, season, and language
record. Artifact production must close that gap before broad generation is trusted.

