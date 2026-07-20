"""Fail-closed public repair orchestration through Evaluation 0.2 publication."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

import ifcopenshell

from .apply import apply_changeset
from .benchmark_evaluation import ProductionEvaluationInputs, evaluate_production
from .evaluation import evaluation_to_dict
from .evaluation_projection import project_public_evaluation
from .production_evidence import build_production_evidence
from .resolution_flow import authorize_prototype, resolve_repair_intent
from .run_artifacts import publish_terminal_artifacts


@dataclass(frozen=True)
class OrchestrationResult:
    status: str
    reason_code: str | None = None
    changeset: Any = None
    evaluation: Mapping[str, Any] | None = None
    successful_ifc: str | None = None
    diagnostic_candidate: str | None = None
    manifest: str | None = None
    prepared_root: str | None = None


class RepairOrchestrator:
    """One public state-machine authority; operation behavior stays in Registry."""

    def __init__(
        self,
        *,
        run_directory: Path | str,
        resolver: Callable[..., Any] = resolve_repair_intent,
        prototype_authorizer: Callable[..., Any] = authorize_prototype,
        changeset_stage: Callable[..., Any],
        audit_stage: Callable[..., Any] | None = None,
        apply_stage: Callable[..., Any] | None = None,
        evaluation_stage: Callable[..., Any] = evaluate_production,
        evidence_builder: Callable[..., Any] = build_production_evidence,
        artifact_publisher: Callable[..., Any] = publish_terminal_artifacts,
        defer_publication: bool = False,
        operation_registry: Any | None = None,
    ) -> None:
        self.run_directory = Path(run_directory)
        self.run_directory.mkdir(parents=True, exist_ok=True)
        self._resolver = resolver
        self._prototype_authorizer = prototype_authorizer
        self._changeset_stage = changeset_stage
        # apply_changeset owns the single complete Audit call.  Retaining this
        # compatibility seam must never cause a second audit.
        self._audit_stage = audit_stage
        self._apply_stage = apply_stage or apply_changeset
        self._evaluation_stage = evaluation_stage
        self._evidence_builder = evidence_builder
        self._artifact_publisher = artifact_publisher
        self._defer_publication = defer_publication
        self._operation_registry = operation_registry
        self._resolution: Any = None

    def start(self, *, intent: Any, repository: Any, expected_source_sha256: str) -> OrchestrationResult:
        self._write("intent.json", intent)
        resolver_kwargs = {"expected_source_sha256": expected_source_sha256}
        if self._operation_registry is not None:
            resolver_kwargs["operation_registry"] = self._operation_registry
        resolution = self._resolver(intent, repository, **resolver_kwargs)
        self._resolution = resolution
        self._write("resolution.json", resolution)
        return self._advance_if_exact(resolution)

    def continue_with_answer(self, answer: Mapping[str, Any]) -> OrchestrationResult:
        if self._resolution is None:
            raise ValueError("REPAIR_RESOLUTION_NOT_STARTED")
        resolution = self._prototype_authorizer(self._resolution, **dict(answer))
        self._resolution = resolution
        self._write("resolution.json", resolution)
        self._write("clarification-answer.json", dict(answer))
        return self._advance_if_exact(resolution)

    def _advance_if_exact(self, resolution: Any) -> OrchestrationResult:
        if resolution.status != "resolved":
            return OrchestrationResult(status="clarification_required", reason_code=resolution.reason_code)
        changeset = self._changeset_stage(resolution)
        self._write("changeset.json", changeset)
        return OrchestrationResult(status="changeset_ready", changeset=changeset)

    def _write(self, name: str, value: Any) -> None:
        rendered = json.dumps(_public_json(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        (self.run_directory / name).write_text(rendered + "\n", encoding="utf-8")

    def apply_and_evaluate(
        self,
        *,
        source_ifc_path: Path | str,
        repair_request: str,
        intent: Any,
        resolution: Any,
        changeset: Mapping[str, Any],
        registry: Any,
        records_by_global_id: Mapping[str, Any],
        type_records_by_global_id: Mapping[str, Any],
        deterministic_policy_facts_by_operation: Mapping[str, tuple[Any, ...]] | None = None,
        verified_absent_categories_by_operation: Mapping[str, tuple[str, ...]] | None = None,
        private_canaries: tuple[str, ...] = (),
    ) -> OrchestrationResult:
        """Apply all operations once, reopen, evaluate, then atomically promote."""

        source = Path(source_ifc_path).resolve()
        source_hash = _path_sha256(source)
        if source_hash != str(changeset.get("base_model_fingerprint", "")):
            return self._terminal_failure("audit_failed", "BASE_MODEL_FINGERPRINT_MISMATCH", changeset, {"source_hash": source_hash}, private_canaries=private_canaries)
        candidate = self.run_directory / "staging" / "application-candidate.ifc"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        if candidate.exists():
            return self._terminal_failure("application_failed", "OUTPUT_ALREADY_EXISTS", changeset, {}, private_canaries=private_canaries)
        try:
            application = self._apply_stage(
                damaged_ifc_path=source,
                repair_request=repair_request,
                changeset=changeset,
                output_path=candidate,
                registry=registry,
            )
        except Exception as error:
            return self._terminal_failure("application_failed", "APPLICATION_STAGE_EXCEPTION", changeset, {"error_type": type(error).__name__}, private_canaries=private_canaries)
        evidence = {
            "audit": application.get("audit"),
            "application": _public_json(application),
            "source_sha256_before": source_hash,
            "source_sha256_after": _path_sha256(source),
        }
        if not _complete_transaction_valid(changeset, application):
            status = "audit_failed" if not bool((application.get("audit") or {}).get("valid")) else "application_failed"
            return self._terminal_failure(status, "UNIFIED_TRANSACTION_FAILED", changeset, evidence, private_canaries=private_canaries)
        if _path_sha256(source) != source_hash:
            return self._terminal_failure("application_failed", "SOURCE_HASH_CHANGED", changeset, evidence, candidate=candidate if candidate.exists() else None, private_canaries=private_canaries)
        output = application.get("output") or {}
        if Path(str(output.get("path", ""))).resolve() != candidate.resolve():
            return self._terminal_failure("application_failed", "APPLICATION_OUTPUT_PATH_MISMATCH", changeset, evidence, candidate=candidate if candidate.exists() else None, private_canaries=private_canaries)
        candidate_hash = _path_sha256(candidate)
        if candidate_hash != _normalize_sha256(str(output.get("sha256", ""))) or not _is_ifc2x3(candidate):
            return self._terminal_failure("application_failed", "CANDIDATE_REOPEN_OR_HASH_FAILED", changeset, evidence, candidate=candidate, private_canaries=private_canaries)
        try:
            production_evidence = self._evidence_builder(
                intent=intent,
                resolution=resolution,
                changeset=changeset,
                registry=registry,
                records_by_global_id=records_by_global_id,
                type_records_by_global_id=type_records_by_global_id,
                deterministic_policy_facts_by_operation=deterministic_policy_facts_by_operation or {},
                verified_absent_categories_by_operation=verified_absent_categories_by_operation or {},
            )
        except Exception as error:
            return self._terminal_failure("l2_not_evaluable", "PRODUCTION_EVIDENCE_FAILED", changeset, {**evidence, "error_type": type(error).__name__}, candidate=candidate, private_canaries=private_canaries)
        missing = _missing_authority_decisions(production_evidence)
        if missing:
            return self._terminal_failure("l2_not_evaluable", "MANDATORY_SEMANTIC_AUTHORITY_MISSING", changeset, {**evidence, "not_evaluable": missing}, candidate=candidate, private_canaries=private_canaries)
        try:
            evaluation = self._evaluation_stage(
                ProductionEvaluationInputs(
                    damaged_ifc_path=source,
                    repaired_ifc_path=candidate,
                    changeset=changeset,
                    application_result=application,
                    registry=registry,
                    expected_facts_by_operation=production_evidence.expected_facts_by_operation,
                )
            )
            public_evaluation = _public_evaluation(evaluation)
        except Exception as error:
            return self._terminal_failure("l2_not_evaluable", "PRODUCTION_EVALUATION_FAILED", changeset, {**evidence, "error_type": type(error).__name__}, candidate=candidate, private_canaries=private_canaries)
        terminal_status = "succeeded" if public_evaluation["successful_artifact_publishable"] else _evaluation_terminal_status(public_evaluation)
        artifacts = self._artifact_publisher(
            run_directory=self.run_directory,
            terminal_status=terminal_status,
            evaluation=public_evaluation,
            candidate_ifc_path=candidate,
            expected_candidate_sha256=candidate_hash,
            evidence={**evidence, "production_applicability": _public_json(production_evidence.applicability_by_operation), "production_conflicts": _public_json(production_evidence.conflicts)},
            private_canaries=private_canaries,
            promote=not self._defer_publication,
        )
        return OrchestrationResult(
            status="succeeded" if artifacts.successful_ifc else terminal_status,
            evaluation=public_evaluation,
            successful_ifc=artifacts.successful_ifc,
            diagnostic_candidate=artifacts.diagnostic_candidate,
            manifest=artifacts.manifest_path,
            prepared_root=artifacts.prepared_root,
        )

    def _terminal_failure(
        self,
        status: str,
        reason_code: str,
        changeset: Mapping[str, Any],
        evidence: Mapping[str, Any],
        *,
        candidate: Path | None = None,
        private_canaries: tuple[str, ...] = (),
    ) -> OrchestrationResult:
        evaluation = _failure_public_evaluation(status, reason_code, changeset)
        artifacts = self._artifact_publisher(
            run_directory=self.run_directory,
            terminal_status=status,
            evaluation=evaluation,
            candidate_ifc_path=candidate,
            evidence=evidence,
            private_canaries=private_canaries,
            promote=not self._defer_publication,
        )
        return OrchestrationResult(
            status=status,
            reason_code=reason_code,
            evaluation=evaluation,
            diagnostic_candidate=artifacts.diagnostic_candidate,
            manifest=artifacts.manifest_path,
            prepared_root=artifacts.prepared_root,
        )


def _complete_transaction_valid(changeset: Mapping[str, Any], application: Mapping[str, Any]) -> bool:
    expected_ids = [str(item.get("operation_id", "")) for item in changeset.get("operations", ())]
    audit = application.get("audit") or {}
    audited_ids = [str(item.get("operation_id", "")) for item in audit.get("operation_audits", ())]
    applied_ids = [str(item.get("operation_id", "")) for item in application.get("operations", ())]
    return bool(application.get("valid")) and bool(application.get("published")) and bool(audit.get("valid")) and audited_ids == expected_ids and applied_ids == expected_ids and bool(application.get("output"))


def _missing_authority_decisions(production_evidence: Any) -> list[str]:
    missing = []
    for operation_id, decisions in production_evidence.applicability_by_operation.items():
        for check_id, decision in decisions.items():
            if decision.outcome == "not_evaluable":
                missing.append(f"{operation_id}:{check_id}")
    return sorted(missing)


def _public_evaluation(evaluation: Any) -> dict[str, Any]:
    if isinstance(evaluation, Mapping):
        payload = dict(evaluation)
        if payload.get("schema_version") == "text2ifc/ifc-repair-evaluation-public/0.2":
            return payload
    else:
        payload = evaluation_to_dict(evaluation)
    return project_public_evaluation(payload)


def _failure_public_evaluation(status: str, reason_code: str, changeset: Mapping[str, Any]) -> dict[str, Any]:
    post_application = status.startswith("l2_")
    application_status = "passed" if post_application else "failed" if status == "application_failed" else "not_evaluable"
    preservation_status = "passed" if post_application else "not_evaluable"
    operations = [
        {
            "operation_id": str(item.get("operation_id", "operation")),
            "operation_type": str(item.get("operation_type", "unsupported")),
            "policy_id": "production.terminal",
            "policy_version": "0.2",
            "status": "not_evaluable",
            "reason": reason_code,
            "levels": [
                {
                    "level": level,
                    "status": (
                        "passed" if post_application and level == "L1"
                        else "not_required" if level == "L3"
                        else "not_evaluable"
                    ),
                    "reason": reason_code,
                    "checks": [],
                }
                for level in ("L1", "L2", "L3")
            ],
        }
        for item in changeset.get("operations", ())
    ]
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "policy_version": "phase8.1",
        "status": "failed",
        "reason": reason_code,
        "complete_repair_success": False,
        "successful_artifact_publishable": False,
        "diagnostic_artifact_retained": status.startswith(("l1_", "l2_")),
        "application": {"check_id": "application.valid", "status": application_status, "reason": reason_code},
        "preservation": {"check_id": "preservation.valid", "status": preservation_status, "reason": reason_code},
        "operations": operations,
    }


def _evaluation_terminal_status(evaluation: Mapping[str, Any]) -> str:
    levels = {
        str(level.get("level")): str(level.get("status"))
        for operation in evaluation.get("operations", ())
        for level in operation.get("levels", ())
    }
    if levels.get("L1") == "failed":
        return "l1_failed"
    l2 = levels.get("L2", str(evaluation.get("status", "not_evaluable")))
    if l2 == "not_evaluable":
        return "l2_not_evaluable"
    if l2 == "partial":
        return "l2_partial"
    return "l2_failed"


def _path_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize_sha256(value: str) -> str:
    return value if value.startswith("sha256:") else f"sha256:{value}"


def _is_ifc2x3(path: Path) -> bool:
    try:
        return ifcopenshell.open(str(path)).schema == "IFC2X3"
    except Exception:
        return False


def _public_json(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return _public_json(value.to_dict())
    if is_dataclass(value):
        return _public_json(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _public_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_public_json(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return {"type": type(value).__name__}


__all__ = ["OrchestrationResult", "RepairOrchestrator"]
