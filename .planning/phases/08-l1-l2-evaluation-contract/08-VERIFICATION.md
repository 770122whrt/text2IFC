---
phase: 08-l1-l2-evaluation-contract
verified: 2026-07-19T05:50:06Z
status: gaps_found
score: 10/11 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Every applied IFC repair is complete and publishable only when mandatory L1 and mandatory L2 both pass"
    status: failed
    reason: "The still-callable evaluate_repair_application compatibility evaluator emits Evaluation 0.1, performs no L2 evaluation, and returns complete_repair_success=true plus successful_artifact_publishable=true when its L1/legacy checks pass. A repository test explicitly preserves this bypass."
    artifacts:
      - path: "src/text2ifc_ifc_repair/compare.py"
        issue: "evaluate_repair_application computes complete without any L2 result and labels the candidate publishable."
      - path: "tests/ifc_repair/test_window_application.py"
        issue: "The real IFC application test asserts complete_repair_success is true although the returned 0.1 report has no L2 hierarchy or semantic gate."
    missing:
      - "Route evaluate_repair_application through Evaluation 0.2 L1/L2 aggregation, or make the legacy projection explicitly non-assuring and non-publishable (complete_repair_success=false and successful_artifact_publishable=false)."
      - "Add a negative regression proving an L1-passing/L2-missing or L2-failing applied repair cannot be complete through any supported evaluator entrypoint."
---

# Phase 8: L1/L2 Evaluation Contract Verification Report

**Phase Goal:** Every applied IFC repair receives a versioned, evidence-bearing evaluation in which mandatory L1 physical/relationship correctness and mandatory L2 semantic fidelity are independently decided and jointly gate complete success; L3 is non-gating; benchmark Gold is evaluator-only and production uses non-Gold authority.

**Verified:** 2026-07-19T05:50:06Z  
**Status:** gaps_found  
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Evaluation 0.2 is exact-versioned, schema-backed, hierarchical, and legacy 0.1 is read without invented L2 assurance. | VERIFIED | `evaluation_models.py:13-14`, `evaluation.py:802-840`, and the Draft 2020-12 schema; contract tests cover hierarchy, round-trip, malformed reports, and legacy projection. |
| 2 | Every check/level uses exactly `passed`, `failed`, `partial`, `not_required`, or `not_evaluable`, with reason and evidence. | VERIFIED | `evaluation_models.py:19-25, 126-171`; `test_evaluation_contract.py:174-239`. |
| 3 | The supported Evaluation 0.2 path requires application, preservation, mandatory L1, and mandatory L2 to pass; L3 is `not_required` and non-gating. | VERIFIED | `evaluation.py:643-758`; mandatory downgrade invariants at `evaluation_models.py:155-169` and `evaluation.py:860-900`; negative truth-table tests at `test_evaluation_contract.py:241-363`. |
| 4 | No supported applied-repair evaluator can declare complete/publishable success without mandatory L2. | FAILED | `compare.py:20-90` still returns schema 0.1 and calculates `complete` with no L2. `test_window_application.py:145-152` asserts that path returns complete success. Fresh spot-check passed, confirming the bypass remains executable. |
| 5 | L1 independently reopens IFC, verifies schema/source immutability, actual scope, topology, containment, duplicates, and tolerances; Applicator self-report does not authorize drift. | VERIFIED | `evaluation.py:45-539`, Window measurements at `operations/window.py:621-940`; fault tests cover collateral Wall drift, extra/deleted roots, relationship faults, duplicate role/chain, wrong host/storey, tolerance, unreadable output, and schema mismatch. |
| 6 | Window and future-family fixtures use one versioned Registry policy/evaluator seam. | VERIFIED | `registry.py:35-129`; Window policy attachment at `operations/window.py:109-225`; fixture dispatch test at `test_evaluation_policy.py:182-203`. |
| 7 | Material, Pset, quantity, Classification, labels, and instance facts become mandatory when authorized evidence exists; verified absence yields `not_required`; required unknowns yield `not_evaluable`. | VERIFIED | Window policy at `operations/window.py:109-142`; generic resolution at `semantic_facts.py:205-378`; parameterized positive/negative/absence tests at `test_evaluation_policy.py:293-394`. |
| 8 | Production accepts only request/surviving/approved-prototype/deterministic authorities and rejects private Gold or prohibited inference. | VERIFIED | Production allowlist and double validation at `benchmark_evaluation.py:35-68, 148-152, 555-570`; prohibited source/precedence tests at `test_evaluation_policy.py:235-290` and production rejection tests at `test_benchmark_evaluation.py:136-201`. |
| 9 | Extraction/open/role failures become structured mandatory `not_evaluable`, never verified absence or an exception. | VERIFIED | `semantic_facts.py:566-578`; `benchmark_evaluation.py:183-271, 449-517`; negative tests at `test_evaluation_policy.py:550-579` and `test_benchmark_evaluation.py:261-291`. |
| 10 | Benchmark Gold is post-application and evaluator-only; public evidence is positive-allowlisted and canary-scanned. | VERIFIED | Type-separated inputs and benchmark boundary at `benchmark_evaluation.py:48-177`; projection/scanner at `evaluation_projection.py:31-106`; privacy tests at `test_benchmark_evaluation.py:294-421`. |
| 11 | LargeBuilding runs with zero Provider calls and reports L1 passed, L2 non-passing, L3 not_required, complete/publishable false, diagnostic-only candidate. | VERIFIED | Real frozen IFC test `test_phase8_large_building.py:29-113`; workflow diagnostic move at `workflow.py:279-340`; validation report records SHA-256 and observed categories. |

**Score:** 10/11 truths verified

## Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `schemas/agent/ifc-repair-evaluation-0.2.schema.json` | Exact Evaluation 0.2 hierarchy/status/evidence schema | VERIFIED | 183 lines; Draft 2020-12 `check_schema` passed fresh. |
| `src/text2ifc_ifc_repair/evaluation_models.py` | Immutable five-state domain | VERIFIED | Substantive frozen records, mandatory invariants, deep evidence freezing. |
| `src/text2ifc_ifc_repair/evaluation.py` | Strict aggregation, serialization, schema validation, independent L1 | VERIFIED | Substantive and wired into benchmark/workflow and compatibility comparator. |
| `src/text2ifc_ifc_repair/evaluation_policy.py` | Versioned operation policy/source authority | VERIFIED | Closed applicability/source/comparison contracts. |
| `src/text2ifc_ifc_repair/semantic_facts.py` | Typed semantic resolution/extraction | VERIFIED | Real IfcOpenShell/Phase 7 extraction, precedence, typed equivalence, typed error path. |
| `src/text2ifc_ifc_repair/registry.py` | Common policy registration/dispatch | VERIFIED | Window and fixture use the same `require_evaluation_policy` and `evaluate_semantics` boundary. |
| `src/text2ifc_ifc_repair/operations/window.py` | Window L1/L2 policy adapter | VERIFIED | Required/conditional L2 policy plus operation-owned L1 authorization and measurements. |
| `src/text2ifc_ifc_repair/benchmark_evaluation.py` | Production/benchmark post-application evaluators | VERIFIED | Real per-operation loop, private role inputs, non-evaluable error conversion, strict aggregate. |
| `src/text2ifc_ifc_repair/evaluation_projection.py` | Public positive allowlist/canary checks | VERIFIED | Projection copies only explicit fields; scanner reads raw file bytes. |
| `src/text2ifc_ifc_repair/workflow.py` | Terminal 0.2 evidence and diagnostic-only retention | VERIFIED | Successful application uses benchmark 0.2; early failures also emit terminal public 0.2. |
| `src/text2ifc_ifc_repair/compare.py` | Legacy compatibility without bypassing new success semantics | FAILED | Compatibility function remains an L1-only 0.1 success/publishability path. |
| Phase 8 focused test files | Positive and adversarial behavior | VERIFIED with debt | 147 focused tests reported passing; fresh targeted negatives passed. Multi-operation regression tests only the role-map helper, not a two-operation full evaluator fixture. |

## Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `evaluation.py` | `evaluation_models.py` / Evaluation 0.2 schema | immutable aggregation and exact validation | WIRED | SDK verified both Plan 01 links. |
| `registry.py` | `evaluation_policy.py` | `OperationDefinition.evaluation_policy` | WIRED | SDK verified; `require_evaluation_policy` and `evaluate_semantics` are active. |
| `operations/window.py` | policy/Registry | `WINDOW_EVALUATION_POLICY` attached by `window_operation_definition` | WIRED | SDK pattern missed naming, but manual inspection verifies lines 109-225 and registry tests exercise dispatch. |
| `evaluation.py` | ChangeSet + Registry + actual IFC diff | `_operation_l1_contexts`, `_authorize_actual_change` | WIRED | Plan pattern named `compare.py`; implementation moved the three-way authorization to `evaluation.py:185-399`, and fault tests exercise it. |
| `benchmark_evaluation.py` | `evaluation.py` / Registry semantic resolver | post-application private/public evaluation | WIRED | Per-operation policy lookup and L1/L2/L3 aggregation at lines 183-381. |
| `evaluation_projection.py` | `workflow.py` | public projection plus finalized bundle scan | WIRED | SDK verified; runtime integration at `workflow.py:279-340, 570-606`. |
| `compare.evaluate_repair_application` | mandatory L2 evaluation | complete/publishable aggregate | NOT_WIRED | This is the blocking legacy bypass. |

## Data-Flow Trace (Level 4)

| Artifact | Data | Source | Produces Real Data | Status |
|---|---|---|---|---|
| Independent L1 | created/modified/removed roots and relationships | reopened damaged/repaired IFC via `normalized_model_diff` | Yes; actual IFC snapshots and operation measurements | FLOWING |
| Production L2 | typed expected/repaired semantic facts | caller-authorized request/surviving/prototype/policy facts plus reopened repaired IFC | Yes; closed source validation and per-fact provenance | FLOWING |
| Benchmark L2 | private original semantic facts | evaluator-only original IFC + operation-scoped mutation roles | Yes; compared against recreated repaired roles | FLOWING |
| Public report | statuses/categories/remediation/source kinds | private Evaluation 0.2 through positive allowlist | Yes; private values/IDs/evidence omitted | FLOWING |
| Legacy comparator | L1/legacy comparator boolean | damaged/repaired IFC + Applicator result | No L2 data enters | DISCONNECTED FROM L2 GATE |

## Behavioral Spot-Checks

| Behavior | Result | Status |
|---|---|---|
| Review regression set: mandatory downgrade, deep immutability, duplicate role, Production private-source rejection, per-operation role map, missing IFC, extraction error, semantic canary, early terminal 0.2 | `12 passed in 3.19s` | PASS |
| Material/Pset/Classification conditional activation, mismatch, no-authority and required-unknown truth table | `32 passed in 1.47s` | PASS |
| Evaluation 0.2 Draft 2020-12 schema | `schema ok` | PASS |
| Legacy applied Window comparator | `1 passed in 38.54s`; the test asserts L1-only Evaluation 0.1 complete success | FAIL (confirms blocker) |
| Phase 8 focused suite (coordinator evidence) | `147 passed` | PASS |
| Full `tests/ifc_repair` (coordinator evidence) | `210 passed` | PASS |
| Compileall/schema/diff check (coordinator evidence) | all passed | PASS |

## Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|---|---|---|---|
| VAL-01 | 08-01, 08-03, 08-04 | SATISFIED | Evaluation 0.2 L1 has structured common/operation evidence and negative IFC fixtures. |
| VAL-02 | 08-02, 08-04 | SATISFIED | Supported Window operation owns a versioned required/conditional semantic allowlist; Registry requires it when evaluated. |
| VAL-03 | 08-01, 08-03, 08-04 | BLOCKED | Five-state 0.2 behavior is correct, but the executable Evaluation 0.1 compatibility path still forces applied-repair success into a boolean and can publish without L2. |
| VAL-04 | 08-04 | SATISFIED | Benchmark original/mapping are evaluator-only; role equivalence and whole-public-boundary tests exist. |
| VAL-05 | 08-02, 08-04 | SATISFIED | Production source allowlist, precedence, prototype compatibility, prohibited-source rejection, and unknown disclosure are implemented. |

No orphaned Phase 8 requirement IDs were found: all VAL-01..VAL-05 appear in PLAN frontmatter and REQUIREMENTS maps no additional requirement to Phase 8.

## Review Fix Audit

| Finding | Code closure | Negative-test closure | Verdict |
|---|---|---|---|
| CR-01 mandatory downgrade | Domain/schema/semantic aggregate reject invalid mandatory state | Public validator and aggregate regressions | CLOSED |
| CR-02 duplicate same-role roots | Singleton cardinality and one-role-per-ID validation | Real IFC duplicate Window, order-independent | CLOSED |
| CR-03 Production accepts `PRIVATE_ORIGINAL` | Constructor and evaluator-entry allowlist checks | Immediate rejection plus tampered frozen-input recheck | CLOSED |
| CR-04 unreadable/missing repaired IFC raises | Model/role failures become evaluator errors and mandatory L2 `not_evaluable` | Both production and benchmark entrypoints | CLOSED |
| CR-05 extraction error becomes `not_required` | Typed extraction error; evaluator converts failure to mandatory `not_evaluable` | Extractor exception and semantic-check regression | CLOSED |
| CR-06 run-global role mapping | Maps keyed by operation ID; semantic role is policy metadata | Mapping unit test covers two operations | CLOSED IN CODE; TEST DEBT |
| WR-01 semantic values omitted from canaries | Canaries derive from private L2 expected values/IDs | Whole-file leak test and Gold/public token classification tests | CLOSED |
| WR-02 early failures emit 0.1 | `_failure_evaluation` constructs hierarchical public 0.2 | Provider/application pre-evaluation terminal test | CLOSED |
| WR-03 nested evidence mutable | Canonical deep freeze + defensive thaw | Post-construction mutation attempts | CLOSED |
| WR-04 adversarial cases missing | CR-01/02/03 regressions added | Fresh targeted set passed | CLOSED |

The Review's ten findings are closed in implementation. CR-06's regression is narrower than its suggested two-operation end-to-end semantic test, but the production loop and operation-keyed lookups are directly visible and no current failure was reproduced.

## Anti-Patterns Found

No TODO/FIXME/placeholder, empty-handler, console-only, or hardcoded-empty user-visible implementation was found in Phase 8 production artifacts. Initial empty collections are populated by deterministic loops or represent valid no-input states.

## Human Verification Required

None. The phase behavior is deterministic/offline and the blocking failure is directly observable in code and an executable repository test.

## Deferred and Remaining Debt

- Phase 10 explicitly owns restoring the LargeBuilding Window's missing Psets, quantities, `IsExternal`, classification, labels, and any later-proven Material mismatch. Those honest L2 failures are not Phase 8 gaps.
- Phase 9 owns the general IFC + request orchestration entrypoint; it does not explicitly own removing the existing L1-only `evaluate_repair_application` success path, so the blocker was not deferred.
- Add a full two-operation evaluator regression with distinct expected/actual semantics and reversed application order. Current CR-06 coverage proves map construction, while static code proves operation-scoped lookup.
- Production evidence construction is a contract seam: Phase 8 validates and compares request/surviving/prototype facts supplied by the caller; Phase 9 must ensure its orchestration actually supplies those non-Gold facts.

## Gaps Summary

The new Evaluation 0.2 implementation is substantive, wired, privacy-safe, and well covered, and the ten code-review findings are materially repaired. The phase goal is nevertheless not universal: an existing applied-repair evaluator remains executable and explicitly returns complete/publishable success without any L2 result. Passing suites do not negate that behavior because one of the passing tests codifies it. Close or hard-fail that legacy success path before treating Phase 8 as achieved.

---

_Verified: 2026-07-19T05:50:06Z_  
_Verifier: the agent (gsd-verifier)_
