"""Bounded request + public scene stage with actual Provider/query evidence."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from text2ifc_agent.prompt_registry import PROJECT_ROOT, render_prompt
from text2ifc_agent.providers import ProviderOutputError
from text2ifc_agent.openai_compat import OpenAICompatError
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
from .scene_diagnostics import SCENE_DIAGNOSTICS_VERSION, checked_scene_diagnostics
from .public_geometry import public_geometry_capability


SCENE_GROUNDING_VERSION = "text2ifc/ifc-scene-grounding/0.7"
TEMPLATE_ID = "ifc-scene-grounding.v0.7"
MAX_ROUNDS = 8
MAX_CONTEXT_BYTES = 384 * 1024
MAX_PREVIOUS_PROPOSAL_BYTES = 16 * 1024
MAX_FEEDBACK_ISSUES = 5


class _SchemaFeedbackError(GroundingError):
    def __init__(self, issues: list[dict]):
        super().__init__("SCENE_RESPONSE_SCHEMA_INVALID")
        self.issues = issues


def _schema_issues(document: Any, schema: dict) -> list[dict]:
    """Report leaf constraints for the actual tagged response, never its JSON dump."""
    kind = document.get("kind") if isinstance(document, dict) else None
    if isinstance(document, dict) and kind not in ("query", "intent", "clarification"):
        return [{"code": "SCENE_RESPONSE_SCHEMA_INVALID", "path": "/kind",
                 "message": "Expected kind: query, intent or clarification."}]
    branch = next((branch for branch in schema["oneOf"]
                   if branch.get("properties", {}).get("kind", {}).get("const") == kind), None)
    selected = {**{key: value for key, value in schema.items() if key != "oneOf"}, **branch} if branch else schema
    errors = list(Draft202012Validator(selected).iter_errors(document))

    def leaves(error):
        if error.context:
            contexts = error.context
            if error.validator in {"oneOf", "anyOf"} and isinstance(error.instance, dict):
                variants = error.validator_value
                matching = []
                for index, variant in enumerate(variants):
                    tags = {key: spec["const"] for key, spec in variant.get("properties", {}).items() if "const" in spec}
                    if tags and all(error.instance.get(key) == value for key, value in tags.items()):
                        matching.append(index)
                if matching:
                    contexts = [child for child in contexts if child.schema_path[0] in matching]
            for child in contexts:
                yield from leaves(child)
        else:
            yield error

    issues = []
    for error in errors:
        for leaf in leaves(error):
            path = list(leaf.absolute_path)
            if leaf.validator == "required" and isinstance(leaf.instance, dict):
                missing = [key for key in leaf.validator_value if key not in leaf.instance]
                # jsonschema emits one error for each missing member; use this
                # error's exact known schema key rather than a response value.
                key = next((key for key in missing if leaf.message == f"'{key}' is a required property"), missing[0])
                path.append(key)
                message = f"Required property: {key}"
            elif leaf.validator in {"enum", "const", "type", "minimum", "maximum", "minItems", "maxItems", "minLength", "maxLength", "pattern"}:
                message = f"Expected {leaf.validator}: {json.dumps(leaf.validator_value, ensure_ascii=False)}"[:300]
            elif leaf.validator == "additionalProperties":
                message = "Unexpected property; only the schema's named properties are allowed."
            else:
                message = f"Constraint failed: {leaf.validator}. Use the response schema at this path."
            pointer = "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in path) if path else ""
            issue = {"code": "SCENE_RESPONSE_SCHEMA_INVALID", "path": pointer[:256], "message": message}
            if issue not in issues:
                issues.append(issue)
            if len(issues) >= MAX_FEEDBACK_ISSUES:
                return issues
    return issues


def _bounded_proposal(parsed: Any, raw_text: str) -> Any:
    proposal = parsed if parsed is not None else {"unparsed_excerpt": raw_text}
    encoded = _pretty_json(proposal).encode("utf-8")
    if len(encoded) <= MAX_PREVIOUS_PROPOSAL_BYTES:
        return proposal
    # A valid JSON envelope stays bounded even when the proposal itself is not
    # parseable. Reserve space for escaping quotes/backslashes in the excerpt.
    excerpt = encoded[:MAX_PREVIOUS_PROPOSAL_BYTES // 3].decode("utf-8", errors="ignore")
    return {"truncated": True, "json_excerpt": excerpt}


def _schema_property_names(value: Any) -> set[str]:
    names: set[str] = set()
    if isinstance(value, dict):
        names.update(value.get("properties", {}))
        for child in value.values():
            names.update(_schema_property_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(_schema_property_names(child))
    return names


def _diagnostic_path(path: str, allowed: set[str]) -> str:
    return "/".join(part if (part in allowed and re.fullmatch(r"[A-Za-z0-9_~.-]+", part)) or part.isascii() and part.isdigit() or not part else "_redacted"
                    for part in path.split("/"))[:96]


def _safe_issue_code(code: str) -> str:
    return code[:96] if re.fullmatch(r"[A-Z][A-Z0-9_]{0,95}", code) else "SCENE_VALIDATION_FAILED"


def _fatal_provider_code(error: Exception, details: dict) -> str | None:
    status = details.get("http_status")
    if isinstance(status, int) and not isinstance(status, bool) and 400 <= status <= 599:
        return f"PROVIDER_HTTP_{status}"
    exception_codes = {"AuthenticationError": "PROVIDER_AUTHENTICATION_FAILED",
                       "PermissionDeniedError": "PROVIDER_PERMISSION_DENIED",
                       "APITimeoutError": "PROVIDER_TIMEOUT",
                       "RateLimitError": "PROVIDER_RATE_LIMITED"}
    if details.get("failure_class") == "provider_connection_error" and details.get("exception_type") in exception_codes:
        return exception_codes[details["exception_type"]]
    known = {"provider_connection_error": "PROVIDER_CONNECTION_ERROR",
             "input_token_budget_exceeded": "PROVIDER_INPUT_TOKEN_BUDGET_EXCEEDED",
             "client_request_blocked": "PROVIDER_REQUEST_BLOCKED",
             "missing_config": "PROVIDER_CONFIGURATION_MISSING"}
    code = known.get(details.get("failure_class"))
    if code:
        return code
    # Adapters without structured transport details retain their exception
    # chain; only known transport failures are terminal here.
    cause = error.__cause__
    if isinstance(cause, (OSError, TimeoutError, ConnectionError)):
        return "PROVIDER_CONNECTION_ERROR"
    return None


def load_scene_response_schema() -> dict:
    return json.loads((PROJECT_ROOT / "schemas/agent/ifc-scene-grounding-response-0.4.schema.json").read_text(encoding="utf-8"))


def generate_scene_repair_intent(*, provider: Any, request_id: str, repair_request: str,
                                 registry: Any, output_dir: Path | str, scene: PublicScene,
                                 intent_schema_version: str = REPAIR_INTENT_SCHEMA_VERSION_0_10,
                                 max_rounds: int = MAX_ROUNDS) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    diagnostic_rounds: list[dict] = []

    def complete(result: dict) -> dict:
        diagnostics = checked_scene_diagnostics({"schema_version": SCENE_DIAGNOSTICS_VERSION,
                       "rounds": diagnostic_rounds,
                       "terminal_reason": result.get("error_code") or result.get("classification", "unknown")})
        result["scene_diagnostics"] = diagnostics
        atomic_write_text(output / "scene-diagnostics.json", _pretty_json(diagnostics))
        return result

    if intent_schema_version != REPAIR_INTENT_SCHEMA_VERSION_0_10:
        return complete(_failure("SCENE_INTENT_VERSION_UNSUPPORTED", []))
    if len(repair_request.encode("utf-8")) > MAX_REQUEST_BYTES:
        return complete(_failure("REPAIR_REQUEST_TOO_LARGE", []))
    if not 1 <= max_rounds <= MAX_ROUNDS:
        return complete(_failure("SCENE_ROUND_BUDGET_INVALID", []))
    schema = load_scene_response_schema()
    diagnostic_path_keys = _schema_property_names(schema)
    catalog = _compact_supported_profiles(registry, intent_schema_version=intent_schema_version)
    for item in catalog:
        capability = public_geometry_capability(item['operation_type'])
        if capability is not None:
            item['public_geometry_capability'] = capability
    overview = scene.overview()
    atomic_write_text(output / "scene-overview.json", _pretty_json(overview))
    attempts, feedback = [], []
    previous_proposal = None
    seen_queries: set[str] = set()
    rendered = None
    for round_number in range(1, max_rounds+1):
        inputs = {"REPAIR_REQUEST": repair_request, "SUPPORTED_OPERATIONS": catalog,
                  "CURRENT_PUBLIC_SCENE": overview, "SCENE_QUERIES": scene.prompt_context(),
                  "VALIDATION_FEEDBACK": feedback, "PREVIOUS_PROPOSAL": previous_proposal,
                  "RESPONSE_SCHEMA": schema}
        context_bytes = len(_pretty_json(inputs).encode("utf-8"))
        if context_bytes > MAX_CONTEXT_BYTES:
            return complete(_failure("SCENE_CONTEXT_BUDGET_EXCEEDED", attempts))
        rendered = render_prompt(template_id=TEMPLATE_ID, inputs=inputs)
        round_dir = output / f"round-{round_number:03d}"
        round_dir.mkdir()
        atomic_write_text(round_dir / "renderer-input.json", _pretty_json(inputs))
        atomic_write_text(round_dir / "rendered-prompt.md", rendered["text"])
        issues, metadata, raw_text, live_evidence = [], {}, "", None
        final_intent, question, derivations = None, None, []
        parsed, page, terminal_code = None, None, None
        action, stage = "unknown", "provider"
        try:
            response, live_evidence = _call_provider(provider, {
                "session_id": f"ifc-repair-scene-{request_id}", "prompt": rendered["text"], "schema": schema,
                "state": {"request_id": request_id, "stage": "ifc_repair_scene_grounding", "attempt": round_number}})
            raw_text, metadata = response.text, response.metadata
            stage = "parse"
            if len(raw_text.encode("utf-8")) > MAX_PROVIDER_RESPONSE_BYTES:
                raise GroundingError("SCENE_RESPONSE_TOO_LARGE")
            status, parsed, parse_issues = response.parse_json()
            if status != "ok" or parse_issues or parsed is None:
                raise GroundingError("SCENE_RESPONSE_INVALID_JSON")
            action = parsed.get("kind", "unknown") if isinstance(parsed, dict) else "unknown"
            if not isinstance(action, str) or action not in {"query", "intent", "clarification"}:
                action = "unknown"
            stage = "schema"
            schema_issues = _schema_issues(parsed, schema)
            if schema_issues:
                raise _SchemaFeedbackError(schema_issues)
            if parsed["kind"] == "query":
                stage = "query"
                page = scene.query(parsed["query"])
                atomic_write_text(output / "scene-queries.json", _pretty_json(scene.pages))
                signature = json.dumps(page["query"], sort_keys=True, ensure_ascii=False)
                if signature in seen_queries:
                    raise GroundingError("SCENE_QUERY_NO_NEW_EVIDENCE: reuse the returned facts or query a different unresolved condition")
                seen_queries.add(signature)
                feedback = []
                previous_proposal = None
            else:
                body = parsed["intent"]
                if parsed["kind"] == "intent":
                    stage = "geometry"
                    body, derivations = bind_spatial_intent(body, parsed["bindings"], scene,
                                                          repair_request=repair_request)
                stage = "intent"
                final_intent, _ = parse_repair_intent_body(body, registry=registry, request_id=request_id,
                    repair_request=repair_request, model=str(metadata.get("model", "")),
                    prompt_hash=rendered["metadata"]["template_hash"], intent_schema_version=intent_schema_version)
                if parsed["kind"] == "clarification":
                    stage = "clarification"
                    _validate_clarification(parsed, final_intent, scene, registry, repair_request=repair_request)
                    question = parsed["question"]
                missing_positions = [p for op in final_intent.operations
                                     for p in registry.missing_required_parameters(op.to_dict())
                                     if p.startswith("/position/")]
                if missing_positions and not question and not final_intent.unsupported_requests:
                    stage = "geometry"
                    raise GroundingError("SCENE_POSITION_NOT_GROUNDED: Query and ground the requested world/relative position; do not ask for a native local offset.")
        except (ProviderOutputError, OpenAICompatError) as error:
            # Failed HTTP/SDK attempts retain the same available evidence as the
            # original intent stage. The outer wire observer accounts all calls.
            if getattr(error, "live_result", None) is not None:
                live_evidence = {"request": error.live_result.request, "response": error.live_result.response,
                                 "events": list(error.live_result.events)}
            details = getattr(error, "details", getattr(error, "evidence", {}))
            if live_evidence is None and ("request" in details or "response" in details):
                live_evidence = {"request": details.get("request", {}), "response": details.get("response", {}), "events": []}
            metadata = {key: details[key] for key in ("provider", "model", "usage", "failure_class", "exception_type", "http_status", "transport_attempts") if key in details}
            raw_text = str(details.get("content_text", raw_text))
            terminal_code = _fatal_provider_code(error, details)
            code = terminal_code or ("PROVIDER_RESPONSE_TRUNCATED" if details.get("failure_class") == "truncated" else "PROVIDER_OUTPUT_INVALID")
            issues = [{"code": code, "path": "", "message": code}]
        except (GroundingError, SceneError, RepairIntentError, OperationRegistryError, PromptProfileError) as error:
            issues = getattr(error, "issues", None) or [{"code": str(getattr(error, "code", str(error).split(":",1)[0])),
                       "path": str(getattr(error, "path", "/bindings" if stage == "geometry" else "")), "message": str(error)[:500]}]
            code = issues[0]["code"]
            if stage == "intent":
                for issue in issues:
                    if issue["path"] and not issue["path"].startswith("/intent/"):
                        issue["path"] = "/intent" + issue["path"]
            if stage == "geometry" and (code == "SCENE_WALL_AXIS_UNSUPPORTED"
                    or code.startswith("PUBLIC_GEOMETRY_") and code.endswith("_UNSUPPORTED")):
                terminal_code = code
            final_intent = None
        attempt = _attempt_record(attempt_number=round_number, issues=issues, provider_metadata=metadata,
                                  raw_text=raw_text, valid=not issues, normalizations=[])
        attempts.append(attempt)
        atomic_write_text(round_dir / f"attempt-{round_number:03d}.json", _pretty_json(attempt))
        atomic_write_text(round_dir / "raw-response.txt", raw_text)
        _write_live_evidence(round_dir, round_number, live_evidence)
        diagnostic = {"round": round_number, "action": action, "stage": stage,
                      "outcome": "terminal" if terminal_code else "invalid" if issues else "valid",
                      "issue_codes": list(dict.fromkeys(_safe_issue_code(i["code"]) for i in issues))[:MAX_FEEDBACK_ISSUES],
                      "issue_paths": list(dict.fromkeys(_diagnostic_path(i["path"], diagnostic_path_keys) for i in issues))[:MAX_FEEDBACK_ISSUES],
                      "context_bytes": context_bytes}
        if page is not None:
            diagnostic.update(query_id=page["query_id"], returned_count=len(page["records"]), total_matches=page["total_matches"])
        diagnostic_rounds.append(diagnostic)
        if terminal_code:
            return complete(_failure(terminal_code, attempts))
        if issues:
            feedback = issues
            previous_proposal = _bounded_proposal(parsed, raw_text)
            continue
        if final_intent is not None:
            result = finish_repair_intent(final_intent, registry=registry, output=output, attempts=attempts,
                                         prompt=_prompt_identity(rendered))
            if question and result["classification"] != "unsupported":
                result.update(classification="clarification_required", scene_question=question)
            atomic_write_text(output / "scene-queries.json", _pretty_json(scene.pages))
            atomic_write_text(output / "grounding-evidence.json", _pretty_json({
                "schema_version": SCENE_GROUNDING_VERSION, "derivations": derivations,
                "offered_ids": sorted(scene.offered_ids), "scene_question": question}))
            result["scene_grounding_version"] = SCENE_GROUNDING_VERSION
            result["public_geometry_requirements"] = {
                item["operation_id"]: item["public_geometry_requirement"] for item in derivations
                if "public_geometry_requirement" in item
            }
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
            return complete(result)
    return complete(_failure("SCENE_GROUNDING_EXHAUSTED", attempts))


def _validate_clarification(parsed: dict, intent: Any, scene: PublicScene, registry: Any,
                            *, repair_request: str = "") -> None:
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
    elif parsed["reason"] == "ambiguous_frame":
        issue = parsed.get("frame_issue", {})
        alternatives = issue.get("alternatives", [])
        if (not issue.get("phrase") or issue["phrase"] not in repair_request
                or len({value.strip().casefold() for value in alternatives}) < 2):
            raise GroundingError("SCENE_FRAME_AMBIGUITY_UNGROUNDED")
    else:
        missing_by_operation = {op.operation_id: set(registry.missing_required_parameters(op.to_dict()))
                                for op in intent.operations}
        missing = [p for paths in missing_by_operation.values() for p in paths]
        facts = parsed.get("missing_facts", [])
        for fact in facts:
            if (fact.get("source") != "user_design"
                    or fact.get("path") not in missing_by_operation.get(fact.get("operation_id"), set())
                    or fact.get("path") == "/position/reference"):
                raise GroundingError("SCENE_CLARIFICATION_NOT_A_USER_FACT")
        # An absent design location differs from a world-to-wall conversion.
        # The model must identify the actual missing user parameter; internal
        # identities/offsets remain forbidden below. This is not proof that a
        # model understood every clause of the request (evaluated separately).
        if not missing or (all(p.startswith("/position/") for p in missing) and not facts):
            raise GroundingError("SCENE_CLARIFICATION_NOT_A_USER_FACT")
    question = parsed["question"].lower()
    if any(term in question for term in ("guid", "globalid", "name", "局部起点", "局部偏移")):
        raise GroundingError("SCENE_CLARIFICATION_REQUESTS_INTERNAL_FACT")


def _failure(code: str, attempts: list[dict]) -> dict:
    recent = [issue for attempt in attempts[-3:] for issue in attempt.get("issues", [])]
    return {"valid": False, "intent": None, "attempts": attempts, "error_code": code,
            "failure_summary": {"stage": "scene_grounding", "rounds": len(attempts),
                                "last_issue_codes": list(dict.fromkeys(i["code"] for i in recent))[-5:]}}
