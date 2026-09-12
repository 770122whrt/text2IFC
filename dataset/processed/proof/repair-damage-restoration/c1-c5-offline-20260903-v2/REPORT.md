# C1-C5 offline replay IFCcompare Proof

This package is deterministic offline public-API replay evidence, not a new live Provider run.
It mirrors the observed genuine-live artifact hierarchy and uses focused IFCcompare for geometry dimensions, requested occurrence properties, and exact surviving Type reuse.

| case | restored members | columns | IFCcompare |
|---|---:|---:|---:|
| C1 | 2 | 0 | passed |
| C2 | 2 | 0 | passed |
| C3 | 4 | 1 | passed |
| C4 | 6 | 1 | passed |
| C5 | 8 | 0 | passed |

C3 and C4 include real IfcColumn damage/restoration coverage.
Whole-model identity differences are retained as diagnostics because restored roots receive new GlobalIds.
