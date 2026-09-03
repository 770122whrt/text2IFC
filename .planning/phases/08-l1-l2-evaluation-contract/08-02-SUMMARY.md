---
phase: 08-l1-l2-evaluation-contract
plan: 02
subsystem: evaluation
tags: [l2, semantic-facts, ifcopenshell, registry, provenance, tdd]

requires:
  - phase: 08-l1-l2-evaluation-contract
    plan: 01
    provides: immutable five-state evaluation records and EvidenceFact/CheckResult contracts
  - phase: 07-ifc-retrieval-index-and-target-resolution
    provides: typed PropertyFact and ElementRecord representations with provenance
provides:
  - Immutable versioned operation-owned L2 policy contracts
  - Closed authorized evidence-source set and deterministic precedence resolver
  - Conditional Material/Pset/quantity/Classification/instance-fact enforcement
  - Policy-driven repaired IFC and Phase 7 record semantic extraction
  - Window 0.1 policy through the common Registry seam
affects: [08-03, 08-04, phase-09, phase-10, future-operation-policies]

tech-stack:
  added: []
  patterns:
    - Frozen operation policy data registered beside callable capabilities
    - One generic fact-pattern evaluator for every operation family
    - Phase 7 and IfcOpenShell facts normalized through one typed provenance seam

key-files:
  created:
    - src/text2ifc_ifc_repair/evaluation_policy.py
    - src/text2ifc_ifc_repair/semantic_facts.py
    - tests/ifc_repair/test_evaluation_policy.py
  modified:
    - src/text2ifc_ifc_repair/registry.py
    - src/text2ifc_ifc_repair/operations/window.py

key-decisions:
  - "Explicit request, private original, surviving target/Host/Type, approved compatible Prototype, and deterministic policy are the only expectation authorities; repaired output is actual evidence only."
  - "Legacy operation definitions may remain registered without a policy, but evaluation 0.2 fails with MISSING_EVALUATION_POLICY when that operation is evaluated."
  - "Common IFC extraction is driven by policy fact patterns, so Window field names exist only in the Window adapter."

patterns-established:
  - "Conditional authorized fact present => mandatory passed/failed comparison; no authorized fact => disclosed not_required source search."
  - "Required fact without reliable expected evidence => mandatory not_evaluable."
  - "Approved Prototype facts activate checks only when explicitly marked compatible."

requirements-completed:
  - VAL-02
  - VAL-05

duration: 18min
completed: 2026-07-19
---

# Phase 8 Plan 2: Operation-owned L2 Policy and Semantic Evidence Summary

**Versioned Window and fixture policies now resolve typed L2 expectations only from authorized provenance, enforce established semantics, and disclose genuinely absent conditional facts as `not_required`.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-07-19T02:48:15Z
- **Completed:** 2026-07-19T03:06:40Z
- **Tasks:** 3
- **Files modified:** 5 code/test files, plus this summary

## Accomplishments

- Added frozen policy/check records with stable validation codes, immutable IDs and versions, unique check IDs, applicability, comparison rules, and a closed evidence-source enum.
- Added one operation-independent resolver that activates Material, Pset, quantity, Classification, label, and custom instance checks only when authorized evidence exists; missing required expectations are non-passing `not_evaluable`.
- Added Window policy 0.1 for compatible Type, Host/Storey, `IsExternal`, dimensions/quantities, requested semantics, and conditional semantic categories without adding Window branches to common modules.
- Reused Phase 7 `PropertyFact`/`ElementRecord` typed values and provenance, and added inheritance-aware IfcOpenShell extraction for Psets, quantities, materials, type/storey/host, and classifications.
- Proved the extension seam with a future-family fixture that registers and evaluates without common aggregation or Window edits.

## TDD Evidence

- **RED:** Focused pytest failed during collection with `ModuleNotFoundError: text2ifc_ifc_repair.evaluation_policy`; both production modules were absent and only the test file was committed.
- **GREEN:** Immutable policies, Registry validation/dispatch, typed resolution, and Window policy made 44 focused tests pass.
- **REFACTOR:** Centralized Phase 7/IfcOpenShell fact conversion, made extraction policy-driven, and expanded to 46 focused tests plus 9 Phase 7/Registry regression tests.

## Task Commits

Each TDD gate was committed atomically:

1. **Task 1: RED - specify policy registration and source authority** - `b4f12a93` (test)
2. **Task 2: GREEN - implement policy, resolver, and Window adapter** - `56037c5b` (feat)
3. **Task 3: REFACTOR - freeze generic typed-fact extension seam** - `15a20f67` (refactor)

## Files Created/Modified

- `src/text2ifc_ifc_repair/evaluation_policy.py` - Frozen policy/spec records, applicability/comparison/source enums, stable validation, and fixed precedence.
- `src/text2ifc_ifc_repair/semantic_facts.py` - Typed expectation resolution, semantic equivalence, absence evidence, Phase 7 conversion, and policy-driven IFC extraction.
- `src/text2ifc_ifc_repair/registry.py` - Optional immutable policy attachment, duplicate/mismatch validation, required-policy error, and common semantic dispatch.
- `src/text2ifc_ifc_repair/operations/window.py` - Window policy 0.1 declaration attached to the existing operation definition; original application and L1 comparison behavior retained.
- `tests/ifc_repair/test_evaluation_policy.py` - 46 policy, source-authority, conditional activation, typed provenance, extension, and IFC extraction tests.

## Decisions Made

- Kept old operation registration backward compatible while making `require_evaluation_policy`/`evaluate_semantics` reject missing policy with a stable code. This preserves Phase 6/7 callers without weakening evaluation 0.2.
- Kept the source enum closed: neighbor copying, name-only inference, LLM guesses, and model knowledge cannot be represented as authorized evidence.
- Used policy patterns to select IFC attributes and relationships. The common resolver/extractor contains no Window-specific field names, and future families use the same interface.
- Compared typed value, value type, and unit; inheritance, Pset path, entity source, and provenance remain evidence metadata rather than invented equivalence inputs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test Bug] Deferred invalid-version construction into the asserted error boundary**
- **Found during:** Task 2 (GREEN)
- **Issue:** One RED parameter constructed an invalid `SemanticFactSpec` during pytest collection, before `pytest.raises` could verify its stable error code.
- **Fix:** Split the case and construct the invalid spec inside the assertion context.
- **Files modified:** `tests/ifc_repair/test_evaluation_policy.py`
- **Verification:** Focused pytest collected normally and all 44 GREEN tests passed.
- **Committed in:** `56037c5b`

**2. [Rule 2 - Missing Critical Functionality] Added repaired IFC and Phase 7 record fact extraction**
- **Found during:** Task 3 (REFACTOR)
- **Issue:** GREEN could compare normalized facts but lacked the plan-required public conversion from Phase 7 records and inheritance-aware repaired IFC entities.
- **Fix:** Added shared `PropertyFact` conversion, `ElementRecord` conversion, and IfcOpenShell utility extraction for Psets/quantities/material/type/storey/host/classification.
- **Files modified:** `src/text2ifc_ifc_repair/semantic_facts.py`, `tests/ifc_repair/test_evaluation_policy.py`
- **Verification:** A real in-memory IFC2X3 occurrence test verifies Pset, Material, and Classification extraction; Phase 7 parity and full regressions pass.
- **Committed in:** `15a20f67`

**3. [Rule 1 - Architecture Boundary Bug] Removed Window field names from common extraction**
- **Found during:** Task 3 static acceptance scan
- **Issue:** The initial generic IFC extractor directly listed `OverallWidth`/`OverallHeight`, violating the locked operation-owned policy boundary.
- **Fix:** Made attribute, label, relationship, Pset, material, and classification selection derive from the supplied operation policy patterns.
- **Files modified:** `src/text2ifc_ifc_repair/semantic_facts.py`, `tests/ifc_repair/test_evaluation_policy.py`
- **Verification:** Common-module scan finds no Window-specific fields; 55 combined tests and compileall pass.
- **Committed in:** `15a20f67`

---

**Total deviations:** 3 auto-fixed (2 Rule 1, 1 Rule 2).
**Impact on plan:** All fixes were required for executable tests, complete typed extraction, and the locked registry/policy boundary; no operation authoring or scope expansion was added.

## Issues Encountered

- Context7 MCP was unavailable and the CLI fallback could not start because the local `npx` installation was broken. The installed official IfcOpenShell 0.8.5 function signatures/docstrings were inspected directly before using `get_psets`, `get_materials`, `get_type`, `get_container`, and classification utilities.
- `registry.py` and `operations/window.py` were pre-existing untracked baselines. They were read completely before editing, patched only at the policy connection points, and their original callable/application/comparison functions were retained.

## Known Stubs

None. No TODO/FIXME/placeholder behavior or unwired empty semantic output was found in the created/modified files.

## User Setup Required

None - no external service configuration required.

## Verification

- `.venv\Scripts\python -m pytest tests\ifc_repair\test_evaluation_policy.py -q` - **46 passed**
- `.venv\Scripts\python -m pytest tests\ifc_repair\test_indexer.py tests\ifc_repair\test_registry.py -q` - **9 passed**
- `.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair` - **passed**
- Common module Window-field scan - **no matches**
- TDD commit order - **RED `b4f12a93` -> GREEN `56037c5b` -> REFACTOR `15a20f67`**

## Next Phase Readiness

- Plan 08-03 can consume Registry policy metadata and typed L2 checks beside independent L1 authorization/preservation checks.
- Plan 08-04 can use the same typed facts for benchmark-private original comparison and public projection without changing operation-specific report shapes.
- Phase 10 remains responsible for authoring missing Window semantics; this plan only evaluates them.

## Self-Check: PASSED

- All five planned code/test artifacts and this summary exist on disk.
- RED, GREEN, and REFACTOR commits `b4f12a93`, `56037c5b`, and `15a20f67` exist in git history.
- Fresh focused pytest, Phase 7/Registry regression pytest, compileall, stub scan, and common-module Window-field scan passed before summary creation.

---
*Phase: 08-l1-l2-evaluation-contract*
*Completed: 2026-07-19*
