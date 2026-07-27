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
