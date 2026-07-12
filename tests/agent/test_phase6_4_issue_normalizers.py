import json

import pytest

from text2ifc_agent.issues import validate_issue_dict
from text2ifc_agent.issue_normalizers import (
    normalize_audit_findings,
    normalize_compiler_result,
    normalize_generator_draft_issues,
    normalize_gate_sidecars,
    normalize_provider_failure,
    normalize_reopen_result,
    normalize_runtime_exception,
    normalize_validation_issues,
    write_terminal_issues,
)


def _assert_valid(issue, *, source, owner, issue_type, route):
    payload = issue.to_dict()
    validate_issue_dict(payload)
    assert payload["source"] == source
    assert payload["owner"] == owner
    assert payload["issue_type"] == issue_type
    assert payload["suggested_route"] == route
    return payload


def test_normalizes_schema_and_semantic_validation_issues():
    issues = normalize_validation_issues(
        [
            {
                "code": "REQUIRED_PROPERTY_MISSING",
                "path": "/entities/0/attributes/ObjectPlacement",
                "message": "ObjectPlacement is required.",
            },
            {
                "code": "UNSUPPORTED_FACT",
                "path": "/known_facts/window/opening_style",
                "message": "Requested fact is outside the BIM JSON supported scope.",
            },
        ],
        source="schema_validation",
    )

    first = _assert_valid(
        issues[0],
        source="schema_validation",
        owner="repair",
        issue_type="schema_mismatch",
        route="repair_json",
    )
    second = _assert_valid(
        issues[1],
        source="schema_validation",
        owner="schema",
        issue_type="unsupported_schema_capability",
        route="blocked_as_unsupported",
    )
    assert first["actual_ref"] == "/entities/0/attributes/ObjectPlacement"
    assert second["retryable"] is False


def test_normalizes_draft_unresolved_paths_as_user_owned_ask_user():
    issues = normalize_validation_issues(
        [
            {
                "code": "DRAFT_REQUIRED_FACT_MISSING",
                "path": "/required_facts/0",
                "message": "Wall thickness is unresolved.",
            }
        ],
        source="semantic_validation",
    )

    payload = _assert_valid(
        issues[0],
        source="semantic_validation",
        owner="user",
        issue_type="draft_unresolved_path",
        route="ask_user",
    )
    assert payload["retryable"] is True


def test_normalizes_generator_draft_missing_entities_as_generator_regeneration():
    issues = normalize_generator_draft_issues(
        {
            "missing_facts": [
                {
                    "code": "MISSING_ENTITIES",
                    "path": "/entities",
                    "message": (
                        "All remaining walls, spaces, slabs, stair, doors, windows, "
                        "openings, and relationships are omitted due to manual generation "
                        "limitations. The Design Brief contains complete facts for automatic generation."
                    ),
                }
            ]
        }
    )

    payload = _assert_valid(
        issues[0],
        source="semantic_validation",
        owner="generator",
        issue_type="missing_entity",
        route="regenerate_json",
    )
    assert payload["retryable"] is True


def test_normalizes_generator_draft_user_fact_gaps_as_ask_user():
    issues = normalize_generator_draft_issues(
        {
            "missing_facts": [
                {
                    "code": "REQUIRED_USER_FACT_MISSING",
                    "path": "/known_facts/walls/thickness",
                    "message": "Wall thickness is missing from the user request.",
                }
            ]
        }
    )

    _assert_valid(
        issues[0],
        source="semantic_validation",
        owner="user",
        issue_type="missing_required_fact",
        route="ask_user",
    )


def test_normalizes_unresolved_model_references_as_generator_regeneration():
    issues = normalize_validation_issues(
        [
            {
                "code": "UNRESOLVED_PLACEMENT_PARENT",
                "path": "/entities/10/attributes/ObjectPlacement/relative_to",
                "message": "Placement parent 'wall-a' is not declared.",
            },
            {
                "code": "UNRESOLVED_RELATIONSHIP_ENDPOINT",
                "path": "/relationships/1/attributes/RelatingBuildingElement",
                "message": "Relationship endpoint 'wall-a' is not declared.",
            },
        ],
        source="schema_validation",
    )

    for issue in issues:
        _assert_valid(
            issue,
            source="schema_validation",
            owner="generator",
            issue_type="missing_relationship",
            route="regenerate_json",
        )


def test_normalizes_compiler_errors_and_unsupported_features():
    unsupported = normalize_compiler_result(
        {
            "success": False,
            "error_type": "UnsupportedFeatureError",
            "message": "IfcStair is not supported by the current compiler.",
        }
    )
    error = normalize_compiler_result(
        {
            "success": False,
            "error_type": "ValueError",
            "message": "Cannot compile malformed placement.",
        }
    )

    _assert_valid(
        unsupported[0],
        source="compiler",
        owner="compiler",
        issue_type="compiler_unsupported_feature",
        route="blocked_as_unsupported",
    )
    _assert_valid(
        error[0],
        source="compiler",
        owner="compiler",
        issue_type="compile_error",
        route="runtime_blocked",
    )


def test_normalizes_reopen_failure():
    issues = normalize_reopen_result(
        {"success": False, "ifc_issues": [{"code": "REOPEN_FAILED", "message": "Cannot reopen IFC."}]}
    )

    _assert_valid(
        issues[0],
        source="reopen_check",
        owner="compiler",
        issue_type="reopen_error",
        route="runtime_blocked",
    )


def test_normalizes_geometry_and_gate_sidecars(tmp_path):
    root = tmp_path / "case"
    root.mkdir()
    (root / "geometry-feedback.json").write_text(
        json.dumps(
            {
                "success": False,
                "issues": [
                    {
                        "code": "ROOM_ENCLOSURE_OPEN",
                        "path": "/spaces/space-1",
                        "message": "Room enclosure is open.",
                        "expected": {"closed": True},
                        "actual": {"closed": False},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (root / "gate-summary.json").write_text(
        json.dumps(
            {
                "overall_status": "failed",
                "gates": [
                    {
                        "name": "dynamic_expected_entities",
                        "status": "failed",
                        "issue_codes": ["EXPECTED_ENTITY_MISSING"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    issues = normalize_gate_sidecars(root)

    _assert_valid(
        issues[0],
        source="geometry_gate",
        owner="gate",
        issue_type="geometry_invalid",
        route="regenerate_json",
    )
    assert '"expected": {"closed": true}' in issues[0].evidence
    assert '"actual": {"closed": false}' in issues[0].evidence
    _assert_valid(
        issues[1],
        source="deterministic_gate",
        owner="generator",
        issue_type="missing_entity",
        route="regenerate_json",
    )


def test_dynamic_gate_feedback_preserves_entity_level_geometry_evidence(tmp_path):
    root = tmp_path / "case"
    root.mkdir()
    (root / "gate-summary.json").write_text(
        json.dumps(
            {
                "overall_status": "failed",
                "gates": [
                    {
                        "name": "dynamic_opening_fill",
                        "status": "failed",
                        "issue_codes": ["OPENING_HOST_LOCAL_BOUNDS_MISMATCH"],
                        "issues": [
                            {
                                "code": "OPENING_HOST_LOCAL_BOUNDS_MISMATCH",
                                "path": "/entities/opening-1/attributes/ObjectPlacement/origin",
                                "element_id": "door-1",
                                "opening_id": "opening-1",
                                "host_wall": "wall-1",
                                "opening_origin": [0, 0, 0],
                                "host_profile": {"x": 4000, "y": 200},
                                "opening_profile": {"x": 900, "y": 2100},
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    issues = normalize_gate_sidecars(root)

    assert len(issues) == 1
    _assert_valid(
        issues[0],
        source="deterministic_gate",
        owner="generator",
        issue_type="geometry_invalid",
        route="regenerate_json",
    )
    assert issues[0].actual_ref == "/entities/opening-1/attributes/ObjectPlacement/origin"
    assert "opening-1" in issues[0].evidence
    assert "wall-1" in issues[0].evidence
    assert "opening_profile" in issues[0].evidence


def test_normalizes_audit_findings_to_owners_and_routes():
    issues = normalize_audit_findings(
        {
            "recommendation": "revise",
            "blocking": True,
            "findings": [
                {
                    "code": "DESIGN_BRIEF_CHANGED_ORIGINAL_REQUEST",
                    "severity": "blocking",
                    "message": "Design Brief changed the original request.",
                },
                {
                    "code": "EXPECTED_STAIR_MISSING",
                    "severity": "blocking",
                    "message": "The stair requested by the user is absent.",
                },
                {
                    "code": "OPENING_FILLING_ORIENTATION_MISMATCH",
                    "severity": "blocking",
                    "message": "A filling element is not aligned with its opening.",
                },
            ],
        }
    )

    _assert_valid(
        issues[0],
        source="audit",
        owner="design_brief",
        issue_type="changed_original_request",
        route="revise_design_brief",
    )
    _assert_valid(
        issues[1],
        source="audit",
        owner="generator",
        issue_type="missing_vertical_connection",
        route="regenerate_json",
    )
    _assert_valid(
        issues[2],
        source="audit",
        owner="generator",
        issue_type="geometry_invalid",
        route="regenerate_json",
    )


def test_audit_space_placement_details_route_to_generator():
    issues = normalize_audit_findings(
        {
            "recommendation": "revise",
            "blocking": True,
            "findings": [
                {
                    "code": "SPACE_PLACEMENT_MISMATCH",
                    "severity": "error",
                    "message": "Space placement does not match expected bounds.",
                    "details": [
                        {
                            "space_id": "space-storey-1-living-room",
                            "expected_bbox": "x=0..4000,y=0..4000",
                            "actual_bbox_global": "x=2000..6000,y=2000..6000",
                        }
                    ],
                }
            ],
        }
    )

    assert len(issues) == 1
    _assert_valid(
        issues[0],
        source="audit",
        owner="generator",
        issue_type="geometry_invalid",
        route="regenerate_json",
    )
    assert "space-storey-1-living-room" in issues[0].evidence
    assert "expected_bbox" in issues[0].evidence
    assert "actual_bbox_global" in issues[0].evidence


def test_normalizes_provider_failures_without_leaking_request_details():
    truncation = normalize_provider_failure(
        {
            "failure_class": "truncated",
            "provider": "deepseek-openai-compatible",
            "details": {
                "request": {"messages": [{"content": "secret-bearing prompt should not appear"}]},
                "finish_reason": "length",
            },
        },
        stage="generator",
    )
    malformed = normalize_provider_failure(
        {
            "failure_class": "missing_choice",
            "provider": "deepseek-openai-compatible",
        },
        stage="audit",
    )

    first = _assert_valid(
        truncation[0],
        source="provider",
        owner="provider",
        issue_type="provider_truncation",
        route="provider_retry",
    )
    second = _assert_valid(
        malformed[0],
        source="provider",
        owner="provider",
        issue_type="provider_format_error",
        route="provider_retry",
    )
    assert "secret-bearing" not in first["evidence"]
    assert second["actual_ref"] == "audit/provider-error.json"


def test_normalizes_runtime_exception():
    issues = normalize_runtime_exception(RuntimeError("boom"), stage="final")

    payload = _assert_valid(
        issues[0],
        source="runtime",
        owner="runtime",
        issue_type="runtime_error",
        route="runtime_blocked",
    )
    assert payload["retryable"] is False


def test_write_terminal_issues_persists_normalized_artifact(tmp_path):
    issues = normalize_runtime_exception(RuntimeError("boom"), stage="final")

    path = write_terminal_issues(tmp_path, issues)

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "text2ifc/issues/1.0"
    assert payload["issues"][0]["issue_type"] == "runtime_error"
