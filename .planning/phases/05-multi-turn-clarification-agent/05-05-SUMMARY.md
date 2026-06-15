# 05-05 Summary: Scripted Clarification Demo to IFC

**Completed:** 2026-06-15
**Plan:** `05-05-PLAN.md`
**Status:** Complete

## Objective

Run the first scripted Chinese multi-turn clarification demo and produce a real
IFC2X3 file.

## Commits

| Type | Commit | Description |
|---|---|---|
| RED | `b10a574` | Added failing scripted demo tests and CLI skeleton |
| GREEN | `5a812dd` | Implemented simple-room Agent demo, formal validation, IFC compilation, and artifact writing |

## Implemented

- `scripts/agent/run_clarification_demo.py`
- `tests/agent/test_clarification_demo.py`
- `dataset/processed/agent-demo/simple-room/`

## Demo Flow

Initial Chinese request:

```text
请帮我创建一个单层矩形房间，包含四面墙、一扇门和一扇窗。
```

The scripted Agent asks three Chinese questions in one turn:

- room length, width, and height;
- door host wall and position;
- window host wall, sill height, and size.

Scripted answers are merged into Agent state. The final candidate contains:

- `IfcProject`
- `IfcSite`
- `IfcBuilding`
- `IfcBuildingStorey`
- `IfcSpace`
- four `IfcWall` entities
- one `IfcDoor`
- one `IfcWindow`
- door and window `IfcOpeningElement` entities
- `IfcRelVoidsElement` and `IfcRelFillsElement` relationships

## Artifacts

| Artifact | Purpose |
|---|---|
| `dataset/processed/agent-demo/simple-room/transcript.json` | Agent/user turn transcript |
| `dataset/processed/agent-demo/simple-room/state.json` | Final Agent state |
| `dataset/processed/agent-demo/simple-room/candidate.json` | Formal BIM JSON 2.0 candidate |
| `dataset/processed/agent-demo/simple-room/diagnostics.json` | Validation and compile diagnostics |
| `dataset/processed/agent-demo/simple-room/metrics.json` | Turn, question, validation, and compile metrics |
| `dataset/processed/agent-demo/simple-room/report.md` | Human-readable run report |
| `dataset/processed/agent-demo/simple-room/output.ifc` | Final IFC2X3 acceptance artifact |

`output.ifc` is tracked through Git LFS.

## Verification

Focused RED verification:

```powershell
python -m pytest tests/agent/test_clarification_demo.py -q
```

Expected RED result:

- 2 failed
- failures were missing demo success, artifacts, validation, and IFC output.

Focused GREEN verification:

```powershell
python -m pytest tests/agent/test_clarification_demo.py -q
```

Result:

- 2 passed

Demo command:

```powershell
python scripts/agent/run_clarification_demo.py --check
```

Result:

- `{"success": true}`

Agent regression:

```powershell
python -m pytest tests/agent -q
```

Result:

- 28 passed

## Final Demo Metrics

```json
{
  "asked_question_count": 3,
  "compile_success": true,
  "final_status": "formal_ready",
  "schema_version": "text2ifc/agent-demo-metrics-v1",
  "turn_count": 5,
  "validation_status": "ok"
}
```

## Requirement Coverage

- **AGENT-01:** Demonstrated for the scripted simple-room path: natural
  language plus answers reaches valid formal BIM JSON 2.0.
- **AGENT-02:** Demonstrated with three Chinese clarification questions.
- **AGENT-03:** Demonstrated through transcript, state, accepted facts,
  diagnostics, and metrics artifacts.

## Security and Boundary Notes

- Failure mode test proves invalid candidates do not write or overwrite
  `output.ifc`.
- The demo compiles only after `validate_v2_document` reports no issues.
- Generated diagnostics use repository-relative artifact paths.
- Sensitive-pattern scan found no token or private provider endpoint in
  Agent source, tests, planning docs, or demo artifacts.

## Deviations

None.

## Next

Proceed to `05-06-PLAN.md`: final verification, security scan, code review,
requirement coverage, Phase 5 summary, ROADMAP/STATE completion, and push.
