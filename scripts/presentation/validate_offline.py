from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.guid
from ifcopenshell.api.material.add_material import add_material

from text2ifc_compiler import compile_document, open_ifc
from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.operations.hosted_opening import body_context
from text2ifc_ifc_repair.operations.structural_member import (
    bind_structural_type,
    create_straight_rectangular_member,
)
from text2ifc_presentation import (
    AppearanceSpec,
    assign_material_appearance,
    item_appearance_signatures,
)


ROOT = Path(__file__).resolve().parents[2]
GENERATION_FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"
REPAIR_FIXTURE = ROOT / "dataset" / "external" / "bimnet" / "d7n.ifc"
SCHEMA_VERSION = "text2ifc/presentation-offline-validation/0.1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _global_id(label: str) -> str:
    return ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, label).hex)


def _product_styles(model: Any) -> dict[str, tuple[dict[str, Any], ...]]:
    result: dict[str, tuple[dict[str, Any], ...]] = {}
    for product in model.by_type("IfcProduct"):
        representation = getattr(product, "Representation", None)
        if representation is None:
            continue
        signatures: list[dict[str, Any]] = []
        for shape in representation.Representations:
            for item in shape.Items:
                signatures.extend(item_appearance_signatures(item))
        if signatures:
            result[str(product.GlobalId)] = tuple(signatures)
    return result


def _generation_validation(output_dir: Path) -> dict[str, Any]:
    document = json.loads(GENERATION_FIXTURE.read_text(encoding="utf-8"))
    first = output_dir / "generation-demo-a.ifc"
    second = output_dir / "generation-demo-b.ifc"
    first_result = compile_document(
        document,
        first,
        appearance_profile="demo-colorful-v0.1",
        appearance_seed="presentation-offline",
    )
    second_result = compile_document(
        document,
        second,
        appearance_profile="demo-colorful-v0.1",
        appearance_seed="presentation-offline",
    )
    if not first_result.success or not second_result.success:
        return {
            "passed": False,
            "reason": "generation_compile_failed",
            "first_issues": [str(item) for item in first_result.ifc_issues],
            "second_issues": [str(item) for item in second_result.ifc_issues],
        }
    first_styles = _product_styles(open_ifc(first))
    second_styles = _product_styles(open_ifc(second))
    colours = {
        (item["red"], item["green"], item["blue"])
        for signatures in first_styles.values()
        for item in signatures
    }
    deterministic = first_styles == second_styles
    passed = bool(first_styles) and deterministic and len(colours) >= 3
    return {
        "passed": passed,
        "profile": "demo-colorful-v0.1",
        "styled_product_count": len(first_styles),
        "distinct_colour_count": len(colours),
        "deterministic_reopen_signatures": deterministic,
        "first_ifc": str(first),
        "first_sha256": _sha256(first),
        "second_ifc": str(second),
        "second_sha256": _sha256(second),
    }


def _repair_validation(output_dir: Path) -> dict[str, Any]:
    model = ifcopenshell.open(str(REPAIR_FIXTURE))
    owner_history = model.by_type("IfcOwnerHistory")[0]
    storey = next(
        item for item in model.by_type("IfcBuildingStorey") if item.Name == "Level 1"
    )
    context = body_context(model)
    type_object = model.create_entity(
        "IfcBeamType",
        GlobalId=_global_id("presentation-offline-beam-type"),
        OwnerHistory=owner_history,
        Name="Presentation Offline Beam Type",
        PredefinedType="NOTDEFINED",
    )
    material = add_material(model, name="Presentation Offline Material")
    model.create_entity(
        "IfcRelAssociatesMaterial",
        GlobalId=_global_id("presentation-offline-beam-material"),
        OwnerHistory=owner_history,
        RelatedObjects=[type_object],
        RelatingMaterial=material,
    )
    assign_material_appearance(
        model,
        material=material,
        context=context,
        spec=AppearanceSpec(
            name="offline-authoritative-blue",
            red=0.18,
            green=0.34,
            blue=0.62,
        ),
    )
    created = create_straight_rectangular_member(
        model=model,
        occurrence_class="IfcBeam",
        occurrence_global_id=_global_id("presentation-offline-beam"),
        operation_id="presentation-offline-beam",
        axis_start_mm=(0.0, 0.0, 3000.0),
        axis_end_mm=(6000.0, 0.0, 3000.0),
        section={"shape": "rectangle", "width_mm": 500.0, "height_mm": 800.0},
        storey=storey,
        owner_history=owner_history,
        representation_context=context,
    )
    binding = bind_structural_type(
        model=model,
        occurrence=created["occurrence"],
        assignment={
            "value": str(type_object.GlobalId),
            "value_type": "IfcBeamType",
            "source_kind": "surviving_type",
        },
        owner_history=owner_history,
        operation_id="presentation-offline-beam",
        expected_ifc_class="IfcBeamType",
        generated_type_factory=None,
        factory_context={},
    )
    output = output_dir / "repair-styled-beam.ifc"
    model.write(str(output))
    reopened = ifcopenshell.open(str(output))
    reopened_beam = reopened.by_guid(str(created["occurrence"].GlobalId))
    reopened_storey = reopened.by_guid(str(storey.GlobalId))
    measurement = measure_straight_rectangular_member(
        reopened_beam, relative_to=reopened_storey
    )
    style_signatures = item_appearance_signatures(
        reopened_beam.Representation.Representations[0].Items[0]
    )
    geometry_ok = (
        measurement["axis_extent_mm"] == 6000.0
        and measurement["section"]
        == {"shape": "rectangle", "width_mm": 500.0, "height_mm": 800.0}
    )
    passed = (
        reopened.schema == "IFC2X3"
        and binding["appearance"].get("applied") is True
        and geometry_ok
        and style_signatures
        == (
            {
                "style_name": "offline-authoritative-blue",
                "red": 0.18,
                "green": 0.34,
                "blue": 0.62,
                "transparency": 0.0,
            },
        )
    )
    return {
        "passed": passed,
        "schema": reopened.schema,
        "geometry_ok": geometry_ok,
        "appearance": binding["appearance"],
        "reopened_style_signatures": style_signatures,
        "ifc": str(output),
        "sha256": _sha256(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    generation = _generation_validation(output_dir)
    repair = _repair_validation(output_dir)
    result = {
        "schema_version": SCHEMA_VERSION,
        "generation": generation,
        "repair": repair,
        "passed": bool(generation.get("passed")) and bool(repair.get("passed")),
    }
    result_path = output_dir / "validation.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
