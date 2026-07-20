---
phase: 09-general-ifc-text-repair-orchestrator
reviewed: 2026-07-20T01:24:37Z
depth: standard
iteration: 2
files_reviewed: 34
files_reviewed_list:
  - prompts/agent/ifc-repair-changeset-v0.2.md
  - prompts/agent/ifc-repair-intent-v0.1.md
  - prompts/agent/registry.json
  - schemas/agent/ifc-repair-clarification-0.1.schema.json
  - schemas/agent/ifc-repair-intent-0.1.schema.json
  - schemas/agent/ifc-repair-result-0.1.schema.json
  - schemas/agent/ifc-repair-run-state-0.1.schema.json
  - scripts/ifc_repair/repair.py
  - scripts/ifc_repair/run_phase9_live_uat.py
  - src/text2ifc_ifc_repair/api.py
  - src/text2ifc_ifc_repair/cli.py
  - src/text2ifc_ifc_repair/orchestrator.py
  - src/text2ifc_ifc_repair/production_evidence.py
  - src/text2ifc_ifc_repair/provider_stage.py
  - src/text2ifc_ifc_repair/repair_intent.py
  - src/text2ifc_ifc_repair/request_stage.py
  - src/text2ifc_ifc_repair/resolution_flow.py
  - src/text2ifc_ifc_repair/run_artifacts.py
  - src/text2ifc_ifc_repair/run_models.py
  - src/text2ifc_ifc_repair/run_store.py
  - tests/ifc_repair/test_clarification_state.py
  - tests/ifc_repair/test_general_changeset_stage.py
  - tests/ifc_repair/test_orchestrator_application.py
  - tests/ifc_repair/test_orchestrator_resolution.py
  - tests/ifc_repair/test_orchestrator_security.py
  - tests/ifc_repair/test_orchestrator_terminal_matrix.py
  - tests/ifc_repair/test_phase9_large_building.py
  - tests/ifc_repair/test_phase9_offline_e2e.py
  - tests/ifc_repair/test_production_evidence.py
  - tests/ifc_repair/test_repair_cli.py
  - tests/ifc_repair/test_repair_intent.py
  - tests/ifc_repair/test_request_stage.py
  - tests/ifc_repair/test_resolution_flow.py
  - tests/ifc_repair/test_run_state.py
findings:
  critical: 3
  warning: 0
  info: 0
  total: 3
status: issues_found
---

# Phase 09: Code Review Report (Iteration 2)

**Reviewed:** 2026-07-20T01:24:37Z
**Depth:** standard
**Files Reviewed:** 34
**Status:** issues_found

## Summary

The three fix groups close 13 of the original 16 findings, including the raw
RepairIntent-to-live-only-Stage-2 seam, clarification reason normalization and
caller binding, terminal artifact hash verification, truthful statuses,
multi-round CLI behavior, OS-managed locking, reparse containment, and a raw
LargeBuilding Provider path. Three BLOCKERs remain: the `add_detail` public
resume path crashes, explicitly named Prototypes are rejected later by the
production-evidence boundary, and terminal artifact promotion is still not
atomic with the durable terminal state transition.

The complete focused suite reports `366 passed, 1 skipped`. Focused seam checks
also report `25 passed`, and the LargeBuilding raw-provider test executes (not
skips) and passes. Those results do not cover the three failing call chains
below.

## Original Finding Closure

| Original | Result | Iteration 2 evidence |
|---|---|---|
| CR-01 | Closed | `ResolvedOperation.to_dict()` recursively thaws parameters/context before Stage 2 serialization; the real-intent seam exercises nested values. |
| CR-02 | Closed | Resolver emits escaped pointers into the exact `/operations/{id}/context/candidate_targets/0` authority document and Stage 2 validates them. |
| CR-03 | Closed | API passes `resolution.source_ifc_sha256` as `base_model_fingerprint`; Provider identity remains a separate input/context field. |
| CR-04 | Closed | Bound Stage 2 dispatches `generate_live()` and persists redacted live request/response/events; a live-only fake reaches a valid ChangeSet. |
| CR-05 | Closed | Resolver failures are split into terminal failures or mapped to schema-approved clarification reasons. |
| CR-06 | **Open** | Candidate selection is validated before state commit and now writes singular `global_id`, but the other required resume mode, `add_detail`, crashes before validation/commit (BL-01). |
| CR-07 | **Open** | Selection-required Prototype authorization reaches `authorize_prototype()`, but explicit GUID/type-name authorization uses an authority kind rejected by production evidence (BL-02). |
| CR-08 | Closed | API and CLI require and forward `clarification_id` plus `expected_state_version`; stale bindings fail before mutation. |
| CR-09 | Closed | Stage payloads bind immutable artifact hashes, load verifies every binding, and terminal reads verify manifest-declared content. |
| CR-10 | Closed | `_fail()` and cancellation publish a non-publishable public Evaluation 0.2 bundle plus manifest/evidence before the terminal transition. |
| CR-11 | **Open** | Bundle construction is staged, but canonical promotion still precedes and is outside the durable state transaction (BL-03). |
| CR-12 | Closed | `prepare_stage_directory()` rejects symlink/junction/reparse components and is used for index, intent, changeset, and staging directories. |
| WR-01 | Closed | Audit/application statuses are preserved and L1/L2 classification is derived from level results. |
| WR-02 | Closed | Interactive CLI loops with current clarification ID/version and an eight-round bound. |
| WR-03 | Closed | Mutation locking uses OS-managed file locks, so process death releases ownership. |
| WR-04 | Closed | LargeBuilding now feeds raw Stage 1 and Stage 2 Provider JSON through the real parser, resolver, evidence builder, apply, and evaluator. |

## Blockers

### BL-01 [BLOCKER]: `add_detail` continuation always references an uninitialized local

**File:** `src/text2ifc_ifc_repair/api.py:202`
**Related:** `src/text2ifc_ifc_repair/api.py:195-207`, `src/text2ifc_ifc_repair/cli.py:128-129`

**Issue:** The `add_detail` branch constructs its Stage 1 resume output path
with `resumed.state_version`, but `resumed` is assigned only later at line 225.
Python therefore raises `UnboundLocalError` before calling the Provider or
committing the answer. This breaks a schema-advertised public answer mode and
also breaks the CLI whenever a user types natural-language detail instead of a
candidate number. Existing API E2E coverage exercises candidate selection and
Prototype authorization, while CLI tests use a fake API, so the real branch is
not executed.

**Fix:** Derive the pre-commit attempt directory from the caller-bound version,
for example:

```python
resume_version = expected_state_version + 1
intent_dir = self.store.prepare_stage_directory(run_id, "intent")
output_dir = intent_dir / f"resume-{resume_version:03d}"
```

Generate and validate the new `RepairIntent`, bind its immutable artifact, and
only then commit the clarification answer. Add a real `RepairAPI` integration
test for `add_detail`, including a second clarification round.

### BL-02 [BLOCKER]: Explicitly named Prototype authority cannot reach production evaluation

**File:** `src/text2ifc_ifc_repair/resolution_flow.py:341-346`
**Related:** `src/text2ifc_ifc_repair/production_evidence.py:32-34`, `src/text2ifc_ifc_repair/production_evidence.py:221-242`

**Issue:** Explicit `global_id`/`type_name` Prototype resolution records
`kind="explicit_prototype_reference"`. The production-evidence boundary accepts
only `formal_type_binding` and `user_authorized_prototype`, so the otherwise
resolved run deterministically raises `UNAUTHORIZED_SEMANTIC_AUTHORITY` and is
reported as `l2_not_evaluable`. The added test stops after resolution and never
passes the result into `build_production_evidence()`. D-16's explicit named
Prototype path is therefore still unusable end to end.

**Fix:** Represent a successfully resolved explicit request as the same
authorized Prototype contract consumed by production evidence, while retaining
distinct request provenance, for example:

```python
{
    "kind": "user_authorized_prototype",
    "global_id": resolved_id,
    "authorization": "explicit_request_reference",
    "request_provenance": prototype.source.to_dict(),
}
```

Then allow and verify that authorization value in `build_production_evidence()`
and add GUID and type-name tests that traverse resolution, Stage 2, production
evidence, and evaluation.

### BL-03 [BLOCKER]: Canonical terminal publication and durable state remain a partial commit

**File:** `src/text2ifc_ifc_repair/run_artifacts.py:91-100`
**Related:** `src/text2ifc_ifc_repair/api.py:355-368`, `src/text2ifc_ifc_repair/api.py:371-387`

**Issue:** The publisher now safely builds and scans a staging directory, but
line 95 atomically renames it to canonical `published/` before returning. Only
after that return does `RepairAPI` acquire the RunStore lock and append the
terminal transition. A process exit, state conflict, or state-write I/O failure
between these operations leaves a canonical successful IFC/evidence bundle
while durable state remains `changeset_ready`. Retrying cannot recover through
the normal path because the publisher rejects the existing directory with
`ARTIFACT_ALREADY_EXISTS`. The new test proves only that a pre-promotion
manifest failure leaves no bundle; it does not test failure after promotion and
before state commit.

**Fix:** Keep the complete bundle under a unique staged name, then add one
RunStore terminal-commit operation that holds the run mutation lock, revalidates
the expected state version and staged hashes, promotes the directory, and
writes the terminal transition/state as one recoverable protocol. At minimum,
persist an explicit prepared-publication record and implement deterministic
startup recovery for either side of the rename/state-write boundary. Add
fault-injection tests immediately after directory promotion and immediately
before/after `state.json` replacement.

---

_Reviewed: 2026-07-20T01:24:37Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
