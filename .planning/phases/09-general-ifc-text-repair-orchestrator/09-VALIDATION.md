---
phase: 9
slug: general-ifc-text-repair-orchestrator
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-07-20
---

# Phase 9 - Validation Strategy

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest through the Python 3.12 project virtual environment |
| Config file | `pyproject.toml` |
| Quick run command | `.venv\Scripts\python -m pytest tests\ifc_repair\test_repair_intent.py tests\ifc_repair\test_repair_run_state.py -q` |
| Full suite command | `.venv\Scripts\python -m pytest tests\ifc_repair -q` |
| Estimated runtime | focused target under 30 seconds; full IFC repair suite under 5 minutes |

## Sampling Rate

- After each RED/GREEN/REFACTOR commit, run the plan's focused test file.
- After every plan, run all completed Phase 9 focused tests plus the directly
  affected Phase 7/8 regression files.
- After every wave, run the full `tests/ifc_repair` suite.
- Before verification, run the full suite, compileall, all new JSON Schema
  validation, privacy canaries, source/manifest hashes, and `git diff --check`.
- Maximum focused feedback latency: 30 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure behavior | Test type | Automated command | File exists | Status |
|---|---:|---:|---|---|---|---|---|---|---|
| 09-01-01 | 01 | 1 | PIPE-01, PIPE-03 | T-09-01 | Prompt injection and malformed intent cannot escape the exact public contract | schema/unit | `pytest tests/ifc_repair/test_repair_intent.py -q` | Wave 0 creates | pending |
| 09-01-02 | 01 | 1 | PIPE-03 | T-09-01, T-09-05 | Stage 1 receives only public bounded inputs and retains redacted attempts | unit | `pytest tests/ifc_repair/test_request_stage.py -q` | Wave 0 creates | pending |
| 09-02-01 | 02 | 2 | PIPE-01, PIPE-04 | T-09-02 | Run transitions are atomic, revision-bound, resumable, and tamper-evident | unit | `pytest tests/ifc_repair/test_repair_run_state.py -q` | Wave 0 creates | pending |
| 09-02-02 | 02 | 2 | PIPE-01, PIPE-04 | T-09-02, T-09-03 | Clarification accepts only current offered answers and never repeats immutable stages | unit | `pytest tests/ifc_repair/test_repair_clarification.py -q` | Wave 0 creates | pending |
| 09-03-01 | 03 | 3 | PIPE-03, PIPE-04 | T-09-03 | Every operation resolves before Stage 2; unresolved operations stop all application | integration | `pytest tests/ifc_repair/test_repair_resolution_flow.py -q` | Wave 0 creates | pending |
| 09-03-02 | 03 | 3 | PIPE-02, PIPE-03 | T-09-03 | Intent/operation cardinality, target, scope, hashes and evidence pointers cannot cross operations | unit/integration | `pytest tests/ifc_repair/test_general_changeset_stage.py -q` | Wave 0 creates | pending |
| 09-04-01 | 04 | 4 | PIPE-02, PIPE-04 | T-09-04 | Production facts use only request/surviving/bound-or-approved/policy authority | unit | `pytest tests/ifc_repair/test_production_evidence.py -q` | Wave 0 creates | pending |
| 09-04-02 | 04 | 4 | PIPE-02, PIPE-04 | T-09-03, T-09-04 | Unified application is atomic and Evaluation 0.2 alone promotes success IFC | integration | `pytest tests/ifc_repair/test_general_orchestrator.py -q` | Wave 0 creates | pending |
| 09-04-03 | 04 | 4 | PIPE-03, PIPE-04 | T-09-02, T-09-04, T-09-05 | Manifest/tamper/Gold canaries fail closed across both Agent stages and public bundle | adversarial | `pytest tests/ifc_repair/test_orchestrator_security.py -q` | Wave 0 creates | pending |
| 09-05-01 | 05 | 5 | PIPE-01, PIPE-04 | T-09-02, T-09-05 | Human, non-interactive, JSON and quiet modes render one API result without secret leakage | CLI | `pytest tests/ifc_repair/test_repair_cli.py -q` | Wave 0 creates | pending |
| 09-05-02 | 05 | 5 | PIPE-01..04 | T-09-01..05 | LargeBuilding exercises the real integration and honestly retains current L2 failure | real IFC/offline | `pytest tests/ifc_repair/test_phase9_large_building.py -q` | Wave 0 creates | pending |

## Wave 0 Requirements

Existing pytest, jsonschema, IfcOpenShell, `tmp_path`, fake/live Provider
fixtures, synthetic IFC builders, Phase 7 SQLite fixtures, Phase 8 Registry/
Evaluation fixtures, LargeBuilding, and secret-canary helpers cover all
infrastructure needs. Each TDD plan creates its focused test file during RED;
no dependency installation or external service is required.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Test instructions |
|---|---|---|---|
| Real DeepSeek two-stage orchestration UAT | PIPE-01, PIPE-03 | Requires live credentials/network and is additive evidence, not deterministic CI authority | Run the Phase 9 live command after `--check-config`; inspect redacted Stage 1/2 traces, target resolution, Evaluation 0.2, source hash, and manifest. Accept an honest L2 non-publishable result before Phase 10. |

## Validation Sign-Off

- [x] Every planned behavior has an automated focused command or a clearly
  isolated opt-in live UAT.
- [x] Sampling continuity has no three-task gap.
- [x] Existing infrastructure covers all Wave 0 needs.
- [x] No watch-mode commands are used.
- [x] Focused feedback target is under 30 seconds.
- [x] `nyquist_compliant: true` is set.

**Approval:** approved 2026-07-20
