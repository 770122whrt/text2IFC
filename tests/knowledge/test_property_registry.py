from __future__ import annotations

import json
from pathlib import Path

import pytest

from text2ifc_knowledge.psd_registry import PsdParseError, build_property_registry
from text2ifc_knowledge.registry import load_ifc2x3_registry


def test_psd_parser_extracts_exact_names_types_and_applicability(
    representative_psd_zip: Path,
) -> None:
    registry = build_property_registry(representative_psd_zip)

    assert registry["counts"]["property_sets"] == 3
    wall = registry["property_sets"]["Pset_WallCommon"]
    assert wall["applicable_classes"] == ["IfcWall"]
    assert wall["properties"]["IsExternal"]["data_type"] == "IfcBoolean"
    assert wall["properties"]["LoadBearing"]["data_type"] == "IfcBoolean"
    assert (
        registry["property_sets"]["Pset_SpaceCommon"]["properties"]["Reference"][
            "data_type"
        ]
        == "IfcIdentifier"
    )


def test_psd_parser_rejects_external_entities(psd_zip_factory, tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("do-not-read", encoding="utf-8")
    xml = (
        '<?xml version="1.0"?>'
        f'<!DOCTYPE x [<!ENTITY leak SYSTEM "{secret.as_uri()}">]>'
        "<PropertySetDef><Name>&leak;</Name><ApplicableClasses>"
        "<ClassName>IfcWall</ClassName></ApplicableClasses>"
        "<PropertyDefs/></PropertySetDef>"
    )
    archive = psd_zip_factory({"R2x3_TC1/psd/Pset_Unsafe.xml": xml})

    with pytest.raises(PsdParseError):
        build_property_registry(archive)


def test_checked_in_property_registry_matches_official_inventory(
    project_root: Path,
) -> None:
    path = (
        project_root
        / "schemas"
        / "ifc"
        / "generated"
        / "IFC2X3"
        / "property_sets.json"
    )
    assert path.exists(), "generated property registry does not exist yet"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["counts"]["property_sets"] == 317
    assert payload["property_sets"]["Pset_WallCommon"]["properties"]["IsExternal"][
        "data_type"
    ] == "IfcBoolean"
    assert "Pset_SpaceCommon" in payload["property_sets"]
    assert "Pset_OpeningElementCommon" in payload["property_sets"]


def test_runtime_registry_load_is_offline(project_root: Path, monkeypatch) -> None:
    def fail_network(*args, **kwargs):
        raise AssertionError("runtime registry loading must not use the network")

    monkeypatch.setattr("urllib.request.urlopen", fail_network)

    registry = load_ifc2x3_registry(project_root)

    assert registry.entity("IfcWall")["supertype"] == "IfcBuildingElement"
    assert registry.property_set("Pset_WallCommon")["name"] == "Pset_WallCommon"
