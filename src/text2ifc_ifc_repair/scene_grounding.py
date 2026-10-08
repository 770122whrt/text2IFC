"""Bounded request + public scene stage with actual Provider/query evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from text2ifc_agent.prompt_registry import PROJECT_ROOT, render_prompt
from text2ifc_agent.providers import ProviderOutputError
from text2ifc_text.splits import atomic_write_text
from .registry import OperationRegistryError
from .repair_intent import RepairIntentError, REPAIR_INTENT_SCHEMA_VERSION_0_10
from .prompt_profiles import PromptProfileError
from .request_stage import (
    MAX_REQUEST_BYTES, MAX_PROVIDER_RESPONSE_BYTES, _call_provider,
    _compact_supported_profiles, _attempt_record, _write_live_evidence,
    _pretty_json, _prompt_identity, parse_repair_intent_body, finish_repair_intent,
)
from .scene_context import PublicScene, SceneError, class_matches
from .spatial_grounding import bind_spatial_intent, GroundingError


SCENE_GROUNDING_VERSION = "text2ifc/ifc-scene-grounding/0.2"
TEMPLATE_ID = "ifc-scene-grounding.v0.2"
MAX_ROUNDS = 8
MAX_CONTEXT_BYTES = 384 * 1024


def load_scene_response_schema() -> dict:
    return json.loads((PROJECT_ROOT / "schemas/agent/ifc-scene-grounding-response-0.2.schema.json").read_text(encoding="utf-8"))


def generate_scene_repair_intent(*, provider: Any, request_id: str, repair_request: str,
                                 registry: Any, output_dir: Path | str, scene: PublicScene,
                                 intent_schema_version: str = REPAIR_INTENT_SCHEMA_VERSION_0_10,
                                 max_rounds: int = MAX_ROUNDS) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if intent_schema_version != REPAIR_INTENT_SCHEMA_VERSION_0_10:
        return _failure("SCENE_INTENT_VERSION_UNSUPPORTED", [])
    if len(repair_request.encode("utf-8")) > MAX_REQUEST_BYTES:
        return _failure("REPAIR_REQUEST_TOO_LARGE", [])
    if not 1 <= max_rounds <= MAX_ROUNDS:
        return _failure("SCENE_ROUND_BUDGET_INVALID", [])
    schema = load_scene_response_schema()
    validator = Draft202012Validator(schema)
    catalog = _compact_supported_profiles(registry, intent_schema_version=intent_schema_version)
    overview = scene.overview()
    atomic_write_text(output / "scene-overview.json", _pretty_json(overview))
    attempts, feedback = [], []
    rendered = None
    for round_number in range(1, max_rounds+1):
        inputs = {"REPAIR_REQUEST": repair_request, "SUPPORTED_OPERATIONS": catalog,
                  "CURRENT_PUBLIC_SCENE": overview, "SCENE_QUERIES": scene.pages,
                  "VALIDATION_FEEDBACK": feedback, "RESPONSE_SCHEMA": schema}
        if len(_pretty_json(inputs).encode("utf-8")) > MAX_CONTEXT_BYTES:
            return _failure("SCENE_CONTEXT_BUDGET_EXCEEDED", attempts)
        rendered = render_prompt(template_id=TEMPLATE_ID, inputs=inputs)
        round_dir = output / f"round-{round_number:03d}"
        round_dir.mkdir()
        atomic_write_text(round_dir / "renderer-input.json", _pretty_json(inputs))
        atomic_write_text(round_dir / "rendered-prompt.md", rendered["text"])
        issues, metadata, raw_text, live_evidence = [], {}, "", None
        final_intent, question, derivations = None, None, []
        try:
            response, live_evidence = _call_provider(provider, {
                "session_id": f"ifc-repair-scene-{request_id}", "prompt": rendered["text"], "schema": schema,
                "state": {"request_id": request_id, "stage": "ifc_repair_scene_grounding", "attempt": round_number}})
            raw_text, metadata = response.text, response.metadata
            if len(raw_text.encode("utf-8")) > MAX_PROVIDER_RESPONSE_BYTES:
                raise GroundingError("SCENE_RESPONSE_TOO_LARGE")
            status, parsed, parse_issues = response.parse_json()
            if status != "ok" or parse_issues or parsed is None:
                raise GroundingError("SCENE_RESPONSE_INVALID_JSON")
            errors = list(validator.iter_errors(parsed))
            if errors:
                raise GroundingError("SCENE_RESPONSE_SCHEMA_INVALID: " + errors[0].message[:300])
            if parsed["kind"] == "query":
                scene.query(parsed["query"])
                atomic_write_text(output / "scene-queries.json", _pretty_json(scene.pages))
                feedback = []
            else:
                body = parsed["intent"]
                if parsed["kind"] == "intent":
                    body, derivations = bind_spatial_intent(body, parsed["bindings"], scene)
                final_intent, _ = parse_repair_intent_body(body, registry=registry, request_id=request_id,
                    repair_request=repair_request, model=str(metadata.get("model", "")),
                    prompt_hash=rendered["metadata"]["template_hash"], intent_schema_version=intent_schema_version)
                if parsed["kind"] == "clarification":
                    _validate_clarification(parsed, final_intent, scene, registry)
                    question = parsed["question"]
        except ProviderOutputError as error:
            # Failed HTTP/SDK attempts retain the same available evidence as the
            # original intent stage. The outer wire observer accounts all calls.
            if error.live_result is not None:
                live_evidence = {"request": error.live_result.request, "response": error.live_result.response,
                                 "events": list(error.live_result.events)}
            issues = [{"code": "PROVIDER_REQUEST_FAILED", "path": "", "message": type(error).__name__}]
        except (GroundingError, SceneError, RepairIntentError, OperationRegistryError, PromptProfileError) as error:
            issues = [{"code": str(getattr(error, "code", str(error).split(":",1)[0])),
                       "path": str(getattr(error, "path", "")), "message": str(error)[:500]}]
            final_intent = None
        attempt = _attempt_record(attempt_number=round_number, issues=issues, provider_metadata=metadata,
                                  raw_text=raw_text, valid=not issues, normalizations=[])
        attempts.append(attempt)
        atomic_write_text(round_dir / f"attempt-{round_number:03d}.json", _pretty_json(attempt))
        atomic_write_text(round_dir / "raw-response.txt", raw_text)
        _write_live_evidence(round_dir, round_number, live_evidence)
        if issues:
            feedback = issues
            continue
        if final_intent is not None:
            # A derived host-local position must be resolved in this stage, not
            # turned back into a request for an internal offset from the user.
            missing_positions = [p for op in final_intent.operations
                                 for p in registry.missing_required_parameters(op.to_dict())
                                 if p.startswith("/position/")]
            if missing_positions and not question and not final_intent.unsupported_requests:
                feedback = [{"code": "SCENE_POSITION_NOT_GROUNDED", "path": "/bindings",
                             "message": "Query and ground the requested world/relative position; do not ask for a native local offset."}]
                continue
            result = finish_repair_intent(final_intent, registry=registry, output=output, attempts=attempts,
                                         prompt=_prompt_identity(rendered))
            if question and result["classification"] != "unsupported":
                result.update(classification="clarification_required", scene_question=question)
            atomic_write_text(output / "scene-queries.json", _pretty_json(scene.pages))
            atomic_write_text(output / "grounding-evidence.json", _pretty_json({
                "schema_version": SCENE_GROUNDING_VERSION, "derivations": derivations,
                "offered_ids": sorted(scene.offered_ids), "scene_question": question}))
            result["scene_grounding_version"] = SCENE_GROUNDING_VERSION
            from .door_geometry import public_wall_face_adaptation_requested
            wall_face_permission = public_wall_face_adaptation_requested(repair_request)
            # Trusted internal metadata, produced only after offered-identity
            # and reference/type verification. Never accept this from Stage 2.
            result["installation_references"] = {
                item["operation_id"]: {
                    "reference_global_id": item["reference_occurrence_id"],
                    "target_global_id": item["target_id"],
                    **({"wall_face_adaptation_authorized": True} if wall_face_permission else {}),
                }
                for item in derivations
                if item.get("reference_occurrence_id") and any(
                    op.operation_id == item["operation_id"]
                    and op.operation_type in {"fill_existing_opening_with_door", "add_door_with_opening_to_wall", "add_window_with_opening_to_wall"}
                    for op in final_intent.operations
                )
            }
            return result
    return _failure("SCENE_GROUNDING_EXHAUSTED", attempts)


def _validate_clarification(parsed: dict, intent: Any, scene: PublicScene, registry: Any) -> None:
    for identity in parsed["candidate_ids"]:
        candidate = scene.offered_record(identity)
        if not any(class_matches(candidate['ifc_class'], c) for op in intent.operations
                   for c in op.target_query.allowed_ifc_classes):
            raise GroundingError("SCENE_CLARIFICATION_CANDIDATE_CLASS_MISMATCH")
    for op in intent.operations:
        identity = op.target_query.global_id
        if identity:
            scene.offered_record(identity)
    if parsed["reason"] == "ambiguous_target":
        if len(parsed["candidate_ids"]) < 2:
            raise GroundingError("SCENE_AMBIGUITY_NEEDS_CANDIDATES")
    else:
        missing = [p for op in intent.operations for p in registry.missing_required_parameters(op.to_dict())]
        if not missing or all(p.startswith("/position/") for p in missing):
            raise GroundingError("SCENE_CLARIFICATION_NOT_A_USER_FACT")
    question = parsed["question"].lower()
    if any(term in question for term in ("guid", "globalid", "name", "局部起点", "局部偏移")):
        raise GroundingError("SCENE_CLARIFICATION_REQUESTS_INTERNAL_FACT")


def _failure(code: str, attempts: list[dict]) -> dict:
    return {"valid": False, "intent": None, "attempts": attempts, "error_code": code}
