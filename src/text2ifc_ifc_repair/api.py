"""Single public IFC-path plus natural-language repair facade."""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, Mapping

import ifcopenshell

from .index_models import INDEX_SCHEMA_VERSION
from .index_store import SQLiteIndexRepository
from .indexer import build_ifc_index
from .operations import create_default_registry
from .orchestrator import OrchestrationResult, RepairOrchestrator
from .provider_stage import generate_bound_changeset
from .production_evidence import build_production_evidence
from .property_intent import NaturalLanguagePropertyIntent
from .property_resolution_coordinator import (
    DurablePropertyResolutionCoordinator,
    PendingPropertyClarification,
)
from .property_resolution_stage import generate_property_resolution_decision
from .semantic_authoring import semantic_manifest_to_dict
from .repair_intent import RepairIntent
from .repair_intent import REPAIR_INTENT_SCHEMA_VERSION_0_10
from .request_stage import generate_repair_intent
from .scene_context import PublicScene, SceneError
from .scene_grounding import generate_scene_repair_intent, SCENE_GROUNDING_VERSION
from .scene_diagnostics import checked_scene_diagnostics
from .run_models import (
    Clarification,
    ClarificationCandidate,
    RunResult,
    RunStage,
    RunStoreError,
    thaw_json,
)
from .run_store import RunStore
from .run_artifacts import publish_terminal_artifacts
from text2ifc_text.splits import atomic_write_text
from text2ifc_knowledge.property_search import (
    PropertyKnowledgeResolver,
    PropertyKnowledgeStore,
    build_project_property_records,
)
from text2ifc_knowledge.property_runtime import (
    create_property_runtime_from_environment,
)


def _source_ifc_schema(source_ifc_path: Path | str) -> str:
    """Probe schema without retaining the opened IFC model for later stages."""

    return str(
        ifcopenshell.open(str(Path(source_ifc_path).resolve())).schema
    )


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
        intent_schema_version: str = REPAIR_INTENT_SCHEMA_VERSION_0_10,
        scene_grounding: bool = False,
        max_validation_corrections: int = 2,
        property_knowledge_resolver: Any | None = None,
        property_knowledge_runtime: Any | None = None,
        property_resolution_stage: Callable[..., Mapping[str, Any]] = (
            generate_property_resolution_decision
        ),
    ) -> None:
        if type(max_validation_corrections) is not int or not 0 <= max_validation_corrections <= 2:
            raise ValueError("VALIDATION_CORRECTION_LIMIT_INVALID")
        self.max_validation_corrections = max_validation_corrections
        self.store = RunStore(output_root)
        self.provider = provider
        self.registry = registry or create_default_registry()
        self._intent_stage = intent_stage
        self._index_stage = index_stage
        self._changeset_stage = changeset_stage
        self._orchestrator_factory = orchestrator_factory
        self._intent_schema_version = intent_schema_version
        self._scene_grounding = scene_grounding
        self._property_knowledge_resolver = property_knowledge_resolver
        self._property_knowledge_runtime = property_knowledge_runtime
        self._property_resolution_stage = property_resolution_stage
        if (
            isinstance(property_knowledge_resolver, PropertyKnowledgeResolver)
            and property_knowledge_resolver.aliases
        ):
            raise ValueError("ACTIVE_REVIEWED_ALIASES_FORBIDDEN")
        requested_options = dict(orchestrator_options or {})
        if requested_options.get("defer_publication") is False:
            raise ValueError("DURABLE_PUBLICATION_CANNOT_BE_DISABLED")
        requested_options["defer_publication"] = True
        if requested_options.get("defer_changeset") is False:
            raise ValueError("DURABLE_CHANGESET_ORDER_CANNOT_BE_DISABLED")
        requested_options["defer_changeset"] = True
        if property_knowledge_resolver is not None:
            resolver_options = dict(requested_options.get("resolver_options") or {})
            resolver_options["property_knowledge_resolver"] = (
                property_knowledge_resolver
            )
            requested_options["resolver_options"] = resolver_options
        self._orchestrator_options = requested_options
        self._before_apply = None

    def configure_integration(self, *, before_apply=None, observer=None) -> None:
        """Attach Python-only caller identity checks and passive observation.

        Default CLI/Python callers retain the existing behavior. Hooks are never
        executable data supplied by an HTTP request or a Provider response.
        """
        if before_apply is not None and not callable(before_apply):
            raise TypeError("before_apply must be callable or None")
        if observer is not None and not callable(observer):
            raise TypeError("observer must be callable or None")
        self._before_apply = before_apply
        if observer is not None:
            self._orchestrator_options["observer"] = observer

    @classmethod
    def from_environment(
        cls, output_root: Path | str, environment: Mapping[str, str] | None = None,
        *, scene_grounding: bool = False,
        max_validation_corrections: int = 2,
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
        intent_schema_version = REPAIR_INTENT_SCHEMA_VERSION_0_10
        return cls(
            output_root,
            provider=OpenAICompatibleLiveProvider(config=config),
            intent_schema_version=intent_schema_version,
            scene_grounding=scene_grounding,
            max_validation_corrections=max_validation_corrections,
            property_knowledge_runtime=create_property_runtime_from_environment(
                dict(os.environ) if environment is None else dict(environment)
            ),
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
            if _source_ifc_schema(source_ifc_path) != "IFC2X3":
                return self._fail(state.run_id, RunStage.INVALID_INPUT, "IFC_SCHEMA_UNSUPPORTED")
        except Exception:
            return self._fail(state.run_id, RunStage.INVALID_INPUT, "IFC_SOURCE_INVALID")
        state = self.store.transition(
            state.run_id,
            to_stage=RunStage.SOURCE_VALIDATED,
            expected_state_version=state.state_version,
            stage_payload={"ifc_schema": "IFC2X3", "source_sha256": state.source.sha256,
                           "max_validation_corrections": self.max_validation_corrections},
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
        intent_result = self._generate_intent(
            state=state, run_dir=run_dir, scene_mode=self._scene_grounding,
            request_id=request_id,
            repair_request=repair_text,
            output_dir=intent_dir,
        )
        if not intent_result.get("valid") or intent_result.get("intent") is None:
            return self._fail(state.run_id, RunStage.PROVIDER_FAILED,
                              str(intent_result.get("error_code") or "INTENT_STAGE_FAILED"),
                              scene_diagnostics=intent_result.get("scene_diagnostics"))
        intent = intent_result["intent"]
        intent_path = intent_dir / "repair-intent.json"
        if not intent_path.exists():
            atomic_write_text(
                intent_path,
                json.dumps(intent.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            )
        context_ref = self._write_context(run_dir, repair_text=repair_text, intent=intent,
                                          scene_mode=self._scene_grounding,
                                          installation_references=intent_result.get("installation_references"),
                                          public_geometry_requirements=intent_result.get("public_geometry_requirements"))
        if intent_result.get("classification") == "unsupported":
            reason_code = str(
                intent_result.get("reason_code") or "OPERATION_UNSUPPORTED"
            )
            self.store.transition(
                state.run_id,
                to_stage=RunStage.INTENT_READY,
                expected_state_version=state.state_version,
                stage_payload={
                    **_scene_payload(intent_result),
                    "intent": self.store.artifact_binding(
                        state.run_id,
                        "intent/repair-intent.json",
                        self._intent_schema_version,
                    ),
                    "api_context": self.store.artifact_binding(
                        state.run_id,
                        context_ref,
                        _context_version(self._scene_grounding),
                    ),
                    "route": {
                        "classification": "unsupported",
                        "reason_code": reason_code,
                    },
                },
            )
            return self._fail(
                state.run_id,
                RunStage.UNSUPPORTED,
                reason_code,
            )
        missing_parameters = list(intent_result.get("missing_parameters") or ())
        if (
            intent_result.get("classification") == "clarification_required"
            or missing_parameters
        ):
            clarification = _parameter_clarification(
                state.run_id,
                state.state_version + 1,
                missing_parameters,
                scene_question=intent_result.get("scene_question"),
            )
            self.store.transition(
                state.run_id,
                to_stage=RunStage.CLARIFICATION_REQUIRED,
                expected_state_version=state.state_version,
                clarification=clarification,
                reason_code=clarification.reason_code,
                stage_payload={
                    **_scene_payload(intent_result),
                    "intent": self.store.artifact_binding(
                        state.run_id,
                        "intent/repair-intent.json",
                        self._intent_schema_version,
                    ),
                    "api_context": self.store.artifact_binding(
                        state.run_id,
                        context_ref,
                        _context_version(self._scene_grounding),
                    ),
                    "missing_parameters": missing_parameters,
                },
            )
            return self.store.read_result(state.run_id)
        state = self.store.transition(
            state.run_id,
            to_stage=RunStage.INTENT_READY,
            expected_state_version=state.state_version,
            stage_payload={
                **_scene_payload(intent_result),
                "intent": self.store.artifact_binding(
                    state.run_id, "intent/repair-intent.json", self._intent_schema_version
                ),
                "api_context": self.store.artifact_binding(
                    state.run_id, context_ref, _context_version(self._scene_grounding)
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
        scene_mode = _context_scene_mode(context)
        repair_text = str(context["repair_text"])
        intent_document = dict(context["intent"])
        kind = str(answer.get("kind", ""))
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
                stage_payload={},
                result_artifacts=cancel_artifacts,
                answer=answer,
                clarification_id=clarification_id,
            )
            return self.store.read_result(run_id)
        attempt_id = uuid.uuid4().hex
        resume_intent_ref: str | None = None
        missing_parameters: list[dict[str, Any]] = []
        scene_question: str | None = None
        generated: Mapping[str, Any] = {}
        property_resolution_answer: dict[str, str] | None = None
        property_resolution_generation: int | None = None
        if kind == "select_candidate" and clarification.reason_code == (
            "property_resolution"
        ):
            if clarification.claim_id is None:
                raise RunStoreError(
                    "RUN_STATE_CONFLICT",
                    "property clarification claim binding is missing",
                )
            property_resolution_answer = {
                "operation_id": clarification.operation_id,
                "claim_id": clarification.claim_id,
                "candidate_token": str(answer.get("candidate_token", "")),
            }
        elif kind == "select_candidate":
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
            generated = self._generate_intent(
                state=pending, run_dir=run_dir, scene_mode=scene_mode,
                request_id=str(intent_document["request_id"]),
                repair_request=repair_text,
                output_dir=resume_dir,
            )
            if not generated.get("valid") or generated.get("intent") is None:
                return self._fail(run_id, RunStage.PROVIDER_FAILED,
                                  str(generated.get("error_code") or "INTENT_RESUME_FAILED"),
                                  scene_diagnostics=generated.get("scene_diagnostics"))
            intent_document = generated["intent"].to_dict()
            missing_parameters = list(generated.get("missing_parameters") or ())
            scene_question = generated.get("scene_question")
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
        intent = RepairIntent.from_dict(
            intent_document,
            registry=self.registry,
            require_complete=not (missing_parameters or scene_question),
        )
        context_ref = self._write_context(
            run_dir, repair_text=repair_text, intent=intent,
            name=f"api-context-v{expected_state_version + 1:03d}-{attempt_id}.json",
            scene_mode=scene_mode,
            installation_references=(generated.get("installation_references", {})
                if kind == "add_detail" else context.get("installation_references", {})),
            public_geometry_requirements=(generated.get("public_geometry_requirements", {})
                if kind == "add_detail" else context.get("public_geometry_requirements", {})),
        )
        resume_payload: dict[str, Any] = {
            **_scene_payload(generated),
            "api_context": self.store.artifact_binding(
                run_id, context_ref, _context_version(scene_mode)
            )
        }
        if kind == "add_detail":
            assert resume_intent_ref is not None
            resume_payload["intent"] = self.store.artifact_binding(
                run_id,
                resume_intent_ref,
                self._intent_schema_version,
            )
            if clarification.reason_code == "property_resolution":
                property_resolution_generation = expected_state_version + 1
                resume_payload["property_resolution_generation"] = (
                    property_resolution_generation
                )
        resumed = self.store.continue_with_answer(
            run_id, clarification_id=clarification_id,
            expected_state_version=expected_state_version, answer=answer,
            stage_payload=resume_payload,
            result_artifacts=None,
        )
        if scene_mode and generated.get("classification") == "unsupported":
            return self._fail(run_id, RunStage.UNSUPPORTED,
                              str(generated.get("reason_code") or "REPAIR_REQUEST_OUT_OF_SCOPE"))
        if missing_parameters or scene_question:
            next_clarification = _parameter_clarification(
                run_id,
                resumed.state_version + 1,
                missing_parameters,
                scene_question=scene_question,
            )
            self.store.transition(
                run_id,
                to_stage=RunStage.CLARIFICATION_REQUIRED,
                expected_state_version=resumed.state_version,
                clarification=next_clarification,
                reason_code=next_clarification.reason_code,
                stage_payload={
                    **resume_payload,
                    "missing_parameters": missing_parameters,
                },
            )
            return self.store.read_result(run_id)
        if resumed.stage is RunStage.INDEX_READY:
            resumed = self.store.transition(
                run_id,
                to_stage=RunStage.INTENT_READY,
                expected_state_version=resumed.state_version,
                stage_payload=resume_payload,
            )
        prototype_answer = None
        property_answer = None
        if kind == "authorize_prototype":
            prototype_answer = {
                "operation_id": clarification.operation_id,
                "candidate_token": str(answer["candidate_token"]),
                "authorized": True,
            }
        elif kind in {"confirm_property", "reject_property"}:
            property_answer = {
                "operation_id": clarification.operation_id,
                "answer_kind": kind,
                "preview_hash": str(answer["preview_hash"]),
                "confirmation_ref": (
                    f"run:{run_id}/{clarification.clarification_id}"
                ),
            }
        return self._resolve_and_finish(
            run_id,
            intent,
            repair_text,
            prototype_answer=prototype_answer,
            property_answer=property_answer,
            property_resolution_answer=property_resolution_answer,
            property_resolution_generation=property_resolution_generation,
        )

    def read_result(self, run_id: str) -> RunResult:
        return self.store.read_result(run_id)

    def read_scene_diagnostics(self, run_id: str) -> dict | None:
        """Read the latest observation from the validated transition chain."""
        state = self.store.load(run_id)
        for transition in reversed(state.transitions):
            if "scene_diagnostics" in transition.stage_payload:
                return checked_scene_diagnostics(thaw_json(transition.stage_payload["scene_diagnostics"]))
        return None

    def _generate_intent(self, *, state: Any, run_dir: Path, scene_mode: bool,
                         request_id: str, repair_request: str, output_dir: Path) -> Mapping[str, Any]:
        arguments = dict(provider=self.provider, request_id=request_id, repair_request=repair_request,
                         registry=self.registry, output_dir=output_dir,
                         intent_schema_version=self._intent_schema_version)
        if not scene_mode:
            return self._intent_stage(**arguments)
        try:
            scene = PublicScene.from_ifc(state.source.reference, run_dir / "index/targets.sqlite",
                                         source_sha256=state.source.sha256)
        except (SceneError, RuntimeError, ValueError) as error:
            return {"valid": False, "intent": None, "error_code": _safe_code(error, "SCENE_READ_FAILED")}
        return generate_scene_repair_intent(**arguments, scene=scene)

    def resume(self, run_id: str) -> RunResult:
        """Resume a non-terminal run from its last committed public boundary."""

        state = self.store.load(run_id)
        if state.stage is RunStage.CLARIFICATION_REQUIRED:
            return self.store.read_result(run_id)
        if state.stage is RunStage.CHANGESET_READY:
            # A process interruption cannot reset an observed Provider budget or
            # replay uncertain side effects. Retain its candidates and terminate.
            run_dir = self.store.runs_root / run_id
            retained = []
            for path in sorted(run_dir.glob("validation-attempt-*.json")):
                document = json.loads(path.read_text(encoding="utf-8"))
                bindings = dict(document["artifacts"])
                for binding in bindings.values():
                    if self.store.artifact_binding(run_id, binding["path"], binding["schema_version"]) != binding:
                        raise RunStoreError("RUN_TAMPER_DETECTED", "validation attempt artifact changed")
                bindings["attempt"] = self.store.artifact_binding(run_id, path.name, "text2ifc/ifc-repair-validation-attempt/0.1")
                retained.append(bindings)
            return self._fail(run_id, RunStage.NOT_PUBLISHABLE, "VALIDATION_EXECUTION_INTERRUPTED",
                              validation_attempts=retained)
        if state.stage is not RunStage.INTENT_READY:
            raise RunStoreError(
                "RUN_STATE_CONFLICT",
                f"run cannot resume from {state.stage.value}",
            )
        context_path = self.store.runs_root / run_id / _latest_api_context(state)
        context = json.loads(context_path.read_text(encoding="utf-8"))
        intent = RepairIntent.from_dict(
            context["intent"],
            registry=self.registry,
        )
        return self._resolve_and_finish(
            run_id,
            intent,
            str(context["repair_text"]),
            property_resolution_generation=(
                _latest_property_resolution_generation(state)
            ),
        )

    def _resolve_and_finish(
        self, run_id: str, intent: RepairIntent, repair_text: str,
        *, prototype_answer: Mapping[str, Any] | None = None,
        property_answer: Mapping[str, Any] | None = None,
        property_resolution_answer: Mapping[str, Any] | None = None,
        property_resolution_generation: int | None = None,
    ) -> RunResult:
        state = self.store.load(run_id)
        run_dir = self.store.runs_root / run_id
        correction_limit = next((transition.stage_payload["max_validation_corrections"]
                                 for transition in state.transitions
                                 if "max_validation_corrections" in transition.stage_payload),
                                self.max_validation_corrections)
        with SQLiteIndexRepository.open(
            run_dir / "index" / "targets.sqlite",
            expected_source_ifc_sha256=state.source.sha256,
        ) as repository:
            records = {
                record.ifc_global_id: record
                for record in repository.iter_records()
                if record.ifc_global_id
            }
            type_records = {
                record.ifc_global_id: record
                for record in repository.iter_type_records()
                if record.ifc_global_id and record.identity_reliable
            }
            policy_facts: dict[str, tuple[Any, ...]] = {}
            verified_absence: dict[str, tuple[str, ...]] = {}

            def stage2(
                resolution: Any, *, validation_feedback: list[dict[str, str]] | None = None,
                correction_index: int = 0,
            ) -> Mapping[str, Any]:
                directory = "changeset" if not correction_index else f"validation-correction-{correction_index:03d}"
                changeset_dir = self.store.prepare_stage_directory(run_id, directory)
                feedback_arguments = {} if validation_feedback is None else {"validation_feedback": validation_feedback}
                if self._changeset_stage is not generate_bound_changeset:
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
                        **feedback_arguments,
                    )
                    if not generated.get("valid") or generated.get("changeset") is None:
                        raise ValueError("CHANGESET_STAGE_FAILED")
                    return generated["changeset"]
                authority_changeset = {
                    "operations": [
                        {
                            "operation_id": operation.operation_id,
                            "operation_type": operation.operation_type,
                        }
                        for operation in resolution.operations
                    ]
                }
                for operation in resolution.operations:
                    policy_operation = operation.to_dict()
                    policy_operation["target"] = (
                        self.registry.bind_resolved_target(
                            operation.operation_type,
                            operation.target_global_id,
                        )
                    )
                    policy_facts[operation.operation_id] = (
                        self.registry.build_semantic_policy_facts(
                            operation.operation_type,
                            operation=policy_operation,
                        )
                    )
                    policy = self.registry.require_evaluation_policy(
                        operation.operation_type
                    )
                    verified_absence[operation.operation_id] = tuple(
                        spec.check_id
                        for spec in policy.semantic_facts
                        if spec.applicability.value == "conditional"
                    )
                production_evidence = build_production_evidence(
                    intent=intent,
                    resolution=resolution,
                    changeset=authority_changeset,
                    registry=self.registry,
                    records_by_global_id=records,
                    type_records_by_global_id=type_records,
                    deterministic_policy_facts_by_operation=policy_facts,
                    verified_absent_categories_by_operation=verified_absence,
                )
                manifests = tuple(
                    self.registry.build_semantic_manifest(
                        production_evidence.operation_types[operation_id],
                        production_evidence=production_evidence,
                        operation_id=operation_id,
                        base_model_fingerprint=resolution.source_ifc_sha256,
                    )
                    for operation_id in sorted(production_evidence.operation_types)
                )
                manifest_payloads: dict[str, str] = {}
                for manifest in manifests:
                    payload = json.dumps(
                        semantic_manifest_to_dict(manifest),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ) + "\n"
                    manifest_path = changeset_dir / f"semantic-manifest-{manifest.operation_id}.json"
                    atomic_write_text(manifest_path, payload)
                    manifest_payloads[manifest.operation_id] = payload
                if len(manifests) == 1:
                    only = manifests[0]
                    semantic_manifest_ref = (
                        f"{directory}/semantic-manifest-{only.operation_id}.json"
                    )
                    semantic_manifest_hash = (
                        "sha256:"
                        + hashlib.sha256(
                            manifest_payloads[only.operation_id].encode("utf-8")
                        ).hexdigest()
                    )
                else:
                    bundle_payload = (
                        json.dumps(
                            {
                                "schema_version": (
                                    "text2ifc/ifc-repair-semantic-manifest-bundle/0.1"
                                ),
                                "manifests": [
                                    semantic_manifest_to_dict(manifest)
                                    for manifest in manifests
                                ],
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                            allow_nan=False,
                        )
                        + "\n"
                    )
                    atomic_write_text(
                        changeset_dir / "semantic-manifests.json",
                        bundle_payload,
                    )
                    semantic_manifest_ref = f"{directory}/semantic-manifests.json"
                    semantic_manifest_hash = (
                        "sha256:"
                        + hashlib.sha256(bundle_payload.encode("utf-8")).hexdigest()
                    )
                # ChangeSet 0.2 binds one immutable semantic-authority artifact.
                # For a batch, that artifact is the ordered manifest bundle.
                manifest_hashes = {
                    manifest.operation_id: semantic_manifest_hash
                    for manifest in manifests
                }
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
                    semantic_manifests=manifests,
                    semantic_manifest_hashes=manifest_hashes,
                    semantic_manifest_ref=semantic_manifest_ref,
                    **feedback_arguments,
                )
                if not generated.get("valid") or generated.get("changeset") is None:
                    raise ValueError("CHANGESET_STAGE_FAILED")
                return generated["changeset"]

            orchestrator_options = dict(self._orchestrator_options)
            resolver_options = dict(
                orchestrator_options.get("resolver_options") or {}
            )
            property_coordinator: DurablePropertyResolutionCoordinator | None = None
            if _has_natural_property_claims(intent):
                if self._property_knowledge_runtime is None:
                    return self._fail(
                        run_id,
                        RunStage.PROVIDER_FAILED,
                        "PROPERTY_RUNTIME_NOT_READY",
                    )
                property_coordinator = DurablePropertyResolutionCoordinator(
                    store=self.store,
                    run_id=run_id,
                    intent=intent,
                    runtime=self._property_knowledge_runtime,
                    provider=self.provider,
                    property_resolution_stage=self._property_resolution_stage,
                    selected_candidate_answer=property_resolution_answer,
                    claim_generation=property_resolution_generation,
                )
                resolver_options["property_knowledge_resolver"] = (
                    property_coordinator
                )
            else:
                resolver_options["property_knowledge_resolver"] = (
                    self._resolver_with_project_facts(
                        repository,
                        state.source.sha256,
                    )
                )
            if intent.schema_version == REPAIR_INTENT_SCHEMA_VERSION_0_10:
                resolver_options["source_ifc_path"] = state.source.reference
            public_context = json.loads((run_dir / _latest_api_context(state)).read_text(encoding="utf-8"))
            if _context_scene_mode(public_context):
                resolver_options["installation_references"] = public_context.get("installation_references", {})
            orchestrator_options["resolver_options"] = resolver_options
            orchestrator = self._orchestrator_factory(
                run_directory=run_dir,
                changeset_stage=stage2,
                operation_registry=self.registry,
                **orchestrator_options,
            )
            try:
                try:
                    outcome = orchestrator.start(
                        intent=intent,
                        repository=repository,
                        expected_source_sha256=state.source.sha256,
                    )
                finally:
                    if property_coordinator is not None:
                        release = getattr(
                            self._property_knowledge_runtime,
                            "release_transient_resources",
                            None,
                        )
                        if callable(release):
                            release()
            except Exception as error:
                return self._fail(
                    run_id,
                    RunStage.PROVIDER_FAILED,
                    _safe_code(error, type(error).__name__),
                )
            resolution = orchestrator._resolution
            if prototype_answer is not None and resolution.status == "clarification_required" and resolution.reason_code == "prototype_selection":
                outcome = orchestrator.continue_with_answer(prototype_answer)
                resolution = orchestrator._resolution
            if (
                property_answer is not None
                and resolution.status == "clarification_required"
                and resolution.reason_code == "property_confirmation"
            ):
                outcome = orchestrator.continue_with_answer(property_answer)
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
                state = self.store.load(run_id)
                clarification = (
                    _property_resolution_clarification(
                        run_id,
                        state.state_version + 1,
                        property_coordinator.pending_clarification,
                    )
                    if (
                        property_coordinator is not None
                        and property_coordinator.pending_clarification is not None
                    )
                    else _clarification(
                        run_id,
                        state.state_version + 1,
                        resolution,
                    )
                )
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
            state = self.store.load(run_id)
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
            try:
                outcome = orchestrator.advance_to_changeset()
            except Exception as error:
                return self._fail(
                    run_id,
                    RunStage.PROVIDER_FAILED,
                    _safe_code(error, "CHANGESET_STAGE_FAILED"),
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
                ), "max_validation_corrections": correction_limit},
            )
            self.store.prepare_stage_directory(run_id, "staging")
            application_arguments = dict(
                source_ifc_path=Path(state.source.reference),
                repair_request=repair_text,
                intent=intent,
                resolution=resolution,
                changeset=outcome.changeset,
                registry=self.registry,
                records_by_global_id=records,
                type_records_by_global_id=type_records,
                deterministic_policy_facts_by_operation=policy_facts,
                verified_absent_categories_by_operation=verified_absence,
            )
            if public_context.get("public_geometry_requirements"):
                application_arguments["public_geometry_requirements"] = public_context["public_geometry_requirements"]
            seen_changesets = {_executable_changeset_hash(outcome.changeset)}
            validation_attempts: list[dict[str, Any]] = []
            validation_corrections: list[dict[str, Any]] = []
            for candidate_index in range(correction_limit + 1):
                # Validate immutable source and previously committed boundaries
                # immediately before each candidate. Never apply to a prior IFC.
                self.store.load(run_id)
                if self._before_apply is not None:
                    try:
                        check = self._before_apply({
                            "run_directory": str(run_dir),
                            "source_ifc_path": state.source.reference,
                            "intent": intent.to_dict(),
                            "resolution": json.loads((run_dir / resolution_ref).read_text(encoding="utf-8")),
                            "installation_references": public_context.get("installation_references", {}),
                        })
                        atomic_write_text(run_dir / "selection-check.json", json.dumps(check, ensure_ascii=False, allow_nan=False))
                        if not isinstance(check, Mapping) or check.get("valid") is not True:
                            issues = check.get("issues", []) if isinstance(check, Mapping) else []
                            reason = str(issues[0].get("code", "SELECTION_CHECK_FAILED")) if issues else "SELECTION_CHECK_FAILED"
                            return self._fail(run_id, RunStage.AUDIT_FAILED, reason,
                                              validation_attempts=validation_attempts)
                    except Exception:
                        return self._fail(run_id, RunStage.AUDIT_FAILED, "SELECTION_CHECK_ERROR",
                                          validation_attempts=validation_attempts)
                final = orchestrator.apply_and_evaluate(
                    **application_arguments,
                    **({} if candidate_index == 0 else {"candidate_name": f"validation-candidate-{candidate_index + 1:03d}.ifc"}),
                )
                attempt = self._save_validation_attempt(run_id, candidate_index + 1, final, application_arguments["changeset"])
                validation_attempts.append(attempt)
                feedback = _public_validation_feedback(final, bound_changeset=application_arguments["changeset"])
                if not feedback:
                    break
                if candidate_index >= correction_limit:
                    final = replace(final, reason_code="VALIDATION_CORRECTION_EXHAUSTED")
                    break
                # The just-failed bundle and candidate are retained before any
                # feedback or additional Provider transport. One Provider object
                # carries the existing cumulative observer across all attempts.
                self.store.load(run_id)
                try:
                    outcome = orchestrator.regenerate_changeset(
                        validation_feedback=feedback, correction_index=candidate_index + 1,
                    )
                except Exception as error:
                    return self._fail(run_id, RunStage.PROVIDER_FAILED,
                                      _safe_code(error, "CHANGESET_STAGE_FAILED"),
                                      validation_attempts=validation_attempts)
                validation_corrections.append(self.store.artifact_binding(
                    run_id, f"changeset-correction-{candidate_index + 1:03d}.json",
                    str(outcome.changeset.get("schema_version", "text2ifc/ifc-repair-changeset/0.1")),
                ))
                digest = _executable_changeset_hash(outcome.changeset)
                if digest in seen_changesets:
                    final = replace(final, reason_code="VALIDATION_CHANGESET_REPEATED")
                    break
                seen_changesets.add(digest)
                application_arguments["changeset"] = outcome.changeset
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
            stage_payload={"status": final.status,
                           "validation_attempts": _committed_attempt_bindings(validation_attempts, final.prepared_root),
                           "validation_corrections": validation_corrections},
            result_artifacts=artifacts,
        )
        return self.store.read_result(run_id)

    def _resolver_with_project_facts(
        self,
        repository: Any,
        source_ifc_sha256: str,
    ) -> Any:
        resolver = self._property_knowledge_resolver
        if resolver is None:
            return None
        if not isinstance(resolver, PropertyKnowledgeResolver):
            return resolver
        standard_paths = {
            (record.set_name, record.property_name)
            for record in resolver.records
            if record.authority == "ifc2x3_psd"
        }
        extracted_project = tuple(
            record
            for record in build_project_property_records(
                repository.iter_records(),
                source_ifc_sha256=source_ifc_sha256,
            )
            if (record.set_name, record.property_name) not in standard_paths
        )
        store = PropertyKnowledgeStore(
            self.store.root / "knowledge" / "property-knowledge.sqlite"
        )
        store.ensure_project_corpus(
            source_ifc_sha256=source_ifc_sha256,
            records=extracted_project,
        )
        project = store.load_project_records(source_ifc_sha256)
        return PropertyKnowledgeResolver(
            registry=resolver.registry,
            records=(*resolver.records, *project),
            aliases=resolver.aliases,
            vector_index=resolver.vector_index,
            max_candidates=resolver.max_candidates,
            vector_min_score=resolver.vector_min_score,
            vector_min_margin=resolver.vector_min_margin,
        )

    def _save_validation_attempt(
        self, run_id: str, index: int, result: OrchestrationResult, changeset: Mapping[str, Any],
    ) -> dict[str, Any]:
        run_dir = self.store.runs_root / run_id
        name = f"validation-attempt-{index:03d}.json"
        path = run_dir / name
        if path.exists():
            raise RunStoreError("RUN_STATE_CONFLICT", "validation attempt already exists")
        bindings = {}
        for key, value in _artifact_references(run_dir, result).items():
            bindings[key] = self.store.artifact_binding(run_id, value, "text2ifc/ifc-repair-validation-artifact/0.1")
        if result.manifest:
            evidence = Path(result.manifest).parent / "terminal/evidence.json"
            bindings["evidence"] = self.store.artifact_binding(run_id, evidence.relative_to(run_dir).as_posix(), "text2ifc/ifc-repair-validation-artifact/0.1")
        changeset_path = "changeset.json" if index == 1 else f"changeset-correction-{index - 1:03d}.json"
        bindings["changeset"] = self.store.artifact_binding(run_id, changeset_path, str(changeset.get("schema_version", "text2ifc/ifc-repair-changeset/0.1")))
        document = {"schema_version": "text2ifc/ifc-repair-validation-attempt/0.1",
                    "candidate_index": index, "status": result.status,
                    "reason_code": result.reason_code, "evaluation": result.evaluation,
                    "artifacts": bindings}
        atomic_write_text(path, json.dumps(document, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")
        bindings["attempt"] = self.store.artifact_binding(run_id, name, "text2ifc/ifc-repair-validation-attempt/0.1")
        return bindings

    def _fail(self, run_id: str, stage: RunStage, reason: str,
              *, validation_attempts: list[dict[str, Any]] | None = None,
              scene_diagnostics: dict | None = None) -> RunResult:
        state = self.store.load(run_id)
        diagnostics = checked_scene_diagnostics(scene_diagnostics) if scene_diagnostics is not None else self.read_scene_diagnostics(run_id)
        artifacts, prepared_root = self._publish_failure_bundle(
            run_id, stage, reason[:128], state.stage.value, scene_diagnostics=diagnostics
        )
        self.store.commit_terminal_publication(
            run_id,
            prepared_root=prepared_root,
            to_stage=stage,
            expected_state_version=state.state_version,
            reason_code=reason[:128],
            stage_payload={"reason_code": reason[:128],
                           **({"scene_diagnostics": diagnostics} if diagnostics is not None else {}),
                           **({"validation_attempts": validation_attempts} if validation_attempts else {})},
            result_artifacts=artifacts,
        )
        return self.store.read_result(run_id)

    def _publish_failure_bundle(
        self, run_id: str, stage: RunStage, reason: str, from_stage: str,
        *, scene_diagnostics: dict | None = None,
    ) -> tuple[dict[str, str], str]:
        run_dir = self.store.runs_root / run_id
        published = publish_terminal_artifacts(
            run_directory=run_dir, terminal_status=stage.value,
            evaluation=_terminal_failure_evaluation(reason), candidate_ifc_path=None,
            evidence={"reason_code": reason, "stage": from_stage,
                      **({"scene_diagnostics": scene_diagnostics} if scene_diagnostics is not None else {})},
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
        scene_mode: bool = False,
        installation_references: Mapping[str, Any] | None = None,
        public_geometry_requirements: Mapping[str, Any] | None = None,
    ) -> str:
        payload = (
            json.dumps(
                {"schema_version": _context_version(scene_mode), "repair_text": repair_text, "intent": intent.to_dict(),
                 **({"scene_grounding_version": SCENE_GROUNDING_VERSION,
                     "installation_references": dict(installation_references or {}),
                     "public_geometry_requirements": dict(public_geometry_requirements or {})} if scene_mode else {})},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n"
        )
        atomic_write_text(run_dir / name, payload)
        return name


def _scene_payload(result: Mapping[str, Any]) -> dict:
    value = checked_scene_diagnostics(result.get("scene_diagnostics"))
    return {"scene_diagnostics": value} if value is not None else {}


def _required_parameter_slot(item: Any) -> str | None:
    if not isinstance(item, Mapping):
        return None
    if item.get("slot"):
        return str(item["slot"])
    path = item.get("path")
    if (
        isinstance(path, str)
        and path.startswith("/parameters/")
        and isinstance(item.get("fact"), str)
        and item["fact"]
        and not any(key in item for key in ("token", "public_id", "ifc_class"))
    ):
        # Structural hooks describe missing facts with paths, not identities.
        return path
    return None


def _clarification(run_id: str, version: int, resolution: Any) -> Clarification:
    raw_candidates = tuple(resolution.candidates)
    slots = tuple(
        slot
        for item in raw_candidates
        if (slot := _required_parameter_slot(item)) is not None
    )
    candidates = tuple(
        ClarificationCandidate(
            token=str(item["token"]),
            public_id=str(item["public_id"]),
            ifc_class=str(item["ifc_class"]),
            name=item.get("name"),
            storey=item.get("storey"),
            position=item.get("position"),
            evidence=tuple(str(value) for value in item.get("evidence", ())),
            candidate_kind=str(item.get("candidate_kind", "target")),
            dimensions=dict(item.get("dimensions") or {}),
            occurrence_count=int(item.get("occurrence_count", 0)),
            storeys=tuple(str(value) for value in item.get("storeys", ())),
        )
        for item in raw_candidates
        if not slots
    )
    reason_map = {
        "ambiguous": "ambiguous_target", "conflict": "selector_conflict",
        "not_found": "additional_target_detail", "missing_evidence": "additional_target_detail",
        "prototype_selection": "prototype_selection",
        "property_confirmation": "property_confirmation",
    }
    reason = (
        "missing_required_parameter"
        if slots
        else reason_map.get(
            str(resolution.reason_code), "additional_target_detail"
        )
    )
    modes = (
        ("authorize_prototype", "cancel") if reason == "prototype_selection"
        else ("confirm_property", "reject_property", "cancel")
        if reason == "property_confirmation"
        else ("select_candidate", "add_detail", "cancel") if candidates
        else ("add_detail", "cancel")
    )
    question = (
        "操作仍需明确输入（"
        + str(resolution.reason_code)
        + "）："
        + "、".join(slots)
        + "。请补充说明或取消。"
        if slots
        else "目标不唯一或证据不足，请选择候选、补充说明或取消。"
    )
    if str(resolution.reason_code).startswith("EXACT_TYPE_") or resolution.reason_code == "TYPE_PROPERTY_MUTATION_DEFERRED":
        reason = "additional_target_detail"
        modes = ("add_detail", "cancel")
        question = "指定 Type 与请求语义需要澄清（" + str(resolution.reason_code) + "）。请明确保留 Type 定义、调整请求，或显式授权合法的实例属性覆盖；不会修改共享 Type。"
    return Clarification(
        clarification_id=f"clarify-{version:03d}",
        run_id=run_id,
        state_version=version,
        operation_id=str(resolution.operation_id or "operation"),
        stage=RunStage.TARGETS_RESOLVED,
        resume_stage=RunStage.INTENT_READY,
        reason_code=reason,
        question=question,
        answer_modes=modes,
        candidates=candidates,
        property_preview=(
            None
            if getattr(resolution, "property_preview", None) is None
            else _public_property_preview(resolution.property_preview)
        ),
    )


def _property_resolution_clarification(
    run_id: str,
    version: int,
    pending: PendingPropertyClarification,
) -> Clarification:
    candidates = tuple(
        ClarificationCandidate(
            token=str(item["candidate_id"]),
            public_id=str(item["record_id"]),
            ifc_class=str(item["applicable_classes"][0]),
            name=str(item["canonical_path"]),
            storey=None,
            position=None,
            evidence=(
                f"definition:{str(item['definition'])[:320]}",
                f"vector-score:{float(item['score']):.6f}",
            ),
            candidate_kind="property",
        )
        for item in pending.candidates
    )
    return Clarification(
        clarification_id=f"clarify-{version:03d}",
        run_id=run_id,
        state_version=version,
        operation_id=pending.operation_id,
        claim_id=pending.claim_id,
        stage=RunStage.INTENT_READY,
        resume_stage=RunStage.INTENT_READY,
        reason_code="property_resolution",
        question=pending.question,
        answer_modes=(
            ("select_candidate", "add_detail", "cancel")
            if candidates
            else ("add_detail", "cancel")
        ),
        candidates=candidates,
    )


def _has_natural_property_claims(intent: RepairIntent) -> bool:
    return any(
        isinstance(claim, NaturalLanguagePropertyIntent)
        for operation in intent.operations
        for claim in operation.property_intents
    ) or any(
        isinstance(claim, NaturalLanguagePropertyIntent)
        for bundle in intent.semantic_bundles
        for claim in bundle.property_intents
    )


def _public_property_preview(preview: Mapping[str, Any]) -> dict[str, Any]:
    """Keep multi-operation confirmation public records bounded and readable."""

    if preview.get("preview_kind") != "property_transaction":
        return dict(preview)
    batches = [
        {
            "operation_id": str(item["operation_id"]),
            "target_global_id": str(item["target_global_id"]),
            "item_count": len(item.get("items", ())),
            "batch_hash": str(item["preview_hash"]),
        }
        for item in preview.get("batches", ())
    ]
    return {
        "preview_kind": "property_transaction",
        "request_hash": str(preview["request_hash"]),
        "model_fingerprint": str(preview["model_fingerprint"]),
        "batches": batches,
        "total_item_count": sum(item["item_count"] for item in batches),
        "preview_hash": str(preview["preview_hash"]),
    }


def _parameter_clarification(
    run_id: str,
    version: int,
    missing_parameters: list[dict[str, Any]],
    *, scene_question: str | None = None,
) -> Clarification:
    labels = {
        "/opening/width_mm": "窗宽",
        "/opening/height_mm": "窗高",
        "/opening/sill_height_mm": "窗台高度",
        "/position/center_offset_mm": "窗中心距墙局部起点的距离",
    }
    first = missing_parameters[0] if missing_parameters else {
        "operation_id": "operation",
        "paths": [],
    }
    paths = [str(path) for path in first.get("paths", ())]
    fields = "、".join(labels.get(path, path) for path in paths)
    question = (
        f"操作 {first.get('operation_id', 'operation')} 还缺少：{fields}。"
        "请补充这些数值及单位；系统不会猜测缺失的几何参数。"
    )
    return Clarification(
        clarification_id=f"clarify-{version:03d}",
        run_id=run_id,
        state_version=version,
        operation_id=str(first.get("operation_id") or "operation"),
        stage=RunStage.INTENT_READY,
        resume_stage=RunStage.INDEX_READY,
        reason_code="additional_target_detail" if scene_question else "missing_required_parameter",
        question=scene_question or question,
        answer_modes=("add_detail", "cancel"),
        candidates=(),
    )


def _context_version(scene_mode: bool) -> str:
    return "text2ifc/ifc-repair-api-context/0.4" if scene_mode else "text2ifc/ifc-repair-api-context/0.1"


def _context_scene_mode(context: Mapping[str, Any]) -> bool:
    version = context.get("scene_grounding_version")
    if version not in (None, SCENE_GROUNDING_VERSION):
        raise RunStoreError("RUN_STATE_CONFLICT", "saved scene method is unsupported; no implicit migration")
    return version == SCENE_GROUNDING_VERSION


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


def _executable_changeset_hash(changeset: Mapping[str, Any]) -> str:
    """Ignore labels and relocated authority refs; retain executable content."""
    document = json.loads(json.dumps(changeset, ensure_ascii=False, allow_nan=False))
    for key in ("changeset_id", "draft_id", "semantic_manifest_ref"):
        document.pop(key, None)
    for key in ("preconditions", "postconditions", "evidence_refs"):
        if key in document:
            document[key] = sorted(set(document[key]))
    if isinstance(document.get("scope"), Mapping):
        document["scope"] = {key: sorted(set(value)) for key, value in document["scope"].items()}
    for operation in document.get("operations", ()):
        if "evidence_refs" in operation:
            operation["evidence_refs"] = sorted(set(operation["evidence_refs"]))
    rendered = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _public_validation_feedback(
    result: OrchestrationResult, *, bound_changeset: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Describe public checks and their already-bound operation/location.

    Missing authority, preservation, path/source/identity/scope, reopen/schema,
    or unmeasurable gates stop. Exception reports are not correction facts.
    """
    report = result.evaluation
    if result.reason_code or result.status not in {"l1_failed", "l2_failed", "l2_partial"} or not isinstance(report, Mapping):
        return []
    if report.get("successful_artifact_publishable") is not False or report.get("complete_repair_success") is not False:
        return []
    if any((report.get(key) or {}).get("status") != "passed" for key in ("application", "preservation")):
        return []
    changeset = result.changeset if bound_changeset is None else bound_changeset
    if not isinstance(changeset, Mapping):
        return []
    bound = {item["operation_id"]: item for item in changeset.get("operations", ())}
    feedback = []
    unsafe = ("source", "preservation", "scope", "authority", "reopen", "schema", "private", "identity", "fingerprint", "unauthor", "unoffered", "conflict")
    for operation_index, operation in enumerate(report.get("operations", ())):
        public_operation = bound.get(operation.get("operation_id"))
        if (public_operation is None
                or public_operation.get("operation_type") != operation.get("operation_type")):
            return []
        for level_index, level in enumerate(operation.get("levels", ())):
            if level.get("status") == "not_evaluable":
                return []
            for check_index, check in enumerate(level.get("checks", ())):
                if check.get("mandatory") is not True:
                    continue
                status = check.get("status")
                if status == "not_evaluable":
                    return []
                if status not in {"failed", "partial"}:
                    continue
                identifier = str(check.get("check_id", ""))
                if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", identifier) or any(token in identifier.casefold() for token in unsafe):
                    return []
                descriptions = {
                    "dimension": "The required dimensions were not satisfied",
                    "type": "The required IFC type assignment was not satisfied",
                    "material": "The required material assignment was not satisfied",
                    "classification": "The required classification was not satisfied",
                    "quantity": "The required quantity assignment was not satisfied",
                    "pset": "The required property-set assignment was not satisfied",
                    "label": "The required label assignment was not satisfied",
                    "host": "The required host relationship was not satisfied",
                    "storey": "The required storey relationship was not satisfied",
                    "is_external": "The required exterior/interior property was not satisfied",
                    "physical": "The required physical/output checks were not satisfied",
                }
                description = descriptions.get(check.get("difference_category"), "A mandatory production check was not satisfied")
                if identifier == "l2.public-request-geometry":
                    description = "The output's world geometry differs from the original public placement requirement"
                message = (f"Error: {description} ({identifier}, {status}). "
                           f"Location: {_validation_location(public_operation)}. "
                           "Regenerate this ChangeSet within the unchanged public bindings.")
                feedback.append({"code": "PRODUCTION_CHECK_FAILED",
                                 "path": f"/operations/{operation_index}/levels/{level_index}/checks/{check_index}",
                                 "message": message[:512]})
    return feedback if 0 < len(feedback) <= 32 else []


def _validation_location(operation: Mapping[str, Any]) -> str:
    """Only public bound targets/position facts; no evaluator free text/values."""
    target = operation.get("target", {})
    identities = [f"{key}={value}" for key, value in target.items()
                  if key.endswith("_global_id") and isinstance(value, str)
                  and re.fullmatch(r"[0-9A-Za-z_$]{22}", value)]
    parameters = operation.get("parameters", {})
    position = parameters.get("position", {})
    facts = {}
    if position.get("reference") in {"wall_local_start", "world", "global"}:
        facts["reference"] = position["reference"]
    for key in ("center_offset_mm", "x_mm", "y_mm", "z_mm", "elevation_mm"):
        value = position.get(key)
        if type(value) in {int, float} and math.isfinite(value):
            facts[key] = value
    sill = parameters.get("opening", {}).get("sill_height_mm")
    if type(sill) in {int, float} and math.isfinite(sill):
        facts["sill_height_mm"] = sill
    context = ", ".join(identities[:2]) or "the already-bound target"
    if facts:
        context += "; " + json.dumps(facts, ensure_ascii=False, separators=(",", ":"))
    return f"operation {operation['operation_id']} ({operation['operation_type']}), {context}"[:280]


def _committed_attempt_bindings(attempts: list[dict[str, Any]], prepared_root: str | None) -> list[dict[str, Any]]:
    # The winning/final prepared root moves through RunStore's journal. Its
    # canonical manifest binds the relocated bytes; prior failed bundles stay.
    name = Path(prepared_root).name if prepared_root else None
    return [{key: binding for key, binding in attempt.items()
             if name is None or not str(binding["path"]).startswith(name + "/")}
            for attempt in attempts]


def _safe_code(error: Exception, fallback: str) -> str:
    code = getattr(error, "code", None)
    detail = str(error).strip()
    return str(code or detail or fallback).split(":", 1)[0][:128]


def _latest_api_context(state: Any) -> str:
    for transition in reversed(state.transitions):
        payload = transition.stage_payload
        binding = payload.get("api_context") if isinstance(payload, Mapping) else None
        if isinstance(binding, Mapping) and binding.get("path"):
            return str(binding["path"])
    raise RunStoreError("RUN_TAMPER_DETECTED", "api context binding is missing")


def _latest_property_resolution_generation(state: Any) -> int | None:
    for transition in reversed(state.transitions):
        value = transition.stage_payload.get("property_resolution_generation")
        if value is not None:
            return int(value)
    return None


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
