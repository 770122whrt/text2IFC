from __future__ import annotations

import json
import inspect
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
    group_counts = Counter(item["group_id"] for item in additions)
    assert len(group_counts) < len(additions)
    assert any(count > 1 for count in group_counts.values())
    assert any(item["phrase"] == "外窗" for item in additions)
    assert {
        (item["class"], item["phrase"])
        for item in additions
        if item["phrase"] == "load bearing"
    } == {("IfcBeam", "load bearing"), ("IfcColumn", "load bearing")}
    assert any(item["authorize"] is False for item in additions)


def test_phase12_1_evaluation_groups_are_non_vacuous_and_split_isolated(
    project_root: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_offline

    cases = run_phase12_offline._property_evaluation_cases(project_root)
    groups: dict[str, list[dict]] = {}
    for case in cases:
        groups.setdefault(case["group_id"], []).append(case)

    assert len(groups) < len(cases)
    assert any(len(members) > 1 for members in groups.values())
    assert all(
        len({member["group_split"] for member in members}) == 1
        for members in groups.values()
    )
    by_id = {case["id"]: case for case in cases}
    assert by_id["a01"]["group_id"] == by_id["p12w01"]["group_id"]
    assert by_id["p12b01"]["group_id"] == by_id["p12b02"]["group_id"]
    assert by_id["p12c01"]["group_id"] == by_id["p12c02"]["group_id"]


def test_candidate_evaluation_has_no_answer_equivalent_stage15_replay() -> None:
    from scripts.ifc_repair import run_phase12_offline

    source = inspect.getsource(
        run_phase12_offline.evaluate_property_resolution_matrix
    )
    assert "phase12_1_stage15_transcript_replay" not in source
    assert "_FrozenStage15PromptReplayProvider" not in source
    assert "_generate_frozen_stage15_candidate_decision" not in source
    assert "offline-frozen-oracle" not in source


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


def test_real_bge_evaluation_blocks_without_independent_stage15_outputs(
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
        "text2ifc/phase12.1-property-resolution-evaluation/0.2"
    )
    assert result["status"] == "blocked"
    assert result["reason_code"] == (
        "INDEPENDENT_STAGE15_CANDIDATE_OUTPUT_REQUIRED"
    )
    assert result["case_count"] == 60
    assert result["failures_in_denominator"] > 0
    assert result["evaluator_id"] == "phase12.1.fixed-property-evaluator/0.2"
    assert result["baseline"]["case_count"] == 60
    assert result["candidate"]["case_count"] == 60
    assert result["candidate"]["semantic_scored_count"] == 0
    assert result["candidate"]["semantic_unscored_count"] == 60
    assert result["candidate"]["false_standard_authorization_count"] is None
    assert result["candidate"]["private_leakage_count"] == 0
    assert result["candidate"]["supported_top_k_recall"] == 1.0
    assert result["candidate"]["confirmed_standard_precision"] is None
    assert result["evaluation_mode"] == (
        "offline_retrieval_only_stage15_fixture_excluded"
    )
    assert result["stage15_candidate_evidence"] == {
        "status": "missing_independent_output",
        "semantic_scored_count": 0,
        "fixture_or_replay_used_for_scoring": False,
        "provider_network_calls": 0,
    }
    assert result["provider_network_calls"] == 0
    assert set(result["candidate"]["family_slices"]) >= {
        "window",
        "door",
        "wall",
        "beam",
        "column",
    }
    assert result["hard_gates"] == {
        "all_supported_in_top_k": True,
        "independent_stage15_candidate_outputs_available": False,
        "zero_alias_runtime_authority": True,
        "zero_private_leakage": True,
    }
    assert result["knowledge_health"]["status"] == "ready"
    assert result["knowledge_health"]["embedding_model_id"] == "BAAI/bge-m3"
    assert result["knowledge_health"]["runtime_mode"] == "production"
    assert result["knowledge_health"]["acceptance_eligible"] is True
    assert Path(result["output_path"]).is_file()
