#!/usr/bin/env node
/** Compile the bounded, read-only Biotic v3 packet used by the newsletter strategist. */

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import {
  compileContextV2,
  decodeWorldV3WireBundle,
} from "../dist/src/world-v3.js";

const root = resolve(process.env.TESTFLIGHT_PROJECT_ROOT ?? process.cwd());
const stdin = await new Promise((resolveInput, reject) => {
  let body = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => {
    body += chunk;
  });
  process.stdin.on("end", () => resolveInput(body));
  process.stdin.on("error", reject);
});
const input = JSON.parse(stdin);
if (typeof input.objective !== "string" || !input.objective.trim()) {
  throw new Error("objective is required");
}

const workspaceId = "world://workspace/brand/hellobiotic-research";
const branchId = "public-research-v3";
const agentDefinitionRef = "agent:hellobiotic-newsletter-strategist@1";
const grantId = "grant:hellobiotic-newsletter-public-research-read";
const moduleIds = [
  "world://ontology/module/brand-world/identity",
  "world://ontology/module/brand-world/expression-manifestation",
  "world://ontology/module/brand-world/offering",
  "world://ontology/module/brand-world/relationships",
];
const bundle = JSON.parse(
  await readFile(
    resolve(
      root,
      "workspaces/brand-hellobiotic-research/v3/proposed-public-research-branch.json",
    ),
    "utf8",
  ),
);
const records = decodeWorldV3WireBundle(bundle);
const compiledAt = input.compiled_at ?? "2026-09-14T00:00:00.000Z";
const route = {
  id: "route:biotic-public-research-newsletter",
  version: 1,
  taskFamily: "newsletter",
  eligibleAgentRoles: ["hellobiotic-newsletter-strategist"],
  startModuleIds: moduleIds,
  requiredSemanticKinds: ["entity", "claim", "evidence"],
  allowedRelationTypeIds: ["world://ontology/brand-world/relation/offers"],
  abstractionOrder: ["foundation", "roads", "evidence"],
  mandatoryGates: ["authority", "lifecycle", "freshness", "conflict"],
  requiredAuthorityGrantRefs: [grantId],
  requiredAuthorityCapabilities: ["world:read"],
  expansionTriggers: ["missing_kind", "missing_evidence", "missing_module"],
  stopConditions: [
    "sufficient",
    "budget_exhausted",
    "no_candidates",
    "gate_failure",
  ],
  sufficiencyPolicy: {
    id: "sufficiency:biotic-public-research-newsletter",
    requirements: [
      { kind: "entity", minimum: 1 },
      { kind: "claim", minimum: 1, mustHaveEvidence: true },
    ],
    requiredModuleIds: moduleIds.slice(0, 2),
    minimumEvidenceRecords: 1,
    unresolvedConflicts: "report",
  },
};
const request = {
  requestId: input.request_id ?? "request:biotic-newsletter-world-reasoning",
  principalRef: "agent:hellobiotic-newsletter-strategist",
  agentDefinitionRef,
  agentRoles: ["hellobiotic-newsletter-strategist"],
  taskRef: input.task_ref ?? "task:biotic-newsletter-world-reasoning",
  taskFamily: "newsletter",
  objective: input.objective,
  authorityGrantRefs: [grantId],
  workspaceId,
  branchId,
  permittedLifecycleStatuses: ["proposed"],
  scope: { moduleIds },
  desiredAbstraction: "evidence",
  sufficiencyPolicyRef: route.sufficiencyPolicy.id,
  budget: {
    maximumRecords: 24,
    maximumCompilerStages: 3,
    maximumSemanticCandidates: 12,
    maximumGraphEdges: 24,
    maximumGraphHops: 2,
  },
  requiredOutputSchema: "artifact:newsletter-reasoning@1",
  compiledAt,
};
const grants = [
  {
    id: grantId,
    principalRef: request.principalRef,
    agentDefinitionRef,
    status: "active",
    capabilities: ["world:read"],
    validFrom: "2026-01-01T00:00:00.000Z",
    scope: { workspaceId, branchIds: [branchId], moduleIds },
  },
];
const packet = compileContextV2(records, request, route, grants);
if (packet.status === "unauthorized" || packet.status === "no_hit") {
  throw new Error(`Brand World context unavailable: ${packet.status}`);
}
process.stdout.write(`${JSON.stringify(packet)}\n`);
