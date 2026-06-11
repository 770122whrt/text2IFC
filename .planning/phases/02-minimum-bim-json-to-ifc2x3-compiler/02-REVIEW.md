---
phase: 02
phase_name: minimum-bim-json-to-ifc2x3-compiler
status: clean
depth: deep
files_reviewed: 16
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
resolved_findings: 4
reviewed: 2026-06-11
---

# Phase 2 Code Review

## Result

No open critical, warning, or informational findings remain.

## Resolved Findings

### WR-02-01: Same-class verifier errors could be deduplicated

Normalized records originally identified an entity only by IFC class. Two
invalid roofs with the same attribute could collapse into one diagnostic.
RED commit `69e8544` proves the loss; GREEN commit `d9a322b` includes GlobalId
or STEP id in the stable entity identity.

### WR-02-02: Input and output could resolve to the same path

The CLI could overwrite its JSON input after successful compilation. RED
commit `69e8544` adds a source-preservation case; `d9a322b` returns
`PATH_CONFLICT` with exit 2 before compilation.

### WR-02-03: Fixed placement stride could overlap long elements

A fixed ten-metre stride was insufficient for elements longer than ten metres.
RED commit `69e8544` adds a long-wall case; `d9a322b` uses cumulative extents
plus a one-metre gap.

### WR-02-04: Non-finite JSON numbers could reach IfcOpenShell

Python's default decoder accepts non-standard `NaN`/`Infinity`, and finite
syntax such as `1e400` becomes infinity. RED commit `3d83a5b` covers public API
and both CLIs; GREEN commit `756c3f7` adds strict parsing and recursive finite
number validation.

## Scope

- Contract-to-compiler boundary and atomic output
- IFC2X3 hierarchy, containment, identity, geometry, and properties
- Reopened schema/EXPRESS validation and normalized diagnostics
- File CLI limits, path behavior, and machine-readable envelopes
- Complete fixture acceptance and all compiler tests

## Evidence

- `python -m pytest tests -q` produced `142 passed`.
- `python scripts/bim_json/generate_reference.py --check` passed.
- `python -m compileall -q src scripts` passed.
- `git diff --check` passed.

## Residual Risk

Exact placements, openings, materials, and topology are explicitly deferred to
Phase 4. Deployment request quotas and domain-specific maximum dimensions
remain Phase 6 concerns.
