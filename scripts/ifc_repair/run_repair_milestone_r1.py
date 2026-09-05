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

from scripts.ifc_repair import run_phase12_live_uat as live
from scripts.ifc_repair import curate_phase12_live_proof as live_curator
from text2ifc_agent.openai_compat import (
    OpenAICompatibleLiveProvider,
    load_openai_compatible_runtime_config,
)
from text2ifc_knowledge.property_runtime import (
    create_property_runtime_from_environment,
)


DEFAULT_MANIFEST = (
    ROOT
    / "docs/validation/repair-milestone-r1/"
    "repair-r1-execution-manifest.json"
)
DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair-runs/repair-milestone-r1"
SCHEMA_VERSION = "text2ifc/repair-milestone-r1-execution-manifest/0.1"
AUTHORIZED_STATUS = "AUTHORIZED_FOR_GENUINE_EXECUTION"
PREPARED_STATUS = "PREPARED_AWAITING_GENUINE_AUTHORIZATION"


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
    _bound_repository_file(document["proof_profiles"])
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
    if not isinstance(resume_bindings, Mapping) or set(resume_bindings) != {
        "M1",
        "H3",
    }:
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
        public_case = {
            "case_id": case_id,
            "model_id": model_id,
            "request": request,
            "request_sha256": str(case["request_sha256"]),
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
    }


def _case_contract_pass(
    case_id: str,
    final: Mapping[str, Any],
    *,
    live_evidence_pass: bool,
    private_evidence_detected: bool,
) -> bool:
    if private_evidence_detected or not live_evidence_pass:
        return False
    if case_id == "H4":
        return (
            final.get("status") == "unsupported"
            and final.get("reason_code") == "STRUCTURAL_ANALYSIS_UNSUPPORTED"
            and final.get("successful_artifact_publishable") is False
            and not final.get("program_guard_evidence", {}).get(
                "mutation_attempted", True
            )
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
            case_id not in {"M1", "H3"}
            or final.get("clarification_answer_applied") is True
        )
    )


def _load_plan07_result(path: Path | str) -> dict[str, Any]:
    result_path = Path(path).resolve()
    if not result_path.is_relative_to(ROOT) or not result_path.is_file():
        raise ValueError("R1_PLAN07_RESULT_PATH_INVALID")
    document = _read_json(result_path)
    audit = live_curator.audit_live_uat_result(document)
    if audit.get("status") != "passed":
        raise ValueError("R1_PLAN07_RESULT_AUDIT_FAILED")
    return {
        "path": result_path.relative_to(ROOT).as_posix(),
        "sha256": _sha256_path(result_path),
        "audit": audit,
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
    }
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

    if admission_evidence_path is None or plan07_result_path is None:
        result.update(
            {
                "status": "blocked",
                "reason_code": "R1_PREFLIGHT_AND_PLAN07_EVIDENCE_REQUIRED",
            }
        )
        live._write_json(output / "r1-execution-result.json", result)
        return result
    try:
        admission = live._load_changed_scope_admission(
            admission_evidence_path
        )
        plan07 = _load_plan07_result(plan07_result_path)
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
    result["prerequisite_evidence"] = {
        "changed_scope_admission": {
            "path": admission["admission_path"],
            "sha256": _sha256_path(Path(admission_evidence_path).resolve()),
            "status": admission["status"],
        },
        "plan07_result": plan07,
    }

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
            contract_pass = _case_contract_pass(
                case_id,
                final,
                live_evidence_pass=live_pass,
                private_evidence_detected=private_evidence,
            )
            case_result = {
                "case_id": case_id,
                "status": "passed" if contract_pass else "failed",
                "contract_pass": contract_pass,
                "final": final,
                "attempts": attempts,
                "transport_calls": len(attempts),
                "transport_calls_by_stage": counts,
                "synthetic_fallback_used": False,
                "private_evidence_detected": private_evidence,
                "execution_error": execution_error,
            }
            live._write_json(case_root / "case-result.json", case_result)
            case_results.append(case_result)
            if execution_error is not None:
                result["stopped_after_case"] = case_id
                result["reason_code"] = "R1_EXECUTION_DEFECT_STOP"
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
