import {
  compileContextV2,
  compileContextV2StaleProjection,
} from "./compiler.js";
import type {
  ContextPacketV2,
  ContextRequestV2,
  ProjectionCandidate,
  ProjectionEdge,
  ProjectionFreshness,
  ResolvedAuthorityGrant,
  RouteDefinition,
  WorldV3Record,
} from "./contracts.js";
import type { WorldV3ReadQuery, WorldV3RecordResolver } from "./resolver.js";

export interface WorldProjectionReadRequest {
  workspaceId: string;
  branchId: string;
  permittedLifecycleStatuses: string[];
  objective: string;
  moduleIds?: string[];
  seedRecordIds?: string[];
  maximumSemanticCandidates: number;
  maximumGraphEdges: number;
  maximumGraphHops: number;
  allowedRelationTypeIds: string[];
}

export interface WorldProjectionReadResult {
  canonicalSnapshotRoot: string;
  projectionSnapshotRoot: string;
  freshness: ProjectionFreshness;
  candidates: ProjectionCandidate[];
  edges: ProjectionEdge[];
  retrievalMethods: string[];
}

/** Discovery boundary: candidates and paths are hints, never asserted facts. */
export interface WorldProjectionReader {
  retrieve(
    request: WorldProjectionReadRequest,
  ): Promise<WorldProjectionReadResult>;
}

/** Canonical hydration boundary. Returned records must be exact V3 wire records. */
export interface WorldV3CanonicalHydrator {
  hydrate(
    query: WorldV3ReadQuery & { snapshotRoot: string },
  ): Promise<readonly WorldV3Record[]>;
}

/** Pins the exact canonical snapshot shared by discovery and hydration. */
export interface WorldV3SnapshotPin {
  pin(request: {
    workspaceId: string;
    branchId: string;
  }): Promise<{ snapshotRoot: string }>;
}

export async function compileContextV2FromResolver(
  resolver: WorldV3RecordResolver,
  request: ContextRequestV2,
  route: RouteDefinition,
  resolvedAuthorityGrants: readonly ResolvedAuthorityGrant[] = [],
): Promise<ContextPacketV2> {
  const records = await resolver.resolve({
    workspaceId: request.workspaceId,
    branchId: request.branchId,
  });
  return compileContextV2(records, request, route, resolvedAuthorityGrants);
}

/**
 * Graph-guided compilation. The projection chooses where to look; only the
 * pinned canonical World supplies records and authoritative relationships.
 */
export async function compileContextV2FromProjection(
  projection: WorldProjectionReader,
  hydrator: WorldV3CanonicalHydrator,
  request: ContextRequestV2,
  route: RouteDefinition,
  resolvedAuthorityGrants: readonly ResolvedAuthorityGrant[] = [],
): Promise<ContextPacketV2> {
  const preflight = compileContextV2(
    [],
    request,
    route,
    resolvedAuthorityGrants,
  );
  if (preflight.status === "unauthorized" || preflight.status === "hold") {
    return preflight;
  }

  const discovered = await projection.retrieve({
    workspaceId: request.workspaceId,
    branchId: request.branchId,
    permittedLifecycleStatuses: request.permittedLifecycleStatuses,
    objective: request.objective,
    ...(request.scope.moduleIds ? { moduleIds: request.scope.moduleIds } : {}),
    ...(request.scope.seedRecordIds
      ? { seedRecordIds: request.scope.seedRecordIds }
      : {}),
    maximumSemanticCandidates: request.budget.maximumSemanticCandidates,
    maximumGraphEdges: request.budget.maximumGraphEdges,
    maximumGraphHops: request.budget.maximumGraphHops,
    allowedRelationTypeIds: route.allowedRelationTypeIds,
  });

  if (discovered.freshness === "stale") {
    const stale = compileContextV2StaleProjection(
      request,
      route,
      resolvedAuthorityGrants,
    );
    return withProjectionTrace(stale, discovered, [], [], 0);
  }

  const semanticCandidateIds = unique(
    discovered.candidates.map((candidate) => candidate.recordId),
  );
  const canonicalEdges = discovered.edges.filter(
    (edge) => edge.edgeClass === "canonical_relation",
  );
  const canonicalRelationIds = unique(
    canonicalEdges.flatMap((edge) =>
      edge.canonicalRelationId ? [edge.canonicalRelationId] : [],
    ),
  );
  const structuralRecordIds = unique(
    discovered.edges
      .filter(
        (edge) =>
          edge.edgeClass === "canonical_relation" ||
          edge.edgeClass === "canonical_reference",
      )
      .flatMap((edge) => [edge.sourceRecordId, edge.targetRecordId]),
  );
  const hydrationIds = unique([
    ...semanticCandidateIds,
    ...canonicalRelationIds,
    ...structuralRecordIds,
  ]).slice(0, request.budget.maximumRecords);
  const hydratedCanonicalRelationIds = canonicalRelationIds.filter((id) =>
    hydrationIds.includes(id),
  );
  const records = await hydrator.hydrate({
    workspaceId: request.workspaceId,
    branchId: request.branchId,
    recordIds: hydrationIds,
    snapshotRoot: discovered.canonicalSnapshotRoot,
  });
  const packet = compileContextV2(
    records,
    request,
    route,
    resolvedAuthorityGrants,
  );
  const discardedEdgeCount = discovered.edges.filter(
    (edge) =>
      edge.edgeClass === "inferred_relation" ||
      edge.edgeClass === "derived_similarity",
  ).length;
  return withProjectionTrace(
    packet,
    discovered,
    records.map((record) => record.id),
    hydratedCanonicalRelationIds,
    discardedEdgeCount,
  );
}

/** Pins once, authorizes before IO, then runs discovery and canonical hydration. */
export class WorldV3GraphContextRuntime {
  constructor(
    private readonly snapshotPin: WorldV3SnapshotPin,
    private readonly projectionReaderFor: (
      canonicalSnapshotRoot: string,
    ) => WorldProjectionReader,
    private readonly canonicalHydrator: WorldV3CanonicalHydrator,
  ) {}

  async compile(
    request: ContextRequestV2,
    route: RouteDefinition,
    resolvedAuthorityGrants: readonly ResolvedAuthorityGrant[] = [],
  ): Promise<ContextPacketV2> {
    let pinnedSnapshotRoot: string | undefined;
    return compileContextV2FromProjection(
      {
        retrieve: async (projectionRequest) => {
          const pinned = await this.snapshotPin.pin({
            workspaceId: projectionRequest.workspaceId,
            branchId: projectionRequest.branchId,
          });
          pinnedSnapshotRoot = pinned.snapshotRoot;
          return this.projectionReaderFor(pinned.snapshotRoot).retrieve(
            projectionRequest,
          );
        },
      },
      {
        hydrate: async (query) => {
          if (query.snapshotRoot !== pinnedSnapshotRoot) {
            throw new Error("hydration snapshot differs from the runtime pin");
          }
          return this.canonicalHydrator.hydrate(query);
        },
      },
      request,
      route,
      resolvedAuthorityGrants,
    );
  }
}

function withProjectionTrace(
  packet: ContextPacketV2,
  discovery: WorldProjectionReadResult,
  hydratedRecordIds: string[],
  canonicalRelationIds: string[],
  discardedEdgeCount: number,
): ContextPacketV2 {
  return {
    ...packet,
    trace: {
      ...packet.trace,
      projectionRetrieval: {
        canonicalSnapshotRoot: discovery.canonicalSnapshotRoot,
        projectionSnapshotRoot: discovery.projectionSnapshotRoot,
        freshness: discovery.freshness,
        candidateRecordIds: discovery.candidates.map(
          (candidate) => candidate.recordId,
        ),
        hydratedRecordIds,
        canonicalRelationIds: unique(canonicalRelationIds),
        discardedEdgeCount,
        retrievalMethods: discovery.retrievalMethods,
      },
    },
  };
}

function unique(values: readonly string[]): string[] {
  return [...new Set(values)];
}
