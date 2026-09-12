import inspect
import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Mapping

import pytest

from scripts.ifc_repair import validate_success_cases
from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
from text2ifc_ifc_repair.evaluation_policy import (
    STRUCTURAL_L1_CHECK_IDS,
    STRUCTURAL_L1_THRESHOLDS,
    compare_structural_l1_measurement,
    structural_l1_authorization,
)
from text2ifc_ifc_repair.operations.structural_member import (
    resolve_structural_member_frame,
)
from text2ifc_ifc_repair.operations.hosted_opening import deterministic_global_id


def _beam_measurement_at_limits() -> tuple[dict[str, Any], dict[str, Any]]:
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


def test_structural_l1_thresholds_are_inclusive_at_frozen_limits() -> None:
    expected, measured = _beam_measurement_at_limits()

    report = compare_structural_l1_measurement(
        family="beam", expected=expected, measured=measured
    )

    assert all(
        check["status"] == "passed" for check in report["l1_checks"].values()
    )
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
def test_structural_l1_thresholds_fail_immediately_beyond_their_named_check(
    defect: str,
    failed_check: str,
) -> None:
    expected, measured = _beam_measurement_at_limits()
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


def test_volume_and_mesh_evidence_are_diagnostic_not_l1_gates() -> None:
    expected, measured = _beam_measurement_at_limits()
    measured.update(
        {
            "axis_start_mm": (5.0001, 0.0, 0.0),
            "volume_mm3": 20_000_000.0,
            "mesh_bounds_mm": {"min": (0, 0, 0), "max": (1000, 100, 200)},
        }
    )

    report = compare_structural_l1_measurement(
        family="beam", expected=expected, measured=measured
    )

    assert report["l1_checks"]["l1.structural.axis-points"]["status"] == "failed"
    assert not any(
        "volume" in check_id or "mesh" in check_id
        for check_id in report["l1_checks"]
    )


@pytest.mark.parametrize("family", ("beam", "column"))
def test_structural_type_relationship_allows_exact_type_reuse_or_new_binding(
    family: str,
) -> None:
    authorization = structural_l1_authorization(family)

    assert authorization["created"]["structural_type_relationship"] == (
        "IfcRelDefinesByType"
    )
    assert authorization["modified"]["structural_type_relationship"] == (
        "IfcRelDefinesByType"
    )
    assert authorization["required_roles"]["created"] == (family,)


def test_column_profile_orientation_passes_at_point_one_degree_and_fails_beyond() -> None:
    expected = resolve_structural_member_frame(
        occurrence_class="IfcColumn",
        axis_start_mm=(0, 0, 0),
        axis_end_mm=(0, 0, 3000),
        section={
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 1, "y": 0},
        },
    )

    def measured(angle_degrees: float) -> dict[str, Any]:
        angle = math.radians(angle_degrees)
        return {
            "axis_start_mm": (0.0, 0.0, 0.0),
            "axis_end_mm": (0.0, 0.0, 3000.0),
            "axis_direction": (0.0, 0.0, 1.0),
            "axis_extent_mm": 3000.0,
            "section": {
                "shape": "rectangle",
                "width_mm": 400.0,
                "depth_mm": 600.0,
            },
            "orientation": (math.cos(angle), math.sin(angle), 0.0),
            "representation_type": "SweptSolid",
        }

    at_limit = compare_structural_l1_measurement(
        family="column", expected=expected, measured=measured(0.1)
    )
    beyond = compare_structural_l1_measurement(
        family="column", expected=expected, measured=measured(0.1001)
    )

    assert (
        at_limit["l1_checks"]["l1.structural.profile-orientation"]["status"]
        == "passed"
    )
    assert (
        beyond["l1_checks"]["l1.structural.profile-orientation"]["status"]
        == "failed"
    )


@dataclass(frozen=True)
class _Product:
    GlobalId: str
    ifc_class: str = "IfcBeam"
    fingerprint: str = ""

    def is_a(self, ifc_class: str | None = None) -> str | bool:
        return self.ifc_class if ifc_class is None else ifc_class == self.ifc_class


class _Model:
    def __init__(self, beams: tuple[_Product, ...]) -> None:
        self._beams = beams
        self.by_guid_calls: list[str] = []

    def by_type(self, ifc_class: str) -> tuple[_Product, ...]:
        assert ifc_class == "IfcBeam"
        return self._beams

    def by_guid(self, global_id: str) -> _Product:
        self.by_guid_calls.append(global_id)
        try:
            return next(item for item in self._beams if item.GlobalId == global_id)
        except StopIteration as error:
            raise RuntimeError(global_id) from error


class _Registry:
    def __init__(self) -> None:
        self.l1_occurrence_ids: list[str] = []

    def dispatch(
        self,
        capability: str,
        operation: Mapping[str, Any],
        **kwargs: Any,
    ) -> dict[str, bool]:
        del operation
        assert capability == "comparison_adapter"
        assert kwargs["application"] == {}
        self.l1_occurrence_ids.append(kwargs["role_mapping"]["beam"])
        return {
            "valid": True,
            "l1_checks": {
                check_id: {"status": "passed"}
                for check_id in STRUCTURAL_L1_CHECK_IDS
            },
        }

    def require(self, operation_type: str) -> SimpleNamespace:
        assert operation_type == "add_beam"
        return SimpleNamespace(
            operation_type=operation_type,
            evaluation_policy=SimpleNamespace(semantic_role="beam"),
            semantic_scope_roles={"beam": "beam_occurrence"},
        )

    def require_evaluation_policy(self, operation_type: str) -> object:
        assert operation_type == "add_beam"
        return object()

    def build_semantic_policy_facts(
        self, operation_type: str, *, operation: Mapping[str, Any]
    ) -> tuple[()]:
        assert operation_type == "add_beam"
        del operation
        return ()

    def evaluate_semantics(
        self,
        operation_type: str,
        *,
        expected_facts: tuple[()],
        repaired_facts: tuple[()],
    ) -> tuple[SimpleNamespace, ...]:
        assert operation_type == "add_beam"
        assert expected_facts
        assert repaired_facts == ()
        return (SimpleNamespace(mandatory=True, status=EvaluationStatus.PASSED),)


def test_independent_structural_audit_derives_new_member_without_application_role_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A saved role claim cannot select an existing member for strict L1/L2."""

    registry = _Registry()
    monkeypatch.setattr(validate_success_cases, "create_default_registry", lambda: registry)
    monkeypatch.setattr(
        validate_success_cases,
        "extract_ifc_semantic_facts",
        lambda *args, **kwargs: (),
    )
    operation = {
        "operation_id": "beam-1",
        "operation_type": "add_beam",
        "target": {"storey_global_id": "storey-1"},
        "parameters": {
            "axis": {
                "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
                "end": {"x_mm": 1000, "y_mm": 0, "z_mm": 3000},
            },
            "section": {
                "shape": "rectangle",
                "width_mm": 100,
                "height_mm": 200,
            },
        },
        "semantic_assignments": [
            {
                "fact_key": "relationship:type",
                "value": "beam-type-1",
                "value_type": "IfcBeamType",
                "ownership": "type_inherited",
                "scope": "beam_occurrence",
                "source_kind": "surviving_type",
            }
        ],
    }
    occurrence_id = deterministic_global_id(operation, "beam")
    damaged_model = _Model((_Product("beam-existing"),))
    repaired_model = _Model(
        (_Product("beam-existing"), _Product(occurrence_id))
    )
    changeset = {"operations": [operation]}
    application = {
        "operations": [
            {
                "operation_id": "beam-1",
                "changes": {
                    "created": [{"role": "beam", "global_id": "beam-existing"}],
                    "modified": [],
                },
            }
        ]
    }

    result = validate_success_cases.audit_repaired_operations(
        changeset=changeset,
        application=application,
        damaged_model=damaged_model,
        repaired_model=repaired_model,
    )

    assert result == {"l1_operation_count": 1, "l2_operation_count": 1}
    assert registry.l1_occurrence_ids == [occurrence_id]
    assert occurrence_id in repaired_model.by_guid_calls
    assert "beam-existing" not in repaired_model.by_guid_calls


def test_independent_structural_authority_rejects_reused_type_fingerprint_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operation = {
        "operation_id": "beam-reuse-1",
        "operation_type": "add_beam",
        "target": {"storey_global_id": "storey-1"},
        "parameters": {
            "axis": {
                "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
                "end": {"x_mm": 1000, "y_mm": 0, "z_mm": 3000},
            },
            "section": {
                "shape": "rectangle",
                "width_mm": 100,
                "height_mm": 200,
            },
        },
        "semantic_assignments": [
            {
                "fact_key": "relationship:type",
                "value": "reused-beam-type",
                "value_type": "IfcBeamType",
                "ownership": "type_inherited",
                "scope": "beam_occurrence",
                "source_kind": "surviving_type",
            }
        ],
    }
    occurrence_id = deterministic_global_id(operation, "beam")
    before_type = _Product(
        "reused-beam-type", ifc_class="IfcBeamType", fingerprint="before"
    )
    after_type = _Product(
        "reused-beam-type", ifc_class="IfcBeamType", fingerprint="after"
    )
    damaged_model = _Model((before_type,))
    repaired_model = _Model((_Product(occurrence_id), after_type))
    monkeypatch.setattr(
        validate_success_cases,
        "type_authority_fingerprint",
        lambda entity: entity.fingerprint,
    )

    with pytest.raises(ValueError, match="reused_type_fingerprint"):
        validate_success_cases._audit_structural_type_and_semantic_authority(
            changeset={"operations": [operation]},
            damaged_model=damaged_model,
            repaired_model=repaired_model,
        )


def test_preservation_authority_cannot_be_supplied_by_application_claims(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert "application" not in inspect.signature(
        validate_success_cases._audit_structural_preservation
    ).parameters
    damaged_model = _Model(())
    repaired_model = _Model((_Product("beam-created"),))
    monkeypatch.setattr(
        validate_success_cases,
        "profile_normalized_model_diff",
        lambda before, after, **_kwargs: {
            "changes": {
                "created": [
                    {"global_id": "beam-created"},
                    {"global_id": "forged-unrelated-root"},
                ],
                "modified": [],
                "removed": [],
            }
        },
    )
    monkeypatch.setattr(
        validate_success_cases,
        "_independent_created_product_contract",
        lambda operations: {
            "beam-created": (
                "IfcBeam",
                {"operation_id": "beam-1", "operation_type": "add_beam"},
                "beam",
            )
        },
    )
    monkeypatch.setattr(
        validate_success_cases,
        "_collect_created_product_root_authority",
        lambda **kwargs: None,
    )

    with pytest.raises(ValueError, match="undeclared_root:forged-unrelated-root"):
        validate_success_cases._audit_structural_preservation(
            changeset={"operations": []},
            damaged_model=damaged_model,
            repaired_model=repaired_model,
        )
