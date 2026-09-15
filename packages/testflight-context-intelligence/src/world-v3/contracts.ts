/** Provider-neutral contracts for deterministic Brand World v3 context compilation. */

export type WorldV3Lifecycle =
  | "proposed"
  | "accepted"
  | "challenged"
  | "superseded"
  | "revoked"
  | "archived";

export type WorldV3Kind =
  | "entity"
  | "state"
  | "event"
  | "relation"
  | "claim"
  | "source"
  | "evidence"
  | "decision";

export interface TemporalInterval {
  start?: string;
  end?: string;
  fromTime?: string;
  toTime?: string;
  fromSemantics?: string;
  toSemantics?: string;
  precision?: string;
  sourceTimezone?: string;
}

export interface RelationParticipant {
  roleId: string;
  recordId: string;
}

export interface EventParticipant {
  roleId: string;
  entityId: string;
}

export interface WorldV3RecordEnvelope {
  id: string;
  typeId: string;
  schemaVersion: string;
  recordVersion: number;
  workspaceId: string;
  moduleId: string;
  branchId: string;
  lifecycleStatus: WorldV3Lifecycle;
  validTime?: TemporalInterval;
  knownTime?: TemporalInterval;
  contextRefs?: string[];
  provenanceRefs?: string[];
  derivationRef?: string;
  authorityRef?: string;
  createdAt: string;
  createdBy: string;
  supersedesRef?: string;
}

export interface WorldEntityRecord extends WorldV3RecordEnvelope {
  kind: "entity";
  canonicalLabel: string;
  aliases: string[];
  definition: string;
}

export interface WorldStateRecord extends WorldV3RecordEnvelope {
  kind: "state";
  subjectIds: string[];
  stateValue: string;
  stateSchemaId: string;
  describedByClaimIds: string[];
}

export interface WorldEventRecord extends WorldV3RecordEnvelope {
  kind: "event";
  eventTypeId: string;
  participants: EventParticipant[];
  occurredAt: TemporalInterval;
  evidenceIds: string[];
}

export interface WorldRelationRecord extends WorldV3RecordEnvelope {
  kind: "relation";
  relationTypeId: string;
  participants: RelationParticipant[];
  evidenceIds: string[];
}

export interface WorldClaimRecord extends WorldV3RecordEnvelope {
  kind: "claim";
  claimKind:
    | "observation"
    | "interpretation"
    | "hypothesis"
    | "proposal"
    | "factual_assertion"
    | "normative_commitment";
  subjectId: string;
  predicateId: string;
  objectId?: string;
  objectValue?: string;
  evidenceIds: string[];
  opposingEvidenceIds: string[];
  contradictionIds: string[];
  limitations: string[];
  permittedTaskTypes: string[];
  perspectiveId?: string;
}

export interface WorldSourceRecord extends WorldV3RecordEnvelope {
  kind: "source";
  locator: string;
  title: string;
  contentPolicy:
    | "retained"
    | "bounded_excerpt"
    | "live_reference_only"
    | "prohibited";
  capturedAt: string;
  contentHash?: string;
}

export interface WorldEvidenceRecord extends WorldV3RecordEnvelope {
  kind: "evidence";
  sourceId: string;
  locator: string;
  excerpt?: string;
  measurement?: string;
  limitations: string[];
  integrityHash?: string;
}

export interface WorldDecisionRecord extends WorldV3RecordEnvelope {
  kind: "decision";
  question: string;
  alternatives: Array<{ id: string; label: string; rationale?: string }>;
  selectedAlternativeId?: string;
  status: "proposed" | "approved" | "rejected" | "superseded";
  rationale?: string;
  evidenceIds: string[];
  affectedRecordIds: string[];
}

/** Strict discriminated read projection of the canonical Python V3 union. */
export type WorldV3Record =
  | WorldEntityRecord
  | WorldStateRecord
  | WorldEventRecord
  | WorldRelationRecord
  | WorldClaimRecord
  | WorldSourceRecord
  | WorldEvidenceRecord
  | WorldDecisionRecord;

export type ContextAbstraction =
  | "overview"
  | "working"
  | "evidence"
  | "history";

export interface ContextScope {
  moduleIds?: string[];
  contextRefs?: string[];
  seedRecordIds?: string[];
  perspectiveRefs?: string[];
  validAt?: string;
}

export interface RetrievalExpansionBudget {
  /** Maximum canonical records disclosed in the final packet. */
  maximumRecords: number;
  /** Maximum compiler disclosure stages (roads, evidence, history). */
  maximumCompilerStages: number;
  /** Maximum semantic candidates requested from the discovery projection. */
  maximumSemanticCandidates: number;
  /** Maximum projection edges returned for structural discovery. */
  maximumGraphEdges: number;
  /** Maximum graph distance from any semantic or explicit seed. */
  maximumGraphHops: number;
}

export interface ContextRequestV2 {
  requestId: string;
  principalRef?: string;
  agentDefinitionRef: string;
  agentRoles: string[];
  taskRef: string;
  taskFamily: string;
  objective: string;
  currentWorkStateRef?: string;
  authorityGrantRefs: string[];
  workspaceId: string;
  branchId: string;
  permittedLifecycleStatuses: WorldV3Lifecycle[];
  scope: ContextScope;
  desiredAbstraction: ContextAbstraction;
  sufficiencyPolicyRef: string;
  budget: RetrievalExpansionBudget;
  requiredOutputSchema?: string;
  /** Supplied instead of reading the wall clock, keeping freshness evaluation replayable. */
  compiledAt: string;
}

export interface SufficiencyRequirement {
  kind: WorldV3Kind;
  minimum: number;
  mustHaveEvidence?: boolean;
}

export interface SufficiencyPolicy {
  id: string;
  requirements: SufficiencyRequirement[];
  requiredModuleIds?: string[];
  minimumEvidenceRecords?: number;
  maximumEvidenceAgeDays?: number;
  unresolvedConflicts: "hold" | "report";
}

export type ExpansionStage = "foundation" | "roads" | "evidence" | "history";

export interface RouteDefinition {
  id: string;
  version: number;
  taskFamily: string;
  eligibleAgentRoles: string[];
  startModuleIds: string[];
  requiredSemanticKinds: WorldV3Kind[];
  allowedRelationTypeIds: string[];
  abstractionOrder: ExpansionStage[];
  mandatoryGates: Array<
    "authority" | "valid_time" | "lifecycle" | "freshness" | "conflict"
  >;
  requiredAuthorityGrantRefs?: string[];
  requiredAuthorityCapabilities?: string[];
  expansionTriggers: Array<
    "missing_kind" | "missing_evidence" | "missing_module" | "history_requested"
  >;
  stopConditions: Array<
    "sufficient" | "budget_exhausted" | "no_candidates" | "gate_failure"
  >;
  sufficiencyPolicy: SufficiencyPolicy;
  priorEffectivenessEvidenceIds?: string[];
}

export type RouteEvaluationStatus =
  | "ready"
  | "partial"
  | "no_hit"
  | "hold"
  | "stale"
  | "unauthorized";

export interface SufficiencyCheck {
  id: string;
  passed: boolean;
  expected: string;
  observed: string;
}

export interface RouteEvaluation {
  readonly routeId: string;
  readonly routeVersion: number;
  readonly status: RouteEvaluationStatus;
  readonly checks: readonly SufficiencyCheck[];
  readonly selectedRecordCount: number;
  readonly expansionCount: number;
  readonly budgetExhausted: boolean;
  readonly unresolvedConflictIds: readonly string[];
  readonly staleEvidenceIds: readonly string[];
  readonly missingAuthorityGrantRefs: readonly string[];
  readonly authorityRejections: readonly AuthorityGrantRejection[];
  readonly stopReason:
    | "sufficient"
    | "budget_exhausted"
    | "no_candidates"
    | "authority_failure"
    | "stale_required_evidence"
    | "unresolved_conflict"
    | "gate_failure"
    | "insufficient";
}

export interface AuthorityGrantScope {
  workspaceId: string;
  branchIds?: string[];
  moduleIds?: string[];
  objectIds?: string[];
  contextRefs?: string[];
}

/** Resolved by an authentication/authorization boundary; never synthesized from request IDs. */
export interface ResolvedAuthorityGrant {
  id: string;
  status: "active" | "revoked";
  principalRef: string;
  agentDefinitionRef: string;
  capabilities: string[];
  scope: AuthorityGrantScope;
  validFrom: string;
  validUntil?: string;
}

export type AuthorityGrantRejectionReason =
  | "missing_request_ref"
  | "unknown_grant"
  | "invalid_grant"
  | "inactive_grant"
  | "wrong_principal"
  | "wrong_agent"
  | "wrong_capability"
  | "not_yet_valid"
  | "expired"
  | "wrong_workspace"
  | "wrong_branch"
  | "wrong_module_scope"
  | "wrong_object_scope"
  | "wrong_context_scope";

export interface AuthorityGrantRejection {
  grantRef: string;
  reason: AuthorityGrantRejectionReason;
  detail: string;
}

export interface ContextCitation {
  evidenceId: string;
  sourceId?: string;
  locator?: string;
}

export type TraceExclusionReason =
  | "not_v3"
  | "wrong_workspace"
  | "wrong_branch"
  | "lifecycle"
  | "task_permission"
  | "perspective"
  | "context"
  | "valid_time"
  | "authority"
  | "relation_family"
  | "not_reached"
  | "budget";

export interface ContextTraceStep {
  sequence: number;
  phase:
    | "validate"
    | "scope"
    | "gate"
    | "select"
    | "expand"
    | "evaluate"
    | "stop";
  action: string;
  recordIds: string[];
  detail?: string;
}

export interface ContextRunTraceV2 {
  readonly version: 2;
  readonly requestId: string;
  readonly routeRef: string;
  readonly inputFingerprint: string;
  readonly steps: readonly ContextTraceStep[];
  readonly exclusions: readonly {
    recordId: string;
    reason: TraceExclusionReason;
  }[];
  readonly selectedRecordIds: readonly string[];
  readonly selectedRecordVersions: readonly {
    id: string;
    recordVersion: number;
  }[];
  readonly expansions: readonly ExpansionStage[];
  readonly omissions: readonly string[];
  readonly stopReason: RouteEvaluation["stopReason"];
  readonly packetHash: string;
  readonly projectionRetrieval?: ProjectionRetrievalTrace;
}

export type ProjectionFreshness = "exact" | "verified_partial" | "stale";
export type ProjectionEdgeClass =
  | "canonical_relation"
  | "canonical_reference"
  | "derived_similarity"
  | "inferred_relation"
  | "projection_structure";

export interface ProjectionCandidate {
  recordId: string;
  recordVersion: number;
  canonicalRecordHash: string;
  score: number;
  retrievalMethod: "semantic" | "structural" | "seed" | "expansion";
  matchedFields: string[];
}

export interface ProjectionEdge {
  sourceRecordId: string;
  targetRecordId: string;
  predicate: string;
  edgeClass: ProjectionEdgeClass;
  canonicalRelationId?: string;
  canonicalRelationHash?: string;
  derivationRef?: string;
}

export interface ProjectionRetrievalTrace {
  canonicalSnapshotRoot: string;
  projectionSnapshotRoot: string;
  freshness: ProjectionFreshness;
  candidateRecordIds: string[];
  hydratedRecordIds: string[];
  canonicalRelationIds: string[];
  discardedEdgeCount: number;
  retrievalMethods: string[];
}

export interface ContextPacketV2 {
  readonly version: 2;
  readonly packetId: string;
  readonly status: RouteEvaluationStatus;
  readonly request: ContextRequestV2;
  readonly routeRef: string;
  readonly records: readonly WorldV3Record[];
  readonly recordIds: readonly string[];
  readonly evidenceIds: readonly string[];
  readonly citations: readonly ContextCitation[];
  readonly unresolvedConflictIds: readonly string[];
  readonly omissions: readonly string[];
  readonly instructions: readonly string[];
  readonly evaluation: RouteEvaluation;
  readonly trace: ContextRunTraceV2;
}

export interface ReplayResult {
  exact: boolean;
  packet: ContextPacketV2;
  differences: string[];
}
