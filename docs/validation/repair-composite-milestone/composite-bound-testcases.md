# Composite Bound Test Cases — Text2IFC Composite Repair Milestone

**Status:** frozen at base revision `8bfcfe075521ddb142f8608296dfbfea1fd385e4` (branch `Zcode`).

Machine-readable twin: `composite-acceptance-freeze.json` (sha256 `bd2867affd95cb95801e1edc174ece3f1c971ebe90885dab8e302a0a12c4d76d`). Case meaning does not change after genuine execution begins.

## Execution order

`C1 → C2 → C3 → C4 → C5 → C5-N`

## C1 — small composite (CM-TALL)

**Storey:** `2nxdYR2RHCDBiKJuiQqMQj` (Level 5)

**Target operation count:** 2 (families: beam, column; property intents: 0)

**Exact frozen request:**

> Renovate Level 5 of this building with a small structural addition in one atomic ChangeSet: add one horizontal straight rectangular Beam with center axis from (3500, -5500, 3500) mm to (5500, -5500, 3500) mm and a rectangular section 300 mm wide and 500 mm high, and add one vertical straight rectangular Column with center-axis base (3500, -5500, 0) mm and top (3500, -5500, 3500) mm, a section 400 mm wide and 600 mm deep, with local width direction (0, 1). Create both on the IFC Building Storey named "Level 5", generate a dedicated structural Type for each, and publish both modifications as one atomic transaction.

**Request SHA-256:** `7709cd81ec0beec2e94c7f3da9622fa8b1e8ed724143d8fd8f12e8dcb65eb07d`

**Frozen operation bindings:**

| operation_id | operation_type | frozen binding |
| --- | --- | --- |
| `C1-beam-01` | `add_beam` | `{"axis": {"start": {"x_mm": 3500, "y_mm": -5500, "z_mm": 3500}, "end": {"x_mm": 5500, "y_mm": -5500, "z_mm": 3500}}, "section": {"shape": "rectangle", "width_mm…` |
| `C1-column-01` | `add_column` | `{"axis": {"base": {"x_mm": 3500, "y_mm": -5500, "z_mm": 0}, "top": {"x_mm": 3500, "y_mm": -5500, "z_mm": 3500}}, "section": {"shape": "rectangle", "width_mm": 4…` |

**Expected terminal class:** `SUCCESS`

**Atomicity:** all_or_nothing

**Expected entity delta:** `IfcBeam` +1, `IfcColumn` +1, `IfcBeamType` +1, `IfcColumnType` +1

**Type policy:** generated

**Property resolution involved:** False

**Provider stages expected:** stage1, stage2

**Reopen:** IFC2X3 reopen + L0/L1/L2 recompute

**Preservation:** whole-model exact authorized delta only

**Operation-bound artifact predicates:**

| predicate_id | operation_id | operation_type | kind |
| --- | --- | --- | --- |
| `C1-C1-beam-01` | `C1-beam-01` | `add_beam` | `structural_add` |
| `C1-C1-column-01` | `C1-column-01` | `add_column` | `structural_add` |
| `C1-atomic` | `—` | `—` | `atomic_operation_set` |

## C2 — medium composite (CM-S65)

**Storey:** `02GkOQJZz4x9WAhoZkM67S` (00 begane grond)

**Target operation count:** 3 (families: column, door; property intents: 0)

**Exact frozen request:**

> On the ground floor storey "00 begane grond" of this building, complete a structural and envelope repair in one atomic ChangeSet: add two vertical straight rectangular Columns with center-axis base (36000, 12000, 0) mm and top (36000, 12000, 3600) mm, and base (40000, 16000, 0) mm and top (40000, 16000, 3600) mm respectively, each with a section 400 mm wide and 600 mm deep and local width direction (0, 1), generating a dedicated structural Type for each; and fill the currently empty wall opening that is 1170.000 mm wide, 2490.000 mm high, 3048.000 mm deep, with wall-local center offset 3795.000 mm and sill height 0.000 mm, by installing a SINGLE_SWING_LEFT door that fits that existing opening exactly, generating its door Type. All three modifications are mandatory and must be published as one atomic transaction.

**Request SHA-256:** `d0a6e7815c28c1dbe3dd4fe7e8ecb2004bfe0e4901d85eb67c1929fea5485447`

**Frozen operation bindings:**

| operation_id | operation_type | frozen binding |
| --- | --- | --- |
| `C2-column-01` | `add_column` | `{"axis": {"base": {"x_mm": 36000, "y_mm": 12000, "z_mm": 0}, "top": {"x_mm": 36000, "y_mm": 12000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm":…` |
| `C2-column-02` | `add_column` | `{"axis": {"base": {"x_mm": 40000, "y_mm": 16000, "z_mm": 0}, "top": {"x_mm": 40000, "y_mm": 16000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm":…` |
| `C2-door-01` | `fill_existing_opening_with_door` | `{"fit_existing_opening": true, "door": {"formal_enum_explicit": true, "operation_type": "SINGLE_SWING_LEFT"}}` |

**Expected terminal class:** `SUCCESS`

**Atomicity:** all_or_nothing

**Expected entity delta:** `IfcColumn` +2, `IfcDoor` +1, `IfcColumnType` +2, `IfcDoorStyle` +1

**Type policy:** generated

**Property resolution involved:** False

**Provider stages expected:** stage1, stage2

**Reopen:** IFC2X3 reopen + L0/L1/L2 recompute

**Preservation:** whole-model exact authorized delta only

**Operation-bound artifact predicates:**

| predicate_id | operation_id | operation_type | kind |
| --- | --- | --- | --- |
| `C2-C2-column-01` | `C2-column-01` | `add_column` | `structural_add` |
| `C2-C2-column-02` | `C2-column-02` | `add_column` | `structural_add` |
| `C2-C2-door-01` | `C2-door-01` | `fill_existing_opening_with_door` | `door_fill` |
| `C2-atomic` | `—` | `—` | `atomic_operation_set` |

## C3 — multi-family composite (CM-TALL)

**Storey:** `2nxdYR2RHCDBiKJuiQqMQj` (Level 5)

**Target operation count:** 5 (families: beam, column, window; property intents: 0)

**Exact frozen request:**

> Renovate Level 5 of this building in one atomic ChangeSet: add two horizontal straight rectangular Beams with center axes from (3500, -5500, 3500) mm to (5500, -5500, 3500) mm and from (3500, -3500, 3500) mm to (5500, -3500, 3500) mm, each with a rectangular section 300 mm wide and 500 mm high; add two vertical straight rectangular Columns with center-axis bases (3500, -5500, 0) mm and (5500, -3500, 0) mm and tops (3500, -5500, 3500) mm and (5500, -3500, 3500) mm respectively, each with a section 400 mm wide and 600 mm deep and local width direction (0, 1); and add one new Window with its opening on the straight wall on this storey that runs south, is 8000 mm long, 4000 mm high and 200 mm thick (storey elevation 12000 mm), placing the window opening 1200 mm wide and 1500 mm high with a 900 mm sill, centered 3000 mm from the wall start. Generate dedicated Types for every new element. All five modifications are mandatory and must be published as one atomic transaction.

**Request SHA-256:** `0fefa9f76de69947e64044178f78f445dbeec6ffc801999594972a6ecfc3fc5f`

**Frozen operation bindings:**

| operation_id | operation_type | frozen binding |
| --- | --- | --- |
| `C3-beam-01` | `add_beam` | `{"axis": {"start": {"x_mm": 3500, "y_mm": -5500, "z_mm": 3500}, "end": {"x_mm": 5500, "y_mm": -5500, "z_mm": 3500}}, "section": {"shape": "rectangle", "width_mm…` |
| `C3-beam-02` | `add_beam` | `{"axis": {"start": {"x_mm": 3500, "y_mm": -3500, "z_mm": 3500}, "end": {"x_mm": 5500, "y_mm": -3500, "z_mm": 3500}}, "section": {"shape": "rectangle", "width_mm…` |
| `C3-column-01` | `add_column` | `{"axis": {"base": {"x_mm": 3500, "y_mm": -5500, "z_mm": 0}, "top": {"x_mm": 3500, "y_mm": -5500, "z_mm": 3500}}, "section": {"shape": "rectangle", "width_mm": 4…` |
| `C3-column-02` | `add_column` | `{"axis": {"base": {"x_mm": 5500, "y_mm": -3500, "z_mm": 0}, "top": {"x_mm": 5500, "y_mm": -3500, "z_mm": 3500}}, "section": {"shape": "rectangle", "width_mm": 4…` |
| `C3-window-01` | `add_window_with_opening_to_wall` | `{"position": {"reference": "wall_local_start", "center_offset_mm": 3000}, "opening": {"width_mm": 1200, "height_mm": 1500, "sill_height_mm": 900}, "window": {"f…` |

**Expected terminal class:** `SUCCESS`

**Atomicity:** all_or_nothing

**Expected entity delta:** `IfcBeam` +2, `IfcColumn` +2, `IfcWindow` +1, `IfcBeamType` +2, `IfcColumnType` +2, `IfcWindowStyle` +1, `IfcOpeningElement` +1

**Type policy:** generated

**Property resolution involved:** False

**Provider stages expected:** stage1, stage2

**Reopen:** IFC2X3 reopen + L0/L1/L2 recompute

**Preservation:** whole-model exact authorized delta only

**Operation-bound artifact predicates:**

| predicate_id | operation_id | operation_type | kind |
| --- | --- | --- | --- |
| `C3-C3-beam-01` | `C3-beam-01` | `add_beam` | `structural_add` |
| `C3-C3-beam-02` | `C3-beam-02` | `add_beam` | `structural_add` |
| `C3-C3-column-01` | `C3-column-01` | `add_column` | `structural_add` |
| `C3-C3-column-02` | `C3-column-02` | `add_column` | `structural_add` |
| `C3-C3-window-01` | `C3-window-01` | `add_window_with_opening_to_wall` | `window_add` |
| `C3-atomic` | `—` | `—` | `atomic_operation_set` |

## C4 — large composite (CM-S65)

**Storey:** `02GkOQJZz4x9WAhoZkM67S` (00 begane grond)

**Target operation count:** 7 (families: beam, column, door, window; property intents: 0)

**Exact frozen request:**

> On the ground floor storey "00 begane grond" of this building, build one local structural and envelope modification in a single atomic ChangeSet: add four vertical straight rectangular Columns with center-axis base/top pairs (36000, 12000, 0)-(36000, 12000, 3600) mm, (40000, 12000, 0)-(40000, 12000, 3600) mm, (36000, 18000, 0)-(36000, 18000, 3600) mm and (40000, 18000, 0)-(40000, 18000, 3600) mm, each with a section 400 mm wide and 600 mm deep and local width direction (0, 1); add one horizontal straight rectangular Beam with center axis from (36000, 15000, 3600) mm to (40000, 15000, 3600) mm and a rectangular section 300 mm wide and 500 mm high; on the straight wall on this storey that runs south, is 10990.0 mm long, 4100.0 mm high and 300.0 mm thick (storey elevation 0 mm), add one new door with its opening, placing the door opening 900 mm wide and 2100 mm high with a 0 mm sill, centered 4000 mm from the wall start, using a SINGLE_SWING_RIGHT door; and add one new Window with its opening on the straight wall on this storey that runs east, is 21880.0 mm long, 4500.0 mm high and 250.0 mm thick (storey elevation 0 mm), placing the window opening 1500 mm wide and 1800 mm high with a 900 mm sill, centered 5000 mm from the wall start. Generate dedicated Types for every new element. All seven modifications are mandatory and must be published as one atomic transaction.

**Request SHA-256:** `00186cfbd69419440aa45f450a74cf95fafe6c605755c73a86d1db132ee83844`

**Frozen operation bindings:**

| operation_id | operation_type | frozen binding |
| --- | --- | --- |
| `C4-column-01` | `add_column` | `{"axis": {"base": {"x_mm": 36000, "y_mm": 12000, "z_mm": 0}, "top": {"x_mm": 36000, "y_mm": 12000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm":…` |
| `C4-column-02` | `add_column` | `{"axis": {"base": {"x_mm": 40000, "y_mm": 12000, "z_mm": 0}, "top": {"x_mm": 40000, "y_mm": 12000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm":…` |
| `C4-column-03` | `add_column` | `{"axis": {"base": {"x_mm": 36000, "y_mm": 18000, "z_mm": 0}, "top": {"x_mm": 36000, "y_mm": 18000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm":…` |
| `C4-column-04` | `add_column` | `{"axis": {"base": {"x_mm": 40000, "y_mm": 18000, "z_mm": 0}, "top": {"x_mm": 40000, "y_mm": 18000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm":…` |
| `C4-beam-01` | `add_beam` | `{"axis": {"start": {"x_mm": 36000, "y_mm": 15000, "z_mm": 3600}, "end": {"x_mm": 40000, "y_mm": 15000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_…` |
| `C4-door-01` | `add_door_with_opening_to_wall` | `{"position": {"reference": "wall_local_start", "center_offset_mm": 4000}, "opening": {"width_mm": 900, "height_mm": 2100, "sill_height_mm": 0, "dimension_meanin…` |
| `C4-window-01` | `add_window_with_opening_to_wall` | `{"position": {"reference": "wall_local_start", "center_offset_mm": 16000}, "opening": {"width_mm": 1500, "height_mm": 1800, "sill_height_mm": 900}, "window": {"…` |

**Expected terminal class:** `SUCCESS`

**Atomicity:** all_or_nothing

**Expected entity delta:** `IfcBeam` +1, `IfcColumn` +4, `IfcDoor` +1, `IfcWindow` +1, `IfcBeamType` +1, `IfcColumnType` +4, `IfcDoorStyle` +1, `IfcWindowStyle` +1, `IfcOpeningElement` +2

**Type policy:** generated

**Property resolution involved:** False

**Provider stages expected:** stage1, stage2

**Reopen:** IFC2X3 reopen + L0/L1/L2 recompute

**Preservation:** whole-model exact authorized delta only

**Operation-bound artifact predicates:**

| predicate_id | operation_id | operation_type | kind |
| --- | --- | --- | --- |
| `C4-C4-column-01` | `C4-column-01` | `add_column` | `structural_add` |
| `C4-C4-column-02` | `C4-column-02` | `add_column` | `structural_add` |
| `C4-C4-column-03` | `C4-column-03` | `add_column` | `structural_add` |
| `C4-C4-column-04` | `C4-column-04` | `add_column` | `structural_add` |
| `C4-C4-beam-01` | `C4-beam-01` | `add_beam` | `structural_add` |
| `C4-C4-door-01` | `C4-door-01` | `add_door_with_opening_to_wall` | `door_add` |
| `C4-C4-window-01` | `C4-window-01` | `add_window_with_opening_to_wall` | `window_add` |
| `C4-atomic` | `—` | `—` | `atomic_operation_set` |

## C5 — hero composite (CM-VVO)

**Storey:** `1vTeahUkP60PdWqwCTjSGJ` (标高2)

**Target operation count:** 8 (families: beam, column, door, window; property intents: 2)

**Exact frozen request:**

> Renovate one defined region of the storey named "标高2" of this building as a single atomic ChangeSet. Structural part: add four vertical straight rectangular Columns with center-axis base/top pairs (20000, -20000, 0)-(20000, -20000, 3600) mm, (26000, -20000, 0)-(26000, -20000, 3600) mm, (20000, -14000, 0)-(20000, -14000, 3600) mm and (26000, -14000, 0)-(26000, -14000, 3600) mm, each with a section 400 mm wide and 600 mm deep and local width direction (0, 1); and add two horizontal straight rectangular Beams with center axes from (20000, -17000, 3600) mm to (26000, -17000, 3600) mm and from (20000, -14000, 3600) mm to (26000, -14000, 3600) mm, each with a rectangular section 300 mm wide and 500 mm high. Envelope part: on the straight wall on this storey that runs east, is 2644.0 mm long, 3581.7 mm high and 180.0 mm thick (storey elevation -2213.701 mm), add one new door with its opening, placing the door opening 900 mm wide and 2100 mm high with a 0 mm sill, centered 1300 mm from the wall start, using a SINGLE_SWING_LEFT door, and set that new door's fire rating to EI60; and add one new Window with its opening on the straight wall on this storey that runs east, is 4609.0 mm long, 3581.7 mm high and 260.0 mm thick (storey elevation -2213.701 mm), placing the window opening 1200 mm wide and 1500 mm high with a 900 mm sill, centered 2000 mm from the wall start, and mark that new window as an external window. Generate dedicated Types for every new element. All these modifications are mandatory and must be published together as one atomic transaction.

**Request SHA-256:** `6dc1b40ef91afd9c02aad6c67397a0bf4b33c6ae76b5e533a8478b4c0bb36ec9`

**Frozen operation bindings:**

| operation_id | operation_type | frozen binding |
| --- | --- | --- |
| `C5-column-01` | `add_column` | `{"axis": {"base": {"x_mm": 20000, "y_mm": -20000, "z_mm": 0}, "top": {"x_mm": 20000, "y_mm": -20000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-column-02` | `add_column` | `{"axis": {"base": {"x_mm": 26000, "y_mm": -20000, "z_mm": 0}, "top": {"x_mm": 26000, "y_mm": -20000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-column-03` | `add_column` | `{"axis": {"base": {"x_mm": 20000, "y_mm": -14000, "z_mm": 0}, "top": {"x_mm": 20000, "y_mm": -14000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-column-04` | `add_column` | `{"axis": {"base": {"x_mm": 26000, "y_mm": -14000, "z_mm": 0}, "top": {"x_mm": 26000, "y_mm": -14000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-beam-01` | `add_beam` | `{"axis": {"start": {"x_mm": 20000, "y_mm": -17000, "z_mm": 3600}, "end": {"x_mm": 26000, "y_mm": -17000, "z_mm": 3600}}, "section": {"shape": "rectangle", "widt…` |
| `C5-beam-02` | `add_beam` | `{"axis": {"start": {"x_mm": 20000, "y_mm": -14000, "z_mm": 3600}, "end": {"x_mm": 26000, "y_mm": -14000, "z_mm": 3600}}, "section": {"shape": "rectangle", "widt…` |
| `C5-door-01` | `add_door_with_opening_to_wall` | `{"position": {"reference": "wall_local_start", "center_offset_mm": 1300}, "opening": {"width_mm": 900, "height_mm": 2100, "sill_height_mm": 0, "dimension_meanin…` |
| `C5-window-01` | `add_window_with_opening_to_wall` | `{"position": {"reference": "wall_local_start", "center_offset_mm": 2000}, "opening": {"width_mm": 1200, "height_mm": 1500, "sill_height_mm": 900}, "window": {"f…` |

**Expected terminal class:** `SUCCESS`

**Atomicity:** all_or_nothing

**Expected entity delta:** `IfcBeam` +2, `IfcColumn` +4, `IfcDoor` +1, `IfcWindow` +1, `IfcBeamType` +2, `IfcColumnType` +4, `IfcDoorStyle` +1, `IfcWindowStyle` +1, `IfcOpeningElement` +2

**Type policy:** generated

**Property resolution involved:** True

**Provider stages expected:** stage1, property_resolution, stage2

**Reopen:** IFC2X3 reopen + L0/L1/L2 recompute

**Preservation:** whole-model exact authorized delta only

**Operation-bound artifact predicates:**

| predicate_id | operation_id | operation_type | kind |
| --- | --- | --- | --- |
| `C5-C5-column-01` | `C5-column-01` | `add_column` | `structural_add` |
| `C5-C5-column-02` | `C5-column-02` | `add_column` | `structural_add` |
| `C5-C5-column-03` | `C5-column-03` | `add_column` | `structural_add` |
| `C5-C5-column-04` | `C5-column-04` | `add_column` | `structural_add` |
| `C5-C5-beam-01` | `C5-beam-01` | `add_beam` | `structural_add` |
| `C5-C5-beam-02` | `C5-beam-02` | `add_beam` | `structural_add` |
| `C5-C5-door-01` | `C5-door-01` | `add_door_with_opening_to_wall` | `door_add` |
| `C5-C5-window-01` | `C5-window-01` | `add_window_with_opening_to_wall` | `window_add` |
| `C5-C5-door-01-property` | `C5-door-01` | `add_door_with_opening_to_wall` | `generated_occurrence_property` |
| `C5-C5-window-01-property` | `C5-window-01` | `add_window_with_opening_to_wall` | `generated_occurrence_property` |
| `C5-atomic` | `—` | `—` | `atomic_operation_set` |

## C5-N — hero-negative composite (CM-VVO)

**Storey:** `1vTeahUkP60PdWqwCTjSGJ` (标高2)

**Target operation count:** 8 (families: beam, column, door, window; property intents: 2)

**Exact frozen request:**

> Renovate one defined region of the storey named "标高2" of this building as a single atomic ChangeSet. Structural part: add four vertical straight rectangular Columns with center-axis base/top pairs (20000, -20000, 0)-(20000, -20000, 3600) mm, (26000, -20000, 0)-(26000, -20000, 3600) mm, (20000, -14000, 0)-(20000, -14000, 3600) mm and (26000, -14000, 0)-(26000, -14000, 3600) mm, each with a section 400 mm wide and 600 mm deep and local width direction (0, 1); and add two horizontal straight rectangular Beams with center axes from (20000, -17000, 3600) mm to (26000, -17000, 3600) mm and from (20000, -14000, 3600) mm to (26000, -14000, 3600) mm, each with a rectangular section 300 mm wide and 500 mm high. Envelope part: on the straight wall on this storey that runs east, is 2644.0 mm long, 3581.7 mm high and 180.0 mm thick (storey elevation -2213.701 mm), add one new door with its opening, placing the door opening 900 mm wide and 2100 mm high with a 0 mm sill, centered 1300 mm from the wall start, using a SINGLE_SWING_LEFT door, and set that new door's fire rating to EI60; and add one new Window with its opening on the straight wall on this storey that runs east, is 4609.0 mm long, 3581.7 mm high and 260.0 mm thick (storey elevation -2213.701 mm), placing the window opening 1200 mm wide and 1500 mm high with a 900 mm sill, centered 2000 mm from the wall start, and mark that new window as an external window. Additionally, create a structural analysis node for this renovation. All these modifications are mandatory and must be published together as one atomic transaction.

**Request SHA-256:** `357ddbeb1f17b463a2d00a9c2a9f1ec503f78b45bcca58fdb2de64e23809ab76`

**Frozen operation bindings:**

| operation_id | operation_type | frozen binding |
| --- | --- | --- |
| `C5-column-01` | `add_column` | `{"axis": {"base": {"x_mm": 20000, "y_mm": -20000, "z_mm": 0}, "top": {"x_mm": 20000, "y_mm": -20000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-column-02` | `add_column` | `{"axis": {"base": {"x_mm": 26000, "y_mm": -20000, "z_mm": 0}, "top": {"x_mm": 26000, "y_mm": -20000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-column-03` | `add_column` | `{"axis": {"base": {"x_mm": 20000, "y_mm": -14000, "z_mm": 0}, "top": {"x_mm": 20000, "y_mm": -14000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-column-04` | `add_column` | `{"axis": {"base": {"x_mm": 26000, "y_mm": -14000, "z_mm": 0}, "top": {"x_mm": 26000, "y_mm": -14000, "z_mm": 3600}}, "section": {"shape": "rectangle", "width_mm…` |
| `C5-beam-01` | `add_beam` | `{"axis": {"start": {"x_mm": 20000, "y_mm": -17000, "z_mm": 3600}, "end": {"x_mm": 26000, "y_mm": -17000, "z_mm": 3600}}, "section": {"shape": "rectangle", "widt…` |
| `C5-beam-02` | `add_beam` | `{"axis": {"start": {"x_mm": 20000, "y_mm": -14000, "z_mm": 3600}, "end": {"x_mm": 26000, "y_mm": -14000, "z_mm": 3600}}, "section": {"shape": "rectangle", "widt…` |
| `C5-door-01` | `add_door_with_opening_to_wall` | `{"position": {"reference": "wall_local_start", "center_offset_mm": 1300}, "opening": {"width_mm": 900, "height_mm": 2100, "sill_height_mm": 0, "dimension_meanin…` |
| `C5-window-01` | `add_window_with_opening_to_wall` | `{"position": {"reference": "wall_local_start", "center_offset_mm": 2000}, "opening": {"width_mm": 1200, "height_mm": 1500, "sill_height_mm": 900}, "window": {"f…` |
| `C5N-analysis-node-01` | `structural_analysis_node` | UNSUPPORTED (verified absent from registry) |

**Expected terminal class:** `UNSUPPORTED_ATOMIC_GUARD`

**Atomicity:** all_or_nothing

**Expected entity delta:** `IfcBeam` +2, `IfcColumn` +4, `IfcDoor` +1, `IfcWindow` +1, `IfcBeamType` +2, `IfcColumnType` +4, `IfcDoorStyle` +1, `IfcWindowStyle` +1, `IfcOpeningElement` +2

**Type policy:** generated

**Property resolution involved:** True

**Provider stages expected:** stage1

**Reopen:** zero model mutation (no publication)

**Preservation:** byte-identical source; no candidate output

**Operation-bound artifact predicates:**

| predicate_id | operation_id | operation_type | kind |
| --- | --- | --- | --- |

