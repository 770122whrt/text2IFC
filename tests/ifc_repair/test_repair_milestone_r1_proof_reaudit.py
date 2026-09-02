from __future__ import annotations

import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

import ifcopenshell
import pytest

from scripts.ifc_repair import validate_success_cases as proof_validator
from tests.ifc_repair.test_beam_application import D7N, _changeset, _parameters
from tests.ifc_repair.test_repair_milestone_r1_proof import (
    _apply_property_case,
)
from tests.ifc_repair.test_r1_live_attempt_audit import (
    _attempt as _base_live_attempt,
)
from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.run_models import RunStage
from text2ifc_ifc_repair.run_store import RunStore


WINDOW_ID = "1PkWQ2IbXBH9Ib7VGdBY7r"
H3_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "dataset/external/ifc-bench/projects/duplex/arc.ifc"
)
H3_SELECTED = "IfcWindow:1hOSvn6df7F8_7GcBWlS2V"
H3_OFFERED = (
    "IfcWindow:1hOSvn6df7F8_7GcBWlS1M",
    H3_SELECTED,
    "IfcWindow:1hOSvn6df7F8_7GcBWlS4Q",
    "IfcWindow:1hOSvn6df7F8_7GcBWlSga",
    "IfcWindow:1hOSvn6df7F8_7GcBWlSnC",
)


def _property_operation(
    *,
    operation_id: str,
    target_id: str,
    set_name: str,
    property_name: str,
    value_type: str,
    value: Any,
) -> dict[str, Any]:
    fact_key = f"pset:{set_name}.{property_name}"
    return {
        "operation_id": operation_id,
        "operation_type": "set_occurrence_properties",
        "target": {"element_global_id": target_id},
        "parameters": {},
        "evidence_refs": ["property-resolution:/claim-h1/decision.json"],
        "semantic_manifest": {
            "manifest_id": f"manifest-{operation_id}",
            "policy_id": "occurrence.property.l2",
            "policy_version": "0.1",
        },
        "semantic_assignments": [
            {
                "operation_id": operation_id,
                "fact_key": fact_key,
                "source_fact_key": fact_key,
                "value": value,
                "value_type": value_type,
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "explicit_request",
                "source_ref": "property-resolution:/claim-h1/decision.json",
                "provenance": ["property-resolution:fixture"],
                "authoring_action": "set_occurrence_pset",
            }
        ],
    }


def _h3_initial_intent() -> dict[str, Any]:
    source = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "将 Level 2 中 819 mm × 759 mm 类型的窗设置为外窗。",
    }
    return {
        "schema_version": "text2ifc/ifc-repair-intent/0.8",
        "request_id": "r1-H3",
        "source_request_hash": "sha256:" + "1" * 64,
        "model_fingerprint": "sha256:" + "2" * 64,
        "prompt_fingerprint": "sha256:" + "3" * 64,
        "operations": [
            {
                "operation_id": "h3-window-property",
                "operation_type": "set_occurrence_properties",
                "routing_intent": {
                    "component_family": "window",
                    "action": "set_properties",
                    "operation_profile": "occurrence.set-properties",
                    "source": source,
                },
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcWindow"],
                    "names": ["819mm x 759mm"],
                    "storey_name": "Level 2",
                    "max_candidates": 5,
                    "winner_margin": 10,
                },
                "parameters": {},
                "attribute_intents": [],
                "property_intents": [
                    {
                        "intent_kind": "natural_language_property",
                        "property_phrase": "外窗",
                        "raw_value": True,
                        "raw_unit": None,
                        "scope": "occurrence_direct",
                        "source": source,
                    }
                ],
                "semantic_bundle_refs": [],
                "quantity_intents": [],
                "occurrence_reuse_intent": None,
                "prototype_intent": None,
                "provenance": [source],
            }
        ],
        "unsupported_requests": [],
        "semantic_bundles": [],
        "provenance": [source],
    }


def _h4_intent() -> dict[str, Any]:
    source = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "Add a Beam and a structural analysis node atomically.",
    }
    return {
        "schema_version": "text2ifc/ifc-repair-intent/0.8",
        "request_id": "r1-H4",
        "source_request_hash": "sha256:" + "4" * 64,
        "model_fingerprint": "sha256:" + "5" * 64,
        "prompt_fingerprint": "sha256:" + "6" * 64,
        "operations": [
            {
                "operation_id": "h4-beam",
                "operation_type": "add_beam",
                "routing_intent": {
                    "component_family": "beam",
                    "action": "add",
                    "operation_profile": "beam.add.v0.3",
                    "source": source,
                },
                "target_query": {
                    "schema_version": "text2ifc/ifc-target-query/0.1",
                    "allowed_ifc_classes": ["IfcBuildingStorey"],
                    "names": ["Level 5"],
                },
                "parameters": {
                    "axis": {
                        "start": {"x_mm": 2000, "y_mm": 10000, "z_mm": 3000},
                        "end": {"x_mm": 8000, "y_mm": 10000, "z_mm": 3000},
                    },
                    "section": {
                        "shape": "rectangle",
                        "width_mm": 300,
                        "height_mm": 500,
                    },
                },
                "attribute_intents": [],
                "property_intents": [],
                "semantic_bundle_refs": [],
                "quantity_intents": [],
                "occurrence_reuse_intent": None,
                "prototype_intent": None,
                "provenance": [source],
            }
        ],
        "unsupported_requests": [
            {
                "unsupported_id": "structural_analysis_node",
                "kind": "registered_capability",
                "operation_id": "h4-beam",
                "capability_id": "structural_analysis_node",
                "source": source,
            }
        ],
        "semantic_bundles": [],
        "provenance": [source],
    }


def _h4_state(*, leak_stage2: bool = False) -> dict[str, Any]:
    transitions = [
        {
            "to_stage": "created",
            "reason_code": None,
            "result_artifacts": {},
        },
        {
            "to_stage": "index_ready",
            "reason_code": None,
            "result_artifacts": {},
        },
    ]
    if leak_stage2:
        transitions.append(
            {
                "to_stage": "changeset_ready",
                "reason_code": None,
                "result_artifacts": {"successful_ifc": "repaired.ifc"},
            }
        )
    transitions.append(
        {
            "to_stage": "unsupported",
            "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
            "result_artifacts": {
                "manifest": ".terminal-bundles/failure/manifest.json",
                "evidence": ".terminal-bundles/failure/terminal/evidence.json",
            },
        }
    )
    return {
        "stage": "unsupported",
        "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
        "transitions": transitions,
        "result_artifacts": transitions[-1]["result_artifacts"],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _canonical_json_sha256(value: Any) -> str:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _r1_live_attempt(
    *,
    case_id: str,
    stage: str,
    parent_attempt_id: str | None,
    response_document: Mapping[str, Any],
    selection: Mapping[str, Any] | None = None,
    rendered_prompt: str | None = None,
) -> dict[str, Any]:
    attempt = _base_live_attempt(
        case_id=case_id,
        stage=stage,
        parent_attempt_id=parent_attempt_id,
    )
    if stage == "stage1":
        catalog = proof_validator._r1_expected_stage1_profiles()
        attempt["profile_ids"] = [str(item["profile_id"]) for item in catalog]
        attempt["profile_versions"] = [
            str(item["profile_version"]) for item in catalog
        ]
        attempt["profile_hashes"] = [
            str(item["profile_hash"]) for item in catalog
        ]
    elif stage == "stage2":
        assert selection is not None
        attempt["profile_ids"] = list(selection["profile_ids"])
        attempt["profile_versions"] = [
            str(item["profile_version"]) for item in selection["profiles"]
        ]
        attempt["profile_hashes"] = list(selection["profile_hashes"])
        attempt["few_shot_ids"] = list(selection["few_shot_ids"])
        attempt["few_shot_hashes"] = list(selection["few_shot_hashes"])
        attempt["few_shot_bindings"] = [
            {"few_shot_id": example_id, "few_shot_hash": digest}
            for example_id, digest in zip(
                attempt["few_shot_ids"],
                attempt["few_shot_hashes"],
                strict=True,
            )
        ]
    if rendered_prompt is not None:
        attempt["request"]["messages"] = [
            {"role": "user", "content": rendered_prompt}
        ]
        attempt["request_sha256"] = _canonical_json_sha256(attempt["request"])
    attempt["response"]["content"] = dict(response_document)
    attempt["response_sha256"] = _canonical_json_sha256(attempt["response"])
    return attempt


def _r1_live_provenance_fixture(
    tmp_path: Path,
    *,
    local_property_decision: Mapping[str, Any] | None = None,
    local_rendered_prompt: str | None = None,
) -> tuple[dict[str, Path], dict[str, Any], dict[str, Any]]:
    case_id = "E1"
    intent = _h3_initial_intent()
    intent["request_id"] = "r1-E1"
    intent["operations"][0]["operation_id"] = "e1-window-property"
    property_operation = _property_operation(
        operation_id="e1-window-property",
        target_id=WINDOW_ID,
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value_type="IfcBoolean",
        value=True,
    )
    changeset = {
        "base_model_fingerprint": "sha256:" + "7" * 64,
        "source_request_hash": intent["source_request_hash"],
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "8" * 64,
        "scope": {"target_ids": [WINDOW_ID], "forbidden_ids": []},
        "operations": [property_operation],
    }
    provider_draft = deepcopy(changeset)
    provider_draft["schema_version"] = (
        "text2ifc/ifc-repair-changeset-draft/0.2"
    )
    selection = proof_validator.select_prompt_profiles(
        ["occurrence.set-properties"]
    ).to_dict()
    stage1 = _r1_live_attempt(
        case_id=case_id,
        stage="stage1",
        parent_attempt_id=None,
        response_document={
            "operations": intent["operations"],
            "semantic_bundles": intent["semantic_bundles"],
            "provenance": intent["provenance"],
        },
    )
    property_decision = {
        "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
        "decision": "confirmed",
        "selected_candidate_id": (
            "candidate:1:ifc2x3:Pset_WindowCommon.IsExternal"
        ),
        "conflicting_candidate_ids": [],
        "clarification_question": None,
    }
    decision_schema = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "schemas/agent/ifc-property-rerank-decision-0.1.schema.json"
        ).read_text(encoding="utf-8")
    )
    property_query = {
        "query_id": "query-e1",
        "run_id": "run-e1",
        "operation_id": "e1-window-property",
        "claim_id": "claim-001",
    }
    candidate_set = {
        "candidate_set_id": "candidate-set-e1",
        "query_id": "query-e1",
        "candidates": [
            {
                "candidate_id": (
                    "candidate:1:ifc2x3:Pset_WindowCommon.IsExternal"
                )
            }
        ],
    }
    renderer_input = {
        "PROPERTY_QUERY": property_query,
        "CANDIDATE_SET": candidate_set,
        "DECISION_SCHEMA": decision_schema,
        "PREVIOUS_VALIDATION_FEEDBACK": [],
    }
    rendered_prompt = str(
        render_prompt(
            template_id=proof_validator.PROPERTY_RESOLUTION_TEMPLATE_ID,
            inputs=renderer_input,
        )["text"]
    )
    stage15 = _r1_live_attempt(
        case_id=case_id,
        stage="property_resolution",
        parent_attempt_id=stage1["attempt_id"],
        response_document=property_decision,
        rendered_prompt=rendered_prompt,
    )
    stage2 = _r1_live_attempt(
        case_id=case_id,
        stage="stage2",
        parent_attempt_id=stage15["attempt_id"],
        response_document=provider_draft,
        selection=selection,
    )
    final_state = _r1_live_success_state()
    case_result = {
        "case_id": case_id,
        "final": {
            "run_id": final_state["run_id"],
            "state_version": final_state["state_version"],
            "status": final_state["stage"],
            "reason_code": final_state["reason_code"],
            "complete_repair_success": True,
            "successful_artifact_publishable": True,
            "artifacts": deepcopy(final_state["result_artifacts"]),
        },
        "attempts": [stage1, stage15, stage2],
        "synthetic_fallback_used": False,
        "private_evidence_detected": False,
    }
    live_result = {
        "evidence_mode": "live",
        "provider_evidence_mode": "live",
        "execution_mode": "production_live",
        "synthetic_fallback_used": False,
        "cases": [case_result],
    }
    case_root = tmp_path / "case"
    claim_attempt = (
        case_root
        / "property-resolution"
        / "e1-window-property"
        / "claim-001"
        / "provider"
        / "attempt-001"
    )
    claim_root = claim_attempt.parents[1]
    _write_json(claim_root / "query.json", property_query)
    _write_json(claim_root / "candidate-set.json", candidate_set)
    _write_json(
        claim_attempt / "parsed-response.json",
        dict(local_property_decision or property_decision),
    )
    _write_json(claim_attempt / "provider-metadata.json", stage15["metadata"])
    _write_json(
        claim_attempt / "trace.json",
        {
            "schema_version": "text2ifc/ifc-property-resolution-trace/0.1",
            "attempt_id": (
                "property-resolution-attempt:run-e1:e1-window-property:"
                "claim-001:1"
            ),
            "run_id": "run-e1",
            "operation_id": "e1-window-property",
            "claim_id": "claim-001",
            "query_id": "query-e1",
            "candidate_set_id": "candidate-set-e1",
            "attempt": 1,
            "template_id": proof_validator.PROPERTY_RESOLUTION_TEMPLATE_ID,
            "template_hash": proof_validator.PROPERTY_RESOLUTION_TEMPLATE_HASH,
            "parse_status": "ok",
            "status": "valid",
            "evidence_class": "live",
            "acceptance_eligible": True,
        },
    )
    _write_json(
        claim_attempt / "raw-response.json",
        {
            "text": json.dumps(property_decision, ensure_ascii=False),
            "transport": {
                "request": stage15["request"],
                "response": stage15["response"],
            },
        },
    )
    _write_json(
        claim_attempt / "renderer-input.json",
        renderer_input,
    )
    _write_json(claim_attempt / "validation-feedback.json", [])
    (claim_attempt / "rendered-prompt.txt").write_text(
        (
            rendered_prompt
            if local_rendered_prompt is None
            else local_rendered_prompt
        ),
        encoding="utf-8",
    )
    artifacts = {
        "live-result.json": live_result,
        "case-result.json": case_result,
        "provider-draft.json": provider_draft,
        "prompt-profile-selection.json": selection,
        "production-boundary.json": {
            "schema_version": "text2ifc/production-input-boundary/0.2",
            "entrypoint": "run_repair_milestone_r1.py",
            "ifc_inputs": ["damaged_ifc_path"],
            "request_inputs": ["public_request_bundle"],
            "original_ifc_supplied": False,
            "mutation_manifest_supplied": False,
            "deleted_object_ids_supplied": False,
            "private_comparator_available_during_repair": False,
            "damaged_ifc_sha256": "sha256:" + "9" * 64,
            "request_sha256": intent["source_request_hash"],
            "resolved_target_count": 1,
        },
    }
    for name, document in artifacts.items():
        _write_json(case_root / name, document)
    roles = {
        "live_provider_result": case_root / "live-result.json",
        "live_provider_case_result": case_root / "case-result.json",
        "live_provider_draft": case_root / "provider-draft.json",
        "live_prompt_profile_selection": case_root
        / "prompt-profile-selection.json",
        "production_input_boundary": case_root / "production-boundary.json",
        "property_parsed_response": claim_attempt / "parsed-response.json",
        "property_provider_metadata": claim_attempt / "provider-metadata.json",
        "property_trace": claim_attempt / "trace.json",
        "property_raw_response": claim_attempt / "raw-response.json",
        "property_rendered_prompt": claim_attempt / "rendered-prompt.txt",
        "property_renderer_input": claim_attempt / "renderer-input.json",
        "property_validation_feedback": claim_attempt / "validation-feedback.json",
        "property_query": claim_root / "query.json",
        "property_candidate_set": claim_root / "candidate-set.json",
    }
    return roles, intent, changeset


def _r1_live_success_state() -> dict[str, Any]:
    return {
        "run_id": "run-e1",
        "state_version": 7,
        "stage": "succeeded",
        "reason_code": None,
        "result_artifacts": {
            "manifest": "published/manifest.json",
            "successful_ifc": "published/successful/repaired.ifc",
            "evaluation": "published/evaluation/public-evaluation.json",
        },
        "transitions": [],
    }


def _write_files_with_roles(
    case_root: Path,
    *,
    case_id: str,
    fixed_roles: dict[str, str],
) -> None:
    (case_root / "REPORT.md").write_text("# H4\n", encoding="utf-8")
    entries: list[dict[str, Any]] = []
    for index, artifact in enumerate(
        sorted(
            path
            for path in case_root.rglob("*")
            if path.is_file() and path.name != "FILES.json"
        ),
        start=1,
    ):
        relative = artifact.relative_to(case_root).as_posix()
        entries.append(
            {
                "path": relative,
                "role": fixed_roles.get(
                    relative,
                    (
                        "proof_report"
                        if relative == "REPORT.md"
                        else f"retained-artifact-{index:04d}"
                    ),
                ),
                "sha256": "sha256:"
                + hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "size_bytes": artifact.stat().st_size,
            }
        )
    _write_json(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
            "case_id": case_id,
            "files": entries,
        },
    )


def test_r1_case_files_hashes_the_declared_report_and_rejects_tamper(
    tmp_path: Path,
) -> None:
    case_root = tmp_path / "case"
    case_root.mkdir()
    _write_json(case_root / "terminal.json", {"case_id": "H4"})
    _write_files_with_roles(
        case_root,
        case_id="H4",
        fixed_roles={"terminal.json": "proof_terminal_record"},
    )

    count, roles = proof_validator._validate_r1_case_files(
        case_id="H4",
        case_root=case_root,
        files_path=case_root / "FILES.json",
        report_path=case_root / "REPORT.md",
    )
    assert count == 2
    assert roles["proof_report"] == (case_root / "REPORT.md").resolve()

    (case_root / "REPORT.md").write_text("# forged\n", encoding="utf-8")
    with pytest.raises(ValueError, match="proof.artifact.(size|sha256):REPORT.md"):
        proof_validator._validate_r1_case_files(
            case_id="H4",
            case_root=case_root,
            files_path=case_root / "FILES.json",
            report_path=case_root / "REPORT.md",
        )


def test_r1_case_files_rejects_a_declared_report_outside_files_hash_coverage(
    tmp_path: Path,
) -> None:
    case_root = tmp_path / "case"
    case_root.mkdir()
    report = case_root / "REPORT.md"
    report.write_text("# H4\n", encoding="utf-8")
    _write_json(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
            "case_id": "H4",
            "files": [
                {
                    "path": "terminal.json",
                    "role": "proof_terminal_record",
                    "sha256": "sha256:"
                    + hashlib.sha256(b'{\"case_id\":\"H4\"}\\n').hexdigest(),
                    "size_bytes": len(b'{\"case_id\":\"H4\"}\\n'),
                }
            ],
        },
    )
    (case_root / "terminal.json").write_bytes(b'{\"case_id\":\"H4\"}\\n')

    with pytest.raises(ValueError, match="proof.files.report_role"):
        proof_validator._validate_r1_case_files(
            case_id="H4",
            case_root=case_root,
            files_path=case_root / "FILES.json",
            report_path=report,
        )


def test_r1_declared_core_artifacts_must_match_the_case_local_files_role(
    tmp_path: Path,
) -> None:
    case_root = tmp_path / "case"
    source = case_root / "source.ifc"
    source.parent.mkdir()
    source.write_bytes(b"source")
    roles = {"repair_input_ifc": source}

    assert proof_validator._require_r1_declared_artifact(
        case_root=case_root,
        declared_path=source,
        roles=roles,
        role="repair_input_ifc",
    ) == source.resolve()

    foreign = tmp_path / "other-case" / "source.ifc"
    foreign.parent.mkdir()
    foreign.write_bytes(b"foreign")
    with pytest.raises(ValueError, match="proof.files.declared_artifact"):
        proof_validator._require_r1_declared_artifact(
            case_root=case_root,
            declared_path=foreign,
            roles=roles,
            role="repair_input_ifc",
        )
    with pytest.raises(ValueError, match="proof.files.declared_artifact"):
        proof_validator._require_r1_declared_artifact(
            case_root=case_root,
            declared_path=source,
            roles={"retained-artifact-0001": source},
            role="repair_input_ifc",
        )


def test_r1_m1_frozen_model_request_resume_and_effective_hash_are_authoritative(
    tmp_path: Path,
) -> None:
    frozen_case, model = proof_validator._r1_frozen_case_authority("M1")
    source = proof_validator.R1_CANONICAL_FREEZE.parents[3] / str(model["path"])
    initial = tmp_path / "initial-request.txt"
    answer = tmp_path / "clarification-answer.txt"
    effective = tmp_path / "request.txt"
    initial.write_text(str(frozen_case["request"]), encoding="utf-8")
    answer.write_text(str(frozen_case["resume"]), encoding="utf-8")
    effective_text = (
        f"{frozen_case['request']}\n补充说明：{str(frozen_case['resume']).strip()}"
    )
    effective.write_text(effective_text, encoding="utf-8")
    authority = proof_validator._audit_r1_frozen_case_authority(
        case_id="M1",
        terminal={
            "source": {
                "sha256_before": "sha256:" + str(model["sha256"]),
                "sha256_after": "sha256:" + str(model["sha256"]),
                "unchanged": True,
            }
        },
        source_ifc_path=source,
        roles={
            "initial_user_request": initial,
            "clarification_answer": answer,
            "user_request": effective,
        },
    )
    assert authority["initial_hash"] == "sha256:" + str(frozen_case["request_sha256"])
    assert authority["effective_hash"] == "sha256:" + hashlib.sha256(
        effective_text.encode("utf-8")
    ).hexdigest()
    proof_validator._audit_r1_request_hash_lineage(
        authority=authority,
        state={"request_hash": authority["initial_hash"]},
        initial_intent={"source_request_hash": authority["initial_hash"]},
        final_intent={"source_request_hash": authority["effective_hash"]},
        changeset={"source_request_hash": authority["effective_hash"]},
        boundary={"request_sha256": authority["effective_hash"]},
    )

    answer.write_text("改为 EI30。", encoding="utf-8")
    with pytest.raises(ValueError, match="proof.case_authority.resume"):
        proof_validator._audit_r1_frozen_case_authority(
            case_id="M1",
            terminal={
                "source": {
                    "sha256_before": "sha256:" + str(model["sha256"]),
                    "sha256_after": "sha256:" + str(model["sha256"]),
                    "unchanged": True,
                }
            },
            source_ifc_path=source,
            roles={
                "initial_user_request": initial,
                "clarification_answer": answer,
                "user_request": effective,
            },
        )


def test_r1_request_lineage_rejects_spliced_effective_intent() -> None:
    initial = "sha256:" + "1" * 64
    effective = "sha256:" + "2" * 64
    with pytest.raises(ValueError, match="proof.case_authority.request_lineage"):
        proof_validator._audit_r1_request_hash_lineage(
            authority={"initial_hash": initial, "effective_hash": effective},
            state={"request_hash": initial},
            initial_intent={"source_request_hash": initial},
            final_intent={"source_request_hash": initial},
            changeset={"source_request_hash": effective},
            boundary={"request_sha256": effective},
        )


def _mixed_changeset() -> tuple[str, dict[str, Any]]:
    request = "Add a beam and set the target window fire rating to EI60."
    changeset = deepcopy(_changeset(request=request, parameters=_parameters()))
    property_operation = _property_operation(
        operation_id="h1-window-fire-rating",
        target_id=WINDOW_ID,
        set_name="Pset_WindowCommon",
        property_name="FireRating",
        value_type="IfcLabel",
        value="EI60",
    )
    changeset["changeset_id"] = "changeset-r1-h1-mixed"
    changeset["source_request_hash"] = "sha256:" + hashlib.sha256(
        request.encode("utf-8")
    ).hexdigest()
    changeset["scope"]["target_ids"].append(WINDOW_ID)
    changeset["evidence_refs"].extend(property_operation["evidence_refs"])
    changeset["postconditions"].append("requested_properties_match")
    changeset["operations"].append(property_operation)
    return request, changeset


def _apply_mixed_delta(
    tmp_path: Path,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    # Proof-unit fixture only: this composes the final model delta produced by
    # both registered applicators. It is not public-executor/atomic admission.
    request, combined_changeset = _mixed_changeset()
    beam_changeset = deepcopy(combined_changeset)
    beam_changeset["operations"] = [beam_changeset["operations"][0]]
    beam_changeset["scope"]["target_ids"] = [
        beam_changeset["scope"]["target_ids"][0]
    ]
    beam_changeset["evidence_refs"] = list(
        beam_changeset["operations"][0]["evidence_refs"]
    )
    intermediate = tmp_path / "beam-only.ifc"
    beam_application = apply_changeset(
        damaged_ifc_path=D7N,
        repair_request=request,
        changeset=beam_changeset,
        output_path=intermediate,
        registry=create_default_registry(),
    )
    assert beam_application["valid"] is True, beam_application
    assert beam_application["published"] is True, beam_application

    property_request = "Set Pset_WindowCommon.FireRating to EI60."
    property_operation = deepcopy(combined_changeset["operations"][1])
    property_changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.2",
        "changeset_id": "changeset-r1-h1-property-step",
        "binding_status": "bound",
        "base_model_fingerprint": "sha256:"
        + hashlib.sha256(intermediate.read_bytes()).hexdigest(),
        "source_request_hash": "sha256:"
        + hashlib.sha256(property_request.encode("utf-8")).hexdigest(),
        "scope": {"target_ids": [WINDOW_ID], "forbidden_ids": []},
        "evidence_refs": list(property_operation["evidence_refs"]),
        "preconditions": ["target_exists"],
        "postconditions": ["requested_properties_match"],
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "operations": [property_operation],
    }
    repaired = tmp_path / "mixed.ifc"
    property_application = apply_changeset(
        damaged_ifc_path=intermediate,
        repair_request=property_request,
        changeset=property_changeset,
        output_path=repaired,
        registry=create_default_registry(),
    )
    assert property_application["valid"] is True, property_application
    assert property_application["published"] is True, property_application
    combined_application = deepcopy(beam_application)
    combined_application["operations"] = [
        *beam_application["operations"],
        *property_application["operations"],
    ]
    combined_application["output"] = repaired.as_posix()
    return repaired, combined_changeset, combined_application


def test_r1_synthetic_final_model_mixed_preservation_uses_all_operations(
    tmp_path: Path,
) -> None:
    repaired, changeset, application = _apply_mixed_delta(tmp_path)
    source_model = ifcopenshell.open(str(D7N))
    repaired_model = ifcopenshell.open(str(repaired))

    proof_validator._audit_authorized_repair_preservation(
        damaged_ifc_path=D7N,
        repaired_ifc_path=repaired,
        changeset=changeset,
        application=application,
        damaged_model=source_model,
        repaired_model=repaired_model,
    )


def test_r1_property_only_global_preservation_rejects_unrelated_root_tamper(
    tmp_path: Path,
) -> None:
    source, repaired, changeset, application = _apply_property_case(
        tmp_path,
        ifc_class="IfcWindow",
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value_type="IfcBoolean",
        value=True,
    )
    tampered = ifcopenshell.open(str(repaired))
    tampered.by_type("IfcWindow")[0].Name = "UNAUTHORIZED WINDOW NAME"
    tampered.write(str(repaired))

    with pytest.raises(ValueError, match="proof.global_preservation"):
        proof_validator._audit_authorized_repair_preservation(
            damaged_ifc_path=source,
            repaired_ifc_path=repaired,
            changeset=changeset,
            application=application,
            damaged_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired)),
        )


def test_r1_exact_operation_set_rejects_extra_same_changeset_operation() -> None:
    _, changeset = _mixed_changeset()
    profile = {
        "artifact_predicates": [
            {
                "predicate_id": "H1-atomic",
                "kind": "atomic_operation_set",
                "operation_types": [
                    "add_beam",
                    "set_occurrence_properties",
                ],
            }
        ]
    }
    proof_validator._audit_r1_exact_operation_set(
        changeset=changeset,
        profile=profile,
    )

    changeset["operations"].append(
        _property_operation(
            operation_id="unauthorized-extra-property",
            target_id=WINDOW_ID,
            set_name="Pset_WindowCommon",
            property_name="IsExternal",
            value_type="IfcBoolean",
            value=False,
        )
    )
    with pytest.raises(ValueError, match="proof.changeset.operation_set"):
        proof_validator._audit_r1_exact_operation_set(
            changeset=changeset,
            profile=profile,
        )


def test_r1_profile_binding_rejects_self_signed_noncanonical_profile(
    tmp_path: Path,
) -> None:
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text("{}\n", encoding="utf-8")
    profile_path = tmp_path / "profiles.json"
    profiles = {
        "schema_version": "text2ifc/ifc-repair-proof-profiles/0.1",
        "provenance_namespace": "repair-milestone-r1",
        "freeze": {
            "path": "freeze.json",
            "sha256": "sha256:"
            + hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
        },
        "execution_order": ["forged-case"],
        "cases": [
            {
                "profile_id": "r1-forged-case",
                "case_id": "forged-case",
                "provenance_namespace": "repair-milestone-r1",
                "terminal_class": "SUCCESS",
                "artifact_predicates": [],
            }
        ],
    }
    profile_path.write_text(
        json.dumps(profiles, indent=2) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="proof.profile.authoritative_profile"):
        proof_validator._validate_r1_profile_freeze(profile_path, profiles)


def test_r1_profile_binding_accepts_byte_exact_canonical_profile_copy(
    tmp_path: Path,
) -> None:
    profile_path = tmp_path / proof_validator.R1_CANONICAL_PROFILE.name
    freeze_path = tmp_path / proof_validator.R1_CANONICAL_FREEZE.name
    shutil.copy2(proof_validator.R1_CANONICAL_PROFILE, profile_path)
    shutil.copy2(proof_validator.R1_CANONICAL_FREEZE, freeze_path)
    profiles = json.loads(profile_path.read_text(encoding="utf-8"))

    proof_validator._validate_r1_profile_freeze(profile_path, profiles)


def test_r1_h3_replays_initial_ambiguity_and_compares_stable_identity_set(
    tmp_path: Path,
) -> None:
    result = proof_validator._audit_r1_initial_target_resolution_replay(
        source_ifc_path=H3_SOURCE,
        initial_intent=_h3_initial_intent(),
        retained_offered_identities=tuple(reversed(H3_OFFERED)),
        selected_identity=H3_SELECTED,
        expected_selected_identity=H3_SELECTED,
        scratch_root=tmp_path,
    )

    assert result["status"] == "clarification_required"
    assert result["reason_code"] == "ambiguous"
    assert set(result["offered_identities"]) == set(H3_OFFERED)


def test_r1_h3_replay_rejects_selected_identity_outside_current_offered_set(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="proof.h3.selected_identity"):
        proof_validator._audit_r1_initial_target_resolution_replay(
            source_ifc_path=H3_SOURCE,
            initial_intent=_h3_initial_intent(),
            retained_offered_identities=H3_OFFERED,
            selected_identity="IfcWindow:not-currently-offered",
            expected_selected_identity=H3_SELECTED,
            scratch_root=tmp_path,
        )


def test_r1_h3_state_selection_binds_dynamic_token_to_stable_identity() -> None:
    candidates = [
        {
            "token": f"candidate:{index}",
            "public_id": identity.split(":", 1)[1],
            "ifc_class": "IfcWindow",
        }
        for index, identity in enumerate(reversed(H3_OFFERED), start=1)
    ]
    selected_token = next(
        item["token"]
        for item in candidates
        if proof_validator._stable_target_identity(item) == H3_SELECTED
    )
    state = {
        "run_id": "repair-r1-h3",
        "stage": "succeeded",
        "transitions": [
            {
                "from_stage": "intent_ready",
                "to_stage": "clarification_required",
                "reason_code": "ambiguous_target",
                "clarification": {
                    "reason_code": "ambiguous_target",
                    "candidates": candidates,
                },
                "answer": None,
            },
            {
                "from_stage": "clarification_required",
                "to_stage": "intent_ready",
                "reason_code": None,
                "clarification": None,
                "answer": {
                    "kind": "select_candidate",
                    "candidate_token": selected_token,
                },
            },
            {
                "from_stage": "changeset_ready",
                "to_stage": "succeeded",
                "reason_code": None,
                "clarification": None,
                "answer": None,
            },
        ],
    }

    lineage = proof_validator._audit_r1_h3_state_selection(
        state=state,
        expected_selected_identity=H3_SELECTED,
    )

    assert set(lineage["offered_identities"]) == set(H3_OFFERED)
    assert lineage["selected_identity"] == H3_SELECTED

    tampered = deepcopy(state)
    tampered["transitions"][0]["result_artifacts"] = {
        "successful_ifc": "published/forged.ifc"
    }
    with pytest.raises(ValueError, match="proof.h3.pre_mutation"):
        proof_validator._audit_r1_h3_state_selection(
            state=tampered,
            expected_selected_identity=H3_SELECTED,
        )


def test_r1_m1_resume_claim_id_is_derived_from_state_generation() -> None:
    state = {
        "stage": "succeeded",
        "transitions": [
            {
                "from_stage": "clarification_required",
                "to_stage": "intent_ready",
                "answer": {"kind": "add_detail", "detail": "Use EI60."},
                "stage_payload": {"property_resolution_generation": 12},
            }
        ],
    }

    assert proof_validator._r1_effective_property_claim_id(
        state=state,
        base_claim_id="claim-001",
    ) == "claim-001-resume-012"


def test_r1_bound_artifact_requires_a_hash_verified_transition_binding(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    from tests.ifc_repair.test_repair_milestone_r1_proof import _source_model

    _source_model(source, "IfcBeam")
    store = RunStore(tmp_path / "runtime")
    state = store.start_run(
        source_path=source,
        request_id="r1-H4",
        request_text="unsupported program",
        run_id="repair-r1-bound-artifact",
    )
    run_root = tmp_path / "runtime" / "runs" / state.run_id
    intent_path = run_root / "intent" / "repair-intent.json"
    _write_json(intent_path, _h4_intent())
    binding = store.artifact_binding(
        state.run_id,
        "intent/repair-intent.json",
        "text2ifc/ifc-repair-intent/0.8",
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=state.state_version,
        stage_payload={"ifc_schema": "IFC2X3"},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.INDEX_READY,
        expected_state_version=state.state_version,
        stage_payload={"index": "fixture"},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.INTENT_READY,
        expected_state_version=state.state_version,
        stage_payload={"intent": binding},
    )

    resolved = proof_validator._r1_bound_transition_artifact(
        state=state,
        state_path=run_root / "state.json",
        artifact_key="intent",
        listed_paths=(intent_path,),
        before_transition_id=None,
        require_unique=True,
    )

    assert resolved == intent_path.resolve()


def _r1_success_terminal_fixture(
    tmp_path: Path,
) -> tuple[dict[str, Any], Path, dict[str, Path], Path, dict[str, Any]]:
    run_root = tmp_path / "run"
    repaired = run_root / "published" / "successful" / "repaired.ifc"
    repaired.parent.mkdir(parents=True)
    shutil.copy2(D7N, repaired)
    evaluation = run_root / "published" / "evaluation" / "public-evaluation.json"
    evidence = run_root / "published" / "terminal" / "evidence.json"
    application_path = run_root / "application.json"
    application = {"valid": True, "published": True, "operations": []}
    _write_json(
        evaluation,
        {
            "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
            "complete_repair_success": True,
            "successful_artifact_publishable": True,
        },
    )
    _write_json(
        evidence,
        {"terminal_status": "succeeded", "evidence": {"application": application}},
    )
    _write_json(application_path, application)

    def _entry(path: Path, role: str) -> dict[str, Any]:
        return {
            "path": path.relative_to(run_root).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "size_bytes": path.stat().st_size,
            "role": role,
        }

    manifest = run_root / "published" / "manifest.json"
    _write_json(
        manifest,
        {
            "schema_version": "text2ifc/ifc-repair-artifact-manifest/0.1",
            "artifacts": [
                _entry(evaluation, "public_evaluation"),
                _entry(evidence, "public_evidence"),
                _entry(repaired, "successful_ifc"),
            ],
        },
    )
    result_artifacts = {
        "manifest": manifest.relative_to(run_root).as_posix(),
        "successful_ifc": repaired.relative_to(run_root).as_posix(),
        "evaluation": evaluation.relative_to(run_root).as_posix(),
    }
    state = {
        "stage": "succeeded",
        "reason_code": None,
        "result_artifacts": dict(result_artifacts),
        "transitions": [
            {
                "to_stage": "succeeded",
                "reason_code": None,
                "stage_payload": {"status": "succeeded"},
                "result_artifacts": dict(result_artifacts),
            }
        ],
    }
    state_path = run_root / "state.json"
    _write_json(state_path, state)
    roles = {
        "runtime_state": state_path,
        "published_repair_output": repaired,
        "production_publication_manifest": manifest,
        "production_evaluation": evaluation,
        "production_publication_evidence": evidence,
        "application_result": application_path,
    }
    return state, state_path, roles, repaired, application


@pytest.mark.parametrize(
    "tamper",
    (
        "state_not_succeeded",
        "successful_ifc_drift",
        "evaluation_unlisted",
        "manifest_hash_drift",
        "application_drift",
    ),
)
def test_r1_success_terminal_binding_is_state_and_manifest_authoritative(
    tmp_path: Path,
    tamper: str,
) -> None:
    state, state_path, roles, repaired, application = (
        _r1_success_terminal_fixture(tmp_path)
    )
    if tamper == "state_not_succeeded":
        state["stage"] = "evaluated"
    elif tamper == "successful_ifc_drift":
        state["result_artifacts"]["successful_ifc"] = "foreign.ifc"
        state["transitions"][-1]["result_artifacts"] = dict(
            state["result_artifacts"]
        )
    elif tamper == "evaluation_unlisted":
        roles.pop("production_evaluation")
    elif tamper == "manifest_hash_drift":
        manifest = proof_validator._read_json(
            roles["production_publication_manifest"]
        )
        manifest["artifacts"][0]["sha256"] = "0" * 64
        _write_json(roles["production_publication_manifest"], manifest)
    else:
        evidence = proof_validator._read_json(
            roles["production_publication_evidence"]
        )
        evidence["evidence"]["application"]["published"] = False
        _write_json(roles["production_publication_evidence"], evidence)

    with pytest.raises(ValueError, match="proof.success.terminal_publication"):
        proof_validator._audit_r1_success_terminal_binding(
            state=state,
            state_path=state_path,
            roles=roles,
            repaired_ifc_path=repaired,
            application=application,
        )


def test_r1_success_terminal_binding_accepts_exact_publication_chain(
    tmp_path: Path,
) -> None:
    state, state_path, roles, repaired, application = (
        _r1_success_terminal_fixture(tmp_path)
    )

    proof_validator._audit_r1_success_terminal_binding(
        state=state,
        state_path=state_path,
        roles=roles,
        repaired_ifc_path=repaired,
        application=application,
    )


def test_r1_h4_replays_unsupported_atomic_guard_from_intent_and_state() -> None:
    result = proof_validator._audit_r1_unsupported_guard_replay(
        intent=_h4_intent(),
        state=_h4_state(),
        expected_supported_capabilities=("add_beam",),
        expected_unsupported_capabilities=("structural_analysis_node",),
        expected_reason_code="STRUCTURAL_ANALYSIS_UNSUPPORTED",
        attempts=({"stage": "stage1"},),
    )

    assert result["supported_capabilities"] == ["add_beam"]
    assert result["unsupported_capabilities"] == ["structural_analysis_node"]
    assert result["stage2_attempts"] == 0
    assert result["published_outputs"] == []


def test_r1_h4_replay_rejects_terminal_claim_without_stage1_unsupported_evidence() -> None:
    intent = _h4_intent()
    intent["unsupported_requests"] = []
    with pytest.raises(ValueError, match="proof.h4.unsupported_request"):
        proof_validator._audit_r1_unsupported_guard_replay(
            intent=intent,
            state=_h4_state(),
            expected_supported_capabilities=("add_beam",),
            expected_unsupported_capabilities=("structural_analysis_node",),
            expected_reason_code="STRUCTURAL_ANALYSIS_UNSUPPORTED",
            attempts=({"stage": "stage1"},),
        )


def test_r1_h4_replay_rejects_stage2_or_successful_ifc_leakage() -> None:
    with pytest.raises(ValueError, match="proof.h4.pre_mutation"):
        proof_validator._audit_r1_unsupported_guard_replay(
            intent=_h4_intent(),
            state=_h4_state(leak_stage2=True),
            expected_supported_capabilities=("add_beam",),
            expected_unsupported_capabilities=("structural_analysis_node",),
            expected_reason_code="STRUCTURAL_ANALYSIS_UNSUPPORTED",
            attempts=({"stage": "stage1"},),
        )


def test_r1_validate_case_h4_rejects_unbound_stage1_intent_role(
    tmp_path: Path,
) -> None:
    case_root = tmp_path / "case"
    source = case_root / "source.ifc"
    frozen_case, frozen_model = proof_validator._r1_frozen_case_authority("H4")
    source.parent.mkdir(parents=True)
    shutil.copy2(
        proof_validator.R1_CANONICAL_FREEZE.parents[3] / str(frozen_model["path"]),
        source,
    )
    request = str(frozen_case["request"])
    (case_root / "request.txt").write_text(request, encoding="utf-8")
    store = RunStore(case_root / "runtime")
    state = store.start_run(
        source_path=source,
        request_id="r1-H4",
        request_text=request,
        run_id="repair-r1-h4",
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.SOURCE_VALIDATED,
        expected_state_version=state.state_version,
        stage_payload={"ifc_schema": "IFC2X3"},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.INDEX_READY,
        expected_state_version=state.state_version,
        stage_payload={"index": "fixture"},
    )
    state = store.transition(
        state.run_id,
        to_stage=RunStage.UNSUPPORTED,
        expected_state_version=state.state_version,
        reason_code="STRUCTURAL_ANALYSIS_UNSUPPORTED",
        stage_payload={"reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED"},
    )
    _write_json(case_root / "intent.json", _h4_intent())
    _write_json(
        case_root / "case-result.json",
        {
            "case_id": "H4",
            "attempts": [{"stage": "stage1"}],
            "synthetic_fallback_used": False,
            "private_evidence_detected": False,
        },
    )
    digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    _write_json(
        case_root / "terminal.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-terminal/0.1",
            "case_id": "H4",
            "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
            "source": {
                "path": "source.ifc",
                "sha256_before": digest,
                "sha256_after": digest,
                "unchanged": True,
            },
            "initial_stop": {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
                "stage2_attempts": 0,
                "apply_attempts": 0,
                "published_outputs": [],
                "supported_capabilities": ["add_beam"],
                "unsupported_capabilities": ["structural_analysis_node"],
                "atomic_request": True,
            },
            "resume_success": False,
        },
    )
    state_relative = (
        Path("runtime/runs") / state.run_id / "state.json"
    ).as_posix()
    _write_files_with_roles(
        case_root,
        case_id="H4",
        fixed_roles={
            "source.ifc": "repair_input_ifc",
                "request.txt": "user_request",
            "intent.json": "stage1_repair_intent",
            "case-result.json": "live_provider_case_result",
            state_relative: "runtime_state",
            "terminal.json": "proof_terminal_record",
        },
    )
    profile_document = json.loads(
        proof_validator.R1_CANONICAL_PROFILE.read_text(encoding="utf-8")
    )
    profile = next(item for item in profile_document["cases"] if item["case_id"] == "H4")

    with pytest.raises(
        ValueError,
        match="proof.runtime_state.artifact_binding:intent",
    ):
        proof_validator._validate_r1_case(
            root=tmp_path,
            case={
                "case_id": "H4",
                "case_root": "case",
                "files": "case/FILES.json",
                "report": "case/REPORT.md",
                "terminal_record": "case/terminal.json",
                "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
            },
            profile=profile,
            provenance_namespace="repair-milestone-r1",
        )


def test_r1_live_provenance_binds_stage1_stage15_stage2_and_boundary(
    tmp_path: Path,
) -> None:
    roles, intent, changeset = _r1_live_provenance_fixture(tmp_path)

    result = proof_validator._audit_r1_live_provider_provenance(
        case_id="E1",
        roles=roles,
        provider_intent=intent,
        changeset=changeset,
        damaged_sha256="sha256:" + "9" * 64,
        validated_state=_r1_live_success_state(),
    )

    assert result["attempt_count"] == 3
    assert result["transport_calls_by_stage"] == {
        "stage1": 1,
        "property_resolution": 1,
        "stage2": 1,
    }


def test_r1_stage1_rounds_bind_initial_and_effective_intents_separately() -> None:
    initial_intent = _h3_initial_intent()
    effective_intent = deepcopy(initial_intent)
    effective_intent["operations"][0]["property_intents"][0].update(
        {"property_phrase": "防火等级", "raw_value": "EI60"}
    )

    def _stage1_document(intent: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "operations": deepcopy(intent["operations"]),
            "unsupported_requests": deepcopy(intent["unsupported_requests"]),
            "semantic_bundles": deepcopy(intent["semantic_bundles"]),
            "provenance": deepcopy(intent["provenance"]),
        }

    initial_attempt = {
        "lineage": "initial",
        "stage": "stage1",
        "response": {"content": _stage1_document(initial_intent)},
    }
    resume_attempt = {
        "lineage": "clarification-resume",
        "stage": "stage1",
        "response": {"content": _stage1_document(effective_intent)},
    }
    attempts = [initial_attempt, resume_attempt]

    proof_validator._audit_r1_stage1_round_bindings(
        attempts=attempts,
        response_document=lambda item: item["response"]["content"],
        expected_intents_by_lineage={
            "initial": initial_intent,
            "clarification-resume": effective_intent,
        },
    )

    initial_attempt["response"]["content"] = _stage1_document(effective_intent)
    with pytest.raises(ValueError, match="proof.live.stage1_binding"):
        proof_validator._audit_r1_stage1_round_bindings(
            attempts=attempts,
            response_document=lambda item: item["response"]["content"],
            expected_intents_by_lineage={
                "initial": initial_intent,
                "clarification-resume": effective_intent,
            },
        )
    initial_attempt["response"]["content"] = _stage1_document(initial_intent)
    resume_attempt["response"]["content"] = _stage1_document(initial_intent)
    with pytest.raises(ValueError, match="proof.live.stage1_binding"):
        proof_validator._audit_r1_stage1_round_bindings(
            attempts=attempts,
            response_document=lambda item: item["response"]["content"],
            expected_intents_by_lineage={
                "initial": initial_intent,
                "clarification-resume": effective_intent,
            },
        )


@pytest.mark.parametrize(
    ("tamper", "error"),
    [
        ("property_parsed", "proof.live.property_attempt_status"),
        ("property_prompt", "proof.live.property_attempt_binding"),
        ("property_transport", "proof.live.property_attempt_binding"),
        ("stage1_response", "proof.live.stage1_binding"),
        ("stage2_response", "proof.live.stage2_binding"),
        ("fallback", "proof.live.attempts"),
        ("private_attempt", "proof.live.attempts"),
        ("private_canary", "proof.live.private_canary"),
        ("production_boundary", "proof.live.production_input_boundary"),
    ],
)
def test_r1_live_provenance_rejects_cross_stage_or_isolation_tamper(
    tmp_path: Path,
    tamper: str,
    error: str,
) -> None:
    roles, intent, changeset = _r1_live_provenance_fixture(tmp_path)
    if tamper == "property_parsed":
        _write_json(
            roles["property_parsed_response"],
            {
                "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
                "decision": "unsupported",
                "selected_candidate_id": None,
                "conflicting_candidate_ids": [],
                "clarification_question": None,
            },
        )
    elif tamper == "property_prompt":
        roles["property_rendered_prompt"].write_text(
            "different offered candidate set",
            encoding="utf-8",
        )
    elif tamper == "property_transport":
        raw_response = proof_validator._read_json(
            roles["property_raw_response"]
        )
        raw_response["transport"]["request"] = {"model": "unbound"}
        _write_json(roles["property_raw_response"], raw_response)
    elif tamper in {
        "stage1_response",
        "stage2_response",
        "fallback",
        "private_attempt",
    }:
        case_result = proof_validator._read_json(
            roles["live_provider_case_result"]
        )
        stage = "stage1" if tamper != "stage2_response" else "stage2"
        attempt = next(
            item for item in case_result["attempts"] if item["stage"] == stage
        )
        if tamper in {"stage1_response", "stage2_response"}:
            attempt["response"]["content"] = {"operations": []}
            attempt["response_sha256"] = _canonical_json_sha256(
                attempt["response"]
            )
        elif tamper == "fallback":
            attempt["fallback_flags"]["synthetic"] = True
        else:
            attempt["private_evidence_detected"] = True
        _write_json(roles["live_provider_case_result"], case_result)
        live_result = proof_validator._read_json(roles["live_provider_result"])
        live_result["cases"] = [case_result]
        _write_json(roles["live_provider_result"], live_result)
    elif tamper == "private_canary":
        draft = proof_validator._read_json(roles["live_provider_draft"])
        draft["diagnostic_note"] = "private-gold"
        _write_json(roles["live_provider_draft"], draft)
    else:
        boundary = proof_validator._read_json(
            roles["production_input_boundary"]
        )
        boundary["original_ifc_supplied"] = True
        _write_json(roles["production_input_boundary"], boundary)

    with pytest.raises(ValueError, match=error):
        proof_validator._audit_r1_live_provider_provenance(
            case_id="E1",
            roles=roles,
            provider_intent=intent,
            changeset=changeset,
            damaged_sha256="sha256:" + "9" * 64,
            validated_state=_r1_live_success_state(),
        )


def test_r1_h4_live_provenance_binds_unsupported_stage1_and_forbids_later_calls(
    tmp_path: Path,
) -> None:
    roles, _intent, _changeset = _r1_live_provenance_fixture(tmp_path)
    intent = _h4_intent()
    stage1_document = {
        "operations": intent["operations"],
        "unsupported_requests": intent["unsupported_requests"],
        "semantic_bundles": intent["semantic_bundles"],
        "provenance": intent["provenance"],
    }
    stage1 = _r1_live_attempt(
        case_id="H4",
        stage="stage1",
        parent_attempt_id=None,
        response_document=stage1_document,
    )
    h4_state = _h4_state()
    h4_state.update(
        {"run_id": "repair-r1-h4", "state_version": 3}
    )
    case_result = {
        "case_id": "H4",
        "final": {
            "run_id": h4_state["run_id"],
            "state_version": h4_state["state_version"],
            "status": h4_state["stage"],
            "reason_code": h4_state["reason_code"],
            "complete_repair_success": False,
            "successful_artifact_publishable": False,
            "artifacts": deepcopy(h4_state["result_artifacts"]),
        },
        "attempts": [stage1],
        "synthetic_fallback_used": False,
        "private_evidence_detected": False,
    }
    live_result = proof_validator._read_json(roles["live_provider_result"])
    live_result["cases"] = [case_result]
    _write_json(roles["live_provider_result"], live_result)
    _write_json(roles["live_provider_case_result"], case_result)
    boundary = proof_validator._read_json(roles["production_input_boundary"])
    boundary["request_sha256"] = intent["source_request_hash"]
    boundary["resolved_target_count"] = 0
    _write_json(roles["production_input_boundary"], boundary)

    proof_validator._audit_r1_live_provider_provenance(
        case_id="H4",
        roles=roles,
        provider_intent=intent,
        changeset=None,
        damaged_sha256="sha256:" + "9" * 64,
        validated_state=h4_state,
    )

    stage1["response"]["content"]["unsupported_requests"] = []
    stage1["response_sha256"] = _canonical_json_sha256(stage1["response"])
    _write_json(roles["live_provider_case_result"], case_result)
    live_result["cases"] = [case_result]
    _write_json(roles["live_provider_result"], live_result)
    with pytest.raises(ValueError, match="proof.live.stage1_binding"):
        proof_validator._audit_r1_live_provider_provenance(
            case_id="H4",
            roles=roles,
            provider_intent=intent,
            changeset=None,
            damaged_sha256="sha256:" + "9" * 64,
            validated_state=h4_state,
        )


def test_r1_stage15_attempt_binding_preserves_invalid_then_valid_retry(
    tmp_path: Path,
) -> None:
    roles, _intent, _changeset = _r1_live_provenance_fixture(tmp_path)
    case_result = proof_validator._read_json(roles["live_provider_case_result"])
    valid = deepcopy(
        next(
            item
            for item in case_result["attempts"]
            if item["stage"] == "property_resolution"
        )
    )
    invalid = deepcopy(valid)
    invalid["response"]["content"] = '{"decision":'
    invalid["response"]["id"] = "response-r1-e1-invalid"
    invalid["metadata"]["response_id"] = "response-r1-e1-invalid"
    invalid["response_sha256"] = _canonical_json_sha256(invalid["response"])
    valid["attempt_id"] = "E1:property_resolution:002"
    valid["parent_attempt_id"] = invalid["attempt_id"]
    valid["ordinal"] = 2
    valid["stage_attempt"] = 2
    valid["correction_reason"] = "JSON_DECODE_ERROR"
    valid["response"]["id"] = "response-r1-e1-valid"
    valid["metadata"]["response_id"] = "response-r1-e1-valid"
    valid["response_sha256"] = _canonical_json_sha256(valid["response"])

    first_root = roles["property_trace"].parent
    second_root = first_root.parent / "attempt-002"
    shutil.copytree(first_root, second_root)
    for index, path in enumerate(second_root.iterdir(), start=1):
        roles[f"property_retry_{index:02d}"] = path

    first_trace = proof_validator._read_json(first_root / "trace.json")
    first_trace.update(
        {
            "status": "invalid",
            "acceptance_eligible": False,
            "parse_status": "parse_error",
        }
    )
    _write_json(first_root / "trace.json", first_trace)
    _write_json(first_root / "parsed-response.json", None)
    _status, _parsed, first_feedback = proof_validator.ProviderOutput(
        text='{"decision":', metadata={}
    ).parse_json()
    _write_json(first_root / "validation-feedback.json", first_feedback)
    _write_json(first_root / "provider-metadata.json", invalid["metadata"])
    _write_json(
        first_root / "raw-response.json",
        {
            "text": '{"decision":',
            "transport": {
                "request": invalid["request"],
                "response": invalid["response"],
            },
        },
    )

    second_trace = proof_validator._read_json(second_root / "trace.json")
    second_trace.update({"attempt": 2, "parse_status": "ok"})
    _write_json(second_root / "trace.json", second_trace)
    _write_json(second_root / "provider-metadata.json", valid["metadata"])
    second_renderer = proof_validator._read_json(second_root / "renderer-input.json")
    second_renderer["PREVIOUS_VALIDATION_FEEDBACK"] = first_feedback
    _write_json(second_root / "renderer-input.json", second_renderer)
    second_prompt = str(
        render_prompt(
            template_id=proof_validator.PROPERTY_RESOLUTION_TEMPLATE_ID,
            inputs=second_renderer,
        )["text"]
    )
    (second_root / "rendered-prompt.txt").write_text(
        second_prompt,
        encoding="utf-8",
    )
    valid["request"]["messages"][0]["content"] = second_prompt
    valid["request_sha256"] = _canonical_json_sha256(valid["request"])
    _write_json(second_root / "validation-feedback.json", [])
    second_raw = proof_validator._read_json(second_root / "raw-response.json")
    second_raw["transport"] = {
        "request": valid["request"],
        "response": valid["response"],
    }
    _write_json(second_root / "raw-response.json", second_raw)

    proof_validator._audit_r1_stage15_attempt_binding(
        roles=roles,
        attempts=[invalid, valid],
        response_document=lambda item: item["response"]["content"],
        provider_intent=_intent,
        state={"transitions": []},
    )

    second_trace["claim_id"] = "claim-spliced"
    _write_json(second_root / "trace.json", second_trace)
    with pytest.raises(ValueError, match="proof.live.property_attempt_renderer"):
        proof_validator._audit_r1_stage15_attempt_binding(
            roles=roles,
            attempts=[invalid, valid],
            response_document=lambda item: item["response"]["content"],
            provider_intent=_intent,
            state={"transitions": []},
        )

    second_trace["claim_id"] = "claim-001"
    _write_json(second_root / "trace.json", second_trace)
    second_renderer["PROPERTY_QUERY"] = {"query_id": "query-spliced"}
    _write_json(second_root / "renderer-input.json", second_renderer)
    with pytest.raises(ValueError, match="proof.live.property_attempt_renderer"):
        proof_validator._audit_r1_stage15_attempt_binding(
            roles=roles,
            attempts=[invalid, valid],
            response_document=lambda item: item["response"]["content"],
            provider_intent=_intent,
            state={"transitions": []},
        )


def test_r1_stage15_attempt_binding_rejects_unbound_renderer_input(
    tmp_path: Path,
) -> None:
    roles, intent, _changeset = _r1_live_provenance_fixture(tmp_path)
    case_result = proof_validator._read_json(roles["live_provider_case_result"])
    attempt = next(
        item
        for item in case_result["attempts"]
        if item["stage"] == "property_resolution"
    )
    renderer = proof_validator._read_json(roles["property_renderer_input"])
    renderer["PROPERTY_QUERY"]["query_id"] = "query-spliced"
    _write_json(roles["property_renderer_input"], renderer)

    with pytest.raises(ValueError, match="proof.live.property_attempt_renderer"):
        proof_validator._audit_r1_stage15_attempt_binding(
            roles=roles,
            attempts=[attempt],
            response_document=lambda item: item["response"]["content"],
            provider_intent=intent,
            state={"transitions": []},
        )


def test_r1_stage15_attempt_binding_rejects_raw_text_transport_drift(
    tmp_path: Path,
) -> None:
    roles, intent, _changeset = _r1_live_provenance_fixture(tmp_path)
    case_result = proof_validator._read_json(roles["live_provider_case_result"])
    attempt = next(
        item
        for item in case_result["attempts"]
        if item["stage"] == "property_resolution"
    )
    decision = dict(attempt["response"].pop("content"))
    compact_text = json.dumps(
        decision,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    attempt["response"]["choices"] = [
        {"message": {"role": "assistant", "content": compact_text}}
    ]
    attempt["response_sha256"] = _canonical_json_sha256(attempt["response"])
    raw = proof_validator._read_json(roles["property_raw_response"])
    assert raw["text"] != compact_text
    raw["transport"]["response"] = attempt["response"]
    _write_json(roles["property_raw_response"], raw)

    with pytest.raises(ValueError, match="proof.live.property_attempt_raw_response"):
        proof_validator._audit_r1_stage15_attempt_binding(
            roles=roles,
            attempts=[attempt],
            response_document=lambda item: json.loads(
                item["response"]["choices"][0]["message"]["content"]
            ),
            provider_intent=intent,
            state={"transitions": []},
        )


def test_r1_stage15_single_attempt_must_be_independently_valid(
    tmp_path: Path,
) -> None:
    roles, intent, _changeset = _r1_live_provenance_fixture(tmp_path)
    case_result = proof_validator._read_json(roles["live_provider_case_result"])
    attempt = next(
        item
        for item in case_result["attempts"]
        if item["stage"] == "property_resolution"
    )
    decision = dict(attempt["response"]["content"])
    decision["selected_candidate_id"] = "candidate:not-offered"
    attempt["response"]["content"] = decision
    attempt["response_sha256"] = _canonical_json_sha256(attempt["response"])
    _write_json(roles["property_parsed_response"], decision)
    raw = proof_validator._read_json(roles["property_raw_response"])
    raw["text"] = json.dumps(decision, ensure_ascii=False)
    raw["transport"]["response"] = attempt["response"]
    _write_json(roles["property_raw_response"], raw)
    renderer = proof_validator._read_json(roles["property_renderer_input"])
    feedback = proof_validator._property_decision_issues(
        decision,
        schema=renderer["DECISION_SCHEMA"],
        offered_ids=frozenset(
            item["candidate_id"]
            for item in renderer["CANDIDATE_SET"]["candidates"]
        ),
    )
    _write_json(roles["property_validation_feedback"], feedback)

    with pytest.raises(ValueError, match="proof.live.property_attempt_status"):
        proof_validator._audit_r1_stage15_attempt_binding(
            roles=roles,
            attempts=[attempt],
            response_document=lambda item: item["response"]["content"],
            provider_intent=intent,
            state={"transitions": []},
        )


def test_r1_independent_proof_uses_frozen_comparison_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    diff_budgets: list[float] = []
    orphan_budgets: list[float] = []
    l1_budgets: list[float] = []

    def _diff(_before: Any, _after: Any, *, timeout_seconds: float) -> dict:
        diff_budgets.append(timeout_seconds)
        return {
            "changes": {"created": [], "modified": [], "removed": []},
        }

    def _orphan(_model: Any, *, timeout_seconds: float) -> dict:
        orphan_budgets.append(timeout_seconds)
        return {}

    def _l1(**kwargs: Any) -> SimpleNamespace:
        l1_budgets.append(kwargs["comparison_timeout_seconds"])
        return SimpleNamespace(
            status=EvaluationStatus.PASSED,
            checks=[],
        )

    monkeypatch.setattr(proof_validator, "profile_normalized_model_diff", _diff)
    monkeypatch.setattr(
        proof_validator,
        "unreachable_non_root_fingerprint_multiset",
        _orphan,
    )
    monkeypatch.setattr(proof_validator, "evaluate_independent_l1", _l1)

    proof_validator._audit_structural_preservation(
        changeset={"operations": []},
        damaged_model=object(),
        repaired_model=object(),
    )
    proof_validator._audit_authorized_repair_preservation(
        damaged_ifc_path="damaged.ifc",
        repaired_ifc_path="repaired.ifc",
        changeset={"operations": []},
        application={},
        damaged_model=object(),
        repaired_model=object(),
    )

    assert diff_budgets == [600.0]
    assert orphan_budgets == [600.0, 600.0]
    assert l1_budgets == [600.0]


def test_r1_m1_initial_replay_is_case_listed_and_uses_base_claim(
    tmp_path: Path,
) -> None:
    roles, intent, _changeset = _r1_live_provenance_fixture(tmp_path)
    claim_root = roles["property_trace"].parents[2]
    query = claim_root / "query.json"
    candidate_set = claim_root / "candidate-set.json"
    claim = claim_root / "claim.json"
    admission = claim_root / "admissibility-provider.json"
    _write_json(
        query,
        {
            "schema_version": "text2ifc/ifc-property-resolution-query/0.2",
            "run_id": "run-e1",
            "operation_id": "e1-window-property",
            "claim_id": "claim-001",
            "query_id": (
                "property-query:run-e1:e1-window-property:claim-001"
            ),
        },
    )
    _write_json(
        candidate_set,
        {
            "schema_version": "text2ifc/ifc-property-candidate-set/0.1",
            "candidate_set_id": (
                "property-candidates:run-e1:e1-window-property:claim-001"
            ),
            "query_id": (
                "property-query:run-e1:e1-window-property:claim-001"
            ),
        },
    )
    initial_claim = deepcopy(intent["operations"][0]["property_intents"][0])
    _write_json(claim, initial_claim)
    _write_json(
        admission,
        {
            "schema_version": "text2ifc/ifc-property-admissibility/0.1",
            "admissibility_id": (
                "property-admissibility:run-e1:e1-window-property:claim-001"
            ),
            "query_id": (
                "property-query:run-e1:e1-window-property:claim-001"
            ),
            "candidate_set_id": (
                "property-candidates:run-e1:e1-window-property:claim-001"
            ),
            "decision_id": (
                "property-decision:run-e1:e1-window-property:claim-001"
            ),
            "status": "clarification_required",
        },
    )
    roles.update(
        {
            "property_query": query,
            "property_candidate_set": candidate_set,
            "property_claim": claim,
            "property_initial_admission": admission,
        }
    )
    replay_paths = {
        "query": query,
        "candidate_set": candidate_set,
        "decision": roles["property_parsed_response"],
        "decision_trace": roles["property_trace"],
        "claim": claim,
        "retained_admission": admission,
    }
    trace_document = proof_validator._read_json(roles["property_trace"])
    trace_document["run_id"] = "run-e1"
    trace_document["query_id"] = proof_validator._read_json(query)["query_id"]
    trace_document["candidate_set_id"] = proof_validator._read_json(
        candidate_set
    )["candidate_set_id"]
    _write_json(roles["property_trace"], trace_document)
    state_path = claim_root.parents[2] / "state.json"
    decision_result = claim_root / "decision-result-initial.json"
    _write_json(
        decision_result,
        {
            "decision": proof_validator._read_json(
                roles["property_parsed_response"]
            ),
            "trace": proof_validator._read_json(roles["property_trace"]),
        },
    )
    _write_json(state_path, {"run_id": "run-e1"})
    roles.update(
        {
            "runtime_state_fixture": state_path,
            "property_decision_result": decision_result,
        }
    )

    def _ref(path: Path) -> dict[str, str]:
        document = proof_validator._read_json(path)
        reference = {
            "path": path.relative_to(state_path.parent).as_posix(),
        }
        if path == query:
            reference.update(
                schema_version=document["schema_version"],
                query_id=document["query_id"],
            )
        elif path == candidate_set:
            reference.update(
                schema_version=document["schema_version"],
                candidate_set_id=document["candidate_set_id"],
            )
        elif path == admission:
            reference.update(
                schema_version=document["schema_version"],
                admissibility_id=document["admissibility_id"],
            )
        else:
            reference.update(
                schema_version=(
                    "text2ifc/ifc-property-resolution-result/0.1"
                ),
                decision_id=(
                    "property-decision:run-e1:e1-window-property:claim-001"
                ),
            )
        return reference

    state = {
        "run_id": "run-e1",
        "transitions": [
            *[
            {
                "transition_id": transition_id,
                "state_version": transition_id,
                "stage_payload": {
                    "property_resolution": {
                        "checkpoint": checkpoint,
                        "run_id": "run-e1",
                        "operation_id": "e1-window-property",
                        "claim_id": "claim-001",
                        "artifacts": (
                            {"query": _ref(query), "candidate_set": _ref(candidate_set)}
                            if checkpoint == "candidates"
                            else (
                                {"decision": _ref(decision_result)}
                                if checkpoint == "decision"
                                else {"admissibility": _ref(admission)}
                            )
                        ),
                    }
                }
            }
            for transition_id, checkpoint in enumerate(
                ("candidates", "decision", "admissibility"), start=1
            )
            ],
            {
                "transition_id": 4,
                "state_version": 4,
                "from_stage": "intent_ready",
                "to_stage": "clarification_required",
                "reason_code": "property_resolution",
                "clarification": {
                    "clarification_id": "clarify-004",
                    "run_id": "run-e1",
                    "operation_id": "e1-window-property",
                    "claim_id": "claim-001",
                    "reason_code": "property_resolution",
                    "answer_modes": ["add_detail", "cancel"],
                },
                "answer": None,
            },
            {
                "transition_id": 5,
                "state_version": 5,
                "from_stage": "clarification_required",
                "to_stage": "intent_ready",
                "answer": {"kind": "add_detail", "detail": "改为 EI60。"},
                "stage_payload": {
                    "clarification_id": "clarify-004",
                    "property_resolution_generation": 5,
                },
            },
        ],
    }

    proof_validator._audit_r1_m1_initial_replay_binding(
        replay_paths=replay_paths,
        roles=roles,
        state=state,
        state_path=state_path,
        expected_resume_answer="改为 EI60。",
        initial_intent=intent,
    )

    state["transitions"][-1]["stage_payload"][
        "property_resolution_generation"
    ] = 99
    with pytest.raises(ValueError, match="proof.m1.resume_lineage"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    state["transitions"][-1]["stage_payload"][
        "property_resolution_generation"
    ] = 5

    state["transitions"][-1]["stage_payload"]["clarification_id"] = (
        "clarify-forged"
    )
    with pytest.raises(ValueError, match="proof.m1.resume_lineage"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    state["transitions"][-1]["stage_payload"]["clarification_id"] = (
        "clarify-004"
    )

    forged_claim = deepcopy(initial_claim)
    forged_claim["raw_value"] = "EI90"
    _write_json(claim, forged_claim)
    with pytest.raises(ValueError, match="proof.m1.initial_claim"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    _write_json(claim, initial_claim)

    state["transitions"][0]["to_stage"] = "changeset_ready"
    with pytest.raises(ValueError, match="proof.m1.initial_stop"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    state["transitions"][0].pop("to_stage")

    state["transitions"][0]["result_artifacts"] = {
        "successful_ifc": "published/forged.ifc"
    }
    with pytest.raises(ValueError, match="proof.m1.initial_stop"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    state["transitions"][0].pop("result_artifacts")

    state["transitions"][-1]["answer"]["detail"] = "改为 EI90。"
    with pytest.raises(ValueError, match="proof.m1.resume_answer"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    state["transitions"][-1]["answer"]["detail"] = "改为 EI60。"

    state["transitions"][-2]["clarification"]["claim_id"] = "claim-spliced"
    with pytest.raises(ValueError, match="proof.m1.resume_clarification"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    state["transitions"][-2]["clarification"]["claim_id"] = "claim-001"

    result_document = proof_validator._read_json(decision_result)
    result_document["trace"]["claim_id"] = "claim-spliced"
    _write_json(decision_result, result_document)
    state["transitions"][1]["stage_payload"]["property_resolution"][
        "artifacts"
    ]["decision"] = _ref(decision_result)
    with pytest.raises(ValueError, match="proof.m1.initial_replay_artifact"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
    result_document["trace"] = proof_validator._read_json(
        roles["property_trace"]
    )
    _write_json(decision_result, result_document)
    state["transitions"][1]["stage_payload"]["property_resolution"][
        "artifacts"
    ]["decision"] = _ref(decision_result)

    foreign_trace = tmp_path / "foreign" / "trace.json"
    foreign_trace.parent.mkdir(parents=True)
    shutil.copy2(roles["property_trace"], foreign_trace)
    replay_paths["decision_trace"] = foreign_trace
    with pytest.raises(ValueError, match="proof.m1.initial_replay_binding"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )

    replay_paths["decision_trace"] = roles["property_trace"]
    query_document = proof_validator._read_json(query)
    query_document["claim_id"] = "claim-001-resume-012"
    _write_json(query, query_document)
    with pytest.raises(ValueError, match="proof.m1.initial_claim"):
        proof_validator._audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=state,
            state_path=state_path,
            expected_resume_answer="改为 EI60。",
            initial_intent=intent,
        )
