# IFC2X3 Small Source Search Follow-up

This report records the second-pass audit requested after the initial `<10 MiB` discovery. Physical canonical data remains source-organized under `dataset/external/`.

## Current repository re-check

### xeokit/xeokit-model-conversion-tests

The current `main` tree contains only 2 IFC files below 10 MiB. Both were opened with IfcOpenShell and are IFC4X1, not IFC2X3:

- `Dormitory-ARC-Level2-only-IfcSpace-only.ifc` — 0.023 MiB, IFC4X1, not a main-model candidate.
- `Dormitory-ARC-Level2-only.ifc` — 2.391 MiB, IFC4X1, 476 elements.

The repository historically contained many more IFC files. Commit history shows a 2023-09-15 `Remove IFCs` change. The pre-removal tree was therefore inspected rather than treating the current branch as exhaustive.

A complete `<10 MiB` scan of the 2023-09-12 pre-removal tree found 51 IFC files, of which 9 were IFC2X3. Seven were meaningful complete models. Exact local comparison found:

- `Duplex_2x3_2011-09-07.ifc` — exact duplicate of the canonical buildingSMART Community Duplex.
- `Duplex_A_20110907.ifc` — exact duplicate of the same canonical Duplex.
- `Clinic_Electrical.ifc` — exact duplicate of the canonical buildingSMART Community Clinic Electrical model; excluded by the current main-model diversity gate because it is a narrow electrical discipline model.

Four unique meaningful model identities remain as provenance/license-review candidates:

| Size (MiB) | Historical xeokit path | Elements | Storeys | Key classes | Status |
| ---: | --- | ---: | ---: | ---: | --- |
| 0.108 | `inputFiles/IfcOpenShell/IfcOpenHouse2x3.ifc` | 44 | 1 | 6 | new SHA; original model rights/source review required |
| 1.553 | `inputFiles/Duplex-IFC2x3-2011-09-14/Duplex_A_20110907_optimized.ifc` | 268 | 4 | 9 | new SHA; known Common BIM/reference model, source-rights review required |
| 2.220 | `inputFiles/Duplex-IFC2x3-2011-05-05/Duplex_2x3_2011-05-05.ifc` | 258 | 4 | 9 | new SHA; historical Duplex version, source-rights review required |
| 3.921 | `inputFiles/BIMData/19_rue_Marc_Antoine_Petit_Ground_floor.ifc` | 358 | 1 | 10 | new SHA; BIMData is discovery-only, original model rights review required |

`inputFiles/Revit/Duplex.ifc` is an exact SHA duplicate of the 2011-05-05 Duplex above and is not a fifth model.

The xeokit static conversion index also exposes additional historical `<10 MiB` names that are no longer in the current Git tree, including `Electric.ifc`, `Ven.ifc`, `bim1840.ifc`, an Auckland `sample.ifc`, and `RiverSideOffice.ifc`. These remain leads only until their original IFC bytes and upstream provenance can be recovered; converted XKT outputs are not treated as source IFC admission evidence.

### viktor-platform/ifc-sample-models

The repository contains 5 IFC files total; 4 are below 10 MiB. All four were opened directly with IfcOpenShell and are IFC4, not IFC2X3:

- `Structure Walls.ifc` — 0.426 MiB, IFC4.
- `SampleBimModelWebinar.ifc` — 5.001 MiB, IFC4.
- `SampleStructuralModel.ifc` — 5.808 MiB, IFC4.
- `SampleBuilding.ifc` — 6.433 MiB, IFC4.

No new `<10 MiB` IFC2X3 candidate exists in the current repository.

### youshengCode/IfcSampleFiles

The current repository contains 18 IFC files; 11 are below 10 MiB. The `<10 MiB` IFC2X3 content consists of the Duplex family already represented locally:

- `Ifc2x3_Duplex_Architecture.ifc` — exact SHA duplicate of canonical buildingSMART Community Duplex Architecture.
- `Ifc2x3_Duplex_Mechanical.ifc` — exact SHA duplicate of canonical buildingSMART Community Duplex Mechanical/Rooms model.
- `Ifc2s3_Duplex_Electrical.ifc` — exact SHA duplicate of canonical buildingSMART Community Duplex Electrical; narrow discipline model.

Other small files in the repository are IFC4. The repository also contains IFC2X3 files above 10 MiB, but these are outside the current small-model acquisition scope.

### bo-codes/ifc-examples

The current repository contains one IFC file, `room.blend.ifc` (~0.006 MiB). It is IFC4 and contains only one IFC element, so it is excluded as a single-component/example fixture.

## Wider source sweep

The GNI BIM Dataset maintains `other_online_BIM_model_resources.csv` with 35 online BIM sources. This list is being used as the systematic discovery backbone rather than ad-hoc search.

Already covered or substantially covered locally:

- BIM Whale IFC Samples
- BIMData R&D / DURAARK upstream
- buildingSMART Sample & Community files
- KIT IFC Examples
- NIBS/Common BIM derivatives represented in Community files
- Schependomlaan (migrated to buildingSMART sample/community data)
- Munkerud and HITOS via DURAARK
- STEP Tools samples

Not currently admitted without further model-level rights/provenance review:

- Open IFC Model Repository (University of Auckland)
- AEC Open Data directory links
- GeometryGym examples where model-level terms are unclear
- Kaggle aggregations until original-source duplication and license inheritance are checked

LivingBIM is open-access but its current downloadable packages are GB-scale and therefore outside the `<10 MiB` acquisition focus.

## GNI admission update

The 16 meaningful GNI BIM Dataset IFC2X3 candidates discovered in the previous batch are now canonical. All 16:

- are below 10 MiB;
- have explicit dataset-level CC BY 4.0 rights;
- passed semantic meaningfulness screening;
- passed parse, traversal, write, and reopen validation;
- are `IFC2X3_CERTIFIED`.

Classification/provenance ledger:

`dataset/manifests/acquisitions/gni-bim-dataset-small-ifc2x3.jsonl`

Physical source root:

`dataset/external/gni-bim-dataset/`
