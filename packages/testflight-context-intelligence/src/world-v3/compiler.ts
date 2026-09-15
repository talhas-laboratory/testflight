import { createHash } from "node:crypto";
import { evaluateResolvedAuthority } from "./authority.js";
import type {
  AuthorityGrantRejection,
  ContextCitation,
  ContextPacketV2,
  ContextRequestV2,
  ContextRunTraceV2,
  ContextTraceStep,
  ExpansionStage,
  RouteDefinition,
  RouteEvaluation,
  ResolvedAuthorityGrant,
  SufficiencyCheck,
  SufficiencyRequirement,
  TraceExclusionReason,
  WorldV3Kind,
  WorldV3Record,
} from "./contracts.js";

const KIND_PRIORITY: Record<WorldV3Kind, number> = {
  entity: 0,
  claim: 1,
  state: 2,
  decision: 3,
  relation: 4,
  event: 5,
  evidence: 6,
  source: 7,
};
const FOUNDATION_KINDS = new Set<WorldV3Kind>([
  "entity",
  "claim",
  "state",
  "decision",
]);
const DAY_MS = 86_400_000;

function stable(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => `${JSON.stringify(key)}:${stable(entry)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

export function contextDigest(value: unknown): string {
  return createHash("sha256").update(stable(value)).digest("hex");
}

function unique(values: readonly string[]): string[] {
  return [...new Set(values)];
}

function sorted(records: readonly WorldV3Record[]): WorldV3Record[] {
  return [...records].sort(
    (left, right) =>
      KIND_PRIORITY[left.kind] - KIND_PRIORITY[right.kind] ||
      left.id.localeCompare(right.id),
  );
}

function outsideInterval(
  interval: WorldV3Record["validTime"],
  validAt?: string,
): boolean {
  if (!interval || !validAt) return false;
  const start = interval.fromTime ?? interval.start;
  const end = interval.toTime ?? interval.end;
  return Boolean((start && validAt < start) || (end && validAt > end));
}

function recordReferences(record: WorldV3Record): string[] {
  const references = [...(record.contextRefs ?? [])];
  if (record.supersedesRef) references.push(record.supersedesRef);
  if ("evidenceIds" in record) references.push(...record.evidenceIds);
  if (record.kind === "claim") {
    references.push(
      ...record.opposingEvidenceIds,
      ...record.contradictionIds,
      record.subjectId,
    );
    if (record.objectId) references.push(record.objectId);
  } else if (record.kind === "relation") {
    references.push(...record.participants.map((item) => item.recordId));
  } else if (record.kind === "event") {
    references.push(...record.participants.map((item) => item.entityId));
  } else if (record.kind === "evidence") {
    references.push(record.sourceId);
  } else if (record.kind === "state") {
    references.push(...record.subjectIds, ...record.describedByClaimIds);
  } else if (record.kind === "decision") {
    references.push(...record.affectedRecordIds);
  }
  return unique(references);
}

function recordEvidenceIds(record: WorldV3Record): readonly string[] {
  return "evidenceIds" in record ? record.evidenceIds : [];
}

function evidenceIsStale(
  record: WorldV3Record,
  compiledAt: string,
  maximumAgeDays?: number,
): boolean {
  if (record.kind !== "evidence" || maximumAgeDays === undefined) return false;
  const observed =
    record.knownTime?.toTime ??
    record.knownTime?.end ??
    record.knownTime?.fromTime ??
    record.knownTime?.start ??
    record.createdAt;
  if (!observed) return true;
  const age = Date.parse(compiledAt) - Date.parse(observed);
  return Number.isNaN(age) || age > maximumAgeDays * DAY_MS;
}

function hasContextOverlap(
  record: WorldV3Record,
  requested: readonly string[] | undefined,
): boolean {
  if (!requested?.length || !record.contextRefs?.length) return true;
  return record.contextRefs.some((ref) => requested.includes(ref));
}

function addStep(
  steps: ContextTraceStep[],
  phase: ContextTraceStep["phase"],
  action: string,
  recordIds: string[],
  detail?: string,
): void {
  steps.push({
    sequence: steps.length,
    phase,
    action,
    recordIds,
    ...(detail ? { detail } : {}),
  });
}

function invalidRequestReason(
  request: ContextRequestV2,
  route: RouteDefinition,
): string | undefined {
  if (
    !request.requestId ||
    !request.workspaceId ||
    !request.branchId ||
    !request.taskFamily
  )
    return "request identity and world scope are required";
  if (!request.agentDefinitionRef || !request.taskRef || !request.objective)
    return "agent, task, and objective are required";
  const budgetValues = Object.values(request.budget);
  if (budgetValues.some((value) => !Number.isInteger(value)))
    return "all context budgets must be integers";
  if (request.budget.maximumRecords < 1)
    return "maximumRecords must be positive";
  if (request.budget.maximumCompilerStages < 0)
    return "maximumCompilerStages must be non-negative";
  if (
    request.budget.maximumSemanticCandidates < 1 ||
    request.budget.maximumSemanticCandidates > 30
  )
    return "maximumSemanticCandidates must be between 1 and 30";
  if (
    request.budget.maximumGraphEdges < 0 ||
    request.budget.maximumGraphEdges > 100
  )
    return "maximumGraphEdges must be between 0 and 100";
  if (
    request.budget.maximumGraphHops < 0 ||
    request.budget.maximumGraphHops > 2
  )
    return "maximumGraphHops must be between 0 and 2";
  if (request.taskFamily !== route.taskFamily)
    return "route does not serve the requested task family";
  if (request.sufficiencyPolicyRef !== route.sufficiencyPolicy.id)
    return "request sufficiency policy does not match the selected route";
  if (
    !request.agentRoles.some((role) => route.eligibleAgentRoles.includes(role))
  )
    return "agent is not eligible for this route";
  if (!Number.isFinite(Date.parse(request.compiledAt)))
    return "compiledAt must be an ISO-compatible timestamp";
  return undefined;
}

interface EmptyOptions {
  exclusions?: ContextRunTraceV2["exclusions"];
  missingAuthorityGrantRefs?: string[];
  authorityRejections?: AuthorityGrantRejection[];
  resolvedAuthorityGrants?: readonly ResolvedAuthorityGrant[];
}

function emptyResult(
  records: readonly WorldV3Record[],
  request: ContextRequestV2,
  route: RouteDefinition,
  status: RouteEvaluation["status"],
  stopReason: RouteEvaluation["stopReason"],
  omissions: string[],
  steps: ContextTraceStep[],
  options: EmptyOptions = {},
): ContextPacketV2 {
  addStep(steps, "stop", stopReason, [], omissions.join("; "));
  const evaluation: RouteEvaluation = {
    routeId: route.id,
    routeVersion: route.version,
    status,
    checks: [],
    selectedRecordCount: 0,
    expansionCount: 0,
    budgetExhausted: false,
    unresolvedConflictIds: [],
    staleEvidenceIds: [],
    missingAuthorityGrantRefs: options.missingAuthorityGrantRefs ?? [],
    authorityRejections: options.authorityRejections ?? [],
    stopReason,
  };
  const packetCore = {
    version: 2 as const,
    status,
    request,
    routeRef: `${route.id}@${route.version}`,
    records: [] as WorldV3Record[],
    recordIds: [] as string[],
    evidenceIds: [] as string[],
    citations: [] as ContextCitation[],
    unresolvedConflictIds: [] as string[],
    omissions,
    instructions: [] as string[],
    evaluation,
  };
  const packetHash = contextDigest(packetCore);
  const trace: ContextRunTraceV2 = {
    version: 2,
    requestId: request.requestId,
    routeRef: packetCore.routeRef,
    inputFingerprint: contextDigest({
      records,
      request,
      route,
      resolvedAuthorityGrants: options.resolvedAuthorityGrants ?? [],
    }),
    steps,
    exclusions: options.exclusions ?? [],
    selectedRecordIds: [],
    selectedRecordVersions: [],
    expansions: [],
    omissions,
    stopReason,
    packetHash,
  };
  return { ...packetCore, packetId: `context:${packetHash}`, trace };
}

/**
 * Return a traceable, non-success result when a derived retrieval layer cannot
 * be safely used. No derived result is ever treated as an ordinary no-hit.
 */
export function compileContextV2StaleProjection(
  request: ContextRequestV2,
  route: RouteDefinition,
  resolvedAuthorityGrants: readonly ResolvedAuthorityGrant[] = [],
): ContextPacketV2 {
  return emptyResult(
    [],
    request,
    route,
    "stale",
    "gate_failure",
    ["semantic projection is not current for the pinned canonical snapshot"],
    [],
    { resolvedAuthorityGrants },
  );
}

function evaluateSufficiency(
  selected: readonly WorldV3Record[],
  route: RouteDefinition,
): SufficiencyCheck[] {
  const requirements: SufficiencyRequirement[] = [
    ...route.sufficiencyPolicy.requirements,
    ...route.requiredSemanticKinds
      .filter(
        (kind) =>
          !route.sufficiencyPolicy.requirements.some(
            (requirement) => requirement.kind === kind,
          ),
      )
      .map((kind) => ({ kind, minimum: 1 })),
  ];
  const checks = requirements.map((requirement): SufficiencyCheck => {
    const matching = selected.filter(
      (record) => record.kind === requirement.kind,
    );
    const usable = requirement.mustHaveEvidence
      ? matching.filter((record) => recordEvidenceIds(record).length > 0)
      : matching;
    return {
      id: `kind:${requirement.kind}`,
      passed: usable.length >= requirement.minimum,
      expected: `at least ${requirement.minimum} ${requirement.kind} record(s)${requirement.mustHaveEvidence ? " with evidence" : ""}`,
      observed: `${usable.length}`,
    };
  });
  for (const moduleId of route.sufficiencyPolicy.requiredModuleIds ?? []) {
    const count = selected.filter(
      (record) => record.moduleId === moduleId,
    ).length;
    checks.push({
      id: `module:${moduleId}`,
      passed: count > 0,
      expected: "at least one selected record",
      observed: `${count}`,
    });
  }
  if (route.sufficiencyPolicy.minimumEvidenceRecords !== undefined) {
    const count = selected.filter(
      (record) => record.kind === "evidence",
    ).length;
    checks.push({
      id: "evidence:minimum",
      passed: count >= route.sufficiencyPolicy.minimumEvidenceRecords,
      expected: `at least ${route.sufficiencyPolicy.minimumEvidenceRecords} evidence record(s)`,
      observed: `${count}`,
    });
  }
  return checks;
}

export function compileContextV2(
  inputRecords: readonly WorldV3Record[],
  request: ContextRequestV2,
  route: RouteDefinition,
  resolvedAuthorityGrants: readonly ResolvedAuthorityGrant[] = [],
): ContextPacketV2 {
  const steps: ContextTraceStep[] = [];
  const invalid = invalidRequestReason(request, route);
  if (invalid) {
    addStep(steps, "validate", "request-rejected", [], invalid);
    return emptyResult(
      inputRecords,
      request,
      route,
      "hold",
      "gate_failure",
      [invalid],
      steps,
    );
  }
  addStep(steps, "validate", "request-and-route-accepted", []);
  const authority = evaluateResolvedAuthority(
    request,
    route,
    resolvedAuthorityGrants,
  );
  if (!authority.authorized) {
    const detail = authority.rejections
      .map((item) => `${item.grantRef}:${item.reason}`)
      .join(", ");
    addStep(steps, "gate", "authority-gate-failed", [], detail);
    return emptyResult(
      inputRecords,
      request,
      route,
      "unauthorized",
      "authority_failure",
      authority.rejections.map(
        (item) => `authority ${item.grantRef}: ${item.detail}`,
      ),
      steps,
      {
        missingAuthorityGrantRefs: authority.missingGrantRefs,
        authorityRejections: authority.rejections,
        resolvedAuthorityGrants,
      },
    );
  }
  addStep(steps, "gate", "authority-gate-passed", authority.acceptedGrantRefs);

  const exclusions: Array<{
    recordId: string;
    reason: TraceExclusionReason;
  }> = [];
  const scoped: WorldV3Record[] = [];
  for (const record of inputRecords) {
    let reason: TraceExclusionReason | undefined;
    if (!record.schemaVersion.startsWith("3.")) reason = "not_v3";
    else if (record.workspaceId !== request.workspaceId)
      reason = "wrong_workspace";
    else if (record.branchId !== request.branchId) reason = "wrong_branch";
    else if (
      !request.permittedLifecycleStatuses.includes(record.lifecycleStatus)
    )
      reason = "lifecycle";
    else if (
      record.kind === "claim" &&
      record.permittedTaskTypes.length &&
      !record.permittedTaskTypes.includes(request.taskFamily)
    )
      reason = "task_permission";
    else if (
      request.scope.perspectiveRefs?.length &&
      record.kind === "claim" &&
      record.perspectiveId &&
      !request.scope.perspectiveRefs.includes(record.perspectiveId)
    )
      reason = "perspective";
    else if (!hasContextOverlap(record, request.scope.contextRefs))
      reason = "context";
    else if (outsideInterval(record.validTime, request.scope.validAt))
      reason = "valid_time";
    else if (
      record.authorityRef &&
      !request.authorityGrantRefs.includes(record.authorityRef)
    )
      reason = "authority";
    else if (
      record.kind === "relation" &&
      route.allowedRelationTypeIds.length &&
      (!record.relationTypeId ||
        !route.allowedRelationTypeIds.includes(record.relationTypeId))
    )
      reason = "relation_family";
    else scoped.push(record);
    if (reason) exclusions.push({ recordId: record.id, reason });
  }
  addStep(
    steps,
    "scope",
    "v3-workspace-branch-and-gates",
    scoped.map((record) => record.id),
  );
  if (!scoped.length) {
    const unauthorized = exclusions.some((item) => item.reason === "authority");
    return emptyResult(
      inputRecords,
      request,
      route,
      unauthorized ? "unauthorized" : "no_hit",
      unauthorized ? "authority_failure" : "no_candidates",
      [
        unauthorized
          ? "matching records require authority not present in the request"
          : "no v3 records matched the requested world scope",
      ],
      steps,
      { exclusions },
    );
  }

  const byId = new Map(scoped.map((record) => [record.id, record]));
  const selected = new Map<string, WorldV3Record>();
  const expansions: ExpansionStage[] = [];
  let expansionCount = 0;
  let budgetExhausted = false;
  const addCandidates = (
    stage: ExpansionStage,
    candidates: readonly WorldV3Record[],
  ): void => {
    if (stage !== "foundation") {
      if (expansionCount >= request.budget.maximumCompilerStages) return;
      expansionCount += 1;
      expansions.push(stage);
    }
    const added: string[] = [];
    for (const record of sorted(candidates)) {
      if (selected.has(record.id)) continue;
      if (selected.size >= request.budget.maximumRecords) {
        budgetExhausted = true;
        exclusions.push({ recordId: record.id, reason: "budget" });
      } else {
        selected.set(record.id, record);
        added.push(record.id);
      }
    }
    addStep(steps, stage === "foundation" ? "select" : "expand", stage, added);
  };

  const startModules = request.scope.moduleIds?.length
    ? request.scope.moduleIds
    : route.startModuleIds;
  const seeds = new Set(request.scope.seedRecordIds ?? []);
  addCandidates(
    "foundation",
    scoped.filter(
      (record) =>
        seeds.has(record.id) ||
        (FOUNDATION_KINDS.has(record.kind) &&
          (!startModules.length ||
            Boolean(
              record.moduleId && startModules.includes(record.moduleId),
            ))),
    ),
  );
  const desiredStageRank: Record<
    ContextRequestV2["desiredAbstraction"],
    number
  > = {
    overview: 0,
    working: 1,
    evidence: 2,
    history: 3,
  };
  const expansionRank: Record<Exclude<ExpansionStage, "foundation">, number> = {
    roads: 1,
    evidence: 2,
    history: 3,
  };
  for (const stage of route.abstractionOrder.filter(
    (candidate) => candidate !== "foundation",
  )) {
    const stageRank = expansionRank[stage];
    const trigger =
      stage === "roads"
        ? "missing_kind"
        : stage === "evidence"
          ? "missing_evidence"
          : "history_requested";
    if (
      stageRank > desiredStageRank[request.desiredAbstraction] ||
      !route.expansionTriggers.includes(trigger)
    )
      continue;
    const currentIds = new Set(selected.keys());
    let candidates: WorldV3Record[];
    if (stage === "roads") {
      const roads = scoped.filter(
        (record) =>
          record.kind === "relation" &&
          (!route.allowedRelationTypeIds.length ||
            Boolean(
              record.relationTypeId &&
                route.allowedRelationTypeIds.includes(record.relationTypeId),
            )) &&
          recordReferences(record).some((ref) => currentIds.has(ref)),
      );
      const connectedIds = new Set(roads.flatMap(recordReferences));
      candidates = [
        ...roads,
        ...scoped.filter((record) => connectedIds.has(record.id)),
      ];
    } else if (stage === "evidence") {
      const evidenceIds = new Set(
        [...selected.values()].flatMap(recordReferences),
      );
      const evidence = scoped.filter(
        (record) => record.kind === "evidence" && evidenceIds.has(record.id),
      );
      const sourceIds = new Set(evidence.flatMap(recordReferences));
      candidates = [
        ...evidence,
        ...scoped.filter(
          (record) => record.kind === "source" && sourceIds.has(record.id),
        ),
      ];
    } else {
      const historyIds = new Set<string>();
      for (const record of selected.values())
        if (record.supersedesRef) historyIds.add(record.supersedesRef);
      candidates = scoped.filter(
        (record) =>
          historyIds.has(record.id) ||
          Boolean(record.supersedesRef && currentIds.has(record.supersedesRef)),
      );
    }
    if (candidates.length) addCandidates(stage, candidates);
  }
  for (const record of scoped) {
    if (
      !selected.has(record.id) &&
      !exclusions.some((item) => item.recordId === record.id)
    )
      exclusions.push({ recordId: record.id, reason: "not_reached" });
  }

  const selectedRecords = [...selected.values()];
  const staleEvidenceIds = selectedRecords
    .filter((record) =>
      evidenceIsStale(
        record,
        request.compiledAt,
        route.sufficiencyPolicy.maximumEvidenceAgeDays,
      ),
    )
    .map((record) => record.id);
  const unresolvedConflictIds = unique(
    selectedRecords.flatMap((record) =>
      record.kind === "claim" ? record.contradictionIds : [],
    ),
  );
  const checks = evaluateSufficiency(selectedRecords, route);
  const sufficient = checks.every((check) => check.passed);
  let status: RouteEvaluation["status"];
  let stopReason: RouteEvaluation["stopReason"];
  if (!selectedRecords.length)
    [status, stopReason] = ["no_hit", "no_candidates"];
  else if (
    unresolvedConflictIds.length &&
    route.sufficiencyPolicy.unresolvedConflicts === "hold"
  )
    [status, stopReason] = ["hold", "unresolved_conflict"];
  else if (
    staleEvidenceIds.length &&
    route.mandatoryGates.includes("freshness")
  )
    [status, stopReason] = ["stale", "stale_required_evidence"];
  else if (sufficient && !budgetExhausted)
    [status, stopReason] = ["ready", "sufficient"];
  else
    [status, stopReason] = [
      "partial",
      budgetExhausted ? "budget_exhausted" : "insufficient",
    ];
  addStep(
    steps,
    "evaluate",
    "sufficiency-and-risk",
    selectedRecords.map((record) => record.id),
    checks.map((check) => `${check.id}:${check.passed}`).join(","),
  );
  addStep(
    steps,
    "stop",
    stopReason,
    selectedRecords.map((record) => record.id),
  );

  const evidenceIds = unique([
    ...selectedRecords
      .filter((record) => record.kind === "evidence")
      .map((record) => record.id),
    ...selectedRecords.flatMap(recordEvidenceIds),
  ]);
  const citations: ContextCitation[] = evidenceIds.map((evidenceId) => {
    const evidence = byId.get(evidenceId);
    return {
      evidenceId,
      ...(evidence?.kind === "evidence" ? { sourceId: evidence.sourceId } : {}),
      ...(evidence?.kind === "evidence" ? { locator: evidence.locator } : {}),
    };
  });
  const omissions = [
    ...checks
      .filter((check) => !check.passed)
      .map(
        (check) =>
          `${check.id}: expected ${check.expected}; observed ${check.observed}`,
      ),
    ...(budgetExhausted ? ["context record budget exhausted"] : []),
    ...(staleEvidenceIds.length
      ? [`stale evidence: ${staleEvidenceIds.join(", ")}`]
      : []),
    ...(unresolvedConflictIds.length
      ? [`unresolved conflicts: ${unresolvedConflictIds.join(", ")}`]
      : []),
  ];
  const evaluation: RouteEvaluation = {
    routeId: route.id,
    routeVersion: route.version,
    status,
    checks,
    selectedRecordCount: selectedRecords.length,
    expansionCount,
    budgetExhausted,
    unresolvedConflictIds,
    staleEvidenceIds,
    missingAuthorityGrantRefs: [],
    authorityRejections: [],
    stopReason,
  };
  const packetCore = {
    version: 2 as const,
    status,
    request,
    routeRef: `${route.id}@${route.version}`,
    records: selectedRecords,
    recordIds: selectedRecords.map((record) => record.id),
    evidenceIds,
    citations,
    unresolvedConflictIds,
    omissions,
    instructions: [
      "Use only the selected records within their stated scope, branch, time, and epistemic status.",
      "Cite evidence IDs for material claims; surface omissions and conflicts instead of inventing support.",
    ],
    evaluation,
  };
  const packetHash = contextDigest(packetCore);
  const trace: ContextRunTraceV2 = {
    version: 2,
    requestId: request.requestId,
    routeRef: packetCore.routeRef,
    inputFingerprint: contextDigest({
      records: inputRecords,
      request,
      route,
      resolvedAuthorityGrants,
    }),
    steps,
    exclusions: exclusions.sort(
      (left, right) =>
        left.recordId.localeCompare(right.recordId) ||
        left.reason.localeCompare(right.reason),
    ),
    selectedRecordIds: packetCore.recordIds,
    selectedRecordVersions: selectedRecords.map((record) => ({
      id: record.id,
      recordVersion: record.recordVersion ?? 1,
    })),
    expansions,
    omissions,
    stopReason,
    packetHash,
  };
  return { ...packetCore, packetId: `context:${packetHash}`, trace };
}
