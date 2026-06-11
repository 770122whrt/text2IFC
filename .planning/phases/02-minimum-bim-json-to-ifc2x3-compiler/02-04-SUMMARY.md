---
phase: 02-minimum-bim-json-to-ifc2x3-compiler
plan: 04
subsystem: compiler-cli-and-acceptance
tags: [cli, ifc-validation, acceptance, tdd, documentation]
requires:
  - phase-02-geometry
  - phase-02-properties
provides:
  - Bounded file-oriented JSON-to-IFC CLI
  - Stable positive and negative IFC verifier evidence
  - Complete all-requirement fixture acceptance
  - Canonical compiler architecture documentation
affects:
  - phase-03-text-to-json-baseline
  - phase-06-deployment
tech-stack:
  added: []
  patterns:
    - CLI emits one deterministic JSON envelope
    - Reopened temporary STEP receives full schema and EXPRESS validation
key-files:
  created:
    - scripts/bim_json/compile_ifc.py
    - tests/compiler/test_complete_compilation.py
    - tests/compiler/test_ifc_verification.py
  modified:
    - src/text2ifc_compiler/compiler.py
    - src/text2ifc_compiler/verification.py
    - docs/architecture/text2ifc-overview.md
key-decisions:
  - "CLI uses positional input JSON and output IFC paths."
  - "In-memory validation checks schema; reopened temporary output adds EXPRESS rules."
  - "Output filesystem failures return IFC_OUTPUT_ERROR instead of tracebacks."
patterns-established:
  - "Exit 0 is success, 1 is contract/compiler failure, and 2 is input/usage failure."
requirements-completed: [IFC-01, IFC-02, IFC-03, IFC-04, IFC-05, VER-01, VER-02, VER-03]
duration: 9min
completed: 2026-06-11
---

# Phase 2 Plan 04: CLI and Complete Acceptance Summary

**The canonical file CLI now runs the complete validated BIM-JSON-to-IFC2X3
path with stable diagnostics, negative verifier proof, and atomic output.**

## Performance

- **Duration:** 9 minutes
- **Tasks:** 2 planned TDD tasks plus one discovered output-error case
- **Focused acceptance tests:** 7
- **Compiler tests:** 35
- **Repository tests:** 132

## Accomplishments

- Added the bounded UTF-8 `compile_ifc.py input.json output.ifc` command.
- Added stable JSON success, contract-error, malformed-input, oversized-input,
  usage-error, IFC-error, and output-error envelopes.
- Proved the verifier detects a deliberately invalid raw IFC2X3 roof.
- Added one complete-fixture test covering every Phase 2 requirement.
- Documented `text2ifc_compiler` as canonical and the old round-trip script as
  legacy research code.
- Kept the compiler suite under its 60-second target.

## Task Commits

1. **RED: CLI, negative verifier, and complete acceptance** - `31002e8`
2. **RED follow-up: Output path failure** - `e63ca4f`
3. **GREEN: Verified compiler CLI and documentation** - `fb7909c`
4. **REFACTOR:** Split validation cost into in-memory schema checking and full
   reopened schema plus EXPRESS checking.

## Test Evidence

- Initial RED: focused tests produced `4 failed, 2 passed`; the already-built
  verifier and complete acceptance passed while CLI behavior failed.
- Discovered RED: missing output parent raised an unhandled
  `FileNotFoundError`.
- GREEN: focused tests produced `7 passed in 14.98s`.
- Compiler suite: `35 passed in 39.79s`.
- Regression: `132 passed in 66.00s`.
- Contract reference drift check passed.
- `python -m compileall -q src scripts` and `git diff --check` passed.
- A real process smoke compiled the canonical complete fixture to
  `cli-smoke-final.ifc`, exited 0 in 4.7 seconds, and returned
  `success: true`.

## CLI Contract

- Exit 0: compiled and verified output.
- Exit 1: BIM JSON validation, IFC validation, or output write failure.
- Exit 2: usage, unreadable/malformed JSON, or input larger than 10 MiB.
- Output is one sorted JSON object with `success`, `output_path`, `schema`,
  `input_errors`, and `ifc_errors`.

## Deviations from Plan

One additional RED-GREEN case was added after real-process verification found
that a missing output parent produced a traceback. The compiler now returns
`IFC_OUTPUT_ERROR` and preserves machine-readable CLI behavior.

The implementation runs schema checks in memory and schema plus EXPRESS rules
after temporary-file reopen. This retains two verification gates while
removing duplicate expensive EXPRESS evaluation and keeping the suite within
the locked runtime limit.

## Issues Encountered

The pytest base temporary directory has restrictive Windows ACL behavior for
manually created child directories. A repository-root smoke output confirmed
the product CLI path completes normally; the generated artifact was removed
after verification.

## User Setup Required

None.

## Next Phase Readiness

Phase 2 implementation passed GSD verification, deep code review, security
review, and requirement coverage audit after four review-driven fixes.

## Post-Plan Review

- Verifier diagnostics now retain every same-class invalid entity.
- Input and output path conflicts fail without touching source data.
- Synthetic placement uses actual element extents rather than a fixed stride.
- Strict JSON loading and semantic validation reject non-finite numbers before
  IfcOpenShell receives them.
- Final repository regression: `142 passed`.

## Self-Check: PASSED

- RED and GREEN commits exist in order.
- Positive and negative verifier paths are covered.
- CLI error paths preserve existing output and avoid partial artifacts.
- Full compiler and repository suites pass.

---

*Phase: 02-minimum-bim-json-to-ifc2x3-compiler*
*Completed: 2026-06-11*
