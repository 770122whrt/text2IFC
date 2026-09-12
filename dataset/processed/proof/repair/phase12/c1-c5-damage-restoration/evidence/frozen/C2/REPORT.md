# C2 damage-restoration proof

这是一次真实 Provider 的个案可行性/可靠性证据，不构成系统级能力提升结论。

- source: `dataset/ifc/train/1px.ifc`
- source batch: `batch-01`
- terminal status: `succeeded`
- latency: `174.063` seconds
- source IFC was not mutated in place
- private original and damage mapping were introduced only after repair

## Focused IFCcompare geometry/property debug

- focused status: `passed`
- restored members: `2`
- failed members: `0`
- geometry compares request→repaired and original→repaired in a common physical frame
- properties compare request→original→repaired for each frozen occurrence property
- Type check requires the exact surviving Type GlobalId and an unchanged Type graph

| member | geometry | properties | exact Type |
|---|---:|---:|---:|
| `restore-beam-1` | passed | passed | passed |
| `restore-door-1` | passed | passed | passed |

## Damage and reconstruction GUID trace

| role | damage action | original class | original GUID | repair action | repaired class | repaired GUID |
|---|---|---|---|---|---|---|
| beam-1 | removed | IfcBeam | `2kMW8XyZv1d9XdPJLihM2E` | rebuilt | IfcBeam | `2rNJSIlpzHCOHLIeIfKKkG` |
| door-1 | removed | IfcDoor | `2AJ6T3vZDDZRJL7l0pGl86` | rebuilt | IfcDoor | `11xxv$HQPPwwhkMbOliRCq` |
| door-opening-1 | retained | IfcOpeningElement | `2AJ6T3vZDDZRJL7kCpGl86` | reused | IfcOpeningElement | `2AJ6T3vZDDZRJL7kCpGl86` |

## Whole-model boundary

- IFCcompare execution: `passed`
- generic changed products: `4` {'IfcBeam': 2, 'IfcDoor': 2}
- class counts restored: `True`
- identity-equivalent: `False`
- restored occurrences and relationships may receive new GlobalIds; therefore whole-model identity is not used as the geometry/property acceptance gate

## Damage coverage

- beams: `1`
- columns: `0`
- doors: `1`
- windows: `0`
