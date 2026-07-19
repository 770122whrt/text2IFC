import hashlib
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element

from text2ifc_ifc_repair.workflow import run_offline_window_benchmark_case


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "dataset"
    / "external"
    / "bim-whale-ifc-samples"
    / "LargeBuilding"
    / "IFC"
    / "LargeBuilding.ifc"
)
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"
ORIGINAL_WINDOW_ID = "2cXV28XOjE6f6irgi0CO4t"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_large_building_phase8_baseline_is_offline_l1_only_success(
    tmp_path: Path,
) -> None:
    output = tmp_path / "phase8-large-building"
    before_hash = _sha256(SOURCE)

    result = run_offline_window_benchmark_case(
        source_path=SOURCE,
        output_dir=output,
        case_id="phase8-large-building-window-baseline",
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id=ORIGINAL_WINDOW_ID,
    )

    assert result["provider_calls"] == 0
    assert _sha256(SOURCE) == before_hash == SOURCE_SHA256
    assert not (output / "provider").exists()
    assert not (output / "repaired.ifc").exists()
    assert (output / "diagnostic" / "repaired-candidate.ifc").is_file()
    assert result["complete_repair_success"] is False
    assert result["successful_artifact_publishable"] is False
    assert result["diagnostic_artifact_retained"] is True

    operation = result["operations"][0]
    levels = {level["level"]: level for level in operation["levels"]}
    assert levels["L1"]["status"] == "passed"
    assert levels["L2"]["status"] in {"failed", "partial", "not_evaluable"}
    assert levels["L3"]["status"] == "not_required"

    remediation = {
        check["difference_category"]
        for check in levels["L2"]["checks"]
        if check["remediation_required"]
        and check["difference_category"]
        in {"pset", "quantity", "is_external", "material", "classification"}
    }
    assert {"pset", "quantity", "is_external", "classification"} <= remediation
    assert remediation <= {
        "pset",
        "quantity",
        "is_external",
        "material",
        "classification",
    }

    original_model = ifcopenshell.open(str(SOURCE))
    original_window = original_model.by_guid(ORIGINAL_WINDOW_ID)
    authorized_materials = ifcopenshell.util.element.get_materials(
        original_window, should_inherit=True
    )
    private = json.loads(
        (output / "private" / "evaluation-private.json").read_text(
            encoding="utf-8"
        )
    )
    private_l2 = {
        level["level"]: level
        for level in private["operations"][0]["levels"]
    }["L2"]
    material_checks = [
        check
        for check in private_l2["checks"]
        if check["check_id"].startswith("window.material")
    ]
    if authorized_materials:
        assert material_checks
        assert all(check["status"] != "not_required" for check in material_checks)
    else:
        assert material_checks == [] or all(
            check["status"] == "not_required" for check in material_checks
        )

    original_psets = ifcopenshell.util.element.get_psets(
        original_window, should_inherit=True
    )
    pset_checks = [
        check
        for check in private_l2["checks"]
        if check["check_id"].startswith(("window.pset", "window.quantity"))
    ]
    if original_psets:
        assert pset_checks
        assert any(check["status"] != "not_required" for check in pset_checks)

