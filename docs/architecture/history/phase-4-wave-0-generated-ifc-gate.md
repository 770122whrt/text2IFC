# Phase 4 Wave 0: Generated IFC Correctness Gate

Phase 4 Wave 0 adds an automated gate for the generated path:

```text
natural language -> BIM JSON 2.0 -> IFC2X3 -> reopened IFC checks
```

The gate exists because a generated IFC can reopen successfully while still
being spatially wrong. The first live simple-room run produced four wall
entities, but the east/west walls were not rotated and the room was visibly
disconnected. Wave 0 turns that lesson into a repeatable test.

## Cases

- `simple-room-fixed`: one 6m x 4m x 3m room, four enclosing walls, one south
  door, and one north window.
- `two-room-suite`: one 8m x 4m x 3m suite split into two rooms by a partition
  wall, with a partition door and an east window.

## Artifacts

Each case writes:

- `input.txt`
- `prompt-used.md`
- `raw-response.txt`
- `candidate.json`
- `expected.json`
- `diagnostics.json`
- `metrics.json`
- `report.md`
- `output.ifc`

Default output root:

```text
dataset/processed/agent-demo/geometry-gate/
```

## Commands

```powershell
python scripts/agent/run_geometry_gate_demo.py --case simple-room-fixed --check
python scripts/agent/run_geometry_gate_demo.py --case two-room-suite --check
python scripts/ifc_quality/check_generated_ifc.py --ifc dataset/processed/agent-demo/geometry-gate/simple-room-fixed/output.ifc --expectation dataset/processed/agent-demo/geometry-gate/simple-room-fixed/expected.json
python scripts/ifc_quality/check_generated_ifc.py --ifc dataset/processed/agent-demo/geometry-gate/two-room-suite/output.ifc --expectation dataset/processed/agent-demo/geometry-gate/two-room-suite/expected.json
python scripts/agent/scan_agent_artifacts.py --path dataset/processed/agent-demo/geometry-gate
```

## Current Metrics

Both generated cases currently pass:

- `parse_valid`
- `bim_json_valid`
- `geometry_pass`
- `attributes_pass`
- `relationships_pass`
- `ifc_structure_pass`
- `compile_reopen_success`

The checker currently focuses on product identity, wall world-space bounding
boxes, wall orientation, and room enclosure failure detection. Later Phase 4
waves should expand it to richer opening-host fit, containment, topology,
material, type, and complex-geometry fidelity.
