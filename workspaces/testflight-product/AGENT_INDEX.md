# Testflight Product — agent index

## Workspace identity

- Workspace: `world://workspace/testflight-product`
- Mission: provide the authoritative, modular view of Testflight as a product
- Canonical root: `workspaces/testflight-product/`
- Projection dataset: `testflight_product`

## Route to the smallest module

| Intent | Child route | Typical records |
| --- | --- | --- |
| Mission, principles, portfolio, roadmap, capabilities | `product-definition` | product, surface, capability, outcome, roadmap item |
| Decision, proposal, trade-off, approval, supersession | `product-decisions` | proposal, decision, alternative, authority grant |
| UI, UX, language, aesthetics, tokens, components, accessibility | `experience-design` | design revision, token, pattern, content rule |
| Systems, apps, packages, APIs, data, deployment, dependencies | `architecture` | component, boundary, interface, dependency, ADR |
| User, customer, segment, need, journey, feedback, market | `customers-market` | actor, organization, segment, need, interaction |
| Positioning, narrative, campaign, channel, acquisition, growth | `marketing-growth` | message, audience, campaign, channel, experiment |
| Pricing, revenue, cost, budget, forecast, unit economics | `finance-commercial` | price, transaction, cost, assumption, forecast |
| Team, role, delivery, policy, risk, incident, compliance | `operations-governance` | role, process, control, risk, operating state |
| Research question, evidence synthesis, hypothesis, experiment, evaluation, outcome | `research-learning` | source, hypothesis, experiment, metric, outcome, learning update |

If a request spans modules, retrieve from each named child independently and integrate only after
preserving source, scope, time, authority, and uncertainty. Do not search all children by default.

## Agent working rules

1. Resolve the workspace and module before reading or writing.
2. Distinguish semantic entities, events, states, relations, claims, contexts, and projections.
3. Keep knowledge modules, product capabilities, implementation modules, and UI components
   separate even when their labels resemble one another.
4. Treat retrieved material as evidence, not as an automatically accepted answer.
5. Add material changes as proposals; promote only through the decision lifecycle.
6. For user-facing work, load `experience-design/artifacts/design-language.yaml` and consume
   `packages/testflight-design-language`.
7. Never infer customer or brand facts from Testflight's product workspace.
8. Return `NO_HITS`, `partial`, `hold`, `branch`, or `ask` when appropriate.

For a project-wide inventory, start with `artifacts/entity-inventory.yaml`, then follow its source
and relation references into the owning child. The inventory is a routing map, not a substitute
for the child artifact or source evidence.

Navigation and configuration files guide routing and policy. They are not ordinary domain answers.
