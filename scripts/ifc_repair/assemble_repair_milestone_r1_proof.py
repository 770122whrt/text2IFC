"""Assemble one genuine R1 execution run into the existing Proof 0.3 contract.

This module is intentionally an evidence copier/indexer.  It does not score a
case, repair an IFC, or replace the independent validator.  The output is
accepted only when ``validate_r1_proof_collection`` independently reopens and
recomputes every frozen case.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    from scripts.ifc_repair.validate_success_cases import (
        validate_r1_proof_collection,
    )
except ModuleNotFoundError:  # Direct script execution.
    from validate_success_cases import validate_r1_proof_collection


ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = (
    ROOT / "docs/validation/repair-milestone-r1/repair-proof-profiles.json"
)
FREEZE_PATH = (
    ROOT / "docs/validation/repair-milestone-r1/repair-acceptance-freeze.json"
)
EXECUTION_RESULT_NAME = "r1-execution-result.json"
PROVENANCE_NAMESPACE = "repair-milestone-r1"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_ref(path: Path) -> str:
    return "sha256:" + _sha256(path)


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def validate_execution_result(
    execution: Mapping[str, Any],
    *,
    expected_order: Iterable[str] | None = None,
) -> list[Mapping[str, Any]]:
    """Require one complete, ordered and genuine runner result."""

    order = list(
        expected_order
        if expected_order is not None
        else (
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
        )
    )
    raw_cases = execution.get("cases")
    cases = (
        [item for item in raw_cases if isinstance(item, Mapping)]
        if isinstance(raw_cases, list)
        else []
    )
    if (
        execution.get("schema_version")
        != "text2ifc/repair-milestone-r1-execution-result/0.1"
        or execution.get("status") != "passed"
        or int(execution.get("case_count", -1)) != len(order)
        or len(cases) != len(order)
    ):
        raise ValueError("R1_ASSEMBLER_EXECUTION_NOT_PASSED")
    if list(execution.get("execution_order") or ()) != order or [
        str(item.get("case_id") or "") for item in cases
    ] != order:
        raise ValueError("R1_ASSEMBLER_EXECUTION_ORDER")
    run_ids: list[str] = []
    for item in cases:
        final = item.get("final")
        run_id = str(final.get("run_id") or "") if isinstance(final, Mapping) else ""
        if (
            item.get("status") != "passed"
            or item.get("contract_pass") is not True
            or item.get("synthetic_fallback_used") is not False
            or not run_id
        ):
            raise ValueError(
                f"R1_ASSEMBLER_CASE_NOT_PASSED:{item.get('case_id')}"
            )
        run_ids.append(run_id)
    if len(set(run_ids)) != len(run_ids):
        raise ValueError("R1_ASSEMBLER_RUN_ID_REUSE")
    attempts = sum(
        len(item.get("attempts") or ())
        for item in cases
        if isinstance(item.get("attempts"), list)
    )
    if int(execution.get("transport_calls", -1)) != attempts:
        raise ValueError("R1_ASSEMBLER_TRANSPORT_CALL_COUNT")
    return cases


def build_terminal_record(
    *,
    case_id: str,
    profile: Mapping[str, Any],
    state: Mapping[str, Any],
    case_result: Mapping[str, Any],
    source_relative: str,
    source_sha256: str,
) -> dict[str, Any]:
    """Derive the existing terminal/0.1 record from immutable run state."""

    final = case_result.get("final")
    if not isinstance(final, Mapping):
        raise ValueError(f"R1_ASSEMBLER_FINAL:{case_id}")
    if (
        final.get("run_id") != state.get("run_id")
        or str(state.get("source", {}).get("sha256") or "") != source_sha256
    ):
        raise ValueError(f"R1_ASSEMBLER_STATE_BINDING:{case_id}")
    terminal_class = str(profile.get("terminal_class") or "")
    document: dict[str, Any] = {
        "schema_version": "text2ifc/ifc-repair-proof-terminal/0.1",
        "case_id": case_id,
        "terminal_class": terminal_class,
        "source": {
            "path": source_relative,
            "sha256_before": source_sha256,
            "sha256_after": source_sha256,
            "unchanged": True,
        },
        "resume_success": terminal_class
        != "UNSUPPORTED_ATOMIC_GUARD",
    }
    if terminal_class == "SUCCESS":
        if (
            state.get("stage") != "succeeded"
            or final.get("complete_repair_success") is not True
            or final.get("successful_artifact_publishable") is not True
        ):
            raise ValueError(f"R1_ASSEMBLER_SUCCESS_TERMINAL:{case_id}")
        return document

    expectation = profile.get("terminal_expectation")
    expectation = dict(expectation) if isinstance(expectation, Mapping) else {}
    if terminal_class == "INADMISSIBLE_VALUE_OR_CLARIFICATION":
        initial = final.get("initial")
        if not isinstance(initial, Mapping):
            raise ValueError("R1_ASSEMBLER_M1_INITIAL")
        document["initial_stop"] = {
            "status": "clarification_required",
            "reason_code": str(initial.get("reason_code") or ""),
            "stage2_attempts": 0,
            "apply_attempts": 0,
            "published_outputs": [],
            **expectation,
        }
        return document

    if terminal_class == "CLARIFICATION_THEN_SUCCESS":
        stops = [
            item
            for item in state.get("transitions", ())
            if isinstance(item, Mapping)
            and item.get("to_stage") == "clarification_required"
            and isinstance(item.get("clarification"), Mapping)
        ]
        if len(stops) != 1:
            raise ValueError("R1_ASSEMBLER_H3_CLARIFICATION")
        clarification = stops[0]["clarification"]
        offered = [
            f"{item.get('ifc_class')}:{item.get('public_id')}"
            for item in clarification.get("candidates", ())
            if isinstance(item, Mapping)
            and item.get("ifc_class")
            and item.get("public_id")
        ]
        selected = str(expectation.get("selected_identity") or "")
        if not offered or selected not in offered:
            raise ValueError("R1_ASSEMBLER_H3_OFFERED_IDENTITY")
        document["initial_stop"] = {
            "status": "clarification_required",
            "reason_code": str(
                clarification.get("reason_code") or "ambiguous_target"
            ),
            "stage2_attempts": 0,
            "apply_attempts": 0,
            "published_outputs": [],
            "offered_identities": offered,
            "selected_identity": selected,
            "lineage_id": f"run:{state['run_id']}",
            "resume_lineage_same": True,
        }
        return document

    if terminal_class == "UNSUPPORTED_ATOMIC_GUARD":
        guard = final.get("program_guard_evidence")
        if (
            state.get("stage") != "unsupported"
            or final.get("complete_repair_success") is not False
            or final.get("successful_artifact_publishable") is not False
            or not isinstance(guard, Mapping)
            or guard.get("candidate_output_paths") != []
            or guard.get("mutation_attempted") is not False
            or guard.get("source_sha256_before") != source_sha256
            or guard.get("source_sha256_after") != source_sha256
            or guard.get("source_unchanged") is not True
            or guard.get("stage2_attempts") != 0
        ):
            raise ValueError("R1_ASSEMBLER_H4_GUARD")
        document["initial_stop"] = {
            "status": "unsupported",
            "reason_code": str(state.get("reason_code") or ""),
            "stage2_attempts": 0,
            "apply_attempts": 0,
            "published_outputs": [],
            **expectation,
        }
        return document
    raise ValueError(f"R1_ASSEMBLER_TERMINAL_CLASS:{terminal_class}")


def build_collection_case(
    *,
    case_id: str,
    terminal_class: str,
    case_root: str,
    source_ifc: str | None = None,
    repaired_ifc: str | None = None,
    changeset: str | None = None,
    application: str | None = None,
    authority_replay: Mapping[str, str] | None = None,
    inadmissible_value_replay: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build one collection/0.2 row without inventing no-output artifacts."""

    item: dict[str, Any] = {
        "case_id": case_id,
        "status": "accepted",
        "terminal_class": terminal_class,
        "provider_evidence_mode": "live",
        "case_root": case_root,
        "files": f"{case_root}/FILES.json",
        "report": f"{case_root}/REPORT.md",
        "terminal_record": f"{case_root}/terminal.json",
    }
    optional = {
        "source_ifc": source_ifc,
        "repaired_ifc": repaired_ifc,
        "changeset": changeset,
        "application": application,
    }
    item.update({key: value for key, value in optional.items() if value})
    if authority_replay:
        item["authority_replay"] = dict(authority_replay)
    if inadmissible_value_replay:
        item["inadmissible_value_replay"] = dict(
            inadmissible_value_replay
        )
    return item


def _bound_artifacts(state: Mapping[str, Any], name: str) -> list[str]:
    paths: list[str] = []
    for transition in state.get("transitions", ()):
        if not isinstance(transition, Mapping):
            continue
        payload = transition.get("stage_payload")
        binding = payload.get(name) if isinstance(payload, Mapping) else None
        if isinstance(binding, Mapping) and binding.get("path"):
            paths.append(str(binding["path"]))
    return paths


def _result_artifact_path(run_path: Path, state: Mapping[str, Any], key: str) -> Path:
    value = state.get("result_artifacts", {}).get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"R1_ASSEMBLER_RESULT_ARTIFACT:{key}")
    path = (run_path / value).resolve()
    path.relative_to(run_path.resolve())
    if not path.is_file():
        raise ValueError(f"R1_ASSEMBLER_RESULT_ARTIFACT_MISSING:{key}")
    return path


def _publication_evidence(manifest_path: Path, run_path: Path) -> Path:
    manifest = _read_json(manifest_path)
    matches = [
        item
        for item in manifest.get("artifacts", ())
        if isinstance(item, Mapping) and item.get("role") == "public_evidence"
    ]
    if len(matches) != 1:
        raise ValueError("R1_ASSEMBLER_PUBLIC_EVIDENCE")
    path = (run_path / str(matches[0].get("path") or "")).resolve()
    path.relative_to(run_path.resolve())
    if not path.is_file():
        raise ValueError("R1_ASSEMBLER_PUBLIC_EVIDENCE_MISSING")
    return path


def _specific_roles(
    *,
    case_root: Path,
    source: Path,
    terminal: Path,
    report: Path,
    source_manifest: Path,
    request: Path,
    initial_request: Path | None,
    answer: Path | None,
    boundary: Path,
    live_result: Path,
    case_result: Path,
    state_path: Path,
    final_intent: Path,
    final_resolution: Path | None,
    changeset: Path | None,
    provider_draft: Path | None,
    prompt_selection: Path | None,
    semantic_manifest: Path | None,
    repaired: Path | None,
    publication_manifest: Path,
    publication_evaluation: Path,
    publication_evidence: Path,
    application: Path | None,
) -> dict[str, str]:
    pairs: list[tuple[str, Path | None]] = [
        ("repair_input_ifc", source),
        ("proof_terminal_record", terminal),
        ("proof_report", report),
        ("source_run_manifest", source_manifest),
        ("user_request", request),
        ("initial_user_request", initial_request),
        ("clarification_answer", answer),
        ("production_input_boundary", boundary),
        ("live_provider_result", live_result),
        ("live_provider_case_result", case_result),
        ("runtime_state", state_path),
        ("stage1_repair_intent", final_intent),
        ("deterministic_target_resolution", final_resolution),
        ("bound_changeset", changeset),
        ("live_provider_draft", provider_draft),
        ("live_prompt_profile_selection", prompt_selection),
        ("semantic_manifests", semantic_manifest),
        ("published_repair_output", repaired),
        ("production_publication_manifest", publication_manifest),
        ("production_evaluation", publication_evaluation),
        ("production_publication_evidence", publication_evidence),
        ("application_result", application),
    ]
    roles: dict[str, str] = {}
    for role, path in pairs:
        if path is None:
            continue
        relative = _relative(path, case_root)
        if relative in roles:
            raise ValueError(f"R1_ASSEMBLER_DUPLICATE_ROLE_PATH:{relative}")
        roles[relative] = role
    return roles


def _write_files_index(case_root: Path, roles: Mapping[str, str]) -> None:
    files = sorted(
        path
        for path in case_root.rglob("*")
        if path.is_file() and path.name != "FILES.json"
    )
    entries: list[dict[str, Any]] = []
    used_roles = set(roles.values())
    generic_index = 1
    for path in files:
        relative = _relative(path, case_root)
        role = roles.get(relative)
        if role is None:
            while True:
                candidate = f"r1_retained_artifact_{generic_index:04d}"
                generic_index += 1
                if candidate not in used_roles:
                    role = candidate
                    used_roles.add(candidate)
                    break
        entries.append(
            {
                "path": relative,
                "role": role,
                "sha256": _sha256_ref(path),
                "size_bytes": path.stat().st_size,
            }
        )
    _write_json(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
            "case_id": case_root.name,
            "files": entries,
        },
    )


def _assemble_case(
    *,
    stage: Path,
    raw_root: Path,
    execution: Mapping[str, Any],
    result_case: Mapping[str, Any],
    profile: Mapping[str, Any],
    frozen: Mapping[str, Any],
    model: Mapping[str, Any],
) -> dict[str, Any]:
    case_id = str(result_case["case_id"])
    case_root = stage / "cases" / case_id
    case_root.mkdir(parents=True)
    final = result_case["final"]
    run_id = str(final["run_id"])
    raw_case_root = raw_root / "cases" / case_id
    raw_run = raw_case_root / "runtime" / "runs" / run_id
    if not raw_run.is_dir():
        raise ValueError(f"R1_ASSEMBLER_RAW_RUN_MISSING:{case_id}")
    copied_run = case_root / "runtime" / "runs" / run_id
    shutil.copytree(
        raw_run,
        copied_run,
        ignore=shutil.ignore_patterns("staging", ".transition.lock"),
    )
    state_path = copied_run / "state.json"
    state = _read_json(state_path)

    source = case_root / "source.ifc"
    source_authority = (ROOT / str(model["path"])).resolve()
    if (
        not source_authority.is_file()
        or _sha256(source_authority) != str(model["sha256"])
        or source_authority.stat().st_size != int(model["size_bytes"])
    ):
        raise ValueError(f"R1_ASSEMBLER_SOURCE_AUTHORITY:{case_id}")
    shutil.copy2(source_authority, source)
    source_sha = _sha256_ref(source)

    request = case_root / "request.txt"
    initial_request: Path | None = None
    answer: Path | None = None
    initial_text = str(frozen["request"])
    resume = frozen.get("resume")
    effective_text = initial_text
    if resume is not None:
        initial_request = case_root / "initial-request.txt"
        answer = case_root / "clarification-answer.txt"
        _write_text(initial_request, initial_text)
        _write_text(answer, str(resume))
        if case_id == "M1":
            effective_text = f"{initial_text}\n补充说明：{str(resume).strip()}"
    _write_text(request, effective_text)

    final_intent_rel = _bound_artifacts(state, "intent")[-1]
    final_intent = copied_run / final_intent_rel
    resolution_refs = _bound_artifacts(state, "resolution")
    changeset_refs = _bound_artifacts(state, "changeset")
    final_resolution = copied_run / resolution_refs[-1] if resolution_refs else None
    changeset = copied_run / changeset_refs[-1] if changeset_refs else None

    publication_manifest = _result_artifact_path(copied_run, state, "manifest")
    publication_evaluation = _result_artifact_path(
        copied_run, state, "evaluation"
    )
    publication_evidence = _publication_evidence(
        publication_manifest, copied_run
    )
    repaired: Path | None = None
    application: Path | None = None
    provider_draft: Path | None = None
    prompt_selection: Path | None = None
    semantic_manifest: Path | None = None
    changeset_document: Mapping[str, Any] | None = None
    operation_count = 0
    if changeset is not None:
        changeset_document = _read_json(changeset)
        operation_count = len(
            [
                item
                for item in changeset_document.get("operations", ())
                if isinstance(item, Mapping)
            ]
        )
        provider_draft = copied_run / "changeset/provider-draft.json"
        prompt_selection = copied_run / "changeset/prompt-profile-selection.json"
        semantic_manifest = copied_run / str(
            changeset_document.get("semantic_manifest_ref") or ""
        )
        repaired = _result_artifact_path(copied_run, state, "successful_ifc")
        evidence_document = _read_json(publication_evidence)
        public_evidence = evidence_document.get("evidence")
        if not isinstance(public_evidence, Mapping) or not isinstance(
            public_evidence.get("application"), Mapping
        ):
            raise ValueError(f"R1_ASSEMBLER_APPLICATION:{case_id}")
        application = case_root / "application.json"
        _write_json(application, public_evidence["application"])

    live_result = case_root / "provider-evidence/live-result.json"
    live_document = json.loads(json.dumps(dict(execution), ensure_ascii=False))
    live_document.update(
        {
            "evidence_mode": "live",
            "provider_evidence_mode": "live",
            "execution_mode": "production_live",
            "synthetic_fallback_used": False,
        }
    )
    _write_json(live_result, live_document)
    copied_case_result = case_root / "provider-evidence/case-result.json"
    shutil.copy2(raw_case_root / "case-result.json", copied_case_result)

    boundary = case_root / "production-boundary.json"
    final_intent_document = _read_json(final_intent)
    _write_json(
        boundary,
        {
            "schema_version": "text2ifc/production-input-boundary/0.2",
            "entrypoint": "run_repair_milestone_r1.py",
            "ifc_inputs": ["damaged_ifc_path"],
            "request_inputs": ["public_request_bundle"],
            "original_ifc_supplied": False,
            "mutation_manifest_supplied": False,
            "deleted_object_ids_supplied": False,
            "private_comparator_available_during_repair": False,
            "damaged_ifc_sha256": source_sha,
            "request_sha256": str(final_intent_document["source_request_hash"]),
            "resolved_target_count": operation_count,
        },
    )

    source_manifest = case_root / "manifest.json"
    live_contract: dict[str, Any] = {
        "case_id": case_id,
        "live_uat_result_path": _relative(live_result, case_root),
        "live_uat_result_sha256": _sha256_ref(live_result),
    }
    if provider_draft is not None and prompt_selection is not None:
        live_contract.update(
            {
                "provider_draft_path": _relative(provider_draft, case_root),
                "provider_draft_sha256": _sha256_ref(provider_draft),
                "prompt_profile_selection_path": _relative(
                    prompt_selection, case_root
                ),
                "prompt_profile_selection_sha256": _sha256_ref(
                    prompt_selection
                ),
            }
        )
    _write_json(
        source_manifest,
        {
            "schema_version": "text2ifc/phase12-live-proof-source/0.1",
            "case_id": case_id,
            "status": "passed",
            "provider": "deepseek-openai-compatible",
            "model": "deepseek-v4-flash",
            "provider_evidence_mode": "live",
            "synthetic_fallback_used": False,
            "operation_count": operation_count,
            "source": {
                "path": str(model["path"]),
                "schema": str(model["schema"]),
                "sha256": source_sha,
                "size_bytes": source.stat().st_size,
            },
            "live_contract": live_contract,
        },
    )

    terminal_path = case_root / "terminal.json"
    terminal = build_terminal_record(
        case_id=case_id,
        profile=profile,
        state=state,
        case_result=result_case,
        source_relative="source.ifc",
        source_sha256=source_sha,
    )
    _write_json(terminal_path, terminal)
    report = case_root / "REPORT.md"
    _write_text(
        report,
        "\n".join(
            (
                f"# Repair Milestone R1 Proof — {case_id}",
                "",
                f"- terminal class: `{profile['terminal_class']}`",
                f"- runtime run: `{run_id}`",
                f"- provider attempts: `{len(result_case.get('attempts') or ())}`",
                f"- published repaired IFC: `{'yes' if repaired else 'no (unsupported atomic guard)'}`",
                "- acceptance authority: independent Proof 0.3 validator",
            )
        ),
    )

    if case_id == "M1":
        initial_intent_rel = _bound_artifacts(state, "intent")[0]
        initial_intent = _read_json(copied_run / initial_intent_rel)
        claim_root = copied_run / "property-resolution/operation-001/claim-001"
        property_intents = initial_intent["operations"][0]["property_intents"]
        _write_json(claim_root / "claim.json", property_intents[0])

    roles = _specific_roles(
        case_root=case_root,
        source=source,
        terminal=terminal_path,
        report=report,
        source_manifest=source_manifest,
        request=request,
        initial_request=initial_request,
        answer=answer,
        boundary=boundary,
        live_result=live_result,
        case_result=copied_case_result,
        state_path=state_path,
        final_intent=final_intent,
        final_resolution=final_resolution,
        changeset=changeset,
        provider_draft=provider_draft,
        prompt_selection=prompt_selection,
        semantic_manifest=semantic_manifest,
        repaired=repaired,
        publication_manifest=publication_manifest,
        publication_evaluation=publication_evaluation,
        publication_evidence=publication_evidence,
        application=application,
    )
    _write_files_index(case_root, roles)

    case_rel = _relative(case_root, stage)
    kwargs: dict[str, Any] = {}
    if repaired is not None and changeset is not None and application is not None:
        assert final_resolution is not None and semantic_manifest is not None
        kwargs.update(
            {
                "source_ifc": _relative(source, stage),
                "repaired_ifc": _relative(repaired, stage),
                "changeset": _relative(changeset, stage),
                "application": _relative(application, stage),
                "authority_replay": {
                    "intent": _relative(final_intent, stage),
                    "resolution": _relative(final_resolution, stage),
                    "semantic_manifest": _relative(semantic_manifest, stage),
                    "source_manifest": _relative(source_manifest, stage),
                    "evidence_root": case_rel,
                }
                if int(profile.get("property_claim_count", 0))
                else None,
            }
        )
    if case_id == "M1":
        claim_root = copied_run / "property-resolution/operation-001/claim-001"
        attempt_root = claim_root / "provider/attempt-001"
        kwargs["inadmissible_value_replay"] = {
            "query": _relative(claim_root / "query.json", stage),
            "candidate_set": _relative(claim_root / "candidate-set.json", stage),
            "decision": _relative(attempt_root / "parsed-response.json", stage),
            "decision_trace": _relative(attempt_root / "trace.json", stage),
            "claim": _relative(claim_root / "claim.json", stage),
            "retained_admission": _relative(
                claim_root / "admissibility-provider.json", stage
            ),
        }
    return build_collection_case(
        case_id=case_id,
        terminal_class=str(profile["terminal_class"]),
        case_root=case_rel,
        **kwargs,
    )


def assemble_r1_proof(
    *,
    run_root: Path | str,
    destination_root: Path | str,
) -> dict[str, Any]:
    """Copy/index a complete runner output and validate it before publication."""

    raw_root = Path(run_root).resolve()
    destination = Path(destination_root).resolve()
    if destination.exists():
        raise ValueError("R1_ASSEMBLER_DESTINATION_NOT_EMPTY")
    execution = _read_json(raw_root / EXECUTION_RESULT_NAME)
    profiles = _read_json(PROFILE_PATH)
    freeze = _read_json(FREEZE_PATH)
    expected_order = [str(value) for value in profiles["execution_order"]]
    cases = validate_execution_result(execution, expected_order=expected_order)
    profiles_by_id = {
        str(item["case_id"]): item
        for item in profiles["cases"]
        if isinstance(item, Mapping)
    }
    frozen_by_id = {
        str(item["case_id"]): item
        for item in freeze["cases"]
        if isinstance(item, Mapping)
    }
    models_by_id = {
        str(item["model_id"]): item
        for item in freeze["models"]
        if isinstance(item, Mapping)
    }
    if set(profiles_by_id) != set(expected_order) or set(frozen_by_id) != set(
        expected_order
    ):
        raise ValueError("R1_ASSEMBLER_FREEZE_CASE_SET")

    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}-assemble-", dir=destination.parent
        )
    ).resolve()
    try:
        shutil.copy2(PROFILE_PATH, stage / PROFILE_PATH.name)
        shutil.copy2(FREEZE_PATH, stage / FREEZE_PATH.name)
        collection_cases = []
        for result_case in cases:
            case_id = str(result_case["case_id"])
            frozen = frozen_by_id[case_id]
            model = models_by_id.get(str(frozen.get("model_id") or ""))
            if not isinstance(model, Mapping):
                raise ValueError(f"R1_ASSEMBLER_MODEL:{case_id}")
            collection_cases.append(
                _assemble_case(
                    stage=stage,
                    raw_root=raw_root,
                    execution=execution,
                    result_case=result_case,
                    profile=profiles_by_id[case_id],
                    frozen=frozen,
                    model=model,
                )
            )
        manifest = {
            "schema_version": "text2ifc/ifc-repair-proof-collection/0.2",
            "provenance_namespace": PROVENANCE_NAMESPACE,
            "profile": PROFILE_PATH.name,
            "case_count": len(collection_cases),
            "cases": collection_cases,
        }
        _write_json(stage / "manifest.json", manifest)
        validation = validate_r1_proof_collection(stage).to_dict()
        if validation.get("status") != "passed" or validation.get("errors"):
            raise ValueError(
                "R1_ASSEMBLER_VALIDATION_FAILED:"
                + json.dumps(validation.get("errors"), ensure_ascii=False)
            )
        stage.replace(destination)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return {
        "schema_version": "text2ifc/repair-milestone-r1-proof-assembly/0.1",
        "status": "assembled",
        "source_run": raw_root.as_posix(),
        "destination_root": destination.as_posix(),
        "case_ids": expected_order,
        "proof_validation": validation,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble one genuine R1 run into Proof collection 0.2."
    )
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--destination-root", type=Path, required=True)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = assemble_r1_proof(
        run_root=args.run_root,
        destination_root=args.destination_root,
    )
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"status={result['status']} cases={len(result['case_ids'])} "
            f"destination={result['destination_root']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
