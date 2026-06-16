# Plan 04-06 Summary: Broader Classes, All-25 Audit, and Phase 6 Readiness

**Date:** 2026-06-16
**Status:** Complete

## What Changed

- Added Phase 4 acceptance coverage for extract-only product classes in real
  BIMNet files.
- Extended Draft loss records with optional `source_capability`.
- Updated extraction so `CLASS_CAPABILITY` losses include:
  - `source_item_class`
  - `source_capability`
  - `substitution: "none"`
- Wrote the Phase 4 architecture summary and Phase 6 readiness decision.

## Capability Decision

No new broad product class was promoted in Wave 6.

Reason:

- The IFC2X3 capability overlay already marks the common BIMNet architectural
  product classes as `generate`.
- The remaining product-class issue in the source set is not silent omission,
  but explicit handling for extract-only classes such as
  `IfcBuildingElementProxy` and `IfcFurnishingElement`.
- Generating proxy boxes for these classes would violate the Phase 4
  no-substitution rule.

## Quantitative Audit

All-25 BIMNet extraction accounting after Wave 6:

| Category | Source | Represented | Reported |
|---|---:|---:|---:|
| Entities | 5308 | 4444 | 864 |
| Relationships | 16926 | 15046 | 1880 |
| Properties | 18758 | 17607 | 1151 |
| Representations | 6382 | 4509 | 1873 |
| Materials | 2554 | 1533 | 1021 |
| Types | 1012 | 154 | 858 |
| Connections | 2263 | 2263 | 0 |

Total explicit losses: 5204.

Largest residual loss classes:

- `MAPPED_GEOMETRY`: 1031
- `MATERIAL_ASSOCIATION`: 1021
- `CLASS_CAPABILITY`: 864
- `TYPE_RELATIONSHIP`: 858
- `UNSUPPORTED_GEOMETRY`: 505
- `UNSUPPORTED_PROPERTY_VALUE`: 485
- `FACETED_BREP_GEOMETRY`: 314

## TDD Evidence

- RED `1cd3021`: extract-only product class losses lacked explicit metadata.
- GREEN `12226f0`: extractor and Draft schema record product-class loss
  metadata with no substitution.

## Verification

Commands run:

```powershell
python -m pytest tests\fidelity\test_phase4_acceptance.py -q
python scripts\bim_json_v2\generate_reference.py
python -m pytest tests\fidelity\test_phase4_acceptance.py tests\fidelity\test_complex_geometry.py tests\extractor -q
python scripts\ifc_pipeline_v2\audit_bimnet.py --write
python scripts\ifc_pipeline_v2\fidelity_inventory.py --all --check
python -m pytest tests\ifc_quality tests\agent tests\compiler -q
python -m compileall src scripts -q
python scripts\agent\scan_agent_artifacts.py --path dataset\processed\agent-demo\geometry-gate
python scripts\agent\run_geometry_gate_demo.py --case simple-room-fixed --check
python scripts\agent\run_geometry_gate_demo.py --case two-room-suite --check
python scripts\ifc_quality\check_generated_ifc.py --ifc dataset\processed\agent-demo\geometry-gate\simple-room-fixed\output.ifc --expectation dataset\processed\agent-demo\geometry-gate\simple-room-fixed\expected.json
python scripts\ifc_quality\check_generated_ifc.py --ifc dataset\processed\agent-demo\geometry-gate\two-room-suite\output.ifc --expectation dataset\processed\agent-demo\geometry-gate\two-room-suite\expected.json
python -m pytest tests\text2json\test_gold_set.py::test_triage_extraction_audit_preserves_counts_and_split_join -q
python -m pytest tests -q --tb=short
```

Observed results:

- Phase 4 acceptance focused test: 1 passed.
- Phase 4 acceptance + complex geometry + extractor regression: 12 passed.
- BIM JSON references regenerated with no tracked drift.
- BIMNet extraction audit wrote successfully for 25 files.
- Fidelity inventory check reported 25 records and no issues.
- IFC quality + Agent + compiler regression: 89 passed.
- compileall passed.
- Geometry-gate artifact secret scan reported 0 findings across 16 files.
- `simple-room-fixed` and `two-room-suite` demo gates both passed.
- Direct generated IFC checks for both geometry-gate outputs passed with no
  issues.
- Full repository regression: 337 passed.

## Phase 6 Readiness Decision

Phase 6 may start, with a strict supported-scope boundary:

- Formal model targets must be valid BIM JSON 2.0 supported-scope documents.
- Draft/loss sidecars must remain linked and unscored as Formal predictions.
- Generated IFC gates must be deployment blockers.
- Complex source geometry recovery remains out of scope until a later exact
  mapped/BRep/tessellation representation is designed and verified.

## Final Review Notes

- Code review: no high-severity issue found in the Wave 6 code path. The
  implementation only adds explicit metadata to existing loss records and
  does not broaden generation claims.
- Security review: no token, provider URL, header, or live credential was
  written to artifacts. Geometry-gate artifact scan found 0 findings.
- Requirement coverage: GEN-01/GEN-02/GEO-03/GEO-04/GEO-05/IFC-06 are covered
  by generated IFC gates, all-25 audit accounting, no-substitution loss
  records, and the Phase 6 readiness report.
