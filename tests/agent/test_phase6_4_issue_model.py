import json

import pytest

from text2ifc_agent.issues import (
    Issue,
    IssueValidationError,
    assert_machine_control_language,
    validate_issue_dict,
    write_issues,
)


def test_issue_serializes_required_fields_and_optional_chinese_message(tmp_path):
    issue = Issue(
        issue_id="issue_0001",
        source="audit",
        severity="blocking",
        owner="generator",
        issue_type="missing_entity",
        expected_fact_ref="expected_facts.storeys[1].vertical_connections.stair",
        actual_ref="candidate_bim_json.entities",
        evidence=(
            "The user requested a stair between storeys, but no IfcStair "
            "or stair-like element exists in the candidate."
        ),
        suggested_route="regenerate_json",
        retryable=True,
        message_zh="\u7f3a\u5c11\u697c\u68af\u5b9e\u4f53\u3002",
    )

    payload = issue.to_dict()
    validate_issue_dict(payload)

    assert payload["source"] == "audit"
    assert payload["severity"] == "blocking"
    assert payload["owner"] == "generator"
    assert payload["issue_type"] == "missing_entity"
    assert payload["suggested_route"] == "regenerate_json"
    assert payload["message_zh"] == "\u7f3a\u5c11\u697c\u68af\u5b9e\u4f53\u3002"

    path = write_issues(tmp_path / "issues.json", [issue])
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["schema_version"] == "text2ifc/issues/1.0"
    assert written["issues"][0]["issue_id"] == "issue_0001"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source", "validator"),
        ("severity", "critical"),
        ("owner", "model"),
        ("issue_type", "missing_wall_magic"),
        ("suggested_route", "rerun_everything"),
    ],
)
def test_issue_rejects_unknown_enum_values(field, value):
    payload = {
        "issue_id": "issue_0001",
        "source": "audit",
        "severity": "blocking",
        "owner": "generator",
        "issue_type": "missing_entity",
        "expected_fact_ref": None,
        "actual_ref": None,
        "evidence": "evidence",
        "suggested_route": "regenerate_json",
        "retryable": True,
    }
    payload[field] = value

    with pytest.raises(IssueValidationError, match=field):
        validate_issue_dict(payload)


def test_machine_control_language_rejects_chinese_keys_and_control_values():
    with pytest.raises(IssueValidationError, match="control key"):
        assert_machine_control_language(
            {
                "\u95ee\u9898\u7c7b\u578b": "missing_entity",
                "raw_user_input": "\u5efa\u4e00\u4e2a\u623f\u95f4",
            }
        )

    with pytest.raises(IssueValidationError, match="control value"):
        assert_machine_control_language(
            {
                "issue_type": "\u7f3a\u5c11\u5b9e\u4f53",
                "message_zh": "\u8fd9\u662f\u5141\u8bb8\u7684\u4e2d\u6587\u8bf4\u660e",
            }
        )


def test_machine_control_language_allows_raw_user_input_and_message_zh():
    assert_machine_control_language(
        {
            "issue_type": "missing_entity",
            "suggested_route": "regenerate_json",
            "raw_user_input": "\u521b\u5efa\u4e00\u4e2a\u623f\u95f4",
            "message_zh": "\u4eba\u5de5\u9605\u8bfb\u8bf4\u660e",
            "transcript": [
                {"role": "user", "content": "\u5899\u539a\u4e3a300mm"}
            ],
        }
    )
