---
phase: 9
slug: general-ifc-text-repair-orchestrator
status: verified
threats_open: 0
asvs_level: 1
created: 2026-07-20
---

# Phase 9 — Security

> Per-phase verification of the threat models frozen in Plans 09-01 through
> 09-05. This audit verifies registered mitigations; it does not expand scope
> into a new general security review.

## Trust Boundaries

| Boundary | Description | Data crossing |
|---|---|---|
| Caller → RepairAPI | Untrusted IFC path and natural-language request enter one public facade | IFC2X3 bytes, request text |
| RepairAPI → Provider | Only versioned public prompt/spec/context contracts may leave the deterministic process | Bounded RepairIntent/ChangeSet requests and redacted attempts |
| Provider → deterministic core | Agent JSON is untrusted until schema, registry, fingerprint, target and evidence binding pass | RepairIntent and unified ChangeSet JSON |
| RunStore → filesystem | Concurrent/resumed runs persist immutable, hash-bound state and terminal evidence | State, transitions, SQLite index, prepared/public bundles |
| Evaluator → publication | Evaluation 0.2 is the sole authority for exposing a successful IFC | Public L1/L2 result, manifest, IFC or diagnostic candidate |
| RepairAPI → CLI | Human/JSON/quiet renderers expose only the compact public RunResult | Status, clarification fields, safe relative artifact references |

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation and verified evidence | Status |
|---|---|---|---|---|---|
| T-09-01A | Information disclosure | Request understanding | mitigate | Public-only `RepairAPI`/request-stage signatures, private canary scans, and redacted attempt artifacts; covered by `test_request_stage.py` and `test_orchestrator_security.py`. | closed |
| T-09-01B | Tampering | RepairIntent | mitigate | Draft 2020-12 exact schema, Registry operation allowlist, prohibited resolved identity fields, and source provenance validation in `repair_intent.py`; covered by `test_repair_intent.py`. | closed |
| T-09-01C | Denial of service | Provider/parser | mitigate | Text/JSON/count/token limits, finite correction attempts, and bounded evidence in `request_stage.py`/`provider_stage.py`; covered by request/provider-stage tests. | closed |
| T-09-02A | Tampering/replay | Run continuation | mitigate | Source/request/stage SHA-256 bindings, monotonic transition chain, clarification ID/version binding, answer schema, and artifact hash verification in `run_store.py`. | closed |
| T-09-02B | Race condition | Concurrent continuation | mitigate | OS-managed per-run lock, expected-version CAS, UUID-qualified attempt artifacts, and a two-thread winner/loser regression test; the losing answer cannot overwrite winner bindings. | closed |
| T-09-02C | Path traversal | Run artifacts | mitigate | Safe generated IDs, resolved-root containment, symlink/junction/reparse rejection, create-new semantics, and source revalidation in `run_store.py`; adversarial tests cover traversal and reparse paths. | closed |
| T-09-03A | Tampering | Stage 2 binding | mitigate | One-to-one operation, target, scope, context and JSON-pointer validation before Audit in `provider_stage.py` and `resolution_flow.py`; covered by `test_general_changeset_stage.py`. | closed |
| T-09-03B | Replay | Index/context | mitigate | Exact source/index/extractor/schema/model fingerprints are checked at repository open and run transitions; bound artifacts are rehashed on every load/resume. | closed |
| T-09-03C | Integrity loss | Unified ChangeSet | mitigate | Operation cardinality and ID-set equality are validated; Audit/application is one all-or-nothing transaction and subset application cannot be published. | closed |
| T-09-04A | Information disclosure | Evaluation/publication | mitigate | Production inputs cannot represent benchmark Gold, source kinds use a positive allowlist, and the whole public bundle is canary-scanned in `production_evidence.py`, `benchmark_evaluation.py`, and `run_artifacts.py`. | closed |
| T-09-04B | Elevation of privilege | Success authority | mitigate | Evaluation 0.2 `successful_artifact_publishable` alone controls success; hidden prepared bundles and a durable recovery journal bind promotion to terminal state. Four crash points are fault-injected. | closed |
| T-09-04C | Spoofing | L2 semantic authority | mitigate | Closed precedence permits only explicit request, surviving bound facts, explicit/formal Prototype authority, and deterministic policy. Type Prototype lookup admits inherited type facts only and fails on conflicts. | closed |
| T-09-04D | Tampering | IFC publication | mitigate | Candidate containment, IFC2X3 reopen, expected SHA-256, content manifest, hidden bundle promotion, terminal read verification, and idempotent journal recovery prevent diagnostic/success swaps. | closed |
| T-09-05A | Information disclosure | CLI | mitigate | Typed compact renderers, redacted errors, safe relative artifact references, bounded stdout and JSON/quiet tests in `cli.py`/`test_repair_cli.py`. | closed |
| T-09-05B | Tampering | Interactive clarification | mitigate | EOF/cancel are explicit terminal answers; candidate tokens must be from the stored set; non-interactive ambiguity remains `clarification_required`. | closed |
| T-09-05C | Repudiation | Live UAT evidence | mitigate | Live execution is opt-in/config-gated and separated from deterministic acceptance. The recorded DeepSeek attempt truthfully remains `provider_failed`, Stage 2 calls `0`, and publishable `false`. | closed |

## Accepted Risks Log

No accepted risks. Every registered Phase 9 threat has an implemented and
verified mitigation.

## Verification Evidence

- Security-focused suite: `145 passed, 1 skipped` on 2026-07-20.
- Full IFC repair suite: `375 passed, 1 skipped`.
- Code review iteration 4: `clean`, zero findings.
- The single skip is the existing platform-permission symlink case; Windows
  junction/reparse containment has a non-skipped test.
- `git diff --check` passed for Phase 9 changes.

## Security Audit Trail

| Audit date | Threats total | Closed | Open | Run by |
|---|---:|---:|---:|---|
| 2026-07-20 | 16 | 16 | 0 | Codex primary agent (inline fallback after auditor quota failure) |

## Sign-Off

- [x] All threats have a disposition.
- [x] Accepted risks are documented (none).
- [x] `threats_open: 0` confirmed.
- [x] `status: verified` set in frontmatter.

**Approval:** verified 2026-07-20
