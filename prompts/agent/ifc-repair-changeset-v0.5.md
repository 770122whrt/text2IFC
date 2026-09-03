# IFC Repair ChangeSet Draft Generator 0.5

Return exactly one JSON draft conforming to `CHANGESET_SCHEMA`. Deterministic
code, not the Provider, binds and authors semantic assignments.

## Public request

{{REPAIR_REQUEST}}

## Immutable bindings

- source request: {{SOURCE_REQUEST_HASH}}
- model: {{MODEL_FINGERPRINT}}
- semantic manifest ref: {{SEMANTIC_MANIFEST_REF}}
- semantic manifest hash: {{SEMANTIC_MANIFEST_SHA256}}

## Resolved operation projection

{{RESOLVED_OPERATIONS}}

The entire `RESOLVED_OPERATIONS` object is the canonical envelope authority.
Copy its `scope`, `evidence_refs`, and every operation exactly. Preserve every
list order shown there; do not reconstruct or sort any union yourself.

## Semantic group counts

{{SEMANTIC_SUMMARY}}

## Explicit user slot references

{{EXPLICIT_REQUEST_SLOT_REFS}}

## Selected operation contracts, profiles, and sentinel few-shots

{{SUPPORTED_OPERATIONS}}

## Draft schema

{{CHANGESET_SCHEMA}}

## Previous validation feedback

{{VALIDATION_FEEDBACK}}

Rules:

1. Copy all canonical authority identifiers, parameters, scope, evidence, and
   hashes exactly; never rebuild the envelope from operation-local fields.
2. Include every offered operation exactly once and keep its `operation_id`,
   `operation_type`, `target`, `parameters`, and `evidence_refs` unchanged.
3. You receive only expanded operation-local semantic summaries.
4. Never request or emit raw cohort candidates, private Ground Truth,
   benchmark Gold, mutation mappings, or hidden original values.
5. Never emit semantic assignments or choose their source. The deterministic
   binder exclusively emits the five authorized source kinds.
6. Do not search targets/prototypes or emit STEP and low-level IFC objects.
7. Return JSON only.
8. Only the selected profiles appear below. A few-shot is structural guidance,
   never authority for project identity, dimensions, Type, or property values.
