# IFC Repair ChangeSet Draft Generator 0.2

Return exactly one JSON object conforming to `CHANGESET_SCHEMA`. This output is
a non-executable draft. Deterministic code, not you, binds semantic assignments.

## Public request

{{REPAIR_REQUEST}}

## Immutable bindings

- source request: {{SOURCE_REQUEST_HASH}}
- model: {{MODEL_FINGERPRINT}}
- semantic manifest ref: {{SEMANTIC_MANIFEST_REF}}
- semantic manifest hash: {{SEMANTIC_MANIFEST_SHA256}}

## Resolved operation projection

{{RESOLVED_OPERATIONS}}

## Semantic group counts

{{SEMANTIC_SUMMARY}}

## Explicit user slot references

{{EXPLICIT_REQUEST_SLOT_REFS}}

## Registered operation contracts

{{SUPPORTED_OPERATIONS}}

## Draft schema

{{CHANGESET_SCHEMA}}

## Previous validation feedback

{{VALIDATION_FEEDBACK}}

Rules:

1. Copy operation IDs, types, targets, parameters, scope, and evidence exactly.
2. Echo all hashes and the manifest reference exactly.
3. Do not emit semantic assignments, Pset values, material/classification
   resource payloads, Type facts, STEP IDs/text, or low-level IFC objects.
4. Do not search, select a prototype, authorize facts, or add custom slots.
5. Return JSON only. The draft cannot be applied until deterministic binding.

## Single-operation shape

Use the exact draft schema above; one operation remains a one-item array.

## Multiple-operation shape

Use the same envelope; include each resolved operation once without merging.
