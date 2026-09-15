# Brand World ontology v3 candidate

This directory defines the shared, brand-neutral Brand World module vocabulary. It is a candidate
until the migration gates in the v3 design are satisfied. Concrete Brand facts never belong here.

Start with `manifest.yaml`, then load only the module that owns the concept being modeled. The
`projections/eight-systems.yaml` file is a rebuildable navigation view; Identity, Expression,
Offering, Experience, Perception, Governance, Environment, and Event are not canonical record
kinds.

`vocabulary.yaml` records the naming boundary between the constitutional World grammar, the Brand
modules, agent/work objects, and human navigation projections. It is a registry for interpretation
and validation, not a generic record schema.

The active candidate rules are:

- an Entity is a referent, not a statement;
- a Claim is a proposition and retains its epistemic kind after approval;
- a State is time- and context-bounded;
- an Event is an occurrence, not a subject-area container;
- a Relation uses named participant roles;
- a Source can be revisited and Evidence identifies a bounded locus within it;
- a Decision records an authorized choice without proving its rationale;
- projections and context packets are reproducible views and never canonical writes.
