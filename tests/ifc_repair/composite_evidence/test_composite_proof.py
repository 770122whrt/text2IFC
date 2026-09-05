"""Focused zero-Provider tests for the composite Proof extension.

Covers the operation-bound composite proof validator
(``scripts/ifc_repair/composite_evidence/composite_proof.py``) against the
frozen composite acceptance cases
(``docs/validation/repair-composite-milestone/composite-acceptance-freeze.json``),
using the deterministic offline driver (``offline_driver.py``) to produce real
repaired IFC artifacts through the production ``apply_changeset`` — no
Provider, network, synthetic, or cached result is involved.

Positive: every frozen positive case (C1..C5) applies and independently
re-proves, including repeated same-family operations bound by ``operation_id``.
Negative/tamper: the proof fails closed when an operation's geometry, binding,
type policy, property, or set membership is altered; the negative twin C5-N
passes only with zero stage-2 evidence and an unmutated source.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import ifcopenshell
import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.composite_evidence.composite_proof import (  # noqa: E402
    CompositeProofError,
    verify_composite_case,
)
from scripts.ifc_repair.composite_evidence.offline_driver import (  # noqa: E402
    build_bound_changeset,
    load_freeze,
    run_offline_case,
)
from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402

FREEZE = load_freeze()
CASES_BY_ID = {case["case_id"]: case for case in FREEZE["cases"]}
MODEL_PATHS = {
    model_id: ROOT / str(model["path"]) for model_id, model in FREEZE["models"].items()
}


def _run_case(tmp_path: Path, case_id: str) -> dict:
    case = CASES_BY_ID[case_id]
    source = MODEL_PATHS[case["model_id"]]
    output = tmp_path / f"{case_id}-repaired.ifc"
    return run_offline_case(case=case, source_path=source, output_path=output)


def _verify(tmp_path: Path, case_id: str, run: dict | None = None) -> dict:
    case = CASES_BY_ID[case_id]
    run = run or _run_case(tmp_path, case_id)
    application = run["application"]
    assert application["valid"] is True, application["issues"]
    assert application["published"] is True, application["issues"]
    source = MODEL_PATHS[case["model_id"]]
    return verify_composite_case(
        case=case,
        changeset=run["changeset"],
        application=application,
        source_model=ifcopenshell.open(str(source)),
        repaired_model=ifcopenshell.open(str(run["output_path"])),
        source_path=source,
        repaired_path=run["output_path"],
    )


# ---------------------------------------------------------------------------
# Freeze contract
# ---------------------------------------------------------------------------


def test_freeze_contains_six_cases_in_frozen_order() -> None:
    assert FREEZE["execution_order"] == ["C1", "C2", "C3", "C4", "C5", "C5-N"]
    assert [case["case_id"] for case in FREEZE["cases"]] == FREEZE["execution_order"]


def test_freeze_operation_counts_follow_the_scale_ladder() -> None:
    expected = {"C1": 2, "C2": 3, "C3": 5, "C4": 7, "C5": 8, "C5-N": 8}
    for case in FREEZE["cases"]:
        assert case["scale"]["operation_count"] == expected[case["case_id"]]
    assert CASES_BY_ID["C1"]["scale"]["families"] == ["beam", "column"]
    assert CASES_BY_ID["C3"]["scale"]["families"] == ["beam", "column", "window"]
    assert CASES_BY_ID["C4"]["scale"]["families"] == ["beam", "column", "door", "window"]
    assert CASES_BY_ID["C5"]["scale"]["families"] == ["beam", "column", "door", "window"]
    assert CASES_BY_ID["C5"]["scale"]["property_intent_count"] == 2


def test_every_predicate_binds_operation_id_and_type() -> None:
    for case in FREEZE["cases"]:
        if case["expected_terminal_class"] == "UNSUPPORTED_ATOMIC_GUARD":
            continue
        operation_ids = {op["operation_id"] for op in case["operations"]}
        for predicate in case["artifact_predicates"]:
            if predicate["kind"] == "atomic_operation_set":
                assert set(predicate["operation_ids"]) == operation_ids
                continue
            assert predicate["operation_id"] in operation_ids, predicate
            assert predicate["operation_type"], predicate


def test_repeated_same_family_operations_have_distinct_operation_ids() -> None:
    for case in FREEZE["cases"]:
        ids = [op["operation_id"] for op in case["operations"]]
        assert len(ids) == len(set(ids)), case["case_id"]
        types = [op["operation_type"] for op in case["operations"]]
        if case["case_id"] in {"C4", "C5", "C5-N"}:
            assert types.count("add_column") == 4, case["case_id"]
        if case["case_id"] in {"C3", "C5", "C5-N"}:
            assert types.count("add_beam") == 2, case["case_id"]


def test_negative_twin_declares_verified_absent_operation() -> None:
    case = CASES_BY_ID["C5-N"]
    registry = create_default_registry()
    unsupported = case["unsupported_operations"]
    assert len(unsupported) == 1
    assert unsupported[0]["operation_type"] == "structural_analysis_node"
    assert "structural_analysis_node" not in registry.operation_types
    assert case["expected_terminal_class"] == "UNSUPPORTED_ATOMIC_GUARD"
    # Twin keeps the positive composition substantially the same.
    positive = CASES_BY_ID["C5"]
    assert [op["operation_id"] for op in case["operations"]] == [
        op["operation_id"] for op in positive["operations"]
    ]


# ---------------------------------------------------------------------------
# Positive cases: apply + independent proof (zero Provider)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("case_id", ["C1", "C2", "C3", "C4", "C5"])
def test_positive_case_applies_and_proves_operation_bound(tmp_path: Path, case_id: str) -> None:
    proof = _verify(tmp_path, case_id)
    case = CASES_BY_ID[case_id]
    assert proof["status"] == "passed"
    predicate_ids = [item["predicate_id"] for item in proof["predicates"]]
    # Every frozen predicate is independently recomputed, plus preservation.
    for predicate in case["artifact_predicates"]:
        assert predicate["predicate_id"] in predicate_ids
    assert f"{case_id}-preservation" in predicate_ids


def test_c4_repeated_columns_are_proven_independently_by_operation_id(tmp_path: Path) -> None:
    proof = _verify(tmp_path, "C4")
    columns = [
        item
        for item in proof["predicates"]
        if item.get("operation_type") == "add_column"
    ]
    assert len(columns) == 4
    assert len({item["operation_id"] for item in columns}) == 4
    assert len({item["occurrence_global_id"] for item in columns}) == 4
    assert len({item["type_global_id"] for item in columns}) == 4


def test_c5_hero_proves_all_families_and_properties(tmp_path: Path) -> None:
    proof = _verify(tmp_path, "C5")
    by_kind = {}
    for item in proof["predicates"]:
        by_kind.setdefault(item.get("kind"), []).append(item)
    assert len(by_kind.get("structural_add", [])) == 6  # 4 columns + 2 beams
    structural_types = [
        item["operation_type"] for item in by_kind.get("structural_add", [])
    ]
    assert structural_types.count("add_column") == 4
    assert structural_types.count("add_beam") == 2
    assert len(by_kind.get("door_add", [])) == 1
    assert len(by_kind.get("window_add", [])) == 1
    properties = by_kind.get("generated_occurrence_property", [])
    assert {item["property"] for item in properties} == {
        "Pset_DoorCommon.FireRating",
        "Pset_WindowCommon.IsExternal",
    }


def test_c5_negative_twin_guard_with_zero_stage2(tmp_path: Path) -> None:
    case = CASES_BY_ID["C5-N"]
    source = MODEL_PATHS[case["model_id"]]
    proof = verify_composite_case(
        case=case,
        changeset={},
        application={},
        source_model=None,
        repaired_model=None,
        source_path=source,
        repaired_path=None,
        live_attempt_evidence=[{"stage": "stage1"}],
    )
    assert proof["status"] == "passed"
    guard = proof["predicates"][0]
    assert guard["stage2_attempts"] == 0


def test_c5_negative_twin_fails_when_stage2_attempted(tmp_path: Path) -> None:
    case = CASES_BY_ID["C5-N"]
    source = MODEL_PATHS[case["model_id"]]
    with pytest.raises(CompositeProofError, match="negative_guard_stage2_attempted"):
        verify_composite_case(
            case=case,
            changeset={},
            application={},
            source_model=None,
            repaired_model=None,
            source_path=source,
            repaired_path=None,
            live_attempt_evidence=[
                {"stage": "stage1"},
                {"stage": "stage2"},
            ],
        )


# ---------------------------------------------------------------------------
# Tamper / fail-closed behaviour
# ---------------------------------------------------------------------------


def test_proof_fails_when_repeated_column_geometry_swapped(tmp_path: Path) -> None:
    """Two same-family ops must not be interchangeable: swapping the frozen
    geometry of one column must break exactly that operation's predicate."""

    case = copy.deepcopy(CASES_BY_ID["C4"])
    run = _run_case(tmp_path, "C4")
    changeset = copy.deepcopy(run["changeset"])
    # Tamper: move C4-column-01 to C4-column-02's axis in the CHANGESET ONLY
    # (the repaired IFC still matches the original request), so the
    # deterministic GlobalId / geometry no longer matches.
    for op in changeset["operations"]:
        if op["operation_id"] == "C4-column-01":
            op["parameters"]["axis"]["base"]["x_mm"] = 94000
            op["parameters"]["axis"]["top"]["x_mm"] = 94000
    with pytest.raises(CompositeProofError) as error:
        verify_composite_case(
            case=case,
            changeset=changeset,
            application=run["application"],
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
            source_path=MODEL_PATHS[case["model_id"]],
            repaired_path=run["output_path"],
        )
    assert "C4-column-01" in str(error.value)


def test_proof_fails_when_operation_id_binding_is_duplicated(tmp_path: Path) -> None:
    """Duplicate operation ids fail closed at the changeSet schema layer.

    The proof contract binds predicates by frozen geometry (the live Provider
    authors its own ids), so id duplication per se is enforced where it
    belongs: ``validate_changeset`` rejects ``DUPLICATE_CHANGESET_OPERATION_ID``
    before any proof runs.  The geometry-level confusion the old tamper
    exercised remains covered by
    ``test_proof_fails_when_repeated_column_geometry_swapped``.
    """

    from text2ifc_ifc_repair.changesets import validate_changeset

    run = _run_case(tmp_path, "C3")
    changeset = copy.deepcopy(run["changeset"])
    for op in changeset["operations"]:
        if op["operation_id"] == "C3-beam-02":
            op["operation_id"] = "C3-beam-01"
    issues = validate_changeset(changeset)
    assert any(
        issue.code == "DUPLICATE_CHANGESET_OPERATION_ID" for issue in issues
    )


def test_proof_fails_when_atomic_set_is_incomplete(tmp_path: Path) -> None:
    case = CASES_BY_ID["C2"]
    run = _run_case(tmp_path, "C2")
    application = copy.deepcopy(run["application"])
    # Tamper: drop one applied operation from the application record; the
    # per-operation binding must fail closed before the atomic set check.
    application["operations"] = application["operations"][:1]
    with pytest.raises(CompositeProofError, match="application_binding"):
        verify_composite_case(
            case=case,
            changeset=run["changeset"],
            application=application,
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
            source_path=MODEL_PATHS[case["model_id"]],
            repaired_path=run["output_path"],
        )


def test_proof_fails_when_changeset_set_is_incomplete(tmp_path: Path) -> None:
    case = CASES_BY_ID["C2"]
    run = _run_case(tmp_path, "C2")
    changeset = copy.deepcopy(run["changeset"])
    # Tamper: drop one operation from the CHANGESET; the per-operation binding
    # must fail closed (the missing operation cannot be proven).
    changeset["operations"] = changeset["operations"][:1]
    with pytest.raises(CompositeProofError, match="operation_binding"):
        verify_composite_case(
            case=case,
            changeset=changeset,
            application=run["application"],
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
            source_path=MODEL_PATHS[case["model_id"]],
            repaired_path=run["output_path"],
        )


def test_proof_fails_when_wall_binding_is_ambiguous(tmp_path: Path) -> None:
    case = copy.deepcopy(CASES_BY_ID["C5"])
    run = _run_case(tmp_path, "C5")
    # Tamper: relax the frozen window wall binding so it matches many walls.
    predicate = next(
        item
        for item in case["artifact_predicates"]
        if item["kind"] == "window_add"
    )
    predicate["target_query"]["geometry_constraints"] = [
        constraint
        for constraint in predicate["target_query"]["geometry_constraints"]
        if constraint["field"] == "storey_elevation_mm"
    ]
    with pytest.raises(CompositeProofError, match="wall_binding"):
        verify_composite_case(
            case=case,
            changeset=run["changeset"],
            application=run["application"],
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
            source_path=MODEL_PATHS[case["model_id"]],
            repaired_path=run["output_path"],
        )


def test_proof_fails_when_property_value_drifts(tmp_path: Path) -> None:
    """A drifted property expectation fails closed.

    The property predicate binds by fact key AND value, so tampering the
    expected value (EI60 → EI90) leaves the predicate bound to no operation —
    fail-closed at resolution.  (When the key matches but the IFC-side value
    differs, the verification fails with ``property_value_mismatch``.)
    """

    case = copy.deepcopy(CASES_BY_ID["C5"])
    run = _run_case(tmp_path, "C5")
    predicate = next(
        item
        for item in case["artifact_predicates"]
        if item.get("kind") == "generated_occurrence_property"
        and item["property"]["property_name"] == "FireRating"
    )
    predicate["property"]["value"] = "EI90"
    # The proof binds property predicates by fact_key AND frozen value; a
    # tampered expectation matches no operation and fails closed at binding
    # (the value-equality contract itself lives in the same resolver).
    with pytest.raises(CompositeProofError, match="property_matched_0_operations"):
        verify_composite_case(
            case=case,
            changeset=run["changeset"],
            application=run["application"],
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
            source_path=MODEL_PATHS[case["model_id"]],
            repaired_path=run["output_path"],
        )


def test_proof_fails_when_entity_delta_is_wrong(tmp_path: Path) -> None:
    case = copy.deepcopy(CASES_BY_ID["C4"])
    run = _run_case(tmp_path, "C4")
    case["expected_entity_delta"]["IfcColumn"] = 3  # actual is 4
    with pytest.raises(CompositeProofError, match="entity_delta_mismatch"):
        verify_composite_case(
            case=case,
            changeset=run["changeset"],
            application=run["application"],
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
            source_path=MODEL_PATHS[case["model_id"]],
            repaired_path=run["output_path"],
        )


# ---------------------------------------------------------------------------
# Source immutability (production invariant, checked at this seam too)
# ---------------------------------------------------------------------------


def test_offline_apply_never_mutates_the_source_model(tmp_path: Path) -> None:
    import hashlib

    case = CASES_BY_ID["C5"]
    source = MODEL_PATHS[case["model_id"]]
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    _run_case(tmp_path, "C5")
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    assert before == after


def test_bound_changeset_bindings_resolve_to_frozen_targets(tmp_path: Path) -> None:
    """The offline driver's deterministic bindings match the frozen queries."""

    for case_id in ("C2", "C4", "C5"):
        case = CASES_BY_ID[case_id]
        changeset, bindings = build_bound_changeset(
            case=case, source_path=MODEL_PATHS[case["model_id"]]
        )
        operations = {op["operation_id"]: op for op in changeset["operations"]}
        for op in case["operations"]:
            operation_id = op["operation_id"]
            if "opening_query" in op.get("expected_target", {}):
                assert operation_id in bindings
                target = operations[operation_id]["target"]
                assert target["opening_global_id"] == bindings[operation_id]
            if "wall_query" in op.get("expected_target", {}):
                assert operation_id in bindings
                target = operations[operation_id]["target"]
                assert target["wall_global_id"] == bindings[operation_id]
