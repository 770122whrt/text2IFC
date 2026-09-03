# C4 offline replay Proof

Evidence mode: `deterministic_offline_replay`; this is not a live Provider claim.
The replay traversed the production public RepairAPI path and was evaluated after repair against the private original.

| restored member | geometry | properties | exact Type |
|---|---:|---:|---:|
| `restore-beam-1` | passed | passed | passed |
| `restore-beam-2` | passed | passed | passed |
| `restore-beam-3` | passed | passed | passed |
| `restore-column-1` | passed | passed | passed |
| `restore-door-1` | passed | passed | passed |
| `restore-window-1` | passed | passed | passed |

- focused IFCcompare: `passed`
- class counts restored: `True`
- whole-model identity equivalent: `False`
- new restored occurrence/relationship GlobalIds are expected; whole-model identity is not the geometry/property gate
