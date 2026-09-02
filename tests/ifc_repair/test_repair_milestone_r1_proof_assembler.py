from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.ifc_repair import validate_success_cases as proof_validator
from scripts.ifc_repair.assemble_repair_milestone_r1_proof import (
    build_collection_case,
    build_terminal_record,
    validate_execution_result,
)


FROZEN_ORDER = [
    "E1",
    "E2",
    "E3",
    "E4",
    "M1",
    "M2",
    "M3",
    "H1",
    "H2",
    "H3",
    "H4",
    "A1",
]


def _source(path: Path) -> str:
    path.write_bytes(b"IFC source fixture")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_execution_result_must_be_one_passed_uninterrupted_frozen_run() -> None:
    cases = [
        {
            "case_id": case_id,
            "status": "passed",
            "contract_pass": True,
            "synthetic_fallback_used": False,
            "attempts": [{}, {}, {}],
            "final": {"run_id": f"run-{case_id}"},
        }
        for case_id in FROZEN_ORDER
    ]
    execution = {
        "schema_version": "text2ifc/repair-milestone-r1-execution-result/0.1",
        "status": "passed",
        "case_count": 12,
        "execution_order": FROZEN_ORDER,
        "transport_calls": 36,
        "cases": cases,
    }

    assert [item["case_id"] for item in validate_execution_result(execution)] == (
        FROZEN_ORDER
    )

    execution["execution_order"] = [*FROZEN_ORDER[:-2], "A1", "H4"]
    with pytest.raises(ValueError, match="R1_ASSEMBLER_EXECUTION_ORDER"):
        validate_execution_result(execution)


def test_h4_terminal_and_collection_case_preserve_no_output_contract(
    tmp_path: Path,
) -> None:
    digest = _source(tmp_path / "source.ifc")
    state = {
        "run_id": "repair-h4",
        "stage": "unsupported",
        "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
        "source": {"sha256": digest},
    }
    case_result = {
        "case_id": "H4",
        "final": {
            "run_id": "repair-h4",
            "status": "unsupported",
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "artifacts": {
                "evaluation": "terminal/evaluation.json",
                "evidence": "terminal/evidence.json",
                "manifest": "terminal/manifest.json",
            },
            "program_guard_evidence": {
                "candidate_output_paths": [],
                "mutation_attempted": False,
                "source_sha256_before": digest,
                "source_sha256_after": digest,
                "source_unchanged": True,
                "stage2_attempts": 0,
            },
        },
    }
    profile = {
        "case_id": "H4",
        "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
        "terminal_expectation": {
            "supported_capabilities": ["add_beam"],
            "unsupported_capabilities": ["structural_analysis_node"],
            "atomic_request": True,
        },
    }

    terminal = build_terminal_record(
        case_id="H4",
        profile=profile,
        state=state,
        case_result=case_result,
        source_relative="source.ifc",
        source_sha256=digest,
    )
    collection_case = build_collection_case(
        case_id="H4",
        terminal_class="UNSUPPORTED_ATOMIC_GUARD",
        case_root="cases/H4",
    )

    assert terminal["resume_success"] is False
    assert terminal["initial_stop"] == {
        "status": "unsupported",
        "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
        "stage2_attempts": 0,
        "apply_attempts": 0,
        "published_outputs": [],
        "supported_capabilities": ["add_beam"],
        "unsupported_capabilities": ["structural_analysis_node"],
        "atomic_request": True,
    }
    assert not (
        {"repaired_ifc", "changeset", "application"} & set(collection_case)
    )


def test_success_collection_case_declares_repair_artifacts_and_authority() -> None:
    item = build_collection_case(
        case_id="E1",
        terminal_class="SUCCESS",
        case_root="cases/E1",
        source_ifc="cases/E1/source.ifc",
        repaired_ifc="cases/E1/runtime/runs/run-E1/successful/repaired.ifc",
        changeset="cases/E1/runtime/runs/run-E1/changeset-v008.json",
        application="cases/E1/application.json",
        authority_replay={
            "intent": "cases/E1/runtime/runs/run-E1/intent/repair-intent.json",
            "resolution": "cases/E1/runtime/runs/run-E1/resolution-v007.json",
            "semantic_manifest": "cases/E1/runtime/runs/run-E1/semantic-manifest.json",
            "source_manifest": "cases/E1/manifest.json",
            "evidence_root": "cases/E1",
        },
    )

    assert item["status"] == "accepted"
    assert item["provider_evidence_mode"] == "live"
    assert item["repaired_ifc"].endswith("repaired.ifc")
    assert set(item["authority_replay"]) == {
        "intent",
        "resolution",
        "semantic_manifest",
        "source_manifest",
        "evidence_root",
    }


def test_current_success_terminal_payload_binds_manifest_and_status() -> None:
    result_artifacts = {
        "manifest": ".terminal-bundles/bundle/manifest.json",
        "evaluation": ".terminal-bundles/bundle/evaluation/public-evaluation.json",
        "successful_ifc": ".terminal-bundles/bundle/successful/repaired.ifc",
    }
    payload = {
        "status": "succeeded",
        "manifest": {
            "path": result_artifacts["manifest"],
            "schema_version": "text2ifc/ifc-repair-artifact-manifest/0.1",
            "sha256": "sha256:" + "a" * 64,
        },
    }

    assert proof_validator._r1_success_terminal_payload_matches(
        payload=payload,
        result_artifacts=result_artifacts,
    )
    payload["manifest"]["path"] = "spliced/manifest.json"
    assert not proof_validator._r1_success_terminal_payload_matches(
        payload=payload,
        result_artifacts=result_artifacts,
    )


def test_current_structural_stage2_selection_uses_stage2_profile() -> None:
    selection = proof_validator._r1_expected_stage2_selection(
        changeset={
            "operations": [
                {"operation_id": "beam-1", "operation_type": "add_beam"}
            ]
        },
        provider_draft={
            "schema_version": "text2ifc/ifc-repair-changeset-draft/0.3"
        },
    )

    assert selection["profile_ids"] == ["beam.add.stage2.v0.1"]


def test_h3_state_lineage_binds_resolution_reason_to_clarification_reason() -> None:
    selected = "IfcWindow:window-2"
    state = {
        "run_id": "repair-h3",
        "stage": "succeeded",
        "transitions": [
            {
                "transition_id": 4,
                "from_stage": "intent_ready",
                "to_stage": "clarification_required",
                "reason_code": "ambiguous",
                "result_artifacts": {},
                "stage_payload": {
                    "resolution": {
                        "path": "resolution-v004.json",
                        "schema_version": "text2ifc/ifc-resolution-flow/0.1",
                        "sha256": "sha256:" + "b" * 64,
                    }
                },
                "clarification": {
                    "reason_code": "ambiguous_target",
                    "candidates": [
                        {
                            "ifc_class": "IfcWindow",
                            "public_id": "window-1",
                            "token": "token-1",
                        },
                        {
                            "ifc_class": "IfcWindow",
                            "public_id": "window-2",
                            "token": "token-2",
                        },
                    ],
                },
            },
            {
                "transition_id": 5,
                "from_stage": "clarification_required",
                "to_stage": "intent_ready",
                "result_artifacts": {},
                "answer": {
                    "kind": "select_candidate",
                    "candidate_token": "token-2",
                },
            },
        ],
    }

    result = proof_validator._audit_r1_h3_state_selection(
        state=state,
        expected_selected_identity=selected,
    )

    assert result["selected_identity"] == selected


def test_m1_rejection_reason_is_bound_to_retained_admission() -> None:
    assert proof_validator._r1_m1_rejection_reason_matches(
        transition_reason="PROPERTY_VALUE_TYPE_INCOMPATIBLE",
        admission={"reason_code": "PROPERTY_VALUE_TYPE_INCOMPATIBLE"},
    )
    assert not proof_validator._r1_m1_rejection_reason_matches(
        transition_reason="property_resolution",
        admission={"reason_code": "PROPERTY_VALUE_TYPE_INCOMPATIBLE"},
    )
