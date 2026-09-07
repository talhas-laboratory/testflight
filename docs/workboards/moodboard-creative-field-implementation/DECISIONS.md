# Decisions

Record durable decisions here.

## D-001 — Application profile over the existing kernel

Status: accepted for implementation planning.

Build Moodboard / Creative Field as a creative-domain application layer over `testflight-semantic`.
Do not create a second world model or make Cognee canonical.

## D-002 — Three-object separation

Status: accepted.

Moodboard owns evidence-bearing curation; Creative Field owns reviewed project semantics; Field
Connector owns task projection, target translation and evaluation.

## D-003 — Project-scoped by default

Status: accepted.

Boards and fields attach to an explicit CreativeProject and Brand workspace. Cross-project or
personal-taste promotion requires a separate reviewed operation.

## D-004 — Connections are first-class contracts

Status: accepted.

Implement `ProjectBinding`, `FieldBinding` and `CreativeContextPacket` in the first architecture
blocks so the moodboard cannot become an isolated subsystem.

## D-005 — Canonical local state and rebuildable indexes

Status: accepted.

Store runtime assets outside Git in a content-addressed local evidence store; keep append-only
events and canonical records in the repository adapter. Cognee, embeddings, UI snapshots and
packets are rebuildable projections.

## D-006 — Provider-neutral operator contracts

Status: accepted.

Creative transformations use versioned operators and provider capability adapters. Client packs
configure general operators unless the transformation itself differs. Semantic provider failure
returns a non-success status; it does not trigger a rule-based semantic substitute.

## D-007 — Narrow first vertical slice

Status: accepted.

Begin with one Hellobiotic project fixture, one image/text board, one reviewed field, text/image
projections and one artifact workflow. A full canvas, mobile-native client, mixing and additional
modalities follow only after the semantic gates pass.

## D-008 — Project Creative Field into an isolated child container

Status: accepted.

Creative Field records are projected into a project-scoped `creative-field` child container with
namespaced stable IDs, source-bearing documents and bounded relationship edges. The projection
preserves scope, lifecycle, authority, evidence and rights metadata, but remains proposal-only and
rebuildable from canonical SQLite records. Construction requires an explicit `*_staging` dataset;
Cognee population is a separately authorized adapter call after retrieval certification.

## D-009 — Treat the Creative Studio UI as a durable command boundary

Status: accepted and implemented.

Creative Studio commands serialize through a thread-safe repository boundary. A reference upload
and its board revision commit atomically; startup replays the latest board revision and review
decisions. Binary content remains in the content-addressed blob store and is served only when its
hash is referenced by the current project. Upload rights are explicit evidence metadata, not an
inferred permission. This keeps the UI replayable without making it canonical for semantic
interpretation.

## D-010 — Keep orchestration provider-neutral and proposal-only

Status: accepted for implementation.

The first runtime bridge is a synchronous `CreativeFieldRunCoordinator` in the creative-domain
package. It composes the existing observation, interpretation, and synthesis workflows through
the `OperatorExecutor` and `CreativeRecordRepository` ports. It persists typed proposal records and
operator receipts, but cannot create an accepted field version. A later application adapter may
expose this coordinator through a job API and connect it to the TypeScript operator runtime; that
transport choice must not leak into domain workflows.

## D-011 — Use a bounded local HTTP boundary for the first runtime bridge

Status: accepted and implemented.

Creative Studio communicates with the TypeScript `OperatorRuntime` through a small local HTTP/JSON
adapter. The runtime owns provider selection, capability preflight, retry/cancellation policy and
redacted receipts; the Python adapter owns only request/response translation. The endpoint accepts
`POST /execute` and `GET /health`, enforces a body limit, normalizes snake_case fields, and is not
intended for public exposure. Authentication and process supervision remain composition-root
responsibilities.

## Open decisions

- First real inference provider and fallback routing policy.
- Exact local asset retention/licensing policy.
- Minimal Creative Studio rendering technology.
- Calibrated thresholds for automatic acceptance versus required review; default is review.
- First production text and image target adapters.

## D-016 — Invocation is an explicit, receipt-bearing boundary

Status: accepted and implemented.

`GenerationPacket` preparation remains target-neutral and proposal-safe. `invoke_generation` is a
separate application command that requires an authority grant, a configured target adapter and
content-addressed output storage. The command persists an immutable `InvocationReceipt` and
`CreativeOutput`; repeated invocation IDs replay the receipt rather than calling a target again.
Provider failures remain failed/held outcomes and cannot promote or mutate Creative Field state.

## D-017 — Evaluation is a proposal-only downstream operator

Status: accepted and implemented.

Creative Studio reconstructs the exact output, packet, projection, request and accepted field
version for `evaluate_output`, then routes that bounded evidence through the registered evaluation
operator. Only typed `CreativeEvaluation` and `FeedbackRecord` proposals are persisted. Replay by
output ID avoids repeated evaluator calls, and no evaluation result can mutate a field version.

## D-012 — Keep the first executable creative pack conservative

Status: accepted and implemented.

The TypeScript runtime registers the three first Creative Field operators with stable IDs,
capability modalities and structural output gates. The versioned YAML files remain the source of
semantic procedure, invariants and evaluator intent until an explicit loader/compiler is added.
This prevents a permissive provider response from bypassing the Python domain validators while
allowing provider and model configuration to remain replaceable at the composition root.

## D-013 — Persist analysis runs as canonical replay records

Status: accepted and implemented.

Creative Studio persists one `CreativeFieldRun` per explicit run ID, including board revision,
stage statuses, redacted operator receipts, errors and proposal identity. The default run ID is
derived from the moodboard and current board revision. A repeated command rehydrates the persisted
result without invoking an executor again, while a new board revision receives a new run identity.
Run replay restores proposal state but never promotes it to an accepted field version.

## D-014 — Acceptance must target a proposal and carry authority

Status: accepted and implemented.

Creative Studio treats the analyzed proposal as the review target. An `accept` command requires an
explicit `authority_grant_id`, calls `CreativeFieldLifecycle.review_and_version`, and persists the
review decision and immutable version together. Missing authority remains a held outcome; hold and
revise actions do not silently create versions. This keeps review distinct from model synthesis and
prevents a UI click from becoming unscoped canonical meaning.

## D-015 — Artifact projection consumes an explicit bounded world packet

Status: accepted and implemented.

Creative Studio's first `project_field` command requires explicit project/field binding inputs,
canonical entity identities, a pre-resolved world-view packet, a request and a target capability
manifest. It delegates scope and precedence checks to `CreativeBindingResolver` and composition to
`CreativeContextCompiler`; it does not search the entire Brand world or infer missing context.
Bindings and packets are persisted as rebuildable canonical application records, with omissions and
conflicts visible to the artifact workflow.

## D-018 — Load semantic contracts at the provider boundary and keep entity binding separate

Status: accepted and implemented.

`reasoning/operators/index.yaml` and its versioned YAML contracts remain the source of operator
procedure, invariants, hold conditions and evaluators. Creative Studio loads only the four Creative
Field contracts needed by its configured runtime; a client pack supplies scoped references and
preferences over those contracts. The provider receives the current operator's bounded,
credential-redacted contract/configuration context, while Python domain validators remain the
authority for persistence. A Brand-world resolver uses exact workspace/context/branch selection;
target entity IDs remain `ProjectBinding` scope and are not silently reused as world-record filters.

## D-019 — Expose artifact handoff as explicit UI commands

Status: accepted and implemented.

Creative Studio exposes the existing `project_field`, `prepare_generation`, `invoke_generation` and
`evaluate_output` commands through a single Artifact Bridge panel. The UI collects the required
workspace, context, branch, entity, privacy, authority, request, target and disclosure values; it
does not infer them or register a target implicitly. Backend validators remain authoritative, so a
missing accepted version, world hit, permission, target adapter or authority grant stays a visible
held outcome. This keeps the mobile surface simple while preserving the canonical command boundary.

## D-020 — Keep HTTP canonical while supporting a safe file preview

Status: accepted and implemented.

Creative Studio remains an HTTP application because state, blobs and commands are served by its
project-scoped API. The static page uses relative asset references so a direct filesystem preview
can still render its visual shell, but file mode skips API calls and presents a preview-only notice.
This makes review screenshots reliable without implying that a file URL can bypass the server
boundary.

## D-021 — Make spatial curation durable but never semantic by implication

Status: accepted and implemented.

Creative Studio now presents `Placement` records as a spatial canvas and persists intentional
rearrangement through a new immutable `BoardRevision`. Named `ReferenceCluster` records are also
revision-scoped, so a later layout cannot rewrite an earlier curatorial state. The UI can surface
source and annotation signals and lets a user create or assign clusters, but movement, proximity
and grouping do not invoke the observation, interpretation or synthesis operators and cannot
mutate the Brand world or Creative Field. The existing project-binding scope remains the boundary:
all layout records are tied to the current project and moodboard.
