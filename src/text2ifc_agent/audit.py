"""Evidence-linked semantic audit subordinate to deterministic gates."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any


REQUIRED_EVIDENCE = (
    "input",
    "design_brief",
    "candidate",
    "validation",
    "geometry",
    "raw_response",
)


def collect_revision_audit_evidence(case_dir: Path | str) -> dict[str, Any]:
    """Collect hash-bound revision, ChangeSet, Gate, and IFC sidecars for Audit."""

    root = Path(case_dir)
    revision = _first_json(
        root / "candidate-revision.json",
        root / "generator" / "candidate-revision.json",
        root / "generator-staged" / "candidate-revision.json",
    )
    if not revision:
        return {
            "status": "not_applicable",
            "reason": "No candidate revision sidecar exists for this legacy run.",
            "issues": [],
        }
    preservation = _read_json(root / "component-preservation.json")
    gate_evidence = _read_json(root / "revision-gates.json")
    package_records = _read_json(root / "generator-staged" / "package-records.json")
    changesets = _collect_named_sidecars(root, "changeset.json")
    scopes = _collect_named_sidecars(root, "change-scope.json")
    operations = [
        dict(operation)
        for record in changesets
        for operation in record["payload"].get("operations", [])
        if isinstance(operation, Mapping)
    ]
    source_issue_ids = sorted(
        {
            str(issue_id)
            for record in changesets
            for issue_id in record["payload"].get("source_issue_ids", [])
        }
    )
    issues: list[dict[str, str]] = []
    candidate_hash = revision.get("candidate_hash")
    gate_hash = (
        gate_evidence.get("plan", {})
        .get("revision_binding", {})
        .get("candidate_hash")
    )
    if gate_evidence and gate_hash != candidate_hash:
        issues.append(
            {
                "code": "AUDIT_REVISION_HASH_MISMATCH",
                "path": "/gate_evidence/plan/revision_binding/candidate_hash",
                "message": "Revision and Gate evidence candidate hashes differ.",
            }
        )
    return {
        "status": "binding_failed" if issues else "bound",
        "revision": revision,
        "changed_ids": list(preservation.get("changed_ids", [])),
        "dependency_ids": list(preservation.get("dependency_ids", [])),
        "preservation": preservation,
        "source_issue_ids": source_issue_ids,
        "operations": operations,
        "scopes": scopes,
        "packages": list(package_records.get("packages", [])),
        "gate_evidence": gate_evidence,
        "ifc_result": _read_json(root / "ifc-verification.json"),
        "geometry_result": _read_json(root / "geometry-feedback.json"),
        "issues": issues,
    }


def build_audit_report(
    *,
    deterministic_gates: Mapping[str, bool],
    intent_coverage: Mapping[str, str],
    mismatches: Sequence[Mapping[str, Any]],
    unsupported_facts: Sequence[Mapping[str, Any] | str],
    evidence: Mapping[str, str],
    narrative_recommendation: str | None = None,
) -> dict[str, Any]:
    """Build an audit report without allowing narrative to override gates."""
    failed_gates = sorted(
        name for name, passed in deterministic_gates.items() if passed is not True
    )
    missing_evidence = [name for name in REQUIRED_EVIDENCE if not evidence.get(name)]
    diagnostics = [
        {
            "code": "MISSING_EVIDENCE",
            "path": f"/evidence/{name}",
            "message": f"Required audit evidence path {name!r} is missing.",
        }
        for name in missing_evidence
    ]
    mismatch_records = [dict(item) for item in mismatches]
    blocking = bool(failed_gates or missing_evidence or mismatch_records)
    if failed_gates or missing_evidence:
        recommendation = "reject"
    elif mismatch_records or unsupported_facts:
        recommendation = "revise"
    else:
        recommendation = "accept"
    return {
        "deterministic_status": "failed" if failed_gates else "passed",
        "deterministic_gates": dict(deterministic_gates),
        "failed_gates": failed_gates,
        "intent_coverage": dict(intent_coverage),
        "mismatches": mismatch_records,
        "unsupported_facts": list(unsupported_facts),
        "evidence": dict(evidence),
        "diagnostics": diagnostics,
        "narrative_recommendation": narrative_recommendation,
        "recommendation": recommendation,
        "blocking": blocking,
    }


def _collect_named_sidecars(root: Path, name: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob(f"changeset-round-*/{name}")):
        records.append({"path": path.relative_to(root).as_posix(), "payload": _read_json(path)})
    for path in sorted((root / "generator-staged").glob(f"package-*/**/{name}")):
        records.append({"path": path.relative_to(root).as_posix(), "payload": _read_json(path)})
    return records


def _first_json(*paths: Path) -> dict[str, Any]:
    for path in paths:
        payload = _read_json(path)
        if payload:
            return payload
    return {}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}
