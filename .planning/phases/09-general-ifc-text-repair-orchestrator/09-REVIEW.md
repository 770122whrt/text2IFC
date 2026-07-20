---
phase: 09-general-ifc-text-repair-orchestrator
reviewed: 2026-07-20T00:22:04Z
depth: standard
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
  critical: 12
  warning: 4
  info: 0
  total: 16
status: issues_found
---

# Phase 09: Code Review Report

**Reviewed:** 2026-07-20T00:22:04Z  
**Depth:** standard  
**Files Reviewed:** 34  
**Status:** issues_found

## Summary

The submitted implementation does not provide a working default IFC + text -> terminal production path. Four independent defects prevent the real Stage 2 path from completing: real resolved parameters are not JSON serializable, resolver-produced evidence pointers do not address the Stage 2 authority document, the Provider-model fingerprint is reused as the IFC base fingerprint, and the bound Stage 2 does not support the production live Provider interface. Clarification/resume, immutable evidence, and atomic publication also have correctness and security gaps.

The focused suite still reports `53 passed` because the offline and LargeBuilding tests inject hand-authored intents, ChangeSets, evaluation evidence, and application/evaluation stages. Two direct reproductions against the real seams produced:

- `RunStoreError PUBLIC_RECORD_INVALID: 'ambiguous' is not one of [...]` for a real ambiguous target.
- `TypeError: Object of type mappingproxy is not JSON serializable` before the real Stage 2 Provider call; after manually thawing the operation, every resolver-produced evidence pointer was rejected as `EVIDENCE_POINTER_NOT_FOUND`.

The live UAT's `MODEL_FINGERPRINT_MISMATCH` is partly a model contract failure at Stage 1, but it masks deterministic implementation bugs that would prevent success even if the model returned a valid Stage 1 object.

## Blockers

### CR-01 [BLOCKER]: Real resolved operations cannot be serialized for Stage 2

**File:** `src/text2ifc_ifc_repair/provider_stage.py:50`  
**Related:** `src/text2ifc_ifc_repair/provider_stage.py:533-538`, `src/text2ifc_ifc_repair/resolution_flow.py:43`, `src/text2ifc_ifc_repair/repair_intent.py:173`

**Issue:** `RepairIntent` deep-freezes nested parameter objects as `MappingProxyType`. `ResolvedOperation.to_dict()` only shallow-copies `parameters`, and `_plain_operation()` then calls `json.dumps`, which raises on the nested mapping proxies. The default `RepairAPI` therefore returns `provider_failed` before making any Stage 2 call. This was reproduced with the real default Registry and resolver.

**Fix:** Recursively thaw the resolved operation before serialization, for example by using the existing `thaw_json()` utility in `ResolvedOperation.to_dict()` or `_plain_operation()`. Add an integration test that passes an actual `RepairIntent.from_dict()` result through `resolve_repair_intent()` and `generate_bound_changeset()` without reconstructing plain fixture dictionaries.

### CR-02 [BLOCKER]: Resolver evidence pointers can never validate against the Stage 2 document

**File:** `src/text2ifc_ifc_repair/resolution_flow.py:140-143`  
**Related:** `src/text2ifc_ifc_repair/provider_stage.py:449-453`, `src/text2ifc_ifc_repair/provider_stage.py:519-522`

**Issue:** Resolution emits pointers such as `resolution:/operation-1/candidates/0/evidence/0`, but Stage 2 builds a document rooted at `/operations/{operation_id}` whose candidate data lives under `/context/candidate_targets`. The emitted path exists in neither representation. After manually thawing CR-01, a real one-operation run produced five `EVIDENCE_POINTER_NOT_FOUND` failures.

**Fix:** Define one canonical resolved-authority JSON shape and generate pointers into that exact persisted shape, e.g. `resolved:/operations/{escaped_operation_id}/context/candidate_targets/0`. Validate every generated pointer inside `resolve_repair_intent()` before returning a resolved batch.

### CR-03 [BLOCKER]: Provider model identity is confused with the IFC base fingerprint

**File:** `src/text2ifc_ifc_repair/api.py:189-196`  
**Related:** `src/text2ifc_ifc_repair/request_stage.py:220-223`, `src/text2ifc_ifc_repair/provider_stage.py:476-479`, `src/text2ifc_ifc_repair/orchestrator.py:106-109`

**Issue:** Stage 1 correctly defines `RepairIntent.model_fingerprint` as the hash of the Provider model identifier. `RepairAPI` passes that value to Stage 2 as `MODEL_FINGERPRINT`, Stage 2 requires it in `ChangeSet.base_model_fingerprint`, and application then compares it to the source IFC SHA-256. Those are different domains, so a contract-compliant generated ChangeSet always terminates with `BASE_MODEL_FINGERPRINT_MISMATCH`. The offline/LargeBuilding tests bypass this by hand-authoring `base_model_fingerprint` from the source hash.

**Fix:** Split the fields into `provider_model_fingerprint` and `base_model_fingerprint`. Bind Stage 2 and the ChangeSet base field to `resolution.source_ifc_sha256`/the persisted source binding; retain Provider model identity only as trace metadata.

### CR-04 [BLOCKER]: Bound Stage 2 cannot call the production live Provider

**File:** `src/text2ifc_ifc_repair/provider_stage.py:77-83`

**Issue:** `generate_bound_changeset()` unconditionally calls `provider.generate_candidate()`. `RepairAPI.from_environment()` constructs `OpenAICompatibleLiveProvider`, whose public generation method is `generate_live()`. Stage 1 explicitly supports both interfaces, but Stage 2 does not. If the live UAT ever passes Stage 1, it will fail with `AttributeError` before Stage 2 evidence is recorded.

**Fix:** Reuse the Stage 1 `_call_provider`-style dispatch for Stage 2, persist redacted live request/response/events per attempt, and test `RepairAPI.from_environment()` with a live-interface-only fake.

### CR-05 [BLOCKER]: Actual resolver reason codes cannot be persisted as clarification

**File:** `schemas/agent/ifc-repair-clarification-0.1.schema.json:20-24`  
**Related:** `src/text2ifc_ifc_repair/resolution_flow.py:93-105`, `src/text2ifc_ifc_repair/resolution_flow.py:237-251`, `src/text2ifc_ifc_repair/api.py:317-325`

**Issue:** The resolver returns `ambiguous`, `conflict`, `not_found`, `unsupported`, `stale_index`, `context_budget_exceeded`, and `missing_evidence`. `_clarification()` copies those values unchanged, but the schema only accepts `ambiguous_target`, `selector_conflict`, `missing_required_parameter`, `prototype_selection`, and `additional_target_detail`. A real ambiguous IFC reproduced an exception during the transition instead of a `clarification_required` result.

**Fix:** Introduce an explicit total mapping from resolver outcomes to either schema-approved clarification reasons or terminal failure stages. Extend the schema only for genuinely user-answerable reasons; stale index, unsupported capability, and context failure should not be disguised as answerable clarification.

### CR-06 [BLOCKER]: Candidate selection consumes the clarification and then creates an invalid RepairIntent

**File:** `src/text2ifc_ifc_repair/api.py:137-160`  
**Related:** `schemas/agent/ifc-repair-intent-0.1.schema.json:77-114`

**Issue:** `continue_with_answer()` first commits the answer and moves the durable state back to `intent_ready`. It then writes `target_query.exact_global_ids`, a field forbidden by the exact RepairIntent schema (the contract uses singular `global_id`). `RepairIntent.from_dict()` raises after the clarification has already been consumed, leaving a nonterminal run that cannot be answered again.

**Fix:** Validate and construct the resumed intent before committing the state transition, set `global_id` to the selected public ID, clear only conflicting selectors according to a documented policy, and make the state+artifact update one atomic commit.

### CR-07 [BLOCKER]: Prototype authorization is unreachable and explicit named Prototypes are ignored

**File:** `src/text2ifc_ifc_repair/api.py:154-176`  
**Related:** `src/text2ifc_ifc_repair/api.py:315`, `src/text2ifc_ifc_repair/resolution_flow.py:174-191`, `src/text2ifc_ifc_repair/resolution_flow.py:201-234`

**Issue:** `_clarification()` always exposes `select_candidate` for any candidate list, including `prototype_selection`. The API interprets that answer as a new target selector instead of calling `authorize_prototype()`. It has no `authorize_prototype` branch at all. Separately, `prototype_intent` values with `reference_kind=global_id` or `type_name` are never deterministically resolved or carried as authorized evidence. D-16 is therefore not implemented through the public API.

**Fix:** Emit `authorize_prototype` only for prototype clarification, persist the affirmative authorization, and resume through `authorize_prototype()` with the stored operation ID/token. Resolve explicitly named GUID/type references deterministically (or clarify if ambiguous) and record distinct request provenance.

### CR-08 [BLOCKER]: The public resume API bypasses clarification version/ID binding

**File:** `src/text2ifc_ifc_repair/api.py:137-147`  
**Related:** `src/text2ifc_ifc_repair/run_store.py:236-257`, `src/text2ifc_ifc_repair/cli.py:45-52`

**Issue:** `RunStore` supports compare-and-append using caller-supplied clarification ID and expected state version, but `RepairAPI.continue_with_answer(run_id, answer)` discards both caller bindings and silently substitutes the latest stored values. A delayed answer from an older prompt can therefore be accepted against a newer clarification whenever its shape/token still matches. The CLI likewise sends only run ID and answer.

**Fix:** Require `clarification_id` and `expected_state_version` in the public API/CLI continuation contract and pass them unchanged to `RunStore`. Reject stale responses rather than rebinding them to current state.

### CR-09 [BLOCKER]: Persisted stage and terminal artifacts are not content-bound or verified

**File:** `src/text2ifc_ifc_repair/api.py:128-135`  
**Related:** `src/text2ifc_ifc_repair/api.py:150-175`, `src/text2ifc_ifc_repair/run_store.py:493-531`, `src/text2ifc_ifc_repair/run_store.py:289-310`

**Issue:** Transitions hash small payloads containing path strings, not the content at those paths. `api-context.json` is written non-atomically and reloaded on resume without checking its hash, request hash, prompt/model bindings, or source binding. Final `read_result()` validates only the transition chain and source IFC; it never verifies the manifest or the hashes of evaluation/successful IFC artifacts. A modified context can alter resumed operations, and a modified successful IFC/evaluation remains reported as valid.

**Fix:** Persist `{path, sha256, schema_version}` for every immutable stage artifact in the transition, verify all completed-stage hashes before resume, and verify the final manifest plus referenced artifacts on every terminal read. Write `api-context.json` atomically and bind it to the stored request/source/run/version.

### CR-10 [BLOCKER]: Early terminal failures do not produce mandatory Evaluation 0.2 evidence

**File:** `src/text2ifc_ifc_repair/api.py:278-287`  
**Related:** `src/text2ifc_ifc_repair/api.py:95-126`, `src/text2ifc_ifc_repair/api.py:214-215`

**Issue:** Invalid IFC, index failure, Stage 1 failure, and Stage 2 failure call `_fail()`, which only appends a state transition. It does not call the terminal artifact publisher, so there is no public Evaluation 0.2, manifest, or immutable failure evidence. The terminal-matrix test calls `publish_terminal_artifacts()` directly and does not exercise these API paths.

**Fix:** Route every terminal outcome through one finalizer that creates a schema-valid non-publishable Evaluation 0.2, evidence, manifest, and result transition. Keep clarification nonterminal, but finalize cancel/unsupported/provider/audit/application failures uniformly.

### CR-11 [BLOCKER]: Successful publication is a multi-step partial commit

**File:** `src/text2ifc_ifc_repair/run_artifacts.py:70-91`  
**Related:** `src/text2ifc_ifc_repair/api.py:254-275`

**Issue:** The publisher writes evaluation, writes evidence, moves the candidate into the canonical `successful/` path, then builds the manifest and performs the whole-bundle canary scan. Manifest overflow, I/O failure, or a canary found in any earlier artifact raises after the canonical successful IFC already exists. The API then separately writes three state transitions without holding a transaction lock. A crash can therefore expose a success artifact while durable state remains `changeset_ready`, `application_ready`, or `evaluated`.

**Fix:** Build and validate the entire terminal bundle in a unique staging directory, including manifest and final canary scan; fsync it, then atomically rename/publish it while holding the run mutation lock and commit one terminal state transition referencing the final hashes. On failure, retain only diagnostic staging evidence.

### CR-12 [BLOCKER]: Intermediate run directories permit symlink/junction escape writes

**File:** `src/text2ifc_ifc_repair/api.py:107-124`  
**Related:** `src/text2ifc_ifc_repair/api.py:197`, `src/text2ifc_ifc_repair/orchestrator.py:110-121`, `src/text2ifc_ifc_repair/request_stage.py:48-49`

**Issue:** `RunStore` validates the run directory and final artifact references, but the API directly uses `run_dir/index`, `run_dir/intent`, `run_dir/changeset`, and `run_dir/staging` without no-follow containment checks. If any child is replaced by a symlink or Windows junction/reparse point, Provider evidence, SQLite data, or the application candidate can be created/overwritten outside the output root before final containment notices. The Windows symlink test is skipped when link privilege is unavailable and does not cover junctions or these stage directories.

**Fix:** Create every stage directory with create-new/no-follow semantics under a locked run, reject symlinks and Windows junction/reparse points for every path component, resolve-and-contain immediately before each open, and use descriptor-relative/no-follow file creation where supported.

## Warnings

### WR-01 [WARNING]: API terminal status and failure Evaluation diagnostics are not truthful

**File:** `src/text2ifc_ifc_repair/api.py:266-275`  
**Related:** `src/text2ifc_ifc_repair/orchestrator.py:237-269`

**Issue:** Every non-success result after application is collapsed to `RunStage.NOT_PUBLISHABLE`, so `audit_failed` and `application_failed` never reach the public status/CLI exit classes defined for them. `_failure_public_evaluation()` also marks `application.valid` as failed even for post-application L2 evidence/evaluator failures, and `_evaluation_terminal_status()` maps any top-level `failed` report to `l2_failed`, including L1 failure.

**Fix:** Map each orchestration status to its matching durable stage, preserve actual application/preservation outcomes in synthetic evaluations, and derive L1/L2 terminal classification from per-level results rather than the aggregate status alone.

### WR-02 [WARNING]: Interactive CLI handles at most one clarification round

**File:** `src/text2ifc_ifc_repair/cli.py:49-53`

**Issue:** The CLI prompts once, calls continuation once, and renders whatever comes back. If added detail yields another ambiguity or a multi-operation run needs a later clarification, default interactive mode exits with `clarification_required` instead of continuing the same repair-scoped session to terminal state.

**Fix:** Loop while status is `clarification_required`, rendering and submitting the exact current clarification binding each time, with an explicit bounded round count and safe EOF/cancel termination.

### WR-03 [WARNING]: A crashed process can permanently brick a run with a stale lock

**File:** `src/text2ifc_ifc_repair/run_store.py:533-552`

**Issue:** The O_EXCL lock is removed only by the current process's `finally`. Process termination or host crash leaves `.transition.lock` forever, and every later resume returns `RUN_LOCKED`. The recorded PID is never used for stale-lock recovery.

**Fix:** Store PID plus process-start/nonce metadata, detect demonstrably stale owners under a separate atomic recovery protocol, or use an OS-managed advisory lock whose ownership is released on process exit.

### WR-04 [WARNING]: End-to-end and LargeBuilding tests are fixture self-proofs

**File:** `tests/ifc_repair/test_phase9_offline_e2e.py:74-110`  
**Related:** `tests/ifc_repair/test_phase9_large_building.py:42-87`, `tests/ifc_repair/test_general_changeset_stage.py:66-99`

**Issue:** The advertised E2E tests inject a prebuilt `RepairIntent`, hand-authored ChangeSet with the correct source hash, fake evidence builder, and fake apply/evaluation stages. LargeBuilding also bypasses both real Agent stages and production evidence. The Stage 2 unit fixture manually supplies the pointer shape the validator expects instead of using `resolve_repair_intent()`. Consequently all 53 focused tests pass while CR-01 through CR-04 make the default production route impossible.

**Fix:** Add at least one offline provider double whose raw Stage 1 and Stage 2 JSON travels through the real `generate_repair_intent`, real resolver/context, real `generate_bound_changeset`, real evidence builder, real apply, and real evaluator. Keep private damage creation outside the API, but do not inject post-boundary domain objects.

---

_Reviewed: 2026-07-20T00:22:04Z_  
_Reviewer: the agent (gsd-code-reviewer)_  
_Depth: standard_
