# Phase 4: High-fidelity IFC Round Trip - Validation Strategy

**Created:** 2026-06-15

## Validation Goal

Phase 4 validation must prove that generated IFC is not only reopenable, but
spatially and semantically correct for the supported scope. It must also prove
that high-fidelity source facts are either preserved accurately or reported as
losses.

## Wave 0 Checks

For each generated demo case:

- Parse provider output as one JSON object.
- Validate BIM JSON 2.0 with `validate_v2_document`.
- Compile to IFC2X3.
- Reopen with IfcOpenShell.
- Check project/site/building/storey/space hierarchy.
- Check product containment and aggregation.
- Check wall count, wall orientation, wall enclosure, and wall thickness.
- Check opening host relationship and opening geometry fit.
- Check door/window dimensions and placement.
- Check selected attributes and property facts.
- Scan artifacts for secrets.
- Write machine-readable metrics and markdown report.

## Fidelity Checks

For source IFC round-trip work:

- Count source materials, material layers, type definitions, topology
  relationships, representation kinds, mapped geometry, BRep, tessellation,
  and product classes.
- Classify each fact as preserved, generated, reported loss, or deferred.
- For generated support, compare reopened IFC to expected source facts.
- For unsupported support, ensure loss accounting balances with represented
  and omitted facts.

## Metrics

- `parse_valid_rate`
- `bim_json_valid_rate`
- `compile_success_rate`
- `reopen_success_rate`
- `geometry_gate_pass_rate`
- `attribute_accuracy`
- `relationship_accuracy`
- `ifc_structure_pass_rate`
- `loss_accounting_balance_rate`
- `repair_iteration_count`
- `secret_scan_findings`

## Required Verification Commands

Wave-specific plans may refine these commands, but final Phase 4 verification
must include:

```powershell
python -m pytest tests/ifc_quality tests/agent tests/compiler -q
python scripts/agent/run_geometry_gate_demo.py --case simple-room-fixed --check
python scripts/agent/run_geometry_gate_demo.py --case two-room-suite --check
python scripts/ifc_quality/check_generated_ifc.py dataset/processed/agent-demo/geometry-gate/simple-room-fixed/output.ifc --expect dataset/processed/agent-demo/geometry-gate/simple-room-fixed/expected.json
python scripts/ifc_quality/check_generated_ifc.py dataset/processed/agent-demo/geometry-gate/two-room-suite/output.ifc --expect dataset/processed/agent-demo/geometry-gate/two-room-suite/expected.json
python scripts/agent/scan_agent_artifacts.py --path dataset/processed/agent-demo/geometry-gate
python -m compileall src scripts -q
```

## Failure Policy

- Invalid JSON, invalid BIM JSON, failed compile, failed reopen, geometry gate
  failure, relationship failure, attribute mismatch, or secret finding blocks
  Wave 0 completion.
- Unsupported high-fidelity source facts do not block if they are explicitly
  reported as losses and excluded from formal generation claims.
- A live provider failure does not block deterministic tests, but it must be
  recorded with redacted diagnostics when used as evidence.

---

*Phase: 04-high-fidelity-ifc-round-trip*
