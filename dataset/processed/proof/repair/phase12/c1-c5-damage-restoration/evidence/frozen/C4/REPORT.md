# C4 damage-restoration proof

这是一次真实 Provider 的个案可行性/可靠性证据，不构成系统级能力提升结论。

- source: `dataset/ifc/test/d7n.ifc`
- source batch: `batch-02`
- terminal status: `succeeded`
- latency: `289.907` seconds
- source IFC was not mutated in place
- private original and damage mapping were introduced only after repair

## Focused IFCcompare geometry/property debug

- focused status: `passed`
- restored members: `6`
- failed members: `0`
- geometry compares request→repaired and original→repaired in a common physical frame
- properties compare request→original→repaired for each frozen occurrence property
- Type check requires the exact surviving Type GlobalId and an unchanged Type graph

| member | geometry | properties | exact Type |
|---|---:|---:|---:|
| `beam-1` | passed | passed | passed |
| `beam-2` | passed | passed | passed |
| `beam-3` | passed | passed | passed |
| `column-1` | passed | passed | passed |
| `door-1` | passed | passed | passed |
| `window-1` | passed | passed | passed |

## Damage and reconstruction GUID trace

| role | damage action | original class | original GUID | repair action | repaired class | repaired GUID |
|---|---|---|---|---|---|---|
| beam-1 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_bw` | rebuilt | IfcBeam | `1ZAaeOoW1L1QUUJRz5EhnR` |
| beam-2 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_kE` | rebuilt | IfcBeam | `00$k1uEtXUYgTtGkFkvwrV` |
| beam-3 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_kQ` | rebuilt | IfcBeam | `2PnlSRoz9I8BHns4YBqd1c` |
| column-1 | removed | IfcColumn | `1Wn_dXmF1DSBE14cb07uYi` | rebuilt | IfcColumn | `1Nfeo7SvXVThFmLIBARQN8` |
| door-1 | removed | IfcDoor | `08DlcJHzb8WfJZDS4ZFHLL` | rebuilt | IfcDoor | `2eo6ilO$vOXwD_jyQVR$O1` |
| door-opening-1 | retained | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHLL` | reused | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHLL` |
| window-1 | removed | IfcWindow | `1PkWQ2IbXBH9Ib7VGdBWCz` | rebuilt | IfcWindow | `2lKOLlncPVzefMXnEzM78Q` |
| window-opening-1 | removed | IfcOpeningElement | `1PkWQ2IbXBH9Ib7USdBWCz` | rebuilt | IfcOpeningElement | `1JeofDfsDPzwRPwgmwo$VO` |

## Whole-model boundary

- IFCcompare execution: `passed`
- generic changed products: `14` {'IfcBeam': 6, 'IfcColumn': 2, 'IfcDoor': 2, 'IfcOpeningElement': 2, 'IfcWindow': 2}
- class counts restored: `True`
- identity-equivalent: `False`
- restored occurrences and relationships may receive new GlobalIds; therefore whole-model identity is not used as the geometry/property acceptance gate

## Damage coverage

- beams: `3`
- columns: `1`
- doors: `1`
- windows: `1`
