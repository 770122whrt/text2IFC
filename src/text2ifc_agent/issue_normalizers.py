"""Translate workflow failures into Phase 6.4 Issue objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .issues import Issue, write_issues


def normalize_validation_issues(
    diagnostics: Sequence[Mapping[str, Any]],
    *,
    source: str,
) -> list[Issue]:
    """Normalize schema or semantic validation diagnostics."""

    issues: list[Issue] = []
    for index, diagnostic in enumerate(diagnostics, start=1):
        code = _upper_code(diagnostic)
        path = _string_or_none(diagnostic.get("path"))
        message = _diagnostic_message(diagnostic)
        if "UNSUPPORTED" in code:
            owner = "schema"
            issue_type = "unsupported_schema_capability"
            route = "blocked_as_unsupported"
            retryable = False
        elif "DRAFT" in code or "UNRESOLVED" in code:
            if source == "schema_validation" and (
                "PLACEMENT_PARENT" in code or "RELATIONSHIP_ENDPOINT" in code
            ):
                owner = "generator"
                issue_type = "missing_relationship"
                route = "regenerate_json"
                retryable = True
            else:
                owner = "user"
                issue_type = "draft_unresolved_path"
                route = "ask_user"
                retryable = True
        elif "MISSING" in code and source == "semantic_validation":
            owner = "user"
            issue_type = "missing_required_fact"
            route = "ask_user"
            retryable = True
        else:
            owner = "repair"
            issue_type = "schema_mismatch"
            route = "repair_json"
            retryable = True
        issues.append(
            Issue(
                issue_id=f"issue_{source}_{index:04d}",
                source=source,
                severity="blocking",
                owner=owner,
                issue_type=issue_type,
                expected_fact_ref=_string_or_none(diagnostic.get("expected_fact_ref")),
                actual_ref=path,
                evidence=_evidence(code, message),
                suggested_route=route,
                retryable=retryable,
            )
        )
    return issues


def normalize_generator_draft_issues(draft: Mapping[str, Any]) -> list[Issue]:
    """Normalize Generator Draft records without treating model omissions as user gaps."""

    issues: list[Issue] = []
    for index, item in enumerate(_list_of_dicts(draft.get("missing_facts")), start=1):
        code = _upper_code(item)
        message = _diagnostic_message(item)
        path = _string_or_none(item.get("path"))
        if "UNSUPPORTED" in code:
            owner = "schema"
            issue_type = "unsupported_schema_capability"
            route = "blocked_as_unsupported"
            retryable = False
        elif "USER" in code or "DRAFT" in code or "UNRESOLVED" in code:
            owner = "user"
            issue_type = "missing_required_fact"
            route = "ask_user"
            retryable = True
        else:
            owner = "generator"
            issue_type = "missing_entity"
            route = "regenerate_json"
            retryable = True
        issues.append(
            Issue(
                issue_id=f"issue_generator_draft_{index:04d}",
                source="semantic_validation",
                severity="blocking",
                owner=owner,
                issue_type=issue_type,
                expected_fact_ref=_string_or_none(item.get("expected_fact_ref")),
                actual_ref=path,
                evidence=_evidence(code, message),
                suggested_route=route,
                retryable=retryable,
            )
        )
    return issues


def normalize_compiler_result(result: Mapping[str, Any]) -> list[Issue]:
    """Normalize compiler failure payloads without re-running compilation."""

    if result.get("success") is True:
        return []
    error_type = str(result.get("error_type") or result.get("exception_type") or "")
    message = _diagnostic_message(result)
    unsupported = "unsupported" in error_type.lower() or "not supported" in message.lower()
    return [
        Issue(
            issue_id="issue_compiler_0001",
            source="compiler",
            severity="blocking",
            owner="compiler",
            issue_type="compiler_unsupported_feature" if unsupported else "compile_error",
            actual_ref=_string_or_none(result.get("path")),
            evidence=_evidence(error_type or "COMPILER_ERROR", message),
            suggested_route=(
                "blocked_as_unsupported" if unsupported else "runtime_blocked"
            ),
            retryable=False,
        )
    ]


def normalize_reopen_result(result: Mapping[str, Any]) -> list[Issue]:
    """Normalize IFC reopen/check-generated-IFC failures."""

    if result.get("success") is True:
        return []
    source_items = _list_of_dicts(result.get("ifc_issues")) or _list_of_dicts(
        result.get("input_issues")
    )
    if not source_items:
        source_items = [result]
    issues: list[Issue] = []
    for index, item in enumerate(source_items, start=1):
        issues.append(
            Issue(
                issue_id=f"issue_reopen_check_{index:04d}",
                source="reopen_check",
                severity="blocking",
                owner="compiler",
                issue_type="reopen_error",
                actual_ref=_string_or_none(item.get("path")),
                evidence=_evidence(_upper_code(item), _diagnostic_message(item)),
                suggested_route="runtime_blocked",
                retryable=False,
            )
        )
    return issues


def normalize_gate_sidecars(case_dir: Path | str) -> list[Issue]:
    """Normalize geometry-feedback and gate-summary sidecars from a run dir."""

    root = Path(case_dir)
    issues: list[Issue] = []
    candidate_ids = _candidate_entity_ids(_read_json(root / "candidate.json"))
    geometry = _read_json(root / "geometry-feedback.json")
    if geometry and geometry.get("success") is False:
        for index, item in enumerate(_list_of_dicts(geometry.get("issues")), start=1):
            code = _upper_code(item)
            issues.extend(
                _targeted_issues(
                    issue_id=f"issue_geometry_gate_{index:04d}",
                    source="geometry_gate",
                    severity="blocking",
                    owner="gate",
                    issue_type="geometry_invalid",
                    route="regenerate_json",
                    retryable=True,
                    detail=item,
                    target_ids=_existing_target_ids(item.get("entity_ids"), candidate_ids),
                )
            )

    gate_summary = _read_json(root / "gate-summary.json")
    if gate_summary and gate_summary.get("overall_status") == "failed":
        gate_index = 0
        for gate in _list_of_dicts(gate_summary.get("gates")):
            if gate.get("status") != "failed":
                continue
            gate_issues = _list_of_dicts(gate.get("issues"))
            details = gate_issues or [
                {"code": code, "message": f"Gate failed: {gate.get('name', '')}"}
                for code in gate.get("issue_codes") or ["GATE_FAILED"]
            ]
            for detail in details:
                gate_index += 1
                code = _upper_code(detail)
                issue_type = _gate_issue_type(str(code))
                issues.extend(
                    _targeted_issues(
                        issue_id=f"issue_deterministic_gate_{gate_index:04d}",
                        source="deterministic_gate",
                        severity="blocking",
                        owner="generator" if issue_type != "gate_false_positive" else "gate",
                        issue_type=issue_type,
                        route=(
                            "gate_issue"
                            if issue_type == "gate_false_positive"
                            else "regenerate_json"
                        ),
                        retryable=issue_type != "gate_false_positive",
                        detail=detail,
                        target_ids=_existing_target_ids(detail.get("entity_ids"), candidate_ids),
                        fallback_ref=(
                            _string_or_none(detail.get("path"))
                            or str(gate.get("name", ""))
                            or None
                        ),
                    )
                )
    return issues


def normalize_audit_findings(
    report: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any] | None = None,
) -> list[Issue]:
    """Normalize Audit Agent findings into issue ownership."""

    findings = _list_of_dicts(report.get("findings"))
    if not findings and report.get("blocking") is True:
        findings = [report]
    issues: list[Issue] = []
    candidate_ids = _candidate_entity_ids(candidate)
    for index, finding in enumerate(findings, start=1):
        code = _upper_code(finding)
        owner, issue_type, route = _audit_mapping(code)
        issues.extend(
            _targeted_issues(
                issue_id=f"issue_audit_{index:04d}",
                source="audit",
                severity=_severity(finding),
                owner=owner,
                issue_type=issue_type,
                route=route,
                retryable=route in {"revise_design_brief", "regenerate_json", "repair_json"},
                detail=finding,
                target_ids=_existing_target_ids(
                    finding.get("affected_entities"), candidate_ids
                ),
            )
        )
    return issues


def normalize_provider_failure(
    failure: Mapping[str, Any],
    *,
    stage: str,
) -> list[Issue]:
    """Normalize provider failure sidecars while avoiding raw request leakage."""

    failure_class = str(failure.get("failure_class") or "provider_error")
    is_truncation = failure_class == "truncated" or _nested_finish_reason(failure) == "length"
    return [
        Issue(
            issue_id=f"issue_provider_{stage}_0001",
            source="provider",
            severity="blocking",
            owner="provider",
            issue_type="provider_truncation" if is_truncation else "provider_format_error",
            actual_ref=f"{stage}/provider-error.json",
            evidence=(
                f"Provider failure at stage={stage}; "
                f"failure_class={failure_class}; provider={failure.get('provider', 'unknown')}"
            ),
            suggested_route="provider_retry",
            retryable=True,
        )
    ]


def normalize_runtime_exception(exc: BaseException, *, stage: str) -> list[Issue]:
    """Normalize an unexpected runtime exception."""

    return [
        Issue(
            issue_id=f"issue_runtime_{stage}_0001",
            source="runtime",
            severity="fatal",
            owner="runtime",
            issue_type="runtime_error",
            actual_ref=stage,
            evidence=f"{type(exc).__name__}: {exc}",
            suggested_route="runtime_blocked",
            retryable=False,
        )
    ]


def write_terminal_issues(
    run_dir: Path | str,
    issues: Sequence[Issue | Mapping[str, Any]],
) -> Path:
    """Persist normalized terminal issues in a run directory."""

    root = Path(run_dir)
    root.mkdir(parents=True, exist_ok=True)
    return write_issues(root / "issues.json", issues)


def _gate_issue_type(code: str) -> str:
    upper = code.upper()
    if "MISMATCH" in upper:
        return "geometry_invalid"
    if "ENTITY" in upper:
        return "missing_entity"
    if "RELATIONSHIP" in upper or "VOID" in upper or "FILL" in upper:
        return "missing_relationship"
    if "HOST" in upper:
        return "missing_host"
    if "STOREY" in upper:
        return "missing_storey_assignment"
    if "SPACE_BOUNDARY" in upper or "BOUNDARY" in upper:
        return "missing_space_boundary"
    if "STAIR" in upper or "VERTICAL" in upper:
        return "missing_vertical_connection"
    if "FALSE_POSITIVE" in upper:
        return "gate_false_positive"
    return "geometry_invalid"


def _audit_mapping(code: str) -> tuple[str, str, str]:
    if "DESIGN" in code or "ORIGINAL_REQUEST" in code:
        return "design_brief", "changed_original_request", "revise_design_brief"
    if "OPENING" in code or "FILLING" in code:
        return "generator", "geometry_invalid", "regenerate_json"
    if "PLACEMENT" in code or "BBOX_MISMATCH" in code:
        return "generator", "geometry_invalid", "regenerate_json"
    if "STAIR" in code or "VERTICAL" in code:
        return "generator", "missing_vertical_connection", "regenerate_json"
    if "ENTITY" in code:
        return "generator", "missing_entity", "regenerate_json"
    if "RELATIONSHIP" in code:
        return "generator", "missing_relationship", "regenerate_json"
    if "HOST" in code:
        return "generator", "missing_host", "regenerate_json"
    if "SCHEMA" in code or "JSON" in code:
        return "repair", "schema_mismatch", "repair_json"
    return "audit", "semantic_mismatch", "revise_design_brief"


def _severity(payload: Mapping[str, Any]) -> str:
    raw = str(payload.get("severity") or "blocking").lower()
    return raw if raw in {"info", "warning", "blocking", "fatal"} else "blocking"


def _upper_code(payload: Mapping[str, Any]) -> str:
    return str(payload.get("code") or payload.get("error_type") or "UNKNOWN").upper()


def _diagnostic_message(payload: Mapping[str, Any]) -> str:
    message = payload.get("message") or payload.get("error") or payload.get("reason")
    return str(message) if message else "No diagnostic message was provided."


def _evidence(code: str, message: str) -> str:
    clean_code = code or "UNKNOWN"
    clean_message = message or "No diagnostic message was provided."
    return f"{clean_code}: {clean_message}"


def _gate_detail_evidence(code: str, detail: Mapping[str, Any]) -> str:
    message = _diagnostic_message(detail)
    evidence_detail = {
        key: value
        for key, value in detail.items()
        if key not in {"code", "message", "error", "reason"}
    }
    if evidence_detail:
        message = (
            f"{message} Evidence: "
            f"{json.dumps(evidence_detail, ensure_ascii=False, sort_keys=True)}"
        )
    return _evidence(code, message)


def _candidate_entity_ids(candidate: Mapping[str, Any] | None) -> set[str] | None:
    if not candidate:
        return None
    return {
        str(entity.get("id"))
        for entity in _list_of_dicts(candidate.get("entities"))
        if entity.get("id")
    }


def _existing_target_ids(value: Any, candidate_ids: set[str] | None) -> list[str]:
    values = list(
        dict.fromkeys(str(item) for item in value)
    ) if isinstance(value, list) else []
    if candidate_ids is None:
        return values
    return [item for item in values if item in candidate_ids]


def _targeted_issues(
    *,
    issue_id: str,
    source: str,
    severity: str,
    owner: str,
    issue_type: str,
    route: str,
    retryable: bool,
    detail: Mapping[str, Any],
    target_ids: Sequence[str],
    fallback_ref: str | None = None,
) -> list[Issue]:
    targets = list(target_ids)
    refs = [f"entity:{target_id}#/attributes" for target_id in targets]
    if not refs:
        refs = [fallback_ref or _string_or_none(detail.get("path"))]
    return [
        Issue(
            issue_id=(issue_id if len(refs) == 1 else f"{issue_id}_{index:02d}"),
            source=source,
            severity=severity,
            owner=owner,
            issue_type=issue_type,
            actual_ref=actual_ref,
            evidence=_gate_detail_evidence(_upper_code(detail), detail),
            suggested_route=route,
            retryable=retryable,
        )
        for index, actual_ref in enumerate(refs, start=1)
    ]


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else None


def _nested_finish_reason(payload: Mapping[str, Any]) -> str | None:
    details = payload.get("details")
    if isinstance(details, Mapping):
        raw = details.get("finish_reason")
        if raw is not None:
            return str(raw)
    return None
