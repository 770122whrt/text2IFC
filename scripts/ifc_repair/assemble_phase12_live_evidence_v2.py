"""Assemble human-first evidence for the Plan 07 VVO genuine live run.

The resulting package independently reopens and re-audits retained artifacts,
but it deliberately keeps Phase acceptance pending until the frozen Plan 12/14
Proof gate consumes the evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

import ifcopenshell


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scripts.ifc_repair import curate_phase12_live_proof as legacy  # noqa: E402
from scripts.ifc_repair import run_phase12_live_uat_v2 as live_v2  # noqa: E402
from scripts.ifc_repair.validate_success_cases import (  # noqa: E402
    audit_repaired_operations,
)
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402
from text2ifc_ifc_repair.prompt_profiles import select_prompt_profiles  # noqa: E402
from text2ifc_ifc_repair.structural_restoration import (  # noqa: E402
    audit_structural_restoration_case,
)


EVIDENCE_SCHEMA = "text2ifc/phase12-live-evidence-package/0.2"
VALIDATION_SCHEMA = "text2ifc/phase12-live-evidence-validation/0.2"
SUCCESS_CASE_IDS = (
    "complete",
    "clarification-resume",
    "window-semantic-canary",
)
NO_REPAIR_CASE_IDS = ("program-guard",)
REQUIRED_CASE_IDS = (*SUCCESS_CASE_IDS, *NO_REPAIR_CASE_IDS)
BASE_CASE = live_v2.SOURCE.parent
EXPECTED_COUNTS = {
    "complete": {"stage1": 1, "property_resolution": 2, "stage2": 1},
    "clarification-resume": {
        "stage1": 1,
        "property_resolution": 1,
        "stage2": 1,
    },
    "window-semantic-canary": {
        "stage1": 1,
        "property_resolution": 1,
        "stage2": 1,
    },
    "program-guard": {"stage1": 1, "property_resolution": 0, "stage2": 0},
}


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"LIVE_V2_EVIDENCE_JSON_OBJECT_REQUIRED:{path}")
    return value


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        value
        if isinstance(value, str)
        else json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )
    path.write_text(payload.rstrip() + "\n", encoding="utf-8")


def _copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _case_definition(case_id: str) -> Any:
    return next(case for case in live_v2.DEFAULT_CASES if case.case_id == case_id)


def _thinking_enabled(attempt: Mapping[str, Any]) -> bool:
    request = attempt.get("request")
    metadata = attempt.get("metadata")
    if not isinstance(request, Mapping) or not isinstance(metadata, Mapping):
        return False
    extra = request.get("extra_body")
    configuration = metadata.get("request_configuration")
    return bool(
        request.get("model") == live_v2.APPROVED_MODEL
        and isinstance(extra, Mapping)
        and extra.get("thinking") == {"type": "enabled"}
        and isinstance(configuration, Mapping)
        and configuration.get("thinking") == {"type": "enabled"}
        and isinstance(configuration.get("temperature"), Mapping)
        and configuration["temperature"].get("effective") is False
    )


def audit_live_uat_result_v2(result: Mapping[str, Any]) -> dict[str, Any]:
    """Recompute transcript integrity without trusting aggregate pass flags."""

    if (
        result.get("schema_version") != legacy.LIVE_UAT_SCHEMA
        or result.get("case_contract_version")
        != live_v2.LIVE_CASE_CONTRACT_VERSION
        or result.get("status") != "passed"
        or result.get("evidence_mode") != "live"
        or result.get("execution_mode") != "production_live"
        or result.get("synthetic_fallback_used") is not False
        or result.get("acceptance_eligible") is not False
        or result.get("proof_validation_status") != "pending_plan_12_14"
    ):
        raise ValueError("LIVE_V2_TRANSCRIPT_ROOT_INVALID")
    cases = result.get("cases")
    if not isinstance(cases, list) or [
        item.get("case_id") if isinstance(item, Mapping) else None
        for item in cases
    ] != list(REQUIRED_CASE_IDS):
        raise ValueError("LIVE_V2_CASE_MATRIX_INVALID")

    aggregate = {"stage1": 0, "property_resolution": 0, "stage2": 0}
    total_calls = 0
    models: set[tuple[str, str]] = set()
    for case in cases:
        assert isinstance(case, Mapping)
        case_id = str(case["case_id"])
        definition = _case_definition(case_id)
        expected_feedback = (
            None
            if definition.feedback is None
            else legacy._text_sha256(str(definition.feedback))
        )
        if (
            case.get("status") != "passed"
            or case.get("contract_pass") is not True
            or case.get("live_evidence_pass") is not True
            or case.get("private_evidence_detected") is not False
            or case.get("synthetic_fallback_used") is not False
            or case.get("request_sha256")
            != legacy._text_sha256(str(definition.request))
            or case.get("feedback_sha256") != expected_feedback
        ):
            raise ValueError(f"LIVE_V2_CASE_INVALID:{case_id}")
        attempts, counts, case_models = legacy._audit_attempts(
            case_id,
            case.get("attempts"),
        )
        if (
            counts != EXPECTED_COUNTS[case_id]
            or case.get("transport_calls") != len(attempts)
            or case.get("transport_calls_by_stage") != counts
            or any(not _thinking_enabled(item) for item in attempts)
            or case_models
            != {("deepseek-openai-compatible", live_v2.APPROVED_MODEL)}
        ):
            raise ValueError(f"LIVE_V2_ATTEMPTS_INVALID:{case_id}")
        final = case.get("final")
        if case_id in SUCCESS_CASE_IDS:
            if not legacy._strict_success(final):
                raise ValueError(f"LIVE_V2_SUCCESS_TERMINAL_INVALID:{case_id}")
            if case_id == "clarification-resume":
                assert isinstance(final, Mapping)
                initial = final.get("initial")
                clarification = final.get("clarification")
                if (
                    final.get("clarification_answer_applied") is not True
                    or not isinstance(initial, Mapping)
                    or initial.get("status") != "clarification_required"
                    or not isinstance(clarification, Mapping)
                    or clarification.get("reason_code") != "property_resolution"
                ):
                    raise ValueError("LIVE_V2_CLARIFICATION_INVALID")
        else:
            if not isinstance(final, Mapping):
                raise ValueError("LIVE_V2_GUARD_INVALID")
            guard = final.get("program_guard_evidence")
            if (
                final.get("status") != "unsupported"
                or final.get("reason_code") != legacy.PROGRAM_GUARD_REASON
                or not isinstance(guard, Mapping)
                or guard.get("source_unchanged") is not True
                or guard.get("mutation_attempted") is not False
                or guard.get("stage2_attempts") != 0
                or guard.get("candidate_output_paths") != []
            ):
                raise ValueError("LIVE_V2_GUARD_INVALID")
        total_calls += len(attempts)
        for stage in aggregate:
            aggregate[stage] += counts[stage]
        models.update(case_models)
    expected_models = [
        {"provider": provider, "model": model}
        for provider, model in sorted(models)
    ]
    if (
        result.get("transport_calls") != total_calls
        or result.get("transport_calls_by_stage") != aggregate
        or result.get("provider_models") != expected_models
    ):
        raise ValueError("LIVE_V2_TRANSCRIPT_AGGREGATE_INVALID")
    return {
        "schema_version": "text2ifc/phase12-live-transcript-audit/0.2",
        "status": "passed",
        "success_case_ids": list(SUCCESS_CASE_IDS),
        "no_repair_case_ids": list(NO_REPAIR_CASE_IDS),
        "transport_calls": total_calls,
        "transport_calls_by_stage": aggregate,
        "provider_models": expected_models,
    }


def _artifact_binding(
    result: Mapping[str, Any],
    case_id: str,
    intent: Mapping[str, Any],
    draft: Mapping[str, Any],
    changeset: Mapping[str, Any],
) -> dict[str, Any]:
    case = legacy._case_from_result(result, case_id)
    attempts = case.get("attempts")
    if not isinstance(attempts, list):
        raise ValueError("LIVE_V2_ATTEMPTS_MISSING")
    stage1 = [item for item in attempts if item.get("stage") == "stage1"]
    stage2 = [item for item in attempts if item.get("stage") == "stage2"]
    if not stage1 or not stage2:
        raise ValueError("LIVE_V2_PROVIDER_DOCUMENT_MISSING")
    legacy._bind_stage1(legacy._response_document(stage1[-1]), intent)
    legacy._bind_stage2(legacy._response_document(stage2[-1]), draft)
    legacy._bind_stage2(draft, changeset)
    return {
        "status": "passed",
        "stage1_attempt_id": stage1[-1]["attempt_id"],
        "stage2_attempt_id": stage2[-1]["attempt_id"],
    }


def _runtime_authority(
    source_root: Path,
    result: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    case = legacy._case_from_result(result, case_id)
    final = case.get("final")
    if not legacy._strict_success(final):
        raise ValueError("LIVE_V2_SUCCESS_TERMINAL_INVALID")
    assert isinstance(final, Mapping)
    run_id = str(final["run_id"])
    case_root = source_root / "cases" / case_id
    if _read(case_root / "case-result.json") != case:
        raise ValueError("LIVE_V2_CASE_RESULT_BINDING_MISMATCH")
    run_root = case_root / "runtime" / "runs" / run_id
    intent_path = legacy._safe_relative(run_root, "intent/repair-intent.json")
    resolution_path = legacy._safe_relative(run_root, "resolution.json")
    changeset_path = legacy._safe_relative(run_root, "changeset.json")
    bound_path = legacy._safe_relative(run_root, "changeset/bound-changeset.json")
    draft_path = legacy._safe_relative(run_root, "changeset/provider-draft.json")
    profile_path = legacy._safe_relative(
        run_root,
        "changeset/prompt-profile-selection.json",
    )
    intent = _read(intent_path)
    changeset = _read(changeset_path)
    bound = _read(bound_path)
    draft = _read(draft_path)
    if legacy._canonical_sha256(changeset) != legacy._canonical_sha256(bound):
        raise ValueError("LIVE_V2_CHANGESET_BINDING_MISMATCH")
    definition = _case_definition(case_id)
    request_hash = legacy._text_sha256(str(definition.request))
    if (
        case.get("request_sha256") != request_hash
        or intent.get("source_request_hash") != request_hash
        or bound.get("source_request_hash") != request_hash
    ):
        raise ValueError("LIVE_V2_REQUEST_BINDING_MISMATCH")
    registry = create_default_registry()
    operation_types = {
        str(item.get("operation_type"))
        for item in bound.get("operations", ())
        if isinstance(item, Mapping)
    }
    draft_schema = str(draft.get("schema_version") or "")
    if draft_schema == "text2ifc/ifc-repair-changeset-draft/0.3":
        profile_ids = [
            str(registry.require(item).stage2_prompt_profile_id)
            for item in operation_types
        ]
    elif draft_schema == "text2ifc/ifc-repair-changeset-draft/0.2":
        profile_ids = [
            str(registry.require(item).prompt_profile_id)
            for item in operation_types
        ]
    else:
        raise ValueError("LIVE_V2_STAGE2_SCHEMA_UNREVIEWED")
    if not profile_ids or any(item == "None" for item in profile_ids):
        raise ValueError("LIVE_V2_PROFILE_ID_MISSING")
    expected_profiles = select_prompt_profiles(sorted(profile_ids)).to_dict()
    if _read(profile_path) != expected_profiles:
        raise ValueError("LIVE_V2_PROFILE_BINDING_MISMATCH")
    binding = _artifact_binding(result, case_id, intent, draft, bound)
    manifest_path = legacy._artifact_from_final(run_root, final, "manifest")
    evaluation_path = legacy._artifact_from_final(run_root, final, "evaluation")
    repaired_path = legacy._artifact_from_final(run_root, final, "successful_ifc")
    publication = _read(manifest_path)
    published = {
        str(item.get("path")): item
        for item in publication.get("artifacts", ())
        if isinstance(item, Mapping)
    }
    for artifact in (evaluation_path, repaired_path):
        relative = artifact.relative_to(run_root).as_posix()
        record = published.get(relative)
        if (
            not isinstance(record, Mapping)
            or record.get("sha256") != _sha256(artifact).removeprefix("sha256:")
            or record.get("size_bytes") != artifact.stat().st_size
        ):
            raise ValueError("LIVE_V2_PUBLICATION_BINDING_MISMATCH")
    terminal = [
        run_root / relative
        for relative in published
        if relative.endswith("/evidence.json")
        or relative == "publication/terminal/evidence.json"
    ]
    terminal = [path for path in terminal if path.is_file()]
    if len(terminal) != 1:
        raise ValueError("LIVE_V2_TERMINAL_EVIDENCE_MISSING")
    return {
        "case": case,
        "run_id": run_id,
        "intent_path": intent_path,
        "resolution_path": resolution_path,
        "changeset_path": changeset_path,
        "draft_path": draft_path,
        "profile_path": profile_path,
        "evaluation_path": evaluation_path,
        "repaired_path": repaired_path,
        "changeset": bound,
        "application": legacy._application_from_terminal(terminal[0]),
        "artifact_binding": binding,
    }


def _write_files(case_root: Path, case_id: str) -> None:
    roles = {
        "REPORT.md": "human_report",
        "request.txt": "public_request",
        "original.ifc": "shared_pre_damage_source",
        "damaged.ifc": "live_repair_input",
        "repaired.ifc": "published_repair_output",
        "NO-REPAIR.md": "expected_no_output_explanation",
        "proof-result.json": "independent_evidence_result",
        "case-result.json": "genuine_provider_attempt_ledger",
        "changeset.json": "bound_changeset",
        "application.json": "application_result",
        "evaluation.json": "production_evaluation",
        "repair-intent.json": "stage1_repair_intent",
        "target-resolution.json": "target_resolution",
        "provider-draft.json": "stage2_provider_draft",
        "prompt-profile-selection.json": "prompt_profile_binding",
        "structural-restoration-audit.json": "independent_restoration_audit",
        "mutation_manifest.private.json": "private_damage_authority",
        "base-damage-manifest.json": "base_damage_manifest",
        "source-role.json": "ifc_role_declaration",
    }
    entries = []
    for path in sorted(case_root.iterdir()):
        if not path.is_file() or path.name == "FILES.json":
            continue
        entries.append(
            {
                "path": path.name,
                "role": roles.get(path.name, "retained_case_evidence"),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    _write(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
            "case_id": case_id,
            "files": entries,
        },
    )


def _stage_success(
    bundle: Path,
    source_root: Path,
    result: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    authority = _runtime_authority(source_root, result, case_id)
    case_root = bundle / "cases" / case_id
    case_root.mkdir(parents=True)
    for name in (
        "original.ifc",
        "damaged.ifc",
        "mutation_manifest.private.json",
    ):
        _copy(BASE_CASE / name, case_root / name)
    _copy(BASE_CASE / "manifest.json", case_root / "base-damage-manifest.json")
    _copy(authority["repaired_path"], case_root / "repaired.ifc")
    for key, name in (
        ("intent_path", "repair-intent.json"),
        ("resolution_path", "target-resolution.json"),
        ("changeset_path", "changeset.json"),
        ("draft_path", "provider-draft.json"),
        ("profile_path", "prompt-profile-selection.json"),
        ("evaluation_path", "evaluation.json"),
    ):
        _copy(authority[key], case_root / name)
    _write(case_root / "application.json", authority["application"])
    definition = _case_definition(case_id)
    _write(case_root / "request.txt", str(definition.request))
    if definition.feedback is not None:
        _write(case_root / "clarification-answer.txt", str(definition.feedback))
    _copy(
        source_root / "cases" / case_id / "case-result.json",
        case_root / "case-result.json",
    )
    _write(
        case_root / "source-role.json",
        {
            "schema_version": "text2ifc/ifc-proof-source-role/0.1",
            "original_role": "shared VVO pre-damage source",
            "damaged_role": "exact public IFC supplied to the live repair API",
            "repaired_role": "genuine Provider-driven published repair output",
            "original_is_case_specific_property_gold": False,
            "private_evidence_available_during_repair": False,
        },
    )
    original = ifcopenshell.open(str(case_root / "original.ifc"))
    damaged = ifcopenshell.open(str(case_root / "damaged.ifc"))
    repaired = ifcopenshell.open(str(case_root / "repaired.ifc"))
    if {original.schema, damaged.schema, repaired.schema} != {"IFC2X3"}:
        raise ValueError(f"LIVE_V2_IFC_SCHEMA_INVALID:{case_id}")
    if _sha256(case_root / "damaged.ifc") != live_v2.FROZEN_SOURCE_SHA256:
        raise ValueError(f"LIVE_V2_SOURCE_DRIFT:{case_id}")
    independent = audit_repaired_operations(
        changeset=authority["changeset"],
        application=authority["application"],
        damaged_model=damaged,
        repaired_model=repaired,
    )
    operation_count = len(authority["changeset"].get("operations", ()))
    operation_types = {
        str(item.get("operation_type"))
        for item in authority["changeset"].get("operations", ())
        if isinstance(item, Mapping)
    }
    structural = None
    if operation_types & {"add_beam", "add_column"}:
        coverage_mode = (
            "requested_operation_subset"
            if case_id == "clarification-resume"
            else "complete_damage_set"
        )
        structural = audit_structural_restoration_case(
            case_root,
            coverage_mode=coverage_mode,
        )
        if structural.get("restoration_eligible") is not True:
            raise ValueError(f"LIVE_V2_RESTORATION_FAILED:{case_id}")
        _write(case_root / "structural-restoration-audit.json", structural)
    strict = authority["case"]["final"]["strict_reopen_verification"]
    l0 = strict.get("l0_pass") is True
    l1 = independent["l1_operation_count"] == operation_count
    l2 = independent["l2_operation_count"] == operation_count
    if not (l0 and l1 and l2):
        raise ValueError(f"LIVE_V2_INDEPENDENT_EVIDENCE_FAILED:{case_id}")
    _write(
        case_root / "proof-result.json",
        {
            "schema_version": VALIDATION_SCHEMA,
            "case_id": case_id,
            "evidence_validation_status": "passed",
            "phase_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
            "provider": "deepseek-openai-compatible",
            "model": live_v2.APPROVED_MODEL,
            "provider_calls": authority["case"]["transport_calls"],
            "provider_calls_by_stage": authority["case"]["transport_calls_by_stage"],
            "runtime_run_id": authority["run_id"],
            "operation_count": operation_count,
            "reopened_ifc_count": 3,
            "l0_pass": l0,
            "l1_pass": l1,
            "l2_pass": l2,
            "independent_l1_operation_count": independent["l1_operation_count"],
            "independent_l2_operation_count": independent["l2_operation_count"],
            "artifact_binding": authority["artifact_binding"],
            "structural_restoration": structural,
        },
    )
    if case_id == "complete":
        conclusion = (
            "同一原子 ChangeSet 恢复一个 Beam 和一个 Column；Storey、中心轴与矩形"
            "截面均在 0.01 mm 容差内匹配损伤前构件。"
        )
    elif case_id == "clarification-resume":
        conclusion = (
            "澄清后只恢复 request 授权的 Column。仍缺失的 Beam 未被偷偷补齐，"
            "并明确列为 unrequested damage。"
        )
    else:
        conclusion = (
            "对既有 Window occurrence 写入外窗属性；这是 property repair，所以有"
            " repaired.ifc，但不会创建 Beam 或 Column。"
        )
    _write(
        case_root / "REPORT.md",
        (
            f"# {case_id}\n\n"
            f"证据结论：**通过**。{conclusion}\n\n"
            f"- Provider/model：`deepseek-openai-compatible / {live_v2.APPROVED_MODEL}`\n"
            f"- Provider calls：`{authority['case']['transport_calls']}`\n"
            f"- Runtime run ID：`{authority['run_id']}`\n"
            f"- Operations：`{operation_count}`\n"
            "- original / damaged / repaired 已独立重开为 `IFC2X3`\n"
            f"- 独立 L1/L2 operations：`{independent['l1_operation_count']}/"
            f"{independent['l2_operation_count']}`\n"
            "- `original.ifc` 是评估后引入的共享损伤前来源，未发送给 Provider。\n"
            "- Phase acceptance 仍由冻结 Plan 12/14 Proof gate 决定。\n"
        ),
    )
    _write_files(case_root, case_id)
    return {
        "case_id": case_id,
        "outcome": "repaired",
        "status": "passed",
        "provider_calls": authority["case"]["transport_calls"],
        "runtime_run_id": authority["run_id"],
        "operation_count": operation_count,
        "l0_pass": l0,
        "l1_pass": l1,
        "l2_pass": l2,
        "repaired_ifc": f"cases/{case_id}/repaired.ifc",
        "report": f"cases/{case_id}/REPORT.md",
    }


def _stage_guard(
    bundle: Path,
    source_root: Path,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    case_id = "program-guard"
    case = legacy._case_from_result(result, case_id)
    final = case["final"]
    guard = final["program_guard_evidence"]
    case_root = bundle / "cases" / case_id
    case_root.mkdir(parents=True)
    _copy(live_v2.SOURCE, case_root / "damaged.ifc")
    _write(case_root / "request.txt", str(_case_definition(case_id).request))
    _copy(
        source_root / "cases" / case_id / "case-result.json",
        case_root / "case-result.json",
    )
    source_unchanged = bool(
        guard.get("source_unchanged") is True
        and guard.get("source_sha256_before") == live_v2.FROZEN_SOURCE_SHA256
        and guard.get("source_sha256_after") == live_v2.FROZEN_SOURCE_SHA256
        and _sha256(case_root / "damaged.ifc") == live_v2.FROZEN_SOURCE_SHA256
    )
    if (
        not source_unchanged
        or guard.get("stage2_attempts") != 0
        or guard.get("mutation_attempted") is not False
        or guard.get("candidate_output_paths") != []
    ):
        raise ValueError("LIVE_V2_GUARD_EVIDENCE_FAILED")
    _write(
        case_root / "proof-result.json",
        {
            "schema_version": VALIDATION_SCHEMA,
            "case_id": case_id,
            "evidence_validation_status": "passed",
            "phase_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
            "outcome": "expected_no_repair",
            "reason_code": final["reason_code"],
            "provider_calls": case["transport_calls"],
            "provider_calls_by_stage": case["transport_calls_by_stage"],
            "runtime_run_id": final["run_id"],
            "source_unchanged": True,
            "stage2_attempts": 0,
            "mutation_attempted": False,
            "published_outputs": [],
            "repaired_ifc_expected": False,
        },
    )
    _write(
        case_root / "NO-REPAIR.md",
        (
            "# 为什么没有 repaired.ifc\n\n"
            "请求同时包含 Beam 和当前合同不支持的 structural analysis node。系统在"
            " Stage 1 后以 `STRUCTURAL_ANALYSIS_UNSUPPORTED` 终止；Stage 2、IFC mutation"
            " 和 publish 都是零。没有 repaired.ifc 是正确的安全结果，不是遗漏。\n"
        ),
    )
    _write(
        case_root / "REPORT.md",
        (
            "# program-guard\n\n"
            "证据结论：**通过（预期无输出）**。\n\n"
            "- Provider calls：`1`（仅 Stage 1）\n"
            "- Stage 2：`0`\n"
            "- Mutation：`false`\n"
            "- Publish：`0`\n"
            "- Source unchanged：`true`\n"
            "- 详细解释见 `NO-REPAIR.md`。\n"
        ),
    )
    _write_files(case_root, case_id)
    return {
        "case_id": case_id,
        "outcome": "expected_no_repair",
        "status": "passed",
        "provider_calls": 1,
        "runtime_run_id": final["run_id"],
        "operation_count": 0,
        "l0_pass": True,
        "l1_pass": None,
        "l2_pass": None,
        "repaired_ifc": None,
        "report": f"cases/{case_id}/REPORT.md",
    }


def _write_manifest(bundle: Path, cases: Sequence[Mapping[str, Any]]) -> None:
    files = []
    for path in sorted(bundle.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        files.append(
            {
                "path": path.relative_to(bundle).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    _write(
        bundle / "manifest.json",
        {
            "schema_version": EVIDENCE_SCHEMA,
            "evidence_validation_status": "passed",
            "phase_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
            "human_entrypoint": "REPORT.md",
            "case_count": len(cases),
            "cases": list(cases),
            "files": files,
        },
    )


def curate(
    run_root: Path | str,
    proof_root: Path | str = live_v2.DEFAULT_PROOF_ROOT,
) -> dict[str, Any]:
    source_root = Path(run_root).resolve()
    result_path = source_root / "live-uat-result.json"
    result = _read(result_path)
    transcript = audit_live_uat_result_v2(result)
    if _sha256(live_v2.SOURCE) != live_v2.FROZEN_SOURCE_SHA256:
        raise ValueError("LIVE_V2_FROZEN_SOURCE_DRIFT")
    destination_root = Path(proof_root).resolve()
    destination_root.mkdir(parents=True, exist_ok=True)
    bundle_name = f"plan07-live-v2-{source_root.name}"
    destination = destination_root / bundle_name
    if destination.exists():
        raise ValueError("LIVE_V2_EVIDENCE_PACKAGE_ALREADY_EXISTS")
    with tempfile.TemporaryDirectory(
        prefix="plan07-live-v2-evidence-",
        dir=destination_root,
    ) as temporary:
        stage = Path(temporary) / bundle_name
        stage.mkdir()
        provider_root = stage / "provider-evidence"
        _copy(result_path, provider_root / "live-uat-result.json")
        admission = result.get("preflight", {}).get("admission_path")
        if isinstance(admission, str):
            admission_path = (ROOT / admission).resolve()
            if admission_path.is_relative_to(ROOT) and admission_path.is_file():
                _copy(admission_path, provider_root / "changed-scope-admission.json")
        cases = [
            _stage_success(stage, source_root, result, case_id)
            for case_id in SUCCESS_CASE_IDS
        ]
        cases.append(_stage_guard(stage, source_root, result))
        validation = {
            "schema_version": VALIDATION_SCHEMA,
            "evidence_validation_status": "passed",
            "phase_acceptance_eligible": False,
            "proof_validation_status": "pending_plan_12_14",
            "source_run": source_root.relative_to(ROOT).as_posix(),
            "transcript": transcript,
            "success_case_count": 3,
            "no_repair_case_count": 1,
            "cases": cases,
        }
        _write(stage / "proof-validation.json", validation)
        rows = "\n".join(
            "| {case_id} | {outcome} | {provider_calls} | {operation_count} | "
            "{l0} | {l1} | {l2} |".format(
                **case,
                l0=case["l0_pass"],
                l1="N/A" if case["l1_pass"] is None else case["l1_pass"],
                l2="N/A" if case["l2_pass"] is None else case["l2_pass"],
            )
            for case in cases
        )
        _write(
            stage / "REPORT.md",
            (
                "# Phase 12 Plan 07 genuine Provider evidence v2\n\n"
                "本次连续 genuine run 的四个冻结角色全部通过：三案产生并独立重开"
                " repaired IFC，一案按 unsupported guard 正确地产生零 repair。\n\n"
                f"- Live run：`{source_root.name}`\n"
                f"- Provider/model：`deepseek-openai-compatible / {live_v2.APPROVED_MODEL}`\n"
                "- Thinking：`enabled`\n"
                f"- Calls：`{transcript['transport_calls']}`（Stage 1=4，"
                "Stage 1.5=4，Stage 2=3）\n\n"
                "| Case | 结果 | Calls | Operations | L0 | L1 | L2 |\n"
                "|---|---:|---:|---:|---:|---:|---:|\n"
                f"{rows}\n\n"
                "## 阅读入口\n\n"
                "打开 `cases/<case>/REPORT.md`，同目录直接提供 request、damaged IFC"
                " 与 repaired IFC。program-guard 的原因在 `NO-REPAIR.md`。\n\n"
                "## 证据边界\n\n"
                "这组材料是真实 Provider 与真实 IFC 的单场景证据；不把它夸大为跨场景"
                "能力提升。Phase acceptance 仍保持 pending，直到冻结 Plan 12/14 Proof gate"
                " 完成。IFC 文件字节大小不是损伤方向判据，判定依据是目标差分、独立重开"
                "以及几何、语义和 preservation 检查。\n"
            ),
        )
        _write_manifest(stage, cases)
        os.replace(stage, destination)
    return {
        "schema_version": EVIDENCE_SCHEMA,
        "evidence_validation_status": "passed",
        "phase_acceptance_eligible": False,
        "proof_validation_status": "pending_plan_12_14",
        "proof_bundle": destination.as_posix(),
        "source_run": source_root.as_posix(),
        "success_case_count": 3,
        "no_repair_case_count": 1,
        "transport_calls": transcript["transport_calls"],
        "case_ids": list(REQUIRED_CASE_IDS),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble human-first evidence for Plan 07 v2 live UAT."
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--proof-root", type=Path, default=live_v2.DEFAULT_PROOF_ROOT)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    payload = curate(args.run_root, args.proof_root)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"evidence={payload['evidence_validation_status']} "
            f"calls={payload['transport_calls']} bundle={payload['proof_bundle']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
