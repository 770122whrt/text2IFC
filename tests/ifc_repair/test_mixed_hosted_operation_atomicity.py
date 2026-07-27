import hashlib
from pathlib import Path

from text2ifc_ifc_repair.audit import audit_changeset
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.operations import create_default_registry


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
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"


def _request_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _parameters(center: float) -> dict:
    return {
        "position": {
            "reference": "wall_local_start",
            "center_offset_mm": center,
        },
        "opening": {
            "width_mm": 915.0,
            "height_mm": 1830.0,
            "sill_height_mm": 305.0,
        },
    }


def test_cross_family_overlap_is_rejected_before_any_ifc_publication(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "mixed-overlap"
    mutation = remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    damaged = case_dir / "damaged.ifc"
    request = "在同一位置添加一个洞口和一扇门。"
    parameters = _parameters(3042.5)
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-mixed-overlap-001",
        "base_model_fingerprint": "sha256:" + mutation["damaged_sha256"],
        "source_request_hash": _request_hash(request),
        "scope": {"target_ids": [WALL_ID], "forbidden_ids": []},
        "evidence_refs": [
            "request:/operations",
            "request:/operations/0",
            "request:/operations/1",
        ],
        "preconditions": ["targets_exist"],
        "postconditions": ["operations_atomic"],
        "operations": [
            {
                "operation_id": "operation-opening-overlap-001",
                "operation_type": "add_opening_to_wall",
                "target": {"wall_global_id": WALL_ID},
                "parameters": parameters,
                "evidence_refs": ["request:/operations/0"],
            },
            {
                "operation_id": "operation-door-overlap-001",
                "operation_type": "add_door_with_opening_to_wall",
                "target": {"wall_global_id": WALL_ID},
                "parameters": {
                    **parameters,
                    "door": {
                        "overall_width_mm": 915.0,
                        "overall_height_mm": 1830.0,
                        "operation_type": "SINGLE_SWING_LEFT",
                    },
                },
                "evidence_refs": ["request:/operations/1"],
            },
        ],
    }

    audit = audit_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert audit["valid"] is False
    assert any(
        issue["code"] == "BATCH_OPENING_OVERLAP"
        for issue in audit["issues"]
    )
    assert not (tmp_path / "repaired.ifc").exists()
