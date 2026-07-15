"""Verify Phase 6.3 matrix artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps" / "python312"))

from text2ifc_agent.gate_audit_bundle import (  # noqa: E402
    gate_summary_hash,
    hash_json_file,
    validate_gate_summary_binding,
)
from text2ifc_agent.route_decision import validate_route_decision_binding  # noqa: E402


DEFAULT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.3-gate-audit"
)
VERIFICATION_SCHEMA_VERSION = "text2ifc/phase6.3-final-verification/1.0"
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"tp-[A-Za-z0-9_-]{12,}"),
    re.compile(r"(?i)(api[_-]?key|authorization|anthropic[_-]?auth[_-]?token)"),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args(argv)
    result = verify(args.root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["valid"] else 2


def verify(root: Path) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if not root.is_dir():
        issues.append({"code": "ROOT_MISSING", "path": str(root)})
        return _write_result(root, issues=issues, cases=[])

    if not (root / "matrix-report.md").is_file():
        issues.append({"code": "MATRIX_REPORT_MISSING", "path": "matrix-report.md"})

    cases = []
    for case_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        case_result = _verify_case(root, case_dir)
        cases.append(case_result)
        issues.extend(case_result["issues"])

    if not cases:
        issues.append({"code": "NO_CASES_FOUND", "path": "/"})

    secret_findings = _scan_secrets(root)
    for finding in secret_findings:
        issues.append({"code": "SECRET_FINDING", **finding})

    non_two_storey = any(
        case["case_id"] == "non-two-storey-three-level"
        and case["non_two_storey_gate_route_covered"]
        for case in cases
    )
    if not non_two_storey:
        issues.append(
            {
                "code": "NON_TWO_STOREY_GATE_ROUTE_NOT_COVERED",
                "path": "/non-two-storey-three-level",
            }
        )

    return _write_result(
        root,
        issues=issues,
        cases=cases,
        secret_finding_count=len(secret_findings),
        non_two_storey_gate_route_covered=non_two_storey,
    )


def _verify_case(root: Path, case_dir: Path) -> dict[str, Any]:
    rel_case = case_dir.relative_to(root).as_posix()
    issues: list[dict[str, Any]] = []
    required = [
        "expected-facts.json",
        "generator/candidate.json",
        "gate-summary.json",
        "route-decision.json",
        "report.md",
        "trace-manifest.json",
    ]
    for relative in required:
        if not (case_dir / relative).is_file():
            issues.append({"code": "CASE_ARTIFACT_MISSING", "path": f"{rel_case}/{relative}"})

    gate_summary = _read_json(case_dir / "gate-summary.json")
    route_decision = _read_json(case_dir / "route-decision.json")
    trace_manifest = _read_json(case_dir / "trace-manifest.json")
    if gate_summary:
        for issue in validate_gate_summary_binding(case_dir=case_dir, summary=gate_summary):
            issues.append({"code": issue["code"], "path": f"{rel_case}{issue['path']}"})
    if route_decision:
        for issue in validate_route_decision_binding(
            case_dir=case_dir,
            decision=route_decision,
        ):
            issues.append({"code": issue["code"], "path": f"{rel_case}{issue['path']}"})
    if gate_summary and route_decision:
        if route_decision.get("gate_summary_hash") != gate_summary_hash(
            case_dir / "gate-summary.json"
        ):
            issues.append(
                {
                    "code": "ROUTE_GATE_SUMMARY_HASH_MISMATCH",
                    "path": f"{rel_case}/route-decision.json",
                }
            )
        if (
            route_decision.get("route") == "accept"
            and gate_summary.get("overall_status") != "passed"
        ):
            issues.append(
                {
                    "code": "FALSE_ACCEPT_BLOCKING_GATES",
                    "path": f"{rel_case}/route-decision.json",
                }
            )
    if trace_manifest:
        issues.extend(_verify_manifest_hashes(case_dir, rel_case, trace_manifest))

    route_basis = route_decision.get("route_basis", {}) if route_decision else {}
    return {
        "case_id": case_dir.name,
        "valid": not issues,
        "issues": issues,
        "gate_overall_status": gate_summary.get("overall_status") if gate_summary else None,
        "route": route_decision.get("route") if route_decision else None,
        "non_two_storey_gate_route_covered": bool(
            route_basis.get("non_two_storey_evidence")
        ),
    }


def _verify_manifest_hashes(
    case_dir: Path,
    rel_case: str,
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    artifact_hashes = manifest.get("artifact_hashes", {})
    if not isinstance(artifact_hashes, Mapping):
        return [{"code": "TRACE_MANIFEST_HASHES_INVALID", "path": f"{rel_case}/trace-manifest.json"}]
    for relative in (
        "expected-facts.json",
        "generator/candidate.json",
        "gate-summary.json",
        "route-decision.json",
        "report.md",
    ):
        path = case_dir / relative
        actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if artifact_hashes.get(relative) != actual:
            issues.append(
                {
                    "code": "TRACE_MANIFEST_HASH_MISMATCH",
                    "path": f"{rel_case}/{relative}",
                }
            )
    return issues


def _scan_secrets(root: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append({"path": path.relative_to(root).as_posix()})
                break
    return findings


def _write_result(
    root: Path,
    *,
    issues: list[dict[str, Any]],
    cases: list[Mapping[str, Any]],
    secret_finding_count: int = 0,
    non_two_storey_gate_route_covered: bool = False,
) -> dict[str, Any]:
    issue_codes = sorted({str(issue.get("code", "UNKNOWN")) for issue in issues})
    hash_binding_valid = not any("HASH_MISMATCH" in code for code in issue_codes)
    result = {
        "schema_version": VERIFICATION_SCHEMA_VERSION,
        "valid": not issues,
        "issue_count": len(issues),
        "issue_codes": issue_codes,
        "issues": issues,
        "case_count": len(cases),
        "cases": cases,
        "hash_binding_valid": hash_binding_valid,
        "secret_finding_count": secret_finding_count,
        "non_two_storey_gate_route_covered": non_two_storey_gate_route_covered,
        "root": str(root),
    }
    root.mkdir(parents=True, exist_ok=True)
    _write_json(root / "final-verification.json", result)
    return result


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
