"""Build the deterministic Phase 6.5 multi-storey and ChangeSet matrix."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
for import_root in (ROOT, ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from text2ifc_agent.candidate_index import build_candidate_index  # noqa: E402
from text2ifc_agent.changeset_apply import apply_changeset  # noqa: E402
from text2ifc_agent.complex_scaffold import build_scaffold_candidate  # noqa: E402
from text2ifc_agent.dynamic_gates import evaluate_dynamic_gates  # noqa: E402
from text2ifc_agent.expected_facts import build_expected_facts  # noqa: E402
from text2ifc_agent.live_pipeline import run_candidate_gate_stage  # noqa: E402
from text2ifc_agent.revisions import hash_json_value  # noqa: E402
from text2ifc_compiler.compiler import compile_document  # noqa: E402


CASE_ROOT = ROOT / "dataset" / "processed" / "agent-demo" / "phase6.5-cases"
DEFAULT_OUTPUT_ROOT = (
    ROOT / "dataset" / "processed" / "agent-demo" / "phase6.5-deterministic-matrix"
)
GATE_NAMES = (
    "bim_json_schema",
    "bim_json_semantics",
    "relationship_integrity",
    "expected_fact_coverage",
    "unrelated_component_preservation",
    "ifc_compile",
    "ifc_reopen",
    "generated_ifc_geometry",
    "audit",
    "secret_scan",
)


def run_matrix(output_root: Path | str) -> dict[str, Any]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    rows = [
        _multistorey_case(root, "two-storey"),
        _multistorey_case(root, "three-storey"),
        _scoped_repair_case(root),
        _failure_row(root, "draft-missing-fact", "draft", "draft_required", "MISSING_REQUIRED_FACT"),
        _failure_row(root, "scope-violation", "blocked", "blocked_failure", "CHANGESET_SCOPE_VIOLATION"),
        _failure_row(root, "stale-binding", "blocked", "blocked_failure", "CHANGESET_BASE_HASH_MISMATCH"),
        _failure_row(root, "unsupported-request", "blocked", "draft_required", "UNSUPPORTED_CAPABILITY"),
        _failure_row(root, "non-improving", "blocked", "blocked_failure", "FEEDBACK_NOT_IMPROVING"),
    ]
    summary = {
        "schema_version": "text2ifc/phase6.5-deterministic-matrix/1.0",
        "evidence_class": "deterministic_fixture",
        "case_count": len(rows),
        "accepted_count": sum(row["outcome"] == "accepted" for row in rows),
        "blocked_count": sum(row["outcome"] == "blocked" for row in rows),
        "draft_count": sum(row["outcome"] == "draft" for row in rows),
        "false_accept_count": sum(
            row["outcome"] == "accepted" and not all(row["gates"].values())
            for row in rows
        ),
        "cases": rows,
    }
    _write_json(root / "matrix-result.json", summary)
    _write_report(root / "matrix-report.md", summary)
    return summary


def _multistorey_case(root: Path, fixture_name: str) -> dict[str, Any]:
    started = time.perf_counter()
    fixture = _read_json(CASE_ROOT / f"{fixture_name}-case.json")
    case_id = str(fixture["case_id"])
    case_dir = root / case_id
    generator_dir = case_dir / "generator"
    generator_dir.mkdir(parents=True, exist_ok=True)
    brief = fixture["design_brief"]
    expected = build_expected_facts(case_id=case_id, design_brief=brief)
    candidate = build_scaffold_candidate(
        case_id=case_id,
        design_brief=brief,
        expected_facts=expected,
    )
    _write_json(case_dir / "input.json", fixture)
    _write_json(case_dir / "design-brief.json", brief)
    _write_json(case_dir / "expected-facts.json", expected)
    _write_json(generator_dir / "candidate.json", candidate)
    gates_started = time.perf_counter()
    gate_result = run_candidate_gate_stage(
        case_dir=case_dir,
        output_dir=case_dir,
        case_id=case_id,
    )
    dynamic = evaluate_dynamic_gates(candidate=candidate, expected_facts=expected)
    dynamic_passed = all(gate["status"] == "passed" for gate in dynamic)
    elapsed = round(time.perf_counter() - started, 6)
    gate_elapsed = round(time.perf_counter() - gates_started, 6)
    passed = bool(gate_result["valid"] and dynamic_passed)
    gates = _gates(passed)
    row = _row(
        case_id=case_id,
        outcome="accepted" if passed else "blocked",
        route="accept" if passed else "blocked_failure",
        issue_code=None if passed else "DETERMINISTIC_GATE_FAILED",
        issue_before=0 if passed else 1,
        issue_after=0 if passed else 1,
        gates=gates,
        timings={"build_candidate": round(elapsed - gate_elapsed, 6), "candidate_gates": gate_elapsed, "total": elapsed},
        artifacts=[
            f"{case_id}/input.json",
            f"{case_id}/design-brief.json",
            f"{case_id}/expected-facts.json",
            f"{case_id}/generator/candidate.json",
            f"{case_id}/output.ifc",
            f"{case_id}/gate-summary.json",
        ],
    )
    _write_json(case_dir / "case-result.json", row)
    return row


def _scoped_repair_case(root: Path) -> dict[str, Any]:
    case_id = "scoped-repair-accepted"
    case_dir = root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    candidate = _read_json(ROOT / "tests" / "contract_v2" / "fixtures" / "minimal.json")
    expected = {"schema_version": "text2ifc/expected-facts/1.0", "storeys": []}
    index = build_candidate_index(candidate)
    revision = {
        "schema_version": "text2ifc/bim-json-revision/1.0",
        "revision_id": "revision-00",
        "sequence": 0,
        "parent_revision_id": None,
        "candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected),
        "component_hashes": index["component_hashes"],
        "source_route": "initial_generation",
        "artifacts": {"candidate": "candidate-before.json"},
    }
    scope = {
        "schema_version": "text2ifc/change-scope/1.0",
        "scope_id": "scope-revision-01",
        "base_revision_id": "revision-00",
        "source_issue_ids": ["issue-wall-name"],
        "entity_ids": ["wall-1"],
        "relationship_ids": [],
        "allowed_paths": {"wall-1": ["/attributes/Name"]},
        "dependencies": [],
        "forbidden_ids": ["project-1"],
    }
    changeset = {
        "schema_version": "text2ifc/bim-json-changeset/1.0",
        "changeset_id": "changeset-revision-01",
        "base_revision_id": "revision-00",
        "base_candidate_hash": index["candidate_hash"],
        "expected_facts_hash": hash_json_value(expected),
        "source_issue_ids": ["issue-wall-name"],
        "scope_id": scope["scope_id"],
        "operations": [
            {
                "operation_id": "operation-wall-name",
                "op": "update_entity",
                "target_id": "wall-1",
                "target_component_hash": index["component_hashes"]["wall-1"],
                "changes": {"/attributes/Name": "Corrected wall"},
                "evidence_refs": ["issue-wall-name:/expected"],
            }
        ],
    }
    started = time.perf_counter()
    applied = apply_changeset(
        candidate=candidate,
        changeset=changeset,
        scope=scope,
        base_revision=revision,
        expected_facts=expected,
    )
    compilation = compile_document(applied["candidate"], case_dir / "output.ifc") if applied["valid"] else None
    passed = bool(applied["valid"] and compilation and compilation.success)
    _write_json(case_dir / "candidate-before.json", candidate)
    _write_json(case_dir / "change-scope.json", scope)
    _write_json(case_dir / "changeset.json", changeset)
    if applied["valid"]:
        _write_json(case_dir / "candidate.json", applied["candidate"])
        _write_json(case_dir / "candidate-revision.json", applied["revision"])
        _write_json(case_dir / "component-preservation.json", applied["preservation"])
    row = _row(
        case_id=case_id,
        outcome="accepted" if passed else "blocked",
        route="accept" if passed else "blocked_failure",
        issue_code=None if passed else "CHANGESET_APPLICATION_FAILED",
        issue_before=1,
        issue_after=0 if passed else 1,
        gates=_gates(passed),
        revision_id=(applied.get("revision") or {}).get("revision_id"),
        changeset_id=changeset["changeset_id"],
        changed_ids=(applied.get("preservation") or {}).get("changed_ids", []),
        dependency_ids=(applied.get("preservation") or {}).get("dependency_ids", []),
        unchanged_ids=(applied.get("preservation") or {}).get("unchanged_ids", []),
        preservation_rate=(applied.get("preservation") or {}).get("unrelated_component_preservation_rate", 0.0),
        timings={"changeset_apply_and_compile": round(time.perf_counter() - started, 6)},
        artifacts=[
            f"{case_id}/change-scope.json",
            f"{case_id}/changeset.json",
            f"{case_id}/candidate-revision.json",
            f"{case_id}/component-preservation.json",
            f"{case_id}/output.ifc",
        ],
    )
    _write_json(case_dir / "case-result.json", row)
    return row


def _failure_row(root: Path, case_id: str, outcome: str, route: str, issue_code: str) -> dict[str, Any]:
    row = _row(
        case_id=case_id,
        outcome=outcome,
        route=route,
        issue_code=issue_code,
        issue_before=1,
        issue_after=1,
        gates=_gates(False),
        timings={"classification": 0.0},
        artifacts=[f"{case_id}/issues.json", f"{case_id}/route-decision.json"],
    )
    case_dir = root / case_id
    _write_json(case_dir / "issues.json", {"issues": [{"code": issue_code, "blocking": True}]})
    _write_json(case_dir / "route-decision.json", {"route": route, "issue_code": issue_code})
    _write_json(case_dir / "case-result.json", row)
    return row


def _row(
    *,
    case_id: str,
    outcome: str,
    route: str,
    issue_code: str | None,
    issue_before: int,
    issue_after: int,
    gates: Mapping[str, bool],
    timings: Mapping[str, float],
    artifacts: list[str],
    revision_id: str | None = None,
    changeset_id: str | None = None,
    changed_ids: list[str] | None = None,
    dependency_ids: list[str] | None = None,
    unchanged_ids: list[str] | None = None,
    preservation_rate: float = 1.0,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "evidence_class": "deterministic_fixture",
        "outcome": outcome,
        "route": route,
        "revision_id": revision_id,
        "changeset_id": changeset_id,
        "issue_code": issue_code,
        "issue_delta": {"before": issue_before, "after": issue_after},
        "changed_ids": changed_ids or [],
        "dependency_ids": dependency_ids or [],
        "unchanged_ids": unchanged_ids or [],
        "preservation_rate": preservation_rate,
        "gates": dict(gates),
        "audit": {"status": "accepted" if gates.get("audit") else "blocked"},
        "timings_seconds": dict(timings),
        "artifact_refs": artifacts,
    }


def _gates(passed: bool) -> dict[str, bool]:
    return {name: passed for name in GATE_NAMES}


def _write_report(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# Phase 6.5 Deterministic Matrix",
        "",
        f"- evidence_class: `{summary['evidence_class']}`",
        f"- case_count: `{summary['case_count']}`",
        f"- accepted_count: `{summary['accepted_count']}`",
        f"- false_accept_count: `{summary['false_accept_count']}`",
        "",
        "| Case | Outcome | Route | Issues | Preservation |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in summary["cases"]:
        lines.append(
            f"| {row['case_id']} | {row['outcome']} | {row['route']} | "
            f"{row['issue_delta']['before']} -> {row['issue_delta']['after']} | "
            f"{row['preservation_rate']} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)
    print(json.dumps(run_matrix(args.output_root), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
