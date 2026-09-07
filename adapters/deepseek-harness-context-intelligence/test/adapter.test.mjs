import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

test("adapter is a native Cordis plugin with automatic and explicit seams", async () => {
  const source = await readFile(
    new URL("../src/index.ts", import.meta.url),
    "utf8",
  );
  assert.match(source, /defineTool\(/);
  assert.match(source, /compile_context/);
  assert.match(source, /agent\/pre-step/);
  assert.match(source, /TESTFLIGHT_INTELLIGENCE_MODEL/);
  assert.match(source, /JsonFileContextTraceStore/);
  assert.match(source, /traceDirectory/);
  assert.match(source, /inspect_context_trace/);
  assert.match(source, /inspect_visual_language/);
  assert.match(source, /agent\/turn-stopping/);
  assert.match(source, /agent_output/);
  assert.match(source, /block\.type !== "reasoning"/);
  assert.match(source, /JsonVisualLanguageResolver/);
  assert.match(source, /visualLanguageManifestPath/);
  assert.match(source, /JsonProcessWorldViewResolver/);
  assert.match(source, /worldViewResolver/);
  assert.match(source, /contextId/);
  assert.match(source, /branchId/);
  assert.match(source, /perspectiveIds/);
  assert.doesNotMatch(source, /TESTFLIGHT_DSH_MODEL/);
});
