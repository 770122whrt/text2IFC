---
phase: 09-general-ifc-text-repair-orchestrator
reviewed: 2026-07-20T01:50:39Z
depth: standard
iteration: 3
files_reviewed: 10
files_reviewed_list:
  - src/text2ifc_ifc_repair/api.py
  - src/text2ifc_ifc_repair/orchestrator.py
  - src/text2ifc_ifc_repair/production_evidence.py
  - src/text2ifc_ifc_repair/resolution_flow.py
  - src/text2ifc_ifc_repair/run_artifacts.py
  - src/text2ifc_ifc_repair/run_store.py
  - tests/ifc_repair/test_phase9_offline_e2e.py
  - tests/ifc_repair/test_production_evidence.py
  - tests/ifc_repair/test_resolution_flow.py
  - tests/ifc_repair/test_run_state.py
findings:
  critical: 2
  warning: 2
  info: 0
  total: 4
status: issues_found
---

# Phase 09: Code Review Report (Iteration 3)

**Reviewed:** 2026-07-20T01:50:39Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

The real `add_detail` continuation no longer references an uninitialized local,
and the new two-round public-API test exercises the repaired branch. The
terminal-publication fix also closes the original partial-commit window: a
hidden prepared bundle, durable recovery journal, content-addressed promoted
bundle, and state-authoritative read path recover the three tested crash points
without exposing `published/`.

The explicit Prototype fix is not complete for the normal IFC index shape.
Type-name and Type-GlobalId resolution authorize the `IfcTypeObject` GlobalId,
while production evidence looks up only product-keyed `ElementRecord` entries.
The new unit test passes because it supplies a synthetic type-keyed record that
the actual indexer does not create. A separate concurrent-resume race can also
overwrite artifacts after another clarification answer has durably bound their
hashes, making an otherwise successful run unreadable.

Focused review tests report `56 passed, 1 skipped`; the parent orchestration run
reports `371 passed, 1 skipped`. A direct production-evidence reproduction with
the real product-keyed record shape fails with
`MISSING_AUTHORIZED_RECORD: user_authorized_prototype:type-1`.

## Iteration 2 Blocker Closure

| Iteration 2 blocker | Result | Iteration 3 evidence |
|---|---|---|
| BL-01 `add_detail` uninitialized `resumed` | Closed | `api.py:198-236` derives the resume directory from the caller-bound version and persists/binds the regenerated intent. `test_add_detail_can_span_two_real_api_clarification_rounds` traverses two real continuations and succeeds. |
| BL-02 explicit Prototype production authority | **Open** | The authority kind and authorization value now pass the allowlist, but Type references still fail the actual product-keyed index boundary (BL-01 below). |
| BL-03 terminal publication partial commit | Closed | `run_store.py:185-301` journals before promotion and recovers promotion/transition/state replacement. Fault-injection tests cover promotion and state-write boundaries and keep canonical `published/` absent. |

## Blockers

### BL-01 [BLOCKER]: Type-name and Type-GlobalId Prototypes still fail production evidence

**Files:** `src/text2ifc_ifc_repair/resolution_flow.py:332-346`, `src/text2ifc_ifc_repair/production_evidence.py:227-245`

**Issue:** `_explicit_prototype()` returns the matched `type_global_id` for a
type-name reference (and for a request that names the type GUID). The production
path builds `records_by_global_id` from `record.ifc_global_id`, because the index
contains product records carrying `type_global_id`; it does not create a second
record keyed by the `IfcTypeObject` GUID. `_operation_candidates()` nevertheless
calls `_record(records_by_global_id, global_id)` for every
`user_authorized_prototype`. Therefore a normal explicit type-name request still
terminates as `MISSING_AUTHORIZED_RECORD`/`l2_not_evaluable`.

The added production test at
`tests/ifc_repair/test_production_evidence.py:308-345` hides this by using
`"prototype-1": _record("prototype-1", ...)`, which is not the type-name
resolution shape. The existing resolution test explicitly demonstrates the
mismatch: product `0BBBB...` carries type `0TYPE...`, and the authority stores
`0TYPE...`.

**Fix:** Preserve a product record identity alongside the explicitly requested
type authority, or teach production evidence to resolve a type GUID through a
uniquely matching product record's `type_global_id` and use only its inherited
type facts. Add GUID and type-name public-API tests that traverse resolution,
Stage 2, production evidence, evaluation, and terminal publication without a
synthetic type-keyed record.

### BL-02 [BLOCKER]: Concurrent clarification resumes can corrupt committed artifact bindings

**Files:** `src/text2ifc_ifc_repair/api.py:161-258`

**Issue:** The initial clarification ID/version check happens before Provider
work and before any RunStore mutation lock. `add_detail` then writes to the
deterministic `intent/resume-{version}` directory and all answer modes write the
deterministic `api-context-v{version}.json` before
`RunStore.continue_with_answer()` performs the compare-and-swap. Two callers can
both pass the initial check. The faster caller can bind and commit its hashes;
the slower caller can then overwrite the same files and lose the state CAS.
Subsequent `load()` verifies the winner's stored hashes against the loser's
bytes and raises `RUN_TAMPER_DETECTED`, corrupting a valid run.

**Fix:** Write each resume attempt under a unique hidden attempt directory.
Under one RunStore lock, revalidate clarification ID/version, validate the
answer and generated intent, promote the winning attempt to a versioned
immutable path, create its bindings, and append the resume transition. Losing
attempts must never be able to mutate paths referenced by committed state. Add
a two-thread/barrier test in which the stale Provider response completes after
the winning state commit and prove the winner remains loadable.

## Warnings

### WR-01 [WARNING]: RepairAPI callers can disable its required deferred-publication invariant

**Files:** `src/text2ifc_ifc_repair/api.py:57-58`, `src/text2ifc_ifc_repair/api.py:381-386`

**Issue:** `defer_publication=True` is installed as a default and then overwritten
by arbitrary `orchestrator_options`. A caller can pass
`{"defer_publication": false}`; the orchestrator promotes immediately and returns
no `prepared_root`, after which the API raises
`TERMINAL_PUBLICATION_NOT_PREPARED`. This is a valid constructor input that
defeats the new durability protocol.

**Fix:** Make deferred publication an API-owned invariant: reject that key in
`orchestrator_options`, or apply `defer_publication=True` after merging caller
options. Add a constructor test proving callers cannot disable it.

### WR-02 [WARNING]: The journal-before-promotion crash point is implemented but not tested

**File:** `tests/ifc_repair/test_run_state.py:389-448`

**Issue:** The production code exposes four fault points, including
`after_journal`, but the test titled “every commit crash window” parametrizes
only `after_promotion`, `before_state_replace`, and `after_state_replace`.
Recovery from a durable journal while the bundle is still prepared is a
distinct branch at `run_store.py:786-789`; a regression there would strand the
run despite the current test name and coverage claim.

**Fix:** Add `after_journal` to the parametrization and assert recovery promotes
the prepared bundle once, commits the terminal state, removes the journal, and
remains idempotent.

---

_Reviewed: 2026-07-20T01:50:39Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
