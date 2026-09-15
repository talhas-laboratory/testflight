import type { WorldV3Kind, WorldV3Record } from "./contracts.js";

export interface WorldV3ReadQuery {
  workspaceId: string;
  branchId: string;
  recordIds?: string[];
  moduleIds?: string[];
  kinds?: WorldV3Kind[];
}

/** Read-only provider boundary. Implementations must never return a non-v3 record. */
export interface WorldV3RecordResolver {
  resolve(query: WorldV3ReadQuery): Promise<readonly WorldV3Record[]>;
}

/** Deterministic resolver for fixtures and embedded read projections. */
export class InMemoryWorldV3RecordResolver implements WorldV3RecordResolver {
  constructor(private readonly records: readonly WorldV3Record[]) {}

  async resolve(query: WorldV3ReadQuery): Promise<readonly WorldV3Record[]> {
    return this.records
      .filter(
        (record) =>
          record.schemaVersion.startsWith("3.") &&
          record.workspaceId === query.workspaceId &&
          record.branchId === query.branchId &&
          (!query.recordIds?.length || query.recordIds.includes(record.id)) &&
          (!query.moduleIds?.length ||
            Boolean(
              record.moduleId && query.moduleIds.includes(record.moduleId),
            )) &&
          (!query.kinds?.length || query.kinds.includes(record.kind)),
      )
      .sort((left, right) => left.id.localeCompare(right.id));
  }
}

/**
 * Visual language is a v3 expression-manifestation projection, not a second
 * canonical manifest. Evidence and sources remain reachable through the compiler.
 */
export class WorldV3VisualLanguageResolver {
  constructor(
    private readonly world: WorldV3RecordResolver,
    private readonly moduleIds: readonly string[] = [
      "expression-manifestation",
    ],
  ) {}

  resolve(
    query: Omit<WorldV3ReadQuery, "moduleIds">,
  ): Promise<readonly WorldV3Record[]> {
    return this.world.resolve({ ...query, moduleIds: [...this.moduleIds] });
  }
}
