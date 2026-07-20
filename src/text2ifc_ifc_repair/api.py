"""Single public IFC-path plus natural-language repair facade."""

from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path
from typing import Any, Callable, Mapping

import ifcopenshell

from .index_models import INDEX_SCHEMA_VERSION
from .index_store import SQLiteIndexRepository
from .indexer import build_ifc_index
from .operations import create_default_registry
from .orchestrator import OrchestrationResult, RepairOrchestrator
from .provider_stage import generate_bound_changeset
from .repair_intent import RepairIntent
from .request_stage import generate_repair_intent
from .run_models import (
    Clarification,
    ClarificationCandidate,
    RunResult,
    RunStage,
    RunStoreError,
)
from .run_store import RunStore
from .run_artifacts import publish_terminal_artifacts
from text2ifc_text.splits import atomic_write_text


class RepairAPI:
    """Behavior authority used by Python callers and every CLI mode.

    Private benchmark originals and mutation mappings deliberately do not exist
    in this constructor or in ``start``.
    """

    def __init__(
        self,
        output_root: Path | str,
        *,
        provider: Any,
        registry: Any | None = None,
        intent_stage: Callable[..., Mapping[str, Any]] = generate_repair_intent,
        index_stage: Callable[..., Any] = build_ifc_index,
        changeset_stage: Callable[..., Mapping[str, Any]] = generate_bound_changeset,
        orchestrator_factory: Callable[..., RepairOrchestrator] = RepairOrchestrator,
        orchestrator_options: Mapping[str, Any] | None = None,
    ) -> None:
        self.store = RunStore(output_root)
        self.provider = provider
        self.registry = registry or create_default_registry()
        self._intent_stage = intent_stage
        self._index_stage = index_stage
        self._changeset_stage = changeset_stage
        self._orchestrator_factory = orchestrator_factory
        requested_options = dict(orchestrator_options or {})
        if requested_options.get("defer_publication") is False:
            raise ValueError("DURABLE_PUBLICATION_CANNOT_BE_DISABLED")
        requested_options["defer_publication"] = True
        self._orchestrator_options = requested_options

    @classmethod
    def from_environment(
        cls, output_root: Path | str, environment: Mapping[str, str] | None = None
    ) -> "RepairAPI":
        """Build the public facade from the established redacted Provider config."""

        import os

        from text2ifc_agent.openai_compat import (
            OpenAICompatibleLiveProvider,
            load_openai_compatible_runtime_config,
        )

        config = load_openai_compatible_runtime_config(
            dict(os.environ) if environment is None else dict(environment)
        )
        return cls(
            output_root,
            provider=OpenAICompatibleLiveProvider(config=config),
        )

    def start(
        self,
        source_ifc_path: Path | str,
        repair_text: str,
        *,
        run_id: str | None = None,
    ) -> RunResult:
        if not isinstance(repair_text, str) or not repair_text.strip():
            raise ValueError("REPAIR_REQUEST_EMPTY")
        request_id = f"request-{hashlib.sha256(repair_text.encode('utf-8')).hexdigest()[:16]}"
        state = self.store.start_run(
            source_path=source_ifc_path,
            request_id=request_id,
            request_text=repair_text,
            run_id=run_id,
        )
        run_dir = self.store.runs_root / state.run_id
        try:
            model = ifcopenshell.open(str(Path(source_ifc_path).resolve()))
            if model.schema != "IFC2X3":
                return self._fail(state.run_id, RunStage.INVALID_INPUT, "IFC_SCHEMA_UNSUPPORTED")
        except Exception:
            return self._fail(state.run_id, RunStage.INVALID_INPUT, "IFC_SOURCE_INVALID")
        state = self.store.transition(
            state.run_id,
            to_stage=RunStage.SOURCE_VALIDATED,
            expected_state_version=state.state_version,
            stage_payload={"ifc_schema": "IFC2X3", "source_sha256": state.source.sha256},
        )
        index_dir = self.store.prepare_stage_directory(state.run_id, "index")
        index_path = index_dir / "targets.sqlite"
        try:
            metadata = self._index_stage(source_ifc_path, index_path)
        except Exception as error:
            return self._fail(state.run_id, RunStage.INVALID_INPUT, _safe_code(error, "INDEX_BUILD_FAILED"))
        state = self.store.transition(
            state.run_id,
            to_stage=RunStage.INDEX_READY,
            expected_state_version=state.state_version,
            stage_payload={
                "index": self.store.artifact_binding(
                    state.run_id, "index/targets.sqlite", INDEX_SCHEMA_VERSION
                ),
                "source_sha256": metadata.source_ifc_sha256,
            },
        )
        intent_dir = self.store.prepare_stage_directory(state.run_id, "intent")
        intent_result = self._intent_stage(
            provider=self.provider,
            request_id=request_id,
            repair_request=repair_text,
            registry=self.registry,
            output_dir=intent_dir,
        )
        if not intent_result.get("valid") or intent_result.get("intent") is None:
            return self._fail(state.run_id, RunStage.PROVIDER_FAILED, str(intent_result.get("error_code") or "INTENT_STAGE_FAILED"))
        intent = intent_result["intent"]
        intent_path = intent_dir / "repair-intent.json"
        if not intent_path.exists():
            atomic_write_text(
                intent_path,
                json.dumps(intent.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            )
        context_ref = self._write_context(run_dir, repair_text=repair_text, intent=intent)
        state = self.store.transition(
            state.run_id,
            to_stage=RunStage.INTENT_READY,
            expected_state_version=state.state_version,
            stage_payload={
                "intent": self.store.artifact_binding(
                    state.run_id, "intent/repair-intent.json", "text2ifc/ifc-repair-intent/0.1"
                ),
                "api_context": self.store.artifact_binding(
                    state.run_id, context_ref, "text2ifc/ifc-repair-api-context/0.1"
                ),
            },
        )
        return self._resolve_and_finish(state.run_id, intent, repair_text)

    def continue_with_answer(
        self,
        run_id: str,
        answer: Mapping[str, Any],
        *,
        clarification_id: str,
        expected_state_version: int,
    ) -> RunResult:
        pending = self.store.load(run_id)
        clarification = pending.clarification
        if clarification is None:
            raise ValueError("CLARIFICATION_NOT_PENDING")
        if clarification.clarification_id != clarification_id or pending.state_version != expected_state_version:
            raise RunStoreError("RUN_STATE_CONFLICT", "clarification binding is stale")
        run_dir = self.store.runs_root / run_id
        context_path = run_dir / _latest_api_context(pending)
        context = json.loads(context_path.read_text(encoding="utf-8"))
        repair_text = str(context["repair_text"])
        intent_document = dict(context["intent"])
        kind = str(answer.get("kind", ""))
        attempt_id = uuid.uuid4().hex
        resume_intent_ref: str | None = None
        if kind == "select_candidate":
            token = str(answer.get("candidate_token", ""))
            selected = next((item for item in clarification.candidates if item.token == token), None)
            if selected is None:
                raise ValueError("CLARIFICATION_CANDIDATE_NOT_OFFERED")
            for operation in intent_document["operations"]:
                if operation["operation_id"] == clarification.operation_id:
                    query = operation["target_query"]
                    # Candidate selection authorizes exactly one public identity;
                    # retain only query controls and remove selectors that could
                    # contradict that identity on resume.
                    operation["target_query"] = {
                        key: value for key, value in query.items()
                        if key in {"schema_version", "allowed_ifc_classes", "max_candidates", "winner_margin"}
                    }
                    operation["target_query"]["global_id"] = selected.public_id
        elif kind == "add_detail":
            repair_text = f"{repair_text}\n补充说明：{str(answer['detail']).strip()}"
            resume_version = expected_state_version + 1
            resume_intent_ref = (
                f"intent/resume-{resume_version:03d}-{attempt_id}/repair-intent.json"
            )
            resume_dir = self.store.prepare_stage_directory(
                run_id, str(Path(resume_intent_ref).parent).replace("\\", "/")
            )
            generated = self._intent_stage(
                provider=self.provider,
                request_id=str(intent_document["request_id"]),
                repair_request=repair_text,
                registry=self.registry,
                output_dir=resume_dir,
            )
            if not generated.get("valid") or generated.get("intent") is None:
                return self._fail(run_id, RunStage.PROVIDER_FAILED, "INTENT_RESUME_FAILED")
            intent_document = generated["intent"].to_dict()
            resumed_intent_path = resume_dir / "repair-intent.json"
            if not resumed_intent_path.exists():
                atomic_write_text(
                    resumed_intent_path,
                    json.dumps(
                        intent_document,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    + "\n",
                )
        intent = RepairIntent.from_dict(intent_document, registry=self.registry)
        context_ref = self._write_context(
            run_dir, repair_text=repair_text, intent=intent,
            name=f"api-context-v{expected_state_version + 1:03d}-{attempt_id}.json",
        )
        resume_payload: dict[str, Any] = {
            "api_context": self.store.artifact_binding(
                run_id, context_ref, "text2ifc/ifc-repair-api-context/0.1"
            )
        }
        if kind == "add_detail":
            assert resume_intent_ref is not None
            resume_payload["intent"] = self.store.artifact_binding(
                run_id,
                resume_intent_ref,
                "text2ifc/ifc-repair-intent/0.1",
            )
        if kind in {"cancel", "eof"}:
            cancel_artifacts, prepared_root = self._publish_failure_bundle(
                run_id, RunStage.CANCELLED, "USER_CANCELLED", pending.stage.value
            )
            self.store.commit_terminal_publication(
                run_id,
                prepared_root=prepared_root,
                to_stage=RunStage.CANCELLED,
                expected_state_version=expected_state_version,
                reason_code="USER_CANCELLED",
                stage_payload=resume_payload,
                result_artifacts=cancel_artifacts,
                answer=answer,
                clarification_id=clarification_id,
            )
            return self.store.read_result(run_id)
        resumed = self.store.continue_with_answer(
            run_id, clarification_id=clarification_id,
            expected_state_version=expected_state_version, answer=answer,
            stage_payload=resume_payload,
            result_artifacts=None,
        )
        prototype_answer = None
        if kind == "authorize_prototype":
            prototype_answer = {
                "operation_id": clarification.operation_id,
                "candidate_token": str(answer["candidate_token"]),
                "authorized": True,
            }
        return self._resolve_and_finish(run_id, intent, repair_text, prototype_answer=prototype_answer)

    def read_result(self, run_id: str) -> RunResult:
        return self.store.read_result(run_id)

    def _resolve_and_finish(
        self, run_id: str, intent: RepairIntent, repair_text: str,
        *, prototype_answer: Mapping[str, Any] | None = None,
    ) -> RunResult:
        state = self.store.load(run_id)
        run_dir = self.store.runs_root / run_id
        with SQLiteIndexRepository.open(
            run_dir / "index" / "targets.sqlite",
            expected_source_ifc_sha256=state.source.sha256,
        ) as repository:
            def stage2(resolution: Any) -> Mapping[str, Any]:
                changeset_dir = self.store.prepare_stage_directory(run_id, "changeset")
                generated = self._changeset_stage(
                    provider=self.provider,
                    case_id=run_id,
                    repair_request=repair_text,
                    source_request_hash=intent.source_request_hash,
                    resolved_operations=resolution.operations,
                    model_fingerprint=intent.model_fingerprint,
                    base_model_fingerprint=resolution.source_ifc_sha256,
                    registry=self.registry,
                    output_dir=changeset_dir,
                )
                if not generated.get("valid") or generated.get("changeset") is None:
                    raise ValueError("CHANGESET_STAGE_FAILED")
                return generated["changeset"]

            orchestrator = self._orchestrator_factory(
                run_directory=run_dir,
                changeset_stage=stage2,
                **self._orchestrator_options,
            )
            try:
                outcome = orchestrator.start(
                    intent=intent,
                    repository=repository,
                    expected_source_sha256=state.source.sha256,
                )
            except Exception as error:
                return self._fail(run_id, RunStage.PROVIDER_FAILED, _safe_code(error, "CHANGESET_STAGE_FAILED"))
            resolution = orchestrator._resolution
            if prototype_answer is not None and resolution.status == "clarification_required" and resolution.reason_code == "prototype_selection":
                outcome = orchestrator.continue_with_answer(prototype_answer)
                resolution = orchestrator._resolution
            if resolution.status == "failed":
                stage = {
                    "unsupported": RunStage.UNSUPPORTED,
                    "stale_index": RunStage.INVALID_INPUT,
                    "context_budget_exceeded": RunStage.PROVIDER_FAILED,
                    "missing_evidence": RunStage.INVALID_INPUT,
                }.get(str(resolution.reason_code), RunStage.INVALID_INPUT)
                return self._fail(run_id, stage, str(resolution.reason_code or "RESOLUTION_FAILED"))
            if outcome.status == "clarification_required":
                clarification = _clarification(run_id, state.state_version + 1, resolution)
                resolution_ref = _snapshot_artifact(
                    run_dir, "resolution.json", f"resolution-v{state.state_version + 1:03d}.json"
                )
                self.store.transition(
                    run_id,
                    to_stage=RunStage.CLARIFICATION_REQUIRED,
                    expected_state_version=state.state_version,
                    clarification=clarification,
                    reason_code=outcome.reason_code,
                    stage_payload={"resolution": self.store.artifact_binding(
                        run_id, resolution_ref, "text2ifc/ifc-resolution-flow/0.1"
                    )},
                )
                return self.store.read_result(run_id)
            resolution_ref = _snapshot_artifact(
                run_dir, "resolution.json", f"resolution-v{state.state_version + 1:03d}.json"
            )
            state = self.store.transition(
                run_id,
                to_stage=RunStage.TARGETS_RESOLVED,
                expected_state_version=state.state_version,
                stage_payload={"resolution": self.store.artifact_binding(
                    run_id, resolution_ref, "text2ifc/ifc-resolution-flow/0.1"
                )},
            )
            changeset_ref = _snapshot_artifact(
                run_dir, "changeset.json", f"changeset-v{state.state_version + 1:03d}.json"
            )
            state = self.store.transition(
                run_id,
                to_stage=RunStage.CHANGESET_READY,
                expected_state_version=state.state_version,
                stage_payload={"changeset": self.store.artifact_binding(
                    run_id, changeset_ref, "text2ifc/ifc-repair-changeset/0.1"
                )},
            )
            records = {
                record.ifc_global_id: record
                for record in repository.iter_records()
                if record.ifc_global_id
            }
            self.store.prepare_stage_directory(run_id, "staging")
            final = orchestrator.apply_and_evaluate(
                source_ifc_path=Path(state.source.reference),
                repair_request=repair_text,
                intent=intent,
                resolution=resolution,
                changeset=outcome.changeset,
                registry=self.registry,
                records_by_global_id=records,
            )
        terminal = {
            "succeeded": RunStage.SUCCEEDED,
            "audit_failed": RunStage.AUDIT_FAILED,
            "application_failed": RunStage.APPLICATION_FAILED,
        }.get(final.status, RunStage.NOT_PUBLISHABLE)
        artifacts = _artifact_references(run_dir, final)
        if final.prepared_root is None:
            raise ValueError("TERMINAL_PUBLICATION_NOT_PREPARED")
        self.store.commit_terminal_publication(
            run_id,
            prepared_root=Path(final.prepared_root).relative_to(run_dir).as_posix(),
            to_stage=terminal,
            expected_state_version=state.state_version,
            reason_code=final.reason_code,
            stage_payload={"status": final.status},
            result_artifacts=artifacts,
        )
        return self.store.read_result(run_id)

    def _fail(self, run_id: str, stage: RunStage, reason: str) -> RunResult:
        state = self.store.load(run_id)
        artifacts, prepared_root = self._publish_failure_bundle(
            run_id, stage, reason[:128], state.stage.value
        )
        self.store.commit_terminal_publication(
            run_id,
            prepared_root=prepared_root,
            to_stage=stage,
            expected_state_version=state.state_version,
            reason_code=reason[:128],
            stage_payload={"reason_code": reason[:128]},
            result_artifacts=artifacts,
        )
        return self.store.read_result(run_id)

    def _publish_failure_bundle(
        self, run_id: str, stage: RunStage, reason: str, from_stage: str,
    ) -> tuple[dict[str, str], str]:
        run_dir = self.store.runs_root / run_id
        published = publish_terminal_artifacts(
            run_directory=run_dir, terminal_status=stage.value,
            evaluation=_terminal_failure_evaluation(reason), candidate_ifc_path=None,
            evidence={"reason_code": reason, "stage": from_stage},
            promote=False,
        )
        if published.prepared_root is None:
            raise ValueError("TERMINAL_PUBLICATION_NOT_PREPARED")
        artifacts = {
            "manifest": Path(published.manifest_path).relative_to(run_dir).as_posix(),
            "evaluation": Path(published.evaluation_path).relative_to(run_dir).as_posix(),
            "evidence": Path(published.evidence_path).relative_to(run_dir).as_posix(),
        }
        return artifacts, Path(published.prepared_root).relative_to(run_dir).as_posix()

    @staticmethod
    def _write_context(
        run_dir: Path, *, repair_text: str, intent: RepairIntent,
        name: str = "api-context.json",
    ) -> str:
        payload = (
            json.dumps(
                {"schema_version": "text2ifc/ifc-repair-api-context/0.1", "repair_text": repair_text, "intent": intent.to_dict()},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n"
        )
        atomic_write_text(run_dir / name, payload)
        return name


def _clarification(run_id: str, version: int, resolution: Any) -> Clarification:
    candidates = tuple(
        ClarificationCandidate(
            token=str(item["token"]),
            public_id=str(item["public_id"]),
            ifc_class=str(item["ifc_class"]),
            name=item.get("name"),
            storey=item.get("storey"),
            position=item.get("position"),
            evidence=tuple(str(value) for value in item.get("evidence", ())),
        )
        for item in resolution.candidates
    )
    reason_map = {
        "ambiguous": "ambiguous_target", "conflict": "selector_conflict",
        "not_found": "additional_target_detail", "missing_evidence": "additional_target_detail",
        "prototype_selection": "prototype_selection",
    }
    reason = reason_map.get(str(resolution.reason_code), "additional_target_detail")
    modes = (
        ("authorize_prototype", "cancel") if reason == "prototype_selection"
        else ("select_candidate", "add_detail", "cancel") if candidates
        else ("add_detail", "cancel")
    )
    return Clarification(
        clarification_id=f"clarify-{version:03d}",
        run_id=run_id,
        state_version=version,
        operation_id=str(resolution.operation_id or "operation"),
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code=reason,
        question="目标不唯一或证据不足，请选择候选、补充说明或取消。",
        answer_modes=modes,
        candidates=candidates,
    )


def _artifact_references(run_dir: Path, result: OrchestrationResult) -> dict[str, str]:
    values = {
        "manifest": result.manifest,
        "successful_ifc": result.successful_ifc,
        "diagnostic_candidate": result.diagnostic_candidate,
    }
    references: dict[str, str] = {}
    for key, value in values.items():
        if value:
            references[key] = Path(value).resolve().relative_to(run_dir.resolve()).as_posix()
    evaluation = (
        Path(result.manifest).parent / "evaluation" / "public-evaluation.json"
        if result.manifest else run_dir / "evaluation" / "public-evaluation.json"
    )
    if evaluation.is_file():
        references["evaluation"] = evaluation.relative_to(run_dir).as_posix()
    return references


def _safe_code(error: Exception, fallback: str) -> str:
    code = getattr(error, "code", None)
    return str(code or fallback).split(":", 1)[0][:128]


def _latest_api_context(state: Any) -> str:
    for transition in reversed(state.transitions):
        payload = transition.stage_payload
        binding = payload.get("api_context") if isinstance(payload, Mapping) else None
        if isinstance(binding, Mapping) and binding.get("path"):
            return str(binding["path"])
    raise RunStoreError("RUN_TAMPER_DETECTED", "api context binding is missing")


def _snapshot_artifact(run_dir: Path, source: str, destination: str) -> str:
    atomic_write_text(run_dir / destination, (run_dir / source).read_text(encoding="utf-8"))
    return destination


def _terminal_failure_evaluation(reason: str) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "policy_version": "phase8.1", "status": "not_evaluable", "reason": reason,
        "complete_repair_success": False, "successful_artifact_publishable": False,
        "diagnostic_artifact_retained": False,
        "application": {"check_id": "application.valid", "status": "not_evaluable", "reason": reason},
        "preservation": {"check_id": "preservation.valid", "status": "not_evaluable", "reason": reason},
        "operations": [],
    }


__all__ = ["RepairAPI", "RunStoreError"]
