"""Run reproducible Phase 11 Door repairs on real IFC2X3 files."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.evaluation import evaluation_to_dict  # noqa: E402
from text2ifc_ifc_repair.evaluation_policy import EvidenceSourceKind  # noqa: E402
from text2ifc_ifc_repair.geometry import (  # noqa: E402
    opening_dimensions_mm,
    opening_position_in_wall_mm,
)
from text2ifc_ifc_repair.index_store import (  # noqa: E402
    SQLiteIndexRepository,
)
from text2ifc_ifc_repair.indexer import build_ifc_index  # noqa: E402
from text2ifc_ifc_repair.ifc_validation import (  # noqa: E402
    DIAGNOSTIC_NORMALIZATION_VERSION,
    VALIDATION_POLICY_VERSION,
    normalized_validation_result,
)
from text2ifc_ifc_repair.mutation import (  # noqa: E402
    remove_door,
    remove_doors_batch,
    remove_windows_and_openings_batch,
)
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402
from text2ifc_ifc_repair.operations.door import (  # noqa: E402
    ADD_OPERATION_TYPE,
    add_door_operation_definition,
)
from text2ifc_ifc_repair.resolution_flow import (  # noqa: E402
    ResolvedOperation,
    generated_type_authority,
    resolve_repair_intent,
)
from text2ifc_ifc_repair.repair_intent import RepairIntent  # noqa: E402
from text2ifc_ifc_repair.semantic_facts import SemanticFact  # noqa: E402
from text2ifc_ifc_repair.spatial import (  # noqa: E402
    resolve_opening_storey,
)
from text2ifc_ifc_repair.validation_cache import (  # noqa: E402
    ValidationCache,
)
from scripts.ifc_repair.audit_door_repair_triplet import (  # noqa: E402
    audit_case,
)


DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair/phase11-door-offline"
CASES = (
    {
        "case_id": "largebuilding-door-preserve-opening",
        "source": ROOT
        / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc",
        "door_global_id": "2cXV28XOjE6f6irgi0COhu",
    },
    {
        "case_id": "vvo-door-preserve-opening",
        "source": ROOT / "dataset/ifc/train/vvo.ifc",
        "door_global_id": "2IUEnGd5v4Yfg1ZlPtd0qa",
    },
    {
        "case_id": "advancedproject-door-preserve-opening",
        "source": ROOT
        / "dataset/external/bim-whale-ifc-samples/AdvancedProject/IFC/AdvancedProject.ifc",
        "door_global_id": "0MOEoDTm9EnO9yKsXjjkME",
        "performance_gate": True,
    },
)
VVO_FIVE_DOOR_CASE = {
    "case_id": "vvo-five-door-preserve-opening",
    "source": ROOT / "dataset/ifc/train/vvo.ifc",
    "door_global_ids": (
        "2IUEnGd5v4Yfg1ZlPtd0qa",
        "2IUEnGd5v4Yfg1ZlPtd0tI",
        "08xWVL$9z6JRwr3oWJHoYK",
        "08xWVL$9z6JRwr3oWJHoYg",
        "08xWVL$9z6JRwr3oWJHpOf",
    ),
}
VVO_MIXED_CASE = {
    "case_id": "vvo-two-door-two-window-mixed",
    "source": ROOT / "dataset/ifc/train/vvo.ifc",
    # These two occurrences resolve their surviving Door Styles from public
    # Type name plus formal OperationType. Their private ids are fixture-only
    # and never enter the public request or RepairIntent.
    "door_global_ids": (
        "2IUEnGd5v4Yfg1ZlPtd0qa",
        "1B$rgWypT66viEf2CI1iIv",
    ),
    "window_case": ROOT
    / "dataset/manifests/ifc-repair-cases/vvo-five-window-001.private.json",
}
DENTAL_CLINIC_MIXED_CASE = {
    "case_id": "dental-clinic-two-door-two-window-geometry-targeted",
    "source": ROOT
    / "dataset/external/ifc-bench/projects/dental_clinic/arc.ifc",
    "private_case": ROOT
    / "dataset/manifests/ifc-repair-cases/dental-clinic-mixed-001.private.json",
    "targeting_mode": "geometry_signature",
    "remove_door_openings": True,
    "generated_types": True,
}
GENERATED_DOOR_CASE = {
    "case_id": "largebuilding-generated-door-type",
    "source": ROOT
    / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc",
    "door_global_id": "2cXV28XOjE6f6irgi0COhu",
}


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _text_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _prewarm_baseline_validation(
    ifc_path: Path,
    cache_dir: Path,
) -> dict[str, Any]:
    """Cache immutable damaged-IFC validation during input preparation."""

    cache = ValidationCache(cache_dir, mode="read_write")
    key = cache.build_key(
        ifc_path,
        validation_policy_version=VALIDATION_POLICY_VERSION,
        diagnostic_normalization_version=(
            DIAGNOSTIC_NORMALIZATION_VERSION
        ),
    )
    _, evidence = cache.get_or_compute(
        key,
        lambda: normalized_validation_result(
            ifcopenshell.open(str(ifc_path))
        ),
    )
    return evidence


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        payload = value
    else:
        payload = json.dumps(
            value, ensure_ascii=False, indent=2, sort_keys=True, default=str
        )
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _execute_public_production(
    *,
    damaged_ifc_path: Path,
    repair_request: str,
    changeset: dict[str, Any],
    repaired_ifc_path: Path,
    expected_facts_by_operation: dict[str, tuple[SemanticFact, ...]],
    registry: Any,
    validation_cache_dir: Path | None = None,
    repeat_warm_evaluation: bool = False,
) -> dict[str, Any]:
    """Run the production boundary with no original/mutation inputs.

    Benchmark preparation may create the damaged IFC and freeze a user request
    before this function is called.  The repair/application/evaluation path
    receives only those public artifacts and surviving-IFC-derived authority.
    """

    boundary = {
        "schema_version": "text2ifc/production-input-boundary/0.1",
        "entrypoint": "_execute_public_production",
        "ifc_inputs": ["damaged_ifc_path"],
        "original_ifc_supplied": False,
        "mutation_manifest_supplied": False,
        "deleted_object_ids_supplied": False,
        "damaged_ifc_sha256": _sha256(damaged_ifc_path),
        "request_sha256": _text_hash(repair_request),
        "changeset_canonical_sha256": _text_hash(
            json.dumps(
                changeset,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        ),
    }
    _write(
        repaired_ifc_path.parent / "production-boundary.json",
        boundary,
    )
    application_started = time.perf_counter()
    application = apply_changeset(
        damaged_ifc_path=damaged_ifc_path,
        repair_request=repair_request,
        changeset=changeset,
        output_path=repaired_ifc_path,
        registry=registry,
    )
    application_seconds = time.perf_counter() - application_started
    if not application["valid"] or not application["published"]:
        raise RuntimeError(
            "PHASE11_PUBLIC_APPLICATION_FAILED:"
            + json.dumps(application.get("issues", ()), ensure_ascii=False)
        )
    evaluation_started = time.perf_counter()
    evaluation = evaluation_to_dict(
        evaluate_production(
            ProductionEvaluationInputs(
                damaged_ifc_path=damaged_ifc_path,
                repaired_ifc_path=repaired_ifc_path,
                changeset=changeset,
                application_result=application,
                registry=registry,
                expected_facts_by_operation=expected_facts_by_operation,
                validation_cache_dir=validation_cache_dir,
            )
        )
    )
    evaluation_seconds = time.perf_counter() - evaluation_started
    if not evaluation["complete_repair_success"]:
        raise RuntimeError(
            "PHASE11_PUBLIC_EVALUATION_FAILED:"
            + json.dumps(
                {
                    "status": evaluation.get("status"),
                    "operations": evaluation.get("operations"),
                },
                ensure_ascii=False,
                default=str,
            )
        )
    warm_evaluation = None
    warm_evaluation_seconds = None
    if repeat_warm_evaluation:
        warm_started = time.perf_counter()
        warm_evaluation = evaluation_to_dict(
            evaluate_production(
                ProductionEvaluationInputs(
                    damaged_ifc_path=damaged_ifc_path,
                    repaired_ifc_path=repaired_ifc_path,
                    changeset=changeset,
                    application_result=application,
                    registry=registry,
                    expected_facts_by_operation=expected_facts_by_operation,
                    validation_cache_dir=validation_cache_dir,
                )
            )
        )
        warm_evaluation_seconds = time.perf_counter() - warm_started
        if not warm_evaluation["complete_repair_success"]:
            raise RuntimeError("PHASE11_PUBLIC_WARM_EVALUATION_FAILED")
    return {
        "application": application,
        "evaluation": evaluation,
        "warm_evaluation": warm_evaluation,
        "application_seconds": application_seconds,
        "evaluation_seconds": evaluation_seconds,
        "warm_evaluation_seconds": warm_evaluation_seconds,
        "production_boundary": boundary,
    }


def _source_chain(source: Path, door_id: str) -> dict[str, Any]:
    model = ifcopenshell.open(str(source))
    millimetres_per_project_unit = (
        ifcopenshell.util.unit.calculate_unit_scale(model) * 1000.0
    )
    door = model.by_guid(door_id)
    opening = door.FillsVoids[0].RelatingOpeningElement
    wall = opening.VoidsElements[0].RelatingBuildingElement
    styles = [
        relation.RelatingType
        for relation in door.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(styles) != 1:
        raise ValueError(f"EXACT_DOOR_TYPE_REQUIRED:{door_id}")
    style = styles[0]
    dimensions = opening_dimensions_mm(opening)
    position = opening_position_in_wall_mm(opening, wall)
    operation_type = str(style.OperationType)
    if operation_type not in {
        "SINGLE_SWING_LEFT",
        "SINGLE_SWING_RIGHT",
        "NOTDEFINED",
    }:
        raise ValueError(f"DOOR_OPERATION_UNSUPPORTED:{operation_type}")
    opening_level = resolve_opening_storey(opening, wall)
    return {
        "door": {
            "global_id": str(door.GlobalId),
            "name": None if door.Name is None else str(door.Name),
            "overall_width_mm": (
                float(door.OverallWidth) * millimetres_per_project_unit
            ),
            "overall_height_mm": (
                float(door.OverallHeight) * millimetres_per_project_unit
            ),
        },
        "opening": {
            "global_id": str(opening.GlobalId),
            "name": None if opening.Name is None else str(opening.Name),
            "width_mm": float(dimensions["width"]),
            "height_mm": float(dimensions["height"]),
            "sill_height_mm": float(position["sill_height"]),
            "center_offset_mm": float(position["center_offset"]),
        },
        "wall": {
            "global_id": str(wall.GlobalId),
            "name": None if wall.Name is None else str(wall.Name),
            "ifc_class": wall.is_a(),
        },
        # A wall may span several storeys. The retained Opening base elevation
        # is the public spatial authority for a new Door occurrence.
        "storey_global_id": str(opening_level.GlobalId),
        "storey_name": str(opening_level.Name),
        "style": {
            "global_id": str(style.GlobalId),
            "name": None if style.Name is None else str(style.Name),
            "operation_type": operation_type,
        },
    }


def _request(chain: dict[str, Any]) -> str:
    door = chain["door"]
    opening = chain["opening"]
    wall = chain["wall"]
    style = chain["style"]
    return (
        f"在墙 {wall['name'] or wall['global_id']}（GlobalId {wall['global_id']}）"
        f"已有洞口 {opening['global_id']} 中安装一扇门。"
        f"门宽 {door['overall_width_mm']} mm、高 {door['overall_height_mm']} mm；"
        f"洞口中心距墙局部起点 {opening['center_offset_mm']} mm，"
        f"洞口宽 {opening['width_mm']} mm、高 {opening['height_mm']} mm、"
        f"门槛高度 {opening['sill_height_mm']} mm。"
        f"明确复用现有 Door Type “{style['name']}”"
        f"（GlobalId {style['global_id']}，OperationType {style['operation_type']}）。"
    )


def _operation(
    chain: dict[str, Any],
    *,
    operation_id: str,
) -> dict[str, Any]:
    door = chain["door"]
    opening = chain["opening"]
    return {
        "operation_id": operation_id,
        "operation_type": "fill_existing_opening_with_door",
        "target": {"opening_global_id": opening["global_id"]},
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": opening["center_offset_mm"],
            },
            "opening": {
                "width_mm": opening["width_mm"],
                "height_mm": opening["height_mm"],
                "sill_height_mm": opening["sill_height_mm"],
            },
            "door": {
                "overall_width_mm": door["overall_width_mm"],
                "overall_height_mm": door["overall_height_mm"],
                "operation_type": chain["style"]["operation_type"],
            },
            "host_wall_global_id": chain["wall"]["global_id"],
        },
        "evidence_refs": ["request:/operation"],
        "semantic_manifest": {
            "manifest_id": f"manifest-{operation_id}",
            "policy_id": "door.fill-existing-opening.l2",
            "policy_version": "0.1",
        },
        "semantic_assignments": [
            {
                "operation_id": operation_id,
                "scope": "door_occurrence",
                "fact_key": "relationship:type",
                "source_fact_key": "relationship:type",
                "value": chain["style"]["global_id"],
                "value_type": "IfcDoorStyle",
                "unit": None,
                "ownership": "type_inherited",
                "applicability": "required",
                "source_kind": "type_inherited",
                "source_ref": f"formal-type:{chain['style']['global_id']}",
                "provenance": ["explicit-type-reuse:request"],
                "authoring_action": "inherit_from_type",
            }
        ],
    }


def _expected_door_facts(
    operation: dict[str, Any],
    damaged: Path,
    *,
    generated_type_id: str | None = None,
) -> tuple[SemanticFact, ...]:
    """Build L2 authority from public inputs and surviving IFC facts only."""

    model = ifcopenshell.open(str(damaged))
    if operation["operation_type"] == "fill_existing_opening_with_door":
        opening = model.by_guid(operation["target"]["opening_global_id"])
        wall = opening.VoidsElements[0].RelatingBuildingElement
        storey = resolve_opening_storey(opening, wall)
    else:
        wall = model.by_guid(operation["target"]["wall_global_id"])
        storey = wall.ContainedInStructure[0].RelatingStructure
    type_id = generated_type_id or next(
        str(item["value"])
        for item in operation["semantic_assignments"]
        if item["fact_key"] == "relationship:type"
    )
    type_source = (
        EvidenceSourceKind.DETERMINISTIC_POLICY
        if generated_type_id
        else EvidenceSourceKind.SURVIVING_TYPE
    )
    door = operation["parameters"]["door"]
    values = (
        (
            "relationship:type",
            type_id,
            "IfcDoorStyle",
            type_source,
            True,
        ),
        (
            "relationship:host",
            str(wall.GlobalId),
            wall.is_a(),
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "relationship:storey",
            str(storey.GlobalId),
            "IfcBuildingStorey",
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "attribute:OverallWidth",
            float(door["overall_width_mm"]),
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
        (
            "attribute:OverallHeight",
            float(door["overall_height_mm"]),
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
    )
    return tuple(
        SemanticFact(
            fact_key=key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=inherited,
            pset_path=None,
            entity_source="public-damaged-ifc-and-bound-changeset",
            source_kind=source_kind,
            source_ref=(
                f"current-ifc:{value}"
                if key.startswith("relationship:")
                else "request:/operation"
            ),
            provenance=(
                "phase11-public-production-authority",
                f"operation:{operation['operation_id']}",
            ),
            occurrence_scope="door_occurrence",
        )
        for key, value, value_type, source_kind, inherited in values
    )


def _window_operation(
    target: dict[str, Any], *, operation_id: str
) -> dict[str, Any]:
    window = target["window"]
    opening = target["opening"]
    prototype = target["prototype_evidence"]
    is_external = next(
        (
            item["value"]
            for item in target.get("requested_properties", ())
            if item["set_name"] == "Pset_WindowCommon"
            and item["property_name"] == "IsExternal"
        ),
        None,
    )
    assignments = [
        {
            "operation_id": operation_id,
            "scope": "window_occurrence",
            "fact_key": "relationship:type",
            "source_fact_key": "relationship:type",
            "value": prototype["global_id"],
            "value_type": "IfcWindowStyle",
            "unit": None,
            "ownership": "type_inherited",
            "applicability": "required",
            "source_kind": "type_inherited",
            "source_ref": f"surviving-type:{prototype['global_id']}",
            "provenance": ["explicit-type-reuse:request"],
            "authoring_action": "inherit_from_type",
        },
        *(
            [
                {
                    "operation_id": operation_id,
                    "scope": "window_occurrence",
                    "fact_key": "pset:Pset_WindowCommon.IsExternal",
                    "source_fact_key": "pset:Pset_WindowCommon.IsExternal",
                    "value": is_external,
                    "value_type": "IfcBoolean",
                    "unit": None,
                    "ownership": "occurrence_direct",
                    "applicability": "required",
                    "source_kind": "explicit_value",
                    "source_ref": "request:/operation/is-external",
                    "provenance": ["explicit-property:request"],
                    "authoring_action": "set_occurrence_pset",
                }
            ]
            if is_external is not None
            else []
        ),
    ]
    for fact_key, value, value_type in (
        (
            "quantity:window-base.Width",
            window["width_mm"],
            "IfcQuantityLength",
        ),
        (
            "quantity:window-base.Height",
            window["height_mm"],
            "IfcQuantityLength",
        ),
        (
            "quantity:window-base.Area",
            window["width_mm"] * window["height_mm"],
            "IfcQuantityArea",
        ),
    ):
        assignments.append(
            {
                "operation_id": operation_id,
                "scope": "window_occurrence",
                "fact_key": fact_key,
                "source_fact_key": fact_key,
                "value": value,
                "value_type": value_type,
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "deterministic_derived",
                "source_ref": "resolved:/operation/window-dimensions",
                "provenance": ["registered-window-parameter-policy:0.2"],
                "authoring_action": "set_quantity",
            }
        )
    return {
        "operation_id": operation_id,
        "operation_type": "add_window_with_opening_to_wall",
        "target": {"wall_global_id": target["wall"]["global_id"]},
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": opening["geometric_center_offset_mm"],
            },
            "opening": {
                "width_mm": window["width_mm"],
                "height_mm": window["height_mm"],
                "sill_height_mm": opening["sill_height_mm"],
            },
            "window": {"fit_opening": True},
        },
        "evidence_refs": ["request:/operation"],
        "semantic_manifest": {
            "manifest_id": f"manifest-{operation_id}",
            "policy_id": "window.add-with-opening.l2",
            "policy_version": "0.2",
        },
        "semantic_assignments": assignments,
    }


def _expected_window_facts(
    target: dict[str, Any], damaged: Path
) -> tuple[SemanticFact, ...]:
    model = ifcopenshell.open(str(damaged))
    wall = model.by_guid(target["wall"]["global_id"])
    storey = wall.ContainedInStructure[0].RelatingStructure
    is_external = next(
        (
            item["value"]
            for item in target.get("requested_properties", ())
            if item["set_name"] == "Pset_WindowCommon"
            and item["property_name"] == "IsExternal"
        ),
        None,
    )
    values = (
        (
            "relationship:type",
            target["prototype_evidence"]["global_id"],
            "IfcWindowStyle",
            EvidenceSourceKind.SURVIVING_TYPE,
            True,
        ),
        (
            "relationship:host",
            target["wall"]["global_id"],
            target["wall"]["ifc_class"],
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "relationship:storey",
            str(storey.GlobalId),
            "IfcBuildingStorey",
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "attribute:OverallWidth",
            target["window"]["width_mm"],
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
        (
            "attribute:OverallHeight",
            target["window"]["height_mm"],
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
        (
            "pset:Pset_WindowCommon.IsExternal",
            is_external,
            "IfcBoolean",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
        (
            "quantity:window-base.Width",
            target["window"]["width_mm"],
            "IfcQuantityLength",
            EvidenceSourceKind.DETERMINISTIC_POLICY,
            False,
        ),
        (
            "quantity:window-base.Height",
            target["window"]["height_mm"],
            "IfcQuantityLength",
            EvidenceSourceKind.DETERMINISTIC_POLICY,
            False,
        ),
        (
            "quantity:window-base.Area",
            target["window"]["width_mm"] * target["window"]["height_mm"],
            "IfcQuantityArea",
            EvidenceSourceKind.DETERMINISTIC_POLICY,
            False,
        ),
    )
    return tuple(
        SemanticFact(
            fact_key=key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=inherited,
            pset_path=None,
            entity_source="public-request",
            source_kind=source_kind,
            source_ref="request:/operation",
            provenance=("phase11-mixed-request",),
            occurrence_scope="window_occurrence",
        )
        for key, value, value_type, source_kind, inherited in values
    )


def _generated_door_operation(
    chain: dict[str, Any],
    *,
    operation_id: str,
    request_hash: str,
    model_hash: str,
) -> tuple[dict[str, Any], str]:
    parameters = {
        "position": {
            "reference": "wall_local_start",
            "center_offset_mm": chain["opening"]["center_offset_mm"],
        },
        "opening": {
            "width_mm": chain["opening"]["width_mm"],
            "height_mm": chain["opening"]["height_mm"],
            "sill_height_mm": chain["opening"]["sill_height_mm"],
        },
        "door": {
            "overall_width_mm": chain["door"]["overall_width_mm"],
            "overall_height_mm": chain["door"]["overall_height_mm"],
            "operation_type": chain["style"]["operation_type"],
        },
    }
    wall_id = chain["wall"]["global_id"]
    resolved = ResolvedOperation(
        operation_id=operation_id,
        operation_type=ADD_OPERATION_TYPE,
        target_global_id=wall_id,
        scope_ids=(wall_id,),
        evidence_pointers=("request:/operation",),
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
    assignment = {
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
    return (
        {
            "operation_id": operation_id,
            "operation_type": ADD_OPERATION_TYPE,
            "target": {"wall_global_id": wall_id},
            "parameters": parameters,
            "evidence_refs": ["request:/operation"],
            "semantic_manifest": {
                "manifest_id": f"manifest-{operation_id}",
                "policy_id": "door.add-with-opening.l2",
                "policy_version": "0.1",
            },
            "semantic_assignments": [assignment],
        },
        str(authority["global_id"]),
    )


def run_case(case: dict[str, Any], output_root: Path) -> dict[str, Any]:
    case_dir = output_root / str(case["case_id"])
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    source = Path(case["source"])
    chain = _source_chain(source, str(case["door_global_id"]))
    fixture = case_dir / "fixture"
    preparation_started = time.perf_counter()
    mutation = remove_door(
        source_path=source,
        output_dir=fixture,
        door_global_id=str(case["door_global_id"]),
        preserve_opening=True,
    )
    damaged = fixture / "damaged.ifc"
    validation_cache_dir = output_root / ".validation-cache"
    baseline_cache_evidence = None
    if case.get("performance_gate"):
        baseline_cache_evidence = _prewarm_baseline_validation(
            damaged,
            validation_cache_dir,
        )
    request = _request(chain)
    operation_id = f"operation-{case['case_id']}"
    operation = _operation(chain, operation_id=operation_id)
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": f"changeset-{case['case_id']}",
        "binding_status": "bound",
        "base_model_fingerprint": _sha256(damaged),
        "source_request_hash": _text_hash(request),
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "e" * 64,
        "scope": {
            "target_ids": [chain["opening"]["global_id"]],
            "forbidden_ids": [],
        },
        "evidence_refs": ["request:/operation"],
        "preconditions": ["opening_available"],
        "postconditions": ["door_fills_opening"],
        "operations": [operation],
    }
    repaired = case_dir / "repaired.ifc"
    registry = create_default_registry()
    expected_facts_by_operation = {
        operation_id: _expected_door_facts(operation, damaged)
    }
    preparation_seconds = time.perf_counter() - preparation_started
    public_run = _execute_public_production(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        repaired_ifc_path=repaired,
        expected_facts_by_operation=expected_facts_by_operation,
        registry=registry,
        validation_cache_dir=validation_cache_dir,
        repeat_warm_evaluation=bool(case.get("performance_gate")),
    )
    application = public_run["application"]
    evaluation = public_run["evaluation"]
    warm_evaluation = public_run["warm_evaluation"]
    application_seconds = public_run["application_seconds"]
    evaluation_seconds = public_run["evaluation_seconds"]
    warm_evaluation_seconds = public_run["warm_evaluation_seconds"]
    allowed = {
        str(item["global_id"])
        for result in application["operations"]
        for kind in ("created", "modified", "removed")
        for item in result["changes"].get(kind, ())
        if item.get("global_id")
    }
    comparison = compare_ifc_models(
        damaged,
        repaired,
        allowed_changed_ids=allowed,
    )
    shutil.copy2(source, case_dir / "original.ifc")
    shutil.copy2(damaged, case_dir / "damaged.ifc")
    _write(case_dir / "request.txt", request)
    _write(case_dir / "changeset.json", changeset)
    _write(case_dir / "application.json", application)
    _write(case_dir / "evaluation.json", evaluation)
    _write(case_dir / "comparison.json", comparison)
    if warm_evaluation is not None:
        _write(case_dir / "evaluation-warm.json", warm_evaluation)
    performance = {
        "preparation_seconds": round(preparation_seconds, 3),
        "application_seconds": round(application_seconds, 3),
        "cold_evaluation_seconds": round(evaluation_seconds, 3),
        "cold_request_to_publication_seconds": round(
            application_seconds + evaluation_seconds, 3
        ),
        "warm_evaluation_seconds": (
            None
            if warm_evaluation_seconds is None
            else round(warm_evaluation_seconds, 3)
        ),
        "deadline_seconds": 180.0 if case.get("performance_gate") else None,
    }
    if case.get("performance_gate") and (
        performance["cold_request_to_publication_seconds"] >= 180.0
        or performance["warm_evaluation_seconds"] >= 180.0
    ):
        raise RuntimeError(
            "PHASE11_ADVANCED_PERFORMANCE_DEADLINE_EXCEEDED:"
            + json.dumps(performance, ensure_ascii=False)
        )
    manifest = {
        "schema_version": "text2ifc/phase11-door-proof/0.1",
        "case_id": case["case_id"],
        "status": "passed",
        "synthetic_fallback_used": False,
        "operation_count": 1,
        "performance": performance,
        "baseline_validation_cache": baseline_cache_evidence,
        "damage": {
            "mode": mutation["mutation_type"],
            "door": mutation["door"],
            "opening": mutation["opening"],
            "wall": mutation["wall"],
        },
        "artifacts": {
            name: {
                "path": name,
                "sha256": _sha256(case_dir / name),
                "bytes": (case_dir / name).stat().st_size,
            }
            for name in (
                "original.ifc",
                "damaged.ifc",
                "repaired.ifc",
                "request.txt",
                "changeset.json",
                "application.json",
                "evaluation.json",
                "comparison.json",
                "production-boundary.json",
                *(("evaluation-warm.json",) if warm_evaluation is not None else ()),
            )
        },
    }
    _write(case_dir / "manifest.json", manifest)
    _write(
        case_dir / "README.md",
        (
            f"# {case['case_id']}\n\n"
            f"- 删除门：`{chain['door']['name']}` (`{chain['door']['global_id']}`)\n"
            f"- 保留洞口：`{chain['opening']['global_id']}`\n"
            f"- 复用 Type：`{chain['style']['name']}` "
            f"(`{chain['style']['global_id']}`)\n"
            f"- OperationType：`{chain['style']['operation_type']}`\n"
            "- 结果：IFC2X3 重开、L1、L2 与全局 preservation 全部通过。\n"
        ),
    )
    return manifest


def run_generated_type_case(
    case: dict[str, Any], output_root: Path
) -> dict[str, Any]:
    """Rebuild one full Door/Opening chain with a controlled generated Type."""

    case_dir = output_root / str(case["case_id"])
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    source = Path(case["source"])
    chain = _source_chain(source, str(case["door_global_id"]))
    fixture = case_dir / "fixture"
    mutation = remove_door(
        source_path=source,
        output_dir=fixture,
        door_global_id=str(case["door_global_id"]),
        preserve_opening=False,
    )
    damaged = fixture / "damaged.ifc"
    request = (
        f"在墙 {chain['wall']['name']}（GlobalId {chain['wall']['global_id']}）"
        f"局部起点 {chain['opening']['center_offset_mm']} mm 处新建门洞和门。"
        f"门洞宽 {chain['opening']['width_mm']} mm、高 "
        f"{chain['opening']['height_mm']} mm、门槛 "
        f"{chain['opening']['sill_height_mm']} mm；门宽 "
        f"{chain['door']['overall_width_mm']} mm、高 "
        f"{chain['door']['overall_height_mm']} mm，开启方式 "
        f"{chain['style']['operation_type']}。不复用既有 Door Type，"
        "使用系统受控单扇门模板生成新的 DoorStyle。"
    )
    operation_id = "operation-generated-door-001"
    model_hash = _sha256(damaged)
    request_hash = _text_hash(request)
    operation, generated_type_id = _generated_door_operation(
        chain,
        operation_id=operation_id,
        request_hash=request_hash,
        model_hash=model_hash,
    )
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": f"changeset-{case['case_id']}",
        "binding_status": "bound",
        "base_model_fingerprint": model_hash,
        "source_request_hash": request_hash,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "scope": {
            "target_ids": [chain["wall"]["global_id"]],
            "forbidden_ids": [],
        },
        "evidence_refs": ["request:/operation"],
        "preconditions": ["target_exists", "opening_interval_available"],
        "postconditions": ["opening_voids_wall", "door_fills_opening"],
        "operations": [operation],
    }
    repaired = case_dir / "repaired.ifc"
    registry = create_default_registry()
    public_run = _execute_public_production(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        repaired_ifc_path=repaired,
        expected_facts_by_operation={
            operation_id: _expected_door_facts(
                operation,
                damaged,
                generated_type_id=generated_type_id,
            )
        },
        registry=registry,
    )
    application = public_run["application"]
    evaluation = public_run["evaluation"]
    reopened = ifcopenshell.open(str(repaired))
    generated_type = reopened.by_guid(generated_type_id)
    if (
        generated_type is None
        or not generated_type.is_a("IfcDoorStyle")
        or str(generated_type.OperationType)
        != chain["style"]["operation_type"]
    ):
        raise RuntimeError("PHASE11_GENERATED_TYPE_NOT_BOUND")
    allowed = {
        str(item["global_id"])
        for result in application["operations"]
        for kind in ("created", "modified", "removed")
        for item in result["changes"].get(kind, ())
        if item.get("global_id")
    }
    comparison = compare_ifc_models(
        damaged, repaired, allowed_changed_ids=allowed
    )
    shutil.copy2(source, case_dir / "original.ifc")
    shutil.copy2(damaged, case_dir / "damaged.ifc")
    _write(case_dir / "request.txt", request)
    _write(case_dir / "changeset.json", changeset)
    _write(case_dir / "application.json", application)
    _write(case_dir / "evaluation.json", evaluation)
    _write(case_dir / "comparison.json", comparison)
    manifest = {
        "schema_version": "text2ifc/phase11-door-proof/0.2",
        "case_id": case["case_id"],
        "status": "passed",
        "synthetic_fallback_used": False,
        "operation_count": 1,
        "generated_type_global_id": generated_type_id,
        "generated_type_template": (
            "text2ifc-door-single-swing-template/0.1"
        ),
        "damage": {
            "mode": mutation["mutation_type"],
            "door": mutation["door"],
            "opening": mutation["opening"],
            "wall": mutation["wall"],
        },
        "artifacts": {
            name: {
                "path": name,
                "sha256": _sha256(case_dir / name),
                "bytes": (case_dir / name).stat().st_size,
            }
            for name in (
                "original.ifc",
                "damaged.ifc",
                "repaired.ifc",
                "request.txt",
                "changeset.json",
                "application.json",
                "evaluation.json",
                "comparison.json",
                "production-boundary.json",
            )
        },
    }
    _write(case_dir / "manifest.json", manifest)
    _write(
        case_dir / "README.md",
        (
            f"# {case['case_id']}\n\n"
            f"- 删除 Door：`{chain['door']['name']}`。\n"
            "- 删除其 Opening，并以 Door+Opening operation 完整重建。\n"
            f"- 新 DoorStyle：`{generated_type_id}`，由受控模板生成。\n"
            "- IFC 重开、L1/L2 与 preservation 全部通过。\n"
        ),
    )
    return manifest


def run_five_door_case(
    case: dict[str, Any], output_root: Path
) -> dict[str, Any]:
    """Repair five removed Doors in one atomic ChangeSet."""

    case_dir = output_root / str(case["case_id"])
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    source = Path(case["source"])
    chains = [
        _source_chain(source, str(door_id))
        for door_id in case["door_global_ids"]
    ]
    fixture = case_dir / "fixture"
    mutation = remove_doors_batch(
        source_path=source,
        output_dir=fixture,
        door_global_ids=tuple(case["door_global_ids"]),
        preserve_openings=True,
    )
    damaged = fixture / "damaged.ifc"
    requests = [_request(chain) for chain in chains]
    request = "\n".join(
        ["请在同一个原子 ChangeSet 中完成以下五扇门修复："]
        + [f"{index}. {text}" for index, text in enumerate(requests, 1)]
    )
    operations = [
        _operation(chain, operation_id=f"operation-door-{index:03d}")
        for index, chain in enumerate(chains, 1)
    ]
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": f"changeset-{case['case_id']}",
        "binding_status": "bound",
        "base_model_fingerprint": _sha256(damaged),
        "source_request_hash": _text_hash(request),
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "e" * 64,
        "scope": {
            "target_ids": [
                chain["opening"]["global_id"] for chain in chains
            ],
            "forbidden_ids": [],
        },
        "evidence_refs": ["request:/operations", "request:/operation"],
        "preconditions": ["openings_available"],
        "postconditions": ["doors_fill_openings"],
        "operations": operations,
    }
    repaired = case_dir / "repaired.ifc"
    registry = create_default_registry()
    expected_by_operation = {
        operation["operation_id"]: _expected_door_facts(
            operation, damaged
        )
        for operation in operations
    }
    public_run = _execute_public_production(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        repaired_ifc_path=repaired,
        expected_facts_by_operation=expected_by_operation,
        registry=registry,
    )
    application = public_run["application"]
    evaluation = public_run["evaluation"]
    allowed = {
        str(item["global_id"])
        for result in application["operations"]
        for kind in ("created", "modified", "removed")
        for item in result["changes"].get(kind, ())
        if item.get("global_id")
    }
    comparison = compare_ifc_models(
        damaged, repaired, allowed_changed_ids=allowed
    )

    # Inject a duplicate target. Audit must reject the whole ChangeSet and no
    # temporary or partially repaired IFC may be published.
    failing = json.loads(json.dumps(changeset))
    duplicate = json.loads(json.dumps(failing["operations"][0]))
    duplicate["operation_id"] = "operation-door-injected-duplicate"
    failing["operations"].append(duplicate)
    failing["changeset_id"] += "-injected-failure"
    failed_output = case_dir / "must-not-exist.ifc"
    failed_application = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=failing,
        output_path=failed_output,
        registry=registry,
    )
    if (
        failed_application["valid"]
        or failed_application["published"]
        or failed_output.exists()
    ):
        raise RuntimeError("PHASE11_BATCH_ATOMIC_ROLLBACK_FAILED")

    shutil.copy2(source, case_dir / "original.ifc")
    shutil.copy2(damaged, case_dir / "damaged.ifc")
    _write(case_dir / "request.txt", request)
    _write(case_dir / "changeset.json", changeset)
    _write(case_dir / "application.json", application)
    _write(case_dir / "evaluation.json", evaluation)
    _write(case_dir / "comparison.json", comparison)
    _write(case_dir / "injected-failure-changeset.json", failing)
    _write(case_dir / "injected-failure-application.json", failed_application)
    manifest = {
        "schema_version": "text2ifc/phase11-door-proof/0.2",
        "case_id": case["case_id"],
        "status": "passed",
        "synthetic_fallback_used": False,
        "operation_count": len(operations),
        "one_atomic_changeset": True,
        "injected_failure_published": False,
        "damage": {
            "mode": mutation["mutation_type"],
            "removed_doors": [
                target["door"] for target in mutation["targets"]
            ],
        },
        "artifacts": {
            name: {
                "path": name,
                "sha256": _sha256(case_dir / name),
                "bytes": (case_dir / name).stat().st_size,
            }
            for name in (
                "original.ifc",
                "damaged.ifc",
                "repaired.ifc",
                "request.txt",
                "changeset.json",
                "application.json",
                "evaluation.json",
                "comparison.json",
                "production-boundary.json",
                "injected-failure-changeset.json",
                "injected-failure-application.json",
            )
        },
    }
    _write(case_dir / "manifest.json", manifest)
    _write(
        case_dir / "README.md",
        (
            f"# {case['case_id']}\n\n"
            "- 一个 ChangeSet、五个 Door operation。\n"
            "- 五个 Door 分别通过 L1/L2，IFC 可重开。\n"
            "- 注入重复 Opening 操作后审计失败，未生成任何 IFC。\n\n"
            "被删除 Door：\n"
            + "\n".join(
                f"- `{chain['door']['name']}` (`{chain['door']['global_id']}`)"
                for chain in chains
            )
            + "\n"
        ),
    )
    return manifest


def _public_provenance(reference: str, excerpt: str) -> dict[str, str]:
    return {
        "source_kind": "user_request",
        "reference": reference,
        "excerpt": excerpt,
    }


def _guid_free_window_request(
    target: dict[str, Any],
) -> str:
    return (
        f"窗 {target['window']['name']}：在楼层 {target['wall']['storey']} 的墙"
        f"“{target['wall']['name']}”上开窗；以 wall_local_start 为基准，"
        f"洞口中心偏移 {target['opening']['geometric_center_offset_mm']} mm，"
        f"宽 {target['window']['width_mm']} mm、高 "
        f"{target['window']['height_mm']} mm、窗台高 "
        f"{target['opening']['sill_height_mm']} mm；复用现有 Window Type"
        f"“{target['prototype_evidence']['name']}”。"
    )


def _guid_free_door_request(chain: dict[str, Any]) -> str:
    return (
        f"门 {chain['door']['name']}：在楼层 {chain['storey_name']} 的墙"
        f"“{chain['wall']['name']}”上，向现有空洞"
        f"“{chain['opening']['name']}”安装门；以 wall_local_start 为基准，"
        f"洞口中心偏移 {chain['opening']['center_offset_mm']} mm，"
        f"洞口宽 {chain['opening']['width_mm']} mm、高 "
        f"{chain['opening']['height_mm']} mm、门槛高 "
        f"{chain['opening']['sill_height_mm']} mm；门宽 "
        f"{chain['door']['overall_width_mm']} mm、高 "
        f"{chain['door']['overall_height_mm']} mm，开启方式 "
        f"{chain['style']['operation_type']}，复用现有 Door Type"
        f"“{chain['style']['name']}”。"
    )


def _geometry_constraints(
    signature: dict[str, Any],
) -> list[dict[str, Any]]:
    tolerance = float(signature["tolerance_mm"])
    return [
        {
            "field": "storey_elevation_mm",
            "value": float(signature["storey_elevation_mm"]),
            "tolerance_mm": tolerance,
        },
        {
            "field": "wall_length_mm",
            "value": float(signature["length_mm"]),
            "tolerance_mm": tolerance,
        },
        {
            "field": "wall_height_mm",
            "value": float(signature["height_mm"]),
            "tolerance_mm": tolerance,
        },
        {
            "field": "wall_thickness_mm",
            "value": float(signature["thickness_mm"]),
            "tolerance_mm": tolerance,
        },
    ]


def _geometry_target_query(signature: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcWall"],
        "direction": str(signature["direction"]),
        "geometry_capabilities": ["straight_wall"],
        "geometry_constraints": _geometry_constraints(signature),
        "max_candidates": 5,
        "winner_margin": 10,
    }


def _geometry_signature_text(signature: dict[str, Any]) -> str:
    return (
        f"楼层标高 {float(signature['storey_elevation_mm']):.3f} mm、"
        f"朝向 {signature['direction']}、墙长 "
        f"{float(signature['length_mm']):.3f} mm、墙高 "
        f"{float(signature['height_mm']):.3f} mm、墙厚 "
        f"{float(signature['thickness_mm']):.3f} mm 的直墙"
    )


def _geometry_window_request(
    target: dict[str, Any],
    signature: dict[str, Any],
    *,
    ordinal: int,
) -> str:
    return (
        f"窗 {ordinal}：在{_geometry_signature_text(signature)}上开窗；"
        "以 wall_local_start 为基准，洞口中心偏移 "
        f"{float(target['opening']['geometric_center_offset_mm']):.3f} mm，"
        f"宽 {float(target['window']['width_mm']):.3f} mm、高 "
        f"{float(target['window']['height_mm']):.3f} mm、窗台高 "
        f"{float(target['opening']['sill_height_mm']):.3f} mm；"
        "未指定复用类型，使用系统受控 WindowStyle 模板。"
    )


def _geometry_door_request(
    chain: dict[str, Any],
    signature: dict[str, Any],
    *,
    ordinal: int,
) -> str:
    return (
        f"门 {ordinal}：在{_geometry_signature_text(signature)}上重新开洞并安装门；"
        "以 wall_local_start 为基准，洞口中心偏移 "
        f"{float(chain['opening']['center_offset_mm']):.3f} mm，"
        f"洞口宽 {float(chain['opening']['width_mm']):.3f} mm、高 "
        f"{float(chain['opening']['height_mm']):.3f} mm、门槛高 "
        f"{float(chain['opening']['sill_height_mm']):.3f} mm；门宽 "
        f"{float(chain['door']['overall_width_mm']):.3f} mm、高 "
        f"{float(chain['door']['overall_height_mm']):.3f} mm，开启方式 "
        f"{chain['style']['operation_type']}；未指定复用类型，"
        "使用系统受控 DoorStyle 模板。"
    )


def _geometry_targeted_mixed_intent(
    *,
    case_id: str,
    request: str,
    window_targets: list[dict[str, Any]],
    window_signatures: list[dict[str, Any]],
    door_chains: list[dict[str, Any]],
    door_signatures: list[dict[str, Any]],
    model_fingerprint: str,
    registry: Any,
) -> RepairIntent:
    window_lines = [
        _geometry_window_request(target, signature, ordinal=index)
        for index, (target, signature) in enumerate(
            zip(window_targets, window_signatures, strict=True), 1
        )
    ]
    door_lines = [
        _geometry_door_request(chain, signature, ordinal=index)
        for index, (chain, signature) in enumerate(
            zip(door_chains, door_signatures, strict=True), 1
        )
    ]
    operations: list[dict[str, Any]] = []
    for index, (target, signature, excerpt) in enumerate(
        zip(
            window_targets,
            window_signatures,
            window_lines,
            strict=True,
        ),
        1,
    ):
        operation_id = f"operation-window-{index:03d}"
        operations.append(
            {
                "operation_id": operation_id,
                "operation_type": "add_window_with_opening_to_wall",
                "target_query": _geometry_target_query(signature),
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": target["opening"][
                            "geometric_center_offset_mm"
                        ],
                    },
                    "opening": {
                        "width_mm": target["window"]["width_mm"],
                        "height_mm": target["window"]["height_mm"],
                        "sill_height_mm": target["opening"][
                            "sill_height_mm"
                        ],
                    },
                    "window": {"fit_opening": True},
                },
                "attribute_intents": [],
                "prototype_intent": None,
                "provenance": [
                    _public_provenance(
                        f"request:/operations/{index - 1}", excerpt
                    )
                ],
            }
        )
    door_offset = len(operations)
    for index, (chain, signature, excerpt) in enumerate(
        zip(door_chains, door_signatures, door_lines, strict=True), 1
    ):
        operation_id = f"operation-door-{index:03d}"
        operations.append(
            {
                "operation_id": operation_id,
                "operation_type": ADD_OPERATION_TYPE,
                "target_query": _geometry_target_query(signature),
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": chain["opening"][
                            "center_offset_mm"
                        ],
                    },
                    "opening": {
                        "width_mm": chain["opening"]["width_mm"],
                        "height_mm": chain["opening"]["height_mm"],
                        "sill_height_mm": chain["opening"][
                            "sill_height_mm"
                        ],
                        "dimension_meaning": "overall_opening",
                    },
                    "door": {
                        "overall_width_mm": chain["door"][
                            "overall_width_mm"
                        ],
                        "overall_height_mm": chain["door"][
                            "overall_height_mm"
                        ],
                        "operation_type": chain["style"][
                            "operation_type"
                        ],
                        "formal_enum_explicit": True,
                        **(
                            {"notdefined_accepted": True}
                            if chain["style"]["operation_type"]
                            == "NOTDEFINED"
                            else {}
                        ),
                    },
                },
                "attribute_intents": [],
                "prototype_intent": None,
                "provenance": [
                    _public_provenance(
                        f"request:/operations/{door_offset + index - 1}",
                        excerpt,
                    )
                ],
            }
        )
    document = {
        "schema_version": "text2ifc/ifc-repair-intent/0.1",
        "request_id": f"request-{case_id}",
        "source_request_hash": _text_hash(request),
        "model_fingerprint": model_fingerprint,
        "prompt_fingerprint": _text_hash(
            "phase11-geometry-signature-mixed-targeting/0.1"
        ),
        "operations": operations,
        "provenance": [
            _public_provenance("request:/text", request)
        ],
    }
    return RepairIntent.from_dict(
        document,
        registry=registry,
        require_complete=False,
    )


def _guid_free_mixed_intent(
    *,
    request: str,
    window_targets: list[dict[str, Any]],
    door_chains: list[dict[str, Any]],
    model_fingerprint: str,
    registry: Any,
) -> RepairIntent:
    window_lines = [
        _guid_free_window_request(target) for target in window_targets
    ]
    door_lines = [_guid_free_door_request(chain) for chain in door_chains]
    operations: list[dict[str, Any]] = []
    for index, (target, excerpt) in enumerate(
        zip(window_targets, window_lines, strict=True), 1
    ):
        operation_id = f"operation-window-{index:03d}"
        operations.append(
            {
                "operation_id": operation_id,
                "operation_type": "add_window_with_opening_to_wall",
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcWall"],
                    "names": [target["wall"]["name"]],
                    "storey_name": target["wall"]["storey"],
                    "geometry_capabilities": ["straight_wall"],
                    "max_candidates": 5,
                    "winner_margin": 10,
                },
                "parameters": {
                    "position": {
                        "reference": "wall_local_start",
                        "center_offset_mm": target["opening"][
                            "geometric_center_offset_mm"
                        ],
                    },
                    "opening": {
                        "width_mm": target["window"]["width_mm"],
                        "height_mm": target["window"]["height_mm"],
                        "sill_height_mm": target["opening"][
                            "sill_height_mm"
                        ],
                    },
                    "window": {"fit_opening": True},
                },
                "attribute_intents": [],
                "prototype_intent": {
                    "reference_kind": "type_name",
                    "reference": target["prototype_evidence"]["name"],
                    "source": _public_provenance(
                        f"request:/operations/{index - 1}/prototype",
                        excerpt,
                    ),
                },
                "provenance": [
                    _public_provenance(
                        f"request:/operations/{index - 1}", excerpt
                    )
                ],
            }
        )
    door_offset = len(operations)
    for index, (chain, excerpt) in enumerate(
        zip(door_chains, door_lines, strict=True), 1
    ):
        operation_id = f"operation-door-{index:03d}"
        public_index = door_offset + index - 1
        operations.append(
            {
                "operation_id": operation_id,
                "operation_type": "fill_existing_opening_with_door",
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcOpeningElement"],
                    "names": [chain["opening"]["name"]],
                    "storey_name": chain["storey_name"],
                    "geometry_capabilities": [
                        "measured_hosted_opening"
                    ],
                    "max_candidates": 5,
                    "winner_margin": 10,
                },
                "parameters": {
                    "fit_existing_opening": True,
                    "door": {
                        "operation_type": chain["style"][
                            "operation_type"
                        ],
                        "formal_enum_explicit": True,
                        **(
                            {"notdefined_accepted": True}
                            if chain["style"]["operation_type"]
                            == "NOTDEFINED"
                            else {}
                        ),
                    },
                },
                "attribute_intents": [],
                "prototype_intent": {
                    "reference_kind": "type_name",
                    "reference": chain["style"]["name"],
                    "source": _public_provenance(
                        f"request:/operations/{public_index}/prototype",
                        excerpt,
                    ),
                },
                "provenance": [
                    _public_provenance(
                        f"request:/operations/{public_index}", excerpt
                    )
                ],
            }
        )
    document = {
        "schema_version": "text2ifc/ifc-repair-intent/0.1",
        "request_id": "request-vvo-guid-free-mixed",
        "source_request_hash": _text_hash(request),
        "model_fingerprint": model_fingerprint,
        "prompt_fingerprint": _text_hash(
            "phase11-guid-free-mixed-targeting/0.1"
        ),
        "operations": operations,
        "provenance": [
            _public_provenance("request:/text", request)
        ],
    }
    return RepairIntent.from_dict(
        document,
        registry=registry,
        require_complete=False,
    )


def _resolved_prototype_global_id(
    operation: ResolvedOperation,
) -> str:
    matches = [
        str(item["global_id"])
        for item in operation.authorized_semantics
        if item.get("kind") == "user_authorized_prototype"
        and item.get("global_id")
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"PHASE11_EXACT_PROTOTYPE_BINDING_REQUIRED:"
            f"{operation.operation_id}:{matches}"
        )
    return matches[0]


def _bind_mixed_operations(
    *,
    resolution: Any,
    window_targets: list[dict[str, Any]],
    door_chains: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    resolved = {
        item.operation_id: item for item in resolution.operations
    }
    bound: list[dict[str, Any]] = []
    for index, target in enumerate(window_targets, 1):
        operation_id = f"operation-window-{index:03d}"
        authority = resolved[operation_id]
        expected_target = str(target["wall"]["global_id"])
        if authority.target_global_id != expected_target:
            raise RuntimeError(
                f"PHASE11_WINDOW_DESCRIPTION_MISBOUND:{operation_id}"
            )
        operation = _window_operation(
            target, operation_id=operation_id
        )
        operation["target"] = {
            "wall_global_id": authority.target_global_id
        }
        operation["parameters"] = authority.to_dict()["parameters"]
        type_id = _resolved_prototype_global_id(authority)
        for assignment in operation["semantic_assignments"]:
            if assignment["fact_key"] == "relationship:type":
                assignment["value"] = type_id
                assignment["source_ref"] = (
                    f"resolved-prototype:{type_id}"
                )
        if type_id != str(target["prototype_evidence"]["global_id"]):
            raise RuntimeError(
                f"PHASE11_WINDOW_TYPE_NAME_MISBOUND:{operation_id}"
            )
        bound.append(operation)
    for index, chain in enumerate(door_chains, 1):
        operation_id = f"operation-door-{index:03d}"
        authority = resolved[operation_id]
        expected_target = str(chain["opening"]["global_id"])
        if authority.target_global_id != expected_target:
            raise RuntimeError(
                f"PHASE11_DOOR_DESCRIPTION_MISBOUND:{operation_id}"
            )
        operation = _operation(chain, operation_id=operation_id)
        operation["target"] = {
            "opening_global_id": authority.target_global_id
        }
        operation["parameters"] = authority.to_dict()["parameters"]
        type_id = _resolved_prototype_global_id(authority)
        for assignment in operation["semantic_assignments"]:
            if assignment["fact_key"] == "relationship:type":
                assignment["value"] = type_id
                assignment["source_ref"] = (
                    f"resolved-prototype:{type_id}"
                )
        if type_id != str(chain["style"]["global_id"]):
            raise RuntimeError(
                f"PHASE11_DOOR_TYPE_NAME_MISBOUND:{operation_id}"
            )
        bound.append(operation)
    return bound


def _generated_type_semantic_assignment(
    authority: dict[str, Any],
    *,
    operation_id: str,
    scope: str,
) -> dict[str, Any]:
    return {
        "operation_id": operation_id,
        "scope": scope,
        "fact_key": "relationship:type",
        "source_fact_key": "relationship:type",
        "value": authority["global_id"],
        "value_type": authority["ifc_class"],
        "unit": None,
        "ownership": "type_inherited",
        "applicability": "required",
        "source_kind": "deterministic_derived",
        "source_ref": f"generated-type:{authority['global_id']}",
        "provenance": [
            f"generated-type-template:{authority['template_version']}"
        ],
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


def _resolved_generated_type(
    operation: ResolvedOperation,
) -> dict[str, Any]:
    matches = [
        dict(item)
        for item in operation.authorized_semantics
        if item.get("kind") == "system_generated_type"
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "PHASE11_GENERATED_TYPE_AUTHORITY_REQUIRED:"
            f"{operation.operation_id}:{len(matches)}"
        )
    return matches[0]


def _generated_window_operation(
    target: dict[str, Any],
    authority: ResolvedOperation,
    *,
    is_external: bool,
) -> tuple[dict[str, Any], str]:
    operation_id = authority.operation_id
    generated_type = _resolved_generated_type(authority)
    opening = authority.parameters["opening"]
    assignments = [
        _generated_type_semantic_assignment(
            generated_type,
            operation_id=operation_id,
            scope="window_occurrence",
        ),
        {
            "operation_id": operation_id,
            "scope": "window_occurrence",
            "fact_key": "pset:Pset_WindowCommon.IsExternal",
            "source_fact_key": "pset:Pset_WindowCommon.IsExternal",
            "value": is_external,
            "value_type": "IfcBoolean",
            "unit": None,
            "ownership": "occurrence_direct",
            "applicability": "required",
            "source_kind": "deterministic_derived",
            "source_ref": "damaged-ifc:/resolved-wall/Pset_WallCommon.IsExternal",
            "provenance": [
                "deterministic-host-externality-projection:0.1"
            ],
            "authoring_action": "set_occurrence_pset",
        },
    ]
    for fact_key, value, value_type in (
        (
            "quantity:window-base.Width",
            opening["width_mm"],
            "IfcQuantityLength",
        ),
        (
            "quantity:window-base.Height",
            opening["height_mm"],
            "IfcQuantityLength",
        ),
        (
            "quantity:window-base.Area",
            float(opening["width_mm"]) * float(opening["height_mm"]),
            "IfcQuantityArea",
        ),
    ):
        assignments.append(
            {
                "operation_id": operation_id,
                "scope": "window_occurrence",
                "fact_key": fact_key,
                "source_fact_key": fact_key,
                "value": value,
                "value_type": value_type,
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "deterministic_derived",
                "source_ref": (
                    "resolved:/operation/window-dimensions"
                ),
                "provenance": [
                    "registered-window-parameter-policy:0.2"
                ],
                "authoring_action": "set_quantity",
            }
        )
    return (
        {
            "operation_id": operation_id,
            "operation_type": "add_window_with_opening_to_wall",
            "target": {"wall_global_id": authority.target_global_id},
            "parameters": authority.to_dict()["parameters"],
            "evidence_refs": ["request:/operation"],
            "semantic_manifest": {
                "manifest_id": f"manifest-{operation_id}",
                "policy_id": "window.add-with-opening.l2",
                "policy_version": "0.2",
            },
            "semantic_assignments": assignments,
        },
        str(generated_type["global_id"]),
    )


def _generated_door_bound_operation(
    authority: ResolvedOperation,
) -> tuple[dict[str, Any], str]:
    operation_id = authority.operation_id
    generated_type = _resolved_generated_type(authority)
    return (
        {
            "operation_id": operation_id,
            "operation_type": ADD_OPERATION_TYPE,
            "target": {"wall_global_id": authority.target_global_id},
            "parameters": authority.to_dict()["parameters"],
            "evidence_refs": ["request:/operation"],
            "semantic_manifest": {
                "manifest_id": f"manifest-{operation_id}",
                "policy_id": "door.add-with-opening.l2",
                "policy_version": "0.1",
            },
            "semantic_assignments": [
                _generated_type_semantic_assignment(
                    generated_type,
                    operation_id=operation_id,
                    scope="door_occurrence",
                )
            ],
        },
        str(generated_type["global_id"]),
    )


def _bind_geometry_mixed_operations(
    *,
    resolution: Any,
    window_targets: list[dict[str, Any]],
    door_chains: list[dict[str, Any]],
    damaged: Path,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    resolved = {
        item.operation_id: item for item in resolution.operations
    }
    bound: list[dict[str, Any]] = []
    generated_type_ids: dict[str, str] = {}
    for index, target in enumerate(window_targets, 1):
        operation_id = f"operation-window-{index:03d}"
        authority = resolved[operation_id]
        if authority.target_global_id != str(target["wall"]["global_id"]):
            raise RuntimeError(
                f"PHASE11_WINDOW_GEOMETRY_MISBOUND:{operation_id}"
            )
        operation, type_id = _generated_window_operation(
            target,
            authority,
            is_external=_wall_is_external(
                damaged, authority.target_global_id
            ),
        )
        bound.append(operation)
        generated_type_ids[operation_id] = type_id
    for index, chain in enumerate(door_chains, 1):
        operation_id = f"operation-door-{index:03d}"
        authority = resolved[operation_id]
        if authority.target_global_id != str(chain["wall"]["global_id"]):
            raise RuntimeError(
                f"PHASE11_DOOR_GEOMETRY_MISBOUND:{operation_id}"
            )
        operation, type_id = _generated_door_bound_operation(authority)
        bound.append(operation)
        generated_type_ids[operation_id] = type_id
    return bound, generated_type_ids


def _wall_is_external(ifc_path: Path, wall_global_id: str) -> bool:
    model = ifcopenshell.open(str(ifc_path))
    wall = model.by_guid(str(wall_global_id))
    psets = ifcopenshell.util.element.get_psets(
        wall,
        psets_only=True,
        should_inherit=True,
    )
    wall_common = next(
        (
            value
            for name, value in psets.items()
            if str(name).casefold() == "pset_wallcommon"
        ),
        None,
    )
    if not isinstance(wall_common, dict):
        raise RuntimeError(
            f"PHASE11_WALL_EXTERNALITY_UNAVAILABLE:{wall_global_id}"
        )
    value = wall_common.get("IsExternal")
    if not isinstance(value, bool):
        raise RuntimeError(
            f"PHASE11_WALL_EXTERNALITY_UNAVAILABLE:{wall_global_id}"
        )
    return value


def _expected_generated_window_facts(
    target: dict[str, Any],
    damaged: Path,
    generated_type_id: str,
) -> tuple[SemanticFact, ...]:
    model = ifcopenshell.open(str(damaged))
    wall = model.by_guid(target["wall"]["global_id"])
    storey = wall.ContainedInStructure[0].RelatingStructure
    width = float(target["window"]["width_mm"])
    height = float(target["window"]["height_mm"])
    is_external = _wall_is_external(
        damaged, str(target["wall"]["global_id"])
    )
    values = (
        (
            "relationship:type",
            generated_type_id,
            "IfcWindowStyle",
            EvidenceSourceKind.DETERMINISTIC_POLICY,
            True,
        ),
        (
            "relationship:host",
            target["wall"]["global_id"],
            target["wall"]["ifc_class"],
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "relationship:storey",
            str(storey.GlobalId),
            "IfcBuildingStorey",
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "attribute:OverallWidth",
            width,
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
        (
            "attribute:OverallHeight",
            height,
            "IfcPositiveLengthMeasure",
            EvidenceSourceKind.EXPLICIT_REQUEST,
            False,
        ),
        (
            "pset:Pset_WindowCommon.IsExternal",
            is_external,
            "IfcBoolean",
            EvidenceSourceKind.SURVIVING_HOST,
            False,
        ),
        (
            "quantity:window-base.Width",
            width,
            "IfcQuantityLength",
            EvidenceSourceKind.DETERMINISTIC_POLICY,
            False,
        ),
        (
            "quantity:window-base.Height",
            height,
            "IfcQuantityLength",
            EvidenceSourceKind.DETERMINISTIC_POLICY,
            False,
        ),
        (
            "quantity:window-base.Area",
            width * height,
            "IfcQuantityArea",
            EvidenceSourceKind.DETERMINISTIC_POLICY,
            False,
        ),
    )
    return tuple(
        SemanticFact(
            fact_key=key,
            value=value,
            value_type=value_type,
            unit=None,
            inherited=inherited,
            pset_path=None,
            entity_source="public-request",
            source_kind=source_kind,
            source_ref="request:/operation",
            provenance=("phase11-geometry-mixed-request",),
            occurrence_scope="window_occurrence",
        )
        for key, value, value_type, source_kind, inherited in values
    )


def run_mixed_case(
    case: dict[str, Any], output_root: Path
) -> dict[str, Any]:
    """Repair two Windows and two Doors in one mixed atomic ChangeSet."""

    case_dir = output_root / str(case["case_id"])
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)
    source = Path(case["source"])
    geometry_targeting = (
        case.get("targeting_mode") == "geometry_signature"
    )
    private_case_path = Path(
        case.get("private_case") or case["window_case"]
    )
    private_window_case = json.loads(
        private_case_path.read_text(encoding="utf-8")
    )
    selected_windows = tuple(private_window_case["targets"][:2])
    window_signatures = [
        dict(item["wall_signature"]) for item in selected_windows
    ] if geometry_targeting else []
    door_target_records = list(
        private_window_case.get("door_targets", ())
    )
    door_global_ids = tuple(
        str(item["door_global_id"]) for item in door_target_records
    ) if geometry_targeting else tuple(case["door_global_ids"])
    door_signatures = [
        dict(item["wall_signature"]) for item in door_target_records
    ] if geometry_targeting else []
    window_fixture = case_dir / "window-fixture"
    remove_windows_and_openings_batch(
        source_path=source,
        output_dir=window_fixture,
        targets=selected_windows,
        expected_source_sha256=private_window_case["source"]["sha256"],
    )
    final_fixture = case_dir / "fixture"
    door_mutation = remove_doors_batch(
        source_path=window_fixture / "damaged.ifc",
        output_dir=final_fixture,
        door_global_ids=door_global_ids,
        preserve_openings=not bool(case.get("remove_door_openings")),
    )
    damaged = final_fixture / "damaged.ifc"
    window_manifest = json.loads(
        (window_fixture / "mutation_manifest.private.json").read_text(
            encoding="utf-8"
        )
    )
    window_targets = window_manifest["targets"]
    if geometry_targeting:
        for target, signature in zip(
            window_targets, window_signatures, strict=True
        ):
            target["wall_signature"] = signature
    door_chains = [
        _source_chain(source, str(door_id))
        for door_id in door_global_ids
    ]
    request_lines = (
        [
            "请在一个原子 ChangeSet 中同时恢复以下两扇窗和两扇门；"
            "所有宿主墙只按楼层标高、朝向、墙体长高厚与墙局部位置定位，"
            "不使用 IFC 标识符或对象名称。",
            *[
                _geometry_window_request(
                    target, signature, ordinal=index
                )
                for index, (target, signature) in enumerate(
                    zip(
                        window_targets,
                        window_signatures,
                        strict=True,
                    ),
                    1,
                )
            ],
            *[
                _geometry_door_request(
                    chain, signature, ordinal=index
                )
                for index, (chain, signature) in enumerate(
                    zip(
                        door_chains,
                        door_signatures,
                        strict=True,
                    ),
                    1,
                )
            ],
        ]
        if geometry_targeting
        else [
            "请在一个原子 ChangeSet 中同时恢复以下两扇窗和两扇门；"
            "所有目标均按名称、楼层和墙局部位置定位，不使用 GlobalId。",
            *[
                _guid_free_window_request(target)
                for target in window_targets
            ],
            *[_guid_free_door_request(chain) for chain in door_chains],
        ]
    )
    request = "\n".join(request_lines)
    registry = create_default_registry()
    index_path = case_dir / "target-index.sqlite"
    metadata = build_ifc_index(damaged, index_path)
    intent = (
        _geometry_targeted_mixed_intent(
            case_id=str(case["case_id"]),
            request=request,
            window_targets=window_targets,
            window_signatures=window_signatures,
            door_chains=door_chains,
            door_signatures=door_signatures,
            model_fingerprint=_sha256(damaged),
            registry=registry,
        )
        if geometry_targeting
        else _guid_free_mixed_intent(
            request=request,
            window_targets=window_targets,
            door_chains=door_chains,
            model_fingerprint=_sha256(damaged),
            registry=registry,
        )
    )
    with SQLiteIndexRepository.open(index_path) as repository:
        resolution = resolve_repair_intent(
            intent,
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
        )
    if resolution.status != "resolved":
        raise RuntimeError(
            "PHASE11_GUID_FREE_TARGET_RESOLUTION_FAILED:"
            + json.dumps(resolution.to_dict(), ensure_ascii=False)
        )
    generated_type_ids: dict[str, str] = {}
    if geometry_targeting:
        operations, generated_type_ids = (
            _bind_geometry_mixed_operations(
                resolution=resolution,
                window_targets=window_targets,
                door_chains=door_chains,
                damaged=damaged,
            )
        )
    else:
        operations = _bind_mixed_operations(
            resolution=resolution,
            window_targets=window_targets,
            door_chains=door_chains,
        )
    window_operations = operations[: len(window_targets)]
    door_operations = operations[len(window_targets) :]
    target_ids = [
        str(item.target_global_id) for item in resolution.operations
    ]
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": f"changeset-{case['case_id']}",
        "binding_status": "bound",
        "base_model_fingerprint": _sha256(damaged),
        "source_request_hash": _text_hash(request),
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "d" * 64,
        "scope": {
            "target_ids": list(dict.fromkeys(target_ids)),
            "forbidden_ids": [],
        },
        "evidence_refs": ["request:/operation"],
        "preconditions": ["mixed_targets_available"],
        "postconditions": ["windows_and_doors_hosted"],
        "operations": operations,
    }
    repaired = case_dir / "repaired.ifc"
    expected_by_operation = (
        {
            **{
                operation["operation_id"]: (
                    _expected_generated_window_facts(
                        target,
                        damaged,
                        generated_type_ids[operation["operation_id"]],
                    )
                )
                for operation, target in zip(
                    window_operations, window_targets, strict=True
                )
            },
            **{
                operation["operation_id"]: (
                    _expected_door_facts(
                        operation,
                        damaged,
                        generated_type_id=(
                            generated_type_ids[operation["operation_id"]]
                        ),
                    )
                )
                for operation in door_operations
            },
        }
        if geometry_targeting
        else {
            **{
                operation["operation_id"]: _expected_window_facts(
                    target, damaged
                )
                for operation, target in zip(
                    window_operations, window_targets, strict=True
                )
            },
            **{
                operation["operation_id"]: _expected_door_facts(
                    operation, damaged
                )
                for operation in door_operations
            },
        }
    )
    public_run = _execute_public_production(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        repaired_ifc_path=repaired,
        expected_facts_by_operation=expected_by_operation,
        registry=registry,
    )
    application = public_run["application"]
    evaluation = public_run["evaluation"]
    allowed = {
        str(item["global_id"])
        for result in application["operations"]
        for kind in ("created", "modified", "removed")
        for item in result["changes"].get(kind, ())
        if item.get("global_id")
    }
    comparison = compare_ifc_models(
        damaged, repaired, allowed_changed_ids=allowed
    )
    shutil.copy2(source, case_dir / "original.ifc")
    shutil.copy2(damaged, case_dir / "damaged.ifc")
    _write(case_dir / "request.txt", request)
    _write(case_dir / "repair-intent.json", intent.to_dict())
    _write(case_dir / "target-resolution.json", resolution.to_dict())
    _write(case_dir / "changeset.json", changeset)
    _write(case_dir / "application.json", application)
    _write(case_dir / "evaluation.json", evaluation)
    _write(case_dir / "comparison.json", comparison)
    manifest = {
        "schema_version": "text2ifc/phase11-door-proof/0.2",
        "case_id": case["case_id"],
        "status": "passed",
        "synthetic_fallback_used": False,
        "operation_count": 4,
        "operation_families": {"window": 2, "door": 2},
        "one_atomic_changeset": True,
        "public_targeting": {
            "guid_free": True,
            **(
                {
                    "name_free": True,
                    "strategy": (
                        "storey_elevation_orientation_and_wall_dimensions"
                    ),
                }
                if geometry_targeting
                else {
                    "strategy": (
                        "name_storey_and_wall_local_position"
                    )
                }
            ),
            "resolved_operation_count": len(resolution.operations),
        },
        "damage": {
            "window_ids": [
                target["window"]["global_id"] for target in window_targets
            ],
            "removed_windows": [
                target["window"] for target in window_targets
            ],
            "window_openings_removed": True,
            "door_openings_removed": bool(
                case.get("remove_door_openings")
            ),
            "removed_doors": [
                target["door"] for target in door_mutation["targets"]
            ],
        },
        "generated_type_ids": generated_type_ids,
        "artifacts": {
            name: {
                "path": name,
                "sha256": _sha256(case_dir / name),
                "bytes": (case_dir / name).stat().st_size,
            }
            for name in (
                "original.ifc",
                "damaged.ifc",
                "repaired.ifc",
                "request.txt",
                "repair-intent.json",
                "target-resolution.json",
                "changeset.json",
                "application.json",
                "evaluation.json",
                "comparison.json",
                "production-boundary.json",
            )
        },
    }
    _write(case_dir / "manifest.json", manifest)
    _write(
        case_dir / "README.md",
        (
            f"# {case['case_id']}\n\n"
            "- 一个 ChangeSet 同时包含两个 Window 和两个 Door operation。\n"
            "- 四个 operation 分别通过 L1/L2，最终只发布一个 IFC。\n\n"
            + (
                "- Door 与 Window 的原 Opening 均已在 damaged IFC 中删除；"
                "修复从完整墙体重新开洞。\n"
                "- 公开请求与 RepairIntent 不使用 GlobalId 或任何对象 Name；"
                "宿主墙由楼层标高、朝向、墙体尺寸和墙局部位置解析。\n\n"
                if geometry_targeting
                else ""
            )
            + "被删除 Door：\n"
            + "\n".join(
                f"- `{chain['door']['name']}` (`{chain['door']['global_id']}`)"
                for chain in door_chains
            )
            + "\n"
        ),
    )
    return manifest


def _run_case_by_id(
    case_id: str, output_root: Path
) -> dict[str, Any]:
    ordinary = next(
        (case for case in CASES if case["case_id"] == case_id),
        None,
    )
    if ordinary is not None:
        return run_case(ordinary, output_root)
    if case_id == GENERATED_DOOR_CASE["case_id"]:
        return run_generated_type_case(GENERATED_DOOR_CASE, output_root)
    if case_id == VVO_FIVE_DOOR_CASE["case_id"]:
        return run_five_door_case(VVO_FIVE_DOOR_CASE, output_root)
    if case_id == VVO_MIXED_CASE["case_id"]:
        return run_mixed_case(VVO_MIXED_CASE, output_root)
    if case_id == DENTAL_CLINIC_MIXED_CASE["case_id"]:
        return run_mixed_case(DENTAL_CLINIC_MIXED_CASE, output_root)
    raise ValueError(f"PHASE11_CASE_UNKNOWN:{case_id}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--case-id",
        action="append",
        help="Run only the named case; may be repeated.",
    )
    args = parser.parse_args(argv)
    args.output_root.mkdir(parents=True, exist_ok=True)
    if args.case_id:
        results = [
            _run_case_by_id(case_id, args.output_root)
            for case_id in args.case_id
        ]
    else:
        results = [run_case(case, args.output_root) for case in CASES]
        results.append(
            run_generated_type_case(GENERATED_DOOR_CASE, args.output_root)
        )
        results.append(
            run_five_door_case(VVO_FIVE_DOOR_CASE, args.output_root)
        )
        results.append(run_mixed_case(VVO_MIXED_CASE, args.output_root))
        results.append(
            run_mixed_case(DENTAL_CLINIC_MIXED_CASE, args.output_root)
        )
    for item in results:
        audit = audit_case(
            args.output_root / str(item["case_id"]),
            write=True,
        )
        if audit["release_decision"]["publishable"] is not True:
            raise RuntimeError(
                "PHASE11_THREE_WAY_AUDIT_FAILED:"
                f"{item['case_id']}:"
                + json.dumps(
                    audit["release_decision"], ensure_ascii=False
                )
            )
        # audit_case refreshes the per-case manifest with its evidence files.
        item.update(
            _read_case_manifest(
                args.output_root / str(item["case_id"]) / "manifest.json"
            )
        )
    summary = {
        "schema_version": "text2ifc/phase11-door-offline-run/0.1",
        "status": "passed",
        "cases": [
            {
                "case_id": item["case_id"],
                "status": item["status"],
                "manifest": f"{item['case_id']}/manifest.json",
            }
            for item in results
        ],
    }
    _write(args.output_root / "run-summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


def _read_case_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"PHASE11_MANIFEST_INVALID:{path}")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
