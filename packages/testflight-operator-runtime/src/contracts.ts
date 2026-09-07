export const operatorOutcomeStatuses = [
  "proposal",
  "partial",
  "hold",
  "branch",
  "ask",
  "no_hit",
  "failed",
] as const;

export type OperatorOutcomeStatus = (typeof operatorOutcomeStatuses)[number];

export interface OperatorContext {
  workspaceId: string;
  projectId: string;
  branchId?: string;
  authorityGrantId?: string;
  privacyPolicyId?: string;
  disclosureRefs: string[];
  [key: string]: unknown;
}

export interface OperatorInvocation {
  operatorId: string;
  operatorVersion: number;
  operationKey: string;
  modality: string;
  input: unknown;
  context: OperatorContext;
  configuration: Record<string, unknown>;
  requestedStatus?: OperatorOutcomeStatus;
  signal?: AbortSignal;
}

export interface OperatorValidation {
  valid: boolean;
  errors: string[];
}

export interface OperatorDefinition {
  id: string;
  version: number;
  purpose: string;
  acceptedModalities: string[];
  requiresStructuredOutput: boolean;
  validateInput?: (input: unknown) => OperatorValidation;
  validateOutput: (output: unknown) => OperatorValidation;
  outputSchema?: Record<string, unknown>;
}

export interface OperatorCapabilityManifest {
  providerId: string;
  modelId: string;
  operatorIds: string[];
  modalities: string[];
  supportsStructuredOutput: boolean;
  maxInputBytes?: number;
}

export interface ProviderExecutionInput {
  definition: OperatorDefinition;
  invocation: OperatorInvocation;
  signal: AbortSignal;
}

export interface ProviderExecutionResult {
  output: unknown;
  status?: OperatorOutcomeStatus;
  disclosureRefs?: string[];
  usage?: Record<string, number>;
}

export interface OperatorProvider {
  readonly id: string;
  readonly capabilities: OperatorCapabilityManifest;
  execute(input: ProviderExecutionInput): Promise<ProviderExecutionResult>;
}

export interface OperatorRuntimePolicy {
  allowedProviderIds?: string[];
  requireDisclosure: boolean;
  timeoutMs: number;
  maxAttempts: number;
  redactedConfigurationKeys?: string[];
}

export interface OperatorReceipt {
  operationKey: string;
  operatorId: string;
  operatorVersion: number;
  providerId?: string;
  modelId?: string;
  startedAt: string;
  finishedAt: string;
  preflightPassed: boolean;
  attempts: number;
  providerCallCount: number;
  idempotentReplay: boolean;
  redactedConfiguration: Record<string, unknown>;
  disclosureRefs: string[];
  errors: string[];
}

export interface OperatorExecutionResult {
  status: OperatorOutcomeStatus;
  output?: unknown;
  holdReason?: string;
  errors: string[];
  receipt: OperatorReceipt;
}
