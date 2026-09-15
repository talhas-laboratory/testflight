import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  compileContextV2,
  decodeWorldV3WireBundle,
  decodeWorldV3WireRecord,
  WorldV3WireDecodeError,
  type ContextRequestV2,
  type ResolvedAuthorityGrant,
  type RouteDefinition,
} from "../src/index.js";

const bundleUrl = new URL(
  "../../../../workspaces/brand-hellobiotic-research/v3/proposed-public-research-branch.json",
  import.meta.url,
);

test("canonical Biotic Python export decodes without losing routing or payload meaning", async () => {
  const wire = JSON.parse(await readFile(bundleUrl, "utf8")) as unknown;
  const records = decodeWorldV3WireBundle(wire);
  assert.ok(records.length > 0);
  assert.ok(records.every((record) => record.schemaVersion.startsWith("3.")));

  const brand = records.find((record) => record.id === "entity:biotic");
  if (!brand || brand.kind !== "entity") assert.fail("Biotic entity missing");
  assert.equal(
    brand?.workspaceId,
    "world://workspace/brand/hellobiotic-research",
  );
  assert.equal(brand?.moduleId, "world://ontology/module/brand-world/identity");
  assert.equal(brand?.canonicalLabel, "Biotic / Hellobiotic");
  assert.deepEqual(brand?.aliases, ["Biotic", "Hellobiotic"]);

  const claim = records.find(
    (record) => record.id === "claim:biotic:public-whole-body-care-framing",
  );
  if (!claim || claim.kind !== "claim") assert.fail("Biotic claim missing");
  assert.equal(claim?.claimKind, "factual_assertion");
  assert.equal(claim?.subjectId, "entity:biotic");
  assert.ok(typeof claim?.objectValue === "string");
  assert.deepEqual(claim?.evidenceIds, ["evidence:biotic:home-page-framing"]);

  const event = records.find((record) => record.kind === "event");
  assert.equal(event?.occurredAt?.fromTime, "2026-08-31T00:00:00Z");
  assert.equal(event?.participants?.[0]?.entityId, "entity:biotic");

  const route: RouteDefinition = {
    id: "route:biotic-public-newsletter",
    version: 2,
    taskFamily: "newsletter",
    eligibleAgentRoles: ["creator", "brand-guardian"],
    startModuleIds: [
      "world://ontology/module/brand-world/identity",
      "world://ontology/module/brand-world/offering",
    ],
    requiredSemanticKinds: ["entity", "claim", "relation", "evidence"],
    allowedRelationTypeIds: ["world://ontology/brand-world/relation/offers"],
    abstractionOrder: ["foundation", "roads", "evidence"],
    mandatoryGates: ["authority", "valid_time", "lifecycle", "conflict"],
    requiredAuthorityCapabilities: ["world:read"],
    expansionTriggers: ["missing_kind", "missing_evidence"],
    stopConditions: [
      "sufficient",
      "budget_exhausted",
      "no_candidates",
      "gate_failure",
    ],
    sufficiencyPolicy: {
      id: "sufficiency:biotic-public-newsletter",
      requirements: [
        { kind: "entity", minimum: 2 },
        { kind: "claim", minimum: 2, mustHaveEvidence: true },
        { kind: "relation", minimum: 1 },
      ],
      requiredModuleIds: [
        "world://ontology/module/brand-world/identity",
        "world://ontology/module/brand-world/offering",
      ],
      minimumEvidenceRecords: 1,
      unresolvedConflicts: "hold",
    },
  };
  const request: ContextRequestV2 = {
    requestId: "request:biotic-public-newsletter",
    principalRef: "principal:fde",
    agentDefinitionRef: "agent:creator@1",
    agentRoles: ["creator"],
    taskRef: "task:biotic-public-newsletter",
    taskFamily: "newsletter",
    objective: "Prepare a source-grounded newsletter brief for review.",
    authorityGrantRefs: ["grant:biotic-public-research-read"],
    workspaceId: "world://workspace/brand/hellobiotic-research",
    branchId: "public-research-v3",
    permittedLifecycleStatuses: ["proposed"],
    scope: {
      moduleIds: [
        "world://ontology/module/brand-world/identity",
        "world://ontology/module/brand-world/offering",
      ],
    },
    desiredAbstraction: "evidence",
    sufficiencyPolicyRef: route.sufficiencyPolicy.id,
    budget: {
      maximumRecords: 24,
      maximumCompilerStages: 2,
      maximumSemanticCandidates: 12,
      maximumGraphEdges: 24,
      maximumGraphHops: 2,
    },
    requiredOutputSchema: "artifact:newsletter-brief@1",
    compiledAt: "2026-09-14T00:00:00Z",
  };
  const grants: ResolvedAuthorityGrant[] = [
    {
      id: "grant:biotic-public-research-read",
      status: "active",
      principalRef: "principal:fde",
      agentDefinitionRef: "agent:creator@1",
      capabilities: ["world:read"],
      scope: {
        workspaceId: "world://workspace/brand/hellobiotic-research",
        branchIds: ["public-research-v3"],
      },
      validFrom: "2026-09-01T00:00:00Z",
      validUntil: "2026-10-01T00:00:00Z",
    },
  ];

  const packet = compileContextV2(records, request, route, grants);
  assert.equal(packet.status, "ready");
  assert.ok(
    packet.records.every((record) => record.schemaVersion.startsWith("3.")),
  );
  assert.ok(packet.recordIds.includes("entity:biotic"));
  assert.ok(
    packet.recordIds.includes(
      "relation:biotic:brand-offers-brightening-deodorant",
    ),
  );
  assert.ok(packet.evidenceIds.includes("evidence:biotic:home-page-framing"));
  assert.ok(
    packet.citations.some(
      (citation) => citation.sourceId === "source:biotic:home-page",
    ),
  );
  assert.deepEqual(packet.trace.expansions, ["roads", "evidence"]);
  assert.ok(
    packet.trace.steps.some(
      (step) =>
        step.action === "authority-gate-passed" &&
        step.recordIds.includes("grant:biotic-public-research-read"),
    ),
  );
  assert.deepEqual(packet.evaluation.authorityRejections, []);
  assert.equal(packet.trace.selectedRecordIds.length, packet.records.length);
  assert.match(packet.packetId, /^context:[0-9a-f]{64}$/);
});

test("wire boundary rejects legacy, malformed, and unknown canonical fields", () => {
  const entity = {
    id: "entity:test",
    kind: "entity",
    type_id: "world://type/Brand",
    schema_version: "3.0.0",
    record_version: 1,
    workspace_id: "world://workspace/test",
    module_id: "world://module/identity",
    branch_id: "main",
    lifecycle_status: "accepted",
    valid_time: null,
    known_time: null,
    context_refs: [],
    provenance_refs: [],
    derivation_ref: null,
    authority_ref: null,
    created_at: "2026-09-14T00:00:00Z",
    created_by: "actor:test",
    supersedes_ref: null,
    canonical_label: "Test",
    aliases: [],
    definition: "Test entity",
  };
  assert.throws(
    () => decodeWorldV3WireRecord({ ...entity, schema_version: "2.0.0" }),
    (error) =>
      error instanceof WorldV3WireDecodeError &&
      error.path === "record.schema_version",
  );
  assert.throws(
    () => decodeWorldV3WireRecord({ ...entity, workspace_id: "" }),
    /expected a non-empty string/,
  );
  assert.throws(
    () => decodeWorldV3WireRecord({ ...entity, arbitrary_payload: true }),
    /unknown record field/,
  );
});
