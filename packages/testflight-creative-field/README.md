# Testflight Creative Field

Provider-neutral contracts for the Moodboard → Creative Field → Field Connector lifecycle.

This package owns creative-domain records and deterministic validation. It does not import model
providers, Cognee, UI frameworks, or target-tool SDKs. It references the shared
`testflight-semantic` kernel for evidence, context, branches, provenance and governance.

The source hierarchy is:

```text
ReferenceAsset / BoardRevision
  → ObservedFeature
  → ReferenceInterpretation / ReferenceContribution
  → CreativeFieldProposal
  → reviewed CreativeFieldVersion
  → FieldProjection / CreativeContextPacket
  → GenerationPacket / CreativeEvaluation
```

Model outputs are proposals. Promotion, binding, disclosure and external action are separate
operations owned by their application or adapter boundary.

`CreativeFieldRunCoordinator` is the provider-neutral composition seam for the first runtime
increment. Given a persisted board revision, it checks project scope and source rights, runs the
observation → interpretation → synthesis workflows through `OperatorExecutor`, and persists only
typed proposal records. Creative Studio persists the surrounding `CreativeFieldRun` record so a
completed run can be replayed without repeating provider work. The coordinator remains synchronous
and proposal-only; background execution and review/version promotion stay outside these domain
contracts.

`FieldProjection` and `CreativeContextPacket` are target-neutral handoffs. A connector adapter may
translate them into a `GenerationPacket`, and the application boundary records an
`InvocationReceipt` and `CreativeOutput` only after an explicitly authorized target call. Output
content is referenced by content-addressed storage rather than embedded in canonical records.
