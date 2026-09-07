# Creative Studio

Creative Studio is the write-capable, project-scoped moodboard surface. References and review
decisions are persisted through the SQLite creative repository; semantic analysis is an explicit
`analyze_field` command that invokes `CreativeFieldRunCoordinator` through the private local
operator-runtime HTTP endpoint.

Run the two local processes separately:

```bash
# terminal 1 — provider-neutral runtime (credentials stay in the environment)
make serve-operator-runtime

# terminal 2 — Creative Studio (analysis is enabled by the endpoint setting)
TESTFLIGHT_OPERATOR_ENDPOINT=http://127.0.0.1:8781/execute \
creative-studio --project-id project:creative-studio
```

Set `TESTFLIGHT_OPERATOR_WORKSPACE_ID`, `TESTFLIGHT_CREATIVE_DIMENSIONS` and
`TESTFLIGHT_CREATIVE_PROJECT_PURPOSE` for a client/project deployment. If the endpoint is omitted,
the board remains usable for capture and review but `analyze_field` returns a held configuration
outcome. Analysis writes a replayable `CreativeFieldRun` and a proposal. To enable the Accept
action to create an immutable version, set `TESTFLIGHT_CREATIVE_AUTHORITY_GRANT_ID` (or pass
`authority_grant_id` in the command payload); without it, acceptance is held. Hold and revise
remain proposal-level decisions.

Set `TESTFLIGHT_CREATIVE_OPERATOR_PACK` (or pass `--operator-pack`) to load a versioned client pack.
The pack contributes scoped vocabulary, context selectors, priorities, forbidden associations and
an evaluator rubric reference as runtime configuration; it does not copy Brand-world facts or
change the general operator contract.

When analysis is enabled, `TESTFLIGHT_CREATIVE_OPERATOR_INDEX` (or `--operator-index`) loads the
canonical YAML contracts from `reasoning/operators/index.yaml`. The selected contract procedure,
invariants, hold conditions and client-pack entry are handed to the provider as bounded, redacted
operator instructions; the domain validators still decide what can be persisted.

Set `TESTFLIGHT_CREATIVE_WORLD_MODEL` (or pass `--world-model`) to resolve the bounded
`ProjectBinding` world view from the existing Brand-world YAML bridge. The command still requires
explicit project/context/branch/entity scope, and a resolver no-hit or scope mismatch is held
before a context packet can reach a target.

After acceptance, `project_field` requires explicit workspace, entity, request, privacy and
disclosure inputs. Supply `world_view` directly for a pre-resolved packet, or configure
`TESTFLIGHT_CREATIVE_WORLD_MODEL` (or `--world-model`) to resolve the exact context/branch through
the existing bounded Brand-world YAML bridge. A resolver no-hit or scope mismatch is held before a
context packet can reach a target. The next command,
`prepare_generation`, translates that packet through a target capability manifest into a
`GenerationPacket`; grounding assets must belong to the project and carry both generation and
disclosure clearance. `invoke_generation` is the only external-action seam: it requires an
authority grant, uses a target adapter registered by target ID, stores normalized output bytes in
the content-addressed blob store, and persists an immutable `InvocationReceipt` plus
`CreativeOutput`. Repeating an invocation ID replays the receipt without calling the target again.
