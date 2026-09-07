# TASK-023-load-semantic-contracts-client-packs-and-world-context: Load semantic contracts and resolve bounded world context

Status: done
Owner: talha
Current gate: done

## Problem

The Creative Studio path could execute typed operators and accept a client pack, but the YAML
operator procedures were not yet handed to the model and a live Brand-world resolver could
mistakenly treat bound entity IDs as world-record filters.

## Scope

In:

- load the requested Creative Field YAML contracts through `reasoning/operators/index.yaml`;
- resolve client pack aliases to stable Creative Field operator IDs and pass selected entries;
- include bounded, redacted contract and client configuration instructions at the provider boundary;
- attach rights-gated, bounded local image/text content to observation and output-evaluation calls;
- resolve exact context/branch world views through the existing Brand-world YAML bridge;
- preserve target entity binding separately from optional world-record filtering;
- document composition-root configuration and add focused regression coverage.

Out:

- automatic semantic acceptance or Brand-world mutation;
- a new retrieval index or second ontology;
- live provider credentials or production provider calibration;
- audio/video provider translation beyond the existing metadata and modality holds.

## Acceptance Criteria

- A configured Creative Studio runtime loads all four registered Creative Field contracts and
  sends only the selected contract to the provider instruction boundary.
- Client pack aliases such as `interpret-reference-role` resolve to the stable interpretation
  operator and remain scoped configuration, not a replacement contract.
- Provider-facing contract/configuration text is bounded and does not expose credential-like keys.
- Uploaded image bytes are read only from project-referenced content-addressed storage and remain
  under the operator media size bound.
- A configured Brand-world resolver returns a hit for an exact context/branch without filtering
  out contextual records merely because target entity IDs are not record IDs.
- Missing world context, scope mismatch, rights gaps and provider failures remain held/failed;
  no canonical field version is silently promoted.

## Verification Evidence

- `uv run pytest packages/testflight-creative-field/tests/test_operator_packs.py packages/testflight-creative-field/tests/test_orchestration.py apps/creative-studio/tests/test_server.py -q` — focused suite passed.
- `pnpm --filter @testflight/operator-runtime check` and `pnpm --filter @testflight/operator-runtime test` — strict TypeScript check and 12 runtime tests passed, including contract/configuration redaction and image translation.
- `pnpm --filter @testflight/operator-runtime build` — launcher bundle built.
- `curl --fail --silent http://127.0.0.1:8787/health` while running the launcher with dummy local credentials — `{"status":"ok"}`; no credential was printed.
- `make check` — passed: 141 Python tests, all TypeScript checks/tests, registry/operator/secret validators, Brand workspace validation, Creative Field certification and Compose validation. The environment reports a non-blocking Node 22 versus repository `>=24` engine warning.
- `git diff --check` — passed before the board update.

## Changed Files

- `packages/testflight-creative-field/src/testflight_creative_field/operator_packs.py`
- `packages/testflight-creative-field/src/testflight_creative_field/__init__.py`
- `packages/testflight-creative-field/tests/test_operator_packs.py`
- `apps/creative-studio/src/testflight_creative_studio/server.py`
- `apps/creative-studio/tests/test_server.py`
- `apps/creative-studio/README.md`
- `.env.example`
- `packages/testflight-operator-runtime/src/providers.ts`
- `packages/testflight-operator-runtime/test/runtime.test.ts`

## Residual Risks

- The default launcher still needs a real provider endpoint and credential supplied out of band;
  this verification intentionally made no live model call.
- The current media bridge sends images as provider image parts and text as bounded text context;
  audio/video decoding and target-specific multimodal translation remain later increments.
- World context remains YAML-bridge based at this composition root; Cognee retrieval/population is
  still a separately authorized, rebuildable projection.
- Feedback promotion, background jobs and a richer project/artifact workflow UI remain.

## Handoff Notes

The next useful increment is the human-facing project/artifact connection: expose the accepted
field's `ProjectBinding`, context packet, target capability manifest and evaluation state in a
reviewable UI/API flow, then add a real provider smoke only after credentials and endpoint policy
are supplied.
