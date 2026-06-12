"""Generate BIM JSON 2.0 and IFC2X3 generation-profile references."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "bim-json" / "2.0" / "schema.json"
DRAFT_PATH = ROOT / "schemas" / "bim-json" / "draft" / "1.0" / "schema.json"
CAPABILITIES_PATH = (
    ROOT / "schemas" / "ifc" / "capabilities" / "IFC2X3.json"
)
DECLARATIONS_PATH = (
    ROOT / "schemas" / "ifc" / "generated" / "IFC2X3" / "declarations.json"
)
PROPERTY_SETS_PATH = (
    ROOT / "schemas" / "ifc" / "generated" / "IFC2X3" / "property_sets.json"
)
CONTRACT_OUTPUT = ROOT / "docs" / "reference" / "bim-json-2.0.md"
PROFILE_OUTPUT = (
    ROOT / "docs" / "reference" / "ifc2x3-generation-profile.md"
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _code_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values)


def _required(schema: dict[str, Any], definition: str) -> list[str]:
    return list(schema["$defs"][definition].get("required", []))


def render_contract(
    schema: dict[str, Any], draft_schema: dict[str, Any]
) -> str:
    root_required = list(schema["required"])
    entity_required = _required(schema, "entity")
    relationship_required = _required(schema, "relationship")
    placement_required = _required(schema, "objectPlacement")
    position_required = _required(schema, "localPosition")
    representation_required = _required(schema, "representation")
    draft_required = list(draft_schema["required"])
    schema_version = schema["properties"]["schema_version"]["const"]
    ifc_schema = schema["properties"]["ifc_schema"]["const"]

    return f"""<!-- Generated from canonical BIM JSON schemas. Do not edit. -->
<!-- Regenerate with: python scripts/bim_json_v2/generate_reference.py -->

# BIM JSON 2.0 Contract Reference

Canonical semantic input and extraction-label contract for text2IFC.

## Document Kinds

### Formal

A Formal document has `schema_version` `{schema_version}` and is complete,
validated, capability-gated, and ready for deterministic IFC compilation.
Its required root fields are {_code_list(root_required)}. The target IFC
schema is `{ifc_schema}` and length values use millimetres.

### Draft Envelope

A Draft Envelope is separate from Formal BIM JSON. Its required fields are
{_code_list(draft_required)}. It preserves partial facts while listing every
known missing fact, unsupported source loss, clarification target, and
provenance record. Drafts cannot enter the IFC compiler.

## Semantic Records

`entities` contains user-meaningful IFC objects. Every entity requires
{_code_list(entity_required)}. `ifc_class` uses the exact IFC2X3 class name,
for example `IfcWall`, `IfcWallStandardCase`, or `IfcSpace`.

`relationships` contains user-meaningful IFC relationships. Every relationship
requires {_code_list(relationship_required)}. The initial explicit relation
profile contains `IfcRelVoidsElement` and `IfcRelFillsElement`.

Source IFC `GlobalId` values may be preserved in `global_id`. Stable semantic
`id` values remain separate and never use STEP line numbers.

## Placement

`ObjectPlacement` is a bounded parent-relative semantic placement requiring
{_code_list(placement_required)}. `relative_to` names the parent semantic
entity. World transforms are derived deterministically and are not canonical
input.

`Representation.position` is an optional geometry-local position requiring
{_code_list(position_required)}. It maps to
`IfcExtrudedAreaSolid.Position` and is independent from product
`ObjectPlacement`.

## Geometry

The Formal generation profile supports `extruded_profile` representations.
The schema requires {_code_list(representation_required)} at the generic
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
"""


def render_profile(
    capabilities_payload: dict[str, Any],
    declarations_payload: dict[str, Any],
    property_sets_payload: dict[str, Any],
) -> str:
    capabilities = capabilities_payload["entities"]
    counts = Counter(capabilities.values())
    by_state = {
        state: sorted(
            name for name, value in capabilities.items() if value == state
        )
        for state in (
            "generate",
            "extract-only",
            "compiler-only",
            "unsupported",
        )
    }
    generate_entities = [
        name for name in by_state["generate"] if not name.startswith("IfcRel")
    ]
    generate_relations = [
        name for name in by_state["generate"] if name.startswith("IfcRel")
    ]
    declaration_counts = declarations_payload["counts"]
    pset_counts = property_sets_payload["counts"]

    return f"""<!-- Generated from IFC2X3 registries and capability overlay. Do not edit. -->
<!-- Regenerate with: python scripts/bim_json_v2/generate_reference.py -->

# IFC2X3 Generation Profile

Deterministic Phase 2.5 capability boundary for text2IFC.

## Knowledge Sources

- Official IFC2X3 EXPRESS registry: {declaration_counts["declarations"]}
  declarations and {declaration_counts["entities"]} entities.
- Official PSD registry: {pset_counts["property_sets"]} property sets,
  {pset_counts["complex_properties"]} complex properties, and
  {pset_counts["simple_properties"]} simple properties.
- Project capability overlay: one explicit state for every IFC2X3 entity.

EXPRESS is the structural authority and PSD XML is the standard property
authority. The project capability overlay describes implemented behavior; it
does not rewrite official schema facts.

## Capability Counts

| State | Count | Meaning |
| --- | ---: | --- |
| `generate` | {counts["generate"]} | Accepted in Formal BIM JSON and emitted exactly |
| `extract-only` | {counts["extract-only"]} | Preserved during extraction but cannot compile formally |
| `compiler-only` | {counts["compiler-only"]} | Generated from semantic input, never model-authored |
| `unsupported` | {counts["unsupported"]} | Reported as Draft/loss content |

## Generate Classes

### Semantic Entities

{_code_list(generate_entities)}

### Explicit Semantic Relationships

{_code_list(generate_relations)}

`IfcWallStandardCase` remains exact and is not downgraded to `IfcWall`.
`IfcSpace`, `IfcOpeningElement`, and explicit void/fill endpoints are part of
the initial profile.

## Extract-only Classes

{_code_list(by_state["extract-only"])}

These classes remain visible in extraction losses and Draft partial documents.
They are never replaced by `IfcBuildingElementProxy` or another generated
class.

## Compiler-only Classes

{_code_list(by_state["compiler-only"])}

These are low-level IFC implementation resources. Natural-language or model
output must not author `IfcCartesianPoint`, `IfcDirection`,
`IfcOwnerHistory`, placement resources, representation resources, or
bookkeeping relationships directly.

## Unsupported Boundary

The remaining {counts["unsupported"]} IFC2X3 entities are explicit
`unsupported` capabilities. Unknown class strings are invalid. A known
non-generate class cannot pass Formal validation and cannot be silently
dropped.

Mapped geometry, arbitrary BRep/tessellation, source materials and layer
composition, reusable types, broad connection topology, furnishing, and MEP
generation remain outside Phase 2.5. Their source facts stay in Draft losses
for later fidelity work.

## Verification Commands

```powershell
python scripts/ifc_knowledge/check_registry.py
python scripts/bim_json_v2/generate_reference.py --check
python scripts/ifc_pipeline_v2/audit_bimnet.py --check-accounting
python -m pytest tests/contract_v2 tests/extractor tests/compiler -q
```
"""


def _outputs() -> dict[Path, str]:
    return {
        CONTRACT_OUTPUT: render_contract(_load(SCHEMA_PATH), _load(DRAFT_PATH)),
        PROFILE_OUTPUT: render_profile(
            _load(CAPABILITIES_PATH),
            _load(DECLARATIONS_PATH),
            _load(PROPERTY_SETS_PATH),
        ),
    }


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check generated references for drift without writing.",
    )
    arguments = parser.parse_args()
    outputs = _outputs()
    if arguments.check:
        drifted = [
            path
            for path, content in outputs.items()
            if not path.is_file()
            or path.read_text(encoding="utf-8") != content
        ]
        if drifted:
            for path in drifted:
                print(f"Reference drift: {path.relative_to(ROOT).as_posix()}")
            return 1
        print("BIM JSON 2.0 references are current.")
        return 0

    for path, content in outputs.items():
        _write(path, content)
        print(f"Wrote reference: {path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
