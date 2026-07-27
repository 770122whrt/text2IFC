import hashlib
import json
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
from ifcopenshell.api.root.remove_product import remove_product

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.benchmark_evaluation import (
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.compare import evaluate_repair_application
from text2ifc_ifc_repair.mutation import remove_window_and_opening
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.door import (
    ADD_OPERATION_TYPE,
    FILL_OPERATION_TYPE,
    add_door_operation_definition,
)
from text2ifc_ifc_repair.resolution_flow import (
    ResolvedOperation,
    generated_type_authority,
)
from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind
from text2ifc_ifc_repair.semantic_facts import SemanticFact


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
OPENING_ID = "2cXV28XOjE6f6irhW0CO4t"
WINDOW_ID = "2cXV28XOjE6f6irgi0CO4t"


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _parameters() -> dict:
    return {
        "position": {
            "reference": "wall_local_start",
            "center_offset_mm": 3042.5,
        },
        "opening": {
            "width_mm": 915.0,
            "height_mm": 1830.0,
            "sill_height_mm": 305.0,
        },
        "door": {
            "overall_width_mm": 915.0,
            "overall_height_mm": 1830.0,
            "operation_type": "SINGLE_SWING_LEFT",
        },
    }


def _generated_assignment(
    *,
    operation_id: str,
    operation_type: str,
    target_id: str,
    parameters: dict,
    request_hash: str,
    model_hash: str,
) -> dict:
    resolved = ResolvedOperation(
        operation_id=operation_id,
        operation_type=operation_type,
        target_global_id=target_id,
        scope_ids=(target_id,),
        evidence_pointers=("request:/operations/0",),
        parameters=parameters,
        context={},
    )
    authority = generated_type_authority(
        add_door_operation_definition(),
        operation_id=operation_id,
        request_hash=request_hash,
        model_fingerprint=model_hash,
        resolved_operation=resolved,
    )
    return {
        "operation_id": operation_id,
        "scope": "door_occurrence",
        "fact_key": "relationship:type",
        "source_fact_key": "relationship:type",
        "value": authority["global_id"],
        "value_type": "IfcDoorStyle",
        "unit": None,
        "ownership": "type_inherited",
        "applicability": "required",
        "source_kind": "deterministic_derived",
        "source_ref": f"generated-type:{authority['global_id']}",
        "provenance": ["generated-type-template:0.1"],
        "derivation": {
            "template_id": authority["template_id"],
            "template_version": authority["template_version"],
            "ifc_class": authority["ifc_class"],
            "formal_attributes": authority["formal_attributes"],
            "template_digest": authority["template_digest"],
            "template": authority["template"],
        },
        "authoring_action": "inherit_from_type",
    }


def _changeset(
    *,
    damaged: Path,
    request: str,
    operation_id: str,
    target: dict,
    parameters: dict,
) -> dict:
    request_hash = _hash_text(request)
    model_hash = _hash_file(damaged)
    target_id = next(iter(target.values()))
    assignment = _generated_assignment(
        operation_id=operation_id,
        operation_type=ADD_OPERATION_TYPE,
        target_id=target_id,
        parameters=parameters,
        request_hash=request_hash,
        model_hash=model_hash,
    )
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": "changeset-door-real-001",
        "binding_status": "bound",
        "base_model_fingerprint": model_hash,
        "source_request_hash": request_hash,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "scope": {"target_ids": [target_id], "forbidden_ids": []},
        "evidence_refs": ["request:/operations/0"],
        "preconditions": ["target_exists"],
        "postconditions": ["door_fills_opening"],
        "operations": [
            {
                "operation_id": operation_id,
                "operation_type": ADD_OPERATION_TYPE,
                "target": target,
                "parameters": parameters,
                "evidence_refs": ["request:/operations/0"],
                "semantic_manifest": {
                    "manifest_id": "manifest-door-real-001",
                    "policy_id": "door.add-with-opening.l2",
                    "policy_version": "0.1",
                },
                "semantic_assignments": [assignment],
            }
        ],
    }


def test_add_door_builds_reopenable_hosted_typed_ifc2x3_chain(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "door-case"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id=OPENING_ID,
        window_global_id=WINDOW_ID,
    )
    damaged = case_dir / "damaged.ifc"
    request = (
        "在指定外墙距墙体局部起点 3042.5 mm 处安装一扇 "
        "915×1830 mm 的左开单扇门，门槛高度 305 mm。"
    )
    changeset = _changeset(
        damaged=damaged,
        request=request,
        operation_id="operation-door-real-001",
        target={"wall_global_id": WALL_ID},
        parameters=_parameters(),
    )
    output = tmp_path / "repaired-door.ifc"

    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] and result["published"], json.dumps(
        result["issues"], ensure_ascii=False
    )
    reopened = ifcopenshell.open(str(output))
    created = {
        item["role"]: reopened.by_guid(item["global_id"])
        for item in result["operations"][0]["changes"]["created"]
        if not item["role"].endswith("relationship")
    }
    door = created["door"]
    opening = created["opening"]
    style = created["generated_door_type"]
    assert len(reopened.by_type("IfcDoor")) == 19
    assert len(reopened.by_type("IfcOpeningElement")) == 60
    assert len(reopened.by_type("IfcRelFillsElement")) == 60
    assert door.FillsVoids[0].RelatingOpeningElement == opening
    assert opening.VoidsElements[0].RelatingBuildingElement == reopened.by_guid(
        WALL_ID
    )
    assert door.ContainedInStructure
    assert float(door.OverallWidth) == 915.0
    assert float(door.OverallHeight) == 1830.0
    assert style.is_a("IfcDoorStyle")
    assert style.OperationType == "SINGLE_SWING_LEFT"
    assert style.RepresentationMaps
    assert any(
        relation.is_a("IfcRelDefinesByType")
        and relation.RelatingType == style
        for relation in door.IsDefinedBy
    )
    assert result["postconditions"][0]["valid"] is True
    evaluation = evaluate_repair_application(
        damaged_ifc_path=damaged,
        repaired_ifc_path=output,
        changeset=changeset,
        application_result=result,
        registry=create_default_registry(),
    )
    assert evaluation["l1"]["status"] == "passed", json.dumps(
        evaluation, ensure_ascii=False, default=str
    )
    assert evaluation["l2"]["status"] == "not_evaluable"
    expected_facts = (
        SemanticFact(
            fact_key="relationship:type",
            value=str(style.GlobalId),
            value_type="IfcDoorStyle",
            unit=None,
            inherited=True,
            pset_path=None,
            entity_source="resolved:door",
            source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
            source_ref=f"generated-type:{style.GlobalId}",
            provenance=("test:door-authority",),
            occurrence_scope="door_occurrence",
            canonical_source_kind="deterministic_derived",
        ),
        SemanticFact(
            fact_key="relationship:host",
            value=WALL_ID,
            value_type="IfcWallStandardCase",
            unit=None,
            inherited=False,
            pset_path=None,
            entity_source="resolved:door",
            source_kind=EvidenceSourceKind.SURVIVING_HOST,
            source_ref=f"guid:{WALL_ID}",
            provenance=("test:door-authority",),
            occurrence_scope="door_occurrence",
        ),
        SemanticFact(
            fact_key="relationship:storey",
            value=str(
                door.ContainedInStructure[0].RelatingStructure.GlobalId
            ),
            value_type="IfcBuildingStorey",
            unit=None,
            inherited=False,
            pset_path=None,
            entity_source="resolved:door",
            source_kind=EvidenceSourceKind.SURVIVING_HOST,
            source_ref=f"guid:{WALL_ID}",
            provenance=("test:door-authority",),
            occurrence_scope="door_occurrence",
        ),
        SemanticFact(
            fact_key="attribute:OverallWidth",
            value=915.0,
            value_type="IfcPositiveLengthMeasure",
            unit=None,
            inherited=False,
            pset_path=None,
            entity_source="resolved:door",
            source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
            source_ref="resolved:/door/overall_width_mm",
            provenance=("test:door-authority",),
            occurrence_scope="door_occurrence",
        ),
        SemanticFact(
            fact_key="attribute:OverallHeight",
            value=1830.0,
            value_type="IfcPositiveLengthMeasure",
            unit=None,
            inherited=False,
            pset_path=None,
            entity_source="resolved:door",
            source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
            source_ref="resolved:/door/overall_height_mm",
            provenance=("test:door-authority",),
            occurrence_scope="door_occurrence",
        ),
    )
    production = evaluate_production(
        ProductionEvaluationInputs(
            damaged_ifc_path=damaged,
            repaired_ifc_path=output,
            changeset=changeset,
            application_result=result,
            registry=create_default_registry(),
            expected_facts_by_operation={
                "operation-door-real-001": expected_facts
            },
        )
    )
    assert production.operations[0].levels[0].status.value == "passed"
    assert production.operations[0].levels[1].status.value == "passed", [
        (
            item.check_id,
            item.status.value,
            item.reason,
            [
                (fact.expected_value, fact.actual_value)
                for fact in item.evidence
            ],
        )
        for item in production.operations[0].levels[1].checks
        if item.status.value == "failed"
    ]


def test_fill_surviving_opening_reuses_exact_door_type_without_mutating_it(
    tmp_path: Path,
) -> None:
    door_id = "2cXV28XOjE6f6irgi0COhu"
    opening_id = "2cXV28XOjE6f6irhW0COhu"
    wall_id = "2cXV28XOjE6f6irgi0COfF"
    style_id = "2cXV28XOjE6f6irhu0COgZ"
    model = ifcopenshell.open(str(SOURCE))
    style = model.by_guid(style_id)
    style_before = {
        "name": str(style.Name),
        "operation_type": str(style.OperationType),
        "construction_type": str(style.ConstructionType),
        "parameter_takes_precedence": bool(style.ParameterTakesPrecedence),
        "sizeable": bool(style.Sizeable),
        "representation_map_count": len(style.RepresentationMaps),
    }
    remove_product(model, product=model.by_guid(door_id))
    damaged = tmp_path / "door-removed-opening-survives.ifc"
    model.write(str(damaged))
    reopened_damaged = ifcopenshell.open(str(damaged))
    assert len(reopened_damaged.by_guid(opening_id).HasFillings) == 0

    operation_id = "operation-door-fill-real-001"
    request = (
        "用现有 DoorStyle 2cXV28XOjE6f6irhu0COgZ "
        "填充洞口 2cXV28XOjE6f6irhW0COhu。"
    )
    request_hash = _hash_text(request)
    model_hash = _hash_file(damaged)
    parameters = {
        "position": {
            "reference": "wall_local_start",
            "center_offset_mm": 1657.5,
        },
        "opening": {
            "width_mm": 915.0,
            "height_mm": 2134.0,
            "sill_height_mm": 0.0,
        },
        "door": {
            "overall_width_mm": 915.0,
            "overall_height_mm": 2134.0,
            "operation_type": "SINGLE_SWING_RIGHT",
        },
        "host_wall_global_id": wall_id,
    }
    assignment = {
        "operation_id": operation_id,
        "scope": "door_occurrence",
        "fact_key": "relationship:type",
        "source_fact_key": "relationship:type",
        "value": style_id,
        "value_type": "IfcDoorStyle",
        "unit": None,
        "ownership": "type_inherited",
        "applicability": "required",
        "source_kind": "type_inherited",
        "source_ref": f"formal-type:{style_id}",
        "provenance": ["explicit-type-reuse:test"],
        "authoring_action": "inherit_from_type",
    }
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": "changeset-door-fill-real-001",
        "binding_status": "bound",
        "base_model_fingerprint": model_hash,
        "source_request_hash": request_hash,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "d" * 64,
        "scope": {"target_ids": [opening_id], "forbidden_ids": []},
        "evidence_refs": ["request:/operations/0"],
        "preconditions": ["opening_available"],
        "postconditions": ["door_fills_opening"],
        "operations": [
            {
                "operation_id": operation_id,
                "operation_type": FILL_OPERATION_TYPE,
                "target": {"opening_global_id": opening_id},
                "parameters": parameters,
                "evidence_refs": ["request:/operations/0"],
                "semantic_manifest": {
                    "manifest_id": "manifest-door-fill-real-001",
                    "policy_id": "door.fill-existing-opening.l2",
                    "policy_version": "0.1",
                },
                "semantic_assignments": [assignment],
            }
        ],
    }
    output = tmp_path / "repaired-door-existing-opening.ifc"

    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] and result["published"], json.dumps(
        result["issues"], ensure_ascii=False
    )
    repaired = ifcopenshell.open(str(output))
    opening = repaired.by_guid(opening_id)
    door = opening.HasFillings[0].RelatedBuildingElement
    reused_style = repaired.by_guid(style_id)
    style_after = {
        "name": str(reused_style.Name),
        "operation_type": str(reused_style.OperationType),
        "construction_type": str(reused_style.ConstructionType),
        "parameter_takes_precedence": bool(
            reused_style.ParameterTakesPrecedence
        ),
        "sizeable": bool(reused_style.Sizeable),
        "representation_map_count": len(reused_style.RepresentationMaps),
    }
    assert len(repaired.by_type("IfcOpeningElement")) == 60
    assert len(repaired.by_type("IfcDoor")) == 18
    assert opening.VoidsElements[0].RelatingBuildingElement == repaired.by_guid(
        wall_id
    )
    assert any(
        relation.is_a("IfcRelDefinesByType")
        and relation.RelatingType == reused_style
        for relation in door.IsDefinedBy
    )
    assert style_after == style_before


def test_generated_door_type_tamper_fails_closed_without_output(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "tamper-case"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id=OPENING_ID,
        window_global_id=WINDOW_ID,
    )
    damaged = case_dir / "damaged.ifc"
    request = "在指定墙体位置安装一扇 915×1830 mm 的左开单扇门。"
    changeset = _changeset(
        damaged=damaged,
        request=request,
        operation_id="operation-door-tamper-001",
        target={"wall_global_id": WALL_ID},
        parameters=_parameters(),
    )
    derivation = changeset["operations"][0]["semantic_assignments"][0][
        "derivation"
    ]
    derivation["formal_attributes"]["operation_type"] = "SINGLE_SWING_RIGHT"
    output = tmp_path / "must-not-publish.ifc"

    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] is False
    assert result["published"] is False
    assert result["issues"][0]["code"] == "OPERATION_APPLICATION_FAILED"
    assert "GENERATED_TYPE_TEMPLATE_DIGEST_MISMATCH" in result["issues"][0][
        "message"
    ]
    assert not output.exists()


def test_door_and_opening_semantics_dispatch_to_declared_occurrences(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "semantic-scope-case"
    remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id=OPENING_ID,
        window_global_id=WINDOW_ID,
    )
    damaged = case_dir / "damaged.ifc"
    request = "安装门，并把资产编号写到门实例、洞口宽度写到洞口数量集。"
    changeset = _changeset(
        damaged=damaged,
        request=request,
        operation_id="operation-door-semantics-001",
        target={"wall_global_id": WALL_ID},
        parameters=_parameters(),
    )
    assignments = changeset["operations"][0]["semantic_assignments"]
    assignments.extend(
        [
            {
                "operation_id": "operation-door-semantics-001",
                "scope": "door_occurrence",
                "fact_key": "pset:Custom_Asset.AssetCode",
                "source_fact_key": "request:/properties/0",
                "value": "D-001",
                "value_type": "IfcLabel",
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "explicit_value",
                "source_ref": "request:/properties/0",
                "provenance": ["request:test"],
                "authoring_action": "set_occurrence_pset",
            },
            {
                "operation_id": "operation-door-semantics-001",
                "scope": "opening_occurrence",
                "fact_key": "quantity:BaseQuantities.Width",
                "source_fact_key": "request:/opening/width_mm",
                "value": 915.0,
                "value_type": "IfcQuantityLength",
                "unit": "mm",
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "deterministic_derived",
                "source_ref": "resolved:/opening/width_mm",
                "provenance": ["formula:identity_mm"],
                "derivation": {
                    "formula": "identity_mm",
                    "input_digest": "sha256:" + "a" * 64,
                },
                "authoring_action": "set_quantity",
            },
        ]
    )
    output = tmp_path / "semantic-scope-door.ifc"

    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] and result["published"], json.dumps(
        result["issues"], ensure_ascii=False
    )
    repaired = ifcopenshell.open(str(output))
    created = {
        item["role"]: repaired.by_guid(item["global_id"])
        for item in result["operations"][0]["changes"]["created"]
        if item["role"] in {"door", "opening"}
    }
    door_psets = ifcopenshell.util.element.get_psets(created["door"])
    opening_psets = ifcopenshell.util.element.get_psets(created["opening"])
    assert door_psets["Custom_Asset"]["AssetCode"] == "D-001"
    assert "Custom_Asset" not in opening_psets
    assert opening_psets["BaseQuantities"]["Width"] == 915.0
    assert "BaseQuantities" not in door_psets
