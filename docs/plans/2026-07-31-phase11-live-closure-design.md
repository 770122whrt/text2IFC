# Phase 11 Live Closure Design

Date: 2026-07-31
Status: Approved

## Objective

Close Phase 11 with real DeepSeek UAT and independently re-audit every curated
Proof case currently labelled successful. Synthetic Provider output is not an
acceptable substitute for live evidence.

## Frozen boundaries

- Keep the existing two-stage RepairIntent to Bound ChangeSet workflow.
- Keep retained Opening geometry targeting and the existing Door geometry
  thresholds.
- Keep Ground Truth isolation and the contextual Storey policy unchanged.
- Do not add aliases or compatibility mappings for non-contract LLM fields.
- Do not begin Phase 12.

## Contract repair

Stage 1 describes user intent, while the operation registry's executable
parameter schema describes the deterministic parameters required after target
resolution. These are different contracts and must no longer share the same
completeness check.

For `fill_existing_opening_with_door`, Stage 1 must identify an exact unfilled
Opening and capture canonical Door intent. The existing `fit_existing_opening`
resolver derives position, width, height, sill height, host wall, containment,
and final overall Door dimensions from the damaged IFC. The Provider must not
invent these derived values.

The compact Stage 1 profile catalog must expose exact canonical parameter
shapes, program-derived slots, and unsupported capabilities. Unknown or
synonymous parameter keys fail schema validation. Unsupported Door operation
types remain representable as canonical intent so that the deterministic
capability gate can return `DOOR_OPERATION_TYPE_UNSUPPORTED` rather than
exhausting Provider retries.

## Verification

The implementation is driven by failing tests covering:

1. fill-existing-opening intent completeness without LLM-authored geometry;
2. strict rejection of non-contract aliases;
3. deterministic unsupported Door capability routing;
4. exact live-runner terminal assertions;
5. independent Proof reopening and strict L0/L1/L2 evaluation.

The Proof auditor must derive its verdict from the IFC files and validation
artifacts it recomputes. A manifest or report field saying `success` is not
evidence by itself. The final live run must preserve redacted Provider evidence,
reopen every repaired IFC, pass strict L0/L1/L2, update the Phase 11 records,
and end in a scoped Git checkpoint.
