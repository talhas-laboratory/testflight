import { spawn } from "node:child_process";

export interface JsonProcessCommand {
  command: string;
  args: readonly string[];
}

/** Reusable transport for one-request JSON bridge processes. */
export async function invokeJsonProcess(
  process: JsonProcessCommand,
  payload: Record<string, unknown>,
  operation: string,
): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const child = spawn(process.command, process.args, {
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk: Buffer) => (stdout += chunk.toString()));
    child.stderr.on("data", (chunk: Buffer) => (stderr += chunk.toString()));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) {
        reject(
          new Error(`${operation} failed: ${stderr.trim() || `exit ${code}`}`),
        );
        return;
      }
      try {
        const value: unknown = JSON.parse(stdout);
        if (!value || typeof value !== "object" || Array.isArray(value)) {
          throw new Error("response must be a JSON object");
        }
        resolve(value as Record<string, unknown>);
      } catch (error) {
        reject(
          new Error(`${operation} returned invalid JSON`, { cause: error }),
        );
      }
    });
    child.stdin.end(JSON.stringify(payload));
  });
}
