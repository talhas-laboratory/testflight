import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import {
  ContextIntelligenceEngine,
  JsonFileContextTraceStore,
  JsonVisualLanguageResolver,
  type ContextTraceEvent,
  type ContextTraceHeader,
  type ContextRunTrace,
  type ContextTraceStore,
  filterRetrievedKnowledge,
  matchContextActivation,
  type IntelligenceConfiguration,
  type IntelligenceModel,
  type KnowledgeRetriever,
  type RetrievedKnowledge,
  type TraceEvidenceReference,
  type VisualLanguageManifest,
  type WorldViewResolver,
} from "../src/index.js";

const configuration: IntelligenceConfiguration = {
  version: 1,
  workspaceId: "world://workspace/brand/example",
  brandId: "world://brand/example",
  datasetName: "example_staging",
  subjectScope: "Example Brand",
  retrieval: {
    topK: 5,
    maximumQueries: 2,
    navigationSourcePatterns: ["agent_index", "agent_config"],
  },
  activation: {
    actionTerms: ["create", "review"],
    domainTerms: ["brand", "campaign", "asset"],
  },
  workflows: [
    {
      stage: "brief",
      goal: "Bound the brief",
      route: "asset-context",
      requiredInputs: ["assetType", "objective", "audience"],
      queryHints: ["identity audience"],
      reasoningInstructions: ["Separate intent from perception."],
    },
  ],
  sections: ["identity", "audience", "evidence"],
  operators: ["world://operator/guardrail/workspace-isolation@1"],
};

test("automatic behavior needs both an action and domain term", () => {
  assert.equal(
    matchContextActivation("Create a campaign asset", configuration).activate,
    true,
  );
  assert.equal(
    matchContextActivation("Create a Python parser", configuration).activate,
    false,
  );
  assert.equal(
    matchContextActivation("Tell me about the brand", configuration).activate,
    false,
  );
});

test("basic filter rejects obvious boundary failures and keeps plausible evidence", () => {
  const result = filterRetrievedKnowledge(
    [
      {
        id: "good",
        text: "Grounded fact",
        sourceUrl: "repo://evidence.md",
        workspaceId: configuration.workspaceId,
        brandId: configuration.brandId,
      },
      { id: "index", text: "routes", sourceUrl: "repo://AGENT_INDEX.md" },
      {
        id: "foreign",
        text: "other",
        sourceUrl: "repo://other.md",
        workspaceId: "other",
      },
      { id: "orphan", text: "no source" },
    ],
    { prompt: "x", workspaceId: configuration.workspaceId },
    configuration,
  );
  assert.deepEqual(
    result.accepted.map((item) => item.id),
    ["good"],
  );
  assert.deepEqual(
    result.rejected.map((item) => item.reason),
    [
      "navigation or configuration document",
      "wrong workspace",
      "missing source anchor",
    ],
  );
});

test("filter excludes explicit branch and perspective mismatches while keeping shared evidence", () => {
  const result = filterRetrievedKnowledge(
    [
      {
        id: "matching",
        text: "Scenario evidence",
        sourceUrl: "repo://scenario.md",
        workspaceId: configuration.workspaceId,
        branchId: "branch:confidence",
        perspectiveIds: ["perspective:customer"],
      },
      {
        id: "wrong-branch",
        text: "Other scenario",
        sourceUrl: "repo://scenario.md",
        workspaceId: configuration.workspaceId,
        branchId: "branch:performance",
      },
      {
        id: "wrong-perspective",
        text: "Internal-only interpretation",
        sourceUrl: "repo://perspective.md",
        workspaceId: configuration.workspaceId,
        perspectiveIds: ["perspective:finance"],
      },
      {
        id: "shared",
        text: "Shared observation",
        sourceUrl: "repo://evidence.md",
        workspaceId: configuration.workspaceId,
      },
    ],
    {
      prompt: "x",
      workspaceId: configuration.workspaceId,
      branchId: "branch:confidence",
      perspectiveIds: ["perspective:customer"],
    },
    configuration,
  );

  assert.deepEqual(
    result.accepted.map((item) => item.id),
    ["matching", "shared"],
  );
  assert.deepEqual(
    result.rejected.map((item) => item.reason),
    ["wrong branch", "wrong perspective"],
  );
});

test("filter treats an explicit main branch as a real branch boundary", () => {
  const result = filterRetrievedKnowledge(
    [
      {
        id: "main",
        text: "Main-branch interpretation",
        sourceUrl: "repo://main.md",
        workspaceId: configuration.workspaceId,
        branchId: "main",
      },
      {
        id: "child",
        text: "Scenario-only interpretation",
        sourceUrl: "repo://child.md",
        workspaceId: configuration.workspaceId,
        branchId: "branch:scenario",
      },
      {
        id: "shared",
        text: "Shared observation",
        sourceUrl: "repo://shared.md",
        workspaceId: configuration.workspaceId,
      },
    ],
    { prompt: "x", workspaceId: configuration.workspaceId, branchId: "main" },
    configuration,
  );

  assert.deepEqual(
    result.accepted.map((item) => item.id),
    ["main", "shared"],
  );
  assert.deepEqual(
    result.rejected.map((item) => item.reason),
    ["wrong branch"],
  );
});

class FakeModel implements IntelligenceModel {
  readonly id = "separate-test-model";
  async completeJson(input: {
    purpose: "interpret" | "synthesize";
  }): Promise<unknown> {
    if (input.purpose === "interpret") return { workflowStage: "brief" };
    return {
      knowledge: {
        identity: [
          {
            statement: "Example has a grounded identity.",
            evidenceIds: ["e1"],
          },
        ],
      },
      conflicts: [],
      limitations: ["Public evidence only."],
      omissions: [],
    };
  }
}

class FakeRetriever implements KnowledgeRetriever {
  async retrieve() {
    return [
      {
        id: "e1",
        text: "Example identity evidence",
        sourceUrl: "repo://evidence.md",
        workspaceId: configuration.workspaceId,
        brandId: configuration.brandId,
      },
    ];
  }
}

class CapturingTraceStore implements ContextTraceStore {
  header: ContextTraceHeader | undefined;
  events: ContextTraceEvent[] = [];
  evidence: Record<string, RetrievedKnowledge> = {};

  async start(header: ContextTraceHeader) {
    this.header = header;
  }

  async append(_runId: string, event: ContextTraceEvent) {
    this.events.push({ ...event, sequence: this.events.length });
  }

  async putEvidence(
    _runId: string,
    item: RetrievedKnowledge,
  ): Promise<TraceEvidenceReference> {
    const hash = `hash-${item.id}`;
    this.evidence[hash] = item;
    return {
      hash,
      retrievalId: item.id,
      ...(item.sourceUrl ? { sourceUrl: item.sourceUrl } : {}),
      entityIds: item.entityIds ?? [],
    };
  }

  async read(_runId: string): Promise<ContextRunTrace> {
    assert.ok(this.header);
    return {
      header: this.header,
      events: this.events,
      evidence: this.evidence,
    };
  }
}

test("engine asks for only material missing workflow inputs", async () => {
  const engine = new ContextIntelligenceEngine(
    configuration,
    new FakeModel(),
    new FakeRetriever(),
  );
  const packet = await engine.compile(
    { prompt: "Create a brand asset" },
    { activationReason: "explicit" },
  );
  assert.equal(packet.status, "needs_clarification");
  assert.deepEqual(packet.unresolvedFields, [
    "assetType",
    "objective",
    "audience",
  ]);
  assert.equal(packet.receipt.intelligenceModel, "separate-test-model");
});

test("engine returns a cited packet and derivation receipt", async () => {
  const engine = new ContextIntelligenceEngine(
    configuration,
    new FakeModel(),
    new FakeRetriever(),
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
    },
    { activationReason: "automatic" },
  );
  assert.equal(packet.status, "ready");
  assert.equal(packet.knowledge.identity?.[0]?.evidenceIds[0], "e1");
  assert.deepEqual(packet.citations, [
    { evidenceId: "e1", sourceUrl: "repo://evidence.md" },
  ]);
  assert.equal(packet.receipt.activationReason, "automatic");
  assert.equal(packet.receipt.datasetName, "example_staging");
});

test("engine preserves explicit branch and perspective selection for later world-view resolution", async () => {
  const engine = new ContextIntelligenceEngine(
    configuration,
    new FakeModel(),
    new FakeRetriever(),
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
      branchId: "branch:confidence-first",
      perspectiveIds: ["perspective:customer", "perspective:customer"],
    },
    { activationReason: "automatic" },
  );

  assert.equal(packet.request.branchId, "branch:confidence-first");
  assert.deepEqual(packet.request.perspectiveIds, ["perspective:customer"]);
  assert.equal(packet.receipt.worldView?.status, "not_resolved");
  assert.equal(packet.receipt.worldView?.branchId, "branch:confidence-first");
});

test("engine injects a resolved world view before evidence synthesis when a resolver is configured", async () => {
  let synthesisPayload: unknown;
  const resolver: WorldViewResolver = {
    resolve(request) {
      assert.deepEqual(request, {
        workspaceId: configuration.workspaceId,
        contextId: "context:members",
        branchId: "branch:confidence-first",
        taskType: "brief",
        perspectiveIds: ["perspective:customer"],
        scope: {
          assetType: "landing page",
          audience: "members",
        },
        permittedRecordIds: [],
      });
      return {
        viewId: "view:members",
        status: "hit",
        workspaceId: request.workspaceId,
        contextId: request.contextId,
        branchId: request.branchId,
        perspectiveIds: request.perspectiveIds,
        selectedRecordIds: ["state:member-service", "frame:member-discovery"],
        unresolvedConflictIds: [],
        omissions: [],
        routeReceipt: ["branch resolved before synthesis"],
      };
    },
  };
  const model: IntelligenceModel = {
    id: "world-view-capturing-model",
    async completeJson(input) {
      if (input.purpose === "interpret") return { workflowStage: "brief" };
      synthesisPayload = input.payload;
      return {
        knowledge: {
          identity: [
            {
              statement: "Example has a grounded identity.",
              evidenceIds: ["e1"],
            },
          ],
        },
        conflicts: [],
        limitations: [],
        omissions: [],
      };
    },
  };
  const engine = new ContextIntelligenceEngine(
    configuration,
    model,
    new FakeRetriever(),
    undefined,
    undefined,
    resolver,
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
      contextId: "context:members",
      branchId: "branch:confidence-first",
      perspectiveIds: ["perspective:customer"],
    },
    { activationReason: "automatic" },
  );

  assert.equal(packet.worldView?.viewId, "view:members");
  assert.equal(packet.receipt.worldView?.status, "resolved");
  assert.deepEqual(packet.receipt.worldView?.selectedRecordIds, [
    "state:member-service",
    "frame:member-discovery",
  ]);
  assert.deepEqual((synthesisPayload as { worldView?: unknown }).worldView, {
    viewId: "view:members",
    status: "hit",
    workspaceId: configuration.workspaceId,
    contextId: "context:members",
    branchId: "branch:confidence-first",
    perspectiveIds: ["perspective:customer"],
    selectedRecordIds: ["state:member-service", "frame:member-discovery"],
    unresolvedConflictIds: [],
    omissions: [],
    routeReceipt: ["branch resolved before synthesis"],
  });
});

test("engine persists exact observable inputs, retrievals, and output packet", async () => {
  const traceStore = new CapturingTraceStore();
  const engine = new ContextIntelligenceEngine(
    configuration,
    new FakeModel(),
    new FakeRetriever(),
    traceStore,
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
    },
    { activationReason: "explicit" },
  );
  assert.equal(packet.receipt.trace.status, "available");
  const trace = await traceStore.read(packet.receipt.trace.runId);
  assert.equal(trace.header.runId, packet.receipt.trace.runId);
  assert.equal(trace.events[0]?.phase, "interpretation");
  assert.deepEqual(trace.events[1]?.input, {
    text: "Create a brand asset\nWorkflow: brief. Goal: Bound the brief.",
    route: "asset-context",
    datasetName: "example_staging",
    workspaceId: "world://workspace/brand/example",
    brandId: "world://brand/example",
    topK: 5,
    retrievalKind: "lexical_chunk",
  });
  assert.equal(trace.events[2]?.phase, "retrieval");
  assert.equal(trace.events[3]?.phase, "filter");
  assert.equal(trace.events[4]?.phase, "synthesis");
  assert.equal(trace.events[5]?.phase, "context_packet");
});

test("file trace store writes one private JSON trace per completed run", async () => {
  const directory = await mkdtemp(join(tmpdir(), "testflight-trace-"));
  try {
    const traceStore = new JsonFileContextTraceStore(directory);
    const engine = new ContextIntelligenceEngine(
      configuration,
      new FakeModel(),
      new FakeRetriever(),
      traceStore,
    );
    const packet = await engine.compile(
      {
        prompt: "Create a brand asset",
        assetType: "landing page",
        objective: "launch",
        audience: "members",
      },
      { activationReason: "explicit" },
    );
    const trace = await traceStore.read(packet.receipt.trace.runId);
    assert.equal(trace.header.runId, packet.receipt.trace.runId);
    assert.deepEqual(trace.events.at(-1)?.output, packet);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("engine distinguishes selected, retrieved, mentioned, and used entities", async () => {
  const entityConfiguration: IntelligenceConfiguration = {
    ...configuration,
    workflows: [
      {
        ...configuration.workflows[0]!,
        entitySelection: {
          always: ["ENT-EXAMPLE-001", "ENT-EXAMPLE-MISSING"],
          conditions: [],
        },
      },
    ],
  };
  const retriever: KnowledgeRetriever = {
    async retrieve(query) {
      if (query.retrievalKind === "exact_entity")
        return [
          {
            id: "entity-evidence",
            text: '{"id":"ENT-EXAMPLE-001","label":"Example identity"}',
            sourceUrl: "repo://entity-inventory.yaml",
            workspaceId: entityConfiguration.workspaceId,
            brandId: entityConfiguration.brandId,
            retrievalKind: "exact_entity",
            entityIds: ["ENT-EXAMPLE-001"],
          },
        ];
      return [
        {
          id: "chunk-evidence",
          text: "Workflow mentions ENT-EXAMPLE-MENTIONED.",
          sourceUrl: "repo://workflow.yaml",
          workspaceId: entityConfiguration.workspaceId,
          brandId: entityConfiguration.brandId,
          retrievalKind: "lexical_chunk",
        },
      ];
    },
  };
  const model: IntelligenceModel = {
    id: "entity-test-model",
    async completeJson(input) {
      if (input.purpose === "interpret") return { workflowStage: "brief" };
      return {
        knowledge: {
          identity: [
            {
              statement:
                "The directly retrieved entity informed this statement.",
              evidenceIds: ["entity-evidence"],
            },
          ],
        },
        conflicts: [],
        limitations: [],
        omissions: [],
      };
    },
  };
  const packet = await new ContextIntelligenceEngine(
    entityConfiguration,
    model,
    retriever,
  ).compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
    },
    { activationReason: "explicit" },
  );
  assert.deepEqual(packet.receipt.entities.selectedEntityIds, [
    "ENT-EXAMPLE-001",
    "ENT-EXAMPLE-MISSING",
  ]);
  assert.deepEqual(packet.receipt.entities.retrievedEntityIds, [
    "ENT-EXAMPLE-001",
  ]);
  assert.deepEqual(packet.receipt.entities.mentionedEntityIds.sort(), [
    "ENT-EXAMPLE-MENTIONED",
  ]);
  assert.deepEqual(packet.receipt.entities.usedEntityIds, ["ENT-EXAMPLE-001"]);
});

test("journal remains readable before a context run completes", async () => {
  const directory = await mkdtemp(join(tmpdir(), "testflight-trace-"));
  try {
    const store = new JsonFileContextTraceStore(directory);
    const runId = "123e4567-e89b-42d3-a456-426614174000";
    await store.start({
      version: 1,
      runId,
      startedAt: "2026-08-27T00:00:00.000Z",
      configuration: {
        workspaceId: configuration.workspaceId,
        brandId: configuration.brandId,
        datasetName: configuration.datasetName,
        operators: configuration.operators,
      },
      modelId: "test-model",
    });
    await store.append(runId, {
      phase: "interpretation",
      input: { prompt: "unfinished run" },
    });
    const trace = await store.read(runId);
    assert.equal(trace.events.length, 1);
    assert.equal(trace.events[0]?.phase, "interpretation");
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test("engine never labels an empty, invalidly cited synthesis ready", async () => {
  const model: IntelligenceModel = {
    id: "invalid-citation-model",
    async completeJson(input) {
      if (input.purpose === "interpret") return { workflowStage: "brief" };
      return {
        knowledge: {
          identity: [
            {
              statement: "This identifier came from inside a source document.",
              evidenceIds: ["EVID-EXAMPLE-001"],
            },
          ],
        },
        conflicts: [],
        limitations: [],
        omissions: [],
      };
    },
  };
  const engine = new ContextIntelligenceEngine(
    configuration,
    model,
    new FakeRetriever(),
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
    },
    { activationReason: "explicit" },
  );
  assert.equal(packet.status, "partial");
  assert.equal(packet.knowledge.evidence?.[0]?.evidenceIds[0], "e1");
  assert.match(packet.limitations.join(" "), /synthesis/i);
});

test("engine bounds a valid synthesis to two statements per section", async () => {
  const model: IntelligenceModel = {
    id: "verbose-model",
    async completeJson(input) {
      if (input.purpose === "interpret") return { workflowStage: "brief" };
      return {
        knowledge: {
          identity: [
            { statement: "One", evidenceIds: ["e1"] },
            { statement: "Two", evidenceIds: ["e1"] },
            { statement: "Three", evidenceIds: ["e1"] },
          ],
        },
        conflicts: [],
        limitations: [],
        omissions: [],
      };
    },
  };
  const engine = new ContextIntelligenceEngine(
    configuration,
    model,
    new FakeRetriever(),
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
    },
    { activationReason: "explicit" },
  );
  assert.deepEqual(
    packet.knowledge.identity?.map((statement) => statement.statement),
    ["One", "Two"],
  );
});

test("foreign workspace requests do not reach retrieval", async () => {
  let called = false;
  const retriever: KnowledgeRetriever = {
    async retrieve() {
      called = true;
      return [];
    },
  };
  const engine = new ContextIntelligenceEngine(
    configuration,
    new FakeModel(),
    retriever,
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      workspaceId: "world://workspace/brand/other",
      assetType: "page",
      objective: "launch",
      audience: "buyers",
    },
    { activationReason: "explicit" },
  );
  assert.equal(packet.status, "no_hit");
  assert.equal(called, false);
});

const visualManifest: VisualLanguageManifest = {
  version: 1,
  workspaceId: "world://workspace/brand/example",
  brandId: "world://brand/example",
  profiles: [
    { id: "VL-BASE", label: "Base", description: "Base", status: "observed" },
    {
      id: "VL-AUDIENCE",
      label: "Audience",
      description: "Overlay",
      status: "observed",
    },
  ],
  references: [
    {
      id: "VR-COLOR",
      revision: 1,
      kind: "color.palette",
      schemaVersion: 1,
      label: "Palette observation",
      payload: { colors: ["#111111", "#f4f1e8"] },
      assetRefs: [],
      authority: "observed_public",
      epistemicStatus: "observed",
      status: "observed",
      sourceIds: ["SRC-1"],
      evidenceIds: ["EVID-1"],
      recordedAt: "2026-01-01T00:00:00Z",
      lastVerifiedAt: "2026-01-01",
      rights: {
        permittedUse: "analysis_and_reference",
        generationUse: "inspiration_only",
      },
      limitations: [],
      slot: "color.palette",
    },
    {
      id: "VR-TYPE",
      revision: 1,
      kind: "typography.role",
      schemaVersion: 1,
      label: "Type observation",
      payload: { role: "display" },
      assetRefs: [],
      authority: "observed_public",
      epistemicStatus: "observed",
      status: "observed",
      sourceIds: ["SRC-2"],
      evidenceIds: ["EVID-2"],
      recordedAt: "2026-01-01T00:00:00Z",
      lastVerifiedAt: "2026-01-01",
      rights: {
        permittedUse: "analysis_and_reference",
        generationUse: "inspiration_only",
      },
      limitations: [],
      slot: "typography.display",
    },
  ],
  revisions: [
    {
      id: "VL-BASE@1",
      profileId: "VL-BASE",
      revision: 1,
      branch: "main",
      parentRevisionIds: [],
      modules: [
        { slot: "color.palette", referenceId: "VR-COLOR", mode: "extend" },
      ],
      authority: "observed_public",
      epistemicStatus: "observed",
      status: "observed",
      validFrom: "2025-01-01",
      validUntil: "2025-12-31",
      recordedAt: "2026-01-01T00:00:00Z",
      lastVerifiedAt: "2026-01-01",
      sourceIds: ["SRC-1"],
      evidenceIds: ["EVID-1"],
      limitations: [],
      gaps: ["authorized typography rules"],
    },
    {
      id: "VL-AUDIENCE@1",
      profileId: "VL-AUDIENCE",
      revision: 1,
      branch: "main",
      parentRevisionIds: [],
      modules: [
        { slot: "typography.display", referenceId: "VR-TYPE", mode: "replace" },
      ],
      authority: "observed_public",
      epistemicStatus: "observed",
      status: "observed",
      validFrom: "2025-01-01",
      recordedAt: "2026-01-01T00:00:00Z",
      lastVerifiedAt: "2026-01-01",
      sourceIds: ["SRC-2"],
      evidenceIds: ["EVID-2"],
      limitations: [],
    },
  ],
  bindings: [
    {
      id: "BIND-BASE",
      profileId: "VL-BASE",
      revisionId: "VL-BASE@1",
      scope: { brandId: "world://brand/example" },
      priority: 1,
      status: "observed",
      validFrom: "2025-01-01",
      validUntil: "2025-12-31",
      recordedAt: "2026-01-01T00:00:00Z",
      lastVerifiedAt: "2026-01-01",
      sourceIds: ["SRC-1"],
      evidenceIds: ["EVID-1"],
      limitations: [],
    },
    {
      id: "BIND-AUDIENCE",
      profileId: "VL-AUDIENCE",
      revisionId: "VL-AUDIENCE@1",
      scope: {
        brandId: "world://brand/example",
        audienceSegmentIds: ["SEG-1"],
      },
      priority: 10,
      status: "observed",
      validFrom: "2025-01-01",
      recordedAt: "2026-01-01T00:00:00Z",
      lastVerifiedAt: "2026-01-01",
      sourceIds: ["SRC-2"],
      evidenceIds: ["EVID-2"],
      limitations: [],
    },
  ],
};

test("visual language resolver composes audience overlays and preserves gaps", () => {
  const result = new JsonVisualLanguageResolver(visualManifest).resolve({
    workspaceId: visualManifest.workspaceId,
    brandId: visualManifest.brandId,
    audienceSegmentIds: ["SEG-1"],
    validTime: "2025-06-01",
  });
  assert.equal(result.status, "partial");
  assert.deepEqual(result.receipt.selectedProfileRevisionIds, [
    "VL-BASE@1",
    "VL-AUDIENCE@1",
  ]);
  assert.deepEqual(result.receipt.selectedReferenceIds, [
    "VR-COLOR",
    "VR-TYPE",
  ]);
  assert.ok(
    result.omissions.includes(
      "The visual-language pack does not establish authorized typography rules.",
    ),
  );
});

test("visual language resolver returns no-hit outside the recorded time range", () => {
  const resolver = new JsonVisualLanguageResolver(visualManifest);
  assert.equal(
    resolver.resolve({
      workspaceId: visualManifest.workspaceId,
      brandId: visualManifest.brandId,
      validTime: "2024-06-01",
    }).status,
    "no_hit",
  );
  assert.equal(
    resolver.resolve({
      workspaceId: visualManifest.workspaceId,
      brandId: visualManifest.brandId,
      validTime: "2025-06-01",
    }).revisions[0]?.id,
    "VL-BASE@1",
  );
});

test("engine adds resolved visual language to the context packet and exact route", async () => {
  const visualConfiguration: IntelligenceConfiguration = {
    ...configuration,
    visualLanguage: {
      enabled: true,
      route: "visual-language",
      workflowStages: ["brief"],
      audienceSegmentAliases: [{ id: "SEG-1", includesAny: ["member"] }],
      offerAliases: [{ id: "OFFER-1", includesAny: ["member"] }],
    },
  };
  const retrieverQueries: string[] = [];
  const retriever: KnowledgeRetriever = {
    async retrieve(query) {
      retrieverQueries.push(query.retrievalKind ?? "unknown");
      return [
        {
          id: "e1",
          text: "Example identity evidence",
          sourceUrl: "repo://evidence.md",
          workspaceId: visualConfiguration.workspaceId,
          brandId: visualConfiguration.brandId,
        },
      ];
    },
  };
  const engine = new ContextIntelligenceEngine(
    visualConfiguration,
    new FakeModel(),
    retriever,
    undefined,
    new JsonVisualLanguageResolver(visualManifest),
  );
  const packet = await engine.compile(
    {
      prompt: "Create a brand asset",
      assetType: "landing page",
      objective: "launch",
      audience: "members",
      channel: "nike.com",
      geography: "global",
    },
    { activationReason: "explicit" },
  );
  assert.equal(packet.visualLanguage?.status, "partial");
  assert.deepEqual(packet.visualLanguage?.receipt.selectedReferenceIds, [
    "VR-COLOR",
    "VR-TYPE",
  ]);
  assert.equal(packet.receipt.visualLanguage?.profileRevisionIds.length, 2);
  assert.ok(retrieverQueries.includes("visual_reference"));
});
