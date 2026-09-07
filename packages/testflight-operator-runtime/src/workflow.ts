import type { OperatorDefinition, OperatorValidation } from "./contracts.js";

export const workflowPromptOperatorId =
  "runtime://testflight/workflow/prompt-step";

function objectValue(value: unknown): OperatorValidation {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? { valid: true, errors: [] }
    : { valid: false, errors: ["workflow prompt input and output must be objects"] };
}

/** Generic model boundary for trusted, versioned workflow prompt contracts.
 *
 * The workflow runtime performs the step-specific schema and invariant checks. This definition
 * only establishes the provider capability and rejects non-object inputs or outputs.
 */
export function createWorkflowPromptOperatorDefinition(): OperatorDefinition {
  return {
    id: workflowPromptOperatorId,
    version: 1,
    purpose:
      "Execute a trusted, versioned workflow prompt using only its disclosed scoped inputs and return structured JSON.",
    acceptedModalities: ["text/plain"],
    requiresStructuredOutput: true,
    validateInput: objectValue,
    validateOutput: objectValue,
  };
}
