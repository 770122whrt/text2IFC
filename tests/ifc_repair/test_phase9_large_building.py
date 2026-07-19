from __future__ import annotations

import hashlib
from pathlib import Path

import ifcopenshell

from tests.ifc_repair.test_phase9_offline_e2e import _api


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset" / "external" / "bim-whale-ifc-samples" / "LargeBuilding" / "IFC" / "LargeBuilding.ifc"
SOURCE_SHA256 = "102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725"


def test_large_building_uses_public_api_and_keeps_current_l2_nonpublishable(tmp_path: Path) -> None:
    model = ifcopenshell.open(str(SOURCE))
    wall_name = next(str(wall.Name) for wall in model.by_type("IfcWall") if wall.Name)
    calls = {"stage1": 0, "stage2": 0, "apply": 0, "evaluation": 0}
    api = _api(tmp_path, operation_count=1, apply_ok=True, publishable=False, calls=calls, target_names=[wall_name])

    # The caller supplies only IFC + natural text. No benchmark IDs or original IFC.
    result = api.start(SOURCE, f"请修复 {wall_name} 上缺失的外窗")

    assert calls == {"stage1": 1, "stage2": 1, "apply": 1, "evaluation": 1}
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert result.complete_repair_success is False
    assert result.successful_artifact_publishable is False
    assert "successful_ifc" not in result.artifacts
    assert "diagnostic_candidate" in result.artifacts
