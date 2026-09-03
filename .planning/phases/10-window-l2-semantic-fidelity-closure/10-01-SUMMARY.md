---
phase: 10-window-l2-semantic-fidelity-closure
plan: 01
subsystem: ifc-repair-semantic-contract
tags: [ifc2x3, window, l2, json-schema, semantic-manifest, tdd]
requires:
  - phase: 09.1-ifc-type-evidence-and-prototype-resolution-correction
    provides: production-safe Type evidence and Window pipeline handoff
provides:
  - typed Gold-free semantic authoring manifest 0.1
  - Window L2 evaluation policy 0.2 with normalized IFC2X3 Base Quantities
  - operation-owned fact-key canonicalization and explicit-request policy extension
affects: [10-02, 10-03, 10-04, 10-05, phase-10.1, phase-11]
tech-stack:
  added: []
  patterns: [schema-first manifest, operation-owned canonicalizer, exact policy versioning]
key-files:
  created:
    - schemas/agent/ifc-repair-semantic-manifest-0.1.schema.json
    - src/text2ifc_ifc_repair/semantic_authoring.py
    - tests/ifc_repair/test_semantic_authoring.py
  modified:
    - src/text2ifc_ifc_repair/evaluation_policy.py
    - src/text2ifc_ifc_repair/semantic_facts.py
    - src/text2ifc_ifc_repair/operations/window.py
    - tests/ifc_repair/test_evaluation_policy.py
key-decisions:
  - "Semantic manifests reject private_original and Provider-authored sources before binding."
  - "Window policy 0.2 canonicalizes BaseQuantities and Qto_WindowBaseQuantities while preserving the source key in provenance."
  - "Policy 0.1 remains a separately addressable historical contract."
patterns-established:
  - "OperationEvaluationPolicy owns an optional fact-key normalizer; common evaluation code has no Window branch."
  - "Explicit user facts extend a policy by exact keys rather than pset:* or instance:* wildcards."
requirements-completed: [WIN-01]
duration: 28min
completed: 2026-07-21
---

# Phase 10 Plan 01: Window semantic manifest and L2 policy contracts Summary

**A typed, immutable semantic compiler input now drives Window L2 policy 0.2 with exporter-compatible quantity normalization and frozen 0.1 history.**

## Performance

- **Duration:** 28 min
- **Started:** 2026-07-21T08:34:00Z
- **Completed:** 2026-07-21T09:02:22Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Added an exact JSON Schema and immutable model for ordered semantic assignments, including ownership, applicability, provenance, source authority and authoring action.
- Rejected wrong versions, missing provenance, cross-operation facts, conflicting duplicates, non-finite values, unsupported fact kinds, private Gold and Provider claims with stable codes.
- Registered Window policy 0.2 with concrete Type/Host/Storey/dimension/IsExternal/BaseQuantity requirements and narrowly selected conditional semantics.
- Kept Window policy 0.1 readable without relabelling its historical broad patterns.
- Proved a fixture operation can register its own normalizer through the common Registry seam.

## Task Commits

1. **Task 1 RED: freeze manifest and Window policy behavior** - `b605c3e7` (test)
2. **Task 2 GREEN: implement manifest and policy normalization** - `8cf1cc97` (feat)
3. **Task 3 REFACTOR: centralize assignment normalization** - `521d6296` (refactor)

## Files Created/Modified

- `schemas/agent/ifc-repair-semantic-manifest-0.1.schema.json` - closed public manifest envelope and assignment vocabulary.
- `src/text2ifc_ifc_repair/semantic_authoring.py` - immutable models, stable validation and deterministic ordering.
- `src/text2ifc_ifc_repair/evaluation_policy.py` - operation-neutral normalization and exact explicit-request extensions.
- `src/text2ifc_ifc_repair/semantic_facts.py` - applies policy-owned canonicalization to expected and reopened facts.
- `src/text2ifc_ifc_repair/operations/window.py` - Window policy 0.2, historical 0.1 and Window-owned quantity aliases.
- `tests/ifc_repair/test_semantic_authoring.py` - manifest, security, normalization and extensibility contract tests.
- `tests/ifc_repair/test_evaluation_policy.py` - concrete Window 0.2 and frozen 0.1 assertions.

## Decisions Made

- Manifest authority is stricter than the historical evaluator source enum: private original and repaired output cannot become authoring assignments.
- Normalized quantity keys are `quantity:window-base.{Width|Height|Area}`; original IFC paths remain in provenance.
- Name, Tag, Mark and arbitrary Psets are absent from the base Window policy and can enter only through exact explicit-request extensions.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The first RED run exposed a test-collection import for the intentionally missing historical policy symbol. The test import was moved inside the test, then RED was rerun successfully as 17 behavioral failures with 47 existing passes.

## User Setup Required

None - no external service configuration required.

## Verification

- `69 passed` for semantic authoring, evaluation policy and Registry focused suites.
- `compileall` completed successfully for `src/text2ifc_ifc_repair`.
- `git diff --check` reported no whitespace errors.

## Self-Check: PASSED

- All declared artifacts exist.
- RED, GREEN and REFACTOR commits are present in order.
- All task acceptance criteria and plan-level verification commands pass.

## Next Phase Readiness

- Ready for 10-02 to derive complete per-operation manifests from Production evidence and the SQLite IFC index.
- No RAG, vector retrieval, custom-property creation or later entity-family behavior was introduced.

---
*Phase: 10-window-l2-semantic-fidelity-closure*
*Completed: 2026-07-21*
