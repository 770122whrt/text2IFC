import importlib.util
from pathlib import Path

import ifcopenshell


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
    assert ifcopenshell.open(str(case_dir / "repaired.ifc")).schema == "IFC2X3"


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
