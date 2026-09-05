"""Focused zero-Provider tests for composite preservation semantics (Section 9).

Verifies EXACT authorized whole-model deltas composed from ALL operations in
the atomic ChangeSet: ``IfcColumn: 88 -> 92`` is valid, ``88 -> 93`` is a
violation — not merely "no obviously unrelated mutation".
"""

from __future__ import annotations

import copy
import hashlib
import sys
from pathlib import Path

import ifcopenshell
import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.composite_evidence.offline_driver import (  # noqa: E402
    load_freeze,
    run_offline_case,
)
from scripts.ifc_repair.composite_evidence.preservation import (  # noqa: E402
    CompositePreservationError,
    composed_allowed_delta,
    verify_exact_composed_delta,
    verify_negative_zero_mutation,
    verify_no_unrelated_mutation,
)

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


@pytest.mark.parametrize("case_id", ["C1", "C2", "C3", "C4", "C5"])
def test_exact_composed_delta_passes_for_every_positive_case(
    tmp_path: Path, case_id: str
) -> None:
    run = _run_case(tmp_path, case_id)
    case = CASES_BY_ID[case_id]
    result = verify_exact_composed_delta(
        case=case,
        application=run["application"],
        source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
        repaired_model=ifcopenshell.open(str(run["output_path"])),
    )
    assert result["status"] == "exact_delta_verified"
    # The composed allowed set covers every operation's authorized delta.
    assert result["allowed_id_count"] >= case["scale"]["operation_count"]


@pytest.mark.parametrize("case_id", ["C1", "C3", "C4", "C5"])
def test_off_by_one_entity_delta_is_a_violation(tmp_path: Path, case_id: str) -> None:
    """88 -> 93 must FAIL even though 88 -> 92 is the authorized delta."""

    run = _run_case(tmp_path, case_id)
    case = copy.deepcopy(CASES_BY_ID[case_id])
    # Find a class with a positive expected delta and inflate it by one.
    target_cls = next(
        cls for cls, delta in case["expected_entity_delta"].items() if delta > 0
    )
    case["expected_entity_delta"][target_cls] += 1
    with pytest.raises(
        CompositePreservationError, match="exact_entity_delta_violated"
    ):
        verify_exact_composed_delta(
            case=case,
            application=run["application"],
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
        )


def test_missing_authorized_delta_is_a_violation(tmp_path: Path) -> None:
    run = _run_case(tmp_path, "C4")
    case = copy.deepcopy(CASES_BY_ID["C4"])
    case["expected_entity_delta"]["IfcColumn"] = 3  # actual 4
    with pytest.raises(
        CompositePreservationError, match="exact_entity_delta_violated"
    ):
        verify_exact_composed_delta(
            case=case,
            application=run["application"],
            source_model=ifcopenshell.open(str(MODEL_PATHS[case["model_id"]])),
            repaired_model=ifcopenshell.open(str(run["output_path"])),
        )


@pytest.mark.parametrize("case_id", ["C1", "C3", "C4", "C5"])
def test_production_comparator_reports_zero_unrelated_mutation(
    tmp_path: Path, case_id: str
) -> None:
    run = _run_case(tmp_path, case_id)
    case = CASES_BY_ID[case_id]
    result = verify_no_unrelated_mutation(
        case=case,
        application=run["application"],
        source_path=MODEL_PATHS[case["model_id"]],
        repaired_path=run["output_path"],
    )
    assert result["status"] == "passed"
    assert result["unexpected_changed_ids"] == []


def test_comparator_flags_mutation_outside_allowed_delta(tmp_path: Path) -> None:
    """A change outside the composed authorized set must fail preservation."""

    run = _run_case(tmp_path, "C1")
    case = CASES_BY_ID["C1"]
    # Shrink the allowed set so one authorized id becomes unauthorized.
    application = copy.deepcopy(run["application"])
    changes = application["operations"][0]["changes"]
    created = [item for item in changes.get("created", ()) if item.get("role") == "beam"]
    assert created, changes
    application["operations"][0]["changes"] = {
        **changes,
        "created": [
            item for item in changes.get("created", ()) if item is not created[0]
        ],
    }
    with pytest.raises(CompositePreservationError, match="unrelated_mutation"):
        verify_no_unrelated_mutation(
            case=case,
            application=application,
            source_path=MODEL_PATHS[case["model_id"]],
            repaired_path=run["output_path"],
        )


def test_composed_allowed_delta_unions_all_operations(tmp_path: Path) -> None:
    run = _run_case(tmp_path, "C4")
    application = run["application"]
    per_operation = []
    for item in application["operations"]:
        single = {"operations": [item]}
        per_operation.append(composed_allowed_delta(single))
    union = composed_allowed_delta(application)
    # Every operation's authorized ids appear in the composed union.
    for delta in per_operation:
        assert delta <= union
    # The union is strictly larger than any single operation's delta.
    assert all(len(union) > len(delta) for delta in per_operation)


def test_negative_twin_source_zero_mutation(tmp_path: Path) -> None:
    case = CASES_BY_ID["C5-N"]
    source = MODEL_PATHS[case["model_id"]]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    result = verify_negative_zero_mutation(
        case=case,
        source_path=source,
        source_sha256_before=digest,
        source_sha256_after=digest,
    )
    assert result["zero_mutation"] is True


def test_negative_twin_detects_source_mutation(tmp_path: Path) -> None:
    case = CASES_BY_ID["C5-N"]
    source = MODEL_PATHS[case["model_id"]]
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(CompositePreservationError, match="source_mutated"):
        verify_negative_zero_mutation(
            case=case,
            source_path=source,
            source_sha256_before=digest,
            source_sha256_after="sha256:" + "0" * 64,
        )
