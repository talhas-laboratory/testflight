import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";

test("the adapter pins the preview release", async () => {
  const source = await readFile(
    new URL("../src/index.ts", import.meta.url),
    "utf8",
  );
  assert.match(source, /@deepseek-ai\/dsh@0\.1\.0-rc\.7/);
  assert.match(source, /agent-runtime/);
});
