from __future__ import annotations

import hashlib
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.geometry import measure_straight_rectangular_member
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.beam import beam_operation_definition
from text2ifc_ifc_repair.resolution_flow import (
    ResolvedOperation,
    generated_type_authority,
)


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"
STOREY_ID = "0K_MqVdrL0JOCMi_GblRwJ"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _parameters(*, inclined: bool = False) -> dict:
    return {
        "axis": {
            "start": {"x_mm": 100000, "y_mm": 100000, "z_mm": 3000},
            "end": {
                "x_mm": 103000,
                "y_mm": 104000,
                "z_mm": 3050 if inclined else 3000,
            },
        },
        "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
    }


def _assignment(
    *, operation_id: str, request_hash: str, model_hash: str, parameters: dict
) -> dict:
    resolved = ResolvedOperation(
        operation_id=operation_id,
        operation_type="add_beam",
        target_global_id=STOREY_ID,
        scope_ids=(STOREY_ID,),
        evidence_pointers=("request:/operations/0",),
        parameters=parameters,
        context={},
    )
    authority = generated_type_authority(
        beam_operation_definition(),
        operation_id=operation_id,
        request_hash=request_hash,
        model_fingerprint=model_hash,
        resolved_operation=resolved,
    )
    return {
        "operation_id": operation_id,
        "scope": "beam_occurrence",
        "fact_key": "relationship:type",
        "source_fact_key": "relationship:type",
        "value": authority["global_id"],
        "value_type": "IfcBeamType",
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


def _changeset(*, request: str, parameters: dict) -> dict:
    operation_id = "beam-application-1"
    request_hash = "sha256:" + hashlib.sha256(request.encode("utf-8")).hexdigest()
    model_hash = _sha256(D7N)
    assignment = _assignment(
        operation_id=operation_id,
        request_hash=request_hash,
        model_hash=model_hash,
        parameters=parameters,
    )
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": "changeset-beam-application-1",
        "binding_status": "bound",
        "base_model_fingerprint": model_hash,
        "source_request_hash": request_hash,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "scope": {"target_ids": [STOREY_ID], "forbidden_ids": []},
        "evidence_refs": ["request:/operations/0"],
        "preconditions": ["target_exists", "structural_axis_available", "structural_type_authorized"],
        "postconditions": ["beam_geometry_matches", "beam_contained_in_storey", "beam_type_bound"],
        "operations": [
            {
                "operation_id": operation_id,
                "operation_type": "add_beam",
                "target": {"storey_global_id": STOREY_ID},
                "parameters": parameters,
                "evidence_refs": ["request:/operations/0"],
                "semantic_manifest": {
                    "manifest_id": "manifest-beam-application-1",
                    "policy_id": "beam.add.l2",
                    "policy_version": "0.1",
                },
                "semantic_assignments": [assignment],
            }
        ],
    }


def test_default_registry_add_beam_publishes_one_reopened_contained_typed_occurrence(
    tmp_path: Path,
) -> None:
    request = "add a 300 by 500 mm horizontal beam on Level 1"
    changeset = _changeset(request=request, parameters=_parameters())
    output = tmp_path / "beam.ifc"
    source_before = _sha256(D7N)
    before = ifcopenshell.open(str(D7N))
    counts_before = {
        name: len(before.by_type(name))
        for name in ("IfcBeam", "IfcBeamType", "IfcRelDefinesByType")
    }

    result = apply_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] and result["published"]
    assert _sha256(D7N) == source_before
    reopened = ifcopenshell.open(str(output))
    assert reopened.schema == "IFC2X3"
    for name in counts_before:
        assert len(reopened.by_type(name)) == counts_before[name] + 1
    created = {
        item["role"]: reopened.by_guid(item["global_id"])
        for item in result["operations"][0]["changes"]["created"]
        if item.get("global_id")
    }
    beam = created["beam"]
    storey = reopened.by_guid(STOREY_ID)
    assert beam.is_a("IfcBeam")
    assert [rel.RelatingStructure for rel in beam.ContainedInStructure] == [storey]
    type_relations = [
        relation
        for relation in beam.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    assert len(type_relations) == 1
    assert type_relations[0].RelatingType.is_a("IfcBeamType")
    assert not [
        relation
        for relation in beam.HasAssociations
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    assert not [
        relation
        for relation in beam.IsDefinedBy
        if relation.is_a("IfcRelDefinesByProperties")
    ]
    measured = measure_straight_rectangular_member(beam, relative_to=storey)
    assert measured["axis_start_mm"] == (100000.0, 100000.0, 3000.0)
    assert measured["axis_end_mm"] == (103000.0, 104000.0, 3000.0)
    assert measured["section"] == {
        "shape": "rectangle",
        "width_mm": 300.0,
        "height_mm": 500.0,
    }
    assert result["postconditions"][0]["valid"] is True


def test_unsupported_inclined_beam_is_rejected_without_publication_or_source_mutation(
    tmp_path: Path,
) -> None:
    request = "add an inclined beam"
    changeset = _changeset(request=request, parameters=_parameters(inclined=True))
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
        issue["code"] == "STRUCTURAL_BEAM_NOT_HORIZONTAL"
        for issue in result["issues"]
    )
