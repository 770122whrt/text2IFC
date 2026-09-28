# IFC2X3 Small Candidate Meaningfulness Review

> Automated IfcOpenShell screening. This is a discovery/admission aid, not a substitute for source/license review.

## Gate

- `single_component`: 1–2 `IfcElement` objects.
- `fragment_fixture`: too few elements or missing project/spatial/containment structure.
- `discipline_model`: spatially structured model with at least 10 elements, useful even if category diversity is narrow.
- `meaningful_model`: spatially structured model with at least 10 elements and either >=3 key element classes or >=25 elements.
- Generation reference recommendation additionally requires `<1 MiB`, building + storey, >=10 elements, and >=3 key classes.

## Summary

- `discipline_model`: **9**
- `fragment_fixture`: **77**
- `invalid`: **5**
- `meaningful_model`: **66**
- `metadata_or_empty`: **22**
- `single_component`: **144**
- New meaningful/discipline candidates: **68**
- New `<1 MiB` Generation reference candidates: **37**
- Machine-readable classification: `dataset/manifests/acquisitions/ifc2x3-small-github-classified.jsonl`

## Recommended candidates

| Size (MiB) | Use | Type | Elements | Storeys | Key classes | Repository | Path |
| ---: | --- | --- | ---: | ---: | ---: | --- | --- |
| 0.013 | generation+repair | `meaningful_model` | 11 | 4 | 3 | `AsuniSoft/ifc2x3-SDK` | `tests/tickets/ticket1179/test_1.ifc` |
| 0.013 | generation+repair | `meaningful_model` | 11 | 4 | 3 | `AsuniSoft/ifc2x3-SDK` | `tests/tickets/ticket5/test_1.ifc` |
| 0.018 | generation+repair | `meaningful_model` | 13 | 1 | 5 | `AsuniSoft/ifc2x3-SDK` | `data/Ifc/builtModel.ifc` |
| 0.058 | generation+repair | `meaningful_model` | 33 | 1 | 2 | `IfcOpenShell/files` | `344--wall--no-holes--augmented.ifc` |
| 0.067 | generation+repair | `meaningful_model` | 24 | 3 | 6 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/ac16_unicode.ifc` |
| 0.067 | generation+repair | `meaningful_model` | 24 | 3 | 6 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/ac16_sjis.ifc` |
| 0.070 | generation+repair | `meaningful_model` | 29 | 1 | 2 | `IfcOpenShell/files` | `474--walls--missing-subtractions--2--augmented.ifc` |
| 0.078 | generation+repair | `meaningful_model` | 24 | 3 | 6 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/ac16_bimserver.ifc` |
| 0.080 | generation+repair | `meaningful_model` | 25 | 3 | 7 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/revit2014_unicode.ifc` |
| 0.085 | generation+repair | `meaningful_model` | 47 | 1 | 7 | `opensourceBIM/TestFiles` | `TestData/data/example.ifc` |
| 0.085 | generation+repair | `meaningful_model` | 16 | 1 | 5 | `opensourceBIM/TestFiles` | `TestData/data/revit_quantities.ifc` |
| 0.092 | generation+repair | `meaningful_model` | 42 | 1 | 2 | `IfcOpenShell/files` | `339--wall--missing-subtractions--augmented.ifc` |
| 0.108 | generation+repair | `meaningful_model` | 25 | 3 | 7 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/revit2014_bimserver.ifc` |
| 0.115 | generation+repair | `meaningful_model` | 44 | 1 | 6 | `Moult/ifc-test-files` | `src/ifc-spf/ifcopenhouse.ifc` |
| 0.124 | generation+repair | `meaningful_model` | 27 | 2 | 5 | `xBimTeam/XbimEssentials` | `Tests/TestFiles/Roof-01_BCAD.ifc` |
| 0.128 | generation+repair | `meaningful_model` | 22 | 3 | 5 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/vectorworks_sjis.ifc` |
| 0.128 | generation+repair | `meaningful_model` | 22 | 3 | 5 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/vectorworks_unicode.ifc` |
| 0.152 | generation+repair | `meaningful_model` | 22 | 3 | 5 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/vectorworks_bimserver.ifc` |
| 0.204 | generation+repair | `meaningful_model` | 25 | 3 | 7 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/revit2013_unicode.ifc` |
| 0.204 | generation+repair | `meaningful_model` | 25 | 3 | 7 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/revit2013_unicode_fixed.ifc` |
| 0.222 | generation+repair | `meaningful_model` | 18 | 1 | 4 | `IfcOpenShell/files` | `487.ifc` |
| 0.246 | generation+repair | `meaningful_model` | 59 | 2 | 4 | `xBimTeam/XbimEssentials` | `Xbim.Essentials.NetCore.Tests/TestFiles/CPM.ifc` |
| 0.263 | generation+repair | `meaningful_model` | 25 | 3 | 7 | `opensourceBIM/TestFiles` | `TestData/data/japanesechars/revit2013_bimserver.ifc` |
| 0.264 | generation+repair | `meaningful_model` | 19 | 3 | 9 | `opensourceBIM/TestFiles` | `TestData/data/export1.ifc` |
| 0.264 | generation+repair | `meaningful_model` | 19 | 3 | 9 | `opensourceBIM/TestFiles` | `TestData/data/exportX.ifc` |
| 0.267 | generation+repair | `meaningful_model` | 19 | 3 | 9 | `opensourceBIM/TestFiles` | `TestData/data/export3.ifc` |
| 0.267 | generation+repair | `meaningful_model` | 19 | 3 | 9 | `opensourceBIM/TestFiles` | `TestData/data/doubleguids.ifc` |
| 0.332 | generation+repair | `meaningful_model` | 35 | 1 | 2 | `IfcOpenShell/files` | `396--slab--segfault--augmented.ifc` |
| 0.395 | generation+repair | `meaningful_model` | 115 | 2 | 5 | `ThatOpen/engine_web-ifc` | `examples/example.ifc` |
| 0.395 | generation+repair | `meaningful_model` | 115 | 2 | 5 | `ThatOpen/engine_web-ifc` | `tests/ifcfiles/public/example.ifc` |
| 0.420 | generation+repair | `meaningful_model` | 12 | 1 | 3 | `IfcOpenShell/files` | `1948--wall--wrong-geometry--augmented.ifc` |
| 0.457 | generation+repair | `meaningful_model` | 252 | 1 | 2 | `IfcOpenShell/files` | `444--beam--segfault--augmented.ifc` |
| 0.515 | generation+repair | `meaningful_model` | 12 | 1 | 3 | `IfcOpenShell/files` | `1948--wall--wrong-geometry.ifc` |
| 0.566 | generation+repair | `meaningful_model` | 32 | 7 | 2 | `IfcOpenShell/files` | `478--walls--missing-subtractions--augmented.ifc` |
| 0.677 | generation+repair | `meaningful_model` | 104 | 2 | 5 | `ThatOpen/engine_web-ifc` | `tests/ifcfiles/public/tested_sample_project.ifc` |
| 0.677 | generation+repair | `meaningful_model` | 104 | 2 | 5 | `ThatOpen/web-ifc-three` | `example/model/test.ifc` |
| 0.756 | generation+repair | `meaningful_model` | 136 | 1 | 2 | `IfcOpenShell/files` | `732--slab--segfault.ifc` |
| 0.030 | repair | `discipline_model` | 13 | 1 | 2 | `IfcOpenShell/files` | `507--wall--missing-subtractions--augmented.ifc` |
| 0.040 | repair | `discipline_model` | 22 | 1 | 1 | `opensourceBIM/TestFiles` | `TestData/data/WallStandardCase-01A.ifc` |
| 0.041 | repair | `discipline_model` | 24 | 1 | 2 | `IfcOpenShell/files` | `426--wall--segfault--augmented.ifc` |
| 0.151 | repair | `discipline_model` | 19 | 1 | 1 | `Moult/ifc-test-files` | `src/ifc-spf/rebar-beam.ifc` |
| 0.168 | repair | `meaningful_model` | 65 | 1 | 1 | `IfcOpenShell/files` | `394--slab--wrong-subtractions--augmented.ifc` |
| 0.192 | repair | `discipline_model` | 11 | 1 | 2 | `IfcOpenShell/files` | `359--wall--wrong-geometry--augmented.ifc` |
| 0.244 | repair | `meaningful_model` | 63 | 1 | 0 | `IfcOpenShell/files` | `330--reinforcingBar--segfault--augmented.ifc` |
| 0.542 | repair | `discipline_model` | 17 | 1 | 1 | `IfcOpenShell/files` | `345--buildingElementProxy--segfault--1--augmented.ifc` |
| 0.690 | repair | `discipline_model` | 18 | 1 | 1 | `IfcOpenShell/files` | `IfcReinforcingBar.ifc` |
| 0.765 | repair | `meaningful_model` | 65 | 0 | 9 | `IfcOpenShell/files` | `acad2010_objects.ifc` |
| 0.766 | repair | `meaningful_model` | 66 | 0 | 9 | `IfcOpenShell/files` | `nested_mapped_item.ifc` |
| 0.817 | repair | `meaningful_model` | 25 | 1 | 1 | `IfcOpenShell/files` | `345--buildingElementProxy--segfault--2--augmented.ifc` |
| 1.361 | repair | `meaningful_model` | 184 | 3 | 9 | `xBimTeam/XbimEssentials` | `Tests/TestSourceFiles/House.ifc` |
| 1.919 | repair | `discipline_model` | 15 | 1 | 2 | `IfcOpenShell/files` | `411--walls--segfault--accept-errors.ifc` |
| 2.272 | repair | `meaningful_model` | 268 | 4 | 9 | `stijngoedertier/georeference-ifc` | `Duplex_A_20110907_georeferenced.ifc` |
| 2.329 | repair | `meaningful_model` | 146 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/AC90R1-niedriha-V2-2x3.ifc` |
| 2.329 | repair | `meaningful_model` | 146 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/Niedri_org.ifc` |
| 2.329 | repair | `meaningful_model` | 146 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/Niedri_slabs.ifc` |
| 2.554 | repair | `meaningful_model` | 692 | 8 | 6 | `opensourceBIM/TestFiles` | `TestData/data/Jesse.1.ifc` |
| 3.069 | repair | `meaningful_model` | 86 | 3 | 8 | `opensourceBIM/TestFiles` | `TestData/data/AC90R1-Jasmin-Sun-105-2x3.ifc` |
| 3.581 | repair | `meaningful_model` | 5178 | 1 | 1 | `IfcOpenShell/files` | `geometrygym_great_court_roof.ifc` |
| 3.909 | repair | `meaningful_model` | 986 | 3 | 8 | `ThatOpen/engine_web-ifc` | `tests/ifcfiles/public/Office_A_20110811.ifc` |
| 3.956 | repair | `meaningful_model` | 131 | 2 | 10 | `opensourceBIM/TestFiles` | `TestData/data/AC11-FZK-Haus-IFC.ifc` |
| 4.319 | repair | `meaningful_model` | 317 | 3 | 7 | `ThatOpen/engine_web-ifc` | `tests/ifcfiles/public/ISSUE_126_model.ifc` |
| 4.348 | repair | `meaningful_model` | 268 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/AC9R1-Haus-G-H-Ver2-2x3.ifc` |
| 4.348 | repair | `meaningful_model` | 268 | 4 | 9 | `opensourceBIM/TestFiles` | `TestData/data/AC9R1-Haus-G-H-Ver2-2x3_ALT.ifc` |
| 4.708 | repair | `meaningful_model` | 1001 | 4 | 11 | `AsuniSoft/ifc2x3-SDK` | `tests/tickets/ticket1179/test_2.ifc` |
| 4.708 | repair | `meaningful_model` | 1001 | 4 | 11 | `AsuniSoft/ifc2x3-SDK` | `tests/tickets/ticket5/test_2.ifc` |
| 4.916 | repair | `meaningful_model` | 228 | 3 | 9 | `ThatOpen/engine_web-ifc` | `tests/ifcfiles/public/ISSUE_034_HouseZ.ifc` |
| 6.103 | repair | `meaningful_model` | 138 | 3 | 3 | `ThatOpen/engine_web-ifc` | `tests/ifcfiles/public/ISSUE_102_M3D-CON.ifc` |
| 8.859 | repair | `discipline_model` | 16 | 1 | 2 | `IfcOpenShell/files` | `456--wall--infiniteLoop--augmented.ifc` |
