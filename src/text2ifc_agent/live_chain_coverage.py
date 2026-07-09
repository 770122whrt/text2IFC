"""Phase 6.4 supplemental live chain coverage evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "text2ifc/phase6.4-live-chain-coverage/1.0"


def build_live_chain_coverage(
    *,
    output_root: Path | str,
    accepted_session_hash: str,
    nonaccept_session_hash: str,
) -> dict[str, Any]:
    root = Path(output_root)
    accepted_dir = root / "runs" / accepted_session_hash
    nonaccept_dir = root / "runs" / nonaccept_session_hash
    links = [
        _provider_smoke_link(root),
        _accepted_design_link(accepted_dir),
        _accepted_generator_link(accepted_dir),
        _accepted_gate_link(accepted_dir),
        _accepted_audit_link(accepted_dir),
        _accepted_ifc_link(accepted_dir),
        _nonaccept_design_link(nonaccept_dir),
        _nonaccept_route_link(nonaccept_dir),
    ]
    missing = [link["link_id"] for link in links if link["required"] and link["status"] != "passed"]
    provider = _provider_from_smoke(root) or _provider_from_links(links) or "unknown"
    result = {
        "schema_version": SCHEMA_VERSION,
        "provider": provider,
        "accepted_session_hash": accepted_session_hash,
        "nonaccept_session_hash": nonaccept_session_hash,
        "all_required_links_passed": not missing,
        "required_link_count": sum(1 for link in links if link["required"]),
        "passed_required_link_count": sum(
            1 for link in links if link["required"] and link["status"] == "passed"
        ),
        "missing_required_link_ids": missing,
        "links": links,
        "report": "live-chain-coverage-report.md",
    }
    _write_json(root / "live-chain-coverage-result.json", result)
    _write_report(root / "live-chain-coverage-report.md", result)
    return result


def _provider_smoke_link(root: Path) -> dict[str, Any]:
    payload = _read_json(root / "smoke-json.json")
    response_id = _string_or_none(payload.get("response_id"))
    finish_reason = _string_or_none(payload.get("finish_reason"))
    passed = payload.get("status") in {"ok", "success", "passed"} and bool(response_id) and finish_reason == "stop"
    return _link(
        link_id="provider_smoke_json",
        source_stage="provider_config",
        target_stage="json_smoke",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="live_model_verified" if passed else "missing",
        provider_response_ids=[response_id] if response_id else [],
        finish_reasons=[finish_reason] if finish_reason else [],
        evidence_paths=["smoke-json.json"] if (root / "smoke-json.json").is_file() else [],
        provider=payload.get("provider"),
        notes="DeepSeek-compatible smoke call returned a non-truncated JSON response.",
    )


def _accepted_design_link(run_dir: Path) -> dict[str, Any]:
    metrics = _read_json(run_dir / "calls" / "01-design-brief" / "metrics.json")
    passed = _has_live_stop(metrics) and (run_dir / "design-brief" / "design-brief.json").is_file()
    return _link(
        link_id="accepted_user_input_to_design_brief",
        source_stage="user_input",
        target_stage="design_brief",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="live_model_verified" if passed else "missing",
        provider_response_ids=_response_ids(metrics),
        finish_reasons=_finish_reasons(metrics),
        evidence_paths=_existing_paths(
            run_dir,
            [
                "calls/01-design-brief/request.redacted.json",
                "calls/01-design-brief/response.raw.json",
                "calls/01-design-brief/metrics.json",
                "design-brief/design-brief.json",
            ],
        ),
        model=metrics.get("model"),
        notes="Accepted run used a real model call to produce a Design Brief.",
    )


def _accepted_generator_link(run_dir: Path) -> dict[str, Any]:
    metrics = _read_json(run_dir / "generator" / "metrics.json")
    passed = (
        _has_live_stop(metrics)
        and (run_dir / "generator" / "candidate.json").is_file()
        and (run_dir / "generator" / "validation.json").is_file()
    )
    return _link(
        link_id="accepted_design_brief_to_bim_json",
        source_stage="design_brief",
        target_stage="bim_json_generator",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="live_model_verified" if passed else "missing",
        provider_response_ids=_response_ids(metrics),
        finish_reasons=_finish_reasons(metrics),
        evidence_paths=_existing_paths(
            run_dir,
            [
                "generator/prompt-rendered.md",
                "generator/trace/request.redacted.json",
                "generator/trace/response.raw.json",
                "generator/metrics.json",
                "generator/candidate.json",
                "generator/validation.json",
            ],
        ),
        model=metrics.get("model"),
        notes="Accepted run used a real model call to generate BIM JSON before validation.",
    )


def _accepted_gate_link(run_dir: Path) -> dict[str, Any]:
    case_result = _read_json(run_dir / "case-result.json")
    passed = (
        case_result.get("deterministic_gates_passed") is True
        and case_result.get("compile_reopen_passed") is True
        and (run_dir / "gate-summary.json").is_file()
        and (run_dir / "ifc-verification.json").is_file()
    )
    return _link(
        link_id="accepted_bim_json_to_deterministic_gates",
        source_stage="bim_json",
        target_stage="deterministic_gates",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="deterministic_verified" if passed else "missing",
        evidence_paths=_existing_paths(
            run_dir,
            ["gate-summary.json", "geometry-feedback.json", "ifc-verification.json", "case-result.json"],
        ),
        final_status=case_result.get("final_status"),
        route=case_result.get("route"),
        notes="Local schema, compiler, reopen, and geometry gates accepted the candidate.",
    )


def _accepted_audit_link(run_dir: Path) -> dict[str, Any]:
    metrics = _read_json(run_dir / "audit" / "metrics.json")
    case_result = _read_json(run_dir / "case-result.json")
    passed = (
        _has_live_stop(metrics)
        and case_result.get("audit_passed") is True
        and (run_dir / "audit" / "audit-report.json").is_file()
    )
    return _link(
        link_id="accepted_deterministic_gates_to_audit",
        source_stage="deterministic_gates",
        target_stage="audit_agent",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="live_model_verified" if passed else "missing",
        provider_response_ids=_response_ids(metrics),
        finish_reasons=_finish_reasons(metrics),
        evidence_paths=_existing_paths(
            run_dir,
            [
                "audit/prompt-rendered.md",
                "audit/trace/request.redacted.json",
                "audit/trace/response.raw.json",
                "audit/metrics.json",
                "audit/audit-report.json",
            ],
        ),
        model=metrics.get("model"),
        final_status=case_result.get("final_status"),
        route=case_result.get("route"),
        notes="Audit Agent reviewed the accepted candidate after deterministic gates.",
    )


def _accepted_ifc_link(run_dir: Path) -> dict[str, Any]:
    case_result = _read_json(run_dir / "case-result.json")
    route = _read_json(run_dir / "route-decision.json")
    passed = (
        case_result.get("final_status") == "accepted"
        and route.get("route") == "accepted"
        and (run_dir / "output.ifc").is_file()
        and (run_dir / "report.md").is_file()
    )
    return _link(
        link_id="accepted_audit_to_ifc",
        source_stage="audit_agent",
        target_stage="ifc_and_report",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="artifact_verified" if passed else "missing",
        evidence_paths=_existing_paths(
            run_dir,
            ["route-decision.json", "feedback-rounds.json", "output.ifc", "report.md"],
        ),
        final_status=case_result.get("final_status"),
        route=route.get("route"),
        notes="Accepted route produced the final IFC and human review report.",
    )


def _nonaccept_design_link(run_dir: Path) -> dict[str, Any]:
    metrics_paths = sorted((run_dir / "calls").glob("*/metrics.json"))
    metrics = [_read_json(path) for path in metrics_paths]
    passed = bool(metrics) and all(_has_live_stop(item) for item in metrics)
    return _link(
        link_id="nonaccept_user_input_to_design_brief_draft",
        source_stage="user_input",
        target_stage="design_brief_draft",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="live_model_verified" if passed else "missing",
        provider_response_ids=[rid for item in metrics for rid in _response_ids(item)],
        finish_reasons=[reason for item in metrics for reason in _finish_reasons(item)],
        evidence_paths=_existing_paths(run_dir, ["calls", "design-brief.json", "conversation.json"]),
        model=next((item.get("model") for item in metrics if item.get("model")), None),
        notes="Non-accept run used real model calls and remained in Draft instead of inventing missing facts.",
    )


def _nonaccept_route_link(run_dir: Path) -> dict[str, Any]:
    case_result = _read_json(run_dir / "case-result.json")
    route = _read_json(run_dir / "route-decision.json")
    passed = (
        case_result.get("final_status") == "draft"
        and route.get("route") == "ask_user"
        and (run_dir / "issues.json").is_file()
        and (run_dir / "feedback-rounds.json").is_file()
        and (run_dir / "report.md").is_file()
    )
    return _link(
        link_id="nonaccept_issues_to_ask_user",
        source_stage="issues",
        target_stage="user",
        required=True,
        status="passed" if passed else "failed",
        evidence_level="artifact_verified" if passed else "missing",
        evidence_paths=_existing_paths(
            run_dir,
            ["issues.json", "route-decision.json", "feedback-rounds.json", "case-result.json", "report.md"],
        ),
        final_status=case_result.get("final_status"),
        route=route.get("route"),
        notes="Missing user facts became issues and routed to ask_user, not accepted IFC.",
    )


def _link(
    *,
    link_id: str,
    source_stage: str,
    target_stage: str,
    required: bool,
    status: str,
    evidence_level: str,
    provider_response_ids: list[str] | None = None,
    finish_reasons: list[str] | None = None,
    evidence_paths: list[str] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "link_id": link_id,
        "source_stage": source_stage,
        "target_stage": target_stage,
        "required": required,
        "status": status,
        "evidence_level": evidence_level,
        "provider_response_ids": provider_response_ids or [],
        "finish_reasons": finish_reasons or [],
        "evidence_paths": evidence_paths or [],
    }
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Phase 6.4 Supplemental Live Chain Coverage",
        "",
        f"- provider: `{result['provider']}`",
        f"- accepted_session_hash: `{result['accepted_session_hash']}`",
        f"- nonaccept_session_hash: `{result['nonaccept_session_hash']}`",
        f"- all_required_links_passed: `{result['all_required_links_passed']}`",
        f"- passed_required_link_count: `{result['passed_required_link_count']}` / `{result['required_link_count']}`",
        "",
        "## Coverage Matrix",
        "",
        "| Link | Status | Evidence | Route | Response IDs | Evidence Paths |",
        "|---|---|---|---|---|---|",
    ]
    for link in result["links"]:
        response_ids = ", ".join(f"`{item}`" for item in link.get("provider_response_ids", [])) or "-"
        route = link.get("route", "-")
        paths = "<br>".join(f"`{item}`" for item in link.get("evidence_paths", [])) or "-"
        lines.append(
            f"| `{link['link_id']}` | `{link['status']}` | `{link['evidence_level']}` | "
            f"`{route}` | {response_ids} | {paths} |"
        )
    if result["missing_required_link_ids"]:
        lines.extend(["", "## Missing Required Links", ""])
        lines.extend(f"- `{link_id}`" for link_id in result["missing_required_link_ids"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _existing_paths(root: Path, paths: list[str]) -> list[str]:
    return [path for path in paths if (root / path).exists()]


def _has_live_stop(metrics: dict[str, Any]) -> bool:
    finish_reason = metrics.get("finish_reason") or metrics.get("stop_reason")
    return bool(metrics.get("response_id")) and finish_reason == "stop"


def _response_ids(metrics: dict[str, Any]) -> list[str]:
    response_id = _string_or_none(metrics.get("response_id"))
    return [response_id] if response_id else []


def _finish_reasons(metrics: dict[str, Any]) -> list[str]:
    finish_reason = _string_or_none(metrics.get("finish_reason") or metrics.get("stop_reason"))
    return [finish_reason] if finish_reason else []


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _provider_from_smoke(root: Path) -> str | None:
    provider = _read_json(root / "smoke-json.json").get("provider")
    return str(provider) if provider else None


def _provider_from_links(links: list[dict[str, Any]]) -> str | None:
    for link in links:
        provider = link.get("provider")
        if provider:
            return str(provider)
    return None
