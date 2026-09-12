# C3 damage-restoration proof

这是一次真实 Provider 的个案可行性/可靠性证据，不构成系统级能力提升结论。

- source: `dataset/ifc/test/d7n.ifc`
- source batch: `batch-02`
- terminal status: `succeeded`
- latency: `249.703` seconds
- source IFC was not mutated in place
- private original and damage mapping were introduced only after repair

## Focused IFCcompare geometry/property debug

- focused status: `passed`
- restored members: `4`
- failed members: `0`
- geometry compares request→repaired and original→repaired in a common physical frame
- properties compare request→original→repaired for each frozen occurrence property
- Type check requires the exact surviving Type GlobalId and an unchanged Type graph

| member | geometry | properties | exact Type |
|---|---:|---:|---:|
| `beam-1-add` | passed | passed | passed |
| `beam-2-add` | passed | passed | passed |
| `column-1-add` | passed | passed | passed |
| `door-1-fill` | passed | passed | passed |

## Damage and reconstruction GUID trace

| role | damage action | original class | original GUID | repair action | repaired class | repaired GUID |
|---|---|---|---|---|---|---|
| beam-1 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_XV` | rebuilt | IfcBeam | `3dDCGbVHnS5x2DfaUPs0PK` |
| beam-2 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_ld` | rebuilt | IfcBeam | `2s$OZ3oVLG3eDAzPS5FPE1` |
| column-1 | removed | IfcColumn | `1Wn_dXmF1DSBE14cb07uXX` | rebuilt | IfcColumn | `3YQzfCl9nGSPdxvRjxCPkl` |
| door-1 | removed | IfcDoor | `08DlcJHzb8WfJZDS4ZFHLL` | rebuilt | IfcDoor | `0Z4jXh_NbPVx9uMW5zayxl` |
| door-opening-1 | retained | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHLL` | reused | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHLL` |

## Whole-model boundary

- IFCcompare execution: `passed`
- generic changed products: `8` {'IfcBeam': 4, 'IfcColumn': 2, 'IfcDoor': 2}
- class counts restored: `True`
- identity-equivalent: `False`
- restored occurrences and relationships may receive new GlobalIds; therefore whole-model identity is not used as the geometry/property acceptance gate

## Damage coverage

- beams: `2`
- columns: `1`
- doors: `1`
- windows: `0`
