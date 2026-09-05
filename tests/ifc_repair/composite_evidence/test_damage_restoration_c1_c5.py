"""Frozen C1-C5 damage-restoration case set: offline full-chain verification.

Non-vvo models (sixty5/str, 1px, d7n).  Per case: deterministic damage
removes exactly the members the request asks to restore (beams via
``remove_structural_members``; doors via ``remove_doors_batch`` with the
opening preserved; windows via ``remove_windows_and_openings_batch``), the
production ``RepairAPI`` public chain restores them with a deterministic
replay provider, and the repaired model is compared with the original
(class counts restored; each restored member aligned with the removed
member's measured geometry; comparator passed).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import ifcopenshell
import ifcopenshell.util.placement
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from dataclasses import replace  # noqa: E402

from text2ifc_agent.providers import ProviderOutput  # noqa: E402
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    evaluate_production,
)
from text2ifc_ifc_repair.evaluation import (  # noqa: E402
    EvaluationExecutionPolicy,
)
from text2ifc_ifc_repair.geometry import (  # noqa: E402
    measure_straight_rectangular_member,
)
from text2ifc_ifc_repair.orchestrator import RepairOrchestrator  # noqa: E402
from text2ifc_ifc_repair.type_templates import (  # noqa: E402
    type_authority_fingerprint,
)


def _large_model_evaluation_stage(inputs):
    """evaluate_production with a deadline that fits the 117k-entity models.

    The default accelerated policy fails closed at 180 s; the sixty5 model
    needs more wall time for its unchanged-validation and full diff.  The
    deadline is raised (not the gate itself): every check still runs.
    """

    return evaluate_production(
        replace(
            inputs,
            execution_policy=EvaluationExecutionPolicy(
                deadline_seconds=900.0
            ),
        )
    )


def _orchestrator_factory(**kwargs):
    kwargs["evaluation_stage"] = _large_model_evaluation_stage
    return RepairOrchestrator(**kwargs)
from text2ifc_ifc_repair.mutation import (  # noqa: E402
    remove_doors_batch,
    remove_structural_members,
    remove_windows_and_openings_batch,
)
from scripts.ifc_repair.composite_evidence.run_damage_restoration_c1_c5 import (  # noqa: E402
    _type_reuse_preflight as _runner_type_reuse_preflight,
)
from scripts.ifc_repair.composite_evidence import (  # noqa: E402
    run_damage_restoration_c1_c5 as live_runner,
)
from scripts.ifc_repair.composite_evidence.restoration_debug import (  # noqa: E402
    compare_damage_restoration,
)
from scripts.ifc_repair.composite_evidence import (  # noqa: E402
    curate_damage_restoration_c1_c5 as proof_curator,
)
from scripts.ifc_repair.composite_evidence.curate_damage_restoration_c1_c5 import (  # noqa: E402
    validate_recorded_debug,
)

FREEZE = json.loads(
    (
        ROOT
        / "docs/validation/repair-composite-milestone"
        / "damage-restoration-c1-c5-freeze.json"
    ).read_text(encoding="utf-8")
)


def test_live_public_input_declares_strict_geometry_target_tolerance() -> None:
    request = live_runner._public_repair_request(FREEZE["cases"][1])

    assert FREEZE["cases"][1]["request"] in request
    assert (
        "Use a target-matching tolerance of 0.1 mm for every stated "
        "millimetre geometry selector"
    ) in request
    assert "0.1 mm" in request


def test_live_public_input_confirms_explicit_notdefined_door_request() -> None:
    case = next(case for case in FREEZE["cases"] if case["case_id"] == "C3")
    assert "operation type NOTDEFINED" in case["request"]

    request = live_runner._public_repair_request(case)

    assert (
        "For every Door explicitly requested with operation type NOTDEFINED, "
        "I explicitly accept NOTDEFINED"
    ) in request


SOURCE = {
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "restore the damaged members",
}


def _section_json(prompt: str, heading: str) -> dict:
    part = prompt.split(f"## {heading}", 1)[1].split("\n## ", 1)[0].strip()
    document, _ = json.JSONDecoder().raw_decode(part)
    return document


def _prototype_intent(member: dict) -> dict | None:
    proto = member.get("prototype_intent")
    if (
        not isinstance(proto, dict)
        or proto.get("reference_kind") != "global_id"
        or not str(proto.get("reference", ""))
    ):
        raise ValueError("DAMAGE_RESTORATION_TYPE_REUSE_REQUIRED")
    return {**proto, "source": SOURCE}


def _property_intents(member: dict) -> list[dict]:
    return [
        {**claim, "source": SOURCE}
        for claim in member.get("property_intents", [])
    ]


def _beam_op(operation_id: str, member: dict) -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_beam",
        "routing_intent": {
            "component_family": "beam",
            "action": "add",
            "operation_profile": "beam.add.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": [member["storey"]],
        },
        "parameters": {
            "axis": {
                "start": {
                    "x_mm": member["axis"]["start"]["x_mm"],
                    "y_mm": member["axis"]["start"]["y_mm"],
                    "z_mm": member["axis"]["start"]["z_mm"],
                },
                "end": {
                    "x_mm": member["axis"]["end"]["x_mm"],
                    "y_mm": member["axis"]["end"]["y_mm"],
                    "z_mm": member["axis"]["end"]["z_mm"],
                },
            },
            "section": {
                "shape": "rectangle",
                "width_mm": member["section"]["width_mm"],
                "height_mm": member["section"]["height_mm"],
            },
        },
        "attribute_intents": [],
        "property_intents": _property_intents(member),
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": _prototype_intent(member),
        "provenance": [SOURCE],
    }


def _column_op(operation_id: str, member: dict) -> dict:
    section = {
        "shape": "rectangle",
        "width_mm": member["section"]["width_mm"],
        "depth_mm": member["section"]["depth_mm"],
    }
    if member["section"].get("orientation") is not None:
        section["orientation"] = member["section"]["orientation"]
    return {
        "operation_id": operation_id,
        "operation_type": "add_column",
        "routing_intent": {
            "component_family": "column",
            "action": "add",
            "operation_profile": "column.add.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "names": [member["storey"]],
        },
        "parameters": {"axis": member["axis"], "section": section},
        "attribute_intents": [],
        "property_intents": _property_intents(member),
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": _prototype_intent(member),
        "provenance": [SOURCE],
    }


def _door_op(operation_id: str, door: dict) -> dict:
    opening = door["opening"]
    door_params = {"operation_type": door["door_type"]}
    if door["door_type"] == "SINGLE_SWING_LEFT":
        door_params["formal_enum_explicit"] = True
    else:
        door_params["notdefined_accepted"] = True
    return {
        "operation_id": operation_id,
        "operation_type": "fill_existing_opening_with_door",
        "routing_intent": {
            "component_family": "door",
            "action": "fill_existing_opening",
            "operation_profile": "door.fill-existing-opening.v0.3",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcOpeningElement"],
            "geometry_capabilities": ["measured_hosted_opening"],
            "geometry_constraints": [
                {
                    "field": "opening_width_mm",
                    "value": opening["width_mm"],
                    "tolerance_mm": 1.0,
                },
                {
                    "field": "opening_height_mm",
                    "value": opening["height_mm"],
                    "tolerance_mm": 1.0,
                },
                {
                    "field": "opening_depth_mm",
                    "value": opening["depth_mm"],
                    "tolerance_mm": 1.0,
                },
                {
                    "field": "opening_center_offset_mm",
                    "value": opening["center_offset_mm"],
                    "tolerance_mm": 1.0,
                },
                {
                    "field": "opening_sill_height_mm",
                    "value": opening["sill_height_mm"],
                    "tolerance_mm": 1.0,
                },
            ],
            "max_candidates": 5,
            "winner_margin": 10,
        },
        "parameters": {
            "door": door_params,
            "fit_existing_opening": True,
        },
        "attribute_intents": [],
        "property_intents": _property_intents(door),
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": _prototype_intent(door),
        "provenance": [SOURCE],
    }


def _window_op(operation_id: str, window: dict) -> dict:
    opening = window["opening"]
    wall = window["wall_query"]
    constraints = [
        {
            "field": "wall_length_mm",
            "value": wall["length_mm"],
            "tolerance_mm": 1.0,
        },
        {
            "field": "wall_height_mm",
            "value": wall["height_mm"],
            "tolerance_mm": 1.0,
        },
        {
            "field": "wall_thickness_mm",
            "value": wall["thickness_mm"],
            "tolerance_mm": 1.0,
        },
    ]
    if "storey_elevation_mm" in wall:
        constraints.append(
            {
                "field": "storey_elevation_mm",
                "value": wall["storey_elevation_mm"],
                "tolerance_mm": 1.0,
            }
        )
    return {
        "operation_id": operation_id,
        "operation_type": "add_window_with_opening_to_wall",
        "routing_intent": {
            "component_family": "window",
            "action": "add_with_opening",
            "operation_profile": "window.add-with-opening.v0.2",
            "source": SOURCE,
        },
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcWall"],
            "direction": wall["direction"],
            "geometry_capabilities": ["straight_wall"],
            "geometry_constraints": constraints,
            "max_candidates": 5,
            "winner_margin": 10,
        },
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
            "window": {"fit_opening": True},
        },
        "attribute_intents": [],
        "property_intents": _property_intents(window),
        "semantic_bundle_refs": [],
        "quantity_intents": [],
        "occurrence_reuse_intent": None,
        "prototype_intent": _prototype_intent(window),
        "provenance": [SOURCE],
    }


def _intent_body(case: dict) -> dict:
    ops: list[dict] = []
    for index, member in enumerate(case["damage"].get("beams", []), 1):
        ops.append(_beam_op(f"restore-beam-{index}", member))
    for index, member in enumerate(case["damage"].get("columns", []), 1):
        ops.append(_column_op(f"restore-column-{index}", member))
    for index, door in enumerate(case["damage"].get("doors", []), 1):
        ops.append(_door_op(f"restore-door-{index}", door))
    for index, window in enumerate(case["damage"].get("windows", []), 1):
        ops.append(_window_op(f"restore-window-{index}", window))
    return {
        "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
        "operations": ops,
        "semantic_bundles": [],
        "provenance": [SOURCE],
        "unsupported_requests": [],
    }


class _ReplayProvider:
    """Deterministic two-stage provider replaying the frozen intents."""

    def __init__(self, case: dict) -> None:
        self._case = case
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        stage = kwargs["state"]["stage"]
        if stage == "ifc_repair_intent":
            return ProviderOutput(
                text=json.dumps(_intent_body(self._case), ensure_ascii=False),
                metadata={"provider": "fixture", "model": "fixture-model"},
            )
        prompt = kwargs["prompt"]
        schema = kwargs["schema"]
        projection = _section_json(prompt, "Resolved operation projection")
        raw_operations = projection["operations"]
        operations = []
        scope_values: list[str] = []
        evidence_values: list[str] = []
        if isinstance(raw_operations, list):
            for op in raw_operations:
                operations.append(
                    {
                        "operation_id": op["operation_id"],
                        "operation_type": op["operation_type"],
                        "target": op["target"],
                        "parameters": op["parameters"],
                        "evidence_refs": list(op["evidence_refs"]),
                    }
                )
                scope_values.extend(
                    str(value)
                    for value in op.get("scope_ids", ())
                    or [op["target"].get(k) for k in op["target"]]
                )
                evidence_values.extend(str(v) for v in op["evidence_refs"])
        else:
            from text2ifc_ifc_repair.operations import (
                create_default_registry,
            )

            registry = create_default_registry()
            for operation_id, op in raw_operations.items():
                operations.append(
                    {
                        "operation_id": operation_id,
                        "operation_type": op["operation_type"],
                        "target": registry.bind_resolved_target(
                            str(op["operation_type"]),
                            str(op["target_global_id"]),
                        ),
                        "parameters": op["parameters"],
                        "evidence_refs": [
                            str(v) for v in op["evidence_pointers"]
                        ],
                    }
                )
                scope_values.extend(
                    str(value) for value in op.get("scope_ids", ())
                )
                evidence_values.extend(
                    str(v) for v in op["evidence_pointers"]
                )
        scope = sorted(set(scope_values))
        evidence = sorted(set(evidence_values))
        binding_lines = prompt.split("## Immutable bindings", 1)[1].split(
            "## Resolved operation projection", 1
        )[0]
        bindings = dict(
            re.findall(r"^- ([^:]+): (.+)$", binding_lines, flags=re.MULTILINE)
        )
        return ProviderOutput(
            text=json.dumps(
                {
                    "schema_version": str(schema["$id"]),
                    "draft_id": "draft-damage-restoration-c1-c5",
                    "base_model_fingerprint": bindings["model"],
                    "source_request_hash": bindings["source request"],
                    "semantic_manifest_ref": bindings["semantic manifest ref"],
                    "semantic_manifest_sha256": bindings[
                        "semantic manifest hash"
                    ],
                    "semantic_summary": _section_json(
                        prompt, "Semantic group counts"
                    ),
                    "scope": {"target_ids": scope, "forbidden_ids": []},
                    "evidence_refs": evidence,
                    "preconditions": [],
                    "postconditions": [],
                    "operations": operations,
                },
                ensure_ascii=False,
            ),
            metadata={"provider": "fixture", "model": "fixture-model"},
        )


def _apply_damage(case: dict, scratch: Path) -> Path:
    source = ROOT / str(case["source"])
    beams = [m["gid"] for m in case["damage"].get("beams", [])]
    columns = [m["gid"] for m in case["damage"].get("columns", [])]
    doors = case["damage"].get("doors", [])
    windows = case["damage"].get("windows", [])
    if beams or columns:
        remove_structural_members(
            source_path=source,
            output_dir=scratch / "structural",
            beam_global_ids=tuple(beams),
            column_global_ids=tuple(columns),
        )
    current = (
        scratch / "structural" / "damaged.ifc"
        if beams or columns
        else source
    )
    if doors:
        remove_doors_batch(
            source_path=current,
            output_dir=scratch / "doors",
            door_global_ids=[d["gid"] for d in doors],
            preserve_openings=True,
        )
        current = scratch / "doors" / "damaged.ifc"
    if windows:
        remove_windows_and_openings_batch(
            source_path=current,
            output_dir=scratch / "windows",
            targets=[
                {
                    "wall_global_id": w["wall_query"]["wall_global_id"],
                    "window_global_id": w["gid"],
                    "opening_global_id": w["opening_gid"],
                }
                for w in windows
            ],
        )
        current = scratch / "windows" / "damaged.ifc"
    return current


def _containing_storey(model, entity):
    matches = [
        relation.RelatingStructure
        for relation in model.by_type("IfcRelContainedInSpatialStructure")
        if entity in relation.RelatedElements
        and relation.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    assert len(matches) == 1, str(entity.GlobalId)
    return matches[0]


def _single_type_global_id(entity) -> str:
    matches = [
        relation.RelatingType
        for relation in entity.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    ]
    assert len(matches) == 1, str(entity.GlobalId)
    return str(matches[0].GlobalId)


def _beam_physical_section(member, storey) -> dict[str, float | str]:
    """Resolve transverse width and vertical height from the IFC solid frame."""

    body = next(
        representation
        for representation in member.Representation.Representations
        if representation.RepresentationIdentifier == "Body"
    )
    assert len(body.Items) == 1
    solid = body.Items[0]
    assert solid.is_a("IfcExtrudedAreaSolid")
    profile = solid.SweptArea
    assert profile.is_a("IfcRectangleProfileDef")
    member_matrix = ifcopenshell.util.placement.get_local_placement(
        member.ObjectPlacement
    )
    storey_matrix = ifcopenshell.util.placement.get_local_placement(
        storey.ObjectPlacement
    )
    solid_matrix = ifcopenshell.util.placement.get_axis2placement(solid.Position)
    frame = np.linalg.inv(storey_matrix) @ member_matrix @ solid_matrix
    x_is_vertical = abs(float(frame[2, 0])) > abs(float(frame[2, 1]))
    width = float(profile.YDim if x_is_vertical else profile.XDim)
    height = float(profile.XDim if x_is_vertical else profile.YDim)
    scale = ifcopenshell.util.unit.calculate_unit_scale(member.file) * 1000.0
    return {
        "width_mm": round(width * scale, 6),
        "height_mm": round(height * scale, 6),
    }


@pytest.mark.parametrize(
    "case",
    [case for case in FREEZE["cases"] if case["case_id"] in {"C2", "C3", "C4", "C5"}],
    ids=lambda case: case["case_id"],
)
def test_frozen_beam_frames_match_the_source_ifc(case: dict) -> None:
    """Freeze exact IFC centre axes, not rounded tessellated bounds."""

    model = ifcopenshell.open(str(ROOT / str(case["source"])))
    for beam in case["damage"].get("beams", []):
        original = model.by_guid(beam["gid"])
        measured = measure_straight_rectangular_member(
            original,
            relative_to=(storey := _containing_storey(model, original)),
        )
        expected_start = tuple(
            float(beam["axis"]["start"][key])
            for key in ("x_mm", "y_mm", "z_mm")
        )
        expected_end = tuple(
            float(beam["axis"]["end"][key])
            for key in ("x_mm", "y_mm", "z_mm")
        )
        assert expected_start == pytest.approx(
            measured["axis_start_mm"], abs=1e-3
        ), beam["gid"]
        assert expected_end == pytest.approx(
            measured["axis_end_mm"], abs=1e-3
        ), beam["gid"]
        assert beam["section"] == _beam_physical_section(
            original, storey
        ), beam["gid"]


@pytest.mark.parametrize(
    "case",
    [case for case in FREEZE["cases"] if case["case_id"] in {"C2", "C3", "C4", "C5"}],
    ids=lambda case: case["case_id"],
)
def test_frozen_repairs_require_the_original_surviving_types(case: dict) -> None:
    """A restoration must reuse each removed occurrence's surviving Type."""

    model = ifcopenshell.open(str(ROOT / str(case["source"])))
    for key in ("beams", "columns", "doors", "windows"):
        for member in case["damage"].get(key, []):
            original = model.by_guid(member["gid"])
            assert member.get("prototype_intent") == {
                "reference_kind": "global_id",
                "reference": _single_type_global_id(original),
            }, (case["case_id"], key, member["gid"])
            assert _single_type_global_id(original) in case["request"], (
                case["case_id"],
                key,
                member["gid"],
            )
            if key == "doors":
                type_entity = next(
                    relation.RelatingType
                    for relation in original.IsDefinedBy
                    if relation.is_a("IfcRelDefinesByType")
                )
                assert member["door_type"] == str(type_entity.OperationType)


@pytest.mark.parametrize("case_id", ("C3", "C4"))
def test_c3_c4_include_real_column_damage_and_restoration(case_id: str) -> None:
    case = next(case for case in FREEZE["cases"] if case["case_id"] == case_id)
    assert case["damage"].get("columns"), case_id


def test_runner_stops_when_the_required_type_does_not_survive_damage(
    tmp_path: Path,
) -> None:
    case = next(case for case in FREEZE["cases"] if case["case_id"] == "C2")
    damaged = _apply_damage(case, tmp_path / "scratch")
    original_model = ifcopenshell.open(str(ROOT / str(case["source"])))
    damaged_model = ifcopenshell.open(str(damaged))
    assert _runner_type_reuse_preflight(
        case,
        original_model=original_model,
        damaged_model=damaged_model,
    )["status"] == "passed"
    door_type_id = case["damage"]["doors"][0]["prototype_intent"][
        "reference"
    ]
    damaged_model.remove(damaged_model.by_guid(door_type_id))

    with pytest.raises(
        ValueError, match="DAMAGE_RESTORATION_TYPE_REUSE_UNAVAILABLE"
    ):
        _runner_type_reuse_preflight(
            case,
            original_model=original_model,
            damaged_model=damaged_model,
        )


def test_proof_curation_accepts_recomputed_focused_ifccompare() -> None:
    payload = {
        "status": "passed",
        "members": [{"repaired_tag": "restore-beam-1"}],
    }

    validate_recorded_debug(payload, json.loads(json.dumps(payload)))


def test_proof_curation_ignores_only_ifccompare_runtime_timings() -> None:
    recorded = {
        "status": "passed",
        "whole_model_ifccompare": {
            "comparison_status": "passed",
            "comparison_metrics": {
                "timeout_seconds": 120.0,
                "root_index_seconds": 1.0,
                "total_seconds": 2.0,
            },
        },
    }
    recomputed = json.loads(json.dumps(recorded))
    recomputed["whole_model_ifccompare"]["comparison_metrics"].update(
        root_index_seconds=3.0,
        total_seconds=4.0,
    )

    validate_recorded_debug(recorded, recomputed)


def test_proof_curation_rejects_focused_ifccompare_drift() -> None:
    recorded = {"status": "passed", "members": []}
    recomputed = {
        "status": "passed",
        "members": [{"repaired_tag": "restore-beam-1"}],
    }

    with pytest.raises(ValueError, match="PROOF_IFCCOMPARE_DEBUG_MISMATCH"):
        validate_recorded_debug(recorded, recomputed)


def test_proof_curation_accepts_a_succeeded_case_from_a_completed_subset() -> None:
    execution = {
        "status": "completed",
        "cases": [
            {"case_id": "C1", "status": "succeeded"},
            {"case_id": "C2", "status": "succeeded"},
        ],
    }

    selected = proof_curator.validate_selected_case_execution(
        execution, case_id="C1"
    )

    assert selected["status"] == "succeeded"
    assert execution["status"] == "completed"


def test_proof_curation_rejects_a_failed_source_batch() -> None:
    execution = {
        "status": "failed",
        "cases": [
            {"case_id": "C1", "status": "succeeded"},
            {"case_id": "C2", "status": "clarification_required"},
        ],
    }

    with pytest.raises(ValueError, match="PROOF_SOURCE_EXECUTION_NOT_COMPLETED"):
        proof_curator.validate_selected_case_execution(execution, case_id="C1")


def test_proof_curation_reuses_recorded_operation_bindings() -> None:
    result = {
        "original_comparison": {
            "restoration_operation_bindings": {
                "beams": ["beam-provider-id"],
                "columns": [],
                "doors": ["door-provider-id"],
                "windows": [],
            }
        }
    }

    assert proof_curator.restoration_tags_for_result(result) == {
        "beams": ["beam-provider-id"],
        "columns": [],
        "doors": ["door-provider-id"],
        "windows": [],
    }


def test_proof_curation_loads_the_actual_public_request(tmp_path: Path) -> None:
    run_dir = tmp_path / "runtime-run"
    renderer_input = run_dir / "intent" / "renderer-input.json"
    renderer_input.parent.mkdir(parents=True)
    renderer_input.write_text(
        json.dumps({"REPAIR_REQUEST": "frozen request plus live suffix"}),
        encoding="utf-8",
    )

    assert (
        proof_curator.load_public_request(run_dir)
        == "frozen request plus live suffix"
    )


def test_proof_report_lists_removed_and_rebuilt_guids() -> None:
    report = proof_curator._case_report(
        {"case_id": "C-test", "source": "source.ifc"},
        {
            "status": "succeeded",
            "latency_seconds": 1.0,
            "original_comparison": {
                "comparison_status": "passed",
                "class_counts_restored": True,
                "identity_equivalent": False,
            },
            "damage": {
                "beams_removed": 1,
                "columns_removed": 0,
                "doors_removed": 0,
                "windows_removed": 0,
            },
        },
        {
            "status": "passed",
            "member_count": 1,
            "failed_member_count": 0,
            "members": [
                {
                    "repaired_tag": "beam-1",
                    "geometry": {"status": "passed"},
                    "properties": {"status": "passed"},
                    "type_reuse": {"status": "passed"},
                }
            ],
        },
        {"summary": {"changed_product_count": 2, "changed_product_classes": {}}},
        guid_trace=[
            {
                "role": "beam-1",
                "damage_action": "removed",
                "original_ifc_class": "IfcBeam",
                "original_global_id": "old-guid",
                "repair_action": "rebuilt",
                "repaired_ifc_class": "IfcBeam",
                "repaired_global_id": "new-guid",
            }
        ],
        source_batch_id="batch-01",
    )

    assert "old-guid" in report
    assert "new-guid" in report
    assert "removed" in report
    assert "rebuilt" in report


def test_proof_copy_normalizes_text_artifacts_to_lf(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    target = tmp_path / "proof" / "target.json"
    source.write_bytes(b'{"status":"passed"}\r\n')

    proof_curator._copy(source, target)

    assert target.read_bytes() == b'{"status":"passed"}\n'


def test_live_runner_uses_an_explicit_shared_property_cache(
    tmp_path: Path,
) -> None:
    prepare = getattr(
        live_runner,
        "_prepare_property_runtime_environment",
        None,
    )
    assert callable(prepare)
    cache_root = tmp_path / "shared-cache"
    (cache_root / "models" / "BAAI-bge-m3").mkdir(parents=True)

    environment = prepare({}, cache_root=cache_root)

    assert environment["TEXT2IFC_PROPERTY_BGE_MODEL_PATH"] == str(
        (cache_root / "models" / "BAAI-bge-m3").resolve()
    )
    assert environment["TEXT2IFC_PROPERTY_QDRANT_PATH"] == str(
        (cache_root / "property-resolution" / "qdrant").resolve()
    )


def test_live_runner_blocks_an_unhealthy_property_runtime_before_provider() -> None:
    require_ready = getattr(
        live_runner,
        "_require_ready_property_runtime",
        None,
    )
    assert callable(require_ready)
    unavailable = SimpleNamespace(
        health=SimpleNamespace(
            status="not_ready",
            reason_code="BGE_M3_UNAVAILABLE",
            acceptance_eligible=False,
        )
    )

    with pytest.raises(RuntimeError, match="BGE_M3_UNAVAILABLE"):
        require_ready(unavailable)

    ready = SimpleNamespace(
        health=SimpleNamespace(
            status="ready",
            reason_code=None,
            acceptance_eligible=True,
        )
    )
    require_ready(ready)


def test_failed_live_case_still_counts_its_provider_attempts() -> None:
    update_count = getattr(live_runner, "_updated_transport_call_count", None)
    assert callable(update_count)
    assert update_count(0, [{"stage": "stage1"}]) == 1


@pytest.mark.parametrize("case", FREEZE["cases"], ids=lambda c: c["case_id"])
def test_live_runner_resolves_actual_operation_ids_from_bound_content(
    case: dict,
) -> None:
    resolve = getattr(live_runner, "_resolve_restoration_tags", None)
    assert callable(resolve)
    run_root = (
        ROOT
        / "dataset/processed/ifc-repair-runs/c1c5-offline-20260903-v2"
        / "cases"
        / case["case_id"]
        / "runtime"
    )
    changeset_path = next(run_root.rglob("bound-changeset.json"))
    changeset = json.loads(changeset_path.read_text(encoding="utf-8"))
    operation_type_by_key = {
        "beams": "add_beam",
        "columns": "add_column",
        "doors": "fill_existing_opening_with_door",
        "windows": "add_window_with_opening_to_wall",
    }
    expected = {key: [] for key in operation_type_by_key}
    for index, operation in enumerate(changeset["operations"], start=1):
        operation["operation_id"] = f"provider-operation-{index}"
        for key, operation_type in operation_type_by_key.items():
            if operation["operation_type"] == operation_type:
                expected[key].append(operation["operation_id"])
    changeset["operations"].reverse()

    assert resolve(case, changeset) == expected


def test_focused_ifccompare_and_type_reuse_accept_actual_operation_tags(
    tmp_path: Path,
) -> None:
    case = next(case for case in FREEZE["cases"] if case["case_id"] == "C1")
    proof = (
        ROOT
        / "dataset/processed/proof/repair-damage-restoration"
        / "c1-c5-offline-20260903-v2/C1"
    )
    repaired_path = tmp_path / "arbitrary-tags.ifc"
    repaired_model = ifcopenshell.open(str(proof / "03-repaired.ifc"))
    tags = {"beams": ["provider-beam-a", "provider-beam-b"]}
    for index, tag in enumerate(tags["beams"], start=1):
        restored = next(
            entity
            for entity in repaired_model.by_type("IfcBeam")
            if str(entity.Tag) == f"restore-beam-{index}"
        )
        restored.Tag = tag
    repaired_model.write(str(repaired_path))

    debug = compare_damage_restoration(
        case,
        original_path=proof / "01-original.ifc",
        repaired_path=repaired_path,
        repaired_tags=tags,
    )
    original_model = ifcopenshell.open(str(proof / "01-original.ifc"))
    damaged_model = ifcopenshell.open(str(proof / "02-damaged.ifc"))
    preflight = live_runner._type_reuse_preflight(
        case,
        original_model=original_model,
        damaged_model=damaged_model,
    )
    type_reuse = live_runner._verify_exact_type_reuse(
        case,
        damaged_model=damaged_model,
        repaired_model=ifcopenshell.open(str(repaired_path)),
        preflight=preflight,
        repaired_tags=tags,
    )

    assert debug["status"] == "passed"
    assert [member["repaired_tag"] for member in debug["members"]] == tags[
        "beams"
    ]
    assert type_reuse["status"] == "passed"


@pytest.mark.parametrize("case", FREEZE["cases"], ids=lambda c: c["case_id"])
def test_damage_restoration_c_case(case: dict, tmp_path: Path) -> None:
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    source = ROOT / str(case["source"])
    damaged = _apply_damage(case, scratch)

    original_model = ifcopenshell.open(str(source))
    damaged_model = ifcopenshell.open(str(damaged))
    type_fingerprints: dict[str, str] = {}
    for ifc_class, key, type_class in (
        ("IfcBeam", "beams", "IfcBeamType"),
        ("IfcColumn", "columns", "IfcColumnType"),
        ("IfcDoor", "doors", "IfcDoorStyle"),
        ("IfcWindow", "windows", "IfcWindowStyle"),
    ):
        for member in case["damage"].get(key, []):
            expected_type_id = member["prototype_intent"]["reference"]
            surviving_type = damaged_model.by_guid(expected_type_id)
            assert surviving_type is not None, (
                "DAMAGE_RESTORATION_TYPE_NOT_SURVIVING",
                case["case_id"],
                member["gid"],
                expected_type_id,
            )
            assert surviving_type.is_a(type_class), (
                case["case_id"],
                expected_type_id,
                surviving_type.is_a(),
            )
            type_fingerprints[expected_type_id] = type_authority_fingerprint(
                surviving_type
            )
    for ifc_class, key in (
        ("IfcBeam", "beams"),
        ("IfcColumn", "columns"),
        ("IfcDoor", "doors"),
        ("IfcWindow", "windows"),
    ):
        removed = len(case["damage"].get(key, []))
        if removed:
            assert len(damaged_model.by_type(ifc_class)) == len(
                original_model.by_type(ifc_class)
            ) - removed, ifc_class

    provider = _ReplayProvider(case)
    api = RepairAPI(
        tmp_path / "runs",
        provider=provider,
        orchestrator_factory=_orchestrator_factory,
        intent_schema_version="text2ifc/ifc-repair-intent/0.8",
    )
    final = api.start(str(damaged), str(case["request"]))

    runs_root = tmp_path / "runs"
    run_root = (
        runs_root / "runs" / str(final.run_id)
        if (runs_root / "runs" / str(final.run_id)).is_dir()
        else runs_root / str(final.run_id)
    )
    if final.status != "succeeded":
        evaluation_path = run_root / str(final.artifacts["evaluation"])
        evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
        pytest.fail(
            json.dumps(
                {"result": final.to_dict(), "evaluation": evaluation},
                ensure_ascii=False,
                indent=2,
            )
        )
    repaired = run_root / final.artifacts["successful_ifc"]
    assert repaired.is_file(), repaired
    repaired_model = ifcopenshell.open(str(repaired))

    for type_class in (
        "IfcBeamType",
        "IfcColumnType",
        "IfcDoorStyle",
        "IfcWindowStyle",
    ):
        assert len(repaired_model.by_type(type_class)) == len(
            damaged_model.by_type(type_class)
        ), ("DAMAGE_RESTORATION_GENERATED_TYPE_FORBIDDEN", type_class)
    for type_global_id, before_fingerprint in type_fingerprints.items():
        repaired_type = repaired_model.by_guid(type_global_id)
        assert repaired_type is not None, type_global_id
        assert type_authority_fingerprint(repaired_type) == before_fingerprint, (
            "DAMAGE_RESTORATION_REUSED_TYPE_MUTATED",
            type_global_id,
        )

    for ifc_class in (
        "IfcBeam",
        "IfcColumn",
        "IfcWall",
        "IfcDoor",
        "IfcWindow",
        "IfcOpeningElement",
    ):
        assert len(repaired_model.by_type(ifc_class)) == len(
            original_model.by_type(ifc_class)
        ), ifc_class

    # Restored beams must sit on the same storey as the originals.
    for beam_index, beam in enumerate(
        case["damage"].get("beams", []), start=1
    ):
        orig = original_model.by_guid(beam["gid"])
        orig_storey = None
        for rel in original_model.by_type("IfcRelContainedInSpatialStructure"):
            if orig in rel.RelatedElements and rel.RelatingStructure.is_a(
                "IfcBuildingStorey"
            ):
                orig_storey = rel.RelatingStructure
                break
        assert orig_storey is not None, beam["gid"]
        want = (beam["axis"]["start"]["x_mm"], beam["axis"]["start"]["y_mm"])
        restored = None
        for e in repaired_model.by_type("IfcBeam"):
            pl = e.ObjectPlacement.RelativePlacement.Location.Coordinates
            if abs(pl[0] - want[0]) < 1.0 and abs(pl[1] - want[1]) < 1.0:
                restored = e
                break
        assert restored is not None, beam["gid"]
        restored_storey = None
        for rel in repaired_model.by_type("IfcRelContainedInSpatialStructure"):
            if restored in rel.RelatedElements and rel.RelatingStructure.is_a(
                "IfcBuildingStorey"
            ):
                restored_storey = rel.RelatingStructure
                break
        assert restored_storey is not None
        assert restored_storey.Name == orig_storey.Name, (
            beam["gid"],
            orig_storey.Name,
            restored_storey.Name,
        )
        assert str(restored.Tag) == f"restore-beam-{beam_index}"
        assert _single_type_global_id(restored) == (
            beam["prototype_intent"]["reference"]
        )

    for column_index, column in enumerate(
        case["damage"].get("columns", []), start=1
    ):
        restored = next(
            item
            for item in repaired_model.by_type("IfcColumn")
            if str(item.Tag) == f"restore-column-{column_index}"
        )
        assert _single_type_global_id(restored) == (
            column["prototype_intent"]["reference"]
        )

    # Property restoration assertions.
    def _psets(model, entity):
        out = {}
        for rel in model.by_type("IfcRelDefinesByProperties"):
            if entity in rel.RelatedObjects:
                pd = rel.RelatingPropertyDefinition
                if pd.is_a("IfcPropertySet"):
                    for p in pd.HasProperties:
                        if p.NominalValue is not None:
                            out[f"{pd.Name}.{p.Name}"] = (
                                p.NominalValue.wrappedValue
                            )
        return out

    def _restored_beam(gid_want):
        beam = next(
            b
            for b in case["damage"].get("beams", [])
            if b["gid"] == gid_want
        )
        want = (beam["axis"]["start"]["x_mm"], beam["axis"]["start"]["y_mm"])
        for e in repaired_model.by_type("IfcBeam"):
            pl = e.ObjectPlacement.RelativePlacement.Location.Coordinates
            if abs(pl[0] - want[0]) < 1.0 and abs(pl[1] - want[1]) < 1.0:
                return e
        return None

    for beam in case["damage"].get("beams", []):
        claims = beam.get("property_intents") or []
        if not claims:
            continue
        restored = _restored_beam(beam["gid"])
        assert restored is not None, beam["gid"]
        props = _psets(repaired_model, restored)
        for claim in claims:
            key = f'{claim["set_name"]}.{claim["property_name"]}'
            assert key in props, (beam["gid"], key, sorted(props))
            assert props[key] == claim["raw_value"], (beam["gid"], key)

    for door_index, door in enumerate(
        case["damage"].get("doors", []), start=1
    ):
        claims = door.get("property_intents") or []
        if not claims:
            continue
        ogid = door["opening"]["gid"]
        restored = None
        for rel in repaired_model.by_type("IfcRelFillsElement"):
            if (
                rel.RelatingOpeningElement
                and str(rel.RelatingOpeningElement.GlobalId) == ogid
                and rel.RelatedBuildingElement
            ):
                restored = rel.RelatedBuildingElement
                break
        assert restored is not None, door["gid"]
        assert str(restored.Tag) == f"restore-door-{door_index}"
        assert _single_type_global_id(restored) == (
            door["prototype_intent"]["reference"]
        )
        props = _psets(repaired_model, restored)
        for claim in claims:
            key = f'{claim["set_name"]}.{claim["property_name"]}'
            assert key in props, (door["gid"], key, sorted(props))
            assert props[key] == claim["raw_value"], (door["gid"], key)

    for window_index, window in enumerate(
        case["damage"].get("windows", []), start=1
    ):
        claims = window.get("property_intents") or []
        if not claims:
            continue
        restored = None
        for e in repaired_model.by_type("IfcWindow"):
            if "Text2IFC" in str(e.Name):
                w = float(e.OverallWidth or 0)
                h = float(e.OverallHeight or 0)
                if (
                    abs(w - window["opening"]["width_mm"]) < 1.0
                    and abs(h - window["opening"]["height_mm"]) < 1.0
                ):
                    restored = e
                    break
        assert restored is not None, window["gid"]
        assert str(restored.Tag) == f"restore-window-{window_index}"
        assert _single_type_global_id(restored) == (
            window["prototype_intent"]["reference"]
        )
        props = _psets(repaired_model, restored)
        for claim in claims:
            key = f'{claim["set_name"]}.{claim["property_name"]}'
            assert key in props, (window["gid"], key, sorted(props))
            assert props[key] == claim["raw_value"], (window["gid"], key)

    for column_index, column in enumerate(
        case["damage"].get("columns", []), start=1
    ):
        restored = next(
            item
            for item in repaired_model.by_type("IfcColumn")
            if str(item.Tag) == f"restore-column-{column_index}"
        )
        props = _psets(repaired_model, restored)
        for claim in column.get("property_intents") or []:
            key = f'{claim["set_name"]}.{claim["property_name"]}'
            assert key in props, (column["gid"], key, sorted(props))
            assert props[key] == claim["raw_value"], (column["gid"], key)

    focused_debug = compare_damage_restoration(
        case,
        original_path=source,
        repaired_path=repaired,
    )
    assert focused_debug["status"] == "passed", focused_debug["members"]
    assert focused_debug["failed_member_count"] == 0
    assert focused_debug["member_count"] == sum(
        len(case["damage"].get(key, ()))
        for key in ("beams", "columns", "doors", "windows")
    )
    for member in focused_debug["members"]:
        assert member["geometry"]["status"] == "passed", member
        assert member["geometry"]["differences"] == []
        assert member["properties"]["status"] == "passed", member
        assert member["type_reuse"]["status"] == "passed", member
    comparison = focused_debug["whole_model_ifccompare"]
    assert comparison["comparison_status"] == "passed", comparison.get(
        "comparison_error_code"
    )
    assert comparison.get("added_ids")
