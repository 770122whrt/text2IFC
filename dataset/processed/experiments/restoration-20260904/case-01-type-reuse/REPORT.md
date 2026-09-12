# Case 01 — Exact Type Reuse Restoration

Status: **PASS**

## Chain

`original.ifc -> deterministic Beam removal -> damaged.ifc -> genuine RepairAPI -> repaired.ifc`

## Restored Beam

- Original deleted Beam: `17tPjyQtf2L9JnbXXmcTUF`
- Repaired Beam: `2fpFNCl9LSbwu0tCr6UKVd`
- Exact reused IfcBeamType: `17tPjyQtf2L9JnbXXmcTTd`
- Storey: `1vTeahUkP60PdWqwCTjUuM`
- Section: `455 x 570 mm`
- Corrected Storey-local center axis: `(-3316.629521, -3863.522838, -285)` to `(-3316.629521, -8803.522838, -285)` mm

The source IFC diagnostic Axis representation lies on the top face of this Beam and was initially mistaken for the Body centroid line. The final accepted run corrects only the public input center-axis Z from `0` to `-285 mm`; Beam authoring code is unchanged.

## Validation

- Original world Body bbox Z: `798 .. 1368 mm`
- Repaired world Body bbox Z: `798 .. 1368 mm`
- Maximum world bbox error: approximately `2.63e-7 mm` (< `0.01 mm` tolerance)
- Exact Type reuse: PASS
- IFC2X3 schema preserved: PASS
- Repository `compare_ifc_models` authorized-scope comparison: `unexpected_changed_ids=[]`
- `complete_preservation_success=true`

Only the final corrected live evidence is retained under `evidence/live/`; the superseded Z=0 run and pytest temporary directories were removed during closure.
