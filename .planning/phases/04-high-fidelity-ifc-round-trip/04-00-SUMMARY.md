# Plan 04-00 Summary: Generated IFC Correctness Gate

**Date:** 2026-06-15
**Status:** Complete

## What Changed

- Added `text2ifc_quality.generated_ifc.check_generated_ifc`, an IfcOpenShell
  quality gate that maps IFC products back to BIM JSON ids through
  `Pset_text2IFCIdentity.BimJsonId` and checks wall world-space orientation and
  bounding boxes.
- Added `scripts/ifc_quality/check_generated_ifc.py` for machine-readable CLI
  diagnostics.
- Added `scripts/agent/run_geometry_gate_demo.py`, a deterministic geometry
  gate demo runner for:
  - `simple-room-fixed`
  - `two-room-suite`
- Wrote durable audit artifacts under
  `dataset/processed/agent-demo/geometry-gate/`.
- Added `prompts/agent/mimo-bim-json-v3.md` and recorded the geometry prompt
  iteration.

## Key Learning

Reopenable IFC is not enough. The previous live simple-room artifact contained
four walls and reopened successfully, but east/west walls used the same local
direction as south/north walls. The root issue was semantic geometry: the model
treated wall placement as a start/corner point, while the IFC rectangle profile
uses a center-origin solid.

## TDD Evidence

- RED `768596d`: known disconnected simple-room IFC must be rejected.
- GREEN `4b25802`: generated IFC geometry checker.
- RED `fcf276b`: quality checker must have a scriptable CLI.
- GREEN `d2af026`: generated IFC gate CLI.
- RED `cc600b5`: geometry gate demo must write audit artifacts.
- GREEN `9ab2275`: simple-room-fixed demo.
- RED `a796c90`: two-room-suite demo.
- GREEN `d96fc00`: two-room-suite implementation.
- RED `11a8dbe`: geometry-aware Mimo prompt contract.
- GREEN `b55cf63`: Mimo prompt v3.

## Verification

Commands run:

```powershell
python -m pytest tests\ifc_quality tests\agent\test_geometry_gate_demo.py -q
python -m pytest tests\agent\test_mimo_prompt_assets.py -q
python scripts\agent\run_geometry_gate_demo.py --case simple-room-fixed --check
python scripts\agent\run_geometry_gate_demo.py --case two-room-suite --check
python scripts\agent\scan_agent_artifacts.py --path dataset\processed\agent-demo\geometry-gate
python -m compileall src scripts -q
```

Observed results:

- Focused quality/demo tests: 4 passed.
- Prompt asset tests: 7 passed.
- `simple-room-fixed`: parse, BIM JSON validation, geometry, attributes,
  relationships, IFC structure, and compile/reopen metrics all passed.
- `two-room-suite`: parse, BIM JSON validation, geometry, attributes,
  relationships, IFC structure, and compile/reopen metrics all passed.
- Artifact secret scan: 0 findings across 16 scanned files.
- `compileall`: passed.

## Artifacts

- `dataset/processed/agent-demo/geometry-gate/simple-room-fixed/output.ifc`
- `dataset/processed/agent-demo/geometry-gate/two-room-suite/output.ifc`
- Each case includes `input.txt`, `prompt-used.md`, `raw-response.txt`,
  `candidate.json`, `expected.json`, `diagnostics.json`, `metrics.json`,
  `report.md`, and `output.ifc`.

## Remaining Phase 4 Work

- Expand the checker beyond wall bbox/orientation into opening-host fit,
  containment, richer relationship checks, and attribute/property scoring.
- Proceed to Wave 1 fidelity inventory and metric harness for source IFC
  round-trip work.
- Use prompt v3 for future live-provider geometry repair experiments without
  recording secrets.
