import type { OperatorDefinition, OperatorValidation } from "./contracts.js";

export const creativeOperatorIds = {
  observation: "world://operator/creative/observation-extraction",
  interpretation: "world://operator/creative/reference-interpretation",
  synthesis: "world://operator/creative/field-synthesis",
  evaluation: "world://operator/creative/output-evaluation",
} as const;

export const creativeOperatorModalities = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/gif",
  "text/plain",
  "multimodal",
] as const;

function objectInput(value: unknown): OperatorValidation {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? { valid: true, errors: [] }
    : { valid: false, errors: ["operator input must be an object"] };
}

function objectOutput(value: unknown): OperatorValidation {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? { valid: true, errors: [] }
    : { valid: false, errors: ["operator output must be an object"] };
}

function arrayFieldOutput(field: string) {
  return (value: unknown): OperatorValidation => {
    const base = objectOutput(value);
    if (!base.valid) return base;
    const record = value as Record<string, unknown>;
    return Array.isArray(record[field])
      ? { valid: true, errors: [] }
      : { valid: false, errors: [`operator output requires ${field}[]`] };
  };
}

function interpretationOutput(value: unknown): OperatorValidation {
  const base = objectOutput(value);
  if (!base.valid) return base;
  const record = value as Record<string, unknown>;
  const errors: string[] = [];
  if (typeof record.proposed_role !== "string" && typeof record.role !== "string")
    errors.push("operator output requires proposed_role");
  if (!Array.isArray(record.evidence_refs)) errors.push("operator output requires evidence_refs[]");
  if (!Array.isArray(record.dimension_contributions))
    errors.push("operator output requires dimension_contributions[]");
  return errors.length ? { valid: false, errors } : { valid: true, errors: [] };
}

function evaluationOutput(value: unknown): OperatorValidation {
  const baseResult = objectOutput(value);
  if (!baseResult.valid) return baseResult;
  const record = value as Record<string, unknown>;
  const errors = ["field_fidelity", "task_fitness", "execution_quality"]
    .filter((field) => typeof record[field] !== "object" || record[field] === null || Array.isArray(record[field]))
    .map((field) => `operator output requires ${field} object`);
  return errors.length ? { valid: false, errors } : { valid: true, errors: [] };
}

const base = {
  version: 1,
  requiresStructuredOutput: true,
  validateInput: objectInput,
};

/** Runtime definitions for the first creative-field operator pack.
 *
 * The portable YAML contracts remain the source of semantic procedure and evaluator intent. These
 * definitions provide the executable capability/modalities and a conservative structural gate;
 * the Python creative workflows perform the domain-specific validation after runtime execution.
 */
export function createCreativeOperatorDefinitions(): OperatorDefinition[] {
  return [
    {
      ...base,
      id: creativeOperatorIds.observation,
      purpose:
        "Extract bounded, source-grounded features from a multimodal reference without turning interpretation into fact.",
      acceptedModalities: [...creativeOperatorModalities],
      validateOutput: arrayFieldOutput("observed_features"),
    },
    {
      ...base,
      id: creativeOperatorIds.interpretation,
      purpose:
        "Convert observations and annotations into alternative, evidence-linked interpretations and transfer instructions.",
      acceptedModalities: [...creativeOperatorModalities],
      validateOutput: interpretationOutput,
    },
    {
      ...base,
      id: creativeOperatorIds.synthesis,
      purpose:
        "Synthesize reference interpretations into a multidimensional, reviewable Creative Field proposal.",
      acceptedModalities: ["multimodal"],
      validateOutput: (value) => {
        const baseResult = objectOutput(value);
        if (!baseResult.valid) return baseResult;
        const record = value as Record<string, unknown>;
        const errors = ["principles", "tensions", "exclusions", "dimension_states"]
          .filter((field) => !Array.isArray(record[field]))
          .map((field) => `operator output requires ${field}[]`);
        return errors.length ? { valid: false, errors } : { valid: true, errors: [] };
      },
    },
    {
      ...base,
      id: creativeOperatorIds.evaluation,
      purpose:
        "Evaluate output fidelity, exclusions, task fitness and execution quality without mutating the accepted field.",
      acceptedModalities: [...creativeOperatorModalities],
      validateOutput: evaluationOutput,
    },
  ];
}
