import type {
  AuthorityGrantRejection,
  ContextRequestV2,
  ResolvedAuthorityGrant,
  RouteDefinition,
} from "./contracts.js";

export interface AuthorityEvaluationResult {
  authorized: boolean;
  acceptedGrantRefs: string[];
  missingGrantRefs: string[];
  rejections: AuthorityGrantRejection[];
}

function rejection(
  grantRef: string,
  reason: AuthorityGrantRejection["reason"],
  detail: string,
): AuthorityGrantRejection {
  return { grantRef, reason, detail };
}

function validateGrant(
  grant: ResolvedAuthorityGrant,
  request: ContextRequestV2,
  route: RouteDefinition,
): AuthorityGrantRejection | undefined {
  if (grant.status !== "active")
    return rejection(grant.id, "inactive_grant", "grant is not active");
  if (!request.principalRef || grant.principalRef !== request.principalRef)
    return rejection(
      grant.id,
      "wrong_principal",
      "grant is not bound to the requesting principal",
    );
  if (grant.agentDefinitionRef !== request.agentDefinitionRef)
    return rejection(
      grant.id,
      "wrong_agent",
      "grant is not bound to the requesting agent definition",
    );
  const compiledAt = Date.parse(request.compiledAt);
  const validFrom = Date.parse(grant.validFrom);
  const validUntil = grant.validUntil
    ? Date.parse(grant.validUntil)
    : undefined;
  if (
    !Number.isFinite(validFrom) ||
    (validUntil !== undefined &&
      (!Number.isFinite(validUntil) || validUntil <= validFrom))
  )
    return rejection(
      grant.id,
      "invalid_grant",
      "grant validity interval is malformed",
    );
  if (compiledAt < validFrom)
    return rejection(grant.id, "not_yet_valid", "grant validity has not begun");
  if (validUntil !== undefined && compiledAt >= validUntil)
    return rejection(grant.id, "expired", "grant validity has ended");
  const capabilities = route.requiredAuthorityCapabilities ?? ["world:read"];
  const missingCapabilities = capabilities.filter(
    (capability) => !grant.capabilities.includes(capability),
  );
  if (missingCapabilities.length)
    return rejection(
      grant.id,
      "wrong_capability",
      `missing capabilities: ${missingCapabilities.join(", ")}`,
    );
  if (grant.scope.workspaceId !== request.workspaceId)
    return rejection(
      grant.id,
      "wrong_workspace",
      `grant workspace ${grant.scope.workspaceId} does not match ${request.workspaceId}`,
    );
  if (
    grant.scope.branchIds?.length &&
    !grant.scope.branchIds.includes(request.branchId)
  )
    return rejection(
      grant.id,
      "wrong_branch",
      `grant does not cover branch ${request.branchId}`,
    );
  const requestedModules = request.scope.moduleIds?.length
    ? request.scope.moduleIds
    : route.startModuleIds;
  if (
    grant.scope.moduleIds?.length &&
    (!requestedModules.length ||
      requestedModules.some(
        (moduleId) => !grant.scope.moduleIds?.includes(moduleId),
      ))
  )
    return rejection(
      grant.id,
      "wrong_module_scope",
      "grant does not cover every requested start module",
    );
  if (grant.scope.objectIds?.length) {
    const requestedObjects = request.scope.seedRecordIds ?? [];
    if (
      !requestedObjects.length ||
      requestedObjects.some(
        (objectId) => !grant.scope.objectIds?.includes(objectId),
      )
    )
      return rejection(
        grant.id,
        "wrong_object_scope",
        "object-scoped grant does not cover the requested seed objects",
      );
  }
  if (grant.scope.contextRefs?.length) {
    const requestedContexts = request.scope.contextRefs ?? [];
    if (
      !requestedContexts.length ||
      requestedContexts.some(
        (contextRef) => !grant.scope.contextRefs?.includes(contextRef),
      )
    )
      return rejection(
        grant.id,
        "wrong_context_scope",
        "context-scoped grant does not cover the requested contexts",
      );
  }
  return undefined;
}

/** Verify request references against grants resolved by a trusted provider boundary. */
export function evaluateResolvedAuthority(
  request: ContextRequestV2,
  route: RouteDefinition,
  resolvedGrants: readonly ResolvedAuthorityGrant[],
): AuthorityEvaluationResult {
  const mandatory = route.mandatoryGates.includes("authority");
  if (!mandatory && !request.authorityGrantRefs.length)
    return {
      authorized: true,
      acceptedGrantRefs: [],
      missingGrantRefs: [],
      rejections: [],
    };

  const byId = new Map(resolvedGrants.map((grant) => [grant.id, grant]));
  const rejections: AuthorityGrantRejection[] = [];
  const missingGrantRefs: string[] = [];
  for (const requiredRef of route.requiredAuthorityGrantRefs ?? []) {
    if (!request.authorityGrantRefs.includes(requiredRef)) {
      missingGrantRefs.push(requiredRef);
      rejections.push(
        rejection(
          requiredRef,
          "missing_request_ref",
          "route-required grant is absent from the request",
        ),
      );
    }
  }
  if (mandatory && !request.authorityGrantRefs.length)
    rejections.push(
      rejection(
        "<none>",
        "missing_request_ref",
        "authority-mandatory route requires at least one grant reference",
      ),
    );

  const acceptedGrantRefs: string[] = [];
  for (const grantRef of request.authorityGrantRefs) {
    const grant = byId.get(grantRef);
    if (!grant) {
      missingGrantRefs.push(grantRef);
      rejections.push(
        rejection(
          grantRef,
          "unknown_grant",
          "request reference has no resolved authority grant",
        ),
      );
      continue;
    }
    const invalid = validateGrant(grant, request, route);
    if (invalid) rejections.push(invalid);
    else acceptedGrantRefs.push(grantRef);
  }
  return {
    authorized:
      rejections.length === 0 && (!mandatory || acceptedGrantRefs.length > 0),
    acceptedGrantRefs,
    missingGrantRefs: [...new Set(missingGrantRefs)],
    rejections,
  };
}
