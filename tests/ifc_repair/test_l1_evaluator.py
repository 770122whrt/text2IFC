import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import ifcopenshell
import ifcopenshell.guid
import pytest

from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.compare import evaluate_repair_application
from text2ifc_ifc_repair import evaluation as evaluation_module
from text2ifc_ifc_repair.evaluation_models import EvaluationStatus, LevelResult
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
WALL_ID = "1F6umJ5H50aeL3A1As_wTm"
OTHER_WALL_ID = "0AAAAAAAAAAAAAAAAAAAAA"
PSET_ID = "0BBBBBBBBBBBBBBBBBBBBB"
EXPECTED_L1_CHECK_IDS = {
    "l1.output.readable",
    "l1.output.schema",
    "l1.source.immutable",
    "l1.scope.created-roots",
    "l1.scope.modified-roots",
    "l1.scope.removed-roots",
    "l1.scope.relations",
    "l1.window.containment",
    "l1.window.dimensions",
    "l1.window.duplicate-chain",
    "l1.window.filling-topology",
    "l1.window.geometry-fit",
    "l1.window.host-topology",
    "l1.window.placement",
    "l1.window.tolerances",
    "l1.window.volume-preservation",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(root: Path) -> tuple[Path, Path, dict[str, Any], dict[str, Any], str]:
    case_dir = root / "case"
    mutation = remove_window_and_opening(
        source_path=SOURCE,
        output_dir=case_dir,
        wall_global_id=WALL_ID,
        opening_global_id="2cXV28XOjE6f6irhW0CO4t",
        window_global_id="2cXV28XOjE6f6irgi0CO4t",
    )
    private_manifest = json.loads(
        (case_dir / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    public_spec = project_public_repair_spec(
        private_manifest, request_id="l1-window-repair-001"
    )
    request = render_repair_request(public_spec)
    evidence = [
        "spec:/opening",
        "spec:/target/local_reference",
        "context:/candidate_targets/0",
    ]
    damaged = case_dir / "damaged.ifc"
    compact_damaged = root / "compact-damaged.ifc"
    source_model = ifcopenshell.open(str(damaged))
    compact = ifcopenshell.file(schema="IFC2X3")
    compact.add(source_model.by_type("IfcProject")[0])
    source_wall = source_model.by_guid(WALL_ID)
    source_storey = source_wall.ContainedInStructure[0].RelatingStructure
    storey = compact.add(source_storey)
    wall = compact.add(source_wall)
    compact.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=wall.OwnerHistory,
        RelatedElements=[wall],
        RelatingStructure=storey,
    )
    compact.create_entity(
        "IfcWall",
        GlobalId=OTHER_WALL_ID,
        OwnerHistory=wall.OwnerHistory,
        Name="out-of-scope wall",
    )
    compact.create_entity(
        "IfcPropertySet",
        GlobalId=PSET_ID,
        OwnerHistory=wall.OwnerHistory,
        Name="preserved root",
        HasProperties=[],
    )
    compact.write(str(compact_damaged))
    compact_fingerprint = _sha256(compact_damaged)
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.1",
        "changeset_id": "changeset-l1-window-repair-001",
        "base_model_fingerprint": "sha256:" + compact_fingerprint,
        "source_request_hash": "sha256:"
        + hashlib.sha256(request.encode("utf-8")).hexdigest(),
        "scope": {"target_ids": [WALL_ID], "forbidden_ids": []},
        "evidence_refs": evidence,
        "preconditions": ["target_exists"],
        "postconditions": ["opening_voids_wall", "window_fills_opening"],
        "operations": [
            {
                "operation_id": "operation-l1-window-001",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {"wall_global_id": WALL_ID},
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
                "evidence_refs": evidence,
            }
        ],
    }
    repaired = root / "repaired.ifc"
    application = apply_changeset(
        damaged_ifc_path=compact_damaged,
        repair_request=request,
        changeset=changeset,
        output_path=repaired,
        registry=create_default_registry(),
    )
    assert application["valid"] is True
    return compact_damaged, repaired, changeset, application, compact_fingerprint


@pytest.fixture(scope="module")
def l1_case(tmp_path_factory: pytest.TempPathFactory):
    return _case(tmp_path_factory.mktemp("l1-evaluator"))


def _evaluate(
    damaged: Path,
    repaired: Path,
    changeset: dict[str, Any],
    application: dict[str, Any],
) -> LevelResult:
    evaluator = getattr(evaluation_module, "evaluate_independent_l1", None)
    assert callable(evaluator), "structured independent L1 evaluation is absent"
    result = evaluator(
        damaged_ifc_path=damaged,
        repaired_ifc_path=repaired,
        changeset=changeset,
        application_result=application,
        registry=create_default_registry(),
    )
    assert isinstance(result, LevelResult)
    return result


def _check(result: LevelResult, check_id: str):
    matches = [check for check in result.checks if check.check_id == check_id]
    assert len(matches) == 1
    return matches[0]


def _assert_failed(result: LevelResult, check_id: str) -> None:
    check = _check(result, check_id)
    assert check.status is EvaluationStatus.FAILED
    assert check.mandatory is True
    assert check.evidence
    assert all(fact.expected_state and fact.actual_state for fact in check.evidence)
    assert result.status is not EvaluationStatus.PASSED


def _write_mutation(
    source: Path,
    destination: Path,
    mutate: Callable[[Any], None],
) -> Path:
    model = ifcopenshell.open(str(source))
    mutate(model)
    model.write(str(destination))
    return destination


def _created(application: dict[str, Any]) -> dict[str, str]:
    return {
        item["role"]: item["global_id"]
        for item in application["operations"][0]["changes"]["created"]
    }


def _other_wall(model: Any) -> Any:
    return model.by_guid(OTHER_WALL_ID)


def test_valid_window_l1_passes_from_reopened_ifc_and_preserves_source(l1_case) -> None:
    damaged, repaired, changeset, application, damaged_hash = l1_case

    result = _evaluate(damaged, repaired, changeset, application)

    assert result.status is EvaluationStatus.PASSED
    assert _sha256(damaged) == damaged_hash
    assert all(check.status is EvaluationStatus.PASSED for check in result.checks)
    assert [check.check_id for check in result.checks] == sorted(
        check.check_id for check in result.checks
    )
    assert {check.check_id for check in result.checks} == EXPECTED_L1_CHECK_IDS
    for check_id in EXPECTED_L1_CHECK_IDS:
        assert _check(result, check_id).status is EvaluationStatus.PASSED
    scope_evidence = [
        fact.actual_value
        for check in result.checks
        if check.check_id.startswith("l1.scope.")
        for fact in check.evidence
    ]
    canonical_scope_evidence = json.dumps(
        scope_evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    assert len(canonical_scope_evidence.encode("utf-8")) < 8192
    assert '"attributes":' not in canonical_scope_evidence


def test_applicator_self_report_cannot_authorize_collateral_wall_drift(
    l1_case, tmp_path: Path
) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    output = _write_mutation(
        repaired,
        tmp_path / "self-reported-wall-drift.ifc",
        lambda model: setattr(model.by_guid(WALL_ID), "Name", "collateral drift"),
    )
    claimed = copy.deepcopy(application)
    claimed["operations"][0]["changes"]["modified"].append(
        {"role": "host_wall", "global_id": WALL_ID}
    )

    result = _evaluate(damaged, output, changeset, claimed)

    _assert_failed(result, "l1.scope.modified-roots")
    evidence = _check(result, "l1.scope.modified-roots").evidence
    assert any(
        fact.actual_value.get("global_id") == WALL_ID
        and fact.actual_value.get("before") != fact.actual_value.get("after")
        for fact in evidence
        if isinstance(fact.actual_value, dict)
    )
    compatibility = evaluate_repair_application(
        damaged_ifc_path=damaged,
        repaired_ifc_path=output,
        changeset=changeset,
        application_result=claimed,
        registry=create_default_registry(),
    )
    assert compatibility["complete_repair_success"] is False
    assert compatibility["successful_artifact_publishable"] is False
    assert compatibility["l1"]["status"] == "failed"


def test_undeclared_extra_root_is_a_named_failure(l1_case, tmp_path: Path) -> None:
    damaged, repaired, changeset, application, _ = l1_case

    def add_root(model: Any) -> None:
        model.create_entity(
            "IfcWall",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=model.by_type("IfcOwnerHistory")[0],
            Name="undeclared extra root",
        )

    output = _write_mutation(repaired, tmp_path / "extra-root.ifc", add_root)
    result = _evaluate(damaged, output, changeset, application)
    _assert_failed(result, "l1.scope.created-roots")


def test_duplicate_same_role_root_is_rejected_regardless_of_report_order(
    l1_case, tmp_path: Path
) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    extra_window_id = ifcopenshell.guid.new()

    def add_extra_window(model: Any) -> None:
        legitimate = model.by_guid(_created(application)["window"])
        model.create_entity(
            "IfcWindow",
            GlobalId=extra_window_id,
            OwnerHistory=legitimate.OwnerHistory,
            Name="collateral same-role window",
            OverallHeight=legitimate.OverallHeight,
            OverallWidth=legitimate.OverallWidth,
        )

    output = _write_mutation(
        repaired,
        tmp_path / "duplicate-window-role.ifc",
        add_extra_window,
    )
    claimed = copy.deepcopy(application)
    created = claimed["operations"][0]["changes"]["created"]
    legitimate_index = next(
        index for index, item in enumerate(created) if item["role"] == "window"
    )
    created.insert(
        legitimate_index,
        {"role": "window", "ifc_class": "IfcWindow", "global_id": extra_window_id},
    )

    result = _evaluate(damaged, output, changeset, claimed)

    _assert_failed(result, "l1.scope.created-roots")


def test_unexpected_root_deletion_is_a_named_failure(l1_case, tmp_path: Path) -> None:
    damaged, repaired, changeset, application, _ = l1_case

    def delete_root(model: Any) -> None:
        model.remove(model.by_guid(PSET_ID))

    output = _write_mutation(repaired, tmp_path / "deleted-root.ifc", delete_root)
    result = _evaluate(damaged, output, changeset, application)
    _assert_failed(result, "l1.scope.removed-roots")


def test_extra_relationship_and_duplicate_chain_are_rejected(
    l1_case, tmp_path: Path
) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    ids = _created(application)

    def duplicate_void(model: Any) -> None:
        model.create_entity(
            "IfcRelVoidsElement",
            GlobalId=ifcopenshell.guid.new(),
            OwnerHistory=model.by_type("IfcOwnerHistory")[0],
            RelatingBuildingElement=model.by_guid(WALL_ID),
            RelatedOpeningElement=model.by_guid(ids["opening"]),
        )

    output = _write_mutation(repaired, tmp_path / "extra-void.ifc", duplicate_void)
    result = _evaluate(damaged, output, changeset, application)
    _assert_failed(result, "l1.scope.relations")
    _assert_failed(result, "l1.window.duplicate-chain")


def test_missing_filling_relationship_is_rejected(l1_case, tmp_path: Path) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    ids = _created(application)
    output = _write_mutation(
        repaired,
        tmp_path / "missing-fill.ifc",
        lambda model: model.remove(model.by_guid(ids["fills_relationship"])),
    )
    result = _evaluate(damaged, output, changeset, application)
    _assert_failed(result, "l1.window.filling-topology")


def test_wrong_host_is_rejected(l1_case, tmp_path: Path) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    ids = _created(application)

    def wrong_host(model: Any) -> None:
        model.by_guid(ids["voids_relationship"]).RelatingBuildingElement = _other_wall(
            model
        )

    output = _write_mutation(repaired, tmp_path / "wrong-host.ifc", wrong_host)
    result = _evaluate(damaged, output, changeset, application)
    _assert_failed(result, "l1.window.host-topology")


def test_wrong_spatial_containment_is_rejected(l1_case, tmp_path: Path) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    ids = _created(application)

    def remove_containment(model: Any) -> None:
        window = model.by_guid(ids["window"])
        relation = window.ContainedInStructure[0]
        relation.RelatedElements = tuple(
            element for element in relation.RelatedElements if element != window
        )

    output = _write_mutation(
        repaired, tmp_path / "wrong-containment.ifc", remove_containment
    )
    result = _evaluate(damaged, output, changeset, application)
    _assert_failed(result, "l1.window.containment")


@pytest.mark.parametrize(
    ("fault", "check_id"),
    [
        ("dimensions", "l1.window.dimensions"),
        ("placement", "l1.window.placement"),
    ],
)
def test_out_of_tolerance_window_measurements_are_not_silently_passed(
    l1_case, tmp_path: Path, fault: str, check_id: str
) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    ids = _created(application)

    def drift(model: Any) -> None:
        opening = model.by_guid(ids["opening"])
        if fault == "placement":
            point = opening.ObjectPlacement.RelativePlacement.Location
            coordinates = list(point.Coordinates)
            coordinates[0] += 10.0
            point.Coordinates = tuple(coordinates)
            return
        polyline = next(
            entity
            for entity in model.traverse(opening.Representation)
            if entity.is_a("IfcPolyline")
        )
        maximum_x = max(float(point.Coordinates[0]) for point in polyline.Points)
        for point in polyline.Points:
            coordinates = list(point.Coordinates)
            if float(coordinates[0]) == maximum_x:
                coordinates[0] += 10.0
                point.Coordinates = tuple(coordinates)

    output = _write_mutation(repaired, tmp_path / f"{fault}-drift.ifc", drift)
    result = _evaluate(damaged, output, changeset, application)
    _assert_failed(result, check_id)
    _assert_failed(result, "l1.window.tolerances")


def test_unmeasurable_mandatory_geometry_is_not_evaluable(
    l1_case, tmp_path: Path
) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    ids = _created(application)
    output = _write_mutation(
        repaired,
        tmp_path / "unmeasurable-geometry.ifc",
        lambda model: setattr(model.by_guid(ids["opening"]), "Representation", None),
    )

    result = _evaluate(damaged, output, changeset, application)

    assert _check(result, "l1.window.dimensions").status is EvaluationStatus.NOT_EVALUABLE
    assert result.status is EvaluationStatus.NOT_EVALUABLE


def test_unreadable_output_is_not_evaluable_and_non_passing(
    l1_case, tmp_path: Path
) -> None:
    damaged, _, changeset, application, _ = l1_case
    output = tmp_path / "unreadable.ifc"

    result = _evaluate(damaged, output, changeset, application)

    check = _check(result, "l1.output.readable")
    assert check.status is EvaluationStatus.NOT_EVALUABLE
    assert result.status is EvaluationStatus.NOT_EVALUABLE


def test_schema_mismatch_is_a_named_failure(l1_case, tmp_path: Path) -> None:
    damaged, _, changeset, application, _ = l1_case
    output = tmp_path / "ifc4.ifc"
    ifcopenshell.file(schema="IFC4").write(str(output))

    result = _evaluate(damaged, output, changeset, application)

    _assert_failed(result, "l1.output.schema")


def test_step_order_and_guid_identity_do_not_create_false_drift(
    l1_case, tmp_path: Path
) -> None:
    damaged, repaired, changeset, application, _ = l1_case
    rewritten = tmp_path / "rewritten.ifc"
    ifcopenshell.open(str(repaired)).write(str(rewritten))

    first = _evaluate(damaged, repaired, changeset, application)
    second = _evaluate(damaged, rewritten, changeset, application)

    assert first == second
    assert first.status is EvaluationStatus.PASSED
