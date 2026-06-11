# IFC2X3 Knowledge Sources

This document defines the source precedence for text2IFC's deterministic
IFC2X3 knowledge registry. It also separates schema knowledge that may be
downloaded from facts about a particular building that must never be guessed.

## Source Precedence

1. **IFC2X3 TC1 EXPRESS** defines declarations, inheritance, attributes,
   selects, enumerations, inverse attributes, and formal rules.
2. **IFC2X3 official PSD XML** defines standard property-set and property
   metadata.
3. **IFC2X3 XSD** supports ifcXML compatibility checks; it does not replace
   EXPRESS.
4. **IFC2X3 official HTML** supplies human-readable definitions and release
   documentation.
5. **IfcOpenShell schema introspection** is the runtime adapter used to derive
   deterministic registry files from the official schema.
6. **bSDD** is optional terminology and classification enrichment only. It is
   not the IFC2X3 structural authority.

When sources disagree, generation stops and reports the conflict. The project
does not choose a convenient value silently.

## Verified Official Artifacts

Verified on 2026-06-11:

| Role | Official URL | SHA-256 / observation |
|---|---|---|
| IFC2X3 TC1 EXPRESS | `https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/EXPRESS/IFC2X3_TC1.exp` | `E18A1B2C3E29F5256904C83378CCAD0850F52287A8D0122D149ABA4A417FE5E5` |
| IFC2X3 XSD | `https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/XML/IFC2X3.xsd` | `E49B60B94BD2CE6AED8486A55BD94E788180109283FB856805995F7A627D1E03` |
| HTML and PSD distribution | `https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/IFC2x3_TC1_HTML_distribution-pset_errata.zip` | `BA22D66BC961B14A65D393E9A83672C17B646D7CDF2991A242F136B2E7849B6F`; 3310 archive entries and 317 PSD XML files |
| Release index | `https://technical.buildingsmart.org/standards/ifc/ifc-schema-specifications/` | Lists IFC2X3 TC1 version 2.3.0.1 as official |
| bSDD service description | `https://technical.buildingsmart.org/services/bsdd/` | buildingSMART states bSDD is not the complete IFC schema and currently publishes IFC4.3 IFC dictionary content |
| IfcOpenShell schema querying | `https://docs.ifcopenshell.org/ifcopenshell-python/schema_querying.html` | Documents querying schema definitions without an IFC model |

The repository file `schemas/ifc/IFC2X3_TC1.exp` has the same SHA-256 as the
official EXPRESS artifact.

## Runtime Cross-Check

Using project-local IfcOpenShell 0.8.5:

- IFC2X3 declarations: 980
- IFC2X3 entity declarations: 653
- `IfcProduct` descendants including itself: 90
- `IfcRelationship` descendants including itself: 50
- IfcOpenShell IFC2X3 property-set templates: 317
- IfcOpenShell simple property templates: 1850

Representative declarations resolve the expected inheritance and attributes:

- `IfcWall -> IfcBuildingElement -> IfcElement -> IfcProduct`
- `IfcSpace -> IfcSpatialStructureElement -> IfcProduct`
- `IfcOpeningElement -> IfcFeatureElementSubtraction -> IfcElement`
- `IfcRelVoidsElement` relates a building element to an opening
- `IfcRelFillsElement` relates an opening to a filling building element

These counts are verification observations, not hand-authored contract truth.
Generated registries must still record their source hashes.

## What Official Sources May Fill

Official sources may supply:

- whether an IFC class exists
- inheritance and valid attributes
- attribute and property value types
- enumerations and select alternatives
- relationship endpoint types
- standard property-set names, properties, and applicability
- official descriptions and stable dictionary identifiers

## What Official Sources Must Not Fill

Official sources cannot determine an unknown fact about a particular source
model or natural-language request, including:

- coordinates or orientation
- dimensions, profiles, or extrusion depth
- storey or space membership
- material assignments
- opening, filling, or connection instances
- property values
- entity counts

Those facts must come from source IFC data or the user. If absent, they remain
explicit missing facts in a Draft Envelope and later become clarification
questions.

## Acquisition Policy

- Download only from recorded official HTTPS URLs.
- Verify SHA-256 before parsing.
- Keep raw downloads outside generated registry output unless redistribution
  terms and Git LFS policy are explicitly satisfied.
- Generate normalized registry artifacts deterministically.
- Check generated artifacts for drift in tests.
- Never edit generated schema facts by hand; capability annotations are
  project-authored overlays stored separately from official facts.
