import { compileContextV2, contextDigest } from "./compiler.js";
import type {
  ContextRequestV2,
  ContextRunTraceV2,
  ReplayResult,
  ResolvedAuthorityGrant,
  RouteDefinition,
  WorldV3Record,
} from "./contracts.js";

/** Re-run an exact input snapshot and report each receipt-level divergence. */
export function replayContextV2(
  records: readonly WorldV3Record[],
  request: ContextRequestV2,
  route: RouteDefinition,
  expected: ContextRunTraceV2,
  resolvedAuthorityGrants: readonly ResolvedAuthorityGrant[] = [],
): ReplayResult {
  const packet = compileContextV2(
    records,
    request,
    route,
    resolvedAuthorityGrants,
  );
  const differences: string[] = [];
  if (packet.trace.inputFingerprint !== expected.inputFingerprint)
    differences.push("input fingerprint changed");
  if (packet.trace.packetHash !== expected.packetHash)
    differences.push("packet hash changed");
  if (contextDigest(packet.trace.steps) !== contextDigest(expected.steps))
    differences.push("trace steps changed");
  if (
    contextDigest(packet.trace.exclusions) !==
    contextDigest(expected.exclusions)
  )
    differences.push("exclusions changed");
  if (
    contextDigest(packet.trace.selectedRecordVersions) !==
    contextDigest(expected.selectedRecordVersions)
  )
    differences.push("selected record versions changed");
  if (packet.trace.stopReason !== expected.stopReason)
    differences.push("stop reason changed");
  return { exact: differences.length === 0, packet, differences };
}
