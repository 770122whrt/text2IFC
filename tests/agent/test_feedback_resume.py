from __future__ import annotations

import json

from text2ifc_agent.interactive_cli_flow import _feedback_resume_state


def test_feedback_resume_state_starts_after_preserved_rounds(tmp_path):
    (tmp_path / "feedback-rounds.json").write_text(
        json.dumps(
            {
                "rounds": [
                    {"round_index": 0, "issues": [{"issue_id": "provider-failure"}]},
                    {
                        "round_index": 1,
                        "issues": [
                            {"issue_id": "schema-1"},
                            {"issue_id": "schema-2"},
                        ],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assert _feedback_resume_state(tmp_path) == (2, 2)


def test_feedback_resume_state_defaults_to_first_round(tmp_path):
    assert _feedback_resume_state(tmp_path) == (0, None)
