# Biotic Progressive World Atlas

Date: 2026-09-14  
Status: implemented local read-only view  
Surface: `surface:brand-lab`

## Purpose

The atlas is a visual and computational projection of the Biotic brand world. It is not a second ontology and does not curate a smaller, presentation-only subset. Its job is to let a person or an agent begin with a legible model of the whole world, move through explicit semantic boundaries, and descend to exact records, relations, and evidence without losing orientation.

The representation must support two distinct uses:

1. Human inspection: understand what exists, how it is organized, and why a record is trustworthy.
2. Agent traversal: identify the smallest relevant region of the world before loading detailed context for a task such as newsletter creation.

## Representation contract

The atlas is derived at runtime from canonical Brand Lab inputs. It never contains hand-authored substitutes for ontology records or relations. Every projected node retains its source file and source field where available. Every projected edge retains its original relation type.

Completeness is evaluated as a graph invariant:

- every canonical root entity and relationship is present;
- every node and edge in the audience, copy/claims, and visual-language graphs is present;
- all serialized world-model records are present;
- evidence notes and source records are addressable;
- product knowledge, content-strategy types and relations, the newsletter agent charter, its workflow steps, and its evaluation rubric are present;
- every relationship endpoint resolves to a projected record.

This is an exhaustive projection of the currently serialized system, not a claim that the real brand world is complete.

## Progressive depths

The same graph is exposed through five depths rather than five separate diagrams:

| Depth | Question answered | Visual form |
| --- | --- | --- |
| 00 World | What regions make up this world? | Central brand nucleus and eight boundary orbits |
| 01 Domains | How is one region internally layered? | Exploded translucent semantic planes |
| 02 All records | What exactly exists here? | Searchable, ordered record registry |
| 03 Relations | What directly affects this record? | Selected record with all incoming and outgoing edges |
| 04 Evidence | Why should this record be trusted? | Record-to-source-to-evidence trace with limitations |

Depth changes preserve the selected boundary and record wherever possible. Search crosses the complete payload, then reveals its result in the exact-record layer. This makes disclosure a navigation policy, not data removal.

## Semantic boundaries

The atlas uses eight stable boundaries, ordered from public brand meaning toward internal operational machinery:

1. Public core — identity, positioning, values, pillars, personality, purpose, and public-facing relations.
2. World model — state, perspective, temporal, conflict, hypothesis, experiment, outcome, and learning records.
3. Product library — product knowledge, SKU variants, purpose, and end-user connections.
4. Audience — audience structures and their declared relationships.
5. Copy and claims — language, claim, and substantiation structures.
6. Visual language — visual system records, references, profiles, revisions, and bindings.
7. Content strategy — internal semantic types, relations, workflow steps, and evaluation dimensions.
8. Evidence — evidence notes, source records, and provenance relations.

The public research world and the internal strategy system remain visibly separate. Cross-boundary edges are shown, but their endpoints do not collapse into a shared semantic type.

## Visual reasoning

The active Testflight experience-design contract supplies the structural rules: evidence before decoration, calm density, spatial thought, visible state, humane precision, and expression within structure. The shared token stylesheet is loaded directly by Brand Lab.

The Biotic atlas introduces scoped expression drawn from the approved moodboard study:

- pale sage as the navigable world field;
- exact grid and registration marks for scientific orientation;
- translucent stacked planes for semantic depth;
- restrained blush and violet accents to distinguish layers without turning the graph into a rainbow taxonomy;
- editorial display typography paired with monospace metadata;
- bounded motion only for hover, selection, and depth transitions.

These are presentation exceptions for `surface:brand-lab`; they do not redefine the shared token package.

## Data flow

```text
canonical YAML and Markdown
        -> Brand Lab loader and validation
        -> exhaustive atlas projection
        -> boundary/depth query in the browser
        -> selected record, relations, evidence, and source locus
```

The server performs normalization and completeness accounting. The browser performs only disclosure, filtering, layout, and selection. This prevents visual state from becoming an alternative source of truth.

## Failure and uncertainty states

- A relationship with a missing endpoint is counted as dangling and surfaced by coverage checks.
- Records without direct evidence say so; absence is not silently repaired.
- Limitations remain attached to evidence traces.
- Empty search and empty-boundary states are explicit.
- Internal workflow or strategy nodes are labeled by boundary so they cannot be mistaken for customer or public brand evidence.

## Verification

The implementation includes a fixture-backed exhaustive coverage test for Biotic. It compares source identifiers against the atlas projection, checks all supplemental graphs, confirms the operational modules, asserts stable boundary order, and requires zero dangling relations.
