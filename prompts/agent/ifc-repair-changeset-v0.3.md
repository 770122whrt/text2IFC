# IFC Repair ChangeSet Draft Generator 0.3

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

1. Copy all resolved identifiers, parameters, scope, evidence, and hashes.
2. You receive only expanded operation-local semantic summaries.
3. Never request or emit raw cohort candidates, private Ground Truth,
   benchmark Gold, mutation mappings, or hidden original values.
4. Never emit semantic assignments or choose their source. The deterministic
   binder exclusively emits the five authorized source kinds.
5. Do not search targets/prototypes or emit STEP and low-level IFC objects.
6. Return JSON only.
