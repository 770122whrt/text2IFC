# BIM JSON 2.6: parameterized door/window components

This version adds `component_geometry` to occurrence `Representation`. The 2.5
material-list, polygon-wall, basic-filling and railing contracts remain available.
Generation/Brief integration is a separate execution stage; this schema alone is
not evidence of a working natural-language loop.

```json
{
  "kind": "component_geometry",
  "geometry_version": "text2ifc/components/1.0",
  "definitions": [{
    "id": "panel-solid",
    "profile": {"kind": "rectangle", "x": 800, "y": 2000},
    "position": {"origin": [0, 0, 0], "axis": [0, 0, 1], "ref_direction": [1, 0, 0]},
    "direction": [0, 0, 1], "depth": 40
  }],
  "parts": [{
    "id": "panel", "role": "panel", "geometry_refs": ["panel-solid"],
    "placement": {"origin": [0, 0, 0], "axis": [0, 0, 1], "ref_direction": [1, 0, 0]},
    "appearance": {"color": [0.6, 0.4, 0.2], "transparency": 0}
  }]
}
```

All lengths are millimetres. This example's profile lies in local XY and extrudes
along local Z: installation orientation must be supplied explicitly. Rectangle
and circle profiles are centered at the profile origin. Polygon coordinates are
explicit closed rings, with optional `holes`; no implicit recentering occurs.

- Each definition is one straight extrusion, using rectangle, circle (`radius`)
  or polygon (`points`, optional `holes`). Both part placement and solid position
  are required. Coordinates compose as product × part × solid exactly once.
- Definitions are local to the parent product and reused only by reference.
  Each referenced use creates a separate solid. Every definition must be used.
- A part may contain several definitions. The part ID survives IFC reopening as
  `IfcShapeAspect.Name`. Its versioned role is stored in Description. Solids are
  linked through real ShapeRepresentations, not only property metadata.
- Optional `repeat: {"count": 14, "step": [0,0,70]}` expands part IDs to
  `id-001` through `id-014`. Step is a translation in the product frame, applied
  to the initial part origin. Zero step and ID collisions are rejected. For a
  subsequent per-instance edit, first materialize the repeated parts explicitly.
- Runtime limits: 512 expanded parts, 2,048 solids, 32 geometry references per
  part, 512 definitions, 257 points per ring, 16 holes. An offline capacity probe
  compiled and reopened both 128 parts/512 solids and 512 parts/2,048 solids;
  these are resource bounds, not an LLM output-capacity claim.
- Part RGB and transparency override occurrence display, then Type display,
  then the ordinary theme. Part appearance supplies both channels. It does not
  assign physical material to the part. Existing whole-product material remains
  independent.
- Only IfcDoor/IfcWindow occurrences use this representation. It is incompatible
  with template fields. No new building products are created for handles/slats.
- Nominal OverallWidth/OverallHeight stay on the product; exterior handles do
  not resize them. Host/opening installation is evaluated in a later stage.
- Unsupported input, unresolved references, invalid profiles and invalid
  coordinate systems fail validation. No template or bounding-box substitution.
  The source reader currently refuses BRep, composite curves, scaled/reflected
  mappings and non-IFC2X3 files. Curved composite profiles require a separate
  scope decision.

The compiler checks actual reopened solids, profiles, holes, placements, part
ownership, nominal dimensions and styles before atomic publication. Its numeric
precision checks deterministic compilation; source roundtrip comparison uses
the separately agreed **1 mm** linear acceptance tolerance.

Explicit version rollback keeps 2.5 as a separate selectable contract: old
templates still compile, and 2.5 refuses component geometry.
