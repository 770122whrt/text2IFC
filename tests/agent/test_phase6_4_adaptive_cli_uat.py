import json
import subprocess
import sys
from pathlib import Path

import pytest

from text2ifc_agent.adaptive_uat import (
    AdaptiveAnswerPolicy,
    LiveUATEvidenceError,
    build_live_uat_result,
    validate_live_uat_evidence,
)


ROOT = Path(__file__).resolve().parents[2]


def test_scripted_or_replay_evidence_cannot_be_final_live_acceptance():
    with pytest.raises(LiveUATEvidenceError, match="scripted"):
        validate_live_uat_evidence(
            {
                "provider": "deepseek-openai-compatible",
                "evidence_class": "live_deepseek",
                "interaction_mode": "scripted_stdin",
                "input_source": "scripted_stdin",
                "used_answers_json": False,
                "used_fake_or_replay_provider": False,
                "response_ids": ["resp_1"],
                "finish_reasons": ["stop"],
            }
        )
    with pytest.raises(LiveUATEvidenceError, match="answers.json"):
        validate_live_uat_evidence(
            {
                "provider": "deepseek-openai-compatible",
                "evidence_class": "live_deepseek",
                "interaction_mode": "adaptive_semantic_uat",
                "input_source": "adaptive_driver",
                "used_answers_json": True,
                "used_fake_or_replay_provider": False,
                "response_ids": ["resp_1"],
                "finish_reasons": ["stop"],
            }
        )
    with pytest.raises(LiveUATEvidenceError, match="fake"):
        validate_live_uat_evidence(
            {
                "provider": "deepseek-openai-compatible",
                "evidence_class": "live_deepseek",
                "interaction_mode": "adaptive_semantic_uat",
                "input_source": "adaptive_driver",
                "used_answers_json": False,
                "used_fake_or_replay_provider": True,
                "response_ids": ["resp_1"],
                "finish_reasons": ["stop"],
            }
        )


def test_adaptive_answer_policy_uses_intents_not_exact_question_text():
    policy = AdaptiveAnswerPolicy(
        answers_by_intent={
            "height": "房间净高为 3000 mm。",
            "wall_thickness": "墙厚为 200 mm。",
            "slab_thickness": "地板厚度为 150 mm。",
            "door_host": "门放在南墙中央。",
            "door_dimensions": "门宽 900 mm，高 2100 mm。",
            "window_dimensions": "窗宽 1200 mm，高 1000 mm，窗台高 900 mm。",
            "unknown": "这个信息暂时不知道。",
        }
    )

    questions = [
        "请给出竖向净尺寸，也就是空间从地面到顶部的尺寸。",
        "How thick should the walls be?",
        "楼板或地坪板需要多厚？",
        "入口开在哪一侧墙上？",
        "请确认这个门洞的宽和高。",
        "窗的宽高以及窗台离地是多少？",
        "请选择一种立面风格。",
    ]

    answers = [policy.answer_question(question).intent for question in questions]

    assert answers == [
        "height",
        "wall_thickness",
        "slab_thickness",
        "door_host",
        "door_dimensions",
        "window_dimensions",
        "unknown",
    ]


def test_build_live_uat_result_labels_deepseek_and_redacts_config(tmp_path):
    result = build_live_uat_result(
        provider="deepseek-openai-compatible",
        model="deepseek-v4-flash",
        response_ids=["resp_design", "resp_generator"],
        finish_reasons=["stop", "stop"],
        usage=[{"prompt_tokens": 1, "completion_tokens": 2}],
        interaction_mode="adaptive_semantic_uat",
        input_source="adaptive_driver",
        used_answers_json=False,
        used_fake_or_replay_provider=False,
        artifacts={"session_export": "runs/abc/session-export.json"},
    )
    path = tmp_path / "live-uat-result.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["evidence_class"] == "live_deepseek"
    assert payload["provider"] == "deepseek-openai-compatible"
    assert payload["response_ids"] == ["resp_design", "resp_generator"]
    assert payload["config"]["api_key"] == "[REDACTED]"
    assert payload["config"]["base_url"] == "[REDACTED]"


def test_phase6_4_live_deepseek_script_config_check_writes_redacted_result(tmp_path):
    output_root = tmp_path / "phase6.4-live"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "agent" / "run_phase6_4_live_deepseek.py"),
            "--check-config",
            "--output-root",
            str(output_root),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "text2ifc/phase6.4-live-uat/1.0"
    assert payload["mode"] == "check_config"
    assert payload["config"]["api_key"] == "[REDACTED]"
    assert payload["config"]["base_url"] == "[REDACTED]"
    assert (output_root / "live-uat-result.json").is_file()
