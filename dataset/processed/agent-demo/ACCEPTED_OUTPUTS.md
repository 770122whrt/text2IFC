# Accepted IFC Outputs

This file is the human-review entry point for retained IFC examples. IFC files
elsewhere under `agent-demo` may be deterministic fixtures or historical phase
evidence and are not implicitly accepted deliverables.

## Easy two-storey building

- IFC: `phase6.5-easy-accepted/two-storey-final-712.ifc`
- Report: `phase6.5-easy-accepted/report.md`
- Scope: retained real-provider Easy run accepted by deterministic checks and
  subsequent human review. The original 163-file live trace was compacted to
  the eight acceptance artifacts required for review and provenance.

## Phase 6.4 routing-loop baseline

- IFC: `phase6.4-authoritative-gate-live-deepseek-final-2/two-storey-residential/two-storey-712.ifc`
- Report: `phase6.4-authoritative-gate-live-deepseek-final-2/two-storey-residential/report.md`
- Scope: retained accepted workflow baseline using the user's review filename.

## Medium two-storey L-shaped building

- IFC: `phase6.5-medium-100mm-gap-fix/output713 -success.ifc`
- Candidate: `phase6.5-medium-100mm-gap-fix/candidate.json`
- Repair manifest: `phase6.5-medium-100mm-gap-fix/repair-manifest.json`
- Verification: `phase6.5-medium-100mm-gap-fix/verification.json`
- Scope: human-approved Medium artifact after the bounded 100 mm perimeter-gap
  repair.

## Cleanup boundary

- `cleanup-report.json` records the removed local debug directories.
- Git-tracked test fixtures and phase evidence are retained even when they
  represent negative cases because repository tests and planning documents may
  depend on them.
- The repository-root terminal record is preserved and is outside this output
  cleanup boundary.
