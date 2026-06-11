---
phase: 02
slug: minimum-bim-json-to-ifc2x3-compiler
status: verified
requirements_verified: 8
requirements_total: 8
automated_tests: 142
gaps: 0
verified: 2026-06-11
---

# Phase 2 Validation

## Validation Principle

Every externally observable compiler behavior began with a failing test.
Artifact requirements inspect serialized and reopened IFC rather than
compiler-side bookkeeping.

## Plan Gates

| Plan | Gate | Result |
|---|---|---|
| 02-01 | Compiler boundary, hierarchy, containment, identity, atomic output | passed |
| 02-02 | Nine-family counts, placements, and dimensions within 1 mm | passed |
| 02-03 | Common booleans and exact predefined-type recovery | passed |
| 02-04 | CLI, positive/negative IFC validation, complete acceptance | passed |

Review added RED-GREEN coverage for same-class verifier diagnostics,
input/output path conflicts, long-element placement overlap, and non-finite
JSON numbers.

## Requirement Coverage

| Requirement | Automated evidence |
|---|---|
| IFC-01 | Complete fixture writes IFC2X3 and reopens with IfcOpenShell |
| IFC-02 | Project/site/building/storey hierarchy and containment assertions |
| IFC-03 | Parameterized exact counts for all nine supported families |
| IFC-04 | Reopened dimensions recover within 1 mm |
| IFC-05 | Reopened psets and enum-compatible attributes preserve values |
| VER-01 | Recorded RED commits precede every implementation wave |
| VER-02 | In-memory schema and reopened schema plus EXPRESS checks |
| VER-03 | Compiler and full repository commands are repeatable |

## Final Commands

```powershell
python -m pytest tests/compiler -q
python -m pytest tests -q
python scripts/bim_json/generate_reference.py --check
python -m compileall -q src scripts
```

## Final Result

All 8 requirements have automated evidence. The full repository suite reports
`142 passed`; no Nyquist validation gap remains.
