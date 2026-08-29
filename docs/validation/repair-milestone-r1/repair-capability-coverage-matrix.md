# Repair Milestone R1 能力覆盖矩阵

## 1. Legend

- `●`：该案例直接验收此能力。
- `◐`：该案例只验收识别、守卫或零修改，不声明成功 authoring。
- `—`：不适用。

矩阵描述的是已冻结的未来执行覆盖，不是已经得到的 live/Proof 结果。

## 2. Semantic and operation coverage

| Capability | E1 | E2 | E3 | E4 | M1 | M2 | M3 | H1 | H2 | H3 | H4 | A1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Property retrieval + Stage 1.5 | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | — | — |
| `IfcBoolean` property | ● | — | — | — | — | — | ● | — | — | ● | — | — |
| `IfcLabel` property | — | ● | — | ● | ● | — | — | ● | ● | — | — | — |
| `IfcIdentifier` property | — | — | ● | — | — | ● | — | — | — | — | — | — |
| Post-resolution invalid value | — | — | — | — | ● | — | — | — | — | — | — | — |
| Window occurrence edit | ● | — | — | — | — | — | — | ● | — | ● | — | — |
| Door occurrence edit | — | ● | — | — | ● | — | — | — | ● | — | — | — |
| Wall occurrence edit | — | — | — | ● | — | — | — | — | ● | — | — | — |
| Beam occurrence edit | — | — | ● | — | — | — | — | — | — | — | — | — |
| Beam add | — | — | — | — | — | ● | — | ● | — | — | ◐ | ● |
| Column add | — | — | — | — | — | — | ● | — | — | — | — | — |
| Generated structural Type | — | — | — | — | — | ● | ● | ● | — | — | ◐ | — |
| Exact existing Type reuse | — | — | — | — | — | — | — | — | — | — | — | ● |
| Explicit non-square Column orientation | — | — | — | — | — | — | ● | — | — | — | — | — |
| Natural target ambiguity/resume | — | — | — | — | — | — | — | — | — | ● | — | — |
| Value correction/resume | — | — | — | — | ● | — | — | — | — | — | — | — |
| Unsupported-program guard | — | — | — | — | — | — | — | — | — | — | ● | — |
| Multi-operation/cross-family | — | — | — | — | — | — | — | ● | ● | — | ● | — |
| Atomic all-or-nothing | — | — | — | — | — | — | — | ● | ● | — | ● | — |

## 3. Execution and evidence coverage

| Contract | E1 | E2 | E3 | E4 | M1 | M2 | M3 | H1 | H2 | H3 | H4 | A1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Exact target/Storey identity | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| Deterministic admissibility | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| Stage 2 exact ChangeSet | ● | ● | ● | ● | resume | ● | ● | ● | ● | resume | N/A | ● |
| Binder equality | ● | ● | ● | ● | resume | ● | ● | ● | ● | resume | N/A | ● |
| Atomic IFC apply | ● | ● | ● | ● | resume | ● | ● | ● | ● | resume | N/A | ● |
| IfcOpenShell reopen | ● | ● | ● | ● | resume | ● | ● | ● | ● | resume | N/A | ● |
| L0 schema/parse | ● | ● | ● | ● | resume | ● | ● | ● | ● | resume | N/A | ● |
| L1 requested semantic diff | ● | ● | ● | ● | resume | ● | ● | ● | ● | resume | N/A | ● |
| L2 geometric/spatial validity | ● | ● | ● | ● | resume | ● | ● | ● | ● | resume | N/A | ● |
| Source/repaired preservation | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| Zero mutation before resume/unsupported | — | — | — | — | ● | — | — | — | — | ● | ● | — |
| Provider attempt provenance | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| Private-Gold/mutation-truth leakage check | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |

For `M1` and `H3`, `resume` means the initial turn must stop without output IFC and the resumed
turn must complete the listed Stage 2/apply/reopen/validation evidence under the same persisted
clarification lineage. For `H4`, L0/L1/L2 are not fabricated for a nonexistent repaired artifact;
the required artifact evidence is unchanged source identity and absence of terminal publication.

## 4. Model and diversity slices

| Slice | Coverage |
|---|---|
| Public source corpora | IFC-Bench (3 models); BIM Whale samples (1 model) |
| Project scale | metre (Duplex); millimetre (WRH, Sixty5, TallBuilding) |
| Building form | compact residential; large hospital; tall structural; small high-rise |
| Discipline emphasis | architectural; structural |
| Size | 0.6 MB to 80.3 MB |
| Storeys | 4, 8, 19, 5 |
| Existing occurrence density | sparse to dense |
| Existing Type graph | no structural occurrence/Type surface through rich Beam/Column Types |
| Language/request form | Chinese natural language; English IFC terms/identities embedded where exactness is required |
| Outcome class | success; post-resolution value correction; target clarification; unsupported transaction |

## 5. Deliberate non-claims and gaps

The following registered or adjacent behaviors are not part of the R1 final acceptance claim:

- `add_window_with_opening_to_wall`, `add_opening_to_wall`,
  `add_door_with_opening_to_wall`, `fill_existing_opening_with_door`;
- unspecified-Type policy behavior;
- rotated/curved/sloped Beam, slanted or split Column, grids and structural analysis objects;
- Type-level property mutation, non-scalar properties, quantities and material authoring;
- IFC4/IFC4x3 authoring;
- geometric restoration scored against private pristine/damaged/repaired triplets.

They are recorded as `SUPPORTED_BUT_NOT_FINAL_ACCEPTANCE_ELIGIBLE` where already registered, or
as out of scope where the manifest says unsupported. Their absence does not get silently converted
into an R1 coverage claim.

## 6. IFCCompare eligibility

The 12 diversity cases have public source IFCs but no legitimate private mutation/pristine truth.
Therefore final truth-based IFCCompare eligibility is `0/12`. Each successful case still requires
source/repaired preservation checks and L0/L1/L2. Existing Plan 07 truth-bearing cases remain a
separate Phase 12.1 closure set and are not counted in this matrix.
