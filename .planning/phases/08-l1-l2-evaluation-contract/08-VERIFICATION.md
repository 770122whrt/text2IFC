---
phase: 08-l1-l2-evaluation-contract
verified: 2026-07-19T06:06:38Z
status: passed
score: 11/11 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 10/11
  gaps_closed:
    - "Legacy evaluate_repair_application now exposes L2 as not_evaluable/legacy_assurance_unavailable and always sets complete_repair_success=false and successful_artifact_publishable=false."
  gaps_remaining: []
  regressions: []
---

# Phase 8: L1/L2 Evaluation Contract Verification Report

**Phase Goal:** Every applied IFC repair receives a versioned, evidence-bearing evaluation in which mandatory L1 physical/relationship correctness and mandatory L2 semantic fidelity are independently decided and jointly gate complete success; L3 is non-gating; benchmark Gold is evaluator-only and production uses non-Gold authority.

**Verified:** 2026-07-19T06:06:38Z  
**Status:** passed  
**Re-verification:** Yes - after closure of the sole initial gap

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|---|---|---|
| 1 | Evaluation 0.2 is exact-versioned, schema-backed, hierarchical, and legacy 0.1 is read without invented L2 assurance. | VERIFIED | `evaluation_models.py:13-14`, `evaluation.py:802-840`, and the Draft 2020-12 schema; contract tests cover hierarchy, round-trip, malformed reports, and legacy projection. |
| 2 | Every check/level uses exactly `passed`, `failed`, `partial`, `not_required`, or `not_evaluable`, with reason and evidence. | VERIFIED | `evaluation_models.py:19-25, 126-171`; `test_evaluation_contract.py:174-239`. |
| 3 | The supported Evaluation 0.2 path requires application, preservation, mandatory L1, and mandatory L2 to pass; L3 is `not_required` and non-gating. | VERIFIED | `evaluation.py:643-758`; mandatory downgrade invariants at `evaluation_models.py:155-169` and `evaluation.py:860-900`; negative truth-table tests at `test_evaluation_contract.py:241-363`. |
| 4 | No supported applied-repair evaluator can declare complete/publishable success without mandatory L2. | VERIFIED | Commit `45f51cba` preserves legacy 0.1 L1/metrics but emits L2 `not_evaluable` with `legacy_assurance_unavailable` and forces complete/publishable false (`compare.py:20-91`). Updated real IFC regression asserts all four outcomes and passed fresh. |
| 5 | L1 independently reopens IFC, verifies schema/source immutability, actual scope, topology, containment, duplicates, and tolerances; Applicator self-report does not authorize drift. | VERIFIED | `evaluation.py:45-539`, Window measurements at `operations/window.py:621-940`; fault tests cover collateral Wall drift, extra/deleted roots, relationship faults, duplicate role/chain, wrong host/storey, tolerance, unreadable output, and schema mismatch. |
| 6 | Window and future-family fixtures use one versioned Registry policy/evaluator seam. | VERIFIED | `registry.py:35-129`; Window policy attachment at `operations/window.py:109-225`; fixture dispatch test at `test_evaluation_policy.py:182-203`. |
| 7 | Material, Pset, quantity, Classification, labels, and instance facts become mandatory when authorized evidence exists; verified absence yields `not_required`; required unknowns yield `not_evaluable`. | VERIFIED | Window policy at `operations/window.py:109-142`; generic resolution at `semantic_facts.py:205-378`; parameterized positive/negative/absence tests at `test_evaluation_policy.py:293-394`. |
| 8 | Production accepts only request/surviving/approved-prototype/deterministic authorities and rejects private Gold or prohibited inference. | VERIFIED | Production allowlist and double validation at `benchmark_evaluation.py:35-68, 148-152, 555-570`; prohibited source/precedence tests at `test_evaluation_policy.py:235-290` and production rejection tests at `test_benchmark_evaluation.py:136-201`. |
| 9 | Extraction/open/role failures become structured mandatory `not_evaluable`, never verified absence or an exception. | VERIFIED | `semantic_facts.py:566-578`; `benchmark_evaluation.py:183-271, 449-517`; negative tests at `test_evaluation_policy.py:550-579` and `test_benchmark_evaluation.py:261-291`. |
| 10 | Benchmark Gold is post-application and evaluator-only; public evidence is positive-allowlisted and canary-scanned. | VERIFIED | Type-separated inputs and benchmark boundary at `benchmark_evaluation.py:48-177`; projection/scanner at `evaluation_projection.py:31-106`; privacy tests at `test_benchmark_evaluation.py:294-421`. |
| 11 | LargeBuilding runs with zero Provider calls and reports L1 passed, L2 non-passing, L3 not_required, complete/publishable false, diagnostic-only candidate. | VERIFIED | Real frozen IFC test `test_phase8_large_building.py:29-113`; workflow diagnostic move at `workflow.py:279-340`; validation report records SHA-256 and observed categories. |

**Score:** 11/11 truths verified

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
| `src/text2ifc_ifc_repair/compare.py` | Legacy compatibility without bypassing new success semantics | VERIFIED | Legacy metrics/L1 remain readable; absent L2 is explicit and complete/publishable are forced false. |
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
| `compare.evaluate_repair_application` | mandatory L2 assurance boundary | explicit unavailable assurance and fail-closed publication | WIRED | L2 is `not_evaluable`/`legacy_assurance_unavailable`; success and publication cannot be asserted from the compatibility path. |

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
| Legacy applied Window comparator after gap closure | Fresh re-verification: `1 passed in 39.08s`; asserts L1 passed, L2 not_evaluable, complete false, publishable false | PASS |
| Phase 8 focused suite (coordinator evidence) | `147 passed` | PASS |
| Full `tests/ifc_repair` (coordinator evidence) | `210 passed` | PASS |
| Compileall/schema/diff check (coordinator evidence) | all passed | PASS |

## Requirements Coverage

| Requirement | Source Plans | Status | Evidence |
|---|---|---|---|
| VAL-01 | 08-01, 08-03, 08-04 | SATISFIED | Evaluation 0.2 L1 has structured common/operation evidence and negative IFC fixtures. |
| VAL-02 | 08-02, 08-04 | SATISFIED | Supported Window operation owns a versioned required/conditional semantic allowlist; Registry requires it when evaluated. |
| VAL-03 | 08-01, 08-03, 08-04 | SATISFIED | Five-state 0.2 behavior is correct; the legacy compatibility evaluator now explicitly reports unavailable L2 assurance and fails closed. |
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

## Re-verification History

The initial verification found one blocker: the callable Evaluation 0.1 compatibility evaluator could return complete/publishable success without L2. Commit `45f51cba` closed it by retaining historical L1, geometry, tolerance, and operation metrics while adding explicit L2 `not_evaluable` / `legacy_assurance_unavailable` and forcing both success booleans false. The updated real LargeBuilding Window application test passed fresh in `39.08s`; the coordinator additionally reports `83 passed` for compare/L1/contract, `210 passed in 156.08s` for all `tests/ifc_repair`, and passing compileall/diff checks.

No gaps remain. Evaluation 0.2 jointly gates mandatory L1/L2, legacy 0.1 fails closed when L2 assurance is unavailable, L3 remains non-gating, and benchmark/production evidence authority remains correctly separated.

---

_Verified: 2026-07-19T06:06:38Z_  
_Verifier: the agent (gsd-verifier)_
