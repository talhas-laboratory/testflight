import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const root = new URL("../", import.meta.url);
const tokens = JSON.parse(await readFile(new URL("tokens.json", root), "utf8"));
const css = await readFile(new URL("tokens.css", root), "utf8");

assert.equal(tokens.status, "active");
assert.match(tokens.revision, /^\d+\.\d+\.\d+$/);

const requiredGroups = ["color", "font", "fontSize", "space", "radius", "shadow", "motion"];
for (const group of requiredGroups) {
  assert.ok(tokens[group] && typeof tokens[group] === "object", `missing token group: ${group}`);
}

const requiredCss = [
  "--tf-color-canvas",
  "--tf-color-surface",
  "--tf-color-text",
  "--tf-color-focus",
  "--tf-color-status-held",
  "--tf-color-status-accepted",
  "--tf-font-editorial",
  "--tf-font-interface",
  "--tf-space-4",
  "--tf-radius-medium",
  "--tf-motion-base",
];
for (const variable of requiredCss) {
  assert.ok(css.includes(`${variable}:`), `missing CSS projection: ${variable}`);
}
assert.ok(css.includes("prefers-reduced-motion"), "reduced-motion projection is required");

