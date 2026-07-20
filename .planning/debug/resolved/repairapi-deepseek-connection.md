---
status: resolved
trigger: "Phase 09.1 real DeepSeek UAT fails through RepairAPI with APIConnectionError while a direct call using the same rendered prompt succeeds."
created: 2026-07-21
updated: 2026-07-21T01:35:00+08:00
---

# Debug Session: RepairAPI DeepSeek Connection

## Symptoms

- expected: Four Phase 09.1 live UAT cases should complete Stage 1 and proceed to Stage 2 when the DeepSeek provider is reachable and returns a contract-valid response.
- actual: Every case exhausts two Stage 1 attempts with `REPAIR_INTENT_RETRY_EXHAUSTED`; Stage 2 is never called and no IFC is produced.
- errors: Safe attempt evidence reports `APIConnectionError` / `provider_connection_error` from `deepseek-openai-compatible`.
- timeline: Reproduced in three full UAT runs on 2026-07-20 after the Phase 09.1 Type-evidence correction work.
- reproduction: Run `scripts/ifc_repair/run_phase9_live_uat.py` with the configured `.env`; a direct `OpenAICompatibleLiveProvider` call using the exact saved rendered prompt succeeds, while the RepairAPI path fails.

## Current Focus

- hypothesis: Historical connection failures were external/transient or stale-process configuration; the deterministic defects are `.env` precedence and cross-family Prototype candidate leakage.
- test: Compare redacted environment precedence, run same-process direct/RepairAPI controls, and rerun all four live cases after operation-scoped Type filtering.
- expecting: Repository `.env` overrides stale process Provider values and the dimensions case offers exactly one IfcWindowStyle before reaching Stage 2.
- next_action: Complete Phase 09.1 documentation and hand genuine L2 authoring gaps to Phase 10.
- reasoning_checkpoint:
- tdd_checkpoint: enabled

## Evidence

- timestamp: 2026-07-20T16:20:04+08:00
  observation: Four UAT cases each made exactly two Stage 1 calls, zero Stage 2 calls, and recorded `APIConnectionError`.
- timestamp: 2026-07-20T16:20:04+08:00
  observation: A manual direct provider call using the exact saved rendered prompt returned valid JSON with 2,592 prompt tokens and 2,021 completion tokens.
- timestamp: 2026-07-21T00:00:00+08:00
  observation: The worktree already contains extensive unrelated modified, deleted, and untracked user changes, including files on the suspected call path; investigation and commits must preserve and narrowly stage only owned hunks/files.
- timestamp: 2026-07-21T00:00:01+08:00
  observation: `RepairAPI.from_environment` passes the supplied mapping unchanged into `load_openai_compatible_runtime_config`; `generate_repair_intent` passes the saved rendered prompt unchanged to `OpenAICompatibleLiveProvider.generate_live`, so RepairAPI introduces no different transport request shape before the failing call.
- timestamp: 2026-07-21T00:00:02+08:00
  observation: `run_phase9_live_uat._environment` starts from `os.environ` and applies `.env` entries with `setdefault`, so stale process values win. The established Phase 6.2 live CLI has a regression test requiring `.env` to override stale provider, base URL, model, and key values.
- timestamp: 2026-07-21T00:00:03+08:00
  observation: Common-pattern scan maps the direct-vs-UAT behavior to Environment/Config; no async, multiprocessing, or alternate provider invocation exists on the Stage 1 path.
- timestamp: 2026-07-21T00:55:00+08:00
  observation: Controlled direct and same-process RepairAPI calls both succeeded; RepairAPI reached application and L2, excluding a deterministic transport-shape difference.
- timestamp: 2026-07-21T01:05:00+08:00
  observation: The first recovered four-case UAT passed three cases but the dimensions case exposed DoorStyle and SpaceType because candidates were bounded before operation/category filtering.
- timestamp: 2026-07-21T01:25:00+08:00
  observation: After operation-scoped class and dimension filtering, all four live cases contract-passed and reached Stage 2/L2.
- timestamp: 2026-07-21T01:35:00+08:00
  observation: A focused RED test proved `.env` could not override stale process Provider values; assignment-based merge fixed it and 22 focused tests plus config check passed.
- timestamp: 2026-07-21T01:46:00+08:00
  observation: Safe cause-chain evidence exposed `APIConnectionError → ConnectError → PermissionError` in sandboxed runs; the identical command with approved external-network permission passed all four cases.

## Eliminated

- hypothesis: The prompt is intrinsically too large or structurally invalid for DeepSeek.
  reason: The exact saved prompt succeeded through a direct provider call.

## Resolution

- root_cause: The repeated UAT connection failures were caused by the sandbox denying external sockets, proven by `APIConnectionError → ConnectError → PermissionError`; the identical approved-network command passed. Two product defects were also corrected: stale process Provider values could override `.env`, and selection_required allowed unrelated IFC Type families.
- fix: Repository `.env` now overrides process Provider keys for the opt-in UAT. OperationDefinition now declares Prototype IFC classes and dimension paths; resolution filters by both before bounding candidates. Safe Provider errors remain redacted and classified.
- verification: Same-process RepairAPI reached L2; final IFC repair suite passed 388 with 1 skip; Provider compatibility suite passed 31; the approved-network four-case DeepSeek UAT contract-passed with Stage 1/Stage 2 totals 5/4.
- files_changed: scripts/ifc_repair/run_phase9_live_uat.py, src/text2ifc_ifc_repair/registry.py, src/text2ifc_ifc_repair/resolution_flow.py, src/text2ifc_ifc_repair/orchestrator.py, src/text2ifc_ifc_repair/api.py, related tests and validation docs.
