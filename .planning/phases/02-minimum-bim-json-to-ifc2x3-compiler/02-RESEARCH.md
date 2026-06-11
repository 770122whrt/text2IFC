# Phase 2 Research: Minimum BIM JSON to IFC2X3 Compiler

**Researched:** 2026-06-11
**Runtime verified:** IfcOpenShell 0.8.5
**Status:** Ready for planning

## Research Question

What is the smallest implementation that compiles canonical BIM JSON 1.0 into
reopenable, measurable, schema-valid IFC2X3 without inventing required source
facts?

## Verified Runtime Facts

1. `ifcopenshell.api.project.create_file(version="IFC2X3")` creates the target
   schema.
2. IFC2X3 authoring APIs require an `IfcPersonAndOrganization` and
   `IfcApplication`. If those entities exist, the default owner settings find
   them; no process-global monkeypatch is required.
3. Geometry API dimensions are SI metres. With an IFC millimetre unit
   assignment, `5.0` passed to a geometry API is serialized as `5000` project
   units.
4. Direct IFC length attributes use project units. Storey elevation and door
   or window `OverallWidth` / `OverallHeight` therefore receive millimetres.
5. A represented `IfcProduct` needs an `ObjectPlacement`. Assigning geometry
   without placement violates IFC2X3 `IfcProduct.WR1`.
6. `geometry.add_mesh_representation` produces an `IfcFacetedBrep` for IFC2X3
   and accepts vertices in SI metres by default.
7. `ifcopenshell.validate.validate(file, json_logger(),
   express_rules=True)` reports both required-attribute and EXPRESS-rule
   failures.
8. A local all-family spike created one of each supported IFC class and passed
   validation with zero issues after placements were assigned.

## Recommended Architecture

```text
BIM JSON mapping
  -> Phase 1 validate_document
  -> compiler bootstrap
  -> hierarchy and stable identity
  -> element class / geometry adapters
  -> selected property mapping
  -> in-memory IFC verifier
  -> temporary STEP file
  -> reopen and verify
  -> atomic destination replace
```

Use one `text2ifc_compiler` package with focused modules:

- `compiler.py`: public API, orchestration, immutable result types, atomic file
  output.
- `bootstrap.py`: IFC2X3 file, owner metadata, units, contexts, and spatial
  hierarchy.
- `identity.py`: deterministic BIM-ID-to-GlobalId conversion.
- `geometry.py`: family class table, SI conversion, minimum representations,
  placements, and measurement helpers.
- `properties.py`: standard IFC2X3 mappings and deterministic fallback pset.
- `verification.py`: normalized schema issues and public reopened-model
  inspection helpers.

The existing `scripts/ifc_pipeline/roundtrip.py` remains historical prototype
code during implementation. The canonical compiler must not call it because it
contains silent hierarchy and geometry fallbacks.

## Identity Strategy

Derive an RFC 4122 UUID with UUIDv5 from a fixed text2IFC namespace and the
tuple `(contract_version, object_kind, bim_id)`, then compress the UUID with
`ifcopenshell.guid.compress`.

This provides:

- identical GlobalIds for identical canonical inputs,
- distinct IDs for equal strings in different object domains,
- valid 22-character IFC GlobalIds,
- no dependence on serialization order or timestamps.

Store the original BIM JSON ID as `BimJsonId` in `Pset_text2IFCIdentity` on
project, site, building, storeys, and elements. Tests recover identity from the
reopened IFC, not compiler memory.

## Hierarchy and Units

Create exactly one:

`IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey[]`

Use `aggregate.assign_object` for that chain and
`spatial.assign_container` for every element. Preserve names and storey
elevations exactly. Do not create a default storey.

Assign an `IfcSIUnit` with prefix `MILLI` and name `METRE`. Centralize geometry
conversion in one `mm_to_m()` function. Direct schema attributes remain in
millimetres.

## Minimum Geometry Table

| BIM kind | IFC2X3 class | Recoverable dimensions | Representation |
|---|---|---|---|
| wall | IfcWall | length, thickness, height | rectangular solid |
| column | IfcColumn | width, depth, height | rectangular solid |
| beam | IfcBeam | length, width, height | rectangular solid |
| slab | IfcSlab | length, width, thickness | rectangular solid |
| door | IfcDoor | width, height | `OverallWidth`, `OverallHeight` |
| window | IfcWindow | width, height | `OverallWidth`, `OverallHeight` |
| stair | IfcStair | length, width, height | rectangular envelope |
| stair_flight | IfcStairFlight | run, width, rise | rectangular envelope |
| roof | IfcRoof | length, width, thickness | rectangular solid |

Phase 2 geometry is a dimension-preserving envelope, not architectural
topology. Exact placement, openings, and detailed stair shape remain Phase 4.
Deterministic synthetic X offsets keep solids separated without claiming source
placement fidelity.

Measure represented elements from tessellated geometry after reopening the IFC.
Do not assert representation internals such as `IfcRectangleProfileDef`;
IfcOpenShell may generate an arbitrary closed profile or faceted BRep while
preserving the same dimensions.

## IFC2X3 Attribute Rules

- `IfcSlab.PredefinedType` is optional and accepts standard enum values.
- `IfcRoof.ShapeType` and `IfcStair.ShapeType` are mandatory. Use a compatible
  source `predefined_type` when it is a valid IFC2X3 enum; otherwise use
  `NOTDEFINED` and preserve the original source string in the fallback pset.
- `IfcStairFlight` has no occurrence-level predefined type. Preserve the
  source value in the fallback pset.
- `IfcWall`, `IfcColumn`, and `IfcBeam` occurrences also lack a compatible
  predefined-type attribute in IFC2X3.
- Door and window occurrence dimensions are optional positive length
  attributes and can preserve the required two-dimensional contract without
  inventing thickness.

## Selected Property Mapping

Use standard common psets when compatible:

- `is_external` -> `IsExternal`
- `load_bearing` -> `LoadBearing`

Use exact Python booleans. For `predefined_type`, set a compatible occurrence
attribute where IFC2X3 provides one, and always preserve the original string as
`PredefinedType` in `Pset_text2IFCProperties`. This guarantees round-trip
retrieval even when IFC enum vocabularies differ from future contract values.

Do not stringify booleans or coerce source strings.

## Verification Design

`verification.py` should expose:

- normalized `IfcValidationIssue` records,
- schema verification for an in-memory file or path,
- hierarchy and containment inspection,
- BIM ID / GlobalId inspection,
- family dimension measurement from reopened IFC.

Normalize validator output to stable project codes and deterministic ordering;
do not expose raw memory addresses or unstable entity formatting in tests.

The compiler verifies in memory, writes a sibling temporary file, reopens and
verifies that file, and only then calls `os.replace`. Validation failure removes
the temporary file and leaves an existing destination byte-for-byte unchanged.

## Implementation Risks

1. Mixing SI geometry inputs with millimetre schema attributes can create
   1000x errors. Keep conversion at named boundaries.
2. Missing placement on represented products creates schema-invalid IFC.
3. `IfcRoof` and `IfcStair` mandatory shape enums need explicit handling.
4. Testing profile implementation details makes tests brittle; use reopened
   geometry bounds.
5. The validator can be expensive on adversarially large inputs. Retain the
   Phase 1 bounded file CLI and add compiler element and output limits before
   deployment work.
6. Direct writes can corrupt or overwrite a valid prior artifact. Use sibling
   temporary files and atomic replacement.

## Proven Spike

The local spike used the installed 0.8.5 APIs to create:

- one project, site, building, and storey,
- one each of `IfcWall`, `IfcColumn`, `IfcBeam`, `IfcSlab`, `IfcDoor`,
  `IfcWindow`, `IfcStair`, `IfcStairFlight`, and `IfcRoof`,
- millimetre units and SI mesh inputs,
- spatial containment and placements for represented elements.

After STEP serialization and reopen:

- schema was `IFC2X3`,
- every class count was one,
- `ifcopenshell.validate` with EXPRESS rules produced zero issues.

An intentionally incomplete raw `IfcRoof` produced required-attribute issues,
proving the negative validation path.

## Planning Consequences

1. Build boundary, hierarchy, identity, verification, and atomic output first.
2. Add measurable all-family geometry second.
3. Add selected-property mappings independently in the same wave as geometry.
4. Finish with reopened end-to-end acceptance, CLI, documentation, and full
   regression.

