import type {
  EventParticipant,
  RelationParticipant,
  TemporalInterval,
  WorldClaimRecord,
  WorldDecisionRecord,
  WorldEvidenceRecord,
  WorldSourceRecord,
  WorldV3Kind,
  WorldV3Lifecycle,
  WorldV3Record,
  WorldV3RecordEnvelope,
} from "./contracts.js";

const KINDS = new Set<WorldV3Kind>([
  "entity",
  "state",
  "event",
  "relation",
  "claim",
  "source",
  "evidence",
  "decision",
]);
const LIFECYCLES = new Set<WorldV3Lifecycle>([
  "proposed",
  "accepted",
  "challenged",
  "superseded",
  "revoked",
  "archived",
]);
const CLAIM_KINDS = new Set([
  "observation",
  "interpretation",
  "hypothesis",
  "proposal",
  "factual_assertion",
  "normative_commitment",
]);
const CONTENT_POLICIES = new Set([
  "retained",
  "bounded_excerpt",
  "live_reference_only",
  "prohibited",
]);
const DECISION_STATUSES = new Set([
  "proposed",
  "approved",
  "rejected",
  "superseded",
]);
const BOUND_SEMANTICS = new Set(["known", "unknown", "unbounded"]);
const TIME_PRECISIONS = new Set(["year", "month", "day", "instant", "unknown"]);
const COMMON_KEYS = new Set([
  "id",
  "kind",
  "type_id",
  "schema_version",
  "record_version",
  "workspace_id",
  "module_id",
  "branch_id",
  "lifecycle_status",
  "valid_time",
  "known_time",
  "context_refs",
  "provenance_refs",
  "derivation_ref",
  "authority_ref",
  "created_at",
  "created_by",
  "supersedes_ref",
]);
const KIND_KEYS: Record<WorldV3Kind, Set<string>> = {
  entity: new Set(["canonical_label", "aliases", "definition"]),
  state: new Set([
    "subject_ids",
    "state_value",
    "state_schema_id",
    "described_by_claim_ids",
  ]),
  event: new Set([
    "event_type_id",
    "participants",
    "occurred_at",
    "evidence_ids",
  ]),
  relation: new Set(["relation_type_id", "participants", "evidence_ids"]),
  claim: new Set([
    "claim_kind",
    "subject_id",
    "predicate_id",
    "object_id",
    "object_value",
    "perspective_id",
    "evidence_ids",
    "opposing_evidence_ids",
    "contradiction_ids",
    "limitations",
    "permitted_task_types",
  ]),
  source: new Set([
    "locator",
    "title",
    "content_policy",
    "captured_at",
    "content_hash",
  ]),
  evidence: new Set([
    "source_id",
    "locator",
    "excerpt",
    "measurement",
    "limitations",
    "integrity_hash",
  ]),
  decision: new Set([
    "question",
    "alternatives",
    "selected_alternative_id",
    "status",
    "rationale",
    "evidence_ids",
    "affected_record_ids",
  ]),
};

export class WorldV3WireDecodeError extends Error {
  constructor(
    readonly path: string,
    message: string,
  ) {
    super(`${path}: ${message}`);
    this.name = "WorldV3WireDecodeError";
  }
}

function object(value: unknown, path: string): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new WorldV3WireDecodeError(path, "expected an object");
  return value as Record<string, unknown>;
}

function string(value: unknown, path: string): string {
  if (typeof value !== "string" || !value.trim())
    throw new WorldV3WireDecodeError(path, "expected a non-empty string");
  return value;
}

function nullableString(value: unknown, path: string): string | undefined {
  return value === null || value === undefined
    ? undefined
    : string(value, path);
}

function member(
  value: unknown,
  allowed: ReadonlySet<string>,
  path: string,
): string {
  const result = string(value, path);
  if (!allowed.has(result))
    throw new WorldV3WireDecodeError(path, `unsupported value ${result}`);
  return result;
}

function timestamp(value: unknown, path: string): string {
  const result = string(value, path);
  if (
    !/^\d{4}-\d{2}-\d{2}T.*(?:Z|[+-]\d{2}:\d{2})$/.test(result) ||
    !Number.isFinite(Date.parse(result))
  )
    throw new WorldV3WireDecodeError(
      path,
      "expected a timezone-aware RFC3339 timestamp",
    );
  return result;
}

function integer(value: unknown, path: string): number {
  if (!Number.isInteger(value) || (value as number) < 1)
    throw new WorldV3WireDecodeError(path, "expected a positive integer");
  return value as number;
}

function strings(value: unknown, path: string): string[] {
  if (!Array.isArray(value))
    throw new WorldV3WireDecodeError(path, "expected an array");
  return value.map((entry, index) => string(entry, `${path}[${index}]`));
}

function optionalStrings(value: unknown, path: string): string[] {
  return value === undefined ? [] : strings(value, path);
}

function nonEmptyStrings(value: unknown, path: string): string[] {
  const result = strings(value, path);
  if (!result.length)
    throw new WorldV3WireDecodeError(path, "expected at least one item");
  return result;
}

function interval(value: unknown, path: string): TemporalInterval | undefined {
  if (value === null || value === undefined) return undefined;
  const input = object(value, path);
  const allowed = new Set([
    "from_time",
    "to_time",
    "from_semantics",
    "to_semantics",
    "precision",
    "source_timezone",
  ]);
  for (const key of Object.keys(input))
    if (!allowed.has(key))
      throw new WorldV3WireDecodeError(
        `${path}.${key}`,
        "unknown temporal field",
      );
  const fromTime = nullableString(input.from_time, `${path}.from_time`);
  const toTime = nullableString(input.to_time, `${path}.to_time`);
  const fromSemantics = member(
    input.from_semantics ?? "unknown",
    BOUND_SEMANTICS,
    `${path}.from_semantics`,
  );
  const toSemantics = member(
    input.to_semantics ?? "unknown",
    BOUND_SEMANTICS,
    `${path}.to_semantics`,
  );
  if (!fromTime && fromSemantics === "known")
    throw new WorldV3WireDecodeError(
      path,
      "from_semantics=known requires from_time",
    );
  if (!toTime && toSemantics === "known")
    throw new WorldV3WireDecodeError(
      path,
      "to_semantics=known requires to_time",
    );
  if (fromTime && fromSemantics !== "known")
    throw new WorldV3WireDecodeError(
      path,
      "from_time requires from_semantics=known",
    );
  if (toTime && toSemantics !== "known")
    throw new WorldV3WireDecodeError(
      path,
      "to_time requires to_semantics=known",
    );
  if (fromTime && toTime && Date.parse(toTime) <= Date.parse(fromTime))
    throw new WorldV3WireDecodeError(
      path,
      "half-open interval requires to_time > from_time",
    );
  return {
    ...(fromTime ? { fromTime: timestamp(fromTime, `${path}.from_time`) } : {}),
    ...(toTime ? { toTime: timestamp(toTime, `${path}.to_time`) } : {}),
    fromSemantics,
    toSemantics,
    precision: member(
      input.precision ?? "unknown",
      TIME_PRECISIONS,
      `${path}.precision`,
    ),
    ...(nullableString(input.source_timezone, `${path}.source_timezone`)
      ? {
          sourceTimezone: string(
            input.source_timezone,
            `${path}.source_timezone`,
          ),
        }
      : {}),
  };
}

function participants(
  value: unknown,
  path: string,
  identifierKey: "record_id",
): RelationParticipant[];
function participants(
  value: unknown,
  path: string,
  identifierKey: "entity_id",
): EventParticipant[];
function participants(
  value: unknown,
  path: string,
  identifierKey: "record_id" | "entity_id",
): Array<RelationParticipant | EventParticipant> {
  if (!Array.isArray(value) || !value.length)
    throw new WorldV3WireDecodeError(
      path,
      "expected a non-empty participant array",
    );
  return value.map((entry, index) => {
    const participant = object(entry, `${path}[${index}]`);
    const allowed = new Set(["role_id", identifierKey]);
    for (const key of Object.keys(participant))
      if (!allowed.has(key))
        throw new WorldV3WireDecodeError(
          `${path}[${index}].${key}`,
          "unknown participant field",
        );
    const identifier = string(
      participant[identifierKey],
      `${path}[${index}].${identifierKey}`,
    );
    return {
      roleId: string(participant.role_id, `${path}[${index}].role_id`),
      ...(identifierKey === "record_id"
        ? { recordId: identifier }
        : { entityId: identifier }),
    };
  });
}

function alternatives(
  value: unknown,
  path: string,
): Array<{ id: string; label: string; rationale?: string }> {
  if (!Array.isArray(value) || !value.length)
    throw new WorldV3WireDecodeError(
      path,
      "expected a non-empty alternatives array",
    );
  return value.map((entry, index) => {
    const alternative = object(entry, `${path}[${index}]`);
    for (const key of Object.keys(alternative))
      if (!["id", "label", "rationale"].includes(key))
        throw new WorldV3WireDecodeError(
          `${path}[${index}].${key}`,
          "unknown alternative field",
        );
    const rationale = nullableString(
      alternative.rationale,
      `${path}[${index}].rationale`,
    );
    return {
      id: string(alternative.id, `${path}[${index}].id`),
      label: string(alternative.label, `${path}[${index}].label`),
      ...(rationale ? { rationale } : {}),
    };
  });
}

/** Decode one canonical Python/Pydantic JSON record into the compiler's camel-case projection. */
export function decodeWorldV3WireRecord(
  value: unknown,
  path = "record",
): WorldV3Record {
  const input = object(value, path);
  const kindValue = string(input.kind, `${path}.kind`);
  if (!KINDS.has(kindValue as WorldV3Kind))
    throw new WorldV3WireDecodeError(
      `${path}.kind`,
      `unsupported kind ${kindValue}`,
    );
  const kind = kindValue as WorldV3Kind;
  for (const key of Object.keys(input))
    if (!COMMON_KEYS.has(key) && !KIND_KEYS[kind].has(key))
      throw new WorldV3WireDecodeError(
        `${path}.${key}`,
        "unknown record field",
      );
  const schemaVersion = string(input.schema_version, `${path}.schema_version`);
  if (!/^3\./.test(schemaVersion))
    throw new WorldV3WireDecodeError(
      `${path}.schema_version`,
      "only World v3 records are accepted",
    );
  const lifecycleValue = string(
    input.lifecycle_status,
    `${path}.lifecycle_status`,
  );
  if (!LIFECYCLES.has(lifecycleValue as WorldV3Lifecycle))
    throw new WorldV3WireDecodeError(
      `${path}.lifecycle_status`,
      "unsupported lifecycle status",
    );
  const common: WorldV3RecordEnvelope = {
    id: string(input.id, `${path}.id`),
    typeId: string(input.type_id, `${path}.type_id`),
    schemaVersion,
    recordVersion: integer(input.record_version, `${path}.record_version`),
    workspaceId: string(input.workspace_id, `${path}.workspace_id`),
    moduleId: string(input.module_id, `${path}.module_id`),
    branchId: string(input.branch_id, `${path}.branch_id`),
    lifecycleStatus: lifecycleValue as WorldV3Lifecycle,
    contextRefs: optionalStrings(input.context_refs, `${path}.context_refs`),
    provenanceRefs: optionalStrings(
      input.provenance_refs,
      `${path}.provenance_refs`,
    ),
    createdAt: timestamp(input.created_at, `${path}.created_at`),
    createdBy: string(input.created_by, `${path}.created_by`),
  };
  const validTime = interval(input.valid_time, `${path}.valid_time`);
  const knownTime = interval(input.known_time, `${path}.known_time`);
  const derivationRef = nullableString(
    input.derivation_ref,
    `${path}.derivation_ref`,
  );
  const authorityRef = nullableString(
    input.authority_ref,
    `${path}.authority_ref`,
  );
  const supersedesRef = nullableString(
    input.supersedes_ref,
    `${path}.supersedes_ref`,
  );
  if (validTime) common.validTime = validTime;
  if (knownTime) common.knownTime = knownTime;
  if (derivationRef) common.derivationRef = derivationRef;
  if (authorityRef) common.authorityRef = authorityRef;
  if (supersedesRef) common.supersedesRef = supersedesRef;
  if (kind === "entity")
    return {
      ...common,
      kind,
      canonicalLabel: string(input.canonical_label, `${path}.canonical_label`),
      aliases: optionalStrings(input.aliases, `${path}.aliases`),
      definition: string(input.definition, `${path}.definition`),
    };
  if (kind === "state")
    return {
      ...common,
      kind,
      subjectIds: nonEmptyStrings(input.subject_ids, `${path}.subject_ids`),
      stateValue: string(input.state_value, `${path}.state_value`),
      stateSchemaId: string(input.state_schema_id, `${path}.state_schema_id`),
      describedByClaimIds: optionalStrings(
        input.described_by_claim_ids,
        `${path}.described_by_claim_ids`,
      ),
    };
  if (kind === "event") {
    const occurredAt = interval(input.occurred_at, `${path}.occurred_at`);
    if (!occurredAt)
      throw new WorldV3WireDecodeError(
        `${path}.occurred_at`,
        "event occurrence time is required",
      );
    return {
      ...common,
      kind,
      eventTypeId: string(input.event_type_id, `${path}.event_type_id`),
      participants: participants(
        input.participants,
        `${path}.participants`,
        "entity_id",
      ),
      occurredAt,
      evidenceIds: optionalStrings(input.evidence_ids, `${path}.evidence_ids`),
    };
  }
  if (kind === "relation") {
    const relationParticipants = participants(
      input.participants,
      `${path}.participants`,
      "record_id",
    );
    if (relationParticipants.length < 2)
      throw new WorldV3WireDecodeError(
        `${path}.participants`,
        "relation requires at least two participants",
      );
    if (
      new Set(relationParticipants.map((participant) => participant.roleId))
        .size !== relationParticipants.length
    )
      throw new WorldV3WireDecodeError(
        `${path}.participants`,
        "relation participant roles must be unique",
      );
    return {
      ...common,
      kind,
      relationTypeId: string(
        input.relation_type_id,
        `${path}.relation_type_id`,
      ),
      participants: relationParticipants,
      evidenceIds: optionalStrings(input.evidence_ids, `${path}.evidence_ids`),
    };
  }
  if (kind === "claim") {
    const objectId = nullableString(input.object_id, `${path}.object_id`);
    const objectValue = nullableString(
      input.object_value,
      `${path}.object_value`,
    );
    if (Boolean(objectId) === Boolean(objectValue))
      throw new WorldV3WireDecodeError(
        path,
        "claim requires exactly one of object_id or object_value",
      );
    const evidenceIds = optionalStrings(
      input.evidence_ids,
      `${path}.evidence_ids`,
    );
    const opposingEvidenceIds = optionalStrings(
      input.opposing_evidence_ids,
      `${path}.opposing_evidence_ids`,
    );
    if (evidenceIds.some((id) => opposingEvidenceIds.includes(id)))
      throw new WorldV3WireDecodeError(
        path,
        "evidence cannot both support and oppose a claim",
      );
    const perspectiveId = nullableString(
      input.perspective_id,
      `${path}.perspective_id`,
    );
    const result: WorldClaimRecord = {
      ...common,
      kind,
      claimKind: member(
        input.claim_kind,
        CLAIM_KINDS,
        `${path}.claim_kind`,
      ) as WorldClaimRecord["claimKind"],
      subjectId: string(input.subject_id, `${path}.subject_id`),
      predicateId: string(input.predicate_id, `${path}.predicate_id`),
      evidenceIds,
      opposingEvidenceIds,
      contradictionIds: optionalStrings(
        input.contradiction_ids,
        `${path}.contradiction_ids`,
      ),
      limitations: optionalStrings(input.limitations, `${path}.limitations`),
      permittedTaskTypes: optionalStrings(
        input.permitted_task_types,
        `${path}.permitted_task_types`,
      ),
    };
    if (objectId) result.objectId = objectId;
    if (objectValue) result.objectValue = objectValue;
    if (perspectiveId) result.perspectiveId = perspectiveId;
    return result;
  }
  if (kind === "source") {
    const contentHash = nullableString(
      input.content_hash,
      `${path}.content_hash`,
    );
    const result: WorldSourceRecord = {
      ...common,
      kind,
      locator: string(input.locator, `${path}.locator`),
      title: string(input.title, `${path}.title`),
      contentPolicy: member(
        input.content_policy,
        CONTENT_POLICIES,
        `${path}.content_policy`,
      ) as WorldSourceRecord["contentPolicy"],
      capturedAt: timestamp(input.captured_at, `${path}.captured_at`),
      ...(contentHash ? { contentHash } : {}),
    };
    return result;
  }
  if (kind === "evidence") {
    const excerpt = nullableString(input.excerpt, `${path}.excerpt`);
    const measurement = nullableString(
      input.measurement,
      `${path}.measurement`,
    );
    if (!excerpt && !measurement)
      throw new WorldV3WireDecodeError(
        path,
        "evidence requires an excerpt or measurement",
      );
    const integrityHash = nullableString(
      input.integrity_hash,
      `${path}.integrity_hash`,
    );
    const result: WorldEvidenceRecord = {
      ...common,
      kind,
      sourceId: string(input.source_id, `${path}.source_id`),
      locator: string(input.locator, `${path}.locator`),
      limitations: optionalStrings(input.limitations, `${path}.limitations`),
      ...(excerpt ? { excerpt } : {}),
      ...(measurement ? { measurement } : {}),
      ...(integrityHash ? { integrityHash } : {}),
    };
    return result;
  }
  const selectedAlternativeId = nullableString(
    input.selected_alternative_id,
    `${path}.selected_alternative_id`,
  );
  const rationale = nullableString(input.rationale, `${path}.rationale`);
  const decisionStatus = member(
    input.status,
    DECISION_STATUSES,
    `${path}.status`,
  );
  const decisionAlternatives = alternatives(
    input.alternatives,
    `${path}.alternatives`,
  );
  if (
    selectedAlternativeId &&
    !decisionAlternatives.some(
      (alternative) => alternative.id === selectedAlternativeId,
    )
  )
    throw new WorldV3WireDecodeError(
      path,
      "selected_alternative_id must identify a declared alternative",
    );
  if (
    decisionStatus === "approved" &&
    (!selectedAlternativeId || !common.authorityRef)
  )
    throw new WorldV3WireDecodeError(
      path,
      "approved decision requires a selection and authority_ref",
    );
  const result: WorldDecisionRecord = {
    ...common,
    kind,
    question: string(input.question, `${path}.question`),
    alternatives: decisionAlternatives,
    status: decisionStatus as WorldDecisionRecord["status"],
    evidenceIds: optionalStrings(input.evidence_ids, `${path}.evidence_ids`),
    affectedRecordIds: optionalStrings(
      input.affected_record_ids,
      `${path}.affected_record_ids`,
    ),
    ...(selectedAlternativeId ? { selectedAlternativeId } : {}),
    ...(rationale ? { rationale } : {}),
  };
  return result;
}

export function decodeWorldV3WireRecords(value: unknown): WorldV3Record[] {
  if (!Array.isArray(value))
    throw new WorldV3WireDecodeError("records", "expected an array");
  return value.map((record, index) =>
    decodeWorldV3WireRecord(record, `records[${index}]`),
  );
}

/** Decode either a records array or the records payload of a canonical proposal bundle. */
export function decodeWorldV3WireBundle(value: unknown): WorldV3Record[] {
  if (Array.isArray(value)) return decodeWorldV3WireRecords(value);
  const bundle = object(value, "bundle");
  const records = decodeWorldV3WireRecords(bundle.records);
  const workspaceId = nullableString(
    bundle.workspace_id,
    "bundle.workspace_id",
  );
  const branchId = nullableString(bundle.branch_id, "bundle.branch_id");
  if (
    workspaceId &&
    records.some((record) => record.workspaceId !== workspaceId)
  )
    throw new WorldV3WireDecodeError(
      "bundle.records",
      "record workspace does not match bundle workspace_id",
    );
  if (branchId && records.some((record) => record.branchId !== branchId))
    throw new WorldV3WireDecodeError(
      "bundle.records",
      "record branch does not match bundle branch_id",
    );
  return records;
}
