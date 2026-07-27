"""Schema-backed Design Brief validation for the Phase 6 intent boundary."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from text2ifc_contract.validation import (
    ValidationIssue,
    _normalize_error,
    _sort_issues,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_BRIEF_SCHEMA_PATHS = {
    "text2ifc/design-brief/1.0": (
        PROJECT_ROOT / "schemas" / "agent" / "design-brief" / "1.0" / "schema.json"
    ),
    "text2ifc/design-brief/2.0": (
        PROJECT_ROOT / "schemas" / "agent" / "design-brief" / "2.0" / "schema.json"
    ),
}


@lru_cache(maxsize=2)
def load_design_brief_schema(
    schema_version: str = "text2ifc/design-brief/1.0",
) -> dict[str, Any]:
    """Load and meta-validate the canonical Design Brief schema."""
    path = DESIGN_BRIEF_SCHEMA_PATHS.get(schema_version)
    if path is None:
        raise ValueError(f"unsupported Design Brief schema version: {schema_version}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_design_brief(
    document: Any,
    *,
    evidence_catalog: list[dict[str, Any]] | None = None,
) -> list[ValidationIssue]:
    """Return stable field-level issues without mutating the brief."""
    schema_version = (
        document.get("schema_version")
        if isinstance(document, dict)
        else "text2ifc/design-brief/1.0"
    )
    if schema_version not in DESIGN_BRIEF_SCHEMA_PATHS:
        return [
            ValidationIssue(
                code="UNSUPPORTED_DESIGN_BRIEF_VERSION",
                path="/schema_version",
                message=f"Unsupported Design Brief schema version: {schema_version!r}.",
            )
        ]
    validator = Draft202012Validator(load_design_brief_schema(schema_version))
    issues = [
        issue
        for error in validator.iter_errors(document)
        for issue in _normalize_error(error)
    ]
    if schema_version == "text2ifc/design-brief/2.0" and isinstance(document, dict):
        issues.extend(_validate_v2_semantics(document, evidence_catalog or []))
    return _sort_issues(issues)


def _validate_v2_semantics(
    document: dict[str, Any],
    evidence_catalog: list[dict[str, Any]],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    supplied_evidence = {
        str(record.get("evidence_id"))
        for record in evidence_catalog
        if isinstance(record, dict) and record.get("evidence_id")
    }
    evidence_locations = (
        ("fact_sources", document.get("fact_sources", [])),
        ("missing_facts", document.get("missing_facts", [])),
        ("ambiguities", document.get("ambiguities", [])),
        ("unsupported_requests", document.get("unsupported_requests", [])),
        ("user_corrections", document.get("user_corrections", [])),
        ("clarification_questions", document.get("clarification_questions", [])),
    )
    for collection_name, records in evidence_locations:
        if not isinstance(records, list):
            continue
        for record_index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            refs = record.get("evidence_refs", [])
            if not isinstance(refs, list):
                continue
            for ref_index, evidence_ref in enumerate(refs):
                if evidence_ref not in supplied_evidence:
                    issues.append(
                        ValidationIssue(
                            code="UNKNOWN_EVIDENCE_REF",
                            path=(
                                f"/{collection_name}/{record_index}/"
                                f"evidence_refs/{ref_index}"
                            ),
                            message=(
                                f"Evidence reference {evidence_ref!r} was not supplied "
                                "to the Design Brief Agent."
                            ),
                        )
                    )

    provenance = document.get("provenance", {})
    if isinstance(provenance, dict):
        for index, evidence_ref in enumerate(
            provenance.get("selected_evidence_ids", [])
        ):
            if evidence_ref not in supplied_evidence:
                issues.append(
                    ValidationIssue(
                        code="UNKNOWN_EVIDENCE_REF",
                        path=f"/provenance/selected_evidence_ids/{index}",
                        message=(
                            f"Evidence reference {evidence_ref!r} was not supplied "
                            "to the Design Brief Agent."
                        ),
                    )
                )

    blockers: dict[str, dict[str, Any]] = {}
    for collection_name in ("missing_facts", "ambiguities", "unsupported_requests"):
        records = document.get(collection_name, [])
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict) and record.get("blocking") is True:
                record_id = record.get("id")
                if isinstance(record_id, str):
                    blockers[record_id] = record

    status = document.get("status")
    questions = document.get("clarification_questions", [])
    if isinstance(questions, list):
        for question_index, question in enumerate(questions):
            if not isinstance(question, dict):
                continue
            for target_index, target in enumerate(question.get("targets", [])):
                if target not in blockers:
                    issues.append(
                        ValidationIssue(
                            code="UNKNOWN_CLARIFICATION_TARGET",
                            path=(
                                f"/clarification_questions/{question_index}/"
                                f"targets/{target_index}"
                            ),
                            message=(
                                f"Clarification target {target!r} is not a blocking "
                                "missing fact, ambiguity, or unsupported request."
                            ),
                        )
                    )
        if status in {"draft_required", "blocked"} and questions:
            issues.append(
                ValidationIssue(
                    code="READINESS_CONFLICT",
                    path="/clarification_questions",
                    message=(
                        f"A {status} Design Brief must not include clarification "
                        "questions; use needs_clarification when user-answerable "
                        "blockers remain."
                    ),
                )
            )

    if status == "ready" and blockers:
        issues.append(
            ValidationIssue(
                code="READINESS_CONFLICT",
                path="/status",
                message="A ready Design Brief cannot contain blocking items.",
            )
        )
    if status == "needs_clarification" and not blockers:
        issues.append(
            ValidationIssue(
                code="READINESS_CONFLICT",
                path="/status",
                message=(
                    "A needs_clarification Design Brief must identify at least one "
                    "blocking item."
                ),
            )
        )
    if status in {"draft_required", "blocked"} and not blockers:
        issues.append(
            ValidationIssue(
                code="READINESS_CONFLICT",
                path="/status",
                message=f"A {status} Design Brief must identify a blocking item.",
                )
            )
    issues.extend(_validate_canonical_known_facts(document.get("known_facts")))
    return issues


def _validate_canonical_known_facts(known_facts: Any) -> list[ValidationIssue]:
    if not isinstance(known_facts, dict):
        return []
    storeys = known_facts.get("storeys")
    if not isinstance(storeys, list):
        return []

    issues: list[ValidationIssue] = []
    for storey_index, storey in enumerate(storeys):
        if not isinstance(storey, dict):
            continue
        for field in ("floor_thickness_mm", "floor_slabs"):
            if field in storey:
                issues.append(
                    ValidationIssue(
                        code="NON_CANONICAL_FLOOR_SLAB_LOCATION",
                        path=f"/known_facts/storeys/{storey_index}/{field}",
                        message=(
                            "Floor slabs must be records in "
                            "known_facts.floor_slabs with id, storey, "
                            "top_elevation_mm, and thickness_mm."
                        ),
                    )
                )

        centered_hosts: set[str] = set()
        for collection in ("doors", "windows"):
            records = storey.get(collection)
            if not isinstance(records, list):
                continue
            for record_index, record in enumerate(records):
                if not isinstance(record, dict):
                    continue
                host = record.get("host_wall")
                if record.get("alignment") != "host_centerline" or not isinstance(
                    host, str
                ):
                    continue
                if host in centered_hosts:
                    issues.append(
                        ValidationIssue(
                            code="AMBIGUOUS_HOST_CENTERLINE",
                            path=(
                                f"/known_facts/storeys/{storey_index}/"
                                f"{collection}/{record_index}/alignment"
                            ),
                            message=(
                                "Multiple openings cannot all use host_centerline "
                                f"on the same host wall {host!r}. Use distinct touching "
                                "wall segments or explicit center_global_mm positions."
                            ),
                        )
                    )
                else:
                    centered_hosts.add(host)
    return issues
