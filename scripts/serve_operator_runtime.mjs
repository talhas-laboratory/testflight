#!/usr/bin/env node

/**
 * Composition-root launcher for the local Creative Field operator runtime.
 *
 * Build first with `pnpm --filter @testflight/operator-runtime build`. Credentials are read from
 * the environment named by TESTFLIGHT_OPERATOR_API_KEY_ENV and are never printed.
 */

import {
  createCreativeOperatorDefinitions,
  createWorkflowPromptOperatorDefinition,
  createOperatorRuntimeHttpServer,
  creativeOperatorIds,
  creativeOperatorModalities,
  OpenAICompatibleOperatorProvider,
  OperatorRuntime,
  workflowPromptOperatorId,
} from "../packages/testflight-operator-runtime/dist/src/index.js";

const required = (name) => {
  const value = process.env[name];
  if (!value?.trim()) throw new Error(`${name} is required`);
  return value;
};

const numberEnv = (name, fallback) => {
  const value = process.env[name];
  if (!value) return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) throw new Error(`${name} must be positive`);
  return parsed;
};

const integerEnv = (name, fallback) => {
  const parsed = numberEnv(name, fallback);
  if (!Number.isInteger(parsed)) throw new Error(`${name} must be a positive integer`);
  return parsed;
};

const apiKeyEnv = process.env.TESTFLIGHT_OPERATOR_API_KEY_ENV || "LLM_API_KEY";
const baseUrl = required("TESTFLIGHT_OPERATOR_BASE_URL");
const credential = required(apiKeyEnv);
const modelId = process.env.TESTFLIGHT_OPERATOR_MODEL_ID || "gpt-5.6-luna";
const providerId = process.env.TESTFLIGHT_OPERATOR_PROVIDER_ID || "configured-compatible";
const host = process.env.TESTFLIGHT_OPERATOR_HOST || "127.0.0.1";
const port = integerEnv("TESTFLIGHT_OPERATOR_PORT", 8781);
const timeoutMs = numberEnv("TESTFLIGHT_OPERATOR_TIMEOUT_MS", 120_000);
const maxAttempts = integerEnv("TESTFLIGHT_OPERATOR_MAX_ATTEMPTS", 2);

const definitions = createCreativeOperatorDefinitions();
const provider = new OpenAICompatibleOperatorProvider({
  id: providerId,
  modelId,
  baseUrl,
  credential,
  operatorIds: [...Object.values(creativeOperatorIds), workflowPromptOperatorId],
  modalities: [...creativeOperatorModalities],
});
const runtime = new OperatorRuntime({
  definitions: [...definitions, createWorkflowPromptOperatorDefinition()],
  providers: [provider],
  policy: { timeoutMs, maxAttempts },
});
const server = createOperatorRuntimeHttpServer({ runtime });

const close = () =>
  new Promise((resolve, reject) => server.close((error) => (error ? reject(error) : resolve())));

server.listen(port, host, () => {
  console.log(`Operator runtime listening on http://${host}:${port}`);
  console.log(`Provider ${providerId} / model ${modelId}`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, async () => {
    await close();
    process.exit(0);
  });
}
