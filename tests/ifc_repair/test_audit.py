import hashlib
import json
from copy import deepcopy
from pathlib import Path

from text2ifc_ifc_repair.audit import audit_changeset
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.projection import (
    project_public_repair_spec,
    render_repair_request,
)


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


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _case(tmp_path: Path) -> tuple[Path, str, dict]:
    case_dir = tmp_path / "case"
    result = remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id="1F6umJ5H50aeL3A1As_wTm",
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    private_manifest = json.loads(
        (case_dir / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    public_spec = project_public_repair_spec(
        private_manifest,
        request_id="large-building-window-repair-001",
    )
    request = render_repair_request(public_spec)
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-window-repair-001",
        "base_model_fingerprint": "sha256:" + result["damaged_sha256"],
        "source_request_hash": _sha256_text(request),
        "scope": {
            "target_ids": ["1F6umJ5H50aeL3A1As_wTm"],
            "forbidden_ids": [],
        },
        "evidence_refs": [
            "spec:/opening",
            "context:/candidate_targets/0",
        ],
        "preconditions": [
            "base_model_fingerprint_matches",
            "target_exists",
        ],
        "postconditions": [
            "opening_voids_wall",
            "window_fills_opening",
        ],
        "operations": [
            {
                "operation_id": "operation-window-001",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {
                    "wall_global_id": "1F6umJ5H50aeL3A1As_wTm",
                },
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": 3042.5,
                    },
                    "opening": {
                        "width_mm": 915.0,
                        "height_mm": 1830.0,
                        "sill_height_mm": 305.0,
                    },
                    "window": {"fit_opening": True},
                },
                "evidence_refs": [
                    "spec:/opening",
                    "context:/candidate_targets/0",
                ],
            }
        ],
    }
    return case_dir / "damaged.ifc", request, changeset


def test_window_changeset_audit_returns_structured_evidence(tmp_path: Path) -> None:
    damaged_ifc, request, changeset = _case(tmp_path)

    audit = audit_changeset(
        damaged_ifc_path=damaged_ifc,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert audit["valid"] is True
    assert audit["issues"] == []
    assert all(check["status"] == "passed" for check in audit["checks"])
    operation_audit = audit["operation_audits"][0]
    assert operation_audit["operation_id"] == "operation-window-001"
    assert operation_audit["evidence"]["wall_dimensions_mm"] == {
        "length": 8200.0,
        "thickness": 200.0,
        "height": 3850.0,
    }
    assert operation_audit["evidence"]["requested_interval_mm"] == [
        2585.0,
        3500.0,
    ]


def test_window_changeset_audit_rejects_overlap_with_existing_opening(
    tmp_path: Path,
) -> None:
    damaged_ifc, request, valid_changeset = _case(tmp_path)
    changeset = deepcopy(valid_changeset)
    changeset["operations"][0]["parameters"]["position"][
        "center_offset_mm"
    ] = 4857.5

    audit = audit_changeset(
        damaged_ifc_path=damaged_ifc,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert audit["valid"] is False
    assert [issue["code"] for issue in audit["issues"]] == ["OPENING_OVERLAP"]


def test_window_changeset_audit_allows_vertically_separated_opening(
    tmp_path: Path,
) -> None:
    damaged_ifc, request, valid_changeset = _case(tmp_path)
    changeset = deepcopy(valid_changeset)
    operation = changeset["operations"][0]
    operation["parameters"]["position"]["center_offset_mm"] = 4857.5
    operation["parameters"]["opening"]["height_mm"] = 200.0
    operation["parameters"]["opening"]["sill_height_mm"] = 0.0

    audit = audit_changeset(
        damaged_ifc_path=damaged_ifc,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert audit["valid"] is True
    assert audit["issues"] == []
    regions = audit["operation_audits"][0]["evidence"][
        "existing_opening_regions_mm"
    ]
    assert regions


def test_audit_rejects_stale_base_fingerprint(tmp_path: Path) -> None:
    damaged_ifc, request, changeset = _case(tmp_path)
    changeset["base_model_fingerprint"] = "sha256:" + "0" * 64

    audit = audit_changeset(
        damaged_ifc_path=damaged_ifc,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert [issue["code"] for issue in audit["issues"]] == [
        "BASE_MODEL_FINGERPRINT_MISMATCH"
    ]


def test_audit_rejects_unregistered_operation(tmp_path: Path) -> None:
    damaged_ifc, request, changeset = _case(tmp_path)
    changeset["operations"][0]["operation_type"] = "unsupported_test_operation"

    audit = audit_changeset(
        damaged_ifc_path=damaged_ifc,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert [issue["code"] for issue in audit["issues"]] == [
        "UNKNOWN_OPERATION_TYPE"
    ]


def test_audit_rejects_target_outside_scope(tmp_path: Path) -> None:
    damaged_ifc, request, changeset = _case(tmp_path)
    changeset["scope"]["target_ids"] = ["another-wall"]

    audit = audit_changeset(
        damaged_ifc_path=damaged_ifc,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert [issue["code"] for issue in audit["issues"]] == [
        "TARGET_OUTSIDE_SCOPE"
    ]


def test_audit_rejects_curved_wall_with_stable_code() -> None:
    curved_ifc = ROOT / "dataset" / "ifc" / "test" / "px4_2.ifc"
    request = "在指定曲墙上新增窗洞。\n"
    fingerprint = "sha256:" + hashlib.sha256(curved_ifc.read_bytes()).hexdigest()
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-curved-wall-rejection",
        "base_model_fingerprint": fingerprint,
        "source_request_hash": _sha256_text(request),
        "scope": {
            "target_ids": ["2PnL0EvVnDjATK7v9JDb0I"],
            "forbidden_ids": [],
        },
        "evidence_refs": ["spec:/opening"],
        "preconditions": ["target_exists"],
        "postconditions": ["opening_voids_wall"],
        "operations": [
            {
                "operation_id": "operation-curved-window",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {"wall_global_id": "2PnL0EvVnDjATK7v9JDb0I"},
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": 1000.0,
                    },
                    "opening": {
                        "width_mm": 900.0,
                        "height_mm": 1200.0,
                        "sill_height_mm": 900.0,
                    },
                    "window": {"fit_opening": True},
                },
                "evidence_refs": ["spec:/opening"],
            }
        ],
    }

    audit = audit_changeset(
        damaged_ifc_path=curved_ifc,
        repair_request=request,
        changeset=changeset,
        registry=create_default_registry(),
    )

    assert [issue["code"] for issue in audit["issues"]] == [
        "UNSUPPORTED_WALL_GEOMETRY"
    ]
