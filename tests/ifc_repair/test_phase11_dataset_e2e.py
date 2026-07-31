import importlib.util
import json
import re
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ifc_repair/run_phase11_offline.py"


def _module():
    spec = importlib.util.spec_from_file_location("phase11_offline", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_largebuilding_phase11_offline_case_is_source_bound_and_reopenable(
    tmp_path: Path,
) -> None:
    module = _module()
    manifest = module.run_case(module.CASES[0], tmp_path)
    case_dir = tmp_path / manifest["case_id"]

    assert manifest["status"] == "passed"
    assert manifest["synthetic_fallback_used"] is False
    assert manifest["operation_count"] == 1
    assert manifest["damage"]["mode"] == "remove_door_preserve_opening"
    assert manifest["damage"]["door"]["name"] == (
        "M_Single-Flush:Inside Door:353172"
    )
    for name in ("original.ifc", "damaged.ifc", "repaired.ifc"):
        assert ifcopenshell.open(str(case_dir / name)).schema == "IFC2X3"


def test_vvo_five_door_case_is_one_changeset_and_rolls_back_on_failure(
    tmp_path: Path,
) -> None:
    module = _module()
    manifest = module.run_five_door_case(
        module.VVO_FIVE_DOOR_CASE, tmp_path
    )
    case_dir = tmp_path / manifest["case_id"]

    assert manifest["status"] == "passed"
    assert manifest["operation_count"] == 5
    assert manifest["one_atomic_changeset"] is True
    assert manifest["injected_failure_published"] is False
    assert not (case_dir / "must-not-exist.ifc").exists()
    repaired = ifcopenshell.open(str(case_dir / "repaired.ifc"))
    assert repaired.schema == "IFC2X3"
    application = json.loads(
        (case_dir / "application.json").read_text(encoding="utf-8")
    )
    created_door_ids = [
        item["global_id"]
        for operation in application["operations"]
        for item in operation["changes"]["created"]
        if item["role"] == "door"
    ]
    assert len(created_door_ids) == 5
    millimetres_per_project_unit = (
        ifcopenshell.util.unit.calculate_unit_scale(repaired) * 1000.0
    )
    for global_id in created_door_ids:
        door = repaired.by_guid(global_id)
        width_mm = (
            float(door.OverallWidth) * millimetres_per_project_unit
        )
        assert 100.0 <= width_mm <= 5000.0
        assert len(door.FillsVoids) == 1


def test_vvo_mixed_case_publishes_two_windows_and_two_doors_atomically(
    tmp_path: Path,
) -> None:
    module = _module()
    manifest = module.run_mixed_case(module.VVO_MIXED_CASE, tmp_path)
    case_dir = tmp_path / manifest["case_id"]

    assert manifest["status"] == "passed"
    assert manifest["operation_count"] == 4
    assert manifest["operation_families"] == {"window": 2, "door": 2}
    assert manifest["one_atomic_changeset"] is True
    repaired = ifcopenshell.open(str(case_dir / "repaired.ifc"))
    assert repaired.schema == "IFC2X3"


def test_vvo_mixed_case_public_targeting_is_guid_free_and_resolves_before_binding(
    tmp_path: Path,
) -> None:
    module = _module()
    manifest = module.run_mixed_case(module.VVO_MIXED_CASE, tmp_path)
    case_dir = tmp_path / manifest["case_id"]

    request = (case_dir / "request.txt").read_text(encoding="utf-8")
    assert re.findall(r"(?<![0-9A-Za-z_$])[0-3][0-9A-Za-z_$]{21}(?![0-9A-Za-z_$])", request) == []

    intent = json.loads((case_dir / "repair-intent.json").read_text(encoding="utf-8"))
    for operation in intent["operations"]:
        target_query = operation["target_query"]
        assert target_query.get("global_id") is None
        assert target_query.get("storey_global_id") is None
        assert target_query.get("host_global_id") is None
        assert target_query["names"]
        prototype = operation.get("prototype_intent")
        if prototype is not None:
            assert prototype["reference_kind"] == "type_name"

    resolution = json.loads(
        (case_dir / "target-resolution.json").read_text(encoding="utf-8")
    )
    assert resolution["status"] == "resolved"
    assert len(resolution["operations"]) == 4
    assert all(item["target_global_id"] for item in resolution["operations"])
    assert manifest["public_targeting"] == {
        "guid_free": True,
        "strategy": "name_storey_and_wall_local_position",
        "resolved_operation_count": 4,
    }


def test_dental_clinic_mixed_case_recreates_openings_from_geometry_targeting(
    tmp_path: Path,
) -> None:
    module = _module()
    manifest = module.run_mixed_case(
        module.DENTAL_CLINIC_MIXED_CASE, tmp_path
    )
    case_dir = tmp_path / manifest["case_id"]

    assert manifest["status"] == "passed"
    assert manifest["operation_families"] == {"window": 2, "door": 2}
    assert manifest["damage"]["door_openings_removed"] is True
    assert manifest["damage"]["window_openings_removed"] is True
    assert manifest["public_targeting"] == {
        "guid_free": True,
        "name_free": True,
        "strategy": "storey_elevation_orientation_and_wall_dimensions",
        "resolved_operation_count": 4,
    }

    request = (case_dir / "request.txt").read_text(encoding="utf-8")
    assert re.findall(
        r"(?<![0-9A-Za-z_$])[0-3][0-9A-Za-z_$]{21}(?![0-9A-Za-z_$])",
        request,
    ) == []
    intent = json.loads(
        (case_dir / "repair-intent.json").read_text(encoding="utf-8")
    )
    for operation in intent["operations"]:
        query = operation["target_query"]
        assert query.get("global_id") is None
        assert query.get("names") in (None, [])
        assert query.get("storey_name") is None
        assert query.get("storey_global_id") is None
        assert query.get("host_global_id") is None
        assert len(query["geometry_constraints"]) == 4

    changeset = json.loads(
        (case_dir / "changeset.json").read_text(encoding="utf-8")
    )
    operation_types = [
        operation["operation_type"] for operation in changeset["operations"]
    ]
    assert operation_types.count("add_window_with_opening_to_wall") == 2
    assert operation_types.count("add_door_with_opening_to_wall") == 2
    assert "fill_existing_opening_with_door" not in operation_types
    damaged_model = ifcopenshell.open(str(case_dir / "damaged.ifc"))
    repaired_model = ifcopenshell.open(str(case_dir / "repaired.ifc"))
    assert repaired_model.schema == "IFC2X3"
    application = json.loads(
        (case_dir / "application.json").read_text(encoding="utf-8")
    )
    window_results = [
        item
        for item in application["operations"]
        if item["operation_id"].startswith("operation-window-")
    ]
    assert all(
        len(
            [
                change
                for change in item["changes"]["created"]
                if change["role"] == "window_type_relationship"
            ]
        )
        == 1
        for item in window_results
    )
    declared_created = {
        change["global_id"]
        for item in application["operations"]
        for change in item["changes"]["created"]
    }
    damaged_roots = {
        str(item.GlobalId)
        for item in damaged_model.by_type("IfcRoot")
    }
    repaired_roots = {
        str(item.GlobalId)
        for item in repaired_model.by_type("IfcRoot")
    }
    assert repaired_roots - damaged_roots == declared_created


def test_largebuilding_generated_door_type_case_is_source_bound(
    tmp_path: Path,
) -> None:
    module = _module()
    manifest = module.run_generated_type_case(
        module.GENERATED_DOOR_CASE, tmp_path
    )
    case_dir = tmp_path / manifest["case_id"]

    assert manifest["status"] == "passed"
    assert manifest["generated_type_template"].endswith("/0.1")
    repaired = ifcopenshell.open(str(case_dir / "repaired.ifc"))
    generated_type = repaired.by_guid(manifest["generated_type_global_id"])
    assert generated_type.is_a("IfcDoorStyle")
    assert generated_type.RepresentationMaps


def test_advancedproject_door_case_completes_full_gate_under_deadline(
    tmp_path: Path,
) -> None:
    module = _module()
    manifest = module.run_case(module.CASES[2], tmp_path)
    case_dir = tmp_path / manifest["case_id"]

    assert manifest["status"] == "passed"
    performance = manifest["performance"]
    assert performance["cold_request_to_publication_seconds"] < 180.0
    assert performance["warm_evaluation_seconds"] < 180.0
    assert ifcopenshell.open(str(case_dir / "repaired.ifc")).schema == "IFC2X3"
