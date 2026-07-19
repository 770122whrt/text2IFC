"""Single public IFC-path plus natural-language repair facade."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping

import ifcopenshell

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
        self._orchestrator_options = dict(orchestrator_options or {})

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
        index_path = run_dir / "index" / "targets.sqlite"
        try:
            metadata = self._index_stage(source_ifc_path, index_path)
        except Exception as error:
            return self._fail(state.run_id, RunStage.INVALID_INPUT, _safe_code(error, "INDEX_BUILD_FAILED"))
        state = self.store.transition(
            state.run_id,
            to_stage=RunStage.INDEX_READY,
            expected_state_version=state.state_version,
            stage_payload={"index": "index/targets.sqlite", "source_sha256": metadata.source_ifc_sha256},
        )
        intent_result = self._intent_stage(
            provider=self.provider,
            request_id=request_id,
            repair_request=repair_text,
            registry=self.registry,
            output_dir=run_dir / "intent",
        )
        if not intent_result.get("valid") or intent_result.get("intent") is None:
            return self._fail(state.run_id, RunStage.PROVIDER_FAILED, str(intent_result.get("error_code") or "INTENT_STAGE_FAILED"))
        intent = intent_result["intent"]
        state = self.store.transition(
            state.run_id,
            to_stage=RunStage.INTENT_READY,
            expected_state_version=state.state_version,
            stage_payload={"intent": "intent/repair-intent.json"},
        )
        self._write_context(run_dir, repair_text=repair_text, intent=intent)
        return self._resolve_and_finish(state.run_id, intent, repair_text)

    def continue_with_answer(self, run_id: str, answer: Mapping[str, Any]) -> RunResult:
        pending = self.store.load(run_id)
        clarification = pending.clarification
        if clarification is None:
            raise ValueError("CLARIFICATION_NOT_PENDING")
        resumed = self.store.continue_with_answer(
            run_id,
            clarification_id=clarification.clarification_id,
            expected_state_version=pending.state_version,
            answer=answer,
        )
        if resumed.stage is RunStage.CANCELLED:
            return self.store.read_result(run_id)
        run_dir = self.store.runs_root / run_id
        context = json.loads((run_dir / "api-context.json").read_text(encoding="utf-8"))
        repair_text = str(context["repair_text"])
        intent_document = dict(context["intent"])
        kind = str(answer.get("kind", ""))
        if kind == "select_candidate":
            token = str(answer.get("candidate_token", ""))
            selected = next(item for item in clarification.candidates if item.token == token)
            for operation in intent_document["operations"]:
                if operation["operation_id"] == clarification.operation_id:
                    operation["target_query"]["exact_global_ids"] = [selected.public_id]
                    operation["target_query"]["names"] = []
        elif kind == "add_detail":
            repair_text = f"{repair_text}\n补充说明：{str(answer['detail']).strip()}"
            generated = self._intent_stage(
                provider=self.provider,
                request_id=str(intent_document["request_id"]),
                repair_request=repair_text,
                registry=self.registry,
                output_dir=run_dir / "intent" / f"resume-{resumed.state_version:03d}",
            )
            if not generated.get("valid") or generated.get("intent") is None:
                return self._fail(run_id, RunStage.PROVIDER_FAILED, "INTENT_RESUME_FAILED")
            intent_document = generated["intent"].to_dict()
        intent = RepairIntent.from_dict(intent_document, registry=self.registry)
        self._write_context(run_dir, repair_text=repair_text, intent=intent)
        return self._resolve_and_finish(run_id, intent, repair_text)

    def read_result(self, run_id: str) -> RunResult:
        return self.store.read_result(run_id)

    def _resolve_and_finish(self, run_id: str, intent: RepairIntent, repair_text: str) -> RunResult:
        state = self.store.load(run_id)
        run_dir = self.store.runs_root / run_id
        with SQLiteIndexRepository.open(
            run_dir / "index" / "targets.sqlite",
            expected_source_ifc_sha256=state.source.sha256,
        ) as repository:
            def stage2(resolution: Any) -> Mapping[str, Any]:
                generated = self._changeset_stage(
                    provider=self.provider,
                    case_id=run_id,
                    repair_request=repair_text,
                    source_request_hash=intent.source_request_hash,
                    resolved_operations=resolution.operations,
                    model_fingerprint=intent.model_fingerprint,
                    registry=self.registry,
                    output_dir=run_dir / "changeset",
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
            if outcome.status == "clarification_required":
                clarification = _clarification(run_id, state.state_version + 1, resolution)
                self.store.transition(
                    run_id,
                    to_stage=RunStage.CLARIFICATION_REQUIRED,
                    expected_state_version=state.state_version,
                    clarification=clarification,
                    reason_code=outcome.reason_code,
                    stage_payload={"resolution": "resolution.json"},
                )
                return self.store.read_result(run_id)
            state = self.store.transition(
                run_id,
                to_stage=RunStage.TARGETS_RESOLVED,
                expected_state_version=state.state_version,
                stage_payload={"resolution": "resolution.json"},
            )
            state = self.store.transition(
                run_id,
                to_stage=RunStage.CHANGESET_READY,
                expected_state_version=state.state_version,
                stage_payload={"changeset": "changeset.json"},
            )
            records = {
                record.ifc_global_id: record
                for record in repository.iter_records()
                if record.ifc_global_id
            }
            final = orchestrator.apply_and_evaluate(
                source_ifc_path=Path(state.source.reference),
                repair_request=repair_text,
                intent=intent,
                resolution=resolution,
                changeset=outcome.changeset,
                registry=self.registry,
                records_by_global_id=records,
            )
        state = self.store.transition(
            run_id,
            to_stage=RunStage.APPLICATION_READY,
            expected_state_version=state.state_version,
            stage_payload={"status": final.status},
        )
        state = self.store.transition(
            run_id,
            to_stage=RunStage.EVALUATED,
            expected_state_version=state.state_version,
            stage_payload={"status": final.status},
        )
        terminal = RunStage.SUCCEEDED if final.status == "succeeded" else RunStage.NOT_PUBLISHABLE
        artifacts = _artifact_references(run_dir, final)
        self.store.transition(
            run_id,
            to_stage=terminal,
            expected_state_version=state.state_version,
            reason_code=final.reason_code,
            stage_payload={"status": final.status},
            result_artifacts=artifacts,
        )
        return self.store.read_result(run_id)

    def _fail(self, run_id: str, stage: RunStage, reason: str) -> RunResult:
        state = self.store.load(run_id)
        self.store.transition(
            run_id,
            to_stage=stage,
            expected_state_version=state.state_version,
            reason_code=reason[:128],
            stage_payload={"reason_code": reason[:128]},
        )
        return self.store.read_result(run_id)

    @staticmethod
    def _write_context(run_dir: Path, *, repair_text: str, intent: RepairIntent) -> None:
        (run_dir / "api-context.json").write_text(
            json.dumps(
                {"schema_version": "text2ifc/ifc-repair-api-context/0.1", "repair_text": repair_text, "intent": intent.to_dict()},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n",
            encoding="utf-8",
        )


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
    modes = ("select_candidate", "add_detail", "cancel") if candidates else ("add_detail", "cancel")
    return Clarification(
        clarification_id=f"clarify-{version:03d}",
        run_id=run_id,
        state_version=version,
        operation_id=str(resolution.operation_id or "operation"),
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code=str(resolution.reason_code or "additional_target_detail"),
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
    evaluation = run_dir / "evaluation" / "public-evaluation.json"
    if evaluation.is_file():
        references["evaluation"] = evaluation.relative_to(run_dir).as_posix()
    return references


def _safe_code(error: Exception, fallback: str) -> str:
    code = getattr(error, "code", None)
    return str(code or fallback).split(":", 1)[0][:128]


__all__ = ["RepairAPI", "RunStoreError"]
