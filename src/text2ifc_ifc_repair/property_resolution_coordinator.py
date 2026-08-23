"""Durable public coordinator for natural-language property resolution."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from text2ifc_knowledge.property_search import (
    PropertyCandidate,
    PropertyKnowledgeQuery,
    PropertyResolutionDecision,
    ResolvedExactProperty,
)
from text2ifc_text.splits import atomic_write_text

from .property_admissibility import admit_property_decision
from .property_intent import ExactPropertyIntent, NaturalLanguagePropertyIntent
from .property_resolution_stage import generate_property_resolution_decision
from .run_models import RunStage


@dataclass(frozen=True)
class PendingPropertyClarification:
    operation_id: str
    claim_id: str
    reason_code: str
    question: str
    candidates: tuple[Mapping[str, Any], ...]


class PropertyResolutionCoordinatorError(ValueError):
    """Stable failure before Stage 2 when durable property state is invalid."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class DurablePropertyResolutionCoordinator:
    """Adapt the new runtime/stage/gate to the existing resolver protocol."""

    def __init__(
        self,
        *,
        store: Any,
        run_id: str,
        intent: Any,
        runtime: Any,
        provider: Any,
        property_resolution_stage: Any = generate_property_resolution_decision,
        selected_candidate_answer: Mapping[str, Any] | None = None,
        claim_generation: int | None = None,
    ) -> None:
        self.store = store
        self.run_id = run_id
        self.intent = intent
        self.runtime = runtime
        self.provider = provider
        self._property_resolution_stage = property_resolution_stage
        self._selected_candidate_answer = dict(selected_candidate_answer or {})
        self._claim_generation = claim_generation
        self.pending_clarification: PendingPropertyClarification | None = None
        self._operation_ordinals = {
            operation.operation_id: index
            for index, operation in enumerate(intent.operations, start=1)
        }

    def resolve(self, query: PropertyKnowledgeQuery) -> PropertyResolutionDecision:
        raise PropertyResolutionCoordinatorError("PROPERTY_CLAIM_BINDING_REQUIRED")

    def resolve_for_claim(
        self,
        *,
        operation_id: str,
        operation_type: str,
        claim_id: str,
        claim: NaturalLanguagePropertyIntent,
        query: PropertyKnowledgeQuery,
    ) -> PropertyResolutionDecision:
        if self._claim_generation is not None:
            claim_id = f"{claim_id}-resume-{self._claim_generation:03d}"
        claim_dir, relative_root = self._claim_directory(operation_id, claim_id)
        answer_token = self._answer_token(operation_id, claim_id)
        checkpoint_suffix = "user" if answer_token is not None else "provider"

        candidate_checkpoint = self._checkpoint(
            operation_id,
            claim_id,
            "candidates",
        )
        if candidate_checkpoint is None:
            try:
                retrieval = self.runtime.retrieve(
                    run_id=self.run_id,
                    request_id=self.intent.request_id,
                    model_id=self.intent.model_fingerprint,
                    operation_id=operation_id,
                    operation_type=operation_type,
                    claim_id=claim_id,
                    property_phrase=str(claim.property_phrase),
                    target_ifc_class=query.target_ifc_class,
                    raw_value=claim.raw_value,
                    raw_unit=claim.raw_unit,
                    scope=claim.scope,
                    project_length_unit=query.project_length_unit,
                )
            except Exception as error:
                code = str(getattr(error, "code", str(error))).split(":", 1)[0]
                self.pending_clarification = PendingPropertyClarification(
                    operation_id=operation_id,
                    claim_id=claim_id,
                    reason_code=code or "PROPERTY_VECTOR_UNAVAILABLE",
                    question=(
                        "Property retrieval is unavailable for this request. "
                        "Please add detail later or cancel."
                    ),
                    candidates=(),
                )
                return self._decision(
                    status="clarification_required",
                    reason_code=code or "PROPERTY_VECTOR_UNAVAILABLE",
                    exact=None,
                    candidate_set={"candidates": []},
                )
            query_document = retrieval.query
            candidate_set = retrieval.candidate_set
            query_ref = f"{relative_root}/query.json"
            candidates_ref = f"{relative_root}/candidate-set.json"
            self._write_once(claim_dir / "query.json", query_document)
            self._write_once(claim_dir / "candidate-set.json", candidate_set)
            self._commit_checkpoint(
                operation_id=operation_id,
                claim_id=claim_id,
                checkpoint="candidates",
                artifacts={
                    "query": self._reference(
                        query_ref,
                        str(query_document["schema_version"]),
                        query_id=str(query_document["query_id"]),
                    ),
                    "candidate_set": self._reference(
                        candidates_ref,
                        str(candidate_set["schema_version"]),
                        candidate_set_id=str(candidate_set["candidate_set_id"]),
                    ),
                },
            )
        else:
            query_document = self._read_reference(candidate_checkpoint, "query")
            candidate_set = self._read_reference(
                candidate_checkpoint,
                "candidate_set",
            )
        committed_candidates = self._checkpoint(
            operation_id,
            claim_id,
            "candidates",
        )
        assert committed_candidates is not None
        self._require_current_runtime(
            query_document,
            candidate_set,
            committed_candidates,
        )

        if not candidate_set["candidates"]:
            self.pending_clarification = PendingPropertyClarification(
                operation_id=operation_id,
                claim_id=claim_id,
                reason_code="PROPERTY_RETRIEVAL_BELOW_FLOOR",
                question=(
                    "No class-applicable scalar property met the configured "
                    "retrieval floor. Please add detail or cancel."
                ),
                candidates=(),
            )
            return self._decision(
                status="clarification_required",
                reason_code="PROPERTY_RETRIEVAL_BELOW_FLOOR",
                exact=None,
                candidate_set=candidate_set,
            )

        decision_checkpoint_name = (
            "user_decision" if answer_token is not None else "decision"
        )
        decision_checkpoint = self._checkpoint(
            operation_id,
            claim_id,
            decision_checkpoint_name,
        )
        if decision_checkpoint is None:
            if answer_token is None:
                result = self._property_resolution_stage(
                    query=query_document,
                    candidate_set=candidate_set,
                    output_dir=claim_dir / "provider",
                    provider=self.provider,
                )
                if not result.get("valid") or result.get("decision") is None:
                    raise PropertyResolutionCoordinatorError(
                        str(
                            result.get("error_code")
                            or "PROPERTY_RESOLUTION_PROVIDER_FAILED"
                        )
                    )
            else:
                offered_ids = {
                    str(item["candidate_id"])
                    for item in candidate_set["candidates"]
                }
                if answer_token not in offered_ids:
                    raise PropertyResolutionCoordinatorError(
                        "PROPERTY_CANDIDATE_NOT_OFFERED"
                    )
                decision = {
                    "schema_version": (
                        "text2ifc/ifc-property-rerank-decision/0.1"
                    ),
                    "decision": "confirmed",
                    "selected_candidate_id": answer_token,
                    "conflicting_candidate_ids": [],
                    "clarification_question": None,
                }
                result = {
                    "valid": True,
                    "classification": "confirmed",
                    "decision": decision,
                    "trace": self._user_trace(
                        query_document,
                        candidate_set,
                    ),
                    "attempts": [],
                    "evidence_class": "public_user_answer",
                    "acceptance_eligible": False,
                    "error_code": None,
                }
            decision_ref = (
                f"{relative_root}/decision-result-{checkpoint_suffix}.json"
            )
            self._write_once(
                claim_dir / f"decision-result-{checkpoint_suffix}.json",
                result,
            )
            self._commit_checkpoint(
                operation_id=operation_id,
                claim_id=claim_id,
                checkpoint=decision_checkpoint_name,
                artifacts={
                    "decision": self._reference(
                        decision_ref,
                        "text2ifc/ifc-property-resolution-result/0.1",
                        decision_id=(
                            f"property-decision:{self.run_id}:"
                            f"{operation_id}:{claim_id}"
                        ),
                    )
                },
            )
        else:
            result = self._read_reference(decision_checkpoint, "decision")

        decision_document = dict(result["decision"])
        trace = dict(result["trace"])
        admissibility_checkpoint_name = (
            "user_admissibility" if answer_token is not None else "admissibility"
        )
        admissibility_checkpoint = self._checkpoint(
            operation_id,
            claim_id,
            admissibility_checkpoint_name,
        )
        if admissibility_checkpoint is None:
            admission = admit_property_decision(
                query=query_document,
                candidate_set=candidate_set,
                decision=decision_document,
                decision_trace=trace,
                policy=self.runtime.policy,
                records=self.runtime.records,
                registry=self.runtime.registry,
                claim=claim,
                project_length_unit=query.project_length_unit,
            )
            admissibility_ref = (
                f"{relative_root}/admissibility-{checkpoint_suffix}.json"
            )
            self._write_once(
                claim_dir / f"admissibility-{checkpoint_suffix}.json",
                admission.to_dict(),
            )
            artifacts = {
                "admissibility": self._reference(
                    admissibility_ref,
                    "text2ifc/ifc-property-admissibility/0.1",
                    admissibility_id=str(
                        admission.to_dict()["admissibility_id"]
                    ),
                )
            }
            if admission.exact_intent is not None:
                exact_ref = f"{relative_root}/exact-intent-{checkpoint_suffix}.json"
                self._write_once(
                    claim_dir / f"exact-intent-{checkpoint_suffix}.json",
                    admission.exact_intent.to_dict(),
                )
                artifacts["exact_intent"] = self._reference(
                    exact_ref,
                    str(self.intent.schema_version),
                )
            self._commit_checkpoint(
                operation_id=operation_id,
                claim_id=claim_id,
                checkpoint=admissibility_checkpoint_name,
                artifacts=artifacts,
            )
            admission_status = admission.status
            reason_code = admission.reason_code
            exact = admission.exact_intent
        else:
            admission_document = self._read_reference(
                admissibility_checkpoint,
                "admissibility",
            )
            admission_status = str(admission_document["status"])
            reason_code = str(admission_document["reason_code"])
            exact_ref = admissibility_checkpoint["artifacts"].get("exact_intent")
            exact = (
                None
                if exact_ref is None
                else ExactPropertyIntent.from_dict(
                    self._read_document(str(exact_ref["path"]))
                )
            )

        if admission_status == "passed" and exact is not None:
            return self._decision(
                status="standard_resolved",
                reason_code="PROPERTY_ADMISSIBLE_STAGE_1_5",
                exact=exact,
                candidate_set=candidate_set,
            )
        if admission_status == "unsupported":
            return self._decision(
                status="unsupported",
                reason_code=reason_code,
                exact=None,
                candidate_set=candidate_set,
            )
        candidate_ids = tuple(
            str(item)
            for item in decision_document.get("conflicting_candidate_ids", ())
        )
        if not candidate_ids and decision_document.get("selected_candidate_id"):
            candidate_ids = (str(decision_document["selected_candidate_id"]),)
        offered = {
            str(item["candidate_id"]): item
            for item in candidate_set["candidates"]
        }
        selected_candidates = tuple(
            offered[item] for item in candidate_ids if item in offered
        )
        self.pending_clarification = PendingPropertyClarification(
            operation_id=operation_id,
            claim_id=claim_id,
            reason_code=(
                "property_resolution"
                if admission_status in {
                    "clarification_required",
                    "custom_confirmation_required",
                }
                else reason_code
            ),
            question=str(
                decision_document.get("clarification_question")
                or "Select the intended property candidate or cancel."
            ),
            candidates=selected_candidates,
        )
        return self._decision(
            status="clarification_required",
            reason_code=reason_code,
            exact=None,
            candidate_set=candidate_set,
        )

    def _claim_directory(
        self,
        operation_id: str,
        claim_id: str,
    ) -> tuple[Path, str]:
        operation_ordinal = self._operation_ordinals[operation_id]
        root = "property-resolution"
        operation_root = f"{root}/operation-{operation_ordinal:03d}"
        relative = f"{operation_root}/{claim_id}"
        self.store.prepare_stage_directory(self.run_id, root)
        self.store.prepare_stage_directory(self.run_id, operation_root)
        directory = self.store.prepare_stage_directory(self.run_id, relative)
        return directory, relative

    def _answer_token(self, operation_id: str, claim_id: str) -> str | None:
        if (
            self._selected_candidate_answer.get("operation_id") != operation_id
            or self._selected_candidate_answer.get("claim_id") != claim_id
        ):
            return None
        token = self._selected_candidate_answer.get("candidate_token")
        return None if token is None else str(token)

    def _checkpoint(
        self,
        operation_id: str,
        claim_id: str,
        checkpoint: str,
    ) -> Mapping[str, Any] | None:
        state = self.store.load(self.run_id)
        for transition in reversed(state.transitions):
            payload = transition.stage_payload.get("property_resolution")
            if not isinstance(payload, Mapping):
                continue
            if (
                payload.get("operation_id") == operation_id
                and payload.get("claim_id") == claim_id
                and payload.get("checkpoint") == checkpoint
            ):
                return payload
        return None

    def _commit_checkpoint(
        self,
        *,
        operation_id: str,
        claim_id: str,
        checkpoint: str,
        artifacts: Mapping[str, Any],
    ) -> None:
        state = self.store.load(self.run_id)
        if state.stage is not RunStage.INTENT_READY:
            raise PropertyResolutionCoordinatorError(
                "PROPERTY_RESOLUTION_RUN_STAGE_INVALID"
            )
        self.store.transition(
            self.run_id,
            to_stage=RunStage.INTENT_READY,
            expected_state_version=state.state_version,
            stage_payload={
                "property_resolution": {
                    "checkpoint": checkpoint,
                    "run_id": self.run_id,
                    "operation_id": operation_id,
                    "claim_id": claim_id,
                    "policy_id": str(self.runtime.policy["policy_id"]),
                    "policy_version": str(self.runtime.policy["version"]),
                    "minimum_retrieval_score": float(
                        self.runtime.policy["minimum_retrieval_score"]
                    ),
                    "max_candidates": int(self.runtime.policy["max_candidates"]),
                    "artifacts": dict(artifacts),
                }
            },
        )

    def _require_current_runtime(
        self,
        query: Mapping[str, Any],
        candidate_set: Mapping[str, Any],
        checkpoint: Mapping[str, Any],
    ) -> None:
        health = self.runtime.health
        if health.status != "ready":
            raise PropertyResolutionCoordinatorError("PROPERTY_RUNTIME_NOT_READY")
        if (
            checkpoint.get("policy_id") != self.runtime.policy.get("policy_id")
            or checkpoint.get("policy_version")
            != self.runtime.policy.get("version")
            or float(checkpoint.get("minimum_retrieval_score", -1.0))
            != float(self.runtime.policy.get("minimum_retrieval_score", -2.0))
            or int(checkpoint.get("max_candidates", -1))
            != int(self.runtime.policy.get("max_candidates", -2))
        ):
            raise PropertyResolutionCoordinatorError("PROPERTY_POLICY_CHANGED")
        expected = {
            "corpus_version": health.corpus_version,
            "embedding_model": {
                "model_id": health.embedding_model_id,
                "model_version": health.embedding_model_version,
            },
            "document_renderer_version": health.document_renderer_version,
            "collection_version": health.collection_version,
        }
        if query.get("corpus_version") != expected["corpus_version"]:
            raise PropertyResolutionCoordinatorError(
                "PROPERTY_RUNTIME_VERSION_CHANGED"
            )
        for key, value in expected.items():
            if key != "corpus_version" and candidate_set.get(key) != value:
                raise PropertyResolutionCoordinatorError(
                    "PROPERTY_RUNTIME_VERSION_CHANGED"
                )

    def _decision(
        self,
        *,
        status: str,
        reason_code: str,
        exact: ExactPropertyIntent | None,
        candidate_set: Mapping[str, Any],
    ) -> PropertyResolutionDecision:
        return PropertyResolutionDecision(
            status=status,
            reason_code=reason_code,
            exact_intent=(
                None
                if exact is None
                else ResolvedExactProperty(
                    set_name=str(exact.set_name),
                    property_name=str(exact.property_name),
                    value=exact.value,
                    requested_value_type=str(exact.requested_value_type),
                    requested_unit=exact.requested_unit,
                    scope=str(exact.scope),
                )
            ),
            candidates=self._candidate_objects(candidate_set),
        )

    def _candidate_objects(
        self,
        candidate_set: Mapping[str, Any],
    ) -> tuple[PropertyCandidate, ...]:
        records = {
            record.canonical_path: record for record in self.runtime.records
        }
        return tuple(
            PropertyCandidate(
                record=records[str(item["canonical_path"])],
                retrieval_paths=("vector",),
                vector_score=float(item["score"]),
            )
            for item in candidate_set.get("candidates", ())
            if str(item["canonical_path"]) in records
        )

    def _read_reference(
        self,
        checkpoint: Mapping[str, Any],
        name: str,
    ) -> dict[str, Any]:
        return self._read_document(
            str(checkpoint["artifacts"][name]["path"])
        )

    def _read_document(self, relative: str) -> dict[str, Any]:
        path = self.store.runs_root / self.run_id / Path(relative)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise PropertyResolutionCoordinatorError(
                "PROPERTY_RESOLUTION_ARTIFACT_INVALID"
            ) from error
        if not isinstance(value, dict):
            raise PropertyResolutionCoordinatorError(
                "PROPERTY_RESOLUTION_ARTIFACT_INVALID"
            )
        return value

    @staticmethod
    def _reference(
        path: str,
        schema_version: str,
        **identities: str,
    ) -> dict[str, str]:
        # Stable IDs and versions bind this stage. Phase 12.1 deliberately adds
        # no cryptographic hash/fingerprint as property authorization.
        return {
            "path": path,
            "schema_version": schema_version,
            **identities,
        }

    @staticmethod
    def _write_once(path: Path, value: Mapping[str, Any]) -> None:
        payload = (
            json.dumps(
                dict(value),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        )
        if path.exists():
            if path.read_text(encoding="utf-8") != payload:
                raise PropertyResolutionCoordinatorError(
                    "PROPERTY_RESOLUTION_ARTIFACT_CONFLICT"
                )
            return
        atomic_write_text(path, payload)

    def _user_trace(
        self,
        query: Mapping[str, Any],
        candidate_set: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "run_id": query["run_id"],
            "request_id": query["request_id"],
            "model_id": query["model_id"],
            "operation_id": query["operation_id"],
            "claim_id": query["claim_id"],
            "query_id": query["query_id"],
            "candidate_set_id": candidate_set["candidate_set_id"],
            "provider_call_ordinal": "property_resolution",
            "status": "valid",
            "evidence_class": "public_user_answer",
        }


__all__ = [
    "DurablePropertyResolutionCoordinator",
    "PendingPropertyClarification",
    "PropertyResolutionCoordinatorError",
]
