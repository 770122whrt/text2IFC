---
phase: 08-l1-l2-evaluation-contract
audited: 2026-07-20
status: secured
threats_declared: 12
threats_mitigated: 12
threats_open: 0
---

# Phase 8 Security Verification

## Verdict

**SECURED.** All 12 threats declared by plans 08-01 through 08-04 have
implemented, wired, and adversarially tested mitigations. No open threat blocks
Phase 8 completion.

This audit covers the Evaluation 0.2 contract, L1/L2 evaluators, operation
policy Registry, benchmark-private boundary, public projection, workflow
terminal state, and the legacy Evaluation 0.1 compatibility entrypoint.

## Threat Verification

| Threat | Severity | Result | Verified mitigation |
|---|---|---|---|
| T-08-01A | high | MITIGATED | Closed five-state results and aggregate invariants reject `partial`, `not_evaluable`, and any other non-pass state at mandatory gates. Model construction and report parsing also downgrade contradictory success booleans. |
| T-08-01B | high | MITIGATED | Evaluation 0.2 is exact-versioned and Draft 2020-12 schema-backed; required hierarchy/evidence fields and `additionalProperties: false` reject malformed reports. |
| T-08-01C | medium | MITIGATED | Legacy 0.1 projects missing L2 as `not_evaluable` with `legacy_assurance_unavailable`; both complete and publishable success are forced false. |
| T-08-02A | high | MITIGATED | Production semantic evidence uses a closed source-kind allowlist, deterministic precedence, compatibility checks, and provenance; private/neighbor/name/LLM guesses cannot authorize a pass. |
| T-08-02B | high | MITIGATED | Authorized Material/Pset/quantity/classification evidence activates mandatory comparison; missing and mismatching values fail, while verified lack of authority is `not_required`. |
| T-08-02C | medium | MITIGATED | The operation Registry requires a versioned typed evaluation policy; generic dispatch tests exercise a future-family fixture through the common contract. |
| T-08-03A | high | MITIGATED | The evaluator reopens both IFCs and authorizes actual changes only through the intersection of Registry policy and declared ChangeSet scope; Applicator self-report is diagnostic, not authority. |
| T-08-03B | high | MITIGATED | Exact role cardinality, relationship endpoints, host/storey containment, duplicate-chain, extra-root, and deleted-root checks fail closed. |
| T-08-03C | medium | MITIGATED | Role/GlobalId-normalized measurements and versioned tolerances replace STEP ordering; adversarial geometry and representation-order fixtures are covered. |
| T-08-04A | critical | MITIGATED | Production and benchmark inputs are distinct types; Gold enters only after application. Public output is positively allowlisted and the complete Provider/public bundle is scanned for private IDs, paths, mappings, and semantic canaries. |
| T-08-04B | high | MITIGATED | Evaluation 0.2 alone derives terminal completion/publication. L1-pass/L2-fail and all early failure paths retain diagnostic evidence but remain non-publishable. |
| T-08-04C | medium | MITIGATED | Private mutation and application role mappings compare semantic/relationship equivalence across recreated GUIDs; exact authoring identity remains non-gating L3 evidence. |

## Boundary and Failure-Mode Checks

- Gold/private input is rejected at the production input boundary, before
  evaluation or Provider serialization.
- Public projection copies only named fields; it never performs a negative
  blacklist copy of the private report.
- Canary detection scans the finalized serialized bundle, not only an
  in-memory projection.
- Extraction, missing-IFC, malformed-report, unknown-evidence, and failed
  Provider paths preserve diagnostics while failing closed.
- The old callable comparator can no longer assert a successful repair without
  L2 assurance.

## Verification Evidence

Fresh audit command on 2026-07-20:

```text
.venv\Scripts\python -m pytest \
  tests\ifc_repair\test_evaluation_contract.py \
  tests\ifc_repair\test_evaluation_policy.py \
  tests\ifc_repair\test_l1_evaluator.py \
  tests\ifc_repair\test_benchmark_evaluation.py \
  tests\ifc_repair\test_phase8_large_building.py -q

144 passed in 18.03s
```

The broader completion evidence remains `210 passed in 156.08s` for
`tests/ifc_repair`, plus passing compileall, JSON Schema validation, and diff
checks. The goal verifier independently reports **11/11 must-haves verified**.

## Residual Design Notes

These are forward-looking hardening opportunities, not open Phase 8 threats:

- Phase 9 orchestration must populate production semantic evidence only from
  the authority classes accepted by this contract.
- Add a full two-operation semantic evaluator fixture when multiple operation
  families are enabled; current code and map-level regressions already isolate
  evidence by `operation_id`.
- L3 authoring exactness remains recorded and intentionally non-gating.

---

_Audited: 2026-07-20_  
_Auditor: Codex (GSD secure-phase workflow)_
