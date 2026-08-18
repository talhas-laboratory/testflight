export const descriptor = Object.freeze({
  name: "deepseek-harness",
  upstream: "https://github.com/deepseek-ai/deepseek-harness",
  adapterVersion: "0.1.0",
  capability: "agent-runtime",
  upstreamVersion: "0.1.0-rc.7",
});

export type HarnessProfile = "headless" | "web";

export function buildHarnessInvocation(
  profile: HarnessProfile,
): readonly string[] {
  return Object.freeze(["pnpm", "dlx", "@deepseek-ai/dsh@0.1.0-rc.7", profile]);
}
