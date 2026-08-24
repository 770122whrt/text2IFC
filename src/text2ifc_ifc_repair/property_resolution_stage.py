"""Bounded, non-executable Provider stage for one property claim."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from jsonschema import Draft202012Validator

from text2ifc_agent.openai_compat import (
    OpenAICompatError,
    OpenAICompatibleLiveProvider,
    estimate_openai_compatible_input_tokens,
)
from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import (
    LiveProviderResult,
    MimoAgentProvider,
    ProviderOutput,
    ProviderOutputError,
    redact_provider_payload,
    resolve_provider_evidence_source,
    validate_provider_output,
)
from text2ifc_text.splits import atomic_write_text


TEMPLATE_ID = "ifc-property-resolution.v0.1"
MAX_PROPERTY_RESOLUTION_ATTEMPTS = 2
MAX_PROPERTY_RESOLUTION_RESPONSE_BYTES = 32_768
MAX_PROPERTY_RESOLUTION_RESPONSE_TOKENS = 4_096
_PRIVATE_CANARIES = (
    "private_original",
    "benchmark_gold",
    "mutation_mapping",
    "iso-10303-21;",
    "ifccartesianpoint",
    "ifcownerhistory",
)


def generate_property_resolution_decision(
    *,
    query: Mapping[str, Any],
    candidate_set: Mapping[str, Any],
    output_dir: Path | str,
    provider: Any | None = None,
    provider_factory: Callable[[], Any] | None = None,
    max_attempts: int = MAX_PROPERTY_RESOLUTION_ATTEMPTS,
) -> dict[str, Any]:
    """Ask one Provider to compare one claim with its persisted offered set."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if max_attempts not in (1, 2):
        return _invalid_result(
            error_code="PROPERTY_RESOLUTION_ATTEMPT_LIMIT_INVALID",
            attempts=(),
        )

    decision_schema = _load_schema(
        "schemas/agent/ifc-property-rerank-decision-0.1.schema.json"
    )
    input_issues = _input_issues(query=query, candidate_set=candidate_set)
    if input_issues:
        return _invalid_result(
            error_code="PROPERTY_RESOLUTION_INPUT_INVALID",
            attempts=(),
            issues=input_issues,
        )
    if (provider is None) == (provider_factory is None):
        return _invalid_result(
            error_code="PROPERTY_RESOLUTION_PROVIDER_INVALID",
            attempts=(),
        )
    if provider is None:
        assert provider_factory is not None
        provider = provider_factory()

    query_document = _plain_document(query)
    candidate_document = _plain_document(candidate_set)
    offered_ids = frozenset(
        str(item["candidate_id"])
        for item in candidate_document["candidates"]
    )
    previous_feedback: list[dict[str, str]] = []
    attempts: list[dict[str, Any]] = []
    for attempt_number in range(1, max_attempts + 1):
        attempt_dir = output / f"attempt-{attempt_number:03d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        renderer_input = {
            "PROPERTY_QUERY": query_document,
            "CANDIDATE_SET": candidate_document,
            "DECISION_SCHEMA": decision_schema,
            "PREVIOUS_VALIDATION_FEEDBACK": previous_feedback,
        }
        rendered = render_prompt(template_id=TEMPLATE_ID, inputs=renderer_input)
        atomic_write_text(
            attempt_dir / "renderer-input.json",
            _json(renderer_input),
        )
        atomic_write_text(
            attempt_dir / "rendered-prompt.txt",
            str(rendered["text"]),
        )
        arguments = {
            "session_id": (
                "ifc-property-resolution-"
                f"{query_document['run_id']}-"
                f"{query_document['operation_id']}-"
                f"{query_document['claim_id']}"
            ),
            "prompt": str(rendered["text"]),
            "schema": decision_schema,
            "state": {
                "run_id": query_document["run_id"],
                "request_id": query_document["request_id"],
                "model_id": query_document["model_id"],
                "operation_id": query_document["operation_id"],
                "claim_id": query_document["claim_id"],
                "stage": "ifc_property_resolution",
                "provider_call_ordinal": "property_resolution",
                "attempt": attempt_number,
                "template_id": str(rendered["metadata"]["template_id"]),
                "template_hash": str(rendered["metadata"]["template_hash"]),
            },
        }
        provider_output: ProviderOutput | None = None
        transport_evidence: Mapping[str, Any] | None = None
        issues: list[dict[str, str]] = []
        try:
            provider_output, transport_evidence = _call_provider(provider, arguments)
        except ProviderOutputError as error:
            live_result = error.live_result
            if (
                isinstance(live_result, LiveProviderResult)
                and isinstance(live_result.output, ProviderOutput)
            ):
                provider_output = live_result.output
                transport_evidence = _live_transport_evidence(live_result)
                issues.append(
                    _issue(
                        "PROPERTY_PROVIDER_RESPONSE_INCOMPLETE",
                        "",
                        "Provider returned an incomplete live response.",
                    )
                )
            else:
                issues.append(
                    _issue(
                        "PROPERTY_PROVIDER_REQUEST_FAILED",
                        "",
                        type(error).__name__,
                    )
                )
        except OpenAICompatError as error:
            evidence = dict(error.evidence)
            if evidence.get("failure_class") == "truncated":
                provider_output = ProviderOutput(
                    text=str(evidence.get("content_text", "")),
                    metadata={
                        key: evidence[key]
                        for key in (
                            "provider",
                            "evidence_class",
                            "session_id",
                            "response_id",
                            "model",
                            "finish_reason",
                            "usage",
                        )
                        if key in evidence
                    },
                )
                transport_evidence = evidence
                issues.append(
                    _issue(
                        "PROPERTY_PROVIDER_RESPONSE_INCOMPLETE",
                        "",
                        "Provider returned a truncated live response.",
                    )
                )
            else:
                issues.append(
                    _issue(
                        "PROPERTY_PROVIDER_REQUEST_FAILED",
                        "",
                        str(evidence.get("failure_class", type(error).__name__)),
                    )
                )

        raw_text = "" if provider_output is None else provider_output.text
        raw_document = {
            "text": raw_text,
            "transport": (
                None
                if transport_evidence is None
                else redact_provider_payload(transport_evidence)
            ),
        }
        atomic_write_text(
            attempt_dir / "raw-response.json",
            _json(raw_document),
        )

        parsed: dict[str, Any] | None = None
        parse_status = "provider_error" if provider_output is None else "not_parsed"
        if provider_output is not None:
            response_bytes = len(raw_text.encode("utf-8"))
            response_tokens = estimate_openai_compatible_input_tokens(raw_text)
            if (
                response_bytes > MAX_PROPERTY_RESOLUTION_RESPONSE_BYTES
                or response_tokens > MAX_PROPERTY_RESOLUTION_RESPONSE_TOKENS
            ):
                issues.append(
                    _issue(
                        "PROPERTY_PROVIDER_RESPONSE_TOO_LARGE",
                        "",
                        "Provider response exceeds the Property Resolution limit.",
                    )
                )
            else:
                try:
                    validate_provider_output(provider_output)
                except ProviderOutputError:
                    issues.append(
                        _issue(
                            "PROPERTY_PRIVATE_OUTPUT_FORBIDDEN",
                            "",
                            "Provider output violates the public structured-output boundary.",
                        )
                    )
                if not issues:
                    parse_status, parsed, parse_issues = provider_output.parse_json()
                    issues.extend(
                        _issue(
                            str(item.get("code", "PROPERTY_PROVIDER_JSON_INVALID")),
                            str(item.get("path", "")),
                            str(item.get("message", "Provider JSON is invalid.")),
                        )
                        for item in parse_issues
                    )
                    if parse_status == "ok" and parsed is not None and not issues:
                        issues.extend(
                            _decision_issues(
                                parsed,
                                schema=decision_schema,
                                offered_ids=offered_ids,
                            )
                        )
        atomic_write_text(
            attempt_dir / "parsed-response.json",
            _json(parsed),
        )
        issues = _sort_issues(issues)
        atomic_write_text(
            attempt_dir / "validation-feedback.json",
            _json(issues),
        )

        evidence_class, acceptance_eligible = _execution_evidence(
            provider=provider,
            transport_evidence=transport_evidence,
        )
        metadata = {
            **(
                {}
                if provider_output is None
                else dict(redact_provider_payload(provider_output.metadata))
            ),
            "evidence_class": evidence_class,
            "acceptance_eligible": acceptance_eligible and not issues,
            "provider_call_ordinal": "property_resolution",
        }
        atomic_write_text(
            attempt_dir / "provider-metadata.json",
            _json(metadata),
        )
        trace = _attempt_trace(
            query=query_document,
            candidate_set=candidate_document,
            rendered=rendered,
            attempt_number=attempt_number,
            parse_status=parse_status,
            valid=parsed is not None and not issues,
            evidence_class=evidence_class,
            acceptance_eligible=acceptance_eligible and parsed is not None and not issues,
        )
        atomic_write_text(attempt_dir / "trace.json", _json(trace))
        attempt = {
            "attempt_id": trace["attempt_id"],
            "attempt": attempt_number,
            "status": "valid" if parsed is not None and not issues else "invalid",
            "parse_status": parse_status,
            "issues": issues,
            "evidence_class": evidence_class,
            "acceptance_eligible": (
                acceptance_eligible and parsed is not None and not issues
            ),
            "artifact_dir": attempt_dir.name,
        }
        attempts.append(attempt)
        if parsed is not None and not issues:
            return {
                "valid": True,
                "classification": str(parsed["decision"]),
                "decision": parsed,
                "prompt": _prompt_identity(rendered),
                "trace": trace,
                "attempts": attempts,
                "evidence_class": evidence_class,
                "acceptance_eligible": acceptance_eligible,
                "error_code": None,
            }
        previous_feedback = issues

    return _invalid_result(
        error_code="PROPERTY_RESOLUTION_RETRY_EXHAUSTED",
        attempts=tuple(attempts),
        prompt=_prompt_identity(rendered),
        issues=previous_feedback,
    )


def _input_issues(
    *,
    query: Mapping[str, Any],
    candidate_set: Mapping[str, Any],
) -> list[dict[str, str]]:
    issues = [
        *_schema_issues(
            query,
            schema=_load_schema(
                "schemas/agent/ifc-property-resolution-query-0.2.schema.json"
            ),
            code="PROPERTY_QUERY_SCHEMA_INVALID",
        ),
        *_schema_issues(
            candidate_set,
            schema=_load_schema(
                "schemas/agent/ifc-property-candidate-set-0.1.schema.json"
            ),
            code="PROPERTY_CANDIDATE_SET_SCHEMA_INVALID",
        ),
    ]
    if issues:
        return _sort_issues(issues)
    if candidate_set.get("query_id") != query.get("query_id"):
        issues.append(
            _issue(
                "PROPERTY_CANDIDATE_QUERY_MISMATCH",
                "/query_id",
                "Candidate set does not belong to this query.",
            )
        )
    if candidate_set.get("corpus_version") != query.get("corpus_version"):
        issues.append(
            _issue(
                "PROPERTY_CANDIDATE_CORPUS_MISMATCH",
                "/corpus_version",
                "Candidate set and query corpus versions differ.",
            )
        )
    candidate_ids = [
        str(item["candidate_id"])
        for item in candidate_set.get("candidates", ())
    ]
    if not candidate_ids or len(candidate_ids) != len(set(candidate_ids)):
        issues.append(
            _issue(
                "PROPERTY_CANDIDATE_MEMBERSHIP_INVALID",
                "/candidates",
                "Offered candidate IDs must be non-empty and unique.",
            )
        )
    return _sort_issues(issues)


def _decision_issues(
    decision: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    offered_ids: frozenset[str],
) -> list[dict[str, str]]:
    issues = _schema_issues(
        decision,
        schema=schema,
        code="PROPERTY_DECISION_SCHEMA_INVALID",
    )
    if issues:
        return issues
    if _contains_private_output(decision):
        return [
            _issue(
                "PROPERTY_PRIVATE_OUTPUT_FORBIDDEN",
                "",
                "Provider decision contains private or low-level content.",
            )
        ]
    selected = decision.get("selected_candidate_id")
    conflicts = tuple(str(item) for item in decision["conflicting_candidate_ids"])
    if selected is not None and str(selected) not in offered_ids:
        issues.append(
            _issue(
                "PROPERTY_CANDIDATE_NOT_OFFERED",
                "/selected_candidate_id",
                "Selected candidate is not in the persisted offered set.",
            )
        )
    if any(item not in offered_ids for item in conflicts):
        issues.append(
            _issue(
                "PROPERTY_CONFLICT_CANDIDATE_NOT_OFFERED",
                "/conflicting_candidate_ids",
                "Conflicting candidates must belong to the persisted offered set.",
            )
        )
    if decision["decision"] == "confirmed" and conflicts:
        issues.append(
            _issue(
                "PROPERTY_DECISION_CARDINALITY_INVALID",
                "/conflicting_candidate_ids",
                "A confirmed decision cannot retain conflicting candidates.",
            )
        )
    return _sort_issues(issues)


def _schema_issues(
    document: Mapping[str, Any],
    *,
    schema: Mapping[str, Any],
    code: str,
) -> list[dict[str, str]]:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    return [
        _issue(code, _pointer(error.absolute_path), error.message)
        for error in errors
    ]


def _call_provider(
    provider: Any,
    arguments: Mapping[str, Any],
) -> tuple[ProviderOutput, Mapping[str, Any] | None]:
    generate_live = getattr(provider, "generate_live", None)
    if callable(generate_live):
        live_result = generate_live(**arguments)
        if not isinstance(live_result, LiveProviderResult):
            raise ProviderOutputError("PROPERTY_LIVE_PROVIDER_RESULT_INVALID")
        if not isinstance(live_result.output, ProviderOutput):
            raise ProviderOutputError("PROPERTY_PROVIDER_OUTPUT_INVALID")
        return live_result.output, _live_transport_evidence(live_result)
    generate_candidate = getattr(provider, "generate_candidate", None)
    if not callable(generate_candidate):
        raise ProviderOutputError("PROPERTY_PROVIDER_INTERFACE_UNSUPPORTED")
    provider_output = generate_candidate(**arguments)
    if not isinstance(provider_output, ProviderOutput):
        raise ProviderOutputError("PROPERTY_PROVIDER_OUTPUT_INVALID")
    return provider_output, None


def _live_transport_evidence(
    live_result: LiveProviderResult,
) -> dict[str, Any]:
    return {
        "evidence_class": live_result.evidence_class,
        "http_status": live_result.http_status,
        "request": live_result.request,
        "response": live_result.response,
        "events": list(live_result.events),
    }


def _execution_evidence(
    *,
    provider: Any,
    transport_evidence: Mapping[str, Any] | None,
) -> tuple[str, bool]:
    live_transport = (
        transport_evidence is not None
        and transport_evidence.get("evidence_class") == "live"
    )
    evidence_source = resolve_provider_evidence_source(provider)
    if isinstance(evidence_source, OpenAICompatibleLiveProvider):
        eligible = live_transport and bool(evidence_source.uses_default_sdk_client)
        return ("live" if eligible else "injected_offline", eligible)
    if isinstance(evidence_source, MimoAgentProvider):
        eligible = bool(live_transport)
        return ("live" if eligible else "injected_offline", eligible)
    return "injected_offline", False


def _attempt_trace(
    *,
    query: Mapping[str, Any],
    candidate_set: Mapping[str, Any],
    rendered: Mapping[str, Any],
    attempt_number: int,
    parse_status: str,
    valid: bool,
    evidence_class: str,
    acceptance_eligible: bool,
) -> dict[str, Any]:
    metadata = rendered["metadata"]
    return {
        "schema_version": "text2ifc/ifc-property-resolution-trace/0.1",
        "attempt_id": (
            "property-resolution-attempt:"
            f"{query['run_id']}:{query['operation_id']}:{query['claim_id']}:"
            f"{attempt_number}"
        ),
        "run_id": query["run_id"],
        "request_id": query["request_id"],
        "model_id": query["model_id"],
        "operation_id": query["operation_id"],
        "claim_id": query["claim_id"],
        "query_id": query["query_id"],
        "candidate_set_id": candidate_set["candidate_set_id"],
        "provider_call_ordinal": "property_resolution",
        "attempt": attempt_number,
        "template_id": metadata["template_id"],
        "template_hash": metadata["template_hash"],
        "parse_status": parse_status,
        "status": "valid" if valid else "invalid",
        "evidence_class": evidence_class,
        "acceptance_eligible": acceptance_eligible,
        "artifact_paths": {
            "renderer_input": "renderer-input.json",
            "rendered_prompt": "rendered-prompt.txt",
            "raw_response": "raw-response.json",
            "parsed_response": "parsed-response.json",
            "validation_feedback": "validation-feedback.json",
            "provider_metadata": "provider-metadata.json",
            "trace": "trace.json",
        },
    }


def _contains_private_output(value: Any) -> bool:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
    return any(canary in rendered for canary in _PRIVATE_CANARIES)


def _load_schema(relative_path: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    return json.loads((root / relative_path).read_text(encoding="utf-8"))


def _plain_document(value: Mapping[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(dict(value), ensure_ascii=False, allow_nan=False))


def _pointer(parts: Any) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens) if tokens else ""


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message[:1000]}


def _sort_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        issues,
        key=lambda item: (item["code"], item["path"], item["message"]),
    )


def _prompt_identity(rendered: Mapping[str, Any]) -> dict[str, str]:
    metadata = rendered["metadata"]
    return {
        "template_id": str(metadata["template_id"]),
        "template_hash": str(metadata["template_hash"]),
    }


def _invalid_result(
    *,
    error_code: str,
    attempts: tuple[dict[str, Any], ...],
    prompt: Mapping[str, str] | None = None,
    issues: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    evidence_class = (
        str(attempts[-1]["evidence_class"])
        if attempts
        else "not_executed"
    )
    return {
        "valid": False,
        "classification": "invalid",
        "decision": None,
        "prompt": dict(prompt or {}),
        "trace": None,
        "attempts": list(attempts),
        "issues": _sort_issues(list(issues or ())),
        "evidence_class": evidence_class,
        "acceptance_eligible": False,
        "error_code": error_code,
    }


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"


__all__ = [
    "MAX_PROPERTY_RESOLUTION_ATTEMPTS",
    "MAX_PROPERTY_RESOLUTION_RESPONSE_BYTES",
    "MAX_PROPERTY_RESOLUTION_RESPONSE_TOKENS",
    "TEMPLATE_ID",
    "generate_property_resolution_decision",
]
