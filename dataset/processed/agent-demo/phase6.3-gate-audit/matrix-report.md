# Phase 6.3 Matrix Report

- Case count: `4`
- False accept count: `0`
- Non-two-storey gate/route covered: `True`

| Case | Status | Gate | Route | Expected counts |
|---|---|---|---|---|
| complex-two-storey | blocked | failed | generator_regeneration_required | `{"IfcBuildingStorey": 2, "IfcDoor": 9, "IfcSpace": 9, "IfcWindow": 9}` |
| non-two-storey-three-level | blocked | failed | generator_regeneration_required | `{"IfcBuildingStorey": 3, "IfcDoor": 3, "IfcSpace": 3, "IfcWindow": 3}` |
| simple-room-smoke | accepted | passed | accept | `{"IfcBuildingStorey": 1, "IfcDoor": 0, "IfcSpace": 1, "IfcWindow": 0}` |
| two-room-smoke | accepted | passed | accept | `{"IfcBuildingStorey": 1, "IfcDoor": 0, "IfcSpace": 2, "IfcWindow": 0}` |
