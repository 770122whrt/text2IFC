import copy
import hashlib
import importlib
import json
from pathlib import Path

import pytest

from text2ifc_contract.validation import validate_document


ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "dataset" / "processed"
SOURCE_FILES = (
    SOURCE_ROOT / "ifc_parsed_data.json",
    SOURCE_ROOT / "ifc_parsed_enhanced.json",
    *sorted((SOURCE_ROOT / "roundtrip_json").glob("*.json")),
)
def _migration_api():
    try:
        module = importlib.import_module("text2ifc_contract.migration")
    except ModuleNotFoundError as exc:
        pytest.fail(f"migration API is not implemented: {exc}")
    return module.migrate_model, module.audit_existing_models


def _legacy_model():
    return {
        "schema": "IFC2X3",
        "filename": "synthetic.ifc",
        "project": [{"name": "Project"}],
        "site": {"name": "Site"},
        "building": [{"name": "Building"}],
        "storeys": [{"name": "Level 1", "elev": 0}],
        "walls": [
            {
                "name": "Wall",
                "storey": "Level 1",
                "length": 5000,
                "height": 3000,
                "thickness": 200,
            }
        ],
        "columns": [],
        "beams": [],
        "slabs": [
            {
                "name": "Slab",
                "storey": "Level 1",
                "length": 5000,
                "width": 4000,
                "thickness": 200,
                "pretype": "FLOOR",
            }
        ],
        "doors": [
            {
                "name": "Door",
                "storey": "Level 1",
                "w": 900,
                "h": 2100,
            }
        ],
        "windows": [],
        "stairs": [],
        "stair_flights": [],
        "roofs": [],
        "materials": [],
        "mep": [],
        "opening_count": 0,
    }


def _codes(result):
    return {diagnostic["code"] for diagnostic in result["diagnostics"]}


def _hash_sources():
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in SOURCE_FILES
    }


def _snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_known_aliases_and_singleton_shapes_convert_without_mutating_source():
    migrate_model, _ = _migration_api()
    source = _legacy_model()
    original = copy.deepcopy(source)

    result = migrate_model(source, "synthetic.json#$")

    assert result["disposition"] == "converted", result["diagnostics"]
    assert source == original
    document = result["document"]
    assert document["contract_version"] == "bim-json/1.0"
    assert document["storeys"][0]["elevation"] == 0
    assert document["elements"][1]["properties"]["predefined_type"] == "FLOOR"
    assert document["elements"][2]["dimensions"] == {"width": 900, "height": 2100}
    assert validate_document(document) == []


def test_legacy_singleton_name_arrays_are_normalized():
    migrate_model, _ = _migration_api()
    source = _legacy_model()
    source["project"] = ["Project"]
    source["site"] = ["Site"]
    source["building"] = ["Building"]

    result = migrate_model(source, "basic.json#$[0]")

    assert result["disposition"] == "converted", result["diagnostics"]
    assert result["document"]["project"]["name"] == "Project"
    assert result["document"]["site"]["name"] == "Site"
    assert result["document"]["building"]["name"] == "Building"


def test_missing_ids_are_deterministic_and_recorded_without_overwriting_existing_ids():
    migrate_model, _ = _migration_api()
    source = _legacy_model()
    source["walls"][0]["id"] = "source-wall-id"

    first = migrate_model(source, "synthetic.json#$")
    second = migrate_model(source, "synthetic.json#$")

    assert first == second
    document = first["document"]
    assert document["project"]["id"] == "project-0001"
    assert document["storeys"][0]["id"] == "storey-0001"
    assert document["elements"][0]["id"] == "source-wall-id"
    assert document["elements"][1]["id"] == "slab-0001"
    assert document["elements"][2]["id"] == "door-0001"
    assert "ID_GENERATED" in _codes(first)


def test_roundtrip_rectangle_profile_and_long_aliases_are_normalized():
    migrate_model, _ = _migration_api()
    source = _legacy_model()
    source["storeys"][0] = {"name": "Level 1", "elevation": 100}
    source["walls"][0] = {
        "name": "Profile wall",
        "storey": "Level 1",
        "profile": {
            "type": "rectangle",
            "x_dim": 6000,
            "y_dim": 240,
            "depth": 3200,
        },
    }
    source["doors"][0] = {
        "name": "Door",
        "storey": "Level 1",
        "width": 1000,
        "height": 2200,
        "predefined_type": "DOOR",
    }

    result = migrate_model(source, "roundtrip.json#$")

    assert result["disposition"] == "converted", result["diagnostics"]
    assert result["document"]["elements"][0]["dimensions"] == {
        "length": 6000,
        "height": 3200,
        "thickness": 240,
    }
    assert result["document"]["elements"][2]["properties"] == {
        "predefined_type": "DOOR"
    }


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda model: model["walls"][0].pop("height"),
            "MISSING_REQUIRED_DIMENSION",
        ),
        (
            lambda model: model["storeys"].append(
                {"name": "Level 1", "elevation": 3000}
            ),
            "NON_UNIQUE_STOREY_NAME",
        ),
        (
            lambda model: model["doors"][0].__setitem__("storey", "Unknown"),
            "UNRESOLVED_STOREY_REFERENCE",
        ),
    ],
)
def test_incomplete_or_ambiguous_models_are_rejected_whole(mutation, code):
    migrate_model, _ = _migration_api()
    source = _legacy_model()
    mutation(source)

    result = migrate_model(source, "invalid.json#$")

    assert result["disposition"] == "rejected"
    assert result["document"] is None
    assert code in _codes(result)
    assert result["source_element_count"] == 3
    assert result["converted_element_count"] == 0


def test_unknown_source_shape_is_rejected_with_stable_code():
    migrate_model, _ = _migration_api()

    result = migrate_model([], "unknown.json#$")

    assert result["disposition"] == "rejected"
    assert _codes(result) == {"UNKNOWN_SOURCE_SHAPE"}


def test_out_of_contract_data_is_reported_as_omissions():
    migrate_model, _ = _migration_api()
    source = _legacy_model()
    source["materials"] = ["Concrete"]
    source["material_assignments"] = {"wall": "Concrete"}
    source["mep"] = [{"type": "IfcFlowSegment", "count": 2}]
    source["opening_count"] = 4

    result = migrate_model(source, "omissions.json#$")

    assert result["disposition"] == "converted", result["diagnostics"]
    assert result["omissions"] == [
        "material_assignments",
        "materials",
        "mep",
        "openings",
    ]


def test_real_audit_classifies_all_53_records_and_validates_converted_outputs(
    tmp_path,
):
    _, audit_existing_models = _migration_api()
    output_root = tmp_path / "bim-json-1.0"

    report = audit_existing_models(SOURCE_ROOT, output_root)

    assert report["summary"]["total"] == 53
    assert report["summary"]["basic"] == 25
    assert report["summary"]["enhanced"] == 25
    assert report["summary"]["roundtrip"] == 3
    assert (
        report["summary"]["converted"] + report["summary"]["rejected"]
        == report["summary"]["total"]
    )
    assert len(report["records"]) == 53

    for record in report["records"]:
        assert {
            "record_id",
            "source_path",
            "source_selector",
            "source_sha256",
            "disposition",
            "diagnostics",
            "omissions",
        } <= record.keys()
        assert record["disposition"] in {"converted", "rejected"}
        assert len(record["source_sha256"]) == 64
        if record["disposition"] == "converted":
            output = output_root / record["output_path"]
            document = json.loads(output.read_text(encoding="utf-8"))
            assert validate_document(document) == []
            assert record["source_element_count"] == record["converted_element_count"]
        else:
            assert record["output_path"] is None
            assert record["diagnostics"]


def test_real_audit_is_byte_deterministic_removes_stale_outputs_and_preserves_sources(
    tmp_path,
):
    _, audit_existing_models = _migration_api()
    output_root = tmp_path / "bim-json-1.0"
    before_hashes = _hash_sources()

    first_report = audit_existing_models(SOURCE_ROOT, output_root)
    first_snapshot = _snapshot(output_root)
    stale = output_root / "migrated" / "stale.json"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("stale", encoding="utf-8")
    second_report = audit_existing_models(SOURCE_ROOT, output_root)

    assert second_report == first_report
    assert _snapshot(output_root) == first_snapshot
    assert _hash_sources() == before_hashes
