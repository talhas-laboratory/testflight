# Fundamental content strategy

## Mission

Model the relational field between people, self, brand, product, and shared domains of
engagement so Biotic can create useful, interesting, evidence-aware newsletter content.

## Scope

This child is bounded to `world://workspace/brand/hellobiotic-research/content-strategy`.
It contains founder-directed strategy and explicit hypotheses, not public customer evidence or
accepted medical claims.

Use it for:

- the fundamental theory of relational content relevance;
- the Biotic newsletter's editorial promise and content territories;
- the proposed person–self–field–brand–product relation model;
- the newsletter agent's generation and evaluation contract.

Do not use it as evidence that an audience actually holds a belief, that a topic will perform, or
that an ingredient or hygiene practice produces a health outcome.

## Retrieval

Use exact lookup or BM25 first inside this child. Use bounded same-child hybrid retrieval only
after an in-domain lexical no-hit. Use graph traversal only for explicit path questions with at
most two hops. Return `NO_HITS` for unsupported or out-of-domain requests.

## Navigation

- `AGENT_CONFIG.yaml`: retrieval and quality policy.
- `WORKSPACE.yaml`: identity and parent topology.
- `artifacts/founder-brief-2026-09-08.md`: source-authorized strategic intent.
- `artifacts/fundamental-content-strategy.md`: evolving human-readable manifest.
- `artifacts/relational-content-model.yaml`: proposed machine-readable model of the field.
- `artifacts/newsletter-agent-charter.yaml`: generation, safety, and evaluation contract.
- `workflows/biotic/newsletter-compose.yaml`: registered proposal-only workflow that returns a
  content plan, draft, and review package; it cannot send or publish.
- `artifacts/evaluation-rubric.yaml`: independent editorial quality dimensions and gates.
- `artifacts/registration-receipt.yaml`: boundary, operator, and validation results.
- `resource_registry.json`: source metadata and provenance.
- `certification_cases/probes.yaml`: retrieval certification cases.

## Agent route

Compile context in this order: current manifest revision → relational model → agent charter →
audience evidence explicitly bridged from an authorized source → topic evidence. Never infer an
individual subscriber profile from a segment label. Return `ask`, `partial`, or `NO_HITS` when the
reader composition or evidence is insufficient.

The executable scaffold follows that route through `compile_relational_context`, `compose_issue`,
`form_content_plan`, `draft_newsletter`, `evaluate_issue`, and `prepare_review_package`. It is
proposal-only. A future publishing workflow needs a distinct explicit authority grant and a
durable human-approval interrupt; it must not be added to this workflow.
