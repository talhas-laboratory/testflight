import type {
  IntelligenceConfiguration,
  NormalizedRequest,
  RejectedKnowledge,
  RetrievedKnowledge,
} from "./contracts.js";

export interface FilterResult {
  accepted: RetrievedKnowledge[];
  rejected: RejectedKnowledge[];
}

function dateOutsideRequest(
  item: RetrievedKnowledge,
  validTime?: string,
): boolean {
  if (!validTime || !/^\d{4}-\d{2}-\d{2}$/.test(validTime)) return false;
  if (item.validFrom && validTime < item.validFrom) return true;
  if (item.validThrough && validTime > item.validThrough) return true;
  return false;
}

function branchOutsideRequest(
  item: RetrievedKnowledge,
  branchId?: string,
): boolean {
  if (!branchId) return false;
  return Boolean(item.branchId && item.branchId !== branchId);
}

function perspectiveOutsideRequest(
  item: RetrievedKnowledge,
  perspectiveIds?: string[],
): boolean {
  if (!perspectiveIds?.length || !item.perspectiveIds?.length) return false;
  return !item.perspectiveIds.some((id) => perspectiveIds.includes(id));
}

export function filterRetrievedKnowledge(
  items: RetrievedKnowledge[],
  request: NormalizedRequest,
  configuration: IntelligenceConfiguration,
): FilterResult {
  const accepted: RetrievedKnowledge[] = [];
  const rejected: RejectedKnowledge[] = [];
  const seen = new Set<string>();
  for (const item of items) {
    let reason: string | undefined;
    if (seen.has(item.id)) reason = "duplicate evidence id";
    else if (item.workspaceId && item.workspaceId !== configuration.workspaceId)
      reason = "wrong workspace";
    else if (item.brandId && item.brandId !== configuration.brandId)
      reason = "wrong brand";
    else if (!item.sourceUrl) reason = "missing source anchor";
    else if (
      configuration.retrieval.navigationSourcePatterns.some((pattern) =>
        item.sourceUrl
          ?.toLocaleLowerCase()
          .includes(pattern.toLocaleLowerCase()),
      )
    )
      reason = "navigation or configuration document";
    else if (dateOutsideRequest(item, request.validTime))
      reason = "clear valid-time mismatch";
    else if (branchOutsideRequest(item, request.branchId))
      reason = "wrong branch";
    else if (perspectiveOutsideRequest(item, request.perspectiveIds))
      reason = "wrong perspective";
    else if (!item.text.trim()) reason = "empty retrieval";

    seen.add(item.id);
    if (reason)
      rejected.push({
        id: item.id,
        reason,
        ...(item.sourceUrl ? { sourceUrl: item.sourceUrl } : {}),
      });
    else accepted.push(item);
  }
  return { accepted, rejected };
}
