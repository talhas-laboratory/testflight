export const descriptor = Object.freeze({
  name: "deepseek-harness",
  upstream: "https://github.com/deepseek-ai/deepseek-harness",
  adapterVersion: "0.1.0",
  capability: "agent-runtime",
  upstreamVersion: "0.1.0-rc.7",
});

export const upstreamPackage = "@deepseek-ai/dsh@0.1.0-rc.7";

export const defaultProfile = "headless" as const;

export type HarnessProfile = "headless" | "web";

export interface HarnessLaunchOptions {
  profile: HarnessProfile;
  patchFile?: string;
}

export interface HarnessEnvironmentOptions {
  dshHome: string;
}

export function buildHarnessInvocation(
  profileOrOptions: HarnessProfile | HarnessLaunchOptions,
): readonly string[] {
  const options =
    typeof profileOrOptions === "string"
      ? { profile: profileOrOptions }
      : profileOrOptions;
  const invocation = [
    "pnpm",
    "dlx",
    upstreamPackage,
    "--profile",
    options.profile,
  ];
  if (options.patchFile) {
    invocation.push("--patch", options.patchFile);
  }
  return Object.freeze(invocation);
}

export function buildHarnessEnvironment(
  options: HarnessEnvironmentOptions,
): Readonly<Record<string, string>> {
  if (!options.dshHome.trim()) {
    throw new Error("dshHome must not be empty");
  }
  return Object.freeze({ DSH_HOME: options.dshHome });
}
