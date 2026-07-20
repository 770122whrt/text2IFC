---
phase: 09-general-ifc-text-repair-orchestrator
verified: 2026-07-20T02:20:00Z
status: passed
score: 12/12 requirements verified
requirements_verified:
  - PIPE-01
  - PIPE-02
  - PIPE-03
  - PIPE-04
human_verification_required: false
---

# Phase 9: General IFC + Text Repair Orchestrator Verification

**Phase goal:** Accept a caller-owned IFC2X3 file plus natural-language repair
text, persist a resumable two-Agent run, resolve targets deterministically,
compile and apply one unified ChangeSet, and publish an IFC only when public
Evaluation 0.2 authorizes it.

**Verdict:** passed. The deterministic product path, clarification lifecycle,
production semantic authority, terminal publication protocol, API/CLI adapters,
and evidence contracts are implemented and exercised. The real DeepSeek UAT
ended honestly at a structured Stage 1 Provider failure; this satisfies the
approved opt-in failure branch but is not evidence of a successful two-stage
live repair.

## Goal Achievement

| # | Observable requirement | Status | Evidence |
|---:|---|---|---|
| 1 | One public Python API and CLI start from a caller IFC path plus text without benchmark IDs/private original and preserve source bytes. | VERIFIED | `api.py`, `cli.py`, `scripts/ifc_repair/repair.py`; `test_phase9_offline_e2e.py` verifies caller SHA-256 and public run output. |
| 2 | Stage 1 produces an exact-versioned, Registry-valid RepairIntent with bounded public evidence. | VERIFIED | RepairIntent schema/model/prompt plus `request_stage.py`; contract and correction tests in `test_repair_intent.py` and `test_request_stage.py`. |
| 3 | Phase 7 SQLite resolution and bounded context execute before Stage 2; every unresolved/failure state blocks Stage 2/application. | VERIFIED | `resolution_flow.py` and `api.py`; zero-call matrix in `test_orchestrator_resolution.py` and adversarial resolution tests. |
| 4 | Clarification is persisted, version-bound, interactive/resumable, and supports candidate selection, natural-language detail, Prototype authorization and cancel/EOF. | VERIFIED | Run schemas/store/API/CLI; real two-round `add_detail`, stale answer, candidate, cancel, and two-thread CAS tests. |
| 5 | Stage 2 receives only resolved public authority and returns one fully bound unified ChangeSet. | VERIFIED | `provider_stage.py`, ChangeSet v0.2 prompt and binding validation; target/scope/pointer/hash/cardinality negatives in `test_general_changeset_stage.py`. |
| 6 | Audit/application is one all-or-nothing Registry transaction; source remains unchanged and no subset becomes a successful output. | VERIFIED | `orchestrator.py`, `audit.py`, `apply.py`; multi-operation rollback test records evaluation call count zero and no success artifact. |
| 7 | Production L2 facts use closed per-operation authority: request, surviving target/host/type, formal or explicit Prototype, deterministic policy. | VERIFIED | `production_evidence.py`; precedence, cross-operation, prohibited inference, explicit product/Type Prototype, inherited-Type-only and conflict tests. |
| 8 | Private original/Gold/mutation inputs cannot enter production generation or public artifacts. | VERIFIED | Public constructor signatures omit those inputs; type-separated benchmark adapter, positive source allowlist and whole-bundle canary tests. |
| 9 | Every terminal run has public Evaluation 0.2; only a complete L1+L2 pass exposes a successful IFC reference. | VERIFIED | Terminal matrix and security tests; durable hidden-bundle publication is forced by `RepairAPI` and cannot be disabled. |
| 10 | Run lifecycle is immutable, resumable, tamper-evident and crash-recoverable. | VERIFIED | `run_store.py` transition/hash chain, safe paths, OS lock, unique attempts and publication journal; four fault-injection crash windows recover idempotently. |
| 11 | CLI is a thin adapter over the same API and supports human, interactive, non-interactive, JSON and quiet modes with stable exit classes. | VERIFIED | `cli.py` delegates start/continue/read; `test_repair_cli.py` covers rendering, stdin, stdout/stderr, compact envelope and exit mapping. |
| 12 | Acceptance is offline-first with a configuration-checked real DeepSeek route that preserves truthful failure semantics. | VERIFIED | Offline and LargeBuilding tests use controlled Provider calls; live evidence records Stage 1 `2`, Stage 2 `0`, terminal `provider_failed`, publishable `false`, no successful IFC. |

**Score:** 12/12 requirements verified.

## Required Artifacts

| Artifact group | Status | Verification |
|---|---|---|
| RepairIntent, clarification, run-state and result schemas | VERIFIED | Seven `ifc-repair-*.schema.json` files passed Draft 2020-12 meta-validation. |
| Stage 1 and Stage 2 prompts/registry entries | VERIFIED | Versioned prompt fingerprints are recorded; Provider correction and raw-output paths are tested. |
| `RepairAPI`, `RepairOrchestrator`, CLI and entry scripts | VERIFIED | Wired through the real SQLite index, resolver, Provider stages, Audit/apply/evaluation and RunStore. |
| Production evidence and Evaluation 0.2 publication | VERIFIED | Closed semantic authority and truth-table publication tests pass. |
| Immutable terminal bundle/manifest | VERIFIED | Content hashes are verified on read; hidden prepared bundle and journal recover every injected crash point. |
| Offline, LargeBuilding and live evidence | VERIFIED | Validation report preserves deterministic success/non-success separately from the real Provider failure. |

## Key Link Verification

| From | To | Via | Status |
|---|---|---|---|
| `RepairAPI.start` | Phase 7 index/resolution | `build_ifc_index` + `SQLiteIndexRepository` + `RepairOrchestrator.start` | WIRED |
| RepairIntent | Stage 2 | fingerprint-bound `ResolutionBatch.operations` passed to `generate_bound_changeset` | WIRED |
| Unified ChangeSet | deterministic IFC compilation | one `apply_changeset` transaction after complete Audit | WIRED |
| Resolution authority | production L2 | `build_production_evidence` with per-operation records and explicit/formal Prototype contracts | WIRED |
| Evaluation 0.2 | public IFC | `successful_artifact_publishable` → prepared bundle → `RunStore.commit_terminal_publication` | WIRED |
| CLI | Python behavior authority | only `RepairAPI.start`, `continue_with_answer`, and `read_result` | WIRED |

## Requirements Coverage

| Requirement | Status | Evidence summary |
|---|---|---|
| PIPE-01 | SATISFIED | One CLI/API command creates a unique run and returns terminal/clarification result plus evidence directory. |
| PIPE-02 | SATISFIED | Successful deterministic run publishes the semantic ChangeSet and compiled IFC2X3 under a content-bound terminal bundle. |
| PIPE-03 | SATISFIED | Provider inputs are bounded public request/spec/context/contracts; Gold/private canaries are rejected and absent. |
| PIPE-04 | SATISFIED | Ambiguous, unsupported, Provider-invalid, Audit/application/L1/L2 failures cannot expose a successful IFC; crash/race paths fail closed. |

No orphaned Phase 9 requirements were found. `PIPE-01..04` are mapped to the
five Phase 9 plans and are all satisfied.

## Verification Commands and Results

- Full repair suite: `375 passed, 1 skipped in 120.21s`.
- Security/threat-focused suite: `145 passed, 1 skipped in 23.95s`.
- Latest four changed modules: `60 passed, 1 skipped`.
- Concurrent clarification race repeated five times: all passed.
- JSON Schema meta-validation: `7 schemas ok`.
- `python -m compileall -q src/text2ifc_ifc_repair scripts/ifc_repair`: passed.
- Phase 9 scoped `git diff --check`: passed.
- Code review iteration 4: clean, zero findings.
- Security register: 16/16 threats closed, 0 open.

The skip is the existing platform-permission symlink test. A non-skipped
Windows junction/reparse test verifies the same containment boundary.

## Live UAT Truth

The DeepSeek configuration preflight was ready at the retained 65,536 input
and completion guards. The live attempt made two Stage 1 calls. The first
response omitted a required opening parameter; the correction response failed
the deterministic model-fingerprint binding. Therefore Stage 2, application,
and L1/L2 evaluation were not reached. The retained terminal result is
`provider_failed`, complete/publishable are false, and no successful IFC exists.

This is accepted by Requirement 12's explicit structured Provider-failure
branch. It does not prove live two-stage success; a later live retry may add UAT
evidence without changing Phase 9 deterministic acceptance.

## Deferred Boundaries

- Phase 10 owns Window L2 authoring closure and a real L1+L2 live pass.
- Phases 11/12 own Opening, Door, Beam and Column operation definitions.
- Phase 13 owns vector retrieval and the 128k experiment; Phase 9 remains 64k.
- L3 identity exactness, curved/free-form walls, and automatic similarity-based
  Prototype authorization remain out of scope.

No Phase 9 implementation or verification gap remains.

---

_Verified: 2026-07-20T02:20:00Z_
_Verifier: Codex primary agent (inline fallback after verifier quota failure)_
