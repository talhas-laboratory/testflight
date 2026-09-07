import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("the active token revision exposes semantic state and focus tokens", async () => {
  const tokens = JSON.parse(await readFile(new URL("tokens.json", root), "utf8"));

  assert.equal(tokens.status, "active");
  assert.ok(tokens.color.focus.$value);
  assert.ok(tokens.color.statusHeld.$value);
  assert.ok(tokens.color.statusAccepted.$value);
  assert.ok(tokens.motion.base.$value);
});

