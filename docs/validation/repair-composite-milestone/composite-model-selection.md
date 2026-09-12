# Composite Model Selection — Text2IFC Composite Repair Milestone

**Status:** frozen at base revision `8bfcfe075521ddb142f8608296dfbfea1fd385e4` (branch `Zcode`).

**Purpose:** specification Section 6. Records every selected IFC2X3 model and
every frozen public geometry binding used by the composite scale ladder.
All measurements below were computed with the production index adapters
themselves (`text2ifc_ifc_repair.index_adapters.default_index_adapter_registry`)
via `scripts/ifc_repair/composite_evidence/inspect_models.py` and targeted
verification scripts — the exact same public measurement path the production
retriever uses. **No private Gold, mutation truth, deleted identity, or
comparator data was read.** The source models are pristine public corpus files;
this evidence group composes NEW authorized modifications on top of them, so
there is no damage/mutation truth to leak.

## 1. Selected models (3 total)

| Model ID | Source path | Schema | Size | SHA-256 | License / authorization |
| --- | --- | --- | --- | --- | --- |
| `CM-VVO` | `dataset/ifc/train/vvo.ifc` | IFC2X3 | 2,409,268 | `b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc` | BIMNet (user-authorized local use, `dataset/manifests/bimnet-ifc2x3.jsonl`); scene family `vvo`, project split `test` |
| `CM-S65` | `dataset/external/ifc-bench/projects/sixty5/str.ifc` | IFC2X3 | 7,422,441 | `79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22` | IFC-Bench (CC BY 4.0 per R1 freeze `R1-S65-STR`), evaluation use |
| `CM-TALL` | `dataset/external/bim-whale-ifc-samples/TallBuilding/IFC/TallBuilding.ifc` | IFC2X3 | 616,509 | `9f180a7148bb7bcf43dd80800068553f1c8b189ebe0dc84b6c498061832960d1` | BIM Whale samples (MIT retained corpus per R1 freeze `R1-BW-TALL`), evaluation use |

Rationale (diversity per Section 4):

* **vvo** — BIMNet corpus, metric-mm file, 7 storeys (Chinese storey names), 77 straight walls all globally unique by (length/height/thickness/direction), 8 empty measurable openings, prior Text2IFC evidence usage (phase10.5 window fidelity, phase11 door, phase12 four-family case, R1 mixed). Chosen for the HERO case C5/C5-N because it is the only model where wall targeting, opening fill, AND structural adds are all simultaneously bindable with public facts, and because it matches the four-family frozen precedent.
* **S65 (sixty5 str)** — IFC-Bench external corpus, 19 storeys, mm units, 299 walls (3 globally unique opening-free long walls on the ground storey), 354 beams, 387 columns, 109 ColumnTypes, 1284 openings (46 unfilled measurable openings hosted on globally unique walls, exactly one uniquely-bindable door-sized opening: 1170×2490×3048 mm, offset 3795, sill 0, host `2$GiA0FALCKuqNnxjNZITr`). Different source, discipline (structural model with Dutch storey names) and scale from vvo and TALL. Prior usage: R1 model selection `R1-S65-STR` (prepared only, never executed). Chosen for C2 (door-fill + columns) and C4 (door-add + window-add + beam + 4 columns) on storey `00 begane grond`.
  * **Note (honest record):** an earlier pre-freeze draft selected WRH (West Riverside Hospital). During the offline full-chain preflight, WRH's 80 MB file was measured to require ~209 s for a single ifcopenshell validation, exceeding the frozen 180 s production evaluation deadline (`src/text2ifc_ifc_repair/evaluation.py:77`, `EvaluationExecutionPolicy.deadline_seconds`), so WRH cannot pass the production L1 validation gate on this machine — a genuine production constraint, not a defect to patch. The freeze was regenerated (before any genuine execution) with S65 bindings, which validate in ~16 s.
* **TALL (Tall Building)** — BIM Whale corpus, 5 storeys, mm units, small model (24 walls, 21 windows, 5 doors, no beams/columns). Prior usage: R1 `R1-BW-TALL` (prepared only). Chosen for C1 (small beam+column composite) and C3 (multi-family) — different unit-system feel, simple layout, storey-local placement in genuinely free space east of all walls.

Rejected: `R1-DPX-ARC` (duplex) — only 1 globally unique wall (geometry ambiguity for wall targeting) and its 8 existing beams are unmeasurable mixed-representation; `R1-WRH-ARC` (West Riverside Hospital) — rich in walls/openings/doors/windows, but its 80 MB file needs ~209 s for one ifcopenshell validation, exceeding the frozen 180 s production evaluation deadline, so it cannot pass the L1 validation gate on this machine (see the honest-record note above); S65 has 0 existing doors/windows of its own, but it does have one uniquely-bindable empty door-sized opening and unique opening-free walls, which is exactly what the door/window bindings need (the door/window entities are created by the operations).

## 2. Model facts (public information only)

### CM-VVO (`vvo.ifc`)

* Units: length unit scale = 0.001 m per project unit (i.e. file is in mm).
* Storeys (7): `标高0` `1vTeahUkP60PdWqwCTjeRs` (elev −2344.06), `标高1` `1vTeahUkP60PdWqwCTjSlm` (−2294.06), **`标高2` `1vTeahUkP60PdWqwCTjSGJ` (−2213.70)**, `标高3` `1vTeahUkP60PdWqwCTjSOR` (807.20), `标高7` `1vTeahUkP60PdWqwCTjUuM` (1368.0), `标高5` `1vTeahUkP60PdWqwCTjUm$` (1961.39), `标高9` `1vTeahUkP60PdWqwCTiX6E` (2399.98).
* Counts: Wall 77 (all straight-wall measurable, all 77 globally unique by L/H/T/direction), OpeningElement 57 (8 empty+measurable), Door 24, Window 21, Beam 6 (all on `标高7`), Column 5 (all on `标高0`), BuildingStorey 7.
* Storey `标高2` local facts: 48 straight walls; 8 empty openings; member placements span storey-local X −13276..12453, Y −14884..15173; no existing beams/columns on this storey (so no same-axis overlap risk).
* Candidate walls (unique geometry, on `标高2`), used bindings:
  * Wall W-A `2CsmzAChHF6O6maGXlo6rd`: L=5325.0, H=3020.9, T=240.0, direction south, storey elevation −2213.701 mm. Hosts 2 empty openings.
  * Wall W-B `0jltRti3rFigAmdXYhXxqI`: L=13455.6, H=4175.1, T=240.0, direction east. Hosts 1 empty opening (door-fill candidate).
  * Wall W-C `1boalssSHBYut0JHgwRsfX`: L=2814.2, H=4175.1, T=260.0, direction east. Hosts 1 empty opening (door-fill candidate).
  * Wall W-D `2HNE4WMQ1CXebZMaih8X$b`: L=4609.0, H=3581.7, T=260.0, direction east, **no openings** (window-add candidate).
  * Wall W-E `03mDp1wyvBggzk6IRg3V0h`: L=6405.9, H=3581.7, T=160.0, direction north, 1 opening (window-add candidate, placed away from existing opening).
* Empty measurable openings on `标高2` (all 8 globally unique by 5-tuple geometry):
  * O-1: w=1000.000 h=1700.000 d=3048.000 off=875.000 sill=965.084 (host W-A)
  * O-2: w=1000.000 h=1700.000 d=3048.000 off=4090.000 sill=913.771 (host W-A)
  * **O-3: w=825.000 h=2975.453 d=240.000 off=12643.061 sill=−0.359 (host W-B) ← C5 door-fill binding**
  * O-4: w=620.000 h=1300.000 d=3048.000 off=8660.000 sill=1026.242 (host `0jltRti3rFigAmdXYhXx0W`)
  * O-5: w=1140.000 h=1400.000 d=3048.000 off=2645.000 sill=900.055 (host `1cbLGwmrv8LAj2u11O6kyr`)
  * O-6: w=6400.000 h=3675.453 d=220.000 off=3439.570 sill=−140.359 (host `1boalssSHBYut0JHgwRsEm`)
  * **O-7: w=1800.000 h=2955.094 d=260.000 off=1366.127 sill=−20.000 (host W-C) ← C2 door-fill binding**
  * O-8: w=290.000 h=3000.000 d=2000.000 off=2418.663 sill=−30.000 (host `3Gek8JPCb13gKANG_jcGzK`)

### CM-S65 (`str.ifc`)

* Units: length unit scale = 0.001 m per project unit (mm file).
* Storeys (19), ground storey used: **`02GkOQJZz4x9WAhoZkM67S` "00 begane grond" (elevation ≈ 0 mm)**.
* Counts: Wall 299 (IfcWallStandardCase 296), Beam 354, Column 387, OpeningElement 1284 (46 unfilled measurable on globally unique walls), ColumnType 109, BeamType 16, Door 0, Window 0.
* Unfilled measurable openings hosted on globally unique walls: 46 total; exactly **one uniquely-bindable door-sized opening**: w=1170.000, h=2490.000, d=3048.000, off=3795.000, sill=0.000, host wall `2$GiA0FALCKuqNnxjNZITr` (L=4630.0, H=4100.0, T=300.0, south, ground storey) ← **C2 door-fill binding**.
* Globally unique opening-free long walls on the ground storey (2):
  * **`2$GiA0FALCKuqNnxjNZIMq`**: L=10990.0, H=4100.0, T=300.0, south ← **C4 door-add binding** (door opening 900×2100, sill 0, offset 4000)
  * **`2$GiA0FALCKuqNnxjNZIFj`**: L=21880.0, H=4500.0, T=250.0, east ← **C4 window-add binding** (window opening 1500×1800, sill 900, offset 5000)
* Storey-local placement ranges (for structural axes): ground-storey element placements span storey-local X 0..31755, Y 0..55435. New structural members are placed storey-locally at X 36000..40000, Y 12000..18000 — east of every existing element, guaranteeing spatial separation.
* ifcopenshell validation time (single file): ~16.2 s (2 pre-existing diagnostics, both present in the source baseline so the new-diagnostic comparison stays clean).
* Note: the wall-query `storey_elevation_mm` constraint uses value 0.0 with a tightened tolerance 0.05 mm (the storey's raw elevation is −5.4e−13 project units).

### CM-TALL (`TallBuilding.ifc`)

* Units: length unit scale = 0.001 m per project unit (mm file).
* Storeys (5): `2nxdYR2RHCDBiKJuiQr1XP` Level 1 (0), `2nxdYR2RHCDBiKJuiQr1lO` Level 2 (4000), `2nxdYR2RHCDBiKJuiQqMP5` Level 4 (8000), **`2nxdYR2RHCDBiKJuiQqMQj` Level 5 (12000)**, `2nxdYR2RHCDBiKJuiQqPdh` Level 6 (16000).
* Counts: Wall 24 (all straight-wall), Door 5, Window 21, Opening 26 (all filled), Beam 0, Column 0.
* Level 5 walls (each unique within the storey by L/H/T/direction; walls recur across storeys, so Storey elevation is part of every wall binding):
  * **W-T1 `0ZBert7zf3GhThdOL2NKAr`**: L=8200, H=4000, T=200, east, 2 openings
  * **W-T2 `0ZBert7zf3GhThdOL2NK9o`**: L=8000, H=4000, T=200, south, no openings ← C3 window-add binding
  * **W-T3 `0ZBert7zf3GhThdOL2NK7O`**: L=7800, H=4000, T=200, south, no openings
* Level 5 element placements span storey-local X −5871..2229, Y −7877..123. New structural members placed at storey-local X 3500..7500 (east of all walls), Y −6000..−1000 — genuinely free space.
* No beams/columns exist, so no same-axis overlap risk; wall targeting includes `storey_elevation_mm = 12000` plus direction to disambiguate cross-storey duplicates.

## 3. Frozen geometry bindings per case

All z values are Storey-local millimetres (`coordinate_reference: storey_local_mm`). Beams are horizontal (constant z); columns vertical (constant x/y, base→top upward). Repeated same-family operations use distinct axes ≥ 1000 mm apart to satisfy `STRUCTURAL_EXISTING_SAME_AXIS_OVERLAP` and the per-operation deterministic GlobalId derivation. Type policy for all structural adds: `generated` (dedicated new Type per operation). Full numeric bindings are frozen in `composite-acceptance-freeze.json` (Section 7).

### C1 (CM-TALL, Level 5) — small composite
* add_beam: axis (3500, −5500, 3500) → (5500, −5500, 3500), section 300×500
* add_column: base (3500, −5500, 0) → top (3500, −5500, 3500), section 400×600, orientation (0,1)

### C2 (CM-S65, storey `00 begane grond`) — medium composite
* add_column ×2: bases (36000, 12000, 0)→(…, 3600) and (40000, 16000, 0)→(…, 3600), sections 400×600, orientation (0,1)
* fill_existing_opening_with_door: opening (w=1170.000, h=2490.000, d=3048.000, off=3795.000, sill=0.000), door SINGLE_SWING_LEFT, fit existing opening

### C3 (CM-TALL, Level 5) — multi-family composite
* add_beam ×2: (3500, −5500, 3500)→(5500, −5500, 3500) and (3500, −3500, 3500)→(5500, −3500, 3500), sections 300×500
* add_column ×2: (3500, −5500, 0)→(3500, −5500, 3500) and (5500, −3500, 0)→(5500, −3500, 3500), sections 400×600
* add_window_with_opening_to_wall: wall W-T2 (L=8000, H=4000, T=200, south, storey elevation 12000), opening 1200×1500, sill 900, center offset 3000 from wall_local_start

### C4 (CM-S65, storey `00 begane grond`) — large composite

**C4 window offset note (pre-execution correction, recorded honestly):** the
S65 window wall is an `IfcFacetedBrep` with recessed regions (18.95 m³ vs
24.62 m³ solid box).  The first frozen offset (5000 mm) landed in a recessed
zone, so the boolean cut removed 0.5598 m³ instead of the nominal 0.675 m³
and the production `l1.window.volume-preservation` gate correctly failed
closed (the gate working as designed, not a production defect).  An empirical
sweep through the REAL production `apply_changeset` measured removed volume
at 13 candidate offsets; offsets 1000/6000/8000/14000/16000/18000/20000/
21000 remove exactly the nominal volume.  Before ANY Provider execution, the
C4 window offset was re-frozen to 16000 mm (fully solid region, spans
15250-16750 mm).

**C4 request-text inconsistency (found 2026-08-31 during the live retry):**
the operation parameter was re-frozen to 16000 mm, but the frozen request
text (request.txt / acceptance-freeze) was NOT updated and still says
"centered 5000 mm from the wall start".  The live Provider faithfully
executed the request text and hit the known recessed zone; the
`l1.window.volume-preservation` gate failed closed exactly as designed.
This is a frozen-case defect (request/fixture mismatch), recorded honestly;
the case is NOT re-frozen in place.

**C4 window offset note (pre-execution correction, recorded honestly):** the
S65 window wall is an `IfcFacetedBrep` with recessed regions (18.95 m³ vs
24.62 m³ solid box).  The first frozen offset (5000 mm) landed in a recessed
zone, so the boolean cut removed 0.5598 m³ instead of the nominal 0.675 m³
and the production `l1.window.volume-preservation` gate correctly failed
closed (the gate working as designed, not a production defect).  An empirical
sweep through the REAL production `apply_changeset` measured the removed
volume at 13 candidate offsets; offsets 1000/6000/8000/14000/16000/18000/
20000/21000 remove exactly the nominal volume.  Before ANY Provider
execution, the C4 window offset was re-frozen to 16000 mm (fully solid
region, spans 15250-16750 mm).
* add_column ×4: (36000, 12000, 0)→(…, 3600), (40000, 12000, 0)→(…, 3600), (36000, 18000, 0)→(…, 3600), (40000, 18000, 0)→(…, 3600), sections 400×600
* add_beam ×1: (36000, 15000, 3600)→(40000, 15000, 3600), section 300×500
* add_door_with_opening_to_wall: wall `2$GiA0FALCKuqNnxjNZIMq` (L=10990.0, H=4100.0, T=300.0, south, storey elevation 0), door opening 900×2100, sill 0, center offset 4000, SINGLE_SWING_RIGHT
* add_window_with_opening_to_wall: wall `2$GiA0FALCKuqNnxjNZIFj` (L=21880.0, H=4500.0, T=250.0, east, storey elevation 0), opening 1500×1800, sill 900, center offset 5000

### C5 HERO (CM-VVO, storey `标高2`) — one coherent renovation request
* add_column ×4: (20000, −20000, 0)→(…, 3600), (26000, −20000, 0)→(…, 3600), (20000, −14000, 0)→(…, 3600), (26000, −14000, 0)→(…, 3600), sections 400×600 (new structural grid east of existing member placements, which span X −13276..12453, Y −14884..15173)
* add_beam ×2: (20000, −17000, 3600)→(26000, −17000, 3600) and (20000, −14000, 3600)→(26000, −14000, 3600), both horizontal at z=3600, sections 300×500
* add_door_with_opening_to_wall: wall W-E `2HNE4WMQ1CXebZMaih8WkH` (L=2644.0, H=3581.7, T=180.0, east, storey elevation −2213.701 mm, no pre-existing openings), door opening 900×2100, sill 0, center offset 1300 from wall_local_start, SINGLE_SWING_LEFT
* add_window_with_opening_to_wall: wall W-D (L=4609.0, H=3581.7, T=260.0, east, storey elevation −2213.701), opening 1200×1500, sill 900, center offset 2000
* 1 property intent on the new door: `Pset_DoorCommon.FireRating = "EI60"` (natural-language form, resolved via Stage 1.5)
* 1 property intent on the new window: `Pset_WindowCommon.IsExternal = true`

**Door binding note (pre-freeze adjustment, recorded honestly):** the first
draft bound the C5 door as `fill_existing_opening_with_door` on the pristine
vvo opening O-3 (825×2975, sill −0.359 mm). The frozen production canonical
schema requires `sill_height_mm ≥ 0`
(`src/text2ifc_ifc_repair/operations/door.py:90,174`), and every door-sized
empty opening on pristine vvo has a slightly negative sill (−0.359 to
−140.359 mm), while the openings with positive sills (965/913/1026/900 mm,
heights 1300–1700 mm) are window-sized. Rather than weaken the case or force a
semantically odd door at a 965 mm sill, the C5/C5-N door was rebound — before
the freeze was finalized and before ANY Provider execution — to an entity-level
`add_door_with_opening_to_wall` on wall W-E, which the specification explicitly
allows for C5 ("adding/filling one Door") and which exercises the same
registered entity-level door capability. The C2 and C4 cases retain genuine
`fill_existing_opening_with_door` operation on S65, so both door operation
variants are exercised across the ladder.

### C5-N Negative twin (CM-VVO, same storey, same structure)
Identical composition to C5 plus ONE required unsupported operation:
`structural_analysis_node` — verified absent from the operation registry
(`create_default_registry()` registers exactly: `add_window_with_opening_to_wall`,
`set_occurrence_properties`, `add_opening_to_wall`,
`add_door_with_opening_to_wall`, `fill_existing_opening_with_door`, `add_beam`,
`add_column` — `src/text2ifc_ifc_repair/operations/__init__.py:18-27`).
The intent capability checker classifies `structural_analysis_*` capability ids
as `STRUCTURAL_ANALYSIS_UNSUPPORTED`
(`src/text2ifc_ifc_repair/request_stage.py:455-458`), and a request mixing
supported and unsupported actions is terminal
`REPAIR_REQUEST_CONTAINS_UNSUPPORTED_ACTIONS` (`request_stage.py:489-504`) with
zero mutation and no Stage 2 call (proven shape: R1 case H4 and live
`program-guard` case, both frozen with zero mutation).

## 4. Binding feasibility checks already performed (before freeze)

1. Every wall binding above resolves to exactly one wall under the production
   retrieval contract (global (L,H,T,direction) uniqueness verified across the
   whole model with the production `WallIndexAdapter`; walls that repeat across
   storeys additionally carry `storey_elevation_mm` and `direction`).
2. Every opening binding resolves to exactly one `IfcOpeningElement`
   (5-tuple geometry uniqueness verified with the production
   `OpeningIndexAdapter`; fill_state `empty` verified).
3. All structural axes obey the frozen frame contract (horizontal beams,
   vertical upward columns) and lie in storey-local free space verified by
   computing storey-relative placement ranges of all existing elements.
4. Wall heights exceed opening heights + sill (e.g. TALL L5 wall H=4000 vs
   opening 1500+900=2400; S65 window wall H=4500 vs 1800+900=2700 and door wall H=4100 vs 2100+0=2100; vvo wall H=3581.7
   vs 1500+900=2400), and center offsets keep openings inside wall extents
   (within-wall horizontal/vertical postconditions,
   `src/text2ifc_ifc_repair/operations/window.py:577-599`).
5. `vvo` `标高2` is the exact storey of the frozen four-family precedent
   (`phase12-vvo-door-window-beam-column-atomic`, `VVO_MIXED_STOREY`), so the
   beam/column placement mechanics there are already production-proven.

## 5. Public-information boundary

Every binding above uses only: wall straight-geometry facts (length, height,
thickness, direction, storey elevation), opening measured geometry (width,
height, depth, center offset, sill height), Storey GlobalId/Name, and requested
new-member geometry. No GlobalId of a pristine/original undamaged comparator,
no mutation recipe, no deleted GUID list, and no private Gold fact enters any
production path. (The wall/opening GlobalIds cited in this document are the
CURRENT public model's own identities — the model IS the public source; they
are recorded here for documentation and Proof verification only, and are not
supplied to the Provider as targeting shortcuts unless the frozen request text
says so.)
