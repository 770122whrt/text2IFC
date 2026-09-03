import json
import copy
import ast
import inspect
import textwrap
from pathlib import Path

import ifcopenshell
import ifcopenshell.guid
import pytest

from scripts.ifc_repair import (
    run_phase11_offline,
    run_phase11_public_triplet_repair,
)
from text2ifc_ifc_repair.door_geometry import (
    measure_door_opening_alignment,
    select_door_placement_in_opening,
)
from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.geometry import product_geometry_bounds_in_host_mm
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.door import (
    FILL_OPERATION_TYPE,
    fill_door_operation_definition,
)
from text2ifc_ifc_repair.operations.hosted_opening import local_placement
from text2ifc_ifc_repair.spatial import resolve_opening_storey


ROOT = Path(__file__).resolve().parents[2]
PROOF_ROOT = (
    ROOT
    / "dataset"
    / "processed"
    / "proof"
    / "ifc-repair-success-cases"
)
KNOWN_FAILURE = (
    ROOT
    / "tests"
    / "fixtures"
    / "ifc_repair"
    / "phase11-door-known-failure"
)


def _check_proof_operation(
    case: Path,
    operation_id: str,
    *,
    reproduce_old_fault: bool = False,
) -> dict:
    changeset = json.loads(
        (case / "changeset" / "bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    application = json.loads(
        (case / "validation" / "application.json").read_text(
            encoding="utf-8"
        )
    )
    operation = next(
        item
        for item in changeset["operations"]
        if item["operation_id"] == operation_id
    )
    operation_result = next(
        item
        for item in application["operations"]
        if item["operation_id"] == operation_id
    )
    assert operation["operation_type"] == FILL_OPERATION_TYPE
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    if reproduce_old_fault:
        door_id = next(
            item["global_id"]
            for item in operation_result["changes"]["created"]
            if item["role"] == "door"
        )
        door = model.by_guid(door_id)
        opening = model.by_guid(operation["target"]["opening_global_id"])
        wall = opening.VoidsElements[0].RelatingBuildingElement
        door.ObjectPlacement = local_placement(
            model,
            relative_to=opening.ObjectPlacement,
            location=(0.0, 0.0, 0.0),
        )
        current_containment = door.ContainedInStructure[0]
        current_containment.RelatedElements = [
            item
            for item in current_containment.RelatedElements
            if item != door
        ]
        wall_containment = wall.ContainedInStructure[0]
        wall_containment.RelatedElements = [
            *wall_containment.RelatedElements,
            door,
        ]
    return fill_door_operation_definition().postcondition_checker(
        operation=operation,
        model=model,
        application=operation_result["changes"],
    )


def _created_door(case: Path, model: object, operation_id: str = "operation-door-001"):
    application = json.loads(
        (case / "validation" / "application.json").read_text(
            encoding="utf-8"
        )
    )
    operation = next(
        item
        for item in application["operations"]
        if item["operation_id"] == operation_id
    )
    global_id = next(
        item["global_id"]
        for item in operation["changes"]["created"]
        if item["role"] == "door"
    )
    return model.by_guid(global_id)


def test_mixed_regression_rejects_old_identity_placement_and_wall_storey() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )

    result = _check_proof_operation(
        case,
        "operation-door-001",
        reproduce_old_fault=True,
    )

    assert result["valid"] is False
    assert {
        "DOOR_GEOMETRY_ALIGNED_WITH_OPENING",
        "DOOR_STOREY_MATCHES_HOST",
    }.issubset({item["code"] for item in result["issues"]})


def test_supplied_vvo_fault_reproduces_exact_800_by_160_mm_world_offset() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    manifest = json.loads(
        (
            case / "validation" / "source-run-manifest.json"
        ).read_text(encoding="utf-8")
    )
    application = json.loads(
        (case / "validation" / "application.json").read_text(
            encoding="utf-8"
        )
    )
    original = ifcopenshell.open(str(case / "01-original.ifc"))
    repaired = ifcopenshell.open(
        str(KNOWN_FAILURE / "03-known-failing-repaired.ifc")
    )
    original_door = original.by_guid(
        manifest["damage"]["removed_doors"][0]["global_id"]
    )
    operation_result = next(
        item
        for item in application["operations"]
        if item["operation_id"] == "operation-door-001"
    )
    repaired_door = repaired.by_guid(
        next(
            item["global_id"]
            for item in operation_result["changes"]["created"]
            if item["role"] == "door"
        )
    )
    opening = repaired_door.FillsVoids[0].RelatingOpeningElement
    original_wall = (
        original_door.FillsVoids[0]
        .RelatingOpeningElement.VoidsElements[0]
        .RelatingBuildingElement
    )
    repaired_wall = (
        opening.VoidsElements[0].RelatingBuildingElement
    )
    original_bounds = product_geometry_bounds_in_host_mm(
        original_door, original_wall
    )
    faulty_bounds = product_geometry_bounds_in_host_mm(
        repaired_door, repaired_wall
    )

    assert [
        round(
            (
                faulty_bounds[axis][0]
                + faulty_bounds[axis][1]
                - original_bounds[axis][0]
                - original_bounds[axis][1]
            )
            / 2.0,
            3,
        )
        for axis in ("x", "y", "z")
    ] == [800.0, 160.0, 0.0]


def test_frozen_supplied_candidate_is_not_publishable_under_strict_l1() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    changeset = json.loads(
        (case / "changeset" / "bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    application = json.loads(
        (case / "validation" / "application.json").read_text(
            encoding="utf-8"
        )
    )
    model = ifcopenshell.open(
        str(KNOWN_FAILURE / "03-known-failing-repaired.ifc")
    )
    results = {}
    for operation in changeset["operations"]:
        if operation["operation_type"] != FILL_OPERATION_TYPE:
            continue
        applied = next(
            item
            for item in application["operations"]
            if item["operation_id"] == operation["operation_id"]
        )
        results[operation["operation_id"]] = (
            fill_door_operation_definition().postcondition_checker(
                operation=operation,
                model=model,
                application=applied["changes"],
            )
        )

    first_codes = {
        item["code"]
        for item in results["operation-door-001"]["issues"]
    }
    assert "DOOR_GEOMETRY_ALIGNED_WITH_OPENING" in first_codes
    assert all(result["valid"] is False for result in results.values())
    assert all(
        "DOOR_STOREY_MATCHES_HOST"
        in {item["code"] for item in result["issues"]}
        for result in results.values()
    )


def test_five_door_regression_rejects_old_geometrically_misaligned_repair() -> None:
    case = (
        PROOF_ROOT
        / "door"
        / "batch"
        / "vvo-five-door-preserve-opening"
    )

    results = [
        _check_proof_operation(
            case,
            f"operation-door-{index:03d}",
            reproduce_old_fault=True,
        )
        for index in range(1, 6)
    ]

    assert any(
        result["valid"] is False
        and "DOOR_GEOMETRY_ALIGNED_WITH_OPENING"
        in {item["code"] for item in result["issues"]}
        for result in results
    )


def test_corrected_vvo_door_proofs_pass_strict_postconditions() -> None:
    cases_and_counts = (
        (
            PROOF_ROOT
            / "door"
            / "batch"
            / "vvo-five-door-preserve-opening",
            5,
        ),
        (
            PROOF_ROOT
            / "mixed"
            / "door-window"
            / "vvo-two-door-two-window-mixed",
            2,
        ),
    )

    results = [
        _check_proof_operation(
            case,
            f"operation-door-{index:03d}",
        )
        for case, count in cases_and_counts
        for index in range(1, count + 1)
    ]

    assert all(result["valid"] is True for result in results)


def test_vvo_fill_applicator_aligns_reused_type_and_uses_opening_storey(
    tmp_path: Path,
) -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    changeset = json.loads(
        (case / "changeset" / "bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    operation = next(
        item
        for item in changeset["operations"]
        if item["operation_id"] == "operation-door-001"
    )
    isolated = copy.deepcopy(changeset)
    isolated["operations"] = [operation]
    isolated["scope"]["target_ids"] = [
        operation["target"]["opening_global_id"]
    ]
    request = (case / "input" / "request.txt").read_text(
        encoding="utf-8"
    ).rstrip("\r\n")
    output = tmp_path / "vvo-repaired-door.ifc"

    application = apply_changeset(
        damaged_ifc_path=case / "02-damaged.ifc",
        repair_request=request,
        changeset=isolated,
        output_path=output,
        registry=create_default_registry(),
    )

    assert application["valid"] and application["published"], json.dumps(
        application["issues"], ensure_ascii=False
    )
    repaired = ifcopenshell.open(str(output))
    changes = application["operations"][0]["changes"]
    door_id = next(
        item["global_id"]
        for item in changes["created"]
        if item["role"] == "door"
    )
    door = repaired.by_guid(door_id)
    opening = repaired.by_guid(operation["target"]["opening_global_id"])
    door_bounds = product_geometry_bounds_in_host_mm(door, opening)
    opening_bounds = product_geometry_bounds_in_host_mm(opening, opening)
    intersection_x = max(
        0.0,
        min(door_bounds["x"][1], opening_bounds["x"][1])
        - max(door_bounds["x"][0], opening_bounds["x"][0]),
    )
    intersection_z = max(
        0.0,
        min(door_bounds["z"][1], opening_bounds["z"][1])
        - max(door_bounds["z"][0], opening_bounds["z"][0]),
    )
    opening_face_area = (
        opening_bounds["x"][1] - opening_bounds["x"][0]
    ) * (opening_bounds["z"][1] - opening_bounds["z"][0])

    assert intersection_x * intersection_z / opening_face_area >= 0.95
    containers = [
        relation.RelatingStructure
        for relation in door.ContainedInStructure
        if relation.RelatingStructure.is_a("IfcBuildingStorey")
    ]
    assert len(containers) == 1
    assert containers[0].Name == "标高2"


def test_vvo_retained_opening_index_uses_opening_level_not_wall_base(
    tmp_path: Path,
) -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    database = tmp_path / "vvo-damaged.sqlite"

    build_ifc_index(case / "02-damaged.ifc", database)

    with SQLiteIndexRepository.open(database) as repository:
        opening = repository.get_by_global_id(
            "2IUEnGd5v4Yfg1ZkLtd0qa"
        )
        wall = repository.get_by_global_id("2HNE4WMQ1CXebZMaih8XoD")
        assert opening is not None and wall is not None
        assert opening.storey_name == "标高2"
        assert wall.storey_name == "标高0"


def test_opening_context_storey_fails_closed_without_wall_containment() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    door = _created_door(case, model)
    opening = door.FillsVoids[0].RelatingOpeningElement
    wall = opening.VoidsElements[0].RelatingBuildingElement
    containment = wall.ContainedInStructure[0]
    containment.RelatedElements = [
        item for item in containment.RelatedElements if item != wall
    ]

    with pytest.raises(
        ValueError, match="OPENING_HOST_STOREY_NOT_FOUND"
    ):
        resolve_opening_storey(opening, wall)


def test_opening_context_storey_fails_closed_on_conflicting_wall_containment() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    door = _created_door(case, model)
    opening = door.FillsVoids[0].RelatingOpeningElement
    wall = opening.VoidsElements[0].RelatingBuildingElement
    containment = wall.ContainedInStructure[0]
    other_storey = next(
        item
        for item in model.by_type("IfcBuildingStorey")
        if item != containment.RelatingStructure
    )
    model.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=containment.OwnerHistory,
        Name=None,
        Description=None,
        RelatedElements=[wall],
        RelatingStructure=other_storey,
    )

    with pytest.raises(
        ValueError, match="OPENING_HOST_STOREY_AMBIGUOUS"
    ):
        resolve_opening_storey(opening, wall)


def test_door_opening_measurement_is_invariant_to_rotated_host_wall() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    door = _created_door(case, model)
    opening = door.FillsVoids[0].RelatingOpeningElement
    wall = opening.VoidsElements[0].RelatingBuildingElement
    before = measure_door_opening_alignment(door, opening)
    wall.ObjectPlacement.RelativePlacement.RefDirection = model.create_entity(
        "IfcDirection", DirectionRatios=(0.0, 1.0, 0.0)
    )
    after = measure_door_opening_alignment(door, opening)

    assert before == after
    assert after["valid"] is True


def test_identity_compensation_and_180_degree_corner_conventions_are_equivalent() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    door = _created_door(case, model)
    opening = door.FillsVoids[0].RelatingOpeningElement
    canonical_bounds = product_geometry_bounds_in_host_mm(door, opening)
    canonical = measure_door_opening_alignment(door, opening)
    door.ObjectPlacement = local_placement(
        model,
        relative_to=opening.ObjectPlacement,
        location=(0.0, 0.0, 0.0),
        ref_direction=(-1.0, 0.0, 0.0),
    )
    reversed_bounds = product_geometry_bounds_in_host_mm(door, opening)
    reversed_convention = measure_door_opening_alignment(door, opening)

    assert canonical["valid"] is True
    assert reversed_convention["valid"] is True
    assert canonical_bounds == reversed_bounds


def test_door_placement_recentres_when_wall_opening_depth_changes() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    door = _created_door(case, model)
    opening = door.FillsVoids[0].RelatingOpeningElement
    solid = opening.Representation.Representations[0].Items[0]
    before = select_door_placement_in_opening(door, opening)
    solid.Depth = float(solid.Depth) + 80.0
    after = select_door_placement_in_opening(door, opening)

    assert before["diagnostics"]["valid"] is True
    assert after["diagnostics"]["valid"] is True
    assert round(after["location"][1] - before["location"][1], 6) == -40.0


def test_supported_left_and_right_handed_types_both_pass_geometry_gate() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    first = _created_door(case, model, "operation-door-001")
    second = _created_door(case, model, "operation-door-002")
    first_type = next(
        relation.RelatingType
        for relation in first.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    )
    second_type = next(
        relation.RelatingType
        for relation in second.IsDefinedBy
        if relation.is_a("IfcRelDefinesByType")
    )

    assert {
        str(first_type.OperationType),
        str(second_type.OperationType),
    } == {"SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT"}
    assert measure_door_opening_alignment(
        first, first.FillsVoids[0].RelatingOpeningElement
    )["valid"]
    assert measure_door_opening_alignment(
        second, second.FillsVoids[0].RelatingOpeningElement
    )["valid"]


def test_public_production_boundary_has_no_original_or_mutation_inputs() -> None:
    signature = inspect.signature(
        run_phase11_offline._execute_public_production
    )
    tree = ast.parse(
        textwrap.dedent(
            inspect.getsource(
                run_phase11_offline._execute_public_production
            )
        )
    )

    assert set(signature.parameters) == {
        "damaged_ifc_path",
        "repair_request",
        "changeset",
        "repaired_ifc_path",
        "expected_facts_by_operation",
        "registry",
        "validation_cache_dir",
        "repeat_warm_evaluation",
    }
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert "original" not in names
    assert "mutation" not in names
    assert "_source_chain" not in names


def test_authority_triplet_public_process_has_no_private_input_channel() -> None:
    signature = inspect.signature(
        run_phase11_public_triplet_repair.run_public_repair
    )
    source = inspect.getsource(run_phase11_public_triplet_repair)
    tree = ast.parse(source)

    assert set(signature.parameters) == {
        "damaged_ifc",
        "public_request_bundle",
        "output_root",
    }
    main_source = inspect.getsource(
        run_phase11_public_triplet_repair.main
    )
    assert "--original" not in main_source
    assert "--mutation" not in main_source
    assert "--deleted" not in main_source
    function_tree = ast.parse(
        textwrap.dedent(
            inspect.getsource(
                run_phase11_public_triplet_repair.run_public_repair
            )
        )
    )
    function_names = {
        node.id
        for node in ast.walk(function_tree)
        if isinstance(node, ast.Name)
    }
    assert "original" not in function_names
    assert "mutation_manifest" not in function_names
    assert "deleted_object_ids" not in function_names
    path_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
    }
    assert not any("01-original.ifc" in value for value in path_literals)


def test_authority_triplet_public_request_uses_only_geometry_selectors() -> None:
    bundle = json.loads(
        (KNOWN_FAILURE / "04-public-repair-input.json").read_text(
            encoding="utf-8"
        )
    )

    assert len(bundle["operations"]) == 4
    assert not any(
        key in operation["target_query"]
        for operation in bundle["operations"]
        for key in (
            "global_id",
            "names",
            "storey_name",
            "storey_global_id",
            "host_global_id",
        )
    )
    assert {
        operation["operation_type"]
        for operation in bundle["operations"]
    } == {
        "add_window_with_opening_to_wall",
        "fill_existing_opening_with_door",
    }


def test_door_geometry_measurement_failure_blocks_postcondition() -> None:
    case = (
        PROOF_ROOT
        / "mixed"
        / "door-window"
        / "vvo-two-door-two-window-mixed"
    )
    changeset = json.loads(
        (case / "changeset" / "bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    application = json.loads(
        (case / "validation" / "application.json").read_text(
            encoding="utf-8"
        )
    )
    operation = next(
        item
        for item in changeset["operations"]
        if item["operation_id"] == "operation-door-002"
    )
    operation_result = next(
        item
        for item in application["operations"]
        if item["operation_id"] == "operation-door-002"
    )
    model = ifcopenshell.open(str(case / "03-repaired.ifc"))
    door_id = next(
        item["global_id"]
        for item in operation_result["changes"]["created"]
        if item["role"] == "door"
    )
    model.by_guid(door_id).Representation = None

    result = fill_door_operation_definition().postcondition_checker(
        operation=operation,
        model=model,
        application=operation_result["changes"],
    )

    assert result["valid"] is False
    failed = {item["code"] for item in result["issues"]}
    assert "DOOR_GEOMETRY_ALIGNED_WITH_OPENING" in failed
    assert "measurement_error" in result["evidence"]["geometry_alignment"]
