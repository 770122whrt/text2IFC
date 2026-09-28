# IFC2X3 Small Model Refined Shortlist

> Main-dataset shortlist after IfcOpenShell semantic screening, candidate-to-candidate SHA deduplication, and fixture-risk filtering.

- Unique meaningful/discipline SHA candidates: **65**
- Main-dataset suitable: **18**
- `<1 MiB` Generation-reference suitable: **9**
- Other Repair-oriented suitable candidates: **9**
- Machine-readable shortlist: `dataset/manifests/acquisitions/ifc2x3-small-github-refined.jsonl`

## Generation-reference shortlist

| Size (MiB) | Elements | Storeys | Classes | Repository | Path | SHA aliases |
| ---: | ---: | ---: | ---: | --- | --- | ---: |
| 0.085 | 47 | 1 | 7 | `opensourceBIM/TestFiles` | `TestData/data/example.ifc` | 0 |
| 0.085 | 16 | 1 | 5 | `opensourceBIM/TestFiles` | `TestData/data/revit_quantities.ifc` | 0 |
| 0.115 | 44 | 1 | 6 | `Moult/ifc-test-files` | `src/ifc-spf/ifcopenhouse.ifc` | 0 |
| 0.246 | 59 | 2 | 4 | `xBimTeam/XbimEssentials` | `Xbim.Essentials.NetCore.Tests/TestFiles/CPM.ifc` | 0 |
| 0.264 | 19 | 3 | 9 | `opensourceBIM/TestFiles` | `TestData/data/export1.ifc` | 0 |
| 0.264 | 19 | 3 | 9 | `opensourceBIM/TestFiles` | `TestData/data/exportX.ifc` | 0 |
| 0.267 | 19 | 3 | 9 | `opensourceBIM/TestFiles` | `TestData/data/export3.ifc` | 0 |
| 0.395 | 115 | 2 | 5 | `ThatOpen/engine_web-ifc` | `examples/example.ifc` | 0 |
| 0.677 | 104 | 2 | 5 | `ThatOpen/web-ifc-three` | `example/model/test.ifc` | 0 |

## Other main-dataset candidates

| Size (MiB) | Type | Elements | Storeys | Classes | Repository | Path |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 0.018 | `meaningful_model` | 13 | 1 | 5 | `AsuniSoft/ifc2x3-SDK` | `data/Ifc/builtModel.ifc` |
| 2.272 | `meaningful_model` | 268 | 4 | 9 | `stijngoedertier/georeference-ifc` | `Duplex_A_20110907_georeferenced.ifc` |
| 2.329 | `meaningful_model` | 146 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/AC90R1-niedriha-V2-2x3.ifc` |
| 2.329 | `meaningful_model` | 146 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/Niedri_slabs.ifc` |
| 2.554 | `meaningful_model` | 692 | 8 | 6 | `opensourceBIM/TestFiles` | `TestData/data/Jesse.1.ifc` |
| 3.069 | `meaningful_model` | 86 | 3 | 8 | `opensourceBIM/TestFiles` | `TestData/data/AC90R1-Jasmin-Sun-105-2x3.ifc` |
| 3.956 | `meaningful_model` | 131 | 2 | 10 | `opensourceBIM/TestFiles` | `TestData/data/AC11-FZK-Haus-IFC.ifc` |
| 4.348 | `meaningful_model` | 268 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/AC9R1-Haus-G-H-Ver2-2x3.ifc` |
| 4.348 | `meaningful_model` | 268 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/AC9R1-Haus-G-H-Ver2-2x3_ALT.ifc` |

## Excluded from main dataset

Candidates classified as single-component, fragment, metadata-only, invalid, obvious bug/ticket/encoding fixtures, or exact candidate duplicates remain discovery evidence only.
