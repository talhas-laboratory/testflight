import type {
  ProjectionCandidate,
  ProjectionEdge,
  ProjectionFreshness,
  WorldV3Record,
} from "./contracts.js";
import { invokeJsonProcess, type JsonProcessCommand } from "./process.js";
import type { WorldV3ReadQuery } from "./resolver.js";
import type {
  WorldProjectionReader,
  WorldProjectionReadRequest,
  WorldProjectionReadResult,
  WorldV3CanonicalHydrator,
  WorldV3SnapshotPin,
} from "./runtime.js";
import { decodeWorldV3WireRecords } from "./wire.js";

export interface CogneeProjectionProcessOptions extends JsonProcessCommand {
  datasetName: string;
  canonicalSnapshotRoot: string;
  manifestPath?: string;
}

/** Local process adapter for Cognee discovery. Results remain untrusted candidates. */
export class CogneeProcessWorldProjectionReader
  implements WorldProjectionReader
{
  constructor(private readonly options: CogneeProjectionProcessOptions) {}

  async retrieve(
    request: WorldProjectionReadRequest,
  ): Promise<WorldProjectionReadResult> {
    const response = await invokeJsonProcess(
      this.options,
      {
        datasetName: this.options.datasetName,
        text: request.objective,
        topK: request.maximumSemanticCandidates,
        retrievalKind: "world_v3",
        workspaceId: request.workspaceId,
        branchId: request.branchId,
        lifecycleStatuses: request.permittedLifecycleStatuses,
        maximumGraphEdges: request.maximumGraphEdges,
        maximumGraphHops: request.maximumGraphHops,
        allowedRelationTypeIds: request.allowedRelationTypeIds,
        ...(request.moduleIds ? { moduleIds: request.moduleIds } : {}),
        ...(request.seedRecordIds
          ? { seedRecordIds: request.seedRecordIds }
          : {}),
        ...(this.options.manifestPath
          ? { manifestPath: this.options.manifestPath }
          : {}),
      },
      "Cognee projection retrieval",
    );
    const candidates = (
      Array.isArray(response.items) ? response.items : []
    ).filter(isProjectionWireCandidate);
    const responseRoot =
      typeof response.projectionSnapshotRoot === "string"
        ? response.projectionSnapshotRoot
        : undefined;
    const roots = new Set([
      ...candidates.map((candidate) => candidate.projectionSnapshotRoot),
      ...(responseRoot ? [responseRoot] : []),
    ]);
    const projectionSnapshotRoot =
      roots.size === 1 ? ([...roots][0] ?? "") : "";
    const freshness: ProjectionFreshness = projectionSnapshotRoot
      ? projectionSnapshotRoot === this.options.canonicalSnapshotRoot
        ? "exact"
        : "stale"
      : "verified_partial";
    return {
      canonicalSnapshotRoot: this.options.canonicalSnapshotRoot,
      projectionSnapshotRoot,
      freshness,
      candidates: candidates.map(
        ({ projectionSnapshotRoot: _root, ...candidate }) => candidate,
      ),
      edges: (Array.isArray(response.edges) ? response.edges : []).filter(
        isProjectionEdge,
      ),
      retrievalMethods: responseRoot
        ? ["semantic", "structural"]
        : ["semantic"],
    };
  }
}

export interface SqliteWorldProcessOptions extends JsonProcessCommand {
  worldDb: string;
}

export class SqliteProcessWorldV3CanonicalHydrator
  implements WorldV3CanonicalHydrator
{
  constructor(private readonly options: SqliteWorldProcessOptions) {}

  async hydrate(
    query: WorldV3ReadQuery & { snapshotRoot: string },
  ): Promise<readonly WorldV3Record[]> {
    const response = await invokeJsonProcess(
      this.options,
      {
        worldDb: this.options.worldDb,
        workspaceId: query.workspaceId,
        branchId: query.branchId,
        snapshotRoot: query.snapshotRoot,
        recordIds: query.recordIds ?? [],
      },
      "canonical hydration",
    );
    if (
      response.snapshotRoot !== query.snapshotRoot ||
      !Array.isArray(response.records)
    ) {
      throw new Error("canonical hydration returned a stale snapshot");
    }
    try {
      return decodeWorldV3WireRecords(response.records);
    } catch (error) {
      throw new Error(
        "canonical hydration returned malformed V3 wire records",
        {
          cause: error,
        },
      );
    }
  }
}

export class SqliteProcessWorldV3SnapshotPin implements WorldV3SnapshotPin {
  constructor(private readonly options: SqliteWorldProcessOptions) {}

  async pin(request: {
    workspaceId: string;
    branchId: string;
  }): Promise<{ snapshotRoot: string }> {
    const response = await invokeJsonProcess(
      this.options,
      {
        operation: "snapshot",
        worldDb: this.options.worldDb,
        workspaceId: request.workspaceId,
        branchId: request.branchId,
      },
      "canonical snapshot pin",
    );
    if (
      typeof response.snapshotRoot !== "string" ||
      !/^[a-f0-9]{64}$/.test(response.snapshotRoot)
    ) {
      throw new Error(
        "canonical snapshot pin returned an invalid snapshot root",
      );
    }
    return { snapshotRoot: response.snapshotRoot };
  }
}

type ProjectionWireCandidate = ProjectionCandidate & {
  projectionSnapshotRoot: string;
};

function isProjectionWireCandidate(
  value: unknown,
): value is ProjectionWireCandidate {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const item = value as Record<string, unknown>;
  return (
    typeof item.recordId === "string" &&
    typeof item.recordVersion === "number" &&
    typeof item.canonicalRecordHash === "string" &&
    typeof item.projectionSnapshotRoot === "string" &&
    /^[a-f0-9]{64}$/.test(item.projectionSnapshotRoot) &&
    typeof item.score === "number" &&
    typeof item.retrievalMethod === "string" &&
    Array.isArray(item.matchedFields)
  );
}

function isProjectionEdge(value: unknown): value is ProjectionEdge {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const edge = value as Record<string, unknown>;
  const edgeClasses = new Set<ProjectionEdge["edgeClass"]>([
    "canonical_relation",
    "canonical_reference",
    "derived_similarity",
    "inferred_relation",
    "projection_structure",
  ]);
  return (
    typeof edge.sourceRecordId === "string" &&
    typeof edge.targetRecordId === "string" &&
    typeof edge.predicate === "string" &&
    typeof edge.edgeClass === "string" &&
    edgeClasses.has(edge.edgeClass as ProjectionEdge["edgeClass"]) &&
    (edge.canonicalRelationId === undefined ||
      typeof edge.canonicalRelationId === "string") &&
    (edge.canonicalRelationHash === undefined ||
      typeof edge.canonicalRelationHash === "string") &&
    (edge.derivationRef === undefined || typeof edge.derivationRef === "string")
  );
}
