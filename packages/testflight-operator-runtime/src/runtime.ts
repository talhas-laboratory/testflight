import type {
  OperatorDefinition,
  OperatorExecutionResult,
  OperatorInvocation,
  OperatorProvider,
  OperatorReceipt,
  OperatorRuntimePolicy,
  ProviderExecutionResult,
} from "./contracts.js";
import { OperatorProviderError } from "./providers.js";

const DEFAULT_POLICY: OperatorRuntimePolicy = {
  requireDisclosure: true,
  timeoutMs: 120_000,
  maxAttempts: 1,
};

function redacted(value: unknown, keys: Set<string>): unknown {
  if (Array.isArray(value)) return value.map((item) => redacted(item, keys));
  if (typeof value !== "object" || value === null) return value;
  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      key,
      keys.has(key.toLocaleLowerCase()) ? "[REDACTED]" : redacted(item, keys),
    ]),
  );
}

function defaultRedactionKeys(): Set<string> {
  return new Set([
    "api_key",
    "apikey",
    "credential",
    "password",
    "secret",
    "token",
  ]);
}

function now(): string {
  return new Date().toISOString();
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : "operator provider failed";
}

function isAbort(error: unknown, signal: AbortSignal): boolean {
  return (
    signal.aborted ||
    (error instanceof DOMException && error.name === "AbortError")
  );
}

export class OperatorRuntime {
  readonly #definitions = new Map<string, OperatorDefinition>();
  readonly #providers: OperatorProvider[];
  readonly #policy: OperatorRuntimePolicy;
  readonly #inFlight = new Map<string, Promise<OperatorExecutionResult>>();

  constructor(options: {
    definitions: OperatorDefinition[];
    providers: OperatorProvider[];
    policy?: Partial<OperatorRuntimePolicy>;
  }) {
    for (const definition of options.definitions) {
      const key = `${definition.id}@${definition.version}`;
      if (this.#definitions.has(key))
        throw new Error(`duplicate operator definition: ${key}`);
      this.#definitions.set(key, definition);
    }
    this.#providers = [...options.providers];
    this.#policy = { ...DEFAULT_POLICY, ...options.policy };
    if (this.#policy.timeoutMs <= 0)
      throw new Error("operator timeout must be positive");
    if (this.#policy.maxAttempts <= 0)
      throw new Error("operator maxAttempts must be positive");
  }

  execute(invocation: OperatorInvocation): Promise<OperatorExecutionResult> {
    const existing = this.#inFlight.get(invocation.operationKey);
    if (existing) return existing.then((result) => this.#replay(result));
    const promise = this.#execute(invocation);
    this.#inFlight.set(invocation.operationKey, promise);
    return promise;
  }

  async #execute(
    invocation: OperatorInvocation,
  ): Promise<OperatorExecutionResult> {
    const startedAt = now();
    const receiptBase: Omit<OperatorReceipt, "providerId" | "modelId"> = {
      operationKey: invocation.operationKey,
      operatorId: invocation.operatorId,
      operatorVersion: invocation.operatorVersion,
      startedAt,
      finishedAt: startedAt,
      preflightPassed: false,
      attempts: 0,
      providerCallCount: 0,
      idempotentReplay: false,
      redactedConfiguration: redacted(
        invocation.configuration,
        new Set([
          ...defaultRedactionKeys(),
          ...(this.#policy.redactedConfigurationKeys ?? []).map((key) =>
            key.toLocaleLowerCase(),
          ),
        ]),
      ) as Record<string, unknown>,
      disclosureRefs: [...invocation.context.disclosureRefs],
      errors: [] as string[],
    };

    const definition = this.#definitions.get(
      `${invocation.operatorId}@${invocation.operatorVersion}`,
    );
    if (!definition) {
      return this.#finish({
        status: "hold",
        holdReason: "operator_not_registered",
        errors: ["operator not registered"],
        receipt: receiptBase,
      });
    }
    if (!invocation.context.projectId || !invocation.context.workspaceId) {
      return this.#finish({
        status: "hold",
        holdReason: "scope_missing",
        errors: ["project and workspace scope are required"],
        receipt: receiptBase,
      });
    }
    if (
      this.#policy.requireDisclosure &&
      invocation.context.disclosureRefs.length === 0
    ) {
      return this.#finish({
        status: "hold",
        holdReason: "disclosure_missing",
        errors: ["disclosure references are required"],
        receipt: receiptBase,
      });
    }
    const inputValidation = definition.validateInput?.(invocation.input);
    if (inputValidation && !inputValidation.valid) {
      return this.#finish({
        status: "hold",
        holdReason: "input_invalid",
        errors: inputValidation.errors,
        receipt: receiptBase,
      });
    }
    const provider = this.#selectProvider(invocation, definition);
    if (!provider) {
      return this.#finish({
        status: "hold",
        holdReason: "preflight_failed",
        errors: ["no provider satisfies operator, modality and policy"],
        receipt: receiptBase,
      });
    }
    receiptBase.preflightPassed = true;
    const providerIdentity = {
      providerId: provider.id,
      modelId: provider.capabilities.modelId,
    };
    const controller = new AbortController();
    const timeout = setTimeout(
      () => controller.abort("operator timeout"),
      this.#policy.timeoutMs,
    );
    const signal = invocation.signal
      ? this.#combineSignals(invocation.signal, controller.signal)
      : controller.signal;
    let response: ProviderExecutionResult | undefined;
    try {
      for (let attempt = 1; attempt <= this.#policy.maxAttempts; attempt += 1) {
        receiptBase.attempts = attempt;
        receiptBase.providerCallCount += 1;
        try {
          response = await provider.execute({ definition, invocation, signal });
          break;
        } catch (error) {
          receiptBase.errors.push(errorText(error));
          const retryable =
            error instanceof OperatorProviderError && error.retryable;
          if (!retryable || attempt >= this.#policy.maxAttempts) throw error;
        }
      }
    } catch (error) {
      clearTimeout(timeout);
      const message = isAbort(error, signal)
        ? "operator execution cancelled or timed out"
        : errorText(error);
      receiptBase.errors.push(message);
      return this.#finish({
        status: isAbort(error, signal) ? "hold" : "failed",
        holdReason: isAbort(error, signal)
          ? "cancelled_or_timed_out"
          : "provider_failed",
        errors: receiptBase.errors,
        receipt: { ...receiptBase, ...providerIdentity },
      });
    }
    clearTimeout(timeout);
    if (!response) {
      return this.#finish({
        status: "failed",
        errors: ["provider returned no result"],
        receipt: { ...receiptBase, ...providerIdentity },
      });
    }
    const outputValidation = definition.validateOutput(response.output);
    if (!outputValidation.valid) {
      const errors = [...receiptBase.errors, ...outputValidation.errors];
      return this.#finish({
        status: "failed",
        errors,
        receipt: { ...receiptBase, ...providerIdentity, errors },
      });
    }
    if (response.disclosureRefs)
      receiptBase.disclosureRefs = [
        ...new Set([...receiptBase.disclosureRefs, ...response.disclosureRefs]),
      ];
    return this.#finish({
      status: response.status ?? invocation.requestedStatus ?? "proposal",
      output: response.output,
      errors: receiptBase.errors,
      receipt: { ...receiptBase, ...providerIdentity },
    });
  }

  #selectProvider(
    invocation: OperatorInvocation,
    definition: OperatorDefinition,
  ): OperatorProvider | undefined {
    return this.#providers.find((provider) => {
      const capabilities = provider.capabilities;
      return (
        (!this.#policy.allowedProviderIds ||
          this.#policy.allowedProviderIds.includes(provider.id)) &&
        capabilities.operatorIds.includes(definition.id) &&
        capabilities.modalities.includes(invocation.modality) &&
        (!definition.requiresStructuredOutput ||
          capabilities.supportsStructuredOutput) &&
        definition.acceptedModalities.includes(invocation.modality)
      );
    });
  }

  #combineSignals(first: AbortSignal, second: AbortSignal): AbortSignal {
    return AbortSignal.any([first, second]);
  }

  #finish(
    result: Omit<OperatorExecutionResult, "receipt"> & {
      receipt: OperatorReceipt;
    },
  ): OperatorExecutionResult {
    return { ...result, receipt: { ...result.receipt, finishedAt: now() } };
  }

  #replay(result: OperatorExecutionResult): OperatorExecutionResult {
    return {
      ...result,
      receipt: { ...result.receipt, idempotentReplay: true },
    };
  }
}
