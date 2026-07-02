"""Gate/Audit evidence bundle helpers for Phase 6.3."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


GATE_SUMMARY_SCHEMA_VERSION = "text2ifc/gate-summary/1.0"


def hash_json_file(path: Path | str) -> str:
    """Hash JSON by canonical content so formatting changes do not matter."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def write_gate_summary(
    *,
    case_dir: Path | str,
    case_id: str,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Write a shared deterministic gate summary for the current candidate."""
    root = Path(case_dir)
    output = Path(output_dir) if output_dir is not None else root
    output.mkdir(parents=True, exist_ok=True)

    candidate_path = root / "generator" / "candidate.json"
    if not candidate_path.is_file():
        raise ValueError("gate summary requires generator/candidate.json")
    candidate_relative = _relative(root, candidate_path)
    candidate_hash = hash_json_file(candidate_path)

    expected_facts_path = root / "expected-facts.json"
    expected_facts_relative = (
        _relative(root, expected_facts_path) if expected_facts_path.is_file() else None
    )
    expected_facts_hash = (
        hash_json_file(expected_facts_path) if expected_facts_path.is_file() else None
    )

    artifact_paths = _existing_artifact_paths(
        root,
        [
            "generator/candidate.json",
            "generator/validation.json",
            "expected-facts.json",
            "semantic-coverage.json",
            "ifc-verification.json",
            "geometry-feedback.json",
            "repair/route.json",
        ],
    )
    artifact_hashes = {
        relative: hash_json_file(root / relative) for relative in artifact_paths
    }

    gates = [
        _bim_json_validation_gate(root),
        _semantic_coverage_gate(root),
        _ifc_compile_reopen_gate(root),
        _geometry_gate(root),
        _repair_route_gate(root),
    ]
    summary = {
        "schema_version": GATE_SUMMARY_SCHEMA_VERSION,
        "case_id": case_id,
        "candidate_path": candidate_relative,
        "candidate_hash": candidate_hash,
        "expected_facts_path": expected_facts_relative,
        "expected_facts_hash": expected_facts_hash,
        "artifact_hashes": artifact_hashes,
        "evidence": {
            "schema_validation": _read_optional_json(root / "generator" / "validation.json"),
            "semantic_coverage": _read_optional_json(root / "semantic-coverage.json"),
            "compile_reopen": _read_optional_json(root / "ifc-verification.json"),
            "geometry": _read_optional_json(root / "geometry-feedback.json"),
            "repair_history": _read_optional_json(root / "repair" / "route.json"),
        },
        "gates": gates,
        "overall_status": _overall_status(gates),
    }
    _write_json(output / "gate-summary.json", summary)
    return summary


def validate_gate_summary_binding(
    *,
    case_dir: Path | str,
    summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return blocking evidence-binding issues for stale gate summaries."""
    root = Path(case_dir)
    issues: list[dict[str, Any]] = []
    candidate_path = root / str(summary.get("candidate_path", ""))
    if candidate_path.is_file():
        current_hash = hash_json_file(candidate_path)
        if summary.get("candidate_hash") != current_hash:
            issues.append(
                {
                    "code": "CANDIDATE_HASH_MISMATCH",
                    "path": "/candidate_hash",
                    "expected": current_hash,
                    "actual": summary.get("candidate_hash"),
                }
            )
    expected_path_value = summary.get("expected_facts_path")
    if isinstance(expected_path_value, str) and expected_path_value:
        expected_path = root / expected_path_value
        if expected_path.is_file():
            current_hash = hash_json_file(expected_path)
            if summary.get("expected_facts_hash") != current_hash:
                issues.append(
                    {
                        "code": "EXPECTED_FACTS_HASH_MISMATCH",
                        "path": "/expected_facts_hash",
                        "expected": current_hash,
                        "actual": summary.get("expected_facts_hash"),
                    }
                )
    return issues


def gate_summary_hash(path: Path | str) -> str:
    """Hash a written gate summary file."""
    return hash_json_file(path)


def _bim_json_validation_gate(root: Path) -> dict[str, Any]:
    payload = _read_optional_json(root / "generator" / "validation.json")
    if payload is None:
        return _gate(
            "bim_json_validation",
            applicability="not_applicable",
            status="skipped",
            basis="generator validation sidecar is not present",
            source_paths=[],
        )
    issues = _issues_from_payload(payload)
    return _gate(
        "bim_json_validation",
        applicability="applicable",
        status="passed" if payload.get("valid") is True else "failed",
        basis="generator validation sidecar",
        issues=issues,
        source_paths=["generator/validation.json"],
    )


def _semantic_coverage_gate(root: Path) -> dict[str, Any]:
    payload = _read_optional_json(root / "semantic-coverage.json")
    if payload is None:
        return _gate(
            "semantic_coverage",
            applicability="not_applicable",
            status="skipped",
            basis="semantic coverage sidecar is not present",
            source_paths=[],
        )
    issues = [
        {
            "code": _semantic_fact_code(fact),
            "path": fact.get("path", "/blocking_facts"),
            "message": fact.get("reason", "Semantic fact is not covered."),
        }
        for fact in payload.get("blocking_facts", [])
        if isinstance(fact, Mapping)
    ]
    return _gate(
        "semantic_coverage",
        applicability="applicable",
        status="passed" if payload.get("valid") is True else "failed",
        basis="semantic coverage sidecar",
        issues=issues,
        source_paths=["semantic-coverage.json"],
    )


def _ifc_compile_reopen_gate(root: Path) -> dict[str, Any]:
    payload = _read_optional_json(root / "ifc-verification.json")
    if payload is None:
        return _gate(
            "ifc_compile_reopen",
            applicability="not_applicable",
            status="skipped",
            basis="IFC verification sidecar is not present",
            source_paths=[],
        )
    issues = [
        *_issues_from_payload({"issues": payload.get("input_issues", [])}),
        *_issues_from_payload({"issues": payload.get("ifc_issues", [])}),
    ]
    return _gate(
        "ifc_compile_reopen",
        applicability="applicable",
        status="passed" if payload.get("success") is True else "failed",
        basis="IFC compile/reopen sidecar",
        issues=issues,
        source_paths=["ifc-verification.json"],
    )


def _geometry_gate(root: Path) -> dict[str, Any]:
    payload = _read_optional_json(root / "geometry-feedback.json")
    if payload is None:
        return _gate(
            "geometry",
            applicability="not_applicable",
            status="skipped",
            basis="geometry feedback sidecar is not present",
            source_paths=[],
        )
    issues = _issues_from_payload(payload)
    return _gate(
        "geometry",
        applicability="applicable",
        status="passed" if payload.get("success") is True else "failed",
        basis="geometry feedback sidecar",
        issues=issues,
        source_paths=["geometry-feedback.json"],
    )


def _repair_route_gate(root: Path) -> dict[str, Any]:
    payload = _read_optional_json(root / "repair" / "route.json")
    if payload is None:
        return _gate(
            "repair_route",
            applicability="not_applicable",
            status="skipped",
            basis="repair route sidecar is not present",
            source_paths=[],
        )
    route = payload.get("route")
    passed = route in {"no_repair_needed", "repair_attempted", "draft_required"}
    return _gate(
        "repair_route",
        applicability="applicable",
        status="passed" if passed else "blocked",
        basis=f"repair route is {route}",
        issues=[] if passed else [{"code": "REPAIR_ROUTE_BLOCKED", "path": "/route"}],
        source_paths=["repair/route.json"],
    )


def _gate(
    name: str,
    *,
    applicability: str,
    status: str,
    basis: str,
    issues: list[dict[str, Any]] | None = None,
    source_paths: list[str],
) -> dict[str, Any]:
    issue_list = list(issues or [])
    return {
        "name": name,
        "applicability": applicability,
        "status": status,
        "basis": basis,
        "issue_count": len(issue_list),
        "issues": issue_list,
        "issue_codes": sorted({str(issue.get("code", "UNKNOWN")) for issue in issue_list}),
        "source_paths": source_paths,
    }


def _issues_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_issues = payload.get("issues", [])
    if not isinstance(raw_issues, list):
        return []
    result: list[dict[str, Any]] = []
    for issue in raw_issues:
        if not isinstance(issue, Mapping):
            continue
        result.append(
            {
                "code": str(issue.get("code", "UNKNOWN")),
                "path": str(issue.get("path", "/")),
                **(
                    {"message": str(issue["message"])}
                    if issue.get("message") is not None
                    else {}
                ),
            }
        )
    return result


def _semantic_fact_code(fact: Mapping[str, Any]) -> str:
    state = fact.get("coverage_state")
    if state == "unsupported_draft":
        return "UNSUPPORTED_FACT"
    if state == "blocked_unknown_capability":
        return "UNKNOWN_CAPABILITY_FACT"
    return "SEMANTIC_COVERAGE_BLOCKING"


def _overall_status(gates: list[Mapping[str, Any]]) -> str:
    statuses = {gate.get("status") for gate in gates}
    if "failed" in statuses:
        return "failed"
    if "blocked" in statuses:
        return "blocked"
    if "inconclusive" in statuses:
        return "inconclusive"
    return "passed"


def _existing_artifact_paths(root: Path, relatives: list[str]) -> list[str]:
    return [relative for relative in relatives if (root / relative).is_file()]


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _read_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(_canonical_json(payload) + "\n", encoding="utf-8")


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
