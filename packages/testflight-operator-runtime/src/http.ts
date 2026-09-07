import {
  createServer,
  type IncomingMessage,
  type Server,
  type ServerResponse,
} from "node:http";
import type {
  OperatorContext,
  OperatorInvocation,
  OperatorRuntimePolicy,
} from "./contracts.js";
import { operatorOutcomeStatuses } from "./contracts.js";
import { OperatorRuntime } from "./runtime.js";

export const DEFAULT_RUNTIME_HTTP_MAX_BODY_BYTES = 10 * 1024 * 1024;

type JsonObject = Record<string, unknown>;

class HttpInputError extends Error {
  readonly statusCode: number;

  constructor(message: string, statusCode = 400) {
    super(message);
    this.name = "HttpInputError";
    this.statusCode = statusCode;
  }
}

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiredString(value: unknown, name: string): string {
  if (typeof value !== "string" || !value.trim())
    throw new HttpInputError(`${name} is required`);
  return value;
}

function requiredInteger(value: unknown, name: string): number {
  const number = typeof value === "number" ? value : Number(value);
  if (!Number.isInteger(number) || number < 1)
    throw new HttpInputError(`${name} must be a positive integer`);
  return number;
}

function asObject(value: unknown, name: string): JsonObject {
  if (!isObject(value)) throw new HttpInputError(`${name} must be an object`);
  return value;
}

function asDisclosureRefs(value: unknown): string[] {
  if (!Array.isArray(value))
    throw new HttpInputError("context.disclosure_refs must be an array");
  if (value.some((item) => typeof item !== "string"))
    throw new HttpInputError("context.disclosure_refs must contain only strings");
  return value as string[];
}

function invocationFromPayload(payload: JsonObject): OperatorInvocation {
  const contextPayload = asObject(payload.context, "context");
  const workspaceId = requiredString(
    contextPayload.workspaceId ?? contextPayload.workspace_id,
    "context.workspace_id",
  );
  const projectId = requiredString(
    contextPayload.projectId ?? contextPayload.project_id,
    "context.project_id",
  );
  const disclosureRefs = asDisclosureRefs(
    contextPayload.disclosureRefs ?? contextPayload.disclosure_refs,
  );
  const context: OperatorContext = {
    ...contextPayload,
    workspaceId,
    projectId,
    disclosureRefs,
  };
  const requestedStatus = payload.requested_status ?? payload.requestedStatus;
  if (requestedStatus !== undefined && typeof requestedStatus !== "string")
    throw new HttpInputError("requested_status must be a string");
  if (
    typeof requestedStatus === "string" &&
    !operatorOutcomeStatuses.includes(
      requestedStatus as (typeof operatorOutcomeStatuses)[number],
    )
  )
    throw new HttpInputError("requested_status is not a supported outcome");
  const invocation: OperatorInvocation = {
    operatorId: requiredString(
      payload.operator_id ?? payload.operatorId,
      "operator_id",
    ),
    operatorVersion: requiredInteger(
      payload.operator_version ?? payload.operatorVersion,
      "operator_version",
    ),
    operationKey: requiredString(
      payload.operation_key ?? payload.operationKey,
      "operation_key",
    ),
    modality: requiredString(payload.modality, "modality"),
    input: payload.input,
    context,
    configuration: asObject(payload.configuration ?? {}, "configuration"),
  };
  if (typeof requestedStatus === "string")
    invocation.requestedStatus = requestedStatus as NonNullable<
      OperatorInvocation["requestedStatus"]
    >;
  return invocation;
}

function receiptToPayload(receipt: Record<string, unknown>): JsonObject {
  return {
    operation_key: receipt.operationKey,
    operator_id: receipt.operatorId,
    operator_version: receipt.operatorVersion,
    ...(receipt.providerId !== undefined
      ? { provider_id: receipt.providerId }
      : {}),
    ...(receipt.modelId !== undefined ? { model_id: receipt.modelId } : {}),
    started_at: receipt.startedAt,
    finished_at: receipt.finishedAt,
    preflight_passed: receipt.preflightPassed,
    attempts: receipt.attempts,
    provider_call_count: receipt.providerCallCount,
    idempotent_replay: receipt.idempotentReplay,
    redacted_configuration: receipt.redactedConfiguration,
    disclosure_refs: receipt.disclosureRefs,
    errors: receipt.errors,
  };
}

function resultToPayload(
  result: Awaited<ReturnType<OperatorRuntime["execute"]>>,
): JsonObject {
  return {
    status: result.status,
    ...(result.output !== undefined ? { output: result.output } : {}),
    ...(result.holdReason !== undefined
      ? { hold_reason: result.holdReason }
      : {}),
    errors: result.errors,
    receipt: receiptToPayload(
      result.receipt as unknown as Record<string, unknown>,
    ),
  };
}

function sendJson(
  response: ServerResponse,
  statusCode: number,
  payload: JsonObject,
): void {
  const body = JSON.stringify(payload);
  response.statusCode = statusCode;
  response.setHeader("content-type", "application/json");
  response.setHeader("content-length", Buffer.byteLength(body));
  response.end(body);
}

function readJson(
  request: IncomingMessage,
  maxBodyBytes: number,
): Promise<JsonObject> {
  return new Promise((resolve, reject) => {
    let totalBytes = 0;
    let settled = false;
    const chunks: Buffer[] = [];
    const fail = (error: Error): void => {
      if (settled) return;
      settled = true;
      reject(error);
    };
    request.on("data", (chunk: Buffer | string) => {
      if (settled) return;
      const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
      totalBytes += buffer.byteLength;
      if (totalBytes > maxBodyBytes) {
        request.resume();
        fail(new HttpInputError("request body exceeds the size limit", 413));
        return;
      }
      chunks.push(buffer);
    });
    request.on("end", () => {
      if (settled) return;
      try {
        const value: unknown = JSON.parse(
          Buffer.concat(chunks).toString("utf8"),
        );
        if (!isObject(value))
          throw new HttpInputError("request body must be an object");
        settled = true;
        resolve(value);
      } catch (error) {
        fail(
          error instanceof HttpInputError
            ? error
            : new HttpInputError("request body is invalid JSON"),
        );
      }
    });
    request.on("error", (error) => fail(error));
  });
}

export interface OperatorRuntimeHttpServerOptions {
  runtime: OperatorRuntime;
  maxBodyBytes?: number;
}

/**
 * Create a bounded local HTTP transport for the provider-neutral operator runtime.
 *
 * The server intentionally accepts only operator invocations and returns normalized JSON. It does
 * not expose provider credentials or a generic file system endpoint; callers remain responsible for
 * choosing which local interface is reachable by Creative Studio.
 */
export function createOperatorRuntimeHttpServer(
  options: OperatorRuntimeHttpServerOptions,
): Server {
  const maxBodyBytes =
    options.maxBodyBytes ?? DEFAULT_RUNTIME_HTTP_MAX_BODY_BYTES;
  if (!Number.isInteger(maxBodyBytes) || maxBodyBytes <= 0)
    throw new Error("runtime HTTP maxBodyBytes must be positive");
  return createServer((request, response) => {
    void (async () => {
      try {
        const path = new URL(request.url ?? "/", "http://runtime.local")
          .pathname;
        if (request.method === "GET" && path === "/health") {
          sendJson(response, 200, { status: "ok" });
          return;
        }
        if (request.method !== "POST" || path !== "/execute") {
          sendJson(response, 404, { error: "not found" });
          return;
        }
        const payload = await readJson(request, maxBodyBytes);
        const result = await options.runtime.execute(
          invocationFromPayload(payload),
        );
        sendJson(response, 200, resultToPayload(result));
      } catch (error) {
        if (error instanceof HttpInputError) {
          sendJson(response, error.statusCode, {
            status: "held",
            error: error.message,
          });
          return;
        }
        sendJson(response, 500, {
          status: "failed",
          error:
            error instanceof Error ? error.message : "runtime request failed",
        });
      }
    })();
  });
}

export type OperatorRuntimeHttpServerFactory = (
  options: OperatorRuntimeHttpServerOptions,
) => Server;

export type OperatorRuntimeHttpPolicy = Partial<OperatorRuntimePolicy>;
