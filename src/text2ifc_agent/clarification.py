"""Deterministic controller for model-authored clarification turns."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, replace
from typing import Any, Callable

from .design_brief import validate_design_brief


class ClarificationError(ValueError):
    """Raised when a live clarification transition is not auditable."""


@dataclass(frozen=True)
class ClarificationTurn:
    turn_id: str
    role: str
    content: str
    question_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "role": self.role,
            "content": self.content,
            "question_ids": list(self.question_ids),
        }


@dataclass(frozen=True)
class ClarificationCall:
    call_index: int
    response_id: str
    prompt_template_id: str
    prompt_template_hash: str
    artifact_dir: str
    brief: dict[str, Any]
    evidence_catalog: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_index": self.call_index,
            "response_id": self.response_id,
            "prompt_template_id": self.prompt_template_id,
            "prompt_template_hash": self.prompt_template_hash,
            "artifact_dir": self.artifact_dir,
            "brief": copy.deepcopy(self.brief),
            "evidence_catalog": copy.deepcopy(self.evidence_catalog),
        }


DesignBriefInvoker = Callable[[list[dict[str, Any]], int], ClarificationCall]


@dataclass(frozen=True)
class ClarificationController:
    case_id: str
    original_request: str
    transcript: tuple[ClarificationTurn, ...]
    calls: tuple[ClarificationCall, ...] = ()
    status: str = "awaiting_model"
    pending_question_ids: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def start(
        cls,
        *,
        case_id: str,
        user_request: str,
    ) -> "ClarificationController":
        if not case_id or not user_request:
            raise ClarificationError("case_id and user_request must be non-empty")
        return cls(
            case_id=case_id,
            original_request=user_request,
            transcript=(
                ClarificationTurn(
                    turn_id="turn-user-001",
                    role="user",
                    content=user_request,
                ),
            ),
        )

    def record_model_call(
        self,
        call: ClarificationCall,
    ) -> "ClarificationController":
        expected_index = len(self.calls) + 1
        if call.call_index != expected_index:
            raise ClarificationError(
                f"expected call_index {expected_index}, got {call.call_index}"
            )
        if not call.response_id:
            raise ClarificationError("live Design Brief call is missing response_id")
        if not call.prompt_template_id or not call.prompt_template_hash:
            raise ClarificationError("live Design Brief call is missing prompt identity")

        issues = validate_design_brief(
            call.brief,
            evidence_catalog=call.evidence_catalog,
        )
        if issues:
            rendered = ", ".join(
                f"{issue.code}@{issue.path}" for issue in issues
            )
            raise ClarificationError(f"invalid Design Brief call: {rendered}")
        if call.brief.get("original_request") != self.original_request:
            raise ClarificationError("Design Brief changed the original request")
        self._validate_source_turns(call.brief)

        status = str(call.brief["status"])
        transcript = list(self.transcript)
        pending: list[str] = []
        if status == "needs_clarification":
            questions = call.brief.get("clarification_questions", [])
            for question in questions:
                question_id = str(question["id"])
                transcript.append(
                    ClarificationTurn(
                        turn_id=_next_turn_id(transcript, "assistant"),
                        role="assistant",
                        content=str(question["text"]),
                        question_ids=(question_id,),
                    )
                )
                pending.append(question_id)

        stored_call = ClarificationCall(
            call_index=call.call_index,
            response_id=call.response_id,
            prompt_template_id=call.prompt_template_id,
            prompt_template_hash=call.prompt_template_hash,
            artifact_dir=call.artifact_dir,
            brief=copy.deepcopy(call.brief),
            evidence_catalog=copy.deepcopy(call.evidence_catalog),
        )
        return replace(
            self,
            transcript=tuple(transcript),
            calls=(*self.calls, stored_call),
            status=status,
            pending_question_ids=tuple(pending),
        )

    def answer_and_rerun(
        self,
        *,
        answer: str,
        invoke_design_brief: DesignBriefInvoker,
    ) -> "ClarificationController":
        if self.status != "needs_clarification" or not self.pending_question_ids:
            raise ClarificationError("no open model-authored clarification question")
        if not answer:
            raise ClarificationError("user answer must be preserved as non-empty text")
        transcript = (
            *self.transcript,
            ClarificationTurn(
                turn_id=_next_turn_id(list(self.transcript), "user"),
                role="user",
                content=answer,
                question_ids=self.pending_question_ids,
            ),
        )
        awaiting = replace(
            self,
            transcript=transcript,
            status="awaiting_model",
            pending_question_ids=(),
        )
        next_call = invoke_design_brief(
            awaiting.transcript_dicts(),
            len(awaiting.calls) + 1,
        )
        return awaiting.record_model_call(next_call)

    def transcript_dicts(self) -> list[dict[str, Any]]:
        return [turn.to_dict() for turn in self.transcript]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "text2ifc/live-clarification-state/1.0",
            "case_id": self.case_id,
            "original_request": self.original_request,
            "status": self.status,
            "pending_question_ids": list(self.pending_question_ids),
            "transcript": self.transcript_dicts(),
            "calls": [call.to_dict() for call in self.calls],
        }

    def _validate_source_turns(self, brief: dict[str, Any]) -> None:
        existing = {turn.turn_id for turn in self.transcript}
        referenced: list[str] = []
        for collection_name in (
            "fact_sources",
            "missing_facts",
            "ambiguities",
            "unsupported_requests",
        ):
            for record in brief.get(collection_name, []):
                if isinstance(record, dict):
                    referenced.extend(str(item) for item in record.get("source_turns", []))
        for record in brief.get("user_corrections", []):
            if isinstance(record, dict) and record.get("source_turn"):
                referenced.append(str(record["source_turn"]))
        provenance = brief.get("provenance", {})
        if isinstance(provenance, dict):
            referenced.extend(
                str(item) for item in provenance.get("source_turns", [])
            )
        unknown = sorted(set(referenced) - existing)
        if unknown:
            raise ClarificationError(
                "Design Brief references transcript turns that do not exist: "
                + ", ".join(unknown)
            )


def _next_turn_id(transcript: list[ClarificationTurn], role: str) -> str:
    return f"turn-{role}-{len(transcript) + 1:03d}"
