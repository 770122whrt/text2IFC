# Phase 6.5 Deterministic Matrix

- evidence_class: `deterministic_fixture`
- case_count: `8`
- accepted_count: `3`
- false_accept_count: `0`

| Case | Outcome | Route | Issues | Preservation |
| --- | --- | --- | --- | --- |
| two-storey-accepted | accepted | accept | 0 -> 0 | 1.0 |
| three-storey-accepted | accepted | accept | 0 -> 0 | 1.0 |
| scoped-repair-accepted | accepted | accept | 1 -> 0 | 1.0 |
| draft-missing-fact | draft | draft_required | 1 -> 1 | 1.0 |
| scope-violation | blocked | blocked_failure | 1 -> 1 | 1.0 |
| stale-binding | blocked | blocked_failure | 1 -> 1 | 1.0 |
| unsupported-request | blocked | draft_required | 1 -> 1 | 1.0 |
| non-improving | blocked | blocked_failure | 1 -> 1 | 1.0 |
