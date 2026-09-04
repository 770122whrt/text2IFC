# C5 damage-restoration proof

这是一次真实 Provider 的个案可行性/可靠性证据，不构成系统级能力提升结论。

- source: `dataset/ifc/test/d7n.ifc`
- source batch: `batch-02`
- terminal status: `succeeded`
- latency: `292.907` seconds
- source IFC was not mutated in place
- private original and damage mapping were introduced only after repair

## Focused IFCcompare geometry/property debug

- focused status: `passed`
- restored members: `8`
- failed members: `0`
- geometry compares request→repaired and original→repaired in a common physical frame
- properties compare request→original→repaired for each frozen occurrence property
- Type check requires the exact surviving Type GlobalId and an unchanged Type graph

| member | geometry | properties | exact Type |
|---|---:|---:|---:|
| `beam-add-1` | passed | passed | passed |
| `beam-add-2` | passed | passed | passed |
| `beam-add-3` | passed | passed | passed |
| `beam-add-4` | passed | passed | passed |
| `door-fill-1` | passed | passed | passed |
| `door-fill-2` | passed | passed | passed |
| `window-add-1` | passed | passed | passed |
| `window-add-2` | passed | passed | passed |

## Damage and reconstruction GUID trace

| role | damage action | original class | original GUID | repair action | repaired class | repaired GUID |
|---|---|---|---|---|---|---|
| beam-1 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_i1` | rebuilt | IfcBeam | `1ggKpNiuvLpA6NLtentUvo` |
| beam-2 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_iq` | rebuilt | IfcBeam | `2PwEcBr2TSX93FtuAOGpTm` |
| beam-3 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_jN` | rebuilt | IfcBeam | `1pzan$JpLKUAvMcxZa4xiJ` |
| beam-4 | removed | IfcBeam | `1RnWak0Kr6GxkeYF4Sd_ky` | rebuilt | IfcBeam | `0dDuisiCLTjA9MeIfMqx_s` |
| door-1 | removed | IfcDoor | `08DlcJHzb8WfJZDS4ZFHLL` | rebuilt | IfcDoor | `2aHbEK1t9Quu0Do$XwqdWS` |
| door-opening-1 | retained | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHLL` | reused | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHLL` |
| door-2 | removed | IfcDoor | `08DlcJHzb8WfJZDS4ZFHQO` | rebuilt | IfcDoor | `2GfqqcchDLrAfPxkzdeWiX` |
| door-opening-2 | retained | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHQO` | reused | IfcOpeningElement | `08DlcJHzb8WfJZDT8ZFHQO` |
| window-1 | removed | IfcWindow | `1PkWQ2IbXBH9Ib7VGdBWCz` | rebuilt | IfcWindow | `0zyd2xxKrPWBhOw$fQhTjF` |
| window-opening-1 | removed | IfcOpeningElement | `1PkWQ2IbXBH9Ib7USdBWCz` | rebuilt | IfcOpeningElement | `1LhXvBVx5GIByeSTDrw_dG` |
| window-2 | removed | IfcWindow | `1PkWQ2IbXBH9Ib7VGdBXBy` | rebuilt | IfcWindow | `3b5LkAHfPUrPCAdmKBYacA` |
| window-opening-2 | removed | IfcOpeningElement | `1PkWQ2IbXBH9Ib7USdBXBy` | rebuilt | IfcOpeningElement | `0hNP1OypTQbwxvEu3eNgBX` |

## Whole-model boundary

- IFCcompare execution: `passed`
- generic changed products: `20` {'IfcBeam': 8, 'IfcDoor': 4, 'IfcOpeningElement': 4, 'IfcWindow': 4}
- class counts restored: `True`
- identity-equivalent: `False`
- restored occurrences and relationships may receive new GlobalIds; therefore whole-model identity is not used as the geometry/property acceptance gate

## Damage coverage

- beams: `4`
- columns: `0`
- doors: `2`
- windows: `2`
