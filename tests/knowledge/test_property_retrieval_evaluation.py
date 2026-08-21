from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator


def _fixture(project_root: Path) -> tuple[dict, list[dict]]:
    path = (
        project_root
        / "tests"
        / "fixtures"
        / "knowledge"
        / "phase12_1_property_resolution.json"
    )
    document = json.loads(path.read_text(encoding="utf-8"))
    baseline_path = project_root / document["baseline_fixture"]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))["cases"]
    return document, [*baseline, *document["cases"]]


def test_phase12_1_frozen_evaluation_has_60_grouped_cases(
    project_root: Path,
) -> None:
    document, cases = _fixture(project_root)

    assert document["schema_version"] == "text2ifc/property-resolution-eval/0.2"
    assert len(cases) == 60
    assert document["baseline_case_count"] == 40
    assert document["addition_case_count"] == 20
    additions = document["cases"]
    assert Counter(item["family"] for item in additions) == {
        "window": 4,
        "door": 4,
        "wall": 4,
        "beam": 4,
        "column": 4,
    }
    assert len({item["id"] for item in cases}) == len(cases)
    assert all(item["group_id"] for item in additions)
    group_roles: dict[str, set[str]] = {}
    for item in additions:
        group_roles.setdefault(item["group_id"], set()).add(item["role"])
    assert all(len(roles) == 1 for roles in group_roles.values())
    assert any(item["phrase"] == "外窗" for item in additions)
    assert {
        (item["class"], item["phrase"])
        for item in additions
        if item["phrase"] == "load bearing"
    } == {("IfcBeam", "load bearing"), ("IfcColumn", "load bearing")}
    assert any(item["authorize"] is False for item in additions)


def test_executable_policy_is_the_frozen_alias_free_v02(
    project_root: Path,
) -> None:
    policy_path = (
        project_root
        / "schemas"
        / "ifc"
        / "knowledge"
        / "property_resolution_policy.v0.2.json"
    )
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (
            project_root
            / "schemas"
            / "ifc"
            / "knowledge"
            / "property_resolution_policy.schema.json"
        ).read_text(encoding="utf-8")
    )

    assert not list(Draft202012Validator(schema).iter_errors(policy))
    assert policy["alias_authority"] is False
    assert policy["vector_top1_authority"] is False
    assert policy["vector_margin_authority"] is False
    assert policy["standard_selection"] == "stage_1_5_required"
    assert 0.0 < policy["minimum_retrieval_score"] < 0.5


def test_real_bge_frozen_baseline_candidate_evaluation_passes_hard_gates(
    project_root: Path,
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_offline

    evaluate = getattr(
        run_phase12_offline,
        "evaluate_property_resolution_matrix",
        None,
    )
    assert callable(evaluate), "Phase 12.1 property evaluator is missing"
    result = evaluate(
        project_root=project_root,
        output_path=tmp_path / "property-evaluation.json",
        qdrant_path=tmp_path / "qdrant",
    )

    assert result["schema_version"] == (
        "text2ifc/phase12.1-property-resolution-evaluation/0.1"
    )
    assert result["status"] == "passed"
    assert result["case_count"] == 60
    assert result["failures_in_denominator"] > 0
    assert result["evaluator_id"] == "phase12.1.fixed-property-evaluator/0.1"
    assert result["baseline"]["case_count"] == 60
    assert result["candidate"]["case_count"] == 60
    assert result["candidate"]["false_standard_authorization_count"] == 0
    assert result["candidate"]["unoffered_selection_count"] == 0
    assert result["candidate"]["private_leakage_count"] == 0
    assert result["candidate"]["supported_top_k_recall"] == 1.0
    assert result["candidate"]["confirmed_standard_precision"] == 1.0
    assert set(result["candidate"]["family_slices"]) >= {
        "window",
        "door",
        "wall",
        "beam",
        "column",
    }
    assert result["hard_gates"] == {
        "all_supported_in_top_k": True,
        "zero_false_standard_authorization": True,
        "zero_wrong_class_type_unit_scope": True,
        "zero_alias_runtime_authority": True,
        "zero_unoffered_selection": True,
        "zero_private_leakage": True,
    }
    assert result["knowledge_health"]["status"] == "ready"
    assert result["knowledge_health"]["embedding_model_id"] == "BAAI/bge-m3"
    assert result["knowledge_health"]["runtime_mode"] == "production"
    assert result["knowledge_health"]["acceptance_eligible"] is True
    assert Path(result["output_path"]).is_file()
