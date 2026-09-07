import type { IntelligenceConfiguration } from "./contracts.js";

export interface ActivationDecision {
  activate: boolean;
  reason: string;
  matchedAction?: string;
  matchedDomain?: string;
}

export function matchContextActivation(
  text: string,
  configuration: IntelligenceConfiguration,
): ActivationDecision {
  const normalized = text.toLocaleLowerCase();
  const matchedAction = configuration.activation.actionTerms.find((term) =>
    normalized.includes(term.toLocaleLowerCase()),
  );
  const matchedDomain = configuration.activation.domainTerms.find((term) =>
    normalized.includes(term.toLocaleLowerCase()),
  );
  if (matchedAction && matchedDomain) {
    return {
      activate: true,
      reason: `brand-dependent action matched: ${matchedAction} + ${matchedDomain}`,
      matchedAction,
      matchedDomain,
    };
  }
  return {
    activate: false,
    reason: "no combined workflow-action and brand-domain match",
  };
}
