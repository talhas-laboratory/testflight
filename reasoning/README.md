# Reasoning operators

This directory contains portable, inspectable guardrail operators for the
reasoning mistakes identified while designing Testflight's semantic/entity
environment. They are derived from the Mindspace portable operator contract;
they are not a personality model and they do not reproduce private
chain-of-thought.

An operator is a semantic contract, not a prompt fragment. It declares what
context it needs, what transformation or check it performs, what it returns,
which distinctions it must preserve, when it must hold, and how its result is
evaluated. An implementation may be deterministic, model-backed, human,
or composite. The contract stays stable when the implementation changes.

## How an agent uses the catalog

1. Read [`operators/index.yaml`](operators/index.yaml) and classify the
   current task or failure mode.
2. Load the smallest relevant operator file. Compose operators when a task
   crosses boundaries; do not send the whole catalog as context.
3. Build an operator-local context packet containing the task, locus, goal,
   evidence/source references, state, relations, uncertainty, conflicts,
   invariants, permissions, and requested return schema.
4. Execute the operator's `procedure` in order. Treat every `hold_when`
   condition as a real stop/branch/ask condition, not as a hint to guess.
5. Return the declared fields and run the listed `evaluators` before handing
   the result to another operator or persisting a proposal.
6. Record the operator id/version, input references, configuration, output,
   evaluator result, and any hold/branch decision in the derivation record.

The default posture is `grounded` evidence, `branch` uncertainty,
`proposal_only` mutation, and no external action without explicit
authorization. A no-hit, insufficient context, unresolved identity, or
contradiction is a valid result.

## Stable configuration axes

Operators accept the same orthogonal knobs wherever applicable:

- `abstraction_level`: `world`, `system`, `module`, or `implementation`;
- `depth`: `map`, `working`, or `exhaustive`;
- `context_lens`: `conceptual`, `technical`, `strategic`, `ethical`, or
  `operational`;
- `output_mode`: `plain_language`, `technical`, or `machine_readable`;
- `evidence_strictness`: `exploratory`, `grounded`, or `citation_required`;
- `uncertainty_policy`: `branch`, `ask`, or `hold`;
- `proof_demand`: `conceptual`, `operational`, or `end_to_end`.

Change these parameters instead of cloning near-identical operators.

## Operator contract

Every operator file follows the contract in [`operator-contract.yaml`](operator-contract.yaml):

```yaml
operator:
  id: world://operator/guardrail/example
  version: 1
  kind: control | transformational
  category: stable mistake category
  purpose: one-sentence semantic purpose
  accepts: typed input descriptions
  requires_context: required packet fields
  preconditions: checks before execution
  parameters: configurable axes
  procedure: ordered observable steps
  returns: structured output fields
  invariants: distinctions that must survive
  forbidden_shortcuts: disallowed substitutions
  hold_when: conditions for hold/branch/ask
  failure_modes: diagnosable failures
  evaluators: deterministic or semantic quality checks
  evidence: source basis and category rationale
```

## Composition

The normal architecture/design route is:

```text
whole-before-parts
  -> boundary/ontology check
  -> context compile
  -> decomposition + integration
  -> identity/provenance check
  -> utility/evaluation check
  -> modularity and runtime-boundary check
```

The 16 guardrail operators in this catalog are narrower controls for common
failure classes. They do not replace domain reasoning; they prevent a useful
transformation from silently becoming an unsupported fact, an unsafe action,
or an unreproducible runtime state.

## Validation

Run:

```bash
uv run python scripts/validate_reasoning_operators.py
uv run pytest tests/test_reasoning_operators.py -q
```

`make check` includes both checks.
