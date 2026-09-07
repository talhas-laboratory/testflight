import { spawn } from "node:child_process";
import type {
  IntelligenceModel,
  KnowledgeRetriever,
  RetrievedKnowledge,
  RetrievalQuery,
  ResolvedWorldView,
  WorldViewResolver,
  WorldViewSelectionRequest,
} from "./contracts.js";

function parseJsonText(value: string): unknown {
  const fenced = value.match(/```(?:json)?\s*([\s\S]*?)```/i);
  return JSON.parse((fenced?.[1] ?? value).trim());
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function responseSchema(input: {
  purpose: "interpret" | "synthesize";
  payload: unknown;
}): { name: string; schema: Record<string, unknown> } {
  if (input.purpose === "interpret") {
    const fields = [
      "workflowStage",
      "assetType",
      "objective",
      "audience",
      "channel",
      "geography",
      "occasion",
      "validTime",
    ];
    return {
      name: "context_interpretation",
      schema: {
        type: "object",
        additionalProperties: false,
        properties: Object.fromEntries(
          fields.map((field) => [field, { type: ["string", "null"] }]),
        ),
        required: fields,
      },
    };
  }
  const payload = isRecord(input.payload) ? input.payload : {};
  const sections = stringArray(payload.sections);
  const evidence = Array.isArray(payload.evidence) ? payload.evidence : [];
  const allowedEvidenceIds = evidence.flatMap((item) =>
    isRecord(item) && typeof item.id === "string" ? [item.id] : [],
  );
  const statement = {
    type: "object",
    additionalProperties: false,
    properties: {
      statement: { type: "string", minLength: 1 },
      evidenceIds: {
        type: "array",
        minItems: 1,
        items: { type: "string", enum: allowedEvidenceIds },
      },
    },
    required: ["statement", "evidenceIds"],
  };
  return {
    name: "context_synthesis",
    schema: {
      type: "object",
      additionalProperties: false,
      properties: {
        knowledge: {
          type: "object",
          additionalProperties: false,
          properties: Object.fromEntries(
            sections.map((section) => [
              section,
              { type: "array", maxItems: 2, items: statement },
            ]),
          ),
          required: sections,
        },
        conflicts: { type: "array", items: { type: "string" } },
        limitations: { type: "array", items: { type: "string" } },
        omissions: { type: "array", items: { type: "string" } },
      },
      required: ["knowledge", "conflicts", "limitations", "omissions"],
    },
  };
}

export class OpenAiCompatibleIntelligenceModel implements IntelligenceModel {
  readonly id: string;
  readonly #baseUrl: string;
  readonly #credential: string;

  constructor(options: { model: string; baseUrl: string; credential: string }) {
    if (!options.model.trim())
      throw new Error("intelligence model is required");
    if (!options.credential.trim())
      throw new Error("intelligence model credential is required");
    this.id = options.model;
    this.#baseUrl = options.baseUrl.replace(/\/$/, "");
    this.#credential = options.credential;
  }

  async completeJson(input: {
    purpose: "interpret" | "synthesize";
    system: string;
    payload: unknown;
    signal?: AbortSignal;
  }): Promise<unknown> {
    const schema = responseSchema(input);
    const response = await fetch(`${this.#baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        authorization: `Bearer ${this.#credential}`,
        "content-type": "application/json",
      },
      body: JSON.stringify({
        model: this.id,
        temperature: 0,
        response_format: {
          type: "json_schema",
          json_schema: {
            name: schema.name,
            strict: true,
            schema: schema.schema,
          },
        },
        max_tokens: input.purpose === "interpret" ? 512 : 4096,
        messages: [
          { role: "system", content: input.system },
          { role: "user", content: JSON.stringify(input.payload) },
        ],
      }),
      ...(input.signal ? { signal: input.signal } : {}),
    });
    if (!response.ok) {
      throw new Error(
        `intelligence model request failed: HTTP ${response.status}`,
      );
    }
    const body = (await response.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const text = body.choices?.[0]?.message?.content;
    if (!text) throw new Error("intelligence model returned no content");
    return parseJsonText(text);
  }
}

export class JsonProcessKnowledgeRetriever implements KnowledgeRetriever {
  readonly #command: string;
  readonly #args: string[];
  readonly #cwd: string | undefined;

  constructor(options: { command: string; args: string[]; cwd?: string }) {
    this.#command = options.command;
    this.#args = [...options.args];
    this.#cwd = options.cwd;
  }

  retrieve(
    query: RetrievalQuery,
    signal?: AbortSignal,
  ): Promise<RetrievedKnowledge[]> {
    return new Promise((resolve, reject) => {
      const child = spawn(this.#command, this.#args, {
        ...(this.#cwd ? { cwd: this.#cwd } : {}),
        stdio: ["pipe", "pipe", "pipe"],
        ...(signal ? { signal } : {}),
      });
      let stdout = "";
      let stderr = "";
      child.stdout
        .setEncoding("utf8")
        .on("data", (chunk: string) => (stdout += chunk));
      child.stderr
        .setEncoding("utf8")
        .on("data", (chunk: string) => (stderr += chunk));
      child.once("error", reject);
      child.once("close", (code) => {
        if (code !== 0) {
          reject(
            new Error(`knowledge retriever exited ${code}: ${stderr.trim()}`),
          );
          return;
        }
        try {
          const parsed = JSON.parse(stdout) as { items?: RetrievedKnowledge[] };
          resolve(Array.isArray(parsed.items) ? parsed.items : []);
        } catch (error) {
          reject(
            new Error("knowledge retriever returned invalid JSON", {
              cause: error,
            }),
          );
        }
      });
      child.stdin.end(JSON.stringify(query));
    });
  }
}

/**
 * Invokes the canonical semantic world-view compiler without importing its
 * Python implementation into the Cordis/TypeScript runtime.
 */
export class JsonProcessWorldViewResolver implements WorldViewResolver {
  readonly #command: string;
  readonly #args: string[];
  readonly #cwd: string | undefined;

  constructor(options: { command: string; args: string[]; cwd?: string }) {
    this.#command = options.command;
    this.#args = [...options.args];
    this.#cwd = options.cwd;
  }

  resolve(request: WorldViewSelectionRequest): Promise<ResolvedWorldView> {
    return new Promise((resolve, reject) => {
      const child = spawn(this.#command, this.#args, {
        ...(this.#cwd ? { cwd: this.#cwd } : {}),
        stdio: ["pipe", "pipe", "pipe"],
      });
      let stdout = "";
      let stderr = "";
      child.stdout
        .setEncoding("utf8")
        .on("data", (chunk: string) => (stdout += chunk));
      child.stderr
        .setEncoding("utf8")
        .on("data", (chunk: string) => (stderr += chunk));
      child.once("error", reject);
      child.once("close", (code) => {
        if (code !== 0) {
          reject(new Error(`world-view resolver exited ${code}: ${stderr.trim()}`));
          return;
        }
        try {
          const parsed = JSON.parse(stdout) as ResolvedWorldView;
          if (!parsed || typeof parsed !== "object" || !parsed.viewId) {
            throw new Error("world-view resolver returned an invalid payload");
          }
          resolve(parsed);
        } catch (error) {
          reject(
            new Error("world-view resolver returned invalid JSON", {
              cause: error,
            }),
          );
        }
      });
      child.stdin.end(JSON.stringify(request));
    });
  }
}
