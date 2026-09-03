from __future__ import annotations

import hashlib
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.column import column_operation_definition
from text2ifc_ifc_repair.resolution_flow import (
    ResolvedOperation,
    generated_type_authority,
)


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"
STOREY_ID = "0K_MqVdrL0JOCMi_GblRwJ"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _parameters(
    *, square: bool = False, inclined: bool = False
) -> dict:
    section = {
        "shape": "rectangle",
        "width_mm": 500 if square else 400,
        "depth_mm": 500 if square else 600,
    }
    if not square:
        section["orientation"] = {"x": 0, "y": 1}
    return {
        "axis": {
            "base": {"x_mm": 100000, "y_mm": 100000, "z_mm": 0},
            "top": {
                "x_mm": 100050 if inclined else 100000,
                "y_mm": 100000,
                "z_mm": 6000,
            },
        },
        "section": section,
    }


def _assignment(
    *, operation_id: str, request_hash: str, model_hash: str, parameters: dict
) -> dict:
    resolved = ResolvedOperation(
        operation_id=operation_id,
        operation_type="add_column",
        target_global_id=STOREY_ID,
        scope_ids=(STOREY_ID,),
        evidence_pointers=("request:/operations/0",),
        parameters=parameters,
        context={},
    )
    authority = generated_type_authority(
        column_operation_definition(),
        operation_id=operation_id,
        request_hash=request_hash,
        model_fingerprint=model_hash,
        resolved_operation=resolved,
    )
    return {
        "operation_id": operation_id,
        "scope": "column_occurrence",
        "fact_key": "relationship:type",
        "source_fact_key": "relationship:type",
        "value": authority["global_id"],
        "value_type": "IfcColumnType",
        "unit": None,
        "ownership": "type_inherited",
        "applicability": "required",
        "source_kind": "deterministic_derived",
        "source_ref": f"generated-type:{authority['global_id']}",
        "provenance": ["generated-type-template:0.1"],
        "derivation": {
            key: authority[key]
            for key in (
                "template_id",
                "template_version",
                "ifc_class",
                "formal_attributes",
                "template_digest",
                "template",
            )
        },
        "authoring_action": "inherit_from_type",
    }


def _changeset(*, request: str, parameters: dict, operation_id: str) -> dict:
    request_hash = "sha256:" + hashlib.sha256(request.encode("utf-8")).hexdigest()
    model_hash = _sha256(D7N)
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": f"changeset-{operation_id}",
        "binding_status": "bound",
        "base_model_fingerprint": model_hash,
        "source_request_hash": request_hash,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "scope": {"target_ids": [STOREY_ID], "forbidden_ids": []},
        "evidence_refs": ["request:/operations/0"],
        "preconditions": ["target_exists", "structural_axis_available", "structural_type_authorized"],
        "postconditions": ["column_geometry_matches", "column_contained_in_base_storey", "column_type_bound"],
        "operations": [
            {
                "operation_id": operation_id,
                "operation_type": "add_column",
                "target": {"storey_global_id": STOREY_ID},
                "parameters": parameters,
                "evidence_refs": ["request:/operations/0"],
                "semantic_manifest": {
                    "manifest_id": f"manifest-{operation_id}",
                    "policy_id": "column.add.l2",
                    "policy_version": "0.1",
                },
                "semantic_assignments": [
                    _assignment(
                        operation_id=operation_id,
                        request_hash=request_hash,
                        model_hash=model_hash,
                        parameters=parameters,
                    )
                ],
            }
        ],
    }


@pytest.mark.parametrize("square", (False, True))
def test_default_registry_add_column_reopens_singly_contained_typed_column(
    tmp_path: Path,
    square: bool,
) -> None:
    request = "add one vertical column from Level 1 through the upper storeys"
    operation_id = "column-square-1" if square else "column-oriented-1"
    changeset = _changeset(
        request=request,
        parameters=_parameters(square=square),
        operation_id=operation_id,
    )
    output = tmp_path / f"{operation_id}.ifc"
    before = ifcopenshell.open(str(D7N))
    counts = {
        name: len(before.by_type(name))
        for name in ("IfcColumn", "IfcColumnType", "IfcRelDefinesByType")
    }

    result = apply_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] and result["published"]
    reopened = ifcopenshell.open(str(output))
    for name in counts:
        assert len(reopened.by_type(name)) == counts[name] + 1
    created = {
        item["role"]: reopened.by_guid(item["global_id"])
        for item in result["operations"][0]["changes"]["created"]
        if item.get("global_id")
    }
    column = created["column"]
    storey = reopened.by_guid(STOREY_ID)
    assert [rel.RelatingStructure for rel in column.ContainedInStructure] == [storey]
    assert len(
        [rel for rel in column.IsDefinedBy if rel.is_a("IfcRelDefinesByType")]
    ) == 1
    measured = measure_straight_rectangular_member(column, relative_to=storey)
    assert measured["axis_start_mm"] == (100000.0, 100000.0, 0.0)
    assert measured["axis_end_mm"] == (100000.0, 100000.0, 6000.0)
    if square:
        assert measured["orientation"] is None
        assert column.ObjectPlacement.RelativePlacement.RefDirection is None
    else:
        assert measured["orientation"] == (0.0, 1.0, 0.0)
    assert not [
        rel for rel in column.HasAssociations if rel.is_a("IfcRelAssociatesMaterial")
    ]
    assert not [
        rel for rel in column.IsDefinedBy if rel.is_a("IfcRelDefinesByProperties")
    ]
    assert result["postconditions"][0]["valid"] is True


def test_inclined_column_is_rejected_without_publication(
    tmp_path: Path,
) -> None:
    request = "add one inclined column"
    changeset = _changeset(
        request=request,
        parameters=_parameters(inclined=True),
        operation_id="column-inclined-1",
    )
    output = tmp_path / "must-not-exist.ifc"
    before = _sha256(D7N)

    result = apply_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] is False
    assert result["published"] is False
    assert not output.exists()
    assert _sha256(D7N) == before
    assert any(
        issue["code"] == "STRUCTURAL_COLUMN_NOT_VERTICAL"
        for issue in result["issues"]
    )
