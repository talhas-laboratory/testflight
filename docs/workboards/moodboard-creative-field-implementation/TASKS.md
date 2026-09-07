# Tasks

| id | status | owner | title | gate | depends on |
|---|---|---|---|---|---|
| `TASK-001-record-architecture-decisions-and-public-contrac` | done | talha | Record architecture decisions and public contracts | done | — |
| `TASK-002-create-the-creative-field-domain-package-and-ont` | done | talha | Create the creative-field domain package and ontology | implementation | 001 |
| `TASK-003-implement-local-multimodal-evidence-and-board-re` | done | talha | Implement local multimodal evidence and board revision storage | implementation | 001, 002 |
| `TASK-004-author-creative-operators-and-semantic-gold-fixt` | done | talha | Author creative operators and semantic gold fixtures | implementation | 001, 002 |
| `TASK-005-implement-provider-neutral-operator-execution-an` | done | talha | Implement provider-neutral operator execution and routing | implementation | 001, 004 |
| `TASK-006-build-reference-observation-and-interpretation-w` | done | talha | Build reference observation and interpretation workflow | implementation | 003, 004, 005 |
| `TASK-007-build-creative-field-synthesis-review-and-versio` | done | talha | Build Creative Field synthesis review and version lifecycle | implementation | 002, 004, 006 |
| `TASK-008-connect-fields-to-brand-world-entities-and-conte` | done | talha | Connect fields to Brand-world entities and contexts | implementation | 002, 007 |
| `TASK-009-compile-field-projections-into-artifact-workflow` | done | talha | Compile field projections into artifact workflows | implementation | 004, 005, 008 |
| `TASK-010-build-the-creative-studio-review-experience` | done | talha | Build the Creative Studio review experience | implementation | 003, 006, 007, 008, 009 |
| `TASK-011-add-connector-adapters-output-evaluation-and-fee` | done | talha | Add connector adapters output evaluation and feedback | implementation | 005, 009, 010 |
| `TASK-012-project-creative-field-records-into-cognee` | done | talha | Project Creative Field records into Cognee | done | 007, 008 |
| `TASK-013-certify-the-end-to-end-vertical-slice-and-operat` | review | talha | Certify the end-to-end vertical slice and operations | review | 001–012 |
| `TASK-014-stabilize-creative-studio-persistence-and-browser-flow` | done | talha | Stabilize Creative Studio persistence and browser flow | done | 003, 005, 010 |
| `TASK-015-build-creative-field-run-coordinator` | done | talha | Build the Creative Field run coordinator | done | 004, 005, 006, 007 |
| `TASK-016-add-operator-runtime-http-transport` | done | talha | Add operator-runtime HTTP transport | done | 005, 015 |
| `TASK-017-define-creative-operator-pack-and-local-launcher` | done | talha | Define the creative operator pack and local launcher | done | 004, 016 |
| `TASK-018-wire-creative-studio-analysis-and-run-replay` | done | talha | Wire Creative Studio analysis and run replay | done | 015, 016, 017 |
| `TASK-019-add-authority-gated-field-version-review` | done | talha | Add authority-gated field version review | done | 007, 018 |
| `TASK-020-connect-accepted-field-to-artifact-context` | done | talha | Connect an accepted field to artifact context | done | 008, 009, 019 |
| `TASK-021-invoke-target-and-persist-output-receipt` | done | talha | Invoke a target and persist output receipt | done | 020, 011 |
| `TASK-022-evaluate-output-and-persist-feedback-proposals` | done | talha | Evaluate output and persist feedback proposals | done | 021, 017 |
| `TASK-023-load-semantic-contracts-client-packs-and-world-context` | done | talha | Load semantic contracts, client packs and bounded world context | done | 020, 022 |
| `TASK-024-expose-artifact-handoff-in-creative-studio` | done | talha | Expose the artifact handoff in Creative Studio | done | 023 |

| `TASK-025-fix-file-url-static-preview` | done | talha | Restore styled Creative Studio preview when opened as a file | done | 024 |
| `TASK-026-build-structured-spatial-moodboard-canvas` | done | talha | Build a durable structured spatial Moodboard canvas | done | 003, 010, 024 |

Status values: `backlog`, `ready`, `in-progress`, `review`, `blocked`, `done`.
A task may enter `done` only when every required gate in `GATES.md` has evidence.
