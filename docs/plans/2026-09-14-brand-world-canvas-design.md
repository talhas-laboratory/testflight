# Brand World Canvas

Date: 2026-09-14  
Status: implementation proposal  
Surface: `surface:brand-world-canvas`  
Initial workspace: `world://workspace/brand/hellobiotic-research`

## Outcome

Build a standalone, read-only application for understanding a Brand as an ontological world. The
first view must expose the eight canonical Brand systems—Identity, Expression, Offering,
Experience, Perception, Governance, Environment, and Event—rather than repository containers or
operational modules. Selecting a system reveals its internal records and cross-system relations.
Selecting a record opens its complete meaning, provenance, evidence, and direct relations in a
floating specimen card so the graph remains legible.

The application is separate from Brand Lab. Brand Lab remains an analytical workspace inspector;
Brand World Canvas is the semantic navigation surface.

## Approaches considered

### A. Deterministic SVG graph with a small Python server — selected

Use native SVG, CSS, and JavaScript for the client and a dependency-light Python HTTP server for a
canonical, read-only JSON projection. SVG preserves sharp labels and accessible node groups. A
stable radial layout gives users a persistent mental map and supports semantic zoom without the
visual jitter of a force simulation. The server can load YAML/JSON directly and serve the shared
design tokens without a frontend build step.

### B. Canvas/WebGL force graph

This would scale to thousands of nodes and support continuous physics, but it would make text,
keyboard access, deterministic screenshots, and deliberate editorial composition harder. The
current Biotic graph does not require this scale.

### C. React plus Cytoscape or Sigma

This provides mature graph primitives but introduces a new JavaScript toolchain and upstream
dependency for behavior that is small enough to implement locally. It remains a future option if
the graph grows beyond the SVG performance envelope.

## Architecture

```text
canonical ontology definitions + Brand workspace records
                         ↓
presentation-only semantic projection
  system assignment · evidence joining · relation normalization
                         ↓
               GET /api/world
                         ↓
standalone SVG application
  world map → system focus → record focus → specimen card
```

The projection is an adapter, not a new ontology. It does not modify IDs, statuses, sources, or
epistemic meaning. Supplemental graph vocabularies are assigned to one of the eight systems only
for navigation; each assignment records the rule that produced it. Evidence and operational
support records remain available through detail views but never replace the first-order Brand
anatomy.

## Interaction model

### World state

Biotic is the central identity. Eight system nodes form a stable ring in ontology order. Curved
hairline connections summarize canonical cross-system relations. Counts describe records assigned
to a system, not an invented measure of importance.

### System focus

Selecting a system expands its records around a central system plate. Directly related records from
other systems appear as smaller boundary portals. Only local relationships are drawn. A breadcrumb
returns to the whole Brand without losing the meaning of the selected record.

### Record focus

Selecting any record highlights only its direct incoming and outgoing relations. Relation names
appear on these active lines. The specimen card presents summary, status, semantic type, source
locus, evidence, limitations, and a readable incoming/outgoing relation list. Tabs prevent the card
from becoming a long permanent inspector.

### Canvas behavior

Pointer drag pans; wheel input zooms around the cursor; labeled buttons support zoom and reset;
keyboard users can focus and activate every node. Empty canvas selection closes the specimen card.
Reduced-motion mode removes interpolated transitions.

## Visual language

The direction is **a living semantic specimen under scientific registration**.

The supplied references contribute:

- translucent mounted plates and concentrated pink axes for the floating detail card;
- exploded biological strata and dotted registration lines for depth and subsystem reveal;
- stable analytic coordinates, sparse labels, and soft local color concentrations for graph
  legibility;
- pale green continuous ground, black technical annotation, and a large organic silhouette for the
  overall field;
- thin lavender/red study marks and repeated numbered notation for hierarchy;
- hierarchical networks as a warning: dense relationships may exist in the data, but only local
  relations are rendered at once.

The active Testflight tokens provide typography roles, focus color, state colors, spacing, and
motion. Scoped surface exceptions are pale mineral green, translucent blush and violet plates,
registration-grid geometry, and square mounted cards. They are presentation values for this
surface only.

## Semantic projection rules

- Canonical root entities retain their declared v1 type.
- Audience observations and hypotheses primarily enter Environment; testimonial and self-reported
  signals enter Perception.
- Voice, message, phrase, typography, palette, imagery, and graphic-device records enter
  Expression.
- Product, SKU, product-form, attribute, benefit, and claim-boundary records enter Offering.
- Touchpoint and practice records enter Experience.
- Perspective records enter Perception; state records follow their primary subject; relationship
  frames enter Experience; branches and events enter Event.
- Workflow, rubric, and source machinery are supporting records. They are discoverable from detail
  cards and counts but do not become first-ring systems.
- Unknown supplemental types remain visible as held projection assignments instead of being
  dropped.

## Failure states

- Loading: the canvas shows a quiet registration field and a textual loading state.
- Invalid payload: the application presents a visible error and no synthetic graph.
- Empty system: the selected system remains visible with a source-grounded empty-state message.
- Missing evidence: the card states that no direct evidence is recorded.
- Unknown projection: the record remains discoverable and identifies the fallback assignment.
- Dangling relation: the server reports it in projection diagnostics and does not invent an
  endpoint.

## Verification

- Projection tests require all eight systems in canonical order.
- Every root Brand entity and relationship must be represented.
- Every rendered relation endpoint must resolve.
- Supplemental audience, copy/claims, and visual-language records must remain discoverable.
- Browser checks cover initial world anatomy, system drill-down, record card, tab switching,
  pan/zoom controls, keyboard activation, responsive layout, and console errors.

## Derivation

Design sources: six user-supplied references, the approved Brand World moodboard study, and
`testflight-design-language@0.1.0`. The references are interpreted as compositional guidance; no
image is copied into the application. This proposal does not change the canonical Brand ontology.
