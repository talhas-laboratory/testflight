# Execution task view

## Goal

Apply a selected operator without collapsing evidence, meaning, state, or
authority.

## Procedure

1. Check the operator version and all preconditions.
2. Execute the finite `procedure` steps in order.
3. Return only the declared fields plus provenance, omissions, and status.
4. If `hold_when` is true, return `hold`, `branch`, `ask`, `partial`, or
   `no_hit` according to the context packet; never guess.
5. Record the operator id/version, input references, configuration, output,
   evaluator status, and derivation.

Execution may be deterministic, model-backed, human, or composite. The
contract is stable across providers.
