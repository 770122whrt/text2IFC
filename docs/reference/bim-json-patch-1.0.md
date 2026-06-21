<!-- Generated from schemas/bim-json-patch/1.0/schema.json. Do not edit. -->
<!-- Regenerate with: python scripts/jsonfix/generate_patch_reference.py -->

# BIM JSON Patch 1.0 Reference

An ordered, provenance-bearing transformation envelope targeting formal BIM JSON 2.0.

## Envelope

Required fields: `patch_version`, `target_schema_version`, `target_ifc_schema`, `target_document_id`, `layers`.

- `patch_version` is fixed to `bim-json-patch/1.0`.
- `target_schema_version` is fixed to `bim-json/2.0`.
- `target_ifc_schema` is fixed to `IFC2X3`.
- `target_document_id` identifies the immutable base document.

## Layers

Every ordered layer requires `id`, `kind`, `provenance`, `operations`.
Layer provenance distinguishes user, Agent, validator, and reviewer facts.

## Operations

Supported operations: `add_entity`, `set_attribute`, `set_property`, `add_relationship`, `set_material`, `mark_missing`, `mark_unsupported_loss`, `request_tombstone`.

Targets require `collection`, `id`; optional addressing fields are `path`, `property`, `property_set`.

`request_tombstone` records deletion-like intent but requires review.

## Safety Boundary

Patch output forbids raw IFC/STEP, STEP line identifiers, low-level IFC helper objects, OpenUSD mesh facts, and generic transform operations.
Unknown facts stay explicit through `mark_missing` or `mark_unsupported_loss`; they are not filled with defaults.

## Compilation Boundary

A patch is not a Formal BIM JSON document and cannot be compiled directly.
The composer applies validated operations to an immutable BIM JSON 2.0 base document.
The resulting candidate must pass `validate_v2_document` before the IFC2X3 compiler is invoked.
