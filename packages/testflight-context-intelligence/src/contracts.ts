export const packetStatuses = [
  "ready",
  "partial",
  "needs_clarification",
  "no_hit",
  "unavailable",
] as const;

export type PacketStatus = (typeof packetStatuses)[number];

export interface ContextRequest {
  prompt: string;
  workflowStage?: string;
  assetType?: string;
  objective?: string;
  audience?: string;
  audienceSegmentIds?: string[];
  channel?: string;
  geography?: string;
  occasion?: string;
  validTime?: string;
  workspaceId?: string;
  productId?: string;
  campaignId?: string;
  offerId?: string;
  visualLanguageProfileId?: string;
  visualLanguageRevisionId?: string;
  contextId?: string;
  branchId?: string;
  perspectiveIds?: string[];
}

export interface NormalizedRequest {
  prompt: string;
  workflowStage?: string;
  assetType?: string;
  objective?: string;
  audience?: string;
  audienceSegmentIds?: string[];
  channel?: string;
  geography?: string;
  occasion?: string;
  validTime?: string;
  workspaceId: string;
  productId?: string;
  campaignId?: string;
  offerId?: string;
  visualLanguageProfileId?: string;
  visualLanguageRevisionId?: string;
  contextId?: string;
  branchId?: string;
  perspectiveIds?: string[];
}

export type VisualLanguageAuthority =
  | "authorized_internal"
  | "official_public"
  | "observed_public"
  | "inferred"
  | "generated_proposal";

export type VisualLanguageLifecycle =
  | "draft"
  | "observed"
  | "approved"
  | "deprecated"
  | "archived";

export type VisualModuleMode = "replace" | "extend" | "disable";

export interface VisualScope {
  brandId: string;
  productId?: string;
  campaignId?: string;
  offerId?: string;
  audienceSegmentIds?: string[];
  channel?: string;
  geography?: string;
  occasion?: string;
  workflowStages?: string[];
}

export interface VisualReferenceRights {
  permittedUse: "analysis_and_reference" | "generation" | "production" | "none";
  generationUse: "inspiration_only" | "derived_asset" | "exact_asset" | "none";
  attribution?: string;
}

export interface VisualReference {
  id: string;
  revision: number;
  kind: string;
  schemaVersion: number;
  label: string;
  payload: Record<string, unknown>;
  assetRefs: string[];
  authority: VisualLanguageAuthority;
  epistemicStatus: "reported" | "observed" | "inferred" | "hypothesized";
  status: VisualLanguageLifecycle;
  sourceIds: string[];
  evidenceIds: string[];
  validFrom?: string;
  validUntil?: string;
  sourcePublishedAt?: string;
  recordedAt: string;
  lastVerifiedAt: string;
  rights: VisualReferenceRights;
  limitations: string[];
  slot?: string;
}

export interface VisualModuleSelection {
  slot: string;
  referenceId: string;
  mode: VisualModuleMode;
}

export interface VisualLanguageProfile {
  id: string;
  label: string;
  description: string;
  status: VisualLanguageLifecycle;
}

export interface VisualLanguageRevision {
  id: string;
  profileId: string;
  revision: number;
  branch: string;
  parentRevisionIds: string[];
  modules: VisualModuleSelection[];
  authority: VisualLanguageAuthority;
  epistemicStatus: "reported" | "observed" | "inferred" | "hypothesized";
  status: VisualLanguageLifecycle;
  validFrom?: string;
  validUntil?: string;
  recordedAt: string;
  lastVerifiedAt: string;
  sourceIds: string[];
  evidenceIds: string[];
  limitations: string[];
  gaps?: string[];
}

export interface VisualLanguageBinding {
  id: string;
  profileId: string;
  revisionId: string;
  scope: VisualScope;
  priority: number;
  status: VisualLanguageLifecycle;
  validFrom?: string;
  validUntil?: string;
  recordedAt: string;
  lastVerifiedAt: string;
  sourceIds: string[];
  evidenceIds: string[];
  limitations: string[];
}

export interface VisualLanguageManifest {
  version: 1;
  workspaceId: string;
  brandId: string;
  profiles: VisualLanguageProfile[];
  revisions: VisualLanguageRevision[];
  references: VisualReference[];
  bindings: VisualLanguageBinding[];
}

export interface VisualLanguageRequest {
  workspaceId: string;
  brandId: string;
  workflowStage?: string;
  productId?: string;
  campaignId?: string;
  offerId?: string;
  audienceSegmentIds?: string[];
  channel?: string;
  geography?: string;
  occasion?: string;
  validTime?: string;
  profileId?: string;
  revisionId?: string;
}

export interface ResolvedVisualLanguage {
  status: "ready" | "partial" | "needs_clarification" | "no_hit";
  request: VisualLanguageRequest;
  profiles: VisualLanguageProfile[];
  revisions: VisualLanguageRevision[];
  references: VisualReference[];
  conflicts: string[];
  omissions: string[];
  citations: Array<{ evidenceId: string; sourceId: string }>;
  receipt: {
    selectedBindingIds: string[];
    selectedProfileRevisionIds: string[];
    selectedReferenceIds: string[];
    excludedReferenceIds: string[];
    precedence: string[];
  };
}

export interface WorldViewSelectionRequest {
  workspaceId: string;
  contextId?: string;
  branchId?: string;
  taskType: string;
  perspectiveIds: string[];
  permittedRecordIds: string[];
  scope: Pick<
    NormalizedRequest,
    | "assetType"
    | "audience"
    | "channel"
    | "geography"
    | "occasion"
    | "validTime"
  >;
}

export interface ResolvedWorldView {
  viewId: string;
  status: "hit" | "partial" | "no_hit" | "hold";
  workspaceId: string;
  contextId?: string;
  branchId?: string;
  perspectiveIds: string[];
  selectedRecordIds: string[];
  unresolvedConflictIds: string[];
  omissions: string[];
  routeReceipt: string[];
  records?: {
    states: Array<Record<string, unknown>>;
    perspectives: Array<Record<string, unknown>>;
    relationshipFrames: Array<Record<string, unknown>>;
    evidenceLinks: Array<Record<string, unknown>>;
    hypotheses: Array<Record<string, unknown>>;
    experiments: Array<Record<string, unknown>>;
    observedOutcomes: Array<Record<string, unknown>>;
    learningUpdates: Array<Record<string, unknown>>;
  };
}

export interface WorldViewResolver {
  resolve(
    request: WorldViewSelectionRequest,
  ): ResolvedWorldView | Promise<ResolvedWorldView>;
}

export interface VisualLanguageResolver {
  resolve(request: VisualLanguageRequest): ResolvedVisualLanguage;
}

export interface WorkflowRecipe {
  stage: string;
  goal: string;
  route: string;
  requiredInputs: string[];
  queryHints: string[];
  reasoningInstructions: string[];
  entitySelection?: {
    always: string[];
    conditions: Array<{
      field: keyof Pick<
        NormalizedRequest,
        | "prompt"
        | "assetType"
        | "objective"
        | "audience"
        | "channel"
        | "geography"
        | "occasion"
      >;
      includesAny: string[];
      entityIds: string[];
    }>;
  };
}

export interface IntelligenceConfiguration {
  version: 1;
  workspaceId: string;
  brandId: string;
  datasetName: string;
  subjectScope: string;
  retrieval: {
    topK: number;
    maximumQueries: number;
    navigationSourcePatterns: string[];
  };
  activation: {
    actionTerms: string[];
    domainTerms: string[];
  };
  workflows: WorkflowRecipe[];
  sections: string[];
  operators: string[];
  visualLanguage?: {
    enabled: boolean;
    route: "visual-language";
    workflowStages: string[];
    manifestPath?: string;
    datasetName?: string;
    audienceSegmentAliases?: Array<{ id: string; includesAny: string[] }>;
    offerAliases?: Array<{ id: string; includesAny: string[] }>;
  };
  worldView?: {
    enabled: boolean;
    manifestPath?: string;
  };
}

export interface RetrievalQuery {
  text: string;
  route: string;
  datasetName: string;
  workspaceId: string;
  brandId: string;
  topK: number;
  retrievalKind?:
    | "lexical_chunk"
    | "exact_entity"
    | "visual_profile"
    | "visual_reference";
  entityIds?: string[];
  profileIds?: string[];
  revisionIds?: string[];
  referenceIds?: string[];
  branchId?: string;
  perspectiveIds?: string[];
}

export interface RetrievedKnowledge {
  id: string;
  text: string;
  sourceUrl?: string;
  workspaceId?: string;
  brandId?: string;
  taskView?: string;
  docType?: string;
  validFrom?: string;
  validThrough?: string;
  promotionStatus?: string;
  score?: number;
  retrievalKind?:
    | "lexical_chunk"
    | "exact_entity"
    | "visual_profile"
    | "visual_reference";
  entityIds?: string[];
  profileId?: string;
  revisionId?: string;
  referenceId?: string;
  referenceKind?: string;
  branchId?: string;
  perspectiveIds?: string[];
}

export interface RejectedKnowledge {
  id: string;
  reason: string;
  sourceUrl?: string;
}

export interface KnowledgeStatement {
  statement: string;
  evidenceIds: string[];
}

export interface Citation {
  evidenceId: string;
  sourceUrl: string;
}

export interface DerivationReceipt {
  activationReason: "automatic" | "explicit";
  intelligenceModel: string;
  workspaceId: string;
  brandId: string;
  datasetName: string;
  workflowStage?: string;
  queries: RetrievalQuery[];
  acceptedEvidenceIds: string[];
  rejected: RejectedKnowledge[];
  operators: string[];
  evaluators: Array<{ id: string; passed: boolean; detail: string }>;
  interpretationMode: "model" | "deterministic_fallback";
  entities: {
    selectedEntityIds: string[];
    retrievedEntityIds: string[];
    mentionedEntityIds: string[];
    usedEntityIds: string[];
  };
  visualLanguage?: {
    status: ResolvedVisualLanguage["status"];
    profileRevisionIds: string[];
    referenceIds: string[];
  };
  trace: {
    runId: string;
    status: "available" | "unavailable" | "disabled";
    detail?: string;
  };
  worldView?: {
    viewId?: string;
    contextId?: string;
    branchId?: string;
    perspectiveIds: string[];
    status: "not_resolved" | "resolved";
    selectedRecordIds?: string[];
    omissions?: string[];
    unresolvedConflictIds?: string[];
  };
}

export interface ContextPacket {
  version: 1;
  status: PacketStatus;
  request: NormalizedRequest;
  unresolvedFields: string[];
  knowledge: Record<string, KnowledgeStatement[]>;
  reasoningInstructions: string[];
  conflicts: string[];
  limitations: string[];
  omissions: string[];
  clarificationQuestions: string[];
  citations: Citation[];
  receipt: DerivationReceipt;
  visualLanguage?: ResolvedVisualLanguage;
  worldView?: ResolvedWorldView;
}

export interface IntelligenceModel {
  readonly id: string;
  completeJson(input: {
    purpose: "interpret" | "synthesize";
    system: string;
    payload: unknown;
    signal?: AbortSignal;
  }): Promise<unknown>;
}

export interface KnowledgeRetriever {
  retrieve(
    query: RetrievalQuery,
    signal?: AbortSignal,
  ): Promise<RetrievedKnowledge[]>;
}

export type ContextTracePhase =
  | "interpretation"
  | "retrieval"
  | "visual_language"
  | "world_view"
  | "filter"
  | "synthesis"
  | "context_packet"
  | "agent_output"
  | "agent_error";

export interface TraceEvidenceReference {
  hash: string;
  retrievalId: string;
  sourceUrl?: string;
  entityIds: string[];
}

export interface ContextTraceEvent {
  sequence?: number;
  at?: string;
  phase: ContextTracePhase;
  input?: unknown;
  output?: unknown;
  evidenceRefs?: TraceEvidenceReference[];
  error?: string;
}

export interface ContextTraceHeader {
  version: 1;
  runId: string;
  startedAt: string;
  configuration: Pick<
    IntelligenceConfiguration,
    "workspaceId" | "brandId" | "datasetName" | "operators"
  >;
  modelId: string;
}

export interface ContextRunTrace {
  header: ContextTraceHeader;
  events: ContextTraceEvent[];
  evidence: Record<string, RetrievedKnowledge>;
}

export interface ContextTraceStore {
  start(header: ContextTraceHeader): Promise<void>;
  append(runId: string, event: ContextTraceEvent): Promise<void>;
  putEvidence(
    runId: string,
    item: RetrievedKnowledge,
  ): Promise<TraceEvidenceReference>;
  read(runId: string): Promise<ContextRunTrace>;
}
