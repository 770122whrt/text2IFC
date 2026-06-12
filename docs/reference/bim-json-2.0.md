<!-- Generated from canonical BIM JSON schemas. Do not edit. -->
<!-- Regenerate with: python scripts/bim_json_v2/generate_reference.py -->

# BIM JSON 2.0 Contract Reference

Canonical semantic input and extraction-label contract for text2IFC.

## Document Kinds

### Formal

A Formal document has `schema_version` `bim-json/2.0` and is complete,
validated, capability-gated, and ready for deterministic IFC compilation.
Its required root fields are `schema_version`, `ifc_schema`, `units`, `entities`, `relationships`, `provenance`. The target IFC
schema is `IFC2X3` and length values use millimetres.

### Draft Envelope

A Draft Envelope is separate from Formal BIM JSON. Its required fields are
`draft_version`, `target_schema_version`, `partial_document`, `missing_facts`, `losses`, `clarification_targets`, `provenance`. It preserves partial facts while listing every
known missing fact, unsupported source loss, clarification target, and
provenance record. Drafts cannot enter the IFC compiler.

## Semantic Records

`entities` contains user-meaningful IFC objects. Every entity requires
`id`, `ifc_class`, `attributes`, `property_sets`, `provenance`. `ifc_class` uses the exact IFC2X3 class name,
for example `IfcWall`, `IfcWallStandardCase`, or `IfcSpace`.

`relationships` contains user-meaningful IFC relationships. Every relationship
requires `id`, `ifc_class`, `attributes`, `provenance`. The initial explicit relation
profile contains `IfcRelVoidsElement` and `IfcRelFillsElement`.

Source IFC `GlobalId` values may be preserved in `global_id`. Stable semantic
`id` values remain separate and never use STEP line numbers.

## Placement

`ObjectPlacement` is a bounded parent-relative semantic placement requiring
`relative_to`, `origin`, `axis`, `ref_direction`. `relative_to` names the parent semantic
entity. World transforms are derived deterministically and are not canonical
input.

`Representation.position` is an optional geometry-local position requiring
`origin`, `axis`, `ref_direction`. It maps to
`IfcExtrudedAreaSolid.Position` and is independent from product
`ObjectPlacement`.

## Geometry

The Formal generation profile supports `extruded_profile` representations.
The schema requires `kind` at the generic
representation level; semantic validation additionally requires `profile`,
`depth`, and `direction` for an extrusion.

Supported profiles are positive rectangles and finite closed polygons.
Mapped geometry, BRep, boolean, surface, tessellated, and other unsupported
representations remain explicit Draft losses. They are never replaced with
boxes or proxies.

## Properties

Native IFC attributes retain canonical IFC2X3 names and registry-validated
types. Official property sets and properties use their buildingSMART names.
Project-specific sets remain explicitly custom and are not presented as
official definitions.

## Compiler Boundary

The model emits semantic classes, attributes, placement, geometry, properties,
and user relationships. The compiler creates `IfcCartesianPoint`,
`IfcDirection`, `IfcLocalPlacement`, `IfcOwnerHistory`, representation
resources, containment, aggregation, and property attachments.

Exact `IfcWallStandardCase` is retained. IFC2X3 requires a material layer-set
usage for this exact subtype, so the compiler creates the minimum technical
attachment from the supplied wall profile without claiming a source material
composition.

## Commands

```powershell
python scripts/bim_json_v2/validate.py INPUT.json
python scripts/bim_json_v2/migrate_v1.py INPUT.json OUTPUT.json
python scripts/ifc_pipeline_v2/extract.py INPUT.ifc OUTPUT.json
python scripts/bim_json/compile_ifc.py INPUT.json OUTPUT.ifc
python scripts/bim_json_v2/generate_reference.py --check
```
