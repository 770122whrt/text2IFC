from __future__ import annotations

import json
from pathlib import Path

import pytest

from text2ifc_contract.capabilities import load_capabilities
from text2ifc_contract.validation_v2 import validate_v2_document


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "contract_v2" / "fixtures" / "minimal.json"


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def issue_pairs(value):
    return {(issue.code, issue.path) for issue in validate_v2_document(value)}


def test_capability_overlay_covers_every_ifc2x3_entity() -> None:
    capabilities = load_capabilities(ROOT)

    assert len(capabilities) == 653
    assert capabilities["IfcWall"] == "generate"
    assert capabilities["IfcWallStandardCase"] == "generate"
    assert capabilities["IfcSpace"] == "generate"
    assert capabilities["IfcBuildingElementProxy"] == "extract-only"
    assert capabilities["IfcFurnishingElement"] == "extract-only"
    assert capabilities["IfcCartesianPoint"] == "compiler-only"
    assert capabilities["IfcStructuralAnalysisModel"] == "unsupported"


def test_wall_standard_case_is_preserved_as_an_exact_generatable_class() -> None:
    value = document()
    value["entities"][1]["ifc_class"] = "IfcWallStandardCase"

    assert validate_v2_document(value) == []


@pytest.mark.parametrize(
    ("ifc_class", "code"),
    [
        ("IfcNotAClass", "UNKNOWN_IFC_CLASS"),
        ("IfcBuildingElementProxy", "CLASS_NOT_GENERATABLE"),
        ("IfcCartesianPoint", "COMPILER_ONLY_CLASS"),
        ("IfcStructuralAnalysisModel", "UNSUPPORTED_IFC_CLASS"),
    ],
)
def test_formal_gate_rejects_unknown_or_non_generatable_classes(
    ifc_class: str, code: str
) -> None:
    value = document()
    value["entities"][1]["ifc_class"] = ifc_class

    assert (code, "/entities/1/ifc_class") in issue_pairs(value)


def test_inherited_attribute_is_accepted_and_class_invalid_attribute_rejected() -> None:
    value = document()
    value["entities"][1]["attributes"]["Description"] = "Inherited from IfcRoot"
    assert validate_v2_document(value) == []

    value["entities"][1]["attributes"]["InteriorOrExteriorSpace"] = "INTERNAL"
    assert (
        "INVALID_IFC_ATTRIBUTE",
        "/entities/1/attributes/InteriorOrExteriorSpace",
    ) in issue_pairs(value)


@pytest.mark.parametrize(
    ("attribute", "value"),
    [
        ("PredefinedType", "BANANA"),
        ("OverallWidth", "wide"),
    ],
)
def test_native_ifc_attribute_values_use_registry_types(
    attribute: str, value
) -> None:
    complete = json.loads(
        (
            ROOT / "tests" / "contract_v2" / "fixtures" / "complete.json"
        ).read_text(encoding="utf-8")
    )
    target_id = "slab-1" if attribute == "PredefinedType" else "door-1"
    target = next(
        item for item in complete["entities"] if item["id"] == target_id
    )
    target["attributes"][attribute] = value
    target_index = complete["entities"].index(target)

    assert (
        "INVALID_IFC_ATTRIBUTE_TYPE",
        f"/entities/{target_index}/attributes/{attribute}",
    ) in issue_pairs(complete)


@pytest.mark.parametrize(
    "global_id",
    ["short", "012345678901234567890!", 42],
)
def test_source_global_id_is_optional_but_format_checked(global_id) -> None:
    value = document()
    value["entities"][1]["global_id"] = global_id

    assert ("INVALID_GLOBAL_ID", "/entities/1/global_id") in issue_pairs(value)


def test_source_global_ids_are_unique_across_semantic_records() -> None:
    value = document()
    duplicate = value["entities"][1]["global_id"]
    value["entities"][0]["global_id"] = duplicate

    assert (
        "DUPLICATE_GLOBAL_ID",
        "/entities/1/global_id",
    ) in issue_pairs(value)


def test_standard_property_names_types_and_applicability_use_registry() -> None:
    value = document()
    value["entities"][1]["property_sets"]["Pset_WallCommon"]["IsExternal"] = "yes"
    assert (
        "INVALID_PROPERTY_TYPE",
        "/entities/1/property_sets/Pset_WallCommon/IsExternal",
    ) in issue_pairs(value)

    value = document()
    value["entities"][1]["property_sets"]["Pset_WallCommon"]["Unknown"] = True
    assert (
        "UNKNOWN_STANDARD_PROPERTY",
        "/entities/1/property_sets/Pset_WallCommon/Unknown",
    ) in issue_pairs(value)

    value = document()
    value["entities"][1]["property_sets"]["Pset_SpaceCommon"] = {
        "Reference": "A"
    }
    assert (
        "PROPERTY_SET_NOT_APPLICABLE",
        "/entities/1/property_sets/Pset_SpaceCommon",
    ) in issue_pairs(value)


def test_nonstandard_property_sets_require_explicit_custom_namespace() -> None:
    value = document()
    value["entities"][1]["property_sets"]["VendorSet"] = {"Code": "A"}

    assert (
        "UNNAMESPACED_CUSTOM_PROPERTY_SET",
        "/entities/1/property_sets/VendorSet",
    ) in issue_pairs(value)
