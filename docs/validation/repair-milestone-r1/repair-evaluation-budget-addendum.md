# Repair Milestone R1 Evaluation Budget Addendum

Status: authorized for R1 execution on 2026-08-31.

This addendum separates correctness admission from performance observation for the frozen R1 12-case genuine execution. It does not change production/default Phase 12 evaluator settings, Provider prompts, property retrieval, Stage 1.5, admissibility, Stage 2, Proof criteria, or testcase semantics.

## Blocking correctness contract

- Evaluation mode: `accelerated`.
- Correctness deadline: `600 seconds` per case.
- Aggregate concurrent RSS limit: `4 GiB`.
- A real deadline, worker, or simultaneous-stage RSS failure remains fail-closed.
- Complete IFC apply, independent reopen, validation/diff, L0, L1, L2, global preservation, source immutability, no fallback, and private-evidence isolation remain blocking.
- The RSS measurement is the maximum of each actual concurrency phase. Historical worker peaks from validation must not be added to a later non-overlapping parent-only diff phase.

## Nonblocking performance observation

- `180 seconds` remains the focused-feedback performance SLO.
- `performance_slo_met=false` is retained as performance evidence but does not convert an otherwise complete R1 correctness result into failure.
- The production/default Phase 12 policy remains unchanged at its existing `180 seconds`; this R1 execution override is explicit and runner-scoped.

## Evidence requirements

Every R1 case result must retain the configured deadline, RSS limit, mode, cache mode, evaluation wall time, performance SLO, whether that SLO was met, and that the SLO is nonblocking. The R1 runner stops on any failed frozen case contract.
