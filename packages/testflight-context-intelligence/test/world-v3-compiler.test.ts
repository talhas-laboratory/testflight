import assert from "node:assert/strict";
import test from "node:test";
import {
  compileContextV2,
  compileContextV2FromProjection,
  compileContextV2FromResolver,
  InMemoryWorldV3RecordResolver,
  replayContextV2,
  WorldV3GraphContextRuntime,
  WorldV3VisualLanguageResolver,
  type ContextRequestV2,
  type ResolvedAuthorityGrant,
  type RouteDefinition,
  type WorldV3Record,
} from "../src/index.js";

const envelope = {
  typeId: "world://ontology/test/record",
  schemaVersion: "3.0.0",
  recordVersion: 1,
  workspaceId: "world://brand/biotic",
  branchId: "client-approved",
  lifecycleStatus: "accepted" as const,
  createdAt: "2026-09-01T00:00:00.000Z",
  createdBy: "test:fixture",
};

const records: WorldV3Record[] = [
  {
    ...envelope,
    id: "entity:biotic",
    kind: "entity",
    moduleId: "identity",
    canonicalLabel: "Biotic",
    aliases: [],
    definition: "A test brand entity.",
  },
  {
    ...envelope,
    id: "entity:deodorant",
    kind: "entity",
    moduleId: "offering",
    canonicalLabel: "Whole-body deodorant",
    aliases: [],
    definition: "A test offering entity.",
  },
  {
    ...envelope,
    id: "claim:microbiome-intent",
    kind: "claim",
    moduleId: "identity",
    evidenceIds: ["evidence:storefront"],
    permittedTaskTypes: ["newsletter"],
    claimKind: "factual_assertion",
    subjectId: "entity:biotic",
    predicateId: "test:frames",
    objectValue: "microbiome-friendly care",
    opposingEvidenceIds: [],
    contradictionIds: [],
    limitations: [],
  },
  {
    ...envelope,
    id: "claim:research-only",
    kind: "claim",
    moduleId: "environment",
    evidenceIds: ["evidence:research"],
    permittedTaskTypes: ["product-research"],
    claimKind: "hypothesis",
    subjectId: "entity:biotic",
    predicateId: "test:researches",
    objectValue: "research topic",
    opposingEvidenceIds: [],
    contradictionIds: [],
    limitations: [],
  },
  {
    ...envelope,
    id: "relation:brand-offers-product",
    kind: "relation",
    moduleId: "offering",
    relationTypeId: "brand-offers-product",
    participants: [
      { roleId: "brand", recordId: "entity:biotic" },
      { roleId: "offering", recordId: "entity:deodorant" },
    ],
    evidenceIds: ["evidence:storefront"],
  },
  {
    ...envelope,
    id: "evidence:storefront",
    kind: "evidence",
    moduleId: "identity",
    sourceId: "source:storefront",
    locator: "https://hellobiotic.com/",
    knownTime: { start: "2026-09-01T00:00:00.000Z" },
    excerpt: "Public storefront evidence.",
    limitations: [],
  },
  {
    ...envelope,
    id: "source:storefront",
    kind: "source",
    moduleId: "identity",
    locator: "https://hellobiotic.com/",
    title: "Biotic storefront",
    contentPolicy: "live_reference_only",
    capturedAt: "2026-09-01T00:00:00.000Z",
  },
  {
    ...envelope,
    id: "evidence:research",
    kind: "evidence",
    moduleId: "environment",
    sourceId: "source:research",
    locator: "repo://research.md",
    excerpt: "Research evidence.",
    limitations: [],
  },
  {
    ...envelope,
    id: "legacy:v2-record",
    kind: "claim",
    moduleId: "identity",
    schemaVersion: "2.0.0",
    claimKind: "factual_assertion",
    subjectId: "entity:biotic",
    predicateId: "test:legacy",
    objectValue: "legacy",
    evidenceIds: [],
    opposingEvidenceIds: [],
    contradictionIds: [],
    limitations: [],
    permittedTaskTypes: [],
  },
];

const route: RouteDefinition = {
  id: "route:biotic-newsletter",
  version: 2,
  taskFamily: "newsletter",
  eligibleAgentRoles: ["creator", "brand-guardian"],
  startModuleIds: ["identity", "offering"],
  requiredSemanticKinds: ["entity", "claim", "evidence"],
  allowedRelationTypeIds: ["brand-offers-product"],
  abstractionOrder: ["foundation", "roads", "evidence"],
  mandatoryGates: [
    "authority",
    "valid_time",
    "lifecycle",
    "freshness",
    "conflict",
  ],
  requiredAuthorityGrantRefs: ["grant:client-approved-read"],
  requiredAuthorityCapabilities: ["world:read"],
  expansionTriggers: ["missing_kind", "missing_evidence", "missing_module"],
  stopConditions: [
    "sufficient",
    "budget_exhausted",
    "no_candidates",
    "gate_failure",
  ],
  sufficiencyPolicy: {
    id: "sufficiency:newsletter",
    requirements: [
      { kind: "entity", minimum: 2 },
      { kind: "claim", minimum: 1, mustHaveEvidence: true },
    ],
    requiredModuleIds: ["identity", "offering"],
    minimumEvidenceRecords: 1,
    maximumEvidenceAgeDays: 30,
    unresolvedConflicts: "hold",
  },
};

const request: ContextRequestV2 = {
  requestId: "request:newsletter-001",
  principalRef: "principal:talha",
  agentDefinitionRef: "agent:creator@1",
  agentRoles: ["creator"],
  taskRef: "task:newsletter-001",
  taskFamily: "newsletter",
  objective:
    "Create a grounded launch newsletter without widening product claims.",
  authorityGrantRefs: ["grant:client-approved-read"],
  workspaceId: envelope.workspaceId,
  branchId: envelope.branchId,
  permittedLifecycleStatuses: ["accepted"],
  scope: { moduleIds: ["identity", "offering"] },
  desiredAbstraction: "evidence",
  sufficiencyPolicyRef: route.sufficiencyPolicy.id,
  budget: {
    maximumRecords: 8,
    maximumCompilerStages: 2,
    maximumSemanticCandidates: 5,
    maximumGraphEdges: 6,
    maximumGraphHops: 2,
  },
  requiredOutputSchema: "artifact:newsletter-brief@1",
  compiledAt: "2026-09-14T00:00:00.000Z",
};

const authorityGrants: ResolvedAuthorityGrant[] = [
  {
    id: "grant:client-approved-read",
    status: "active",
    principalRef: "principal:talha",
    agentDefinitionRef: "agent:creator@1",
    capabilities: ["world:read"],
    scope: { workspaceId: envelope.workspaceId },
    validFrom: "2026-09-01T00:00:00.000Z",
    validUntil: "2026-10-01T00:00:00.000Z",
  },
];

test("newsletter route compiles high-level records before roads and evidence", () => {
  const packet = compileContextV2(records, request, route, authorityGrants);
  assert.equal(packet.status, "ready");
  assert.deepEqual(packet.trace.expansions, ["roads", "evidence"]);
  assert.deepEqual(
    packet.trace.steps
      .filter((step) => step.phase === "select")
      .map((step) => step.action),
    ["foundation"],
  );
  assert.ok(
    packet.recordIds.indexOf("entity:biotic") <
      packet.recordIds.indexOf("evidence:storefront"),
  );
  assert.ok(packet.recordIds.includes("relation:brand-offers-product"));
  assert.deepEqual(packet.citations, [
    {
      evidenceId: "evidence:storefront",
      sourceId: "source:storefront",
      locator: "https://hellobiotic.com/",
    },
  ]);
  assert.ok(!packet.recordIds.includes("legacy:v2-record"));
  assert.ok(
    packet.trace.exclusions.some(
      (item) =>
        item.recordId === "legacy:v2-record" && item.reason === "not_v3",
    ),
  );
});

test("same world gives explainable authority and agent route failures", () => {
  const unauthorized = compileContextV2(
    records,
    { ...request, authorityGrantRefs: [] },
    route,
    authorityGrants,
  );
  assert.equal(unauthorized.status, "unauthorized");
  assert.equal(unauthorized.evaluation.stopReason, "authority_failure");
  assert.deepEqual(unauthorized.evaluation.missingAuthorityGrantRefs, [
    "grant:client-approved-read",
  ]);

  const ineligible = compileContextV2(
    records,
    { ...request, agentRoles: ["researcher"] },
    route,
    authorityGrants,
  );
  assert.equal(ineligible.status, "hold");
  assert.match(ineligible.omissions[0] ?? "", /not eligible/);

  const wrongPolicy = compileContextV2(
    records,
    { ...request, sufficiencyPolicyRef: "sufficiency:other" },
    route,
    authorityGrants,
  );
  assert.equal(wrongPolicy.status, "hold");
  assert.match(wrongPolicy.omissions[0] ?? "", /does not match/);
});

test("grant references cannot spoof resolved authority", () => {
  const baseGrant = authorityGrants[0];
  assert.ok(baseGrant);
  const cases: Array<{
    label: string;
    grants: ResolvedAuthorityGrant[];
    reason:
      | "unknown_grant"
      | "expired"
      | "wrong_principal"
      | "wrong_agent"
      | "wrong_capability"
      | "wrong_workspace"
      | "wrong_module_scope"
      | "wrong_object_scope"
      | "wrong_context_scope";
  }> = [
    { label: "unknown", grants: [], reason: "unknown_grant" },
    {
      label: "expired",
      grants: [{ ...baseGrant, validUntil: "2026-09-10T00:00:00.000Z" }],
      reason: "expired",
    },
    {
      label: "wrong principal",
      grants: [{ ...baseGrant, principalRef: "principal:other" }],
      reason: "wrong_principal",
    },
    {
      label: "wrong capability",
      grants: [{ ...baseGrant, capabilities: ["world:propose"] }],
      reason: "wrong_capability",
    },
    {
      label: "wrong agent",
      grants: [{ ...baseGrant, agentDefinitionRef: "agent:researcher@1" }],
      reason: "wrong_agent",
    },
    {
      label: "wrong workspace",
      grants: [{ ...baseGrant, scope: { workspaceId: "world://brand/other" } }],
      reason: "wrong_workspace",
    },
    {
      label: "wrong module scope",
      grants: [
        {
          ...baseGrant,
          scope: {
            workspaceId: envelope.workspaceId,
            moduleIds: ["environment"],
          },
        },
      ],
      reason: "wrong_module_scope",
    },
    {
      label: "wrong object scope",
      grants: [
        {
          ...baseGrant,
          scope: {
            workspaceId: envelope.workspaceId,
            objectIds: ["entity:other"],
          },
        },
      ],
      reason: "wrong_object_scope",
    },
    {
      label: "wrong context scope",
      grants: [
        {
          ...baseGrant,
          scope: {
            workspaceId: envelope.workspaceId,
            contextRefs: ["context:private"],
          },
        },
      ],
      reason: "wrong_context_scope",
    },
  ];
  for (const scenario of cases) {
    const packet = compileContextV2(records, request, route, scenario.grants);
    assert.equal(packet.status, "unauthorized", scenario.label);
    assert.deepEqual(packet.recordIds, [], scenario.label);
    assert.equal(
      packet.evaluation.authorityRejections[0]?.reason,
      scenario.reason,
      scenario.label,
    );
    assert.equal(
      packet.trace.steps.some(
        (step) =>
          step.action === "authority-gate-failed" &&
          step.detail?.includes(scenario.reason),
      ),
      true,
      scenario.label,
    );
  }
});

test("wrong branch is a no-hit and never falls back to another branch", () => {
  const packet = compileContextV2(
    records,
    { ...request, branchId: "public-research" },
    route,
    authorityGrants,
  );
  assert.equal(packet.status, "no_hit");
  assert.equal(packet.recordIds.length, 0);
  assert.ok(
    packet.trace.exclusions.some((item) => item.reason === "wrong_branch"),
  );
  assert.ok(
    packet.trace.exclusions.every(
      (item) => item.reason === "wrong_branch" || item.reason === "not_v3",
    ),
  );
});

test("budget exhaustion returns a partial packet with the named insufficiency", () => {
  const packet = compileContextV2(
    records,
    { ...request, budget: { ...request.budget, maximumRecords: 2 } },
    route,
    authorityGrants,
  );
  assert.equal(packet.status, "partial");
  assert.equal(packet.evaluation.budgetExhausted, true);
  assert.equal(packet.evaluation.stopReason, "budget_exhausted");
  assert.ok(packet.omissions.includes("context record budget exhausted"));
});

test("stale required evidence and unresolved conflicts are explicit non-success states", () => {
  const staleRecords = records.map((record) =>
    record.id === "evidence:storefront"
      ? { ...record, knownTime: { start: "2025-01-01T00:00:00.000Z" } }
      : record,
  );
  const stale = compileContextV2(staleRecords, request, route, authorityGrants);
  assert.equal(stale.status, "stale");
  assert.deepEqual(stale.evaluation.staleEvidenceIds, ["evidence:storefront"]);

  const conflictedRecords = records.map((record) =>
    record.id === "claim:microbiome-intent"
      ? { ...record, contradictionIds: ["claim:contradiction"] }
      : record,
  );
  const conflicted = compileContextV2(
    conflictedRecords,
    request,
    route,
    authorityGrants,
  );
  assert.equal(conflicted.status, "hold");
  assert.equal(conflicted.evaluation.stopReason, "unresolved_conflict");
});

test("trace replay is exact and detects changed record versions", () => {
  const original = compileContextV2(records, request, route, authorityGrants);
  const exact = replayContextV2(
    records,
    request,
    route,
    original.trace,
    authorityGrants,
  );
  assert.equal(exact.exact, true);
  assert.deepEqual(exact.differences, []);

  const changed = records.map((record) =>
    record.id === "entity:biotic" ? { ...record, recordVersion: 2 } : record,
  );
  const replayed = replayContextV2(
    changed,
    request,
    route,
    original.trace,
    authorityGrants,
  );
  assert.equal(replayed.exact, false);
  assert.ok(replayed.differences.includes("input fingerprint changed"));
  assert.ok(replayed.differences.includes("selected record versions changed"));

  const grantDrift = replayContextV2(records, request, route, original.trace, [
    { ...authorityGrants[0]!, validUntil: "2026-09-20T00:00:00.000Z" },
  ]);
  assert.equal(grantDrift.exact, false);
  assert.ok(grantDrift.differences.includes("input fingerprint changed"));
});

test("world and visual-language resolvers expose v3 records only", async () => {
  const expression: WorldV3Record = {
    ...envelope,
    id: "entity:visual-language",
    kind: "entity",
    moduleId: "expression-manifestation",
    canonicalLabel: "Visual language",
    aliases: [],
    definition: "A test visual-language entity.",
  };
  const legacyExpression: WorldV3Record = {
    ...expression,
    id: "legacy:visual-language",
    schemaVersion: "2.0.0",
  };
  const resolver = new InMemoryWorldV3RecordResolver([
    ...records,
    expression,
    legacyExpression,
  ]);
  const visual = await new WorldV3VisualLanguageResolver(resolver).resolve({
    workspaceId: envelope.workspaceId,
    branchId: envelope.branchId,
  });
  assert.deepEqual(
    visual.map((record) => record.id),
    ["entity:visual-language"],
  );

  const packet = await compileContextV2FromResolver(
    resolver,
    request,
    route,
    authorityGrants,
  );
  assert.equal(packet.status, "ready");
  assert.ok(!packet.trace.exclusions.some((item) => item.reason === "not_v3"));
});

test("projection retrieval hydrates canonical records and discards inferred edges", async () => {
  const packet = await compileContextV2FromProjection(
    {
      async retrieve() {
        return {
          canonicalSnapshotRoot: "a".repeat(64),
          projectionSnapshotRoot: "a".repeat(64),
          freshness: "exact" as const,
          candidates: [
            {
              recordId: "entity:biotic",
              recordVersion: 1,
              canonicalRecordHash: "b".repeat(64),
              score: 1,
              retrievalMethod: "semantic" as const,
              matchedFields: ["canonicalLabel"],
            },
          ],
          edges: [
            {
              sourceRecordId: "entity:biotic",
              targetRecordId: "entity:deodorant",
              predicate: "offers",
              edgeClass: "inferred_relation" as const,
            },
          ],
          retrievalMethods: ["semantic"],
        };
      },
    },
    {
      async hydrate() {
        return records;
      },
    },
    request,
    route,
    authorityGrants,
  );
  assert.equal(packet.status, "ready");
  assert.equal(packet.trace.projectionRetrieval?.discardedEdgeCount, 1);
  assert.equal(
    packet.trace.projectionRetrieval?.hydratedRecordIds.length,
    records.length,
  );
});

test("projection discovery receives independent scope and traversal budgets", async () => {
  let discoveryRequest: Record<string, unknown> | undefined;
  await compileContextV2FromProjection(
    {
      async retrieve(value) {
        discoveryRequest = value as unknown as Record<string, unknown>;
        return {
          canonicalSnapshotRoot: "a".repeat(64),
          projectionSnapshotRoot: "a".repeat(64),
          freshness: "exact" as const,
          candidates: [],
          edges: [],
          retrievalMethods: ["semantic"],
        };
      },
    },
    {
      async hydrate() {
        return [];
      },
    },
    request,
    route,
    authorityGrants,
  );

  assert.deepEqual(discoveryRequest, {
    workspaceId: request.workspaceId,
    branchId: request.branchId,
    permittedLifecycleStatuses: request.permittedLifecycleStatuses,
    objective: request.objective,
    moduleIds: request.scope.moduleIds,
    maximumSemanticCandidates: 5,
    maximumGraphEdges: 6,
    maximumGraphHops: 2,
    allowedRelationTypeIds: route.allowedRelationTypeIds,
  });
});

test("projection retrieval hydrates bounded canonical graph neighbors", async () => {
  let hydratedIds: readonly string[] = [];
  await compileContextV2FromProjection(
    {
      async retrieve() {
        return {
          canonicalSnapshotRoot: "a".repeat(64),
          projectionSnapshotRoot: "a".repeat(64),
          freshness: "exact" as const,
          candidates: [
            {
              recordId: "claim:microbiome-intent",
              recordVersion: 1,
              canonicalRecordHash: "b".repeat(64),
              score: 1,
              retrievalMethod: "semantic" as const,
              matchedFields: ["indexText"],
            },
          ],
          edges: [
            {
              sourceRecordId: "entity:biotic",
              targetRecordId: "entity:deodorant",
              predicate: "HAS_PARTICIPANT",
              edgeClass: "canonical_relation" as const,
              canonicalRelationId: "relation:brand-offers-product",
              canonicalRelationHash: "c".repeat(64),
            },
          ],
          retrievalMethods: ["semantic", "structural"],
        };
      },
    },
    {
      async hydrate(query) {
        hydratedIds = query.recordIds ?? [];
        return records;
      },
    },
    request,
    route,
    authorityGrants,
  );
  assert.deepEqual(hydratedIds, [
    "claim:microbiome-intent",
    "relation:brand-offers-product",
    "entity:biotic",
    "entity:deodorant",
  ]);
});

test("a stale projection is an explicit gate failure, not a no-hit", async () => {
  let hydrated = false;
  const packet = await compileContextV2FromProjection(
    {
      async retrieve() {
        return {
          canonicalSnapshotRoot: "a".repeat(64),
          projectionSnapshotRoot: "b".repeat(64),
          freshness: "stale" as const,
          candidates: [],
          edges: [],
          retrievalMethods: ["semantic"],
        };
      },
    },
    {
      async hydrate() {
        hydrated = true;
        return records;
      },
    },
    request,
    route,
    authorityGrants,
  );
  assert.equal(packet.status, "stale");
  assert.equal(packet.evaluation.stopReason, "gate_failure");
  assert.equal(hydrated, false);
  assert.equal(packet.trace.projectionRetrieval?.freshness, "stale");
});

test("graph context runtime pins one canonical snapshot for discovery and hydration", async () => {
  const snapshotRoot = "c".repeat(64);
  let readerRoot: string | undefined;
  let hydrationRoot: string | undefined;
  const runtime = new WorldV3GraphContextRuntime(
    {
      async pin() {
        return { snapshotRoot };
      },
    },
    (root) => {
      readerRoot = root;
      return {
        async retrieve() {
          return {
            canonicalSnapshotRoot: root,
            projectionSnapshotRoot: root,
            freshness: "exact" as const,
            candidates: [
              {
                recordId: "entity:biotic",
                recordVersion: 1,
                canonicalRecordHash: "d".repeat(64),
                score: 1,
                retrievalMethod: "semantic" as const,
                matchedFields: ["canonicalLabel"],
              },
            ],
            edges: [],
            retrievalMethods: ["semantic"],
          };
        },
      };
    },
    {
      async hydrate(query) {
        hydrationRoot = query.snapshotRoot;
        return records;
      },
    },
  );

  const packet = await runtime.compile(request, route, authorityGrants);
  assert.equal(packet.status, "ready");
  assert.equal(readerRoot, snapshotRoot);
  assert.equal(hydrationRoot, snapshotRoot);
  assert.equal(
    packet.trace.projectionRetrieval?.canonicalSnapshotRoot,
    snapshotRoot,
  );
});

test("graph context runtime rejects unauthorized requests before snapshot pinning", async () => {
  let pinCalls = 0;
  const runtime = new WorldV3GraphContextRuntime(
    {
      async pin() {
        pinCalls += 1;
        return { snapshotRoot: "e".repeat(64) };
      },
    },
    () => {
      throw new Error("projection reader must not be created");
    },
    {
      async hydrate() {
        throw new Error("hydrator must not be called");
      },
    },
  );
  const packet = await runtime.compile(
    { ...request, authorityGrantRefs: [] },
    route,
    [],
  );
  assert.equal(packet.status, "unauthorized");
  assert.equal(pinCalls, 0);
});
