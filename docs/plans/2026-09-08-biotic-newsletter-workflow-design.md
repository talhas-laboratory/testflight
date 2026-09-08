# Biotic newsletter workflow — initial design

## Decision

Implement the newsletter agent as a fixed, proposal-only workflow. It compiles bounded
relational context, forms an issue composition, produces a writer-facing content plan, drafts,
evaluates, and returns a review package. It does not publish, send, or mutate canonical brand
knowledge.

## Why this shape

The issue is a composition of field, reader stake, contribution, moment, Biotic's bounded
legitimacy, evidence, optional product role, and expression. The workflow keeps the
ontology-facing reasoning record separate from the writer-facing `content_plan` so a copywriting
node receives clear constraints without treating founder strategy as customer or scientific fact.

The portable workflow definition owns access, knowledge envelope, authority, node contracts,
prompts, and outputs. `adapters/langgraph` owns `StateGraph` compilation. The runtime owns the
model-provider route. That preserves provider neutrality and makes each small-model decision
inspectable.

## Node topology and handoffs

```text
compile_relational_context
  -> compose_issue
  -> form_content_plan
  -> draft_newsletter
  -> evaluate_issue
  -> prepare_review_package
```

`compile_relational_context` is deterministic. It determines whether personalization can be
contextual, audience-level, or broad only; it also assigns stable evidence IDs and records the
invariants every later node must preserve.

`compose_issue` is a planner rather than a topic picker: it considers a small portfolio of
materially different field–stake–contribution compositions, scores them against the relational
model, selects one, and records residual uncertainty. `form_content_plan` then locks meaning
(reader promise, contribution, claim and CTA boundaries, product role) while keeping craft
directional or open. `draft_newsletter` can be creative inside that envelope but carries the
same `composition_id` and records every factual claim it uses. `evaluate_issue` independently
scores the visible draft and returns a concrete repair brief when it cannot clear review.

`compile_generation_packet` is a deterministic boundary between planning and writing. It gives a
blank creative agent a binding `constraints` object plus a readable `creative_brief`; it never
passes a prior draft or review into generation. `prepare_review_package` is deterministic: it rejects composition drift, product-role escalation,
failed hard gates, and claim-lineage drift before returning `review_required`.

## State and control

The workflow is a predetermined editorial process, so normal edges are sufficient in v1. Each
node writes one named output into LangGraph state. There is no unbounded agent loop and no hidden
tool autonomy. Retries apply only to transient or timeout failures; semantic, evidence, and
editorial failures return typed `hold` outcomes.

The present workflow has no irreversible action. A later, distinct publication workflow must use
a LangGraph `interrupt()` at its approval node, a durable checkpointer, and a caller-provided
`thread_id`; it may resume only with an explicit human decision. No send action belongs in this
workflow or in its authority envelope.

## Evidence and relational boundaries

- Founder-directed content strategy is an editorial constraint, not customer evidence.
- Audience context is accepted only with a stated source status; a segment never becomes an
  individual's identity, health state, insecurity, or motive.
- Each factual claim must retain a claim ID, evidence ID, source reference, allowed expression,
  and limitations; the draft and evaluation may only reuse those IDs.
- A product is optional and may be `none`, `contextual`, `illustrative`, or `practical`; it cannot
  become the issue topic merely through adjacency.
- Publication status stays `proposal_only` through every node.

## Verification

The workflow definition is schema-validated and covered by a runtime test with a fake structured
model. The test asserts that relational context, claim limitations, a content plan, draft, and
evaluation reach the review package, and that the final output cannot represent a send or a
canonical write. It also asserts that a draft using an unplanned or untraced evidence ID is held
before review. The golden node pack captures the planner's semantic and governance expectations;
it does not pretend to measure live-model editorial quality.
