import { existsSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import z from "@deepseek-ai/schemastery";
import type { Context } from "@deepseek-ai/cordis";
import "@deepseek-ai/dsh-agent";
import type { Agent } from "@deepseek-ai/dsh-agent";
import {
  createUserMessage,
  type AssistantMessage,
  type ContentBlock,
  type UserMessage,
} from "@deepseek-ai/dsh-llm";
import { defineTool } from "@deepseek-ai/dsh-tools";
import {
  ContextIntelligenceEngine,
  JsonFileContextTraceStore,
  JsonProcessKnowledgeRetriever,
  JsonProcessWorldViewResolver,
  JsonVisualLanguageResolver,
  OpenAiCompatibleIntelligenceModel,
  matchContextActivation,
  type ContextPacket,
  type ContextRequest,
  type IntelligenceConfiguration,
  type IntelligenceModel,
  type KnowledgeRetriever,
  type VisualLanguageManifest,
  type WorldViewResolver,
} from "@testflight/context-intelligence";

export const name = "testflight-context-intelligence";
export const inject = ["tools", "agents"];

export const Config = z.object({
  configPath: z
    .string()
    .default("workspaces/brand-nike-research/INTELLIGENCE.json"),
  pythonCommand: z.string().default(".venv-cognee/bin/python"),
  repositoryRoot: z.string().default("."),
  traceDirectory: z.string().default(".data/context-intelligence/traces"),
  traceMaxRuns: z.number().default(200),
  traceMaxAgeDays: z.number().default(30),
  visualLanguageManifestPath: z.string().default(""),
  autoActivate: z.boolean().default(true),
});

export interface PluginConfig {
  configPath: string;
  pythonCommand: string;
  repositoryRoot: string;
  traceDirectory: string;
  traceMaxRuns: number;
  traceMaxAgeDays: number;
  visualLanguageManifestPath: string;
  autoActivate: boolean;
}

export const descriptor = Object.freeze({
  name,
  capability: "workflow-context-intelligence",
  upstream: "@deepseek-ai/dsh@0.1.0-rc.7",
  writesKnowledge: false,
  writesTrace: true,
});

export interface PluginDependencies {
  model?: IntelligenceModel;
  retriever?: KnowledgeRetriever;
  worldViewResolver?: WorldViewResolver;
}

function isConfiguration(value: unknown): value is IntelligenceConfiguration {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Partial<IntelligenceConfiguration>;
  return (
    candidate.version === 1 &&
    typeof candidate.workspaceId === "string" &&
    typeof candidate.brandId === "string" &&
    typeof candidate.datasetName === "string" &&
    Array.isArray(candidate.workflows) &&
    Array.isArray(candidate.sections)
  );
}

async function loadConfiguration(
  path: string,
): Promise<IntelligenceConfiguration> {
  const value: unknown = JSON.parse(await readFile(path, "utf8"));
  if (!isConfiguration(value))
    throw new Error(`invalid context intelligence configuration: ${path}`);
  return value;
}

function intelligenceModelFromEnvironment(): IntelligenceModel {
  const model = process.env.TESTFLIGHT_INTELLIGENCE_MODEL?.trim();
  const credentialEnvironment =
    process.env.TESTFLIGHT_INTELLIGENCE_API_KEY_ENV?.trim() ||
    "OPENROUTER_API_KEY";
  const credential = process.env[credentialEnvironment]?.trim();
  if (!model || !credential) {
    return {
      id: model || "unconfigured",
      async completeJson() {
        throw new Error(
          `set TESTFLIGHT_INTELLIGENCE_MODEL and ${credentialEnvironment} for model-backed context intelligence`,
        );
      },
    };
  }
  return new OpenAiCompatibleIntelligenceModel({
    model,
    credential,
    baseUrl:
      process.env.TESTFLIGHT_INTELLIGENCE_BASE_URL?.trim() ||
      "https://openrouter.ai/api/v1",
  });
}

function resolvePythonCommand(root: string, configured: string): string {
  const requested = resolve(root, configured);
  if (existsSync(requested)) return requested;
  // The server provisioner creates .venv-cognee; local workspace development
  // commonly uses uv's .venv. Only fall back when the untouched default was
  // requested, never when a user selected a specific interpreter.
  const localFallback = resolve(root, ".venv/bin/python");
  if (configured === ".venv-cognee/bin/python" && existsSync(localFallback))
    return localFallback;
  return requested;
}

function textFromMessage(message: UserMessage): string {
  return message.content
    .filter(
      (block): block is ContentBlock & { type: "text"; text: string } =>
        block.type === "text",
    )
    .map((block) => block.text)
    .join("\n");
}

function renderPacket(packet: ContextPacket): string {
  return [
    "Context intelligence packet (evidence and operating instructions; not a finished asset):",
    JSON.stringify(packet),
  ].join("\n");
}

function openTurn(agent: Agent): number | undefined {
  const ended = new Set(
    agent.session.events
      .filter((event) => event.type === "turn/end")
      .map((event) => event.data.turn),
  );
  for (const event of [...agent.session.events].reverse()) {
    if (event.type === "turn/start" && !ended.has(event.data.turn))
      return event.data.turn;
  }
  return undefined;
}

function visibleAssistantOutput(message: AssistantMessage) {
  return {
    id: message.id,
    role: message.role,
    content: message.content.filter((block) => block.type !== "reasoning"),
    source: message.source,
  };
}

export function createEngineFactory(
  config: PluginConfig,
  dependencies: PluginDependencies = {},
) {
  let pending: Promise<ContextIntelligenceEngine> | undefined;
  return () => {
    pending ??= (async () => {
      const root = resolve(config.repositoryRoot);
      const configuration = await loadConfiguration(
        resolve(root, config.configPath),
      );
      const pythonCommand = resolvePythonCommand(root, config.pythonCommand);
      const retriever =
        dependencies.retriever ??
        new JsonProcessKnowledgeRetriever({
          command: pythonCommand,
          args: ["-m", "testflight_adapter_cognee.context_retrieval_bridge"],
          cwd: root,
        });
      let visualLanguageResolver: JsonVisualLanguageResolver | undefined;
      if (configuration.visualLanguage?.enabled) {
        const manifestPath = resolve(
          root,
          config.visualLanguageManifestPath ||
            configuration.visualLanguage.manifestPath ||
            "workspaces/brand-nike-research/visual-language/manifest.json",
        );
        const manifest = JSON.parse(
          await readFile(manifestPath, "utf8"),
        ) as VisualLanguageManifest;
        visualLanguageResolver = new JsonVisualLanguageResolver(manifest);
      }
      const worldViewResolver =
        dependencies.worldViewResolver ??
        (configuration.worldView?.enabled
          ? new JsonProcessWorldViewResolver({
              command: pythonCommand,
              args: [
                "-m",
                "testflight_adapter_cognee.world_view_bridge",
                "--world-model",
                resolve(
                  root,
                  configuration.worldView.manifestPath ||
                    "workspaces/brand-nike-research/artifacts/world-modeling.yaml",
                ),
              ],
              cwd: root,
            })
          : undefined);
      return new ContextIntelligenceEngine(
        configuration,
        dependencies.model ?? intelligenceModelFromEnvironment(),
        retriever,
        new JsonFileContextTraceStore(resolve(root, config.traceDirectory), {
          maxRuns: config.traceMaxRuns,
          maxAgeDays: config.traceMaxAgeDays,
        }),
        visualLanguageResolver,
        worldViewResolver,
      );
    })();
    return pending;
  };
}

export function apply(ctx: Context, config: PluginConfig): void {
  const engine = createEngineFactory(config);
  const runsByTurn = new Map<string, Set<string>>();
  const turnKey = (agent: Agent, turn: number) => `${agent.id}:${turn}`;
  const linkRun = (agent: Agent | undefined, runId: string) => {
    if (!agent) return;
    const turn = openTurn(agent);
    if (turn === undefined) return;
    const key = turnKey(agent, turn);
    const runs = runsByTurn.get(key) ?? new Set<string>();
    runs.add(runId);
    runsByTurn.set(key, runs);
  };
  ctx.tools.register(
    defineTool({
      name: "compile_context",
      description:
        "Compile workspace-scoped, evidence-grounded context and reasoning instructions for a brand workflow. Use before creating, adapting, reviewing, positioning, or evaluating brand work when automatic context is absent or needs explicit inputs.",
      parameters: {
        prompt: {
          type: "string",
          required: true,
          description: "The full task to interpret.",
        },
        workflowStage: {
          type: "string",
          description:
            "brief, concept, production, review, or post_publication_learning",
        },
        assetType: { type: "string", description: "The requested asset type." },
        objective: {
          type: "string",
          description: "The outcome the asset should support.",
        },
        audience: { type: "string", description: "The intended audience." },
        audienceSegmentIds: {
          type: "array",
          description: "Stable audience segment ids, when available.",
          items: { type: "string" },
        },
        channel: { type: "string", description: "The delivery channel." },
        geography: { type: "string", description: "The geographic scope." },
        occasion: {
          type: "string",
          description: "The campaign, moment, or use occasion.",
        },
        validTime: {
          type: "string",
          description: "Relevant date in YYYY-MM-DD form.",
        },
        workspaceId: {
          type: "string",
          description: "Explicit knowledge workspace id.",
        },
        productId: {
          type: "string",
          description: "Product or product-family id.",
        },
        campaignId: { type: "string", description: "Campaign id." },
        offerId: { type: "string", description: "Offer or service id." },
        visualLanguageProfileId: {
          type: "string",
          description: "Optional explicit visual-language profile id.",
        },
        visualLanguageRevisionId: {
          type: "string",
          description: "Optional explicit visual-language revision id.",
        },
        contextId: {
          type: "string",
          description: "Canonical context id for conditional world selection.",
        },
        branchId: {
          type: "string",
          description: "Canonical branch id for an interpretation or scenario.",
        },
        perspectiveIds: {
          type: "array",
          description: "Optional canonical perspective ids to apply.",
          items: { type: "string" },
        },
      },
      output: {
        schema: { type: "object", additionalProperties: true, properties: {} },
        render: (_args, value) => [
          {
            type: "text",
            text: renderPacket(value as unknown as ContextPacket),
          },
        ],
      },
      isConcurrencySafe: () => true,
      async execute(args, exec) {
        const packet = await (
          await engine()
        ).compile(args as ContextRequest, {
          activationReason: "explicit",
          signal: exec.signal,
        });
        linkRun(exec.agent, packet.receipt.trace.runId);
        return JSON.parse(JSON.stringify(packet));
      },
    }),
  );

  ctx.tools.register(
    defineTool({
      name: "inspect_context_trace",
      description:
        "Inspect an observable context-intelligence run by id. Returns prompts, retrieval decisions, entity touches, visible outputs, and optionally exact evidence text; never hidden chain-of-thought.",
      parameters: {
        runId: { type: "string", required: true, description: "Trace run id." },
        includeEvidence: {
          type: "boolean",
          description: "Include exact raw evidence bodies. Defaults to false.",
        },
      },
      output: {
        schema: { type: "object", additionalProperties: true, properties: {} },
        render: (_args, value) => [
          { type: "text", text: JSON.stringify(value, null, 2) },
        ],
      },
      isConcurrencySafe: () => true,
      async execute(args) {
        const compiledEngine = await engine();
        if (!compiledEngine.traceStore)
          throw new Error("context trace storage is disabled");
        const trace = await compiledEngine.traceStore.read(String(args.runId));
        if (args.includeEvidence) return JSON.parse(JSON.stringify(trace));
        const compact = {
          ...trace,
          evidence: Object.fromEntries(
            Object.entries(trace.evidence).map(([hash, item]) => [
              hash,
              {
                id: item.id,
                ...(item.sourceUrl ? { sourceUrl: item.sourceUrl } : {}),
                entityIds: item.entityIds ?? [],
                ...(item.retrievalKind
                  ? { retrievalKind: item.retrievalKind }
                  : {}),
                textLength: item.text.length,
              },
            ]),
          ),
        };
        return JSON.parse(JSON.stringify(compact));
      },
    }),
  );

  ctx.tools.register(
    defineTool({
      name: "inspect_visual_language",
      description:
        "Resolve the governing visual-language profile revisions and references for a brand scope and valid time without invoking an intelligence model.",
      parameters: {
        prompt: {
          type: "string",
          description: "Optional natural-language scope hints.",
        },
        workflowStage: {
          type: "string",
          description: "brief, concept, production, or review.",
        },
        audience: { type: "string", description: "Audience description." },
        audienceSegmentIds: {
          type: "array",
          description: "Stable audience segment ids, when available.",
          items: { type: "string" },
        },
        productId: {
          type: "string",
          description: "Product or product-family id.",
        },
        campaignId: { type: "string", description: "Campaign id." },
        offerId: { type: "string", description: "Offer or service id." },
        channel: { type: "string", description: "Delivery channel." },
        geography: { type: "string", description: "Geographic scope." },
        occasion: { type: "string", description: "Occasion or moment." },
        validTime: { type: "string", description: "Date in YYYY-MM-DD form." },
        visualLanguageProfileId: {
          type: "string",
          description: "Explicit profile id.",
        },
        visualLanguageRevisionId: {
          type: "string",
          description: "Explicit revision id.",
        },
      },
      output: {
        schema: { type: "object", additionalProperties: true, properties: {} },
        render: (_args, value) => [
          { type: "text", text: JSON.stringify(value, null, 2) },
        ],
      },
      isConcurrencySafe: () => true,
      async execute(args) {
        const compiledEngine = await engine();
        const result = compiledEngine.resolveVisualLanguage(
          args as ContextRequest,
        );
        if (!result) throw new Error("visual-language resolution is disabled");
        return JSON.parse(JSON.stringify(result));
      },
    }),
  );

  ctx.on("agent/turn-stopping", async ({ agent, turn }) => {
    const key = turnKey(agent, turn);
    const runIds = runsByTurn.get(key);
    if (!runIds?.size) return;
    const event = [...agent.session.events]
      .reverse()
      .find(
        (candidate) =>
          candidate.type === "assistant/message" &&
          candidate.data.turn === turn,
      );
    if (!event || event.type !== "assistant/message") return;
    const compiledEngine = await engine();
    if (!compiledEngine.traceStore) return;
    await Promise.all(
      [...runIds].map((runId) =>
        compiledEngine.traceStore!.append(runId, {
          phase: "agent_output",
          output: {
            sessionId: agent.id,
            turn,
            step: event.data.step,
            message: visibleAssistantOutput(event.data.message),
            usage: event.data.usage,
            interrupted: event.data.interrupted,
          },
        }),
      ),
    );
    runsByTurn.delete(key);
  });

  ctx.on("agent/error", ({ agent, turn, step, error }) => {
    const key = turnKey(agent, turn);
    const runIds = runsByTurn.get(key);
    if (!runIds?.size) return;
    void engine().then(async (compiledEngine) => {
      if (!compiledEngine.traceStore) return;
      await Promise.all(
        [...runIds].map((runId) =>
          compiledEngine.traceStore!.append(runId, {
            phase: "agent_error",
            input: { sessionId: agent.id, turn, step },
            error: error instanceof Error ? error.message : String(error),
          }),
        ),
      );
      runsByTurn.delete(key);
    });
  });

  if (!config.autoActivate) return;
  ctx.on(
    "agent/pre-step",
    async ({ agent, messages, turn, step, signal }, next) => {
      const decision = await next();
      if (decision.kind === "reject" || step !== 1 || signal.aborted)
        return decision;
      if (
        decision.messages.some(
          (message) =>
            message.source.kind === "plugin" && message.source.plugin === name,
        )
      )
        return decision;
      const candidate = [...messages]
        .reverse()
        .find((message) => message.source.kind === "user");
      if (!candidate) return decision;
      const prompt = textFromMessage(candidate);
      const compiledEngine = await engine();
      const activation = matchContextActivation(
        prompt,
        compiledEngine.configuration,
      );
      if (!activation.activate) return decision;
      const packet = await compiledEngine.compile(
        { prompt },
        { activationReason: "automatic", signal },
      );
      const key = turnKey(agent, turn);
      const runs = runsByTurn.get(key) ?? new Set<string>();
      runs.add(packet.receipt.trace.runId);
      runsByTurn.set(key, runs);
      const text = renderPacket(packet);
      return {
        kind: "enter",
        messages: [
          ...decision.messages,
          createUserMessage({
            content: [{ type: "text", text }],
            source: {
              kind: "plugin",
              plugin: name,
              form: "snapshot",
              sections: [{ name, text }],
            },
          }),
        ],
      };
    },
  );
}
