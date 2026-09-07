import { randomUUID } from "node:crypto";
import type {
  Citation,
  ContextPacket,
  ContextRequest,
  ContextTraceEvent,
  ContextTraceStore,
  IntelligenceConfiguration,
  IntelligenceModel,
  KnowledgeRetriever,
  KnowledgeStatement,
  NormalizedRequest,
  RetrievedKnowledge,
  RetrievalQuery,
  ResolvedVisualLanguage,
  WorkflowRecipe,
  VisualLanguageRequest,
  VisualLanguageResolver,
  ResolvedWorldView,
  WorldViewResolver,
} from "./contracts.js";
import { filterRetrievedKnowledge } from "./filter.js";

const INTERPRET_SYSTEM = `You interpret an agent request for a context retrieval system. Preserve uncertainty. Never invent missing inputs. Select only a supplied workflow stage.`;
const SYNTHESIZE_SYSTEM = `You compile evidence for another agent. Every statement must cite one or more retrieval IDs supplied in allowedEvidenceIds. The optional worldView is a bounded branch, context, perspective, and reasoning-scope selection; use it to determine relevance and constraints, but never treat it as citation-free evidence. Never use identifiers found inside the source text. Return only task-relevant, evidence-grounded context. Do not create the requested asset, reveal chain-of-thought, or add facts absent from evidence.`;
const MAX_STATEMENTS_PER_SECTION = 2;
const ENTITY_ID_PATTERN = /\bENT-[A-Z0-9-]+\b/g;

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function selectEntityIds(
  request: NormalizedRequest,
  workflow: WorkflowRecipe | undefined,
): string[] {
  const selection = workflow?.entitySelection;
  if (!selection) return [];
  return unique([
    ...selection.always,
    ...selection.conditions.flatMap((condition) => {
      const value = request[condition.field];
      if (typeof value !== "string") return [];
      const lower = value.toLocaleLowerCase();
      return condition.includesAny.some((term) =>
        lower.includes(term.toLocaleLowerCase()),
      )
        ? condition.entityIds
        : [];
    }),
  ]);
}

function applyVisualLanguageAliases(
  request: NormalizedRequest,
  configuration: IntelligenceConfiguration,
): NormalizedRequest {
  const aliases = configuration.visualLanguage;
  if (!aliases) return request;
  const searchable = [
    request.prompt,
    request.audience,
    request.objective,
    request.offerId,
  ]
    .filter(Boolean)
    .join(" ")
    .toLocaleLowerCase();
  const segmentIds = unique([
    ...(request.audienceSegmentIds ?? []),
    ...(aliases.audienceSegmentAliases ?? []).flatMap((alias) =>
      alias.includesAny.some((term) =>
        searchable.includes(term.toLocaleLowerCase()),
      )
        ? [alias.id]
        : [],
    ),
  ]);
  const offerId =
    request.offerId ??
    aliases.offerAliases?.find((alias) =>
      alias.includesAny.some((term) =>
        searchable.includes(term.toLocaleLowerCase()),
      ),
    )?.id;
  return {
    ...request,
    ...(segmentIds.length ? { audienceSegmentIds: segmentIds } : {}),
    ...(offerId ? { offerId } : {}),
  };
}

function mentionedEntityIds(items: RetrievedKnowledge[]): string[] {
  return unique(
    items.flatMap((item) => item.text.match(ENTITY_ID_PATTERN) ?? []),
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function deterministicStage(
  prompt: string,
  workflows: WorkflowRecipe[],
): string | undefined {
  const lower = prompt.toLocaleLowerCase();
  return workflows.find((workflow) =>
    lower.includes(workflow.stage.replaceAll("_", " ")),
  )?.stage;
}

function normalize(
  request: ContextRequest,
  interpretation: unknown,
  configuration: IntelligenceConfiguration,
): NormalizedRequest {
  const interpreted = isRecord(interpretation) ? interpretation : {};
  return {
    prompt: request.prompt.trim(),
    workspaceId: request.workspaceId ?? configuration.workspaceId,
    ...((request.workflowStage ?? optionalString(interpreted.workflowStage))
      ? {
          workflowStage:
            request.workflowStage ?? optionalString(interpreted.workflowStage),
        }
      : {}),
    ...((request.assetType ?? optionalString(interpreted.assetType))
      ? {
          assetType: request.assetType ?? optionalString(interpreted.assetType),
        }
      : {}),
    ...((request.objective ?? optionalString(interpreted.objective))
      ? {
          objective: request.objective ?? optionalString(interpreted.objective),
        }
      : {}),
    ...((request.audience ?? optionalString(interpreted.audience))
      ? { audience: request.audience ?? optionalString(interpreted.audience) }
      : {}),
    ...(request.audienceSegmentIds?.length
      ? { audienceSegmentIds: request.audienceSegmentIds }
      : {}),
    ...((request.channel ?? optionalString(interpreted.channel))
      ? { channel: request.channel ?? optionalString(interpreted.channel) }
      : {}),
    ...((request.geography ?? optionalString(interpreted.geography))
      ? {
          geography: request.geography ?? optionalString(interpreted.geography),
        }
      : {}),
    ...((request.occasion ?? optionalString(interpreted.occasion))
      ? { occasion: request.occasion ?? optionalString(interpreted.occasion) }
      : {}),
    ...((request.validTime ?? optionalString(interpreted.validTime))
      ? {
          validTime: request.validTime ?? optionalString(interpreted.validTime),
        }
      : {}),
    ...(request.productId ? { productId: request.productId } : {}),
    ...(request.campaignId ? { campaignId: request.campaignId } : {}),
    ...(request.offerId ? { offerId: request.offerId } : {}),
    ...(request.visualLanguageProfileId
      ? { visualLanguageProfileId: request.visualLanguageProfileId }
      : {}),
    ...(request.visualLanguageRevisionId
      ? { visualLanguageRevisionId: request.visualLanguageRevisionId }
      : {}),
    ...(request.contextId ? { contextId: request.contextId } : {}),
    ...(request.branchId ? { branchId: request.branchId } : {}),
    ...(request.perspectiveIds?.length
      ? { perspectiveIds: unique(request.perspectiveIds) }
      : {}),
  } as NormalizedRequest;
}

function emptyKnowledge(
  sections: string[],
): Record<string, KnowledgeStatement[]> {
  return Object.fromEntries(sections.map((section) => [section, []]));
}

function citations(items: RetrievedKnowledge[]): Citation[] {
  return items.flatMap((item) =>
    item.sourceUrl ? [{ evidenceId: item.id, sourceUrl: item.sourceUrl }] : [],
  );
}

function fallbackKnowledge(
  items: RetrievedKnowledge[],
  sections: string[],
): Record<string, KnowledgeStatement[]> {
  const knowledge = emptyKnowledge(sections);
  const section = sections.includes("evidence") ? "evidence" : sections[0];
  if (!section) return knowledge;
  knowledge[section] = items.map((item) => ({
    statement: item.text.slice(0, 1200),
    evidenceIds: [item.id],
  }));
  return knowledge;
}

function validateSynthesis(
  value: unknown,
  sections: string[],
  acceptedIds: Set<string>,
):
  | Pick<ContextPacket, "knowledge" | "conflicts" | "limitations" | "omissions">
  | undefined {
  if (!isRecord(value) || !isRecord(value.knowledge)) return undefined;
  const knowledge = emptyKnowledge(sections);
  for (const section of sections) {
    const entries = value.knowledge[section];
    if (!Array.isArray(entries)) continue;
    knowledge[section] = entries
      .flatMap((entry): KnowledgeStatement[] => {
        if (
          !isRecord(entry) ||
          typeof entry.statement !== "string" ||
          !Array.isArray(entry.evidenceIds)
        )
          return [];
        const evidenceIds = entry.evidenceIds.filter(
          (id): id is string => typeof id === "string" && acceptedIds.has(id),
        );
        return evidenceIds.length
          ? [{ statement: entry.statement, evidenceIds }]
          : [];
      })
      .slice(0, MAX_STATEMENTS_PER_SECTION);
  }
  const strings = (key: string): string[] =>
    Array.isArray(value[key])
      ? value[key].filter((item): item is string => typeof item === "string")
      : [];
  const validated = {
    knowledge,
    conflicts: strings("conflicts"),
    limitations: strings("limitations"),
    omissions: strings("omissions"),
  };
  const statementCount = Object.values(validated.knowledge).flat().length;
  return statementCount > 0 ? validated : undefined;
}

export class ContextIntelligenceEngine {
  constructor(
    readonly configuration: IntelligenceConfiguration,
    readonly model: IntelligenceModel,
    readonly retriever: KnowledgeRetriever,
    readonly traceStore?: ContextTraceStore,
    readonly visualLanguageResolver?: VisualLanguageResolver,
    readonly worldViewResolver?: WorldViewResolver,
  ) {}

  resolveVisualLanguage(
    request: ContextRequest,
  ): ResolvedVisualLanguage | undefined {
    if (
      !this.visualLanguageResolver ||
      !this.configuration.visualLanguage?.enabled
    )
      return undefined;
    const normalized = applyVisualLanguageAliases(
      normalize(
        { ...request, prompt: request.prompt ?? "" },
        {},
        this.configuration,
      ),
      this.configuration,
    );
    return this.visualLanguageResolver.resolve({
      workspaceId: this.configuration.workspaceId,
      brandId: this.configuration.brandId,
      ...(normalized.workflowStage
        ? { workflowStage: normalized.workflowStage }
        : {}),
      ...(normalized.productId ? { productId: normalized.productId } : {}),
      ...(normalized.campaignId ? { campaignId: normalized.campaignId } : {}),
      ...(normalized.offerId ? { offerId: normalized.offerId } : {}),
      ...(normalized.audienceSegmentIds
        ? { audienceSegmentIds: normalized.audienceSegmentIds }
        : {}),
      ...(normalized.channel ? { channel: normalized.channel } : {}),
      ...(normalized.geography ? { geography: normalized.geography } : {}),
      ...(normalized.occasion ? { occasion: normalized.occasion } : {}),
      ...(normalized.validTime ? { validTime: normalized.validTime } : {}),
      ...(normalized.visualLanguageProfileId
        ? { profileId: normalized.visualLanguageProfileId }
        : {}),
      ...(normalized.visualLanguageRevisionId
        ? { revisionId: normalized.visualLanguageRevisionId }
        : {}),
    });
  }

  async compile(
    request: ContextRequest,
    options: {
      activationReason: "automatic" | "explicit";
      signal?: AbortSignal;
    },
  ): Promise<ContextPacket> {
    const runId = randomUUID();
    const startedAt = new Date().toISOString();
    let traceState: ContextPacket["receipt"]["trace"] = {
      runId,
      status: this.traceStore ? "available" : "disabled",
    };
    if (this.traceStore) {
      try {
        await this.traceStore.start({
          version: 1,
          runId,
          startedAt,
          configuration: {
            workspaceId: this.configuration.workspaceId,
            brandId: this.configuration.brandId,
            datasetName: this.configuration.datasetName,
            operators: this.configuration.operators,
          },
          modelId: this.model.id,
        });
      } catch (error) {
        traceState = {
          runId,
          status: "unavailable",
          detail: error instanceof Error ? error.message : "trace start failed",
        };
      }
    }
    const record = async (event: ContextTraceEvent): Promise<void> => {
      if (!this.traceStore || traceState.status !== "available") return;
      try {
        await this.traceStore.append(runId, event);
      } catch (error) {
        traceState = {
          runId,
          status: "unavailable",
          detail:
            error instanceof Error ? error.message : "trace append failed",
        };
      }
    };
    const storeEvidence = async (items: RetrievedKnowledge[]) => {
      if (!this.traceStore || traceState.status !== "available") return [];
      try {
        return await Promise.all(
          items.map((item) => this.traceStore!.putEvidence(runId, item)),
        );
      } catch (error) {
        traceState = {
          runId,
          status: "unavailable",
          detail:
            error instanceof Error ? error.message : "evidence storage failed",
        };
        return [];
      }
    };
    const finish = async (packet: ContextPacket): Promise<ContextPacket> => {
      packet.receipt.trace = traceState;
      await record({ phase: "context_packet", output: packet });
      packet.receipt.trace = traceState;
      return packet;
    };
    let interpretation: unknown = {};
    let interpretationMode: "model" | "deterministic_fallback" = "model";
    try {
      const payload = {
        request,
        subjectScope: this.configuration.subjectScope,
        workflowStages: this.configuration.workflows.map(
          (workflow) => workflow.stage,
        ),
      };
      interpretation = await this.model.completeJson({
        purpose: "interpret",
        system: INTERPRET_SYSTEM,
        payload,
        ...(options.signal ? { signal: options.signal } : {}),
      });
      await record({
        phase: "interpretation",
        input: { system: INTERPRET_SYSTEM, payload },
        output: interpretation,
      });
    } catch (error) {
      interpretationMode = "deterministic_fallback";
      interpretation = {
        workflowStage: deterministicStage(
          request.prompt,
          this.configuration.workflows,
        ),
      };
      await record({
        phase: "interpretation",
        input: { system: INTERPRET_SYSTEM, request },
        output: interpretation,
        error:
          error instanceof Error
            ? error.message
            : "model interpretation failed; deterministic fallback used",
      });
    }
    const normalized = normalize(request, interpretation, this.configuration);
    const workflow = this.configuration.workflows.find(
      (candidate) => candidate.stage === normalized.workflowStage,
    );
    const unresolvedFields = workflow
      ? workflow.requiredInputs.filter(
          (field) => !normalized[field as keyof NormalizedRequest],
        )
      : ["workflowStage"];
    const selectedEntityIds = selectEntityIds(normalized, workflow);
    const baseReceipt = {
      activationReason: options.activationReason,
      intelligenceModel: this.model.id,
      workspaceId: this.configuration.workspaceId,
      brandId: this.configuration.brandId,
      datasetName: this.configuration.datasetName,
      ...(workflow ? { workflowStage: workflow.stage } : {}),
      operators: this.configuration.operators,
      interpretationMode,
      entities: {
        selectedEntityIds,
        retrievedEntityIds: [],
        mentionedEntityIds: [],
        usedEntityIds: [],
      },
      trace: traceState,
    };
    if (normalized.workspaceId !== this.configuration.workspaceId) {
      return finish({
        version: 1,
        status: "no_hit",
        request: normalized,
        unresolvedFields: [],
        knowledge: emptyKnowledge(this.configuration.sections),
        reasoningInstructions: [],
        conflicts: [],
        limitations: [
          "The requested workspace is outside this plugin configuration.",
        ],
        omissions: [],
        clarificationQuestions: [],
        citations: [],
        receipt: {
          ...baseReceipt,
          queries: [],
          acceptedEvidenceIds: [],
          rejected: [],
          evaluators: [
            {
              id: "workspace-isolation",
              passed: true,
              detail: "foreign workspace rejected",
            },
          ],
        },
      });
    }
    if (!workflow || unresolvedFields.length > 0) {
      return finish({
        version: 1,
        status: "needs_clarification",
        request: normalized,
        unresolvedFields,
        knowledge: emptyKnowledge(this.configuration.sections),
        reasoningInstructions: workflow?.reasoningInstructions ?? [],
        conflicts: [],
        limitations: [],
        omissions: [
          "Retrieval was deferred because material workflow inputs are unresolved.",
        ],
        clarificationQuestions: unresolvedFields.map(
          (field) => `What ${field} should this work use?`,
        ),
        citations: [],
        receipt: {
          ...baseReceipt,
          queries: [],
          acceptedEvidenceIds: [],
          rejected: [],
          evaluators: [
            {
              id: "minimum-required-inputs",
              passed: false,
              detail: unresolvedFields.join(", "),
            },
          ],
        },
      });
    }
    let visualLanguage: ResolvedVisualLanguage | undefined;
    if (
      this.visualLanguageResolver &&
      this.configuration.visualLanguage?.enabled &&
      this.configuration.visualLanguage.workflowStages.includes(workflow.stage)
    ) {
      const visualRequestSource = applyVisualLanguageAliases(
        normalized,
        this.configuration,
      );
      const visualRequest: VisualLanguageRequest = {
        workspaceId: this.configuration.workspaceId,
        brandId: this.configuration.brandId,
        workflowStage: workflow.stage,
        ...(normalized.productId ? { productId: normalized.productId } : {}),
        ...(normalized.campaignId ? { campaignId: normalized.campaignId } : {}),
        ...(visualRequestSource.offerId
          ? { offerId: visualRequestSource.offerId }
          : {}),
        ...(visualRequestSource.audienceSegmentIds
          ? { audienceSegmentIds: visualRequestSource.audienceSegmentIds }
          : {}),
        ...(normalized.channel ? { channel: normalized.channel } : {}),
        ...(normalized.geography ? { geography: normalized.geography } : {}),
        ...(normalized.occasion ? { occasion: normalized.occasion } : {}),
        ...(normalized.validTime ? { validTime: normalized.validTime } : {}),
        ...(normalized.visualLanguageProfileId
          ? { profileId: normalized.visualLanguageProfileId }
          : {}),
        ...(normalized.visualLanguageRevisionId
          ? { revisionId: normalized.visualLanguageRevisionId }
          : {}),
      };
      visualLanguage = this.visualLanguageResolver.resolve(visualRequest);
      await record({
        phase: "visual_language",
        input: visualRequest,
        output: visualLanguage,
      });
    }
    let worldView: ResolvedWorldView | undefined;
    if (this.worldViewResolver) {
      const worldViewRequest = {
        workspaceId: this.configuration.workspaceId,
        ...(normalized.contextId ? { contextId: normalized.contextId } : {}),
        ...(normalized.branchId ? { branchId: normalized.branchId } : {}),
        taskType: workflow.stage,
        perspectiveIds: normalized.perspectiveIds ?? [],
        scope: {
          ...(normalized.assetType ? { assetType: normalized.assetType } : {}),
          ...(normalized.audience ? { audience: normalized.audience } : {}),
          ...(normalized.channel ? { channel: normalized.channel } : {}),
          ...(normalized.geography ? { geography: normalized.geography } : {}),
          ...(normalized.occasion ? { occasion: normalized.occasion } : {}),
          ...(normalized.validTime ? { validTime: normalized.validTime } : {}),
        },
        // Entity recipe selection and semantic-record authorization are separate
        // concerns. An injected resolver applies its own recorded permission policy.
        permittedRecordIds: [],
      };
      worldView = await this.worldViewResolver.resolve(worldViewRequest);
      await record({
        phase: "world_view",
        input: worldViewRequest,
        output: worldView,
      });
    }
    const queryTexts = [
      `${normalized.prompt}\nWorkflow: ${workflow.stage}. Goal: ${workflow.goal}.`,
      ...workflow.queryHints.map((hint) => `${hint}. ${normalized.prompt}`),
    ].slice(0, this.configuration.retrieval.maximumQueries);
    const queries: RetrievalQuery[] = queryTexts.map((text) => ({
      text,
      route: workflow.route,
      datasetName: this.configuration.datasetName,
      workspaceId: this.configuration.workspaceId,
      brandId: this.configuration.brandId,
      topK: this.configuration.retrieval.topK,
      retrievalKind: "lexical_chunk",
      ...(normalized.branchId ? { branchId: normalized.branchId } : {}),
      ...(normalized.perspectiveIds?.length
        ? { perspectiveIds: normalized.perspectiveIds }
        : {}),
    }));
    if (visualLanguage?.status !== "no_hit") {
      const revisionIds =
        visualLanguage?.receipt.selectedProfileRevisionIds ?? [];
      const referenceIds = visualLanguage?.receipt.selectedReferenceIds ?? [];
      if (revisionIds.length || referenceIds.length) {
        queries.push({
          text: `visual language profile revisions ${revisionIds.join(" ")} references ${referenceIds.join(" ")}`,
          route: "visual-language",
          datasetName:
            this.configuration.visualLanguage?.datasetName ??
            this.configuration.datasetName,
          workspaceId: this.configuration.workspaceId,
          brandId: this.configuration.brandId,
          topK: Math.min(
            30,
            Math.max(this.configuration.retrieval.topK, referenceIds.length),
          ),
          retrievalKind: "visual_reference",
          revisionIds,
          referenceIds,
          ...(normalized.branchId ? { branchId: normalized.branchId } : {}),
          ...(normalized.perspectiveIds?.length
            ? { perspectiveIds: normalized.perspectiveIds }
            : {}),
        });
      }
    }
    if (selectedEntityIds.length > 0) {
      queries.push({
        text: `exact entity records ${selectedEntityIds.join(" ")}`,
        route: "entity",
        datasetName: this.configuration.datasetName,
        workspaceId: this.configuration.workspaceId,
        brandId: this.configuration.brandId,
        topK: Math.min(
          30,
          Math.max(this.configuration.retrieval.topK, selectedEntityIds.length),
        ),
        retrievalKind: "exact_entity",
        entityIds: selectedEntityIds,
        ...(normalized.branchId ? { branchId: normalized.branchId } : {}),
        ...(normalized.perspectiveIds?.length
          ? { perspectiveIds: normalized.perspectiveIds }
          : {}),
      });
    }
    let retrieved: RetrievedKnowledge[];
    try {
      const resultSets = await Promise.all(
        queries.map(async (query) => {
          const items = await this.retriever.retrieve(query, options.signal);
          const evidenceRefs = await storeEvidence(items);
          await record({
            phase: "retrieval",
            input: query,
            output: items.map(({ text: _text, ...metadata }) => metadata),
            evidenceRefs,
          });
          return items;
        }),
      );
      retrieved = resultSets.flat();
    } catch (error) {
      await record({
        phase: "retrieval",
        input: queries,
        error: error instanceof Error ? error.message : "retriever failed",
      });
      return finish({
        version: 1,
        status: "unavailable",
        request: normalized,
        unresolvedFields: [],
        knowledge: emptyKnowledge(this.configuration.sections),
        reasoningInstructions: workflow.reasoningInstructions,
        conflicts: [],
        limitations: [
          error instanceof Error
            ? error.message
            : "knowledge retriever unavailable",
        ],
        omissions: ["No alternative dataset or web fallback was used."],
        clarificationQuestions: [],
        citations: [],
        receipt: {
          ...baseReceipt,
          queries,
          acceptedEvidenceIds: [],
          rejected: [],
          evaluators: [
            {
              id: "retrieval-availability",
              passed: false,
              detail: "retriever failed",
            },
          ],
        },
      });
    }
    const filtered = filterRetrievedKnowledge(
      retrieved,
      normalized,
      this.configuration,
    );
    await record({
      phase: "filter",
      input: { retrievedEvidenceIds: retrieved.map((item) => item.id) },
      output: {
        acceptedEvidenceIds: filtered.accepted.map((item) => item.id),
        rejected: filtered.rejected,
      },
    });
    if (filtered.accepted.length === 0) {
      return finish({
        version: 1,
        status: "no_hit",
        request: normalized,
        unresolvedFields: [],
        knowledge: emptyKnowledge(this.configuration.sections),
        reasoningInstructions: workflow.reasoningInstructions,
        conflicts: [],
        limitations: [],
        omissions: [
          "No eligible evidence was retrieved from the configured dataset.",
        ],
        clarificationQuestions: [],
        citations: [],
        receipt: {
          ...baseReceipt,
          queries,
          acceptedEvidenceIds: [],
          rejected: filtered.rejected,
          evaluators: [
            {
              id: "retrieval-eligibility",
              passed: true,
              detail: "valid no-hit",
            },
          ],
        },
      });
    }
    const retrievedEntityIds = unique(
      filtered.accepted.flatMap((item) => item.entityIds ?? []),
    );
    const mentionedIds = mentionedEntityIds(
      filtered.accepted.filter((item) => item.retrievalKind !== "exact_entity"),
    );
    let synthesized: ReturnType<typeof validateSynthesis>;
    try {
      const payload = {
        request: normalized,
        workflow,
        visualLanguage,
        // This is a bounded, deterministic selection of canonical semantic
        // records. It is distinct from retrieved evidence and must reach the
        // synthesis model so the model can apply its branch/perspective scope.
        worldView,
        sections: this.configuration.sections,
        allowedEvidenceIds: filtered.accepted.map((item) => item.id),
        evidence: filtered.accepted,
      };
      const response = await this.model.completeJson({
        purpose: "synthesize",
        system: SYNTHESIZE_SYSTEM,
        payload,
        ...(options.signal ? { signal: options.signal } : {}),
      });
      const evidenceRefs = await storeEvidence(filtered.accepted);
      await record({
        phase: "synthesis",
        input: {
          system: SYNTHESIZE_SYSTEM,
          payload: { ...payload, evidence: undefined },
        },
        evidenceRefs,
        output: response,
      });
      synthesized = validateSynthesis(
        response,
        this.configuration.sections,
        new Set(filtered.accepted.map((item) => item.id)),
      );
    } catch (error) {
      synthesized = undefined;
      await record({
        phase: "synthesis",
        error:
          error instanceof Error
            ? error.message
            : "model synthesis failed; lexical fallback used",
      });
    }
    const usedFallback = !synthesized;
    const usedEvidenceIds = usedFallback
      ? filtered.accepted.map((item) => item.id)
      : unique(
          Object.values(synthesized?.knowledge ?? {})
            .flat()
            .flatMap((statement) => statement.evidenceIds),
        );
    const usedEntityIds = unique(
      filtered.accepted
        .filter((item) => usedEvidenceIds.includes(item.id))
        .flatMap((item) => item.entityIds ?? []),
    );
    return finish({
      version: 1,
      status:
        usedFallback || interpretationMode === "deterministic_fallback"
          ? "partial"
          : "ready",
      request: normalized,
      unresolvedFields: [],
      knowledge:
        synthesized?.knowledge ??
        fallbackKnowledge(filtered.accepted, this.configuration.sections),
      reasoningInstructions: workflow.reasoningInstructions,
      conflicts: synthesized?.conflicts ?? [],
      limitations: [
        ...(synthesized?.limitations ?? []),
        ...(usedFallback
          ? [
              "The intelligence model synthesis failed; exact lexical excerpts are returned.",
            ]
          : []),
      ],
      omissions: synthesized?.omissions ?? [],
      clarificationQuestions: [],
      citations: citations(filtered.accepted),
      receipt: {
        ...baseReceipt,
        entities: {
          selectedEntityIds,
          retrievedEntityIds,
          mentionedEntityIds: mentionedIds,
          usedEntityIds,
        },
        queries,
        acceptedEvidenceIds: filtered.accepted.map((item) => item.id),
        rejected: filtered.rejected,
        evaluators: [
          {
            id: "workspace-isolation",
            passed: true,
            detail: "configured workspace only",
          },
          {
            id: "source-anchor",
            passed: true,
            detail: "all accepted evidence has a source",
          },
          {
            id: "synthesis-evidence-ids",
            passed: !usedFallback,
            detail: usedFallback
              ? "fallback excerpts used"
              : "all statements bounded to accepted ids",
          },
        ],
        ...(visualLanguage
          ? {
              visualLanguage: {
                status: visualLanguage.status,
                profileRevisionIds:
                  visualLanguage.receipt.selectedProfileRevisionIds,
                referenceIds: visualLanguage.receipt.selectedReferenceIds,
              },
            }
          : {}),
        worldView: {
          ...(worldView
            ? {
                viewId: worldView.viewId,
                contextId: worldView.contextId,
                selectedRecordIds: worldView.selectedRecordIds,
                omissions: worldView.omissions,
                unresolvedConflictIds: worldView.unresolvedConflictIds,
              }
            : {}),
          ...(normalized.branchId ? { branchId: normalized.branchId } : {}),
          perspectiveIds: normalized.perspectiveIds ?? [],
          status: worldView ? "resolved" : "not_resolved",
        },
      },
      ...(visualLanguage ? { visualLanguage } : {}),
      ...(worldView ? { worldView } : {}),
    });
  }
}
