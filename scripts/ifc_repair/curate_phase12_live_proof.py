"""Validate and curate genuine Phase 12 live structural Proof.

The runner's aggregate booleans are never curation authority.  This module
reconciles the redacted attempt ledger, binds the last valid Provider
documents to retained runtime artifacts, stages candidate Proof, and invokes
the family-neutral validator in a separate Python process before installation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from scripts.ifc_repair.run_phase12_live_uat import (  # noqa: E402
    DEFAULT_CASES,
    DEFAULT_OUTPUT,
    DEFAULT_PROOF_ROOT,
    FROZEN_SOURCE_SHA256,
    PROGRAM_GUARD_REASON,
    SOURCE,
    _few_shot_binding_map,
    _load_green_full_preflight_evidence,
)
from text2ifc_agent.prompt_registry import load_prompt_registry  # noqa: E402
from text2ifc_ifc_repair.prompt_profiles import select_prompt_profiles  # noqa: E402
from text2ifc_ifc_repair.run_models import RunStoreError  # noqa: E402
from text2ifc_ifc_repair.run_store import RunStore  # noqa: E402
from text2ifc_ifc_repair.property_resolution_stage import (  # noqa: E402
    TEMPLATE_ID as PROPERTY_RESOLUTION_TEMPLATE_ID,
)

from text2ifc_proof.live_audit import (
    EXPECTED_SELECTED_PROFILES,
    EXPECTED_STAGE1_PROFILES,
    FORBIDDEN_FALLBACK_FLAGS,
    HISTORICAL_SELECTED_PROFILES,
    LIVE_EVIDENCE_MODE,
    LIVE_PROVIDER,
    LIVE_UAT_SCHEMA,
    PROGRAM_GUARD_CASE_ID,
    PROPERTY_RESOLUTION_TEMPLATE_HASH,
    REQUIRED_CASE_IDS,
    SEMANTIC_CANARY_CASE_ID,
    SUCCESS_CASE_IDS,
    _attempt_round_contract,
    _audit_attempts,
    _bind_stage1,
    _bind_stage2,
    _canonical_sha256,
    _case_definition,
    _expected_plan07_stage2_profiles,
    _profile_identity_from_records,
    _require_text,
    _response_document,
    _stage2_identity_from_selection,
    _stage2_response_schema,
    _strict_success,
    _text_sha256,
    _valid_sha256,
    audit_live_artifact_binding,
    audit_live_attempts,
    audit_live_uat_result,
)


LIVE_SOURCE_SCHEMA = "text2ifc/phase12-live-proof-source/0.1"
BASE_EVIDENCE_MODE = "offline_bound_deterministic"
EVIDENCE_SCOPE = "cross_scene_same_family_bimnet"
BASE_DAMAGE_CASE_ID = "phase12-d7n-beam-column-atomic"
BASE_DAMAGE_CASE = SOURCE.parent

PROOF_CASE_IDS = {
    "complete": "phase12-live-deepseek-complete",
    "clarification-resume": "phase12-live-deepseek-clarification-resume",
}
VALIDATOR = ROOT / "scripts/ifc_repair/validate_success_cases.py"
PROOF_VALIDATION_SCHEMA = (
    ROOT / "schemas/agent/ifc-repair-proof-validation-0.2.schema.json"
)


def _path_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON_OBJECT_REQUIRED:{path}")
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


def _safe_relative(root: Path, raw: Any) -> Path:
    relative = Path(str(raw).replace("\\", "/"))
    if not str(raw) or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"LIVE_ARTIFACT_PATH_UNSAFE:{raw}")
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _effective_request(case_id: str) -> tuple[str, str, str | None]:
    case = _case_definition(case_id)
    initial = str(case.request)
    feedback = None if case.feedback is None else str(case.feedback)
    effective = (
        f"{initial}\n补充说明：{feedback.strip()}"
        if feedback is not None and case.feedback_kind == "add_detail"
        else initial
    )
    return effective, initial, feedback


def _case_from_result(result: Mapping[str, Any], case_id: str) -> Mapping[str, Any]:
    case = next(
        (
            item
            for item in result.get("cases", ())
            if isinstance(item, Mapping) and item.get("case_id") == case_id
        ),
        None,
    )
    if not isinstance(case, Mapping):
        raise ValueError(f"LIVE_CASE_MISSING:{case_id}")
    return case


def _copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_bound_preflight_evidence(
    preflight_root: Path,
    destination: Path,
) -> None:
    """Retain only the strict preflight manifest and its declared evidence closure."""

    preflight_path = preflight_root / "preflight.json"
    _load_green_full_preflight_evidence(preflight_path)
    payload = _read(preflight_path)
    _copy_file(preflight_path, destination / "preflight.json")
    copied: set[str] = {"preflight.json"}
    records: list[dict[str, Any]] = []

    def retain(
        source: Path,
        relative: Path,
        *,
        check_name: str,
        evidence_kind: str,
        source_reference: str,
    ) -> None:
        normalized = relative.as_posix()
        if normalized not in copied:
            _copy_file(source, destination / relative)
            copied.add(normalized)
        records.append(
            {
                "check_name": check_name,
                "evidence_kind": evidence_kind,
                "source_reference": source_reference,
                "retained_path": normalized,
                "sha256": _path_sha256(source),
                "size_bytes": source.stat().st_size,
            }
        )

    for check in payload["checks"]:
        name = str(check["name"])
        for stream_name in ("stdout", "stderr"):
            relative = Path("logs") / f"{name}.{stream_name}.txt"
            retain(
                preflight_root / relative,
                relative,
                check_name=name,
                evidence_kind=stream_name,
                source_reference=relative.as_posix(),
            )
        for index, artifact in enumerate(check["artifacts"], start=1):
            reference = str(artifact["path"])
            candidate = Path(reference)
            source = (
                candidate.resolve()
                if candidate.is_absolute()
                else (preflight_root / candidate).resolve()
            )
            try:
                relative = source.relative_to(preflight_root.resolve())
            except ValueError:
                digest = _path_sha256(source).removeprefix("sha256:")[:12]
                relative = (
                    Path("external-artifacts")
                    / f"{name}-{index:02d}-{digest}-{source.name}"
                )
            retain(
                source,
                relative,
                check_name=name,
                evidence_kind="declared_artifact",
                source_reference=reference,
            )
    _write(
        destination / "retained-artifacts.json",
        {
            "schema_version": (
                "text2ifc/phase12-live-proof-preflight-retention/0.1"
            ),
            "preflight_sha256": _path_sha256(preflight_path),
            "retained": records,
        },
    )


def _artifact_from_final(run_root: Path, final: Mapping[str, Any], name: str) -> Path:
    artifacts = final.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError("LIVE_TERMINAL_ARTIFACTS_MISSING")
    return _safe_relative(run_root, artifacts.get(name))


def _application_from_terminal(path: Path) -> dict[str, Any]:
    terminal = _read(path)
    evidence = terminal.get("evidence")
    application = evidence.get("application") if isinstance(evidence, Mapping) else None
    if not isinstance(application, dict):
        raise ValueError("LIVE_TERMINAL_APPLICATION_MISSING")
    return application


def _load_validated_run_state(
    runtime_root: Path,
    run_id: str,
    state_path: Path,
) -> Any:
    """Load and verify the production state plus its append-only transition ledger."""

    try:
        state = RunStore(runtime_root).load(run_id)
    except RunStoreError as error:
        raise ValueError("LIVE_RUNTIME_STATE_CHAIN_MISMATCH") from error
    if state.to_dict() != _read(state_path):
        raise ValueError("LIVE_RUNTIME_STATE_CHAIN_MISMATCH")
    return state


def _latest_bound_api_context(state: Any) -> Mapping[str, Any]:
    for transition in reversed(state.transitions):
        payload = transition.stage_payload
        binding = payload.get("api_context") if isinstance(payload, Mapping) else None
        if isinstance(binding, Mapping) and binding.get("path"):
            if (
                set(binding) != {"path", "sha256", "schema_version"}
                or binding.get("schema_version")
                != "text2ifc/ifc-repair-api-context/0.1"
            ):
                raise ValueError("LIVE_EFFECTIVE_REQUEST_CONTEXT_MISMATCH")
            return binding
    raise ValueError("LIVE_EFFECTIVE_REQUEST_CONTEXT_MISMATCH")


def _runtime_authority(
    source_root: Path,
    result: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    case = _case_from_result(result, case_id)
    final = case.get("final")
    if not _strict_success(final):
        raise ValueError("LIVE_SUCCESS_TERMINAL_INVALID")
    assert isinstance(final, Mapping)
    run_id = _require_text(final.get("run_id"), "LIVE_RUN_ID_REQUIRED")
    case_root = source_root / "cases" / case_id
    retained_case = _read(case_root / "case-result.json")
    if retained_case != case:
        raise ValueError("LIVE_CASE_RESULT_BINDING_MISMATCH")
    runtime_root = case_root / "runtime"
    run_root = runtime_root / "runs" / run_id
    if not run_root.is_dir():
        raise ValueError("LIVE_RUNTIME_RUN_MISSING")
    intent_path = _safe_relative(run_root, "intent/repair-intent.json")
    resolution_path = _safe_relative(run_root, "resolution.json")
    applied_changeset_path = _safe_relative(run_root, "changeset.json")
    bound_changeset_path = _safe_relative(
        run_root, "changeset/bound-changeset.json"
    )
    provider_draft_path = _safe_relative(run_root, "changeset/provider-draft.json")
    profile_path = _safe_relative(
        run_root, "changeset/prompt-profile-selection.json"
    )
    state_path = _safe_relative(run_root, "state.json")
    state = _load_validated_run_state(runtime_root, run_id, state_path)
    intent = _read(intent_path)
    applied_changeset = _read(applied_changeset_path)
    bound_changeset = _read(bound_changeset_path)
    provider_draft = _read(provider_draft_path)
    if _canonical_sha256(applied_changeset) != _canonical_sha256(bound_changeset):
        raise ValueError("LIVE_RUNTIME_CHANGESET_BINDING_MISMATCH")
    effective, initial, feedback = _effective_request(case_id)
    if case.get("request_sha256") != _text_sha256(initial) or case.get(
        "feedback_sha256"
    ) != (None if feedback is None else _text_sha256(feedback)):
        raise ValueError("LIVE_CASE_REQUEST_HASH_MISMATCH")
    effective_hash = _text_sha256(effective)
    if (
        intent.get("source_request_hash") != effective_hash
        or bound_changeset.get("source_request_hash") != effective_hash
    ):
        raise ValueError("LIVE_EFFECTIVE_REQUEST_BINDING_MISMATCH")
    context_binding = _latest_bound_api_context(state)
    context_path = _safe_relative(run_root, context_binding["path"])
    context = _read(context_path)
    context_intent = context.get("intent")
    if (
        _path_sha256(context_path) != context_binding.get("sha256")
        or context.get("repair_text") != effective
        or not isinstance(context_intent, Mapping)
        or context_intent.get("source_request_hash") != effective_hash
    ):
        raise ValueError("LIVE_EFFECTIVE_REQUEST_CONTEXT_MISMATCH")
    profile = _read(profile_path)
    expected_runtime_profiles = _expected_plan07_stage2_profiles(
        case_id,
        _require_text(
            provider_draft.get("schema_version"),
            "LIVE_RUNTIME_STAGE2_SCHEMA_REQUIRED",
        ),
    )
    if (
        frozenset(map(str, profile.get("profile_ids", ())))
        != expected_runtime_profiles
    ):
        raise ValueError("LIVE_RUNTIME_PROFILE_SELECTION_MISMATCH")


    audit_live_artifact_binding(
        result,
        case_id=case_id,
        intent=intent,
        provider_draft=provider_draft,
        changeset=bound_changeset,
    )
    manifest_path = _artifact_from_final(run_root, final, "manifest")
    evaluation_path = _artifact_from_final(run_root, final, "evaluation")
    repaired_path = _artifact_from_final(run_root, final, "successful_ifc")
    publication = _read(manifest_path)
    published = publication.get("artifacts")
    if not isinstance(published, list) or not published:
        raise ValueError("LIVE_PUBLICATION_MANIFEST_INVALID")
    published_paths = {
        str(item.get("path")): item
        for item in published
        if isinstance(item, Mapping)
    }
    for artifact in (evaluation_path, repaired_path):
        relative = artifact.relative_to(run_root).as_posix()
        record = published_paths.get(relative)
        if (
            not isinstance(record, Mapping)
            or record.get("sha256") != _path_sha256(artifact).removeprefix("sha256:")
            or record.get("size_bytes") != artifact.stat().st_size
        ):
            raise ValueError("LIVE_PUBLICATION_ARTIFACT_BINDING_MISMATCH")
    terminal_paths = [
        run_root / str(relative)
        for relative in published_paths
        if str(relative).endswith("/evidence.json")
        or str(relative) == "publication/terminal/evidence.json"
    ]
    terminal_paths = [path for path in terminal_paths if path.is_file()]
    if len(terminal_paths) != 1:
        raise ValueError("LIVE_TERMINAL_EVIDENCE_MISSING")
    semantic_ref = str(bound_changeset.get("semantic_manifest_ref") or "")
    semantic_path = _safe_relative(run_root, semantic_ref)
    return {
        "case": case,
        "run_id": run_id,
        "runtime_root": runtime_root,
        "run_root": run_root,
        "intent_path": intent_path,
        "resolution_path": resolution_path,
        "changeset_path": applied_changeset_path,
        "bound_changeset_path": bound_changeset_path,
        "provider_draft_path": provider_draft_path,
        "profile_path": profile_path,
        "semantic_path": semantic_path,
        "evaluation_path": evaluation_path,
        "repaired_path": repaired_path,
        "application": _application_from_terminal(terminal_paths[0]),
        "effective_request": effective,
        "initial_request": initial,
        "feedback": feedback,
        "changeset": bound_changeset,
    }


def _role_for_path(relative: str, fixed: Mapping[str, str], index: int) -> str:
    return fixed.get(relative, f"live_retained_artifact_{index:04d}")


def _write_case_files(case_root: Path, case_id: str) -> None:
    fixed_roles = {
        "manifest.json": "source_run_manifest",
        "base-damage-source-manifest.json": "base_damage_source_manifest",
        "original.ifc": "original_ground_truth",
        "damaged.ifc": "repair_input_ifc",
        "repaired.ifc": "published_repair_output",
        "request.txt": "user_request",
        "initial-request.txt": "initial_user_request",
        "clarification-answer.txt": "clarification_answer",
        "repair-intent.json": "stage1_repair_intent",
        "target-resolution.json": "deterministic_target_resolution",
        "semantic-manifests.json": "semantic_manifests",
        "changeset.json": "bound_changeset",
        "provider-draft.json": "live_provider_draft",
        "prompt-profile-selection.json": "live_prompt_profile_selection",
        "application.json": "application_result",
        "evaluation.json": "production_evaluation",
        "production-boundary.json": "production_input_boundary",
        "mutation_manifest.private.json": "mutation_manifest_private",
        "provider-evidence/live-uat-result.json": "live_provider_result",
        "provider-evidence/case-result.json": "live_provider_case_result",
    }
    entries = []
    for index, artifact in enumerate(sorted(case_root.rglob("*")), start=1):
        if not artifact.is_file() or artifact.name in {"FILES.json", "REPORT.md"}:
            continue
        relative = artifact.relative_to(case_root).as_posix()
        role = _role_for_path(relative, fixed_roles, index)
        if (
            artifact.parent == case_root
            and artifact.name.startswith("semantic-manifest")
            and artifact.suffix == ".json"
        ):
            role = "semantic_manifests"
        entries.append(
            {
                "path": relative,
                "role": role,
                "sha256": _path_sha256(artifact),
                "size_bytes": artifact.stat().st_size,
            }
        )
    _write(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.1",
            "case_id": case_id,
            "files": entries,
        },
    )


def _stage_case(
    stage_root: Path,
    source_root: Path,
    result: Mapping[str, Any],
    case_id: str,
) -> dict[str, Any]:
    authority = _runtime_authority(source_root, result, case_id)
    proof_case_id = PROOF_CASE_IDS[case_id]
    relative_root = Path("structural") / "live" / proof_case_id
    case_root = stage_root / relative_root
    case_root.mkdir(parents=True)
    for name in ("original.ifc", "damaged.ifc", "mutation_manifest.private.json"):
        _copy_file(BASE_DAMAGE_CASE / name, case_root / name)
    _copy_file(SOURCE, case_root / "damaged.ifc")
    base_manifest_path = BASE_DAMAGE_CASE / "manifest.json"
    _copy_file(base_manifest_path, case_root / "base-damage-source-manifest.json")
    _copy_file(authority["repaired_path"], case_root / "repaired.ifc")
    _copy_file(authority["intent_path"], case_root / "repair-intent.json")
    _copy_file(authority["resolution_path"], case_root / "target-resolution.json")
    _copy_file(
        authority["semantic_path"],
        case_root / Path(authority["semantic_path"]).name,
    )
    _copy_file(authority["changeset_path"], case_root / "changeset.json")
    _copy_file(authority["provider_draft_path"], case_root / "provider-draft.json")
    _copy_file(
        authority["profile_path"], case_root / "prompt-profile-selection.json"
    )
    _copy_file(authority["evaluation_path"], case_root / "evaluation.json")
    _write(case_root / "application.json", authority["application"])
    _write(case_root / "request.txt", authority["effective_request"])
    _write(case_root / "initial-request.txt", authority["initial_request"])
    if authority["feedback"] is not None:
        _write(case_root / "clarification-answer.txt", authority["feedback"])
    shutil.copytree(authority["runtime_root"], case_root / "runtime")
    provider_root = case_root / "provider-evidence"
    _copy_file(source_root / "live-uat-result.json", provider_root / "live-uat-result.json")
    _copy_file(
        source_root / "cases" / case_id / "case-result.json",
        provider_root / "case-result.json",
    )
    preflight_root = source_root / "preflight"
    if not preflight_root.is_dir():
        raise ValueError("LIVE_PREFLIGHT_EVIDENCE_MISSING")
    preflight = _read(preflight_root / "preflight.json")
    if preflight.get("status") != "passed":
        raise ValueError("LIVE_PREFLIGHT_EVIDENCE_FAILED")
    _copy_bound_preflight_evidence(
        preflight_root,
        provider_root / "preflight",
    )
    changeset = authority["changeset"]
    operation_count = len(changeset.get("operations", ()))
    _write(
        case_root / "production-boundary.json",
        {
            "schema_version": "text2ifc/production-input-boundary/0.2",
            "entrypoint": "run_phase12_live_uat.py",
            "ifc_inputs": ["damaged_ifc_path"],
            "request_inputs": ["public_request_bundle"],
            "original_ifc_supplied": False,
            "mutation_manifest_supplied": False,
            "deleted_object_ids_supplied": False,
            "private_comparator_available_during_repair": False,
            "damaged_ifc_sha256": _path_sha256(case_root / "damaged.ifc"),
            "request_sha256": changeset.get("source_request_hash"),
            "resolved_target_count": operation_count,
        },
    )
    base_manifest = _read(base_manifest_path)
    source_manifest = {
        "schema_version": LIVE_SOURCE_SCHEMA,
        "case_id": proof_case_id,
        "status": "passed",
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-chat",
        "provider_evidence_mode": LIVE_EVIDENCE_MODE,
        "synthetic_fallback_used": False,
        "evidence_scope": EVIDENCE_SCOPE,
        "operation_count": operation_count,
        "source": base_manifest.get("source"),
        "damage": base_manifest.get("damage"),
        "base_damage_contract": {
            "case_id": BASE_DAMAGE_CASE_ID,
            "source_manifest_path": "base-damage-source-manifest.json",
            "source_manifest_sha256": _path_sha256(
                case_root / "base-damage-source-manifest.json"
            ),
            "mutation_manifest_path": "mutation_manifest.private.json",
            "mutation_manifest_sha256": _path_sha256(
                case_root / "mutation_manifest.private.json"
            ),
            "original_ifc_sha256": _path_sha256(case_root / "original.ifc"),
            "damaged_ifc_sha256": _path_sha256(case_root / "damaged.ifc"),
        },
        "live_contract": {
            "case_id": case_id,
            "live_uat_result_path": "provider-evidence/live-uat-result.json",
            "live_uat_result_sha256": _path_sha256(
                provider_root / "live-uat-result.json"
            ),
            "provider_draft_path": "provider-draft.json",
            "provider_draft_sha256": _path_sha256(case_root / "provider-draft.json"),
            "prompt_profile_selection_path": "prompt-profile-selection.json",
            "prompt_profile_selection_sha256": _path_sha256(
                case_root / "prompt-profile-selection.json"
            ),
        },
        "artifacts": {},
    }
    _write(case_root / "manifest.json", source_manifest)
    artifacts = {}
    for artifact in sorted(case_root.rglob("*")):
        if not artifact.is_file() or artifact.name in {
            "FILES.json",
            "REPORT.md",
            "manifest.json",
        }:
            continue
        relative = artifact.relative_to(case_root).as_posix()
        artifacts[relative] = {
            "path": relative,
            "bytes": artifact.stat().st_size,
            "sha256": _path_sha256(artifact),
        }
    source_manifest["artifacts"] = artifacts
    _write(case_root / "manifest.json", source_manifest)
    _write(
        case_root / "REPORT.md",
        (
            f"# Phase 12 live Proof: {case_id}\n\n"
            "Genuine live transcript and its retained RepairAPI runtime were "
            "strictly revalidated before installation.\n"
        ),
    )
    _write_case_files(case_root, proof_case_id)
    operation_types = sorted(
        {
            str(item.get("operation_type"))
            for item in changeset.get("operations", ())
            if isinstance(item, Mapping)
        }
    )
    return {
        "case_id": proof_case_id,
        "phase": "12",
        "status": "accepted",
        "operation_family": "structural",
        "case_kind": "live",
        "provider": "deepseek-openai-compatible",
        "model": "deepseek-chat",
        "provider_evidence_mode": LIVE_EVIDENCE_MODE,
        "evidence_scope": EVIDENCE_SCOPE,
        "operation_count": operation_count,
        "operation_types": operation_types,
        "original_ifc": (relative_root / "original.ifc").as_posix(),
        "damaged_ifc": (relative_root / "damaged.ifc").as_posix(),
        "repaired_ifc": (relative_root / "repaired.ifc").as_posix(),
        "report": (relative_root / "REPORT.md").as_posix(),
        "files": (relative_root / "FILES.json").as_posix(),
    }


def _default_validator_runner(
    command: Sequence[str], *, cwd: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _validate_subprocess(
    collection_root: Path,
    *,
    validator_runner: Callable[..., subprocess.CompletedProcess[str]],
    candidate_only: bool,
) -> dict[str, Any]:
    command = (sys.executable, str(VALIDATOR), "--root", str(collection_root), "--json")
    completed = validator_runner(command, cwd=ROOT)
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as error:
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED") from error
    if not isinstance(payload, dict):
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED")
    try:
        proof_validation_schema = _read(PROOF_VALIDATION_SCHEMA)
        Draft202012Validator.check_schema(proof_validation_schema)
        Draft202012Validator(proof_validation_schema).validate(payload)
    except Exception as error:
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED") from error
    cases = payload.get("cases")
    case_ids = {
        str(item.get("case_id"))
        for item in cases or ()
        if isinstance(item, Mapping)
    }
    common_pass = (
        completed.returncode == 0
        and payload.get("status") == "passed"
        and payload.get("errors") == []
        and isinstance(cases, list)
    )
    if candidate_only:
        common_pass = bool(
            common_pass
            and payload.get("case_count") == 2
            and payload.get("independently_recomputed_case_count") == 2
            and payload.get("legacy_unverifiable_case_count") == 0
            and case_ids == set(PROOF_CASE_IDS.values())
            and len(cases) == 2
            and all(
                item.get("provider_evidence_mode") == LIVE_EVIDENCE_MODE
                and item.get("live_transcript_status") == "strict_recomputed"
                and item.get("property_authority_coverage")
                == "strict_stage_1_5_recomputed"
                and int(item.get("property_claim_count", 0)) >= 1
                and item.get("current_property_acceptance_eligible") is True
                for item in cases
            )
        )
    else:
        manifest = _read(collection_root / "manifest.json")
        cases_by_id = {
            str(item.get("case_id")): item
            for item in cases
            if isinstance(item, Mapping)
        }
        required_property_cases = [
            cases_by_id.get(case_id) for case_id in PROOF_CASE_IDS.values()
        ]
        common_pass = bool(
            common_pass
            and payload.get("case_count") == manifest.get("case_count")
            and set(PROOF_CASE_IDS.values()).issubset(case_ids)
            and all(
                isinstance(item, Mapping)
                and item.get("property_authority_coverage")
                == "strict_stage_1_5_recomputed"
                and int(item.get("property_claim_count", 0)) >= 1
                and item.get("current_property_acceptance_eligible") is True
                for item in required_property_cases
            )
        )
    if not common_pass:
        raise ValueError("LIVE_CANDIDATE_VALIDATION_FAILED")
    return payload


def _resolve_source_root(run_root: Path | str) -> Path:
    requested = Path(run_root).resolve()
    if (requested / "live-uat-result.json").is_file():
        return requested
    candidates = sorted(
        path.parent
        for path in requested.glob("uat-*/live-uat-result.json")
        if path.is_file()
    )
    if not candidates:
        raise FileNotFoundError(requested / "live-uat-result.json")
    return candidates[-1]


def curate(
    run_root: Path | str = DEFAULT_OUTPUT,
    proof_root: Path | str = DEFAULT_PROOF_ROOT,
    *,
    validator_runner: Callable[..., subprocess.CompletedProcess[str]] = _default_validator_runner,
) -> dict[str, Any]:
    """Stage, independently validate, then atomically install two live cases."""

    source_root = _resolve_source_root(run_root)
    destination = Path(proof_root).resolve()
    live_result_path = source_root / "live-uat-result.json"
    result = _read(live_result_path)
    audit = audit_live_uat_result(result)
    if _path_sha256(SOURCE) != FROZEN_SOURCE_SHA256:
        raise ValueError("LIVE_FROZEN_SOURCE_DRIFT")
    destination.mkdir(parents=True, exist_ok=True)
    collection_path = destination / "manifest.json"
    collection = _read(collection_path)
    prior_cases = collection.get("cases")
    if not isinstance(prior_cases, list):
        raise ValueError("LIVE_PROOF_COLLECTION_INVALID")
    prior_ids = {str(item.get("case_id")) for item in prior_cases if isinstance(item, Mapping)}
    if prior_ids & set(PROOF_CASE_IDS.values()):
        raise ValueError("LIVE_PROOF_CASE_ALREADY_EXISTS")
    with tempfile.TemporaryDirectory(
        prefix="phase12-live-proof-", dir=destination.parent
    ) as temporary:
        stage_root = Path(temporary) / "candidate"
        stage_root.mkdir()
        entries = [
            _stage_case(stage_root, source_root, result, case_id)
            for case_id in SUCCESS_CASE_IDS
        ]
        _write(
            stage_root / "manifest.json",
            {
                "schema_version": "text2ifc/ifc-repair-success-collection/0.1",
                "case_count": 2,
                "cases": entries,
            },
        )
        _validate_subprocess(
            stage_root,
            validator_runner=validator_runner,
            candidate_only=True,
        )
        installed: list[Path] = []
        original_manifest = collection_path.read_bytes()
        try:
            for entry in entries:
                relative = Path(str(entry["files"])).parent
                target = destination / relative
                if target.exists():
                    raise ValueError("LIVE_PROOF_CASE_ALREADY_EXISTS")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(stage_root / relative, target)
                installed.append(target)
            updated = dict(collection)
            updated["cases"] = [*prior_cases, *entries]
            updated["case_count"] = len(updated["cases"])
            temporary_manifest = collection_path.with_suffix(".json.tmp")
            _write(temporary_manifest, updated)
            os.replace(temporary_manifest, collection_path)
            _validate_subprocess(
                destination,
                validator_runner=validator_runner,
                candidate_only=False,
            )
        except Exception:
            for target in reversed(installed):
                shutil.rmtree(target)
            collection_path.write_bytes(original_manifest)
            raise
    return {
        "schema_version": "text2ifc/phase12-live-proof-curation/0.1",
        "status": "passed",
        "proof_root": destination.as_posix(),
        "source_run_root": source_root.as_posix(),
        "case_ids": list(PROOF_CASE_IDS.values()),
        "program_guard_curated": False,
        "transcript_audit": audit,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Curate genuine Phase 12 live structural Proof."
    )
    parser.add_argument("--run-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--proof-root", type=Path, default=DEFAULT_PROOF_ROOT)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    payload = curate(args.run_root, args.proof_root)
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"status={payload['status']} cases={len(payload['case_ids'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
