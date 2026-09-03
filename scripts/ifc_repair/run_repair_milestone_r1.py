"""Manifest-bound genuine runner for Repair Milestone R1.

The default command validates the frozen execution package without constructing
a Provider.  Genuine execution additionally requires both an authorized
manifest and an explicit authorization reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

R1_NATIVE_RUNTIME_BOOTSTRAP: dict[str, Any] | None = None
if __name__ == "__main__" and "--execute-genuine" in sys.argv:
    try:
        from text2ifc_knowledge.property_search import (
            prepare_local_embedding_native_runtime,
        )

        R1_NATIVE_RUNTIME_BOOTSTRAP = (
            prepare_local_embedding_native_runtime()
        )
    except Exception as error:
        R1_NATIVE_RUNTIME_BOOTSTRAP = {
            "status": "failed",
            "reason_code": (str(error) or type(error).__name__)[:256],
        }

import ifcopenshell

from scripts.ifc_repair import run_phase12_live_uat as live
from scripts.ifc_repair import curate_phase12_live_proof as live_curator
from scripts.ifc_repair import validate_success_cases as proof_validator
from text2ifc_agent.openai_compat import (
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_knowledge.property_runtime import (
    create_property_runtime_from_environment,
)
from text2ifc_ifc_repair.evaluation import EvaluationExecutionPolicy


DEFAULT_MANIFEST = (
    ROOT
    / "docs/validation/repair-milestone-r1/"
    "repair-r1-execution-manifest.json"
)
DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair-runs/repair-milestone-r1"
SCHEMA_VERSION = "text2ifc/repair-milestone-r1-execution-manifest/0.1"
AUTHORIZED_STATUS = "AUTHORIZED_FOR_GENUINE_EXECUTION"
PREPARED_STATUS = "PREPARED_AWAITING_GENUINE_AUTHORIZATION"
R1_CORRECTNESS_DEADLINE_SECONDS = 600.0
R1_PERFORMANCE_SLO_SECONDS = 180.0
R1_PERFORMANCE_SLO_BLOCKING = False
R1_RSS_LIMIT_BYTES = 4 * 1024**3


def _r1_evaluation_execution_policy() -> EvaluationExecutionPolicy:
    return EvaluationExecutionPolicy(
        deadline_seconds=R1_CORRECTNESS_DEADLINE_SECONDS,
        rss_limit_bytes=R1_RSS_LIMIT_BYTES,
    )


def _case_stop_reason(
    *,
    contract_pass: bool,
    execution_error: str | None,
) -> str | None:
    if execution_error is not None:
        return "R1_EXECUTION_DEFECT_STOP"
    if not contract_pass:
        return "R1_CASE_CONTRACT_STOP"
    return None


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("R1_EXECUTION_DOCUMENT_OBJECT_REQUIRED")
    return value


def _bound_repository_file(binding: Mapping[str, Any]) -> Path:
    path = (ROOT / str(binding.get("path") or "")).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError("R1_EXECUTION_BOUND_FILE_INVALID")
    if _sha256_path(path) != str(binding.get("sha256") or ""):
        raise ValueError("R1_EXECUTION_BOUND_FILE_HASH_MISMATCH")
    return path


def load_execution_manifest(
    manifest_path: Path | str = DEFAULT_MANIFEST,
) -> dict[str, Any]:
    """Validate the public execution authority without exposing evaluation Gold."""

    path = Path(manifest_path).resolve()
    document = _read_json(path)
    required = {
        "schema_version",
        "status",
        "acceptance_freeze",
        "proof_profiles",
        "provider",
        "execution_order",
        "resume_bindings",
        "production_input_policy",
        "stop_rules",
        "prerequisites",
    }
    if set(document) != required:
        raise ValueError("R1_EXECUTION_MANIFEST_KEYS_INVALID")
    if document["schema_version"] != SCHEMA_VERSION:
        raise ValueError("R1_EXECUTION_MANIFEST_VERSION_INVALID")
    if document["status"] not in {PREPARED_STATUS, AUTHORIZED_STATUS}:
        raise ValueError("R1_EXECUTION_MANIFEST_STATUS_INVALID")
    provider = document["provider"]
    if not isinstance(provider, Mapping) or (
        provider.get("provider"),
        provider.get("endpoint"),
        provider.get("model"),
        provider.get("thinking"),
        provider.get("evidence_mode"),
    ) != (
        "deepseek",
        "https://api.deepseek.com/chat/completions",
        "deepseek-v4-flash",
        "enabled",
        "live",
    ):
        raise ValueError("R1_EXECUTION_PROVIDER_CONTRACT_INVALID")

    freeze_path = _bound_repository_file(document["acceptance_freeze"])
    proof_profiles_path = _bound_repository_file(document["proof_profiles"])
    freeze = _read_json(freeze_path)
    order = [str(value) for value in document["execution_order"]]
    if order != [str(value) for value in freeze.get("execution_order", ())]:
        raise ValueError("R1_EXECUTION_ORDER_MISMATCH")

    model_documents = freeze.get("models")
    case_documents = freeze.get("cases")
    if not isinstance(model_documents, list) or not isinstance(case_documents, list):
        raise ValueError("R1_EXECUTION_FREEZE_SHAPE_INVALID")
    models = {str(item["model_id"]): dict(item) for item in model_documents}
    cases = [dict(item) for item in case_documents]
    if [str(item.get("case_id")) for item in cases] != order:
        raise ValueError("R1_EXECUTION_CASE_SET_MISMATCH")
    proof_profiles = _read_json(proof_profiles_path)
    profile_cases = proof_profiles.get("cases")
    if (
        proof_profiles.get("schema_version")
        != "text2ifc/ifc-repair-proof-profiles/0.1"
        or proof_profiles.get("provenance_namespace")
        != "repair-milestone-r1"
        or proof_profiles.get("execution_order") != order
        or not isinstance(profile_cases, list)
        or [str(item.get("case_id")) for item in profile_cases] != order
    ):
        raise ValueError("R1_EXECUTION_PROOF_PROFILES_INVALID")
    proof_profiles_by_case = {
        str(item["case_id"]): dict(item) for item in profile_cases
    }

    for model in models.values():
        model_path = (ROOT / str(model["path"])).resolve()
        if not model_path.is_relative_to(ROOT) or not model_path.is_file():
            raise ValueError("R1_EXECUTION_MODEL_MISSING")
        if model_path.stat().st_size != int(model["size_bytes"]):
            raise ValueError("R1_EXECUTION_MODEL_SIZE_MISMATCH")
        if _sha256_path(model_path) != str(model["sha256"]):
            raise ValueError("R1_EXECUTION_MODEL_HASH_MISMATCH")
        model["resolved_path"] = str(model_path)

    resume_bindings = document["resume_bindings"]
    if not isinstance(resume_bindings, Mapping) or not resume_bindings:
        raise ValueError("R1_EXECUTION_RESUME_BINDINGS_INVALID")
    public_cases: list[dict[str, Any]] = []
    for case in cases:
        case_id = str(case["case_id"])
        request = str(case["request"])
        if _sha256_bytes(request.encode("utf-8")) != str(case["request_sha256"]):
            raise ValueError("R1_EXECUTION_REQUEST_HASH_MISMATCH")
        model_id = str(case["model_id"])
        if model_id not in models:
            raise ValueError("R1_EXECUTION_CASE_MODEL_MISMATCH")
        expected = case.get("evaluation_only_expected")
        if not isinstance(expected, Mapping):
            raise ValueError("R1_EXECUTION_EXPECTED_OUTCOME_MISSING")
        outcome = str(
            expected.get("outcome") or expected.get("resume_outcome") or ""
        )
        initial_outcome = str(expected.get("initial_outcome") or "")
        if outcome == "unsupported_program_zero_mutation" and not (
            initial_outcome == "" or initial_outcome == outcome
        ):
            raise ValueError("R1_EXECUTION_EXPECTED_OUTCOME_INVALID")
        public_case = {
            "case_id": case_id,
            "model_id": model_id,
            "request": request,
            "request_sha256": str(case["request_sha256"]),
            "expected_outcome": outcome,
            "expect_program_guard": outcome
            == "unsupported_program_zero_mutation",
            "expect_resume": case_id in resume_bindings,
            "feedback": None,
            "feedback_kind": None,
            "source_path": models[model_id]["resolved_path"],
            "source_sha256": str(models[model_id]["sha256"]),
        }
        if case_id in resume_bindings:
            binding = resume_bindings[case_id]
            frozen_resume = str(case.get("resume") or "")
            if (
                _sha256_bytes(frozen_resume.encode("utf-8"))
                != str(binding.get("sha256") or "")
                or str(case.get("resume_sha256") or "")
                != str(binding.get("sha256") or "")
            ):
                raise ValueError("R1_EXECUTION_RESUME_HASH_MISMATCH")
            if binding["kind"] == "add_detail":
                if binding.get("detail") != frozen_resume:
                    raise ValueError("R1_EXECUTION_RESUME_DETAIL_MISMATCH")
                public_case["feedback"] = str(binding["detail"])
                public_case["feedback_kind"] = "add_detail"
            elif binding["kind"] == "select_candidate":
                if binding.get("public_answer") != frozen_resume:
                    raise ValueError("R1_EXECUTION_RESUME_ANSWER_MISMATCH")
                public_case["feedback"] = str(
                    binding["stable_public_identity"]
                )
                public_case["feedback_kind"] = "select_candidate"
            else:
                raise ValueError("R1_EXECUTION_RESUME_KIND_INVALID")
        public_cases.append(public_case)

    return {
        **document,
        "manifest_path": str(path),
        "manifest_sha256": _sha256_path(path),
        "freeze_path": str(freeze_path),
        "models": models,
        "cases": cases,
        "public_cases": public_cases,
        "proof_profiles_by_case": proof_profiles_by_case,
    }


def _case_contract_pass(
    expected_outcome: str,
    final: Mapping[str, Any],
    *,
    live_evidence_pass: bool,
    private_evidence_detected: bool,
    expect_resume: bool,
    artifact_predicate_pass: bool = True,
) -> bool:
    if (
        private_evidence_detected
        or not live_evidence_pass
        or not artifact_predicate_pass
    ):
        return False
    if expected_outcome == "unsupported_program_zero_mutation":
        return (
            final.get("status") == "unsupported"
            and final.get("reason_code") == "STRUCTURAL_ANALYSIS_UNSUPPORTED"
            and final.get("successful_artifact_publishable") is False
            and isinstance(final.get("program_guard_evidence"), Mapping)
            and final.get("program_guard_evidence").get(
                "mutation_attempted"
            )
            is False
        )
    strict = final.get("strict_reopen_verification")
    if not isinstance(strict, Mapping):
        return False
    return (
        final.get("status") == "succeeded"
        and final.get("complete_repair_success") is True
        and final.get("successful_artifact_publishable") is True
        and strict.get("status") == "passed"
        and strict.get("l0_pass") is True
        and strict.get("l1_pass") is True
        and strict.get("l2_pass") is True
        and (
            not expect_resume
            or final.get("clarification_answer_applied") is True
        )
    )


def _safe_run_artifact(run_root: Path, relative: str) -> Path:
    value = Path(relative)
    path = (run_root / value).resolve()
    if (
        not relative
        or value.is_absolute()
        or ".." in value.parts
        or not path.is_relative_to(run_root.resolve())
        or not path.is_file()
    ):
        raise ValueError("R1_ARTIFACT_PREDICATE_PATH_INVALID")
    return path


def _post_execution_predicate_audit(
    *,
    case_root: Path,
    source_path: Path | str,
    final: Mapping[str, Any],
    profile: Mapping[str, Any],
    predicate_auditor: Callable[..., list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Reopen retained outputs and apply frozen predicates after Provider use."""

    predicates = profile.get("artifact_predicates")
    if not isinstance(predicates, list):
        return {
            "status": "failed",
            "reason_code": "R1_ARTIFACT_PREDICATE_PROFILE_INVALID",
            "predicate_results": [],
        }
    if not predicates:
        return {
            "status": "not_applicable",
            "reason_code": None,
            "predicate_results": [],
        }
    try:
        run_id = str(final.get("run_id") or "")
        run_root = (
            case_root / "runtime" / "runs" / run_id
        ).resolve()
        expected_runs_root = (case_root / "runtime" / "runs").resolve()
        if (
            not run_id
            or not run_root.is_relative_to(expected_runs_root)
            or not run_root.is_dir()
        ):
            raise ValueError("R1_ARTIFACT_PREDICATE_RUN_INVALID")
        state = _read_json(run_root / "state.json")
        changeset_bindings = []
        for transition in state.get("transitions", ()):
            payload = (
                transition.get("stage_payload")
                if isinstance(transition, Mapping)
                else None
            )
            binding = (
                payload.get("changeset")
                if isinstance(payload, Mapping)
                else None
            )
            if isinstance(binding, Mapping):
                changeset_bindings.append(binding)
        if len(changeset_bindings) != 1:
            raise ValueError("R1_ARTIFACT_PREDICATE_CHANGESET_BINDING")
        changeset_binding = changeset_bindings[0]
        if (
            set(changeset_binding)
            != {"path", "schema_version", "sha256"}
            or changeset_binding.get("schema_version")
            != "text2ifc/ifc-repair-changeset/0.1"
        ):
            raise ValueError("R1_ARTIFACT_PREDICATE_CHANGESET_BINDING")
        changeset_path = _safe_run_artifact(
            run_root, str(changeset_binding.get("path") or "")
        )
        if str(changeset_binding.get("sha256") or "").removeprefix(
            "sha256:"
        ) != _sha256_path(changeset_path):
            raise ValueError("R1_ARTIFACT_PREDICATE_CHANGESET_HASH")

        artifacts = final.get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise ValueError("R1_ARTIFACT_PREDICATE_TERMINAL_BINDING")
        manifest_path = _safe_run_artifact(
            run_root, str(artifacts.get("manifest") or "")
        )
        manifest = _read_json(manifest_path)
        entries = manifest.get("artifacts")
        if (
            manifest.get("schema_version")
            != "text2ifc/ifc-repair-artifact-manifest/0.1"
            or not isinstance(entries, list)
        ):
            raise ValueError("R1_ARTIFACT_PREDICATE_MANIFEST")
        by_role: dict[str, Path] = {}
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise ValueError("R1_ARTIFACT_PREDICATE_MANIFEST")
            role = str(entry.get("role") or "")
            artifact = _safe_run_artifact(
                run_root, str(entry.get("path") or "")
            )
            if (
                role in by_role
                or str(entry.get("sha256") or "").removeprefix("sha256:")
                != _sha256_path(artifact)
                or int(entry.get("size_bytes", -1)) != artifact.stat().st_size
            ):
                raise ValueError("R1_ARTIFACT_PREDICATE_MANIFEST")
            by_role[role] = artifact
        repaired_path = by_role.get("successful_ifc")
        evidence_path = by_role.get("public_evidence")
        if (
            repaired_path is None
            or evidence_path is None
            or repaired_path
            != _safe_run_artifact(
                run_root, str(artifacts.get("successful_ifc") or "")
            )
        ):
            raise ValueError("R1_ARTIFACT_PREDICATE_TERMINAL_BINDING")
        evidence = _read_json(evidence_path)
        evidence_payload = evidence.get("evidence")
        application = (
            evidence_payload.get("application")
            if isinstance(evidence_payload, Mapping)
            else None
        )
        if not isinstance(application, Mapping):
            raise ValueError("R1_ARTIFACT_PREDICATE_APPLICATION")
        source = Path(source_path).resolve()
        if not source.is_file():
            raise ValueError("R1_ARTIFACT_PREDICATE_SOURCE")
        auditor = (
            proof_validator.audit_r1_artifact_predicates
            if predicate_auditor is None
            else predicate_auditor
        )
        predicate_results = auditor(
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired_path)),
            changeset=_read_json(changeset_path),
            application=dict(application),
            predicates=predicates,
        )
        return {
            "status": "passed",
            "reason_code": None,
            "predicate_results": predicate_results,
        }
    except Exception as error:
        reason = str(error).split(":", 1)[0] or type(error).__name__
        return {
            "status": "failed",
            "reason_code": reason[:128],
            "predicate_results": [],
        }


def _retained_preflight_artifact_overrides(
    preflight_path: Path,
) -> dict[str, Path]:
    retention_path = preflight_path.parent / "retained-artifacts.json"
    if not retention_path.is_file():
        return {}
    retention = _read_json(retention_path)
    if (
        retention.get("schema_version")
        != "text2ifc/phase12-live-proof-preflight-retention/0.1"
        or retention.get("preflight_sha256")
        != f"sha256:{_sha256_path(preflight_path)}"
        or not isinstance(retention.get("retained"), list)
    ):
        raise ValueError("R1_PLAN07_PREFLIGHT_RETENTION_INVALID")
    overrides: dict[str, Path] = {}
    for item in retention["retained"]:
        if not isinstance(item, Mapping) or item.get("evidence_kind") != (
            "declared_artifact"
        ):
            continue
        reference = str(item.get("source_reference") or "")
        relative = Path(str(item.get("retained_path") or ""))
        retained_path = (preflight_path.parent / relative).resolve()
        if (
            not reference
            or relative.is_absolute()
            or ".." in relative.parts
            or not retained_path.is_relative_to(preflight_path.parent.resolve())
            or not retained_path.is_file()
            or item.get("sha256")
            != f"sha256:{_sha256_path(retained_path)}"
            or item.get("size_bytes") != retained_path.stat().st_size
        ):
            raise ValueError("R1_PLAN07_PREFLIGHT_RETENTION_INVALID")
        prior = overrides.get(reference)
        if prior is not None and prior != retained_path:
            raise ValueError("R1_PLAN07_PREFLIGHT_RETENTION_CONFLICT")
        overrides[reference] = retained_path
    if not overrides:
        raise ValueError("R1_PLAN07_PREFLIGHT_RETENTION_EMPTY")
    return overrides

def _load_plan07_result(path: Path | str) -> dict[str, Any]:
    result_path = Path(path).resolve()
    if not result_path.is_relative_to(ROOT) or not result_path.is_file():
        raise ValueError("R1_PLAN07_RESULT_PATH_INVALID")
    document = _read_json(result_path)
    audit = live_curator.audit_live_uat_result(document)
    if audit.get("status") != "passed":
        raise ValueError("R1_PLAN07_RESULT_AUDIT_FAILED")
    preflight_path = result_path.parent / "preflight" / "preflight.json"
    overrides = _retained_preflight_artifact_overrides(preflight_path)
    preflight = (
        live._load_green_full_preflight_evidence(
            preflight_path,
            artifact_overrides=overrides,
        )
        if overrides
        else live._load_green_full_preflight_evidence(preflight_path)
    )
    retained_preflight = {
        key: value
        for key, value in preflight.items()
        if key
        not in {
            "mode",
            "evidence_path",
            "evidence_file_sha256",
        }
    }
    if document.get("preflight") != retained_preflight:
        raise ValueError("R1_PLAN07_PREFLIGHT_RESULT_BINDING")
    return {
        "path": result_path.relative_to(ROOT).as_posix(),
        "sha256": _sha256_path(result_path),
        "audit": audit,
        "preflight": {
            "path": preflight["evidence_path"],
            "sha256": preflight["evidence_file_sha256"],
            "status": preflight["status"],
            "evidence_sha256": preflight["evidence_sha256"],
        },
    }


def _load_r1_prerequisite_evidence(
    *,
    plan07_result_path: Path | str,
    admission_evidence_path: Path | str | None,
) -> dict[str, Any]:
    plan07 = _load_plan07_result(plan07_result_path)
    evidence: dict[str, Any] = {
        "full_preflight": plan07["preflight"],
        "plan07_result": plan07,
    }
    if admission_evidence_path is not None:
        admission = live._load_changed_scope_admission(
            admission_evidence_path
        )
        evidence["changed_scope_admission"] = {
            "path": admission["admission_path"],
            "sha256": _sha256_path(Path(admission_evidence_path).resolve()),
            "status": admission["status"],
        }
    return evidence


def _warm_property_runtime(runtime: Any) -> dict[str, Any]:
    """Exercise lazy embedding initialization before any Provider call."""

    try:
        warmup = getattr(runtime, "warmup", None)
        if not callable(warmup):
            raise RuntimeError("PROPERTY_RUNTIME_WARMUP_UNAVAILABLE")
        details = warmup()
        if not isinstance(details, Mapping) or details.get("status") != "ready":
            raise RuntimeError("PROPERTY_RUNTIME_WARMUP_FAILED")
        return {
            "status": "passed",
            "reason_code": None,
            "details": dict(details),
        }
    except Exception as error:
        reason = str(error) or type(error).__name__
        return {
            "status": "failed",
            "reason_code": reason[:256],
            "details": None,
        }


def run_r1_acceptance(
    output_root: Path | str,
    *,
    manifest_path: Path | str = DEFAULT_MANIFEST,
    execute_genuine: bool = False,
    authorization_reference: str | None = None,
    admission_evidence_path: Path | str | None = None,
    plan07_result_path: Path | str | None = None,
    transport_factory: Callable[[], Any] | None = None,
    property_runtime_factory: Callable[[], Any] | None = None,
    case_executor: Callable[..., Mapping[str, Any]] = live._production_case_executor,
) -> dict[str, Any]:
    """Validate readiness or execute the exact manifest using production seams."""

    output = Path(output_root).resolve()
    output.mkdir(parents=True, exist_ok=False)
    loaded = load_execution_manifest(manifest_path)
    result: dict[str, Any] = {
        "schema_version": "text2ifc/repair-milestone-r1-execution-result/0.1",
        "manifest_sha256": loaded["manifest_sha256"],
        "status": "not_started",
        "case_count": len(loaded["public_cases"]),
        "execution_order": list(loaded["execution_order"]),
        "transport_calls": 0,
        "transport_calls_by_stage": {
            "stage1": 0,
            "property_resolution": 0,
            "stage2": 0,
        },
        "cases": [],
        "evaluation_contract": {
            "correctness_deadline_seconds": (
                R1_CORRECTNESS_DEADLINE_SECONDS
            ),
            "rss_limit_bytes": R1_RSS_LIMIT_BYTES,
            "performance_slo_seconds": R1_PERFORMANCE_SLO_SECONDS,
            "performance_slo_blocking": R1_PERFORMANCE_SLO_BLOCKING,
        },
    }
    if R1_NATIVE_RUNTIME_BOOTSTRAP is not None:
        result["native_runtime_bootstrap"] = dict(
            R1_NATIVE_RUNTIME_BOOTSTRAP
        )
    if (
        execute_genuine
        and isinstance(R1_NATIVE_RUNTIME_BOOTSTRAP, Mapping)
        and R1_NATIVE_RUNTIME_BOOTSTRAP.get("status") == "failed"
    ):
        result.update(
            {
                "status": "blocked",
                "reason_code": "R1_NATIVE_RUNTIME_BOOTSTRAP_FAILED",
            }
        )
        live._write_json(output / "r1-execution-result.json", result)
        return result
    if not execute_genuine:
        result["status"] = "ready_for_genuine_authorization"
        live._write_json(output / "r1-execution-result.json", result)
        return result
    if (
        loaded["status"] != AUTHORIZED_STATUS
        or not authorization_reference
        or not str(authorization_reference).strip()
    ):
        result.update(
            {
                "status": "blocked",
                "reason_code": "R1_GENUINE_AUTHORIZATION_REQUIRED",
            }
        )
        live._write_json(output / "r1-execution-result.json", result)
        return result

    if plan07_result_path is None:
        result.update(
            {
                "status": "blocked",
                "reason_code": "R1_PREFLIGHT_AND_PLAN07_EVIDENCE_REQUIRED",
            }
        )
        live._write_json(output / "r1-execution-result.json", result)
        return result
    try:
        prerequisite_evidence = _load_r1_prerequisite_evidence(
            plan07_result_path=plan07_result_path,
            admission_evidence_path=admission_evidence_path,
        )
    except Exception as error:
        result.update(
            {
                "status": "blocked",
                "reason_code": "R1_PREFLIGHT_OR_PLAN07_EVIDENCE_INVALID",
                "prerequisite_reason_code": str(error).split(":", 1)[0][
                    :128
                ],
            }
        )
        live._write_json(output / "r1-execution-result.json", result)
        return result
    result["prerequisite_evidence"] = prerequisite_evidence

    if transport_factory is None or property_runtime_factory is None:
        raise ValueError("R1_PRODUCTION_FACTORIES_REQUIRED")
    transport = transport_factory()
    if not live._approved_deepseek_transport(transport):
        raise ValueError("R1_LIVE_DEEPSEEK_TRANSPORT_REQUIRED")
    property_runtime, readiness = live._open_property_runtime(
        property_runtime_factory
    )
    result["property_runtime_readiness"] = readiness
    if property_runtime is None:
        result.update(
            {
                "status": "blocked",
                "reason_code": readiness.get("reason_code")
                or "PROPERTY_RUNTIME_NOT_READY",
            }
        )
        live._write_json(output / "r1-execution-result.json", result)
        return result
    warmup = _warm_property_runtime(property_runtime)
    result["property_runtime_warmup"] = warmup
    if warmup["status"] != "passed":
        live._close_property_runtime(property_runtime)
        result.update(
            {
                "status": "blocked",
                "reason_code": "R1_PROPERTY_RUNTIME_WARMUP_FAILED",
            }
        )
        live._write_json(output / "r1-execution-result.json", result)
        return result

    provider = live.TranscriptProvider(transport)
    case_results: list[dict[str, Any]] = []
    try:
        for case_document in loaded["public_cases"]:
            case_id = str(case_document["case_id"])
            provider.set_case(case_id)
            before = len(provider.attempts)
            case_root = output / "cases" / case_id
            case_root.mkdir(parents=True)
            case = live.LiveCase(
                case_id=case_id,
                request=str(case_document["request"]),
                feedback=case_document["feedback"],
                feedback_kind=case_document["feedback_kind"],
                expect_program_guard=bool(
                    case_document["expect_program_guard"]
                ),
            )
            try:
                final = dict(
                    case_executor(
                        case,
                        provider,
                        case_root,
                        property_knowledge_runtime=property_runtime,
                        source_path=case_document["source_path"],
                        expected_source_sha256=(
                            "sha256:" + str(case_document["source_sha256"])
                        ),
                        evaluation_execution_policy=(
                            _r1_evaluation_execution_policy()
                        ),
                        performance_slo_seconds=(
                            R1_PERFORMANCE_SLO_SECONDS
                        ),
                    )
                )
                execution_error = None
            except Exception as error:
                execution_error = str(
                    getattr(error, "code", None)
                    or str(error)
                    or type(error).__name__
                )[:256]
                final = {
                    "status": "provider_failed",
                    "reason_code": execution_error.split(":", 1)[0],
                    "complete_repair_success": False,
                    "successful_artifact_publishable": False,
                }
            private_evidence = live._private_evidence_detected(final)
            final = live._redact_for_evidence(final)
            attempts = provider.attempts[before:]
            counts = live._counts(attempts)
            live_pass = live._live_attempt_evidence_pass(attempts)
            base_contract_pass = _case_contract_pass(
                str(case_document["expected_outcome"]),
                final,
                live_evidence_pass=live_pass,
                private_evidence_detected=private_evidence,
                expect_resume=bool(case_document["expect_resume"]),
            )
            predicate_audit = (
                _post_execution_predicate_audit(
                    case_root=case_root,
                    source_path=case_document["source_path"],
                    final=final,
                    profile=loaded["proof_profiles_by_case"][case_id],
                )
                if base_contract_pass
                else {
                    "status": "not_evaluated",
                    "reason_code": "R1_BASE_CASE_CONTRACT_FAILED",
                    "predicate_results": [],
                }
            )
            contract_pass = _case_contract_pass(
                str(case_document["expected_outcome"]),
                final,
                live_evidence_pass=live_pass,
                private_evidence_detected=private_evidence,
                expect_resume=bool(case_document["expect_resume"]),
                artifact_predicate_pass=predicate_audit["status"]
                in {"passed", "not_applicable"},
            )
            case_result = {
                "case_id": case_id,
                "expected_outcome": str(case_document["expected_outcome"]),
                "status": "passed" if contract_pass else "failed",
                "contract_pass": contract_pass,
                "final": final,
                "attempts": attempts,
                "transport_calls": len(attempts),
                "transport_calls_by_stage": counts,
                "synthetic_fallback_used": False,
                "private_evidence_detected": private_evidence,
                "execution_error": execution_error,
                "artifact_predicate_audit": predicate_audit,
            }
            live._write_json(case_root / "case-result.json", case_result)
            case_results.append(case_result)
            stop_reason = _case_stop_reason(
                contract_pass=contract_pass,
                execution_error=execution_error,
            )
            if stop_reason is not None:
                result["stopped_after_case"] = case_id
                result["reason_code"] = stop_reason
                break
    finally:
        live._close_property_runtime(property_runtime)

    aggregate = live._counts(provider.attempts)
    result.update(
        {
            "status": (
                "passed"
                if len(case_results) == len(loaded["public_cases"])
                and all(item["contract_pass"] for item in case_results)
                else "failed"
            ),
            "authorization_reference": str(authorization_reference),
            "transport_calls": len(provider.attempts),
            "transport_calls_by_stage": aggregate,
            "cases": case_results,
        }
    )
    live._write_json(output / "r1-execution-result.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--execute-genuine", action="store_true")
    parser.add_argument("--authorization-reference")
    parser.add_argument("--changed-scope-admission", type=Path)
    parser.add_argument("--plan07-result", type=Path)
    args = parser.parse_args(argv)
    run_root = args.output_root / datetime.now(timezone.utc).strftime(
        "r1-%Y%m%dT%H%M%S%fZ"
    )
    environment = live._environment(args.env_file)

    def transport_factory() -> OpenAICompatibleLiveProvider:
        config = load_openai_compatible_runtime_config(environment)
        return OpenAICompatibleLiveProvider(config=config)

    result = run_r1_acceptance(
        run_root,
        manifest_path=args.manifest,
        execute_genuine=args.execute_genuine,
        authorization_reference=args.authorization_reference,
        admission_evidence_path=args.changed_scope_admission,
        plan07_result_path=args.plan07_result,
        transport_factory=transport_factory,
        property_runtime_factory=lambda: (
            create_property_runtime_from_environment(
                environment,
                project_root=ROOT,
            )
        ),
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "transport_calls": result["transport_calls"],
                "result": str(run_root / "r1-execution-result.json"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if result["status"] in {
        "ready_for_genuine_authorization",
        "passed",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
