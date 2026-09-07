import { access, readFile } from "node:fs/promises";
import { constants } from "node:fs";
import { resolve } from "node:path";

const root = resolve(process.cwd(), "../..");
const configPath = resolve(
  root,
  "workspaces/brand-nike-research/INTELLIGENCE.json",
);
const pythonPath = resolve(
  root,
  process.env.TESTFLIGHT_COGNEE_VENV || ".venv-cognee",
  "bin/python",
);
const config = JSON.parse(await readFile(configPath, "utf8"));
if (config.version !== 1 || !String(config.datasetName).endsWith("_staging")) {
  throw new Error("invalid or unsafe context intelligence configuration");
}
try {
  await access(pythonPath, constants.X_OK);
  console.log(
    `available: workspace=${config.workspaceId} dataset=${config.datasetName}`,
  );
} catch {
  console.log(`unavailable: Cognee Python is not executable at ${pythonPath}`);
  if (process.argv.includes("--strict")) process.exitCode = 1;
}
