import type {
  ResolvedVisualLanguage,
  VisualLanguageBinding,
  VisualLanguageManifest,
  VisualLanguageRequest,
  VisualLanguageResolver,
  VisualLanguageRevision,
  VisualLanguageAuthority,
  VisualLanguageProfile,
  VisualModuleSelection,
  VisualReference,
} from "./contracts.js";

const authorityWeight: Record<VisualLanguageAuthority, number> = {
  authorized_internal: 5,
  official_public: 4,
  observed_public: 3,
  inferred: 2,
  generated_proposal: 1,
};

function includesDate(
  validTime: string | undefined,
  validFrom: string | undefined,
  validUntil: string | undefined,
): boolean {
  if (!validTime) return true;
  if (validFrom && validTime < validFrom) return false;
  if (validUntil && validTime > validUntil) return false;
  return true;
}

function containsAll(
  haystack: string[] | undefined,
  needles: string[],
): boolean {
  if (!needles.length) return true;
  if (!haystack?.length) return false;
  return needles.every((needle) => haystack.includes(needle));
}

function scopeMatches(
  scope: VisualLanguageBinding["scope"],
  request: VisualLanguageRequest,
): boolean {
  if (scope.brandId !== request.brandId) return false;
  if (scope.productId && scope.productId !== request.productId) return false;
  if (scope.campaignId && scope.campaignId !== request.campaignId) return false;
  if (scope.offerId && scope.offerId !== request.offerId) return false;
  if (scope.channel && scope.channel !== request.channel) return false;
  if (scope.geography && scope.geography !== request.geography) return false;
  if (scope.occasion && scope.occasion !== request.occasion) return false;
  if (
    scope.workflowStages?.length &&
    (!request.workflowStage ||
      !scope.workflowStages.includes(request.workflowStage))
  )
    return false;
  if (!containsAll(request.audienceSegmentIds, scope.audienceSegmentIds ?? []))
    return false;
  return true;
}

function scopeSpecificity(scope: VisualLanguageBinding["scope"]): number {
  return [
    scope.productId,
    scope.campaignId,
    scope.offerId,
    scope.audienceSegmentIds?.length ? "audience" : undefined,
    scope.channel,
    scope.geography,
    scope.occasion,
    scope.workflowStages?.length ? "workflow" : undefined,
  ].filter(Boolean).length;
}

function compareBindings(
  left: VisualLanguageBinding,
  right: VisualLanguageBinding,
  revisions: Map<string, VisualLanguageRevision>,
): number {
  const leftRevision = revisions.get(left.revisionId);
  const rightRevision = revisions.get(right.revisionId);
  const leftAuthority = leftRevision
    ? authorityWeight[leftRevision.authority]
    : 0;
  const rightAuthority = rightRevision
    ? authorityWeight[rightRevision.authority]
    : 0;
  return (
    right.priority - left.priority ||
    scopeSpecificity(right.scope) - scopeSpecificity(left.scope) ||
    rightAuthority - leftAuthority ||
    (rightRevision?.revision ?? 0) - (leftRevision?.revision ?? 0) ||
    left.id.localeCompare(right.id)
  );
}

function active<T extends { status: string }>(value: T): boolean {
  return value.status !== "archived";
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function citationPairs(
  revisions: VisualLanguageRevision[],
  references: VisualReference[],
): Array<{ evidenceId: string; sourceId: string }> {
  return [...revisions, ...references].flatMap((item) =>
    item.evidenceIds.flatMap((evidenceId, index) => ({
      evidenceId,
      sourceId: item.sourceIds[index] ?? item.sourceIds[0] ?? "",
    })),
  );
}

export class JsonVisualLanguageResolver implements VisualLanguageResolver {
  readonly #manifest: VisualLanguageManifest;

  constructor(manifest: VisualLanguageManifest) {
    validateVisualLanguageManifest(manifest);
    this.#manifest = manifest;
  }

  resolve(request: VisualLanguageRequest): ResolvedVisualLanguage {
    if (request.workspaceId !== this.#manifest.workspaceId) {
      return noHit(
        request,
        "Requested workspace is outside the visual-language manifest.",
      );
    }
    if (request.brandId !== this.#manifest.brandId) {
      return noHit(
        request,
        "Requested brand is outside the visual-language manifest.",
      );
    }
    const profiles = new Map(
      this.#manifest.profiles
        .filter(active)
        .map((profile) => [profile.id, profile]),
    );
    const revisions = new Map(
      this.#manifest.revisions
        .filter(active)
        .filter((revision) =>
          includesDate(
            request.validTime,
            revision.validFrom,
            revision.validUntil,
          ),
        )
        .map((revision) => [revision.id, revision]),
    );
    const references = new Map(
      this.#manifest.references
        .filter(active)
        .filter((reference) =>
          includesDate(
            request.validTime,
            reference.validFrom,
            reference.validUntil,
          ),
        )
        .map((reference) => [reference.id, reference]),
    );
    if (request.profileId && !profiles.has(request.profileId)) {
      return noHit(
        request,
        "Requested visual-language profile does not exist.",
      );
    }
    if (request.revisionId && !revisions.has(request.revisionId)) {
      return noHit(
        request,
        "Requested visual-language revision is not valid for this time.",
      );
    }
    const matching = this.#manifest.bindings
      .filter(active)
      .filter((binding) =>
        includesDate(request.validTime, binding.validFrom, binding.validUntil),
      )
      .filter((binding) => scopeMatches(binding.scope, request))
      .filter(
        (binding) =>
          !request.profileId || binding.profileId === request.profileId,
      )
      .filter(
        (binding) =>
          !request.revisionId || binding.revisionId === request.revisionId,
      )
      .filter((binding) => revisions.has(binding.revisionId))
      .sort((left, right) => compareBindings(left, right, revisions));
    if (!matching.length)
      return noHit(
        request,
        "No visual-language binding matches this scope and time.",
      );

    const selected: VisualLanguageBinding[] = [];
    const selectedProfiles = new Set<string>();
    const excludedBindingIds: string[] = [];
    for (const binding of matching) {
      if (selectedProfiles.has(binding.profileId)) {
        excludedBindingIds.push(binding.id);
        continue;
      }
      selectedProfiles.add(binding.profileId);
      selected.push(binding);
    }
    const ordered = [...selected].sort((left, right) => {
      const leftRevision = revisions.get(left.revisionId)!;
      const rightRevision = revisions.get(right.revisionId)!;
      return (
        scopeSpecificity(left.scope) - scopeSpecificity(right.scope) ||
        left.priority - right.priority ||
        left.id.localeCompare(right.id)
      );
    });
    const modules = new Map<string, VisualReference[]>();
    const slotOwners = new Map<string, VisualLanguageBinding>();
    const conflicts: string[] = [];
    const omissions: string[] = [];
    const resolvedRevisionIds: string[] = [];
    const resolvedReferenceIds: string[] = [];
    for (const binding of ordered) {
      const revision = revisions.get(binding.revisionId);
      if (!revision) continue;
      resolvedRevisionIds.push(revision.id);
      omissions.push(
        ...(revision.gaps ?? []).map(
          (gap) => `The visual-language pack does not establish ${gap}.`,
        ),
      );
      for (const module of revision.modules) {
        const reference = references.get(module.referenceId);
        if (!reference) {
          omissions.push(
            `Reference ${module.referenceId} is missing or invalid for the requested time.`,
          );
          continue;
        }
        if (reference.rights.permittedUse === "none") {
          omissions.push(
            `Reference ${reference.id} is excluded because its rights prohibit use.`,
          );
          continue;
        }
        const current = modules.get(module.slot) ?? [];
        if (module.mode === "disable") {
          modules.delete(module.slot);
          continue;
        }
        if (module.mode === "replace" && current.length > 0) {
          const owner = slotOwners.get(module.slot);
          if (
            owner &&
            scopeSpecificity(owner.scope) === scopeSpecificity(binding.scope) &&
            owner.priority === binding.priority
          ) {
            conflicts.push(
              `Module ${module.slot} has incompatible replacements from ${owner.id} and ${binding.id}.`,
            );
            continue;
          }
          modules.set(module.slot, []);
        }
        const next = modules.get(module.slot) ?? [];
        if (!next.some((item) => item.id === reference.id))
          next.push(reference);
        modules.set(module.slot, next);
        slotOwners.set(module.slot, binding);
        resolvedReferenceIds.push(reference.id);
      }
    }
    const selectedReferences = [...modules.values()].flat();
    const selectedProfilesList = ordered.flatMap((binding) => {
      const profile = profiles.get(binding.profileId);
      return profile ? [profile] : [];
    });
    const status = conflicts.length
      ? "needs_clarification"
      : omissions.length || excludedBindingIds.length
        ? "partial"
        : "ready";
    return {
      status,
      request,
      profiles: selectedProfilesList,
      revisions: ordered.flatMap((binding) => {
        const revision = revisions.get(binding.revisionId);
        return revision ? [revision] : [];
      }),
      references: selectedReferences,
      conflicts,
      omissions: unique(omissions),
      citations: citationPairs(
        ordered.flatMap((binding) => {
          const revision = revisions.get(binding.revisionId);
          return revision ? [revision] : [];
        }),
        selectedReferences,
      ),
      receipt: {
        selectedBindingIds: selected.map((binding) => binding.id),
        selectedProfileRevisionIds: unique(resolvedRevisionIds),
        selectedReferenceIds: unique(resolvedReferenceIds),
        excludedReferenceIds: excludedBindingIds,
        precedence: ordered.map((binding) => binding.id),
      },
    };
  }
}

function noHit(
  request: VisualLanguageRequest,
  omission: string,
): ResolvedVisualLanguage {
  return {
    status: "no_hit",
    request,
    profiles: [],
    revisions: [],
    references: [],
    conflicts: [],
    omissions: [omission],
    citations: [],
    receipt: {
      selectedBindingIds: [],
      selectedProfileRevisionIds: [],
      selectedReferenceIds: [],
      excludedReferenceIds: [],
      precedence: [],
    },
  };
}

export function validateVisualLanguageManifest(
  manifest: VisualLanguageManifest,
): void {
  if (manifest.version !== 1)
    throw new Error("unsupported visual-language manifest version");
  if (!manifest.workspaceId || !manifest.brandId)
    throw new Error(
      "visual-language manifest requires workspace and brand ids",
    );
  const uniqueIds = (values: string[], label: string) => {
    if (
      values.some((value) => !value) ||
      new Set(values).size !== values.length
    )
      throw new Error(
        `visual-language ${label} ids must be unique and non-empty`,
      );
  };
  uniqueIds(
    manifest.profiles.map((item) => item.id),
    "profile",
  );
  uniqueIds(
    manifest.revisions.map((item) => item.id),
    "revision",
  );
  uniqueIds(
    manifest.references.map((item) => item.id),
    "reference",
  );
  uniqueIds(
    manifest.bindings.map((item) => item.id),
    "binding",
  );
  const profileIds = new Set(manifest.profiles.map((item) => item.id));
  const revisionIds = new Set(manifest.revisions.map((item) => item.id));
  const referenceIds = new Set(manifest.references.map((item) => item.id));
  for (const revision of manifest.revisions) {
    if (!profileIds.has(revision.profileId))
      throw new Error(`revision ${revision.id} references unknown profile`);
    for (const module of revision.modules) {
      if (!module.slot || !referenceIds.has(module.referenceId))
        throw new Error(`revision ${revision.id} references an invalid module`);
    }
  }
  for (const binding of manifest.bindings) {
    if (
      !profileIds.has(binding.profileId) ||
      !revisionIds.has(binding.revisionId)
    )
      throw new Error(
        `binding ${binding.id} references an unknown profile or revision`,
      );
    if (binding.scope.brandId !== manifest.brandId)
      throw new Error(
        `binding ${binding.id} crosses the manifest brand boundary`,
      );
  }
  for (const reference of manifest.references) {
    if (
      !reference.kind ||
      !reference.label ||
      !reference.recordedAt ||
      !reference.lastVerifiedAt
    )
      throw new Error(`reference ${reference.id} is missing required metadata`);
    if (!reference.sourceIds.length || !reference.evidenceIds.length)
      throw new Error(
        `reference ${reference.id} requires source and evidence anchors`,
      );
    if (reference.rights.permittedUse === "none" && reference.assetRefs.length)
      throw new Error(
        `reference ${reference.id} cannot expose assets with no permitted use`,
      );
  }
}
