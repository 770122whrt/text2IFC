from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import ifcopenshell
import pytest

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.audit import audit_changeset
from text2ifc_ifc_repair.evaluation import evaluate_independent_l1
from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
from text2ifc_ifc_repair.evaluation_policy import (
    STRUCTURAL_L1_THRESHOLDS,
    EvidenceSourceKind,
    SemanticApplicability,
    compare_structural_l1_measurement,
    extend_policy_with_explicit_facts,
)
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.beam import (
    BEAM_EVALUATION_POLICY,
    beam_operation_definition,
)
from text2ifc_ifc_repair.operations.column import column_operation_definition
from text2ifc_ifc_repair.operations.structural_member import (
    resolve_structural_member_frame,
)
from text2ifc_ifc_repair.registry import OperationRegistry
from text2ifc_ifc_repair.resolution_flow import (
    ResolvedOperation,
    generated_type_authority,
)
from text2ifc_ifc_repair.semantic_facts import (
    SemanticFact,
    evaluate_operation_semantics,
)


ROOT = Path(__file__).resolve().parents[2]
D7N = ROOT / "dataset" / "ifc" / "test" / "d7n.ifc"
D7N_STOREY_ID = "0K_MqVdrL0JOCMi_GblRwJ"
FOUR_FAMILY_CASE = (
    ROOT
    / "dataset"
    / "processed"
    / "proof"
    / "ifc-repair-success-cases"
    / "mixed"
    / "door-window"
    / "vvo-authority-triplet-public-repair"
)
VVO_STOREY_ID = "1vTeahUkP60PdWqwCTjSGJ"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _request_hash(request: str) -> str:
    return "sha256:" + hashlib.sha256(request.encode("utf-8")).hexdigest()


def _beam_parameters() -> dict:
    return {
        "axis": {
            "start": {"x_mm": 100000, "y_mm": 100000, "z_mm": 3000},
            "end": {"x_mm": 103000, "y_mm": 104000, "z_mm": 3000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 300,
            "height_mm": 500,
        },
    }


def _column_parameters(*, support_contact: bool = True) -> dict:
    x_mm, y_mm = ((103000, 104000) if support_contact else (106000, 106000))
    return {
        "axis": {
            "base": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": 0},
            "top": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": 6000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 0, "y": 1},
        },
    }


def _type_assignment(
    *,
    family: str,
    operation_id: str,
    storey_id: str,
    request_hash: str,
    model_hash: str,
    parameters: dict,
) -> dict:
    definition = (
        beam_operation_definition()
        if family == "beam"
        else column_operation_definition()
    )
    operation_type = f"add_{family}"
    ifc_type = f"Ifc{family.title()}Type"
    resolved = ResolvedOperation(
        operation_id=operation_id,
        operation_type=operation_type,
        target_global_id=storey_id,
        scope_ids=(storey_id,),
        evidence_pointers=(f"request:/operations/{operation_id}",),
        parameters=parameters,
        context={},
    )
    authority = generated_type_authority(
        definition,
        operation_id=operation_id,
        request_hash=request_hash,
        model_fingerprint=model_hash,
        resolved_operation=resolved,
    )
    return {
        "operation_id": operation_id,
        "scope": f"{family}_occurrence",
        "fact_key": "relationship:type",
        "source_fact_key": "relationship:type",
        "value": authority["global_id"],
        "value_type": ifc_type,
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


def _structural_operation(
    *,
    family: str,
    operation_id: str,
    storey_id: str,
    request_hash: str,
    model_hash: str,
    parameters: dict,
) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": f"add_{family}",
        "target": {"storey_global_id": storey_id},
        "parameters": parameters,
        "evidence_refs": [f"request:/operations/{operation_id}"],
        "semantic_manifest": {
            "manifest_id": f"manifest-{operation_id}",
            "policy_id": f"{family}.add.l2",
            "policy_version": "0.1",
        },
        "semantic_assignments": [
            _type_assignment(
                family=family,
                operation_id=operation_id,
                storey_id=storey_id,
                request_hash=request_hash,
                model_hash=model_hash,
                parameters=parameters,
            )
        ],
    }


def _structural_changeset(
    *,
    request: str,
    duplicate_beam: bool = False,
    support_contact: bool = True,
) -> dict:
    request_digest = _request_hash(request)
    model_hash = _sha256(D7N)
    operations = [
        _structural_operation(
            family="beam",
            operation_id="mixed-beam-1",
            storey_id=D7N_STOREY_ID,
            request_hash=request_digest,
            model_hash=model_hash,
            parameters=_beam_parameters(),
        )
    ]
    if duplicate_beam:
        operations.append(
            _structural_operation(
                family="beam",
                operation_id="mixed-beam-duplicate",
                storey_id=D7N_STOREY_ID,
                request_hash=request_digest,
                model_hash=model_hash,
                parameters=deepcopy(_beam_parameters()),
            )
        )
    else:
        operations.append(
            _structural_operation(
                family="column",
                operation_id="mixed-column-1",
                storey_id=D7N_STOREY_ID,
                request_hash=request_digest,
                model_hash=model_hash,
                parameters=_column_parameters(support_contact=support_contact),
            )
        )
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": "changeset-structural-atomicity-1",
        "binding_status": "bound",
        "base_model_fingerprint": model_hash,
        "source_request_hash": request_digest,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "scope": {"target_ids": [D7N_STOREY_ID], "forbidden_ids": []},
        "evidence_refs": [
            "request:/operations",
            *(
                reference
                for operation in operations
                for reference in operation["evidence_refs"]
            ),
        ],
        "preconditions": ["structural_targets_available"],
        "postconditions": ["structural_operations_atomic"],
        "operations": operations,
    }


def _role_mapping(application: dict) -> dict[str, str]:
    return {
        str(item["role"]): str(item["global_id"])
        for change_kind in ("created", "modified", "removed")
        for item in application.get(change_kind, ())
        if item.get("role") and item.get("global_id")
    }


def _measurement_at_thresholds() -> tuple[dict, dict]:
    expected = resolve_structural_member_frame(
        occurrence_class="IfcBeam",
        axis_start_mm=(0, 0, 0),
        axis_end_mm=(1000, 0, 0),
        section={"shape": "rectangle", "width_mm": 100, "height_mm": 200},
    )
    angle = math.radians(STRUCTURAL_L1_THRESHOLDS.direction_degrees)
    measured = {
        "axis_start_mm": (5.0, 0.0, 0.0),
        "axis_end_mm": (1005.0, 0.0, 0.0),
        "axis_direction": (math.cos(angle), math.sin(angle), 0.0),
        "axis_extent_mm": 1001.0,
        "section": {
            "shape": "rectangle",
            "width_mm": 101.0,
            "height_mm": 201.0,
        },
        "orientation": (math.cos(angle), math.sin(angle), 0.0),
        "representation_type": "SweptSolid",
    }
    return expected, measured


def test_structural_l1_thresholds_pass_at_limits_without_volume_proxy() -> None:
    expected, measured = _measurement_at_thresholds()
    report = compare_structural_l1_measurement(
        family="beam", expected=expected, measured=measured
    )

    assert all(
        check["status"] == "passed" for check in report["l1_checks"].values()
    )
    assert not any("volume" in check_id for check_id in report["l1_checks"])
    assert report["metrics"]["max_axis_point_error_mm"] == pytest.approx(5.0)
    assert report["metrics"]["direction_error_degrees"] == pytest.approx(0.1)
    assert report["metrics"]["member_dimension_error_mm"] == pytest.approx(1.0)
    assert report["metrics"]["max_section_dimension_error_mm"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("defect", "failed_check"),
    (
        ("axis_point", "l1.structural.axis-points"),
        ("direction", "l1.structural.axis-direction"),
        ("member_dimension", "l1.structural.member-dimension"),
        ("section_dimension", "l1.structural.section-dimensions"),
    ),
)
def test_structural_l1_thresholds_fail_immediately_beyond_limits(
    defect: str,
    failed_check: str,
) -> None:
    expected, measured = _measurement_at_thresholds()
    if defect == "axis_point":
        measured["axis_start_mm"] = (5.0001, 0.0, 0.0)
    elif defect == "direction":
        angle = math.radians(0.1001)
        measured["axis_direction"] = (math.cos(angle), math.sin(angle), 0.0)
        measured["orientation"] = measured["axis_direction"]
    elif defect == "member_dimension":
        measured["axis_extent_mm"] = 1001.0001
    else:
        measured["section"]["width_mm"] = 101.0001

    report = compare_structural_l1_measurement(
        family="beam", expected=expected, measured=measured
    )

    assert report["l1_checks"][failed_check]["status"] == "failed"


def test_reopened_beam_column_support_contact_is_one_strict_transaction(
    tmp_path: Path,
) -> None:
    request = "add one beam supported by one column in one transaction"
    changeset = _structural_changeset(request=request, support_contact=True)
    output = tmp_path / "beam-column.ifc"
    registry = create_default_registry()

    audit = audit_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=changeset,
        registry=registry,
    )
    result = apply_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=registry,
    )

    assert audit["valid"] is True
    assert result["valid"] is True and result["published"] is True
    assert len(result["operations"]) == 2
    before = ifcopenshell.open(str(D7N))
    after = ifcopenshell.open(str(output))
    for operation, applied in zip(
        changeset["operations"], result["operations"], strict=True
    ):
        report = registry.dispatch(
            "comparison_adapter",
            operation,
            before_model=before,
            after_model=after,
            application=applied["changes"],
            role_mapping=_role_mapping(applied["changes"]),
        )
        assert report["valid"] is True
        assert all(
            check["status"] == "passed"
            for check in report["l1_checks"].values()
        )

    l1 = evaluate_independent_l1(
        damaged_ifc_path=D7N,
        repaired_ifc_path=output,
        changeset=changeset,
        application_result=result,
        registry=registry,
    )
    structural_checks = [
        check for check in l1.checks if check.check_id.startswith("l1.structural")
    ]
    assert structural_checks
    assert all(check.status is EvaluationStatus.PASSED for check in structural_checks)
    assert l1.status is EvaluationStatus.PASSED


def test_same_axis_duplicate_fails_audit_and_publishes_nothing(
    tmp_path: Path,
) -> None:
    request = "add two overlapping beams"
    changeset = _structural_changeset(request=request, duplicate_beam=True)
    output = tmp_path / "must-not-exist.ifc"
    source_before = _sha256(D7N)

    result = apply_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["published"] is False
    assert any(
        issue["code"] == "STRUCTURAL_SAME_AXIS_OVERLAP"
        for issue in result["issues"]
    )
    assert not output.exists()
    assert _sha256(D7N) == source_before


def test_one_structural_postcondition_failure_suppresses_whole_transaction(
    tmp_path: Path,
) -> None:
    request = "add one beam and one column but inject a Column failure"
    changeset = _structural_changeset(request=request)
    output = tmp_path / "must-not-exist.ifc"
    source_before = _sha256(D7N)
    registry = OperationRegistry()
    registry.register(beam_operation_definition())
    registry.register(
        replace(
            column_operation_definition(),
            postcondition_checker=lambda **kwargs: {
                "valid": False,
                "checks": [],
                "issues": [
                    {
                        "code": "INJECTED_COLUMN_POSTCONDITION_FAILURE",
                        "path": "/postconditions",
                        "message": "injected",
                    }
                ],
            },
        )
    )

    result = apply_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=registry,
    )

    assert result["valid"] is False and result["published"] is False
    assert [issue["code"] for issue in result["issues"]] == [
        "INJECTED_COLUMN_POSTCONDITION_FAILURE"
    ]
    assert not output.exists()
    assert _sha256(D7N) == source_before


def _structural_property_fact(
    *,
    repaired: bool,
    value_type: str = "IfcBoolean",
    occurrence_scope: str = "beam_occurrence",
) -> SemanticFact:
    return SemanticFact(
        fact_key="pset:Pset_BeamCommon.LoadBearing",
        value=True,
        value_type=value_type,
        unit=None,
        inherited=False,
        pset_path="Pset_BeamCommon.LoadBearing",
        entity_source="IfcBeam:phase12",
        source_kind=(
            EvidenceSourceKind.REPAIRED_OUTPUT
            if repaired
            else EvidenceSourceKind.EXPLICIT_REQUEST
        ),
        source_ref="request:/operations/0/properties/0",
        provenance=("phase12-structural-l2",),
        occurrence_scope=occurrence_scope,
        canonical_source_kind=(
            "repaired_output" if repaired else "explicit_request"
        ),
    )


@pytest.mark.parametrize(
    "repaired",
    (
        _structural_property_fact(repaired=True, value_type="IfcLabel"),
        _structural_property_fact(
            repaired=True, occurrence_scope="column_occurrence"
        ),
    ),
)
def test_requested_structural_l2_type_and_scope_mismatch_are_blocking(
    repaired: SemanticFact,
) -> None:
    policy = extend_policy_with_explicit_facts(
        BEAM_EVALUATION_POLICY,
        ("pset:Pset_BeamCommon.LoadBearing",),
        applicability=SemanticApplicability.REQUIRED,
    )
    checks = evaluate_operation_semantics(
        policy,
        expected_facts=(_structural_property_fact(repaired=False),),
        repaired_facts=(repaired,),
    )
    requested = next(
        check
        for check in checks
        if check.check_id == "explicit.pset-Pset_BeamCommon.LoadBearing"
    )
    assert requested.mandatory is True
    assert requested.status is not EvaluationStatus.PASSED


def test_real_window_door_beam_column_changeset_publishes_once(
    tmp_path: Path,
) -> None:
    damaged = FOUR_FAMILY_CASE / "02-damaged.ifc"
    request = (
        (FOUR_FAMILY_CASE / "input" / "request.txt").read_text(encoding="utf-8")
        + "\nAdd one Beam and one Column on the exact authorized Storey."
    )
    changeset = json.loads(
        (FOUR_FAMILY_CASE / "changeset" / "bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    model_hash = _sha256(damaged)
    request_digest = _request_hash(request)
    changeset["changeset_id"] = "changeset-phase12-four-family-atomicity"
    changeset["base_model_fingerprint"] = model_hash
    changeset["source_request_hash"] = request_digest
    changeset["scope"]["target_ids"].append(VVO_STOREY_ID)
    changeset["operations"].extend(
        (
            _structural_operation(
                family="beam",
                operation_id="four-family-beam-1",
                storey_id=VVO_STOREY_ID,
                request_hash=request_digest,
                model_hash=model_hash,
                parameters=_beam_parameters(),
            ),
            _structural_operation(
                family="column",
                operation_id="four-family-column-1",
                storey_id=VVO_STOREY_ID,
                request_hash=request_digest,
                model_hash=model_hash,
                parameters=_column_parameters(),
            ),
        )
    )
    changeset["evidence_refs"].extend(
        (
            "request:/operations/four-family-beam-1",
            "request:/operations/four-family-column-1",
        )
    )
    output = tmp_path / "four-family.ifc"
    source_before = _sha256(damaged)

    result = apply_changeset(
        damaged_ifc_path=damaged,
        repair_request=request,
        changeset=changeset,
        output_path=output,
        registry=create_default_registry(),
    )

    assert result["valid"] is True and result["published"] is True
    assert len(result["operations"]) == 6
    assert {
        operation["operation_type"] for operation in result["operations"]
    } == {
        "add_window_with_opening_to_wall",
        "fill_existing_opening_with_door",
        "add_beam",
        "add_column",
    }
    assert ifcopenshell.open(str(output)).schema == "IFC2X3"
    assert _sha256(damaged) == source_before
