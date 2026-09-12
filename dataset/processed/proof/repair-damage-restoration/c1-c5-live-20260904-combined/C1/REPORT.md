# C1 damage-restoration proof

这是一次真实 Provider 的个案可行性/可靠性证据，不构成系统级能力提升结论。

- source: `dataset/external/ifc-bench/projects/sixty5/str.ifc`
- source batch: `batch-01`
- terminal status: `succeeded`
- latency: `446.297` seconds
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
| `add-support-beam-1` | passed | passed | passed |
| `add-support-beam-2` | passed | passed | passed |

## Damage and reconstruction GUID trace

| role | damage action | original class | original GUID | repair action | repaired class | repaired GUID |
|---|---|---|---|---|---|---|
| beam-1 | removed | IfcBeam | `07ykdjoGLBROeD1VZtZex9` | rebuilt | IfcBeam | `0PHy0Z4ATS3AnyPFMvZ9yN` |
| beam-2 | removed | IfcBeam | `07ykdjoGLBROeD1VZtZebp` | rebuilt | IfcBeam | `1VcZXBjsbVbu6zMmHkJXyl` |

## Whole-model boundary

- IFCcompare execution: `passed`
- generic changed products: `4` {'IfcBeam': 4}
- class counts restored: `True`
- identity-equivalent: `False`
- restored occurrences and relationships may receive new GlobalIds; therefore whole-model identity is not used as the geometry/property acceptance gate

## Damage coverage

- beams: `2`
- columns: `0`
- doors: `0`
- windows: `0`
