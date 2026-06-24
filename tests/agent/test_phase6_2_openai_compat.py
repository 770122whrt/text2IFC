import json
from pathlib import Path

import pytest

from text2ifc_agent.openai_compat import (
    OpenAICompatError,
    build_compatibility_report,
    load_openai_compatible_config,
    normalize_openai_base_url,
    parse_chat_completion_evidence,
)


def test_openai_compatible_config_accepts_api_key_without_leaking_values():
    config = load_openai_compatible_config(
        {
            "API_KEY": "secret-api-key",
            "OpenAI_BASE_URL": "https://api.xiaomimimo.com",
            "TEXT2IFC_MIMO_MODEL": "mimo-v2.5-pro",
        }
    )
    rendered = json.dumps(config, sort_keys=True)

    assert config["configured"] is True
    assert config["api_key_env"] == "API_KEY"
    assert config["base_url_configured"] is True
    assert config["model"] == "mimo-v2.5-pro"
    assert config["missing"] == []
    assert "secret-api-key" not in rendered
    assert "api.xiaomimimo.com" not in rendered


def test_openai_compatible_config_reports_missing_names_only():
    config = load_openai_compatible_config({})
    rendered = json.dumps(config, sort_keys=True)

    assert config["configured"] is False
    assert "API_KEY or MIMO_API_KEY or OPENAI_API_KEY" in rendered
    assert "OpenAI_BASE_URL or OPENAI_BASE_URL" in rendered
    assert "TEXT2IFC_MIMO_MODEL" in rendered
    assert "Bearer" not in rendered
    assert "https://" not in rendered


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("https://api.xiaomimimo.com", "https://api.xiaomimimo.com/v1"),
        ("https://api.xiaomimimo.com/", "https://api.xiaomimimo.com/v1"),
        ("https://api.xiaomimimo.com/v1", "https://api.xiaomimimo.com/v1"),
        ("https://api.xiaomimimo.com/v1/", "https://api.xiaomimimo.com/v1"),
    ],
)
def test_normalize_openai_base_url_targets_v1(raw, expected):
    assert normalize_openai_base_url(raw) == expected


def test_parse_chat_completion_evidence_preserves_required_metadata():
    response = {
        "id": "chatcmpl-live-001",
        "object": "chat.completion",
        "model": "mimo-v2.5-pro",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": '{"ok": true}'},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 3, "total_tokens": 13},
    }

    evidence = parse_chat_completion_evidence(
        response,
        request={
            "model": "mimo-v2.5-pro",
            "messages": [{"role": "user", "content": "hello"}],
            "max_completion_tokens": 1024,
        },
        evidence_class="sdk_smoke",
    )

    assert evidence["provider"] == "mimo-openai-compatible"
    assert evidence["evidence_class"] == "sdk_smoke"
    assert evidence["response_id"] == "chatcmpl-live-001"
    assert evidence["model"] == "mimo-v2.5-pro"
    assert evidence["finish_reason"] == "stop"
    assert evidence["parse_eligible"] is True
    assert evidence["content_text"] == '{"ok": true}'
    assert evidence["usage"] == {
        "prompt_tokens": 10,
        "completion_tokens": 3,
        "total_tokens": 13,
    }
    assert evidence["request"]["max_completion_tokens"] == 1024
    assert "hello" in json.dumps(evidence["request"], sort_keys=True)


def test_parse_chat_completion_blocks_length_finish_reason():
    response = {
        "id": "chatcmpl-length-001",
        "object": "chat.completion",
        "model": "mimo-v2.5-pro",
        "choices": [
            {
                "index": 0,
                "finish_reason": "length",
                "message": {"role": "assistant", "content": '{"ok":'},
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
    }

    with pytest.raises(OpenAICompatError, match="finish_reason=length") as captured:
        parse_chat_completion_evidence(
            response,
            request={"model": "mimo-v2.5-pro", "messages": []},
            evidence_class="sdk_smoke",
        )

    assert captured.value.evidence["parse_eligible"] is False
    assert captured.value.evidence["failure_class"] == "truncated"
    assert captured.value.evidence["response_id"] == "chatcmpl-length-001"


def test_compatibility_report_shape_records_decision_and_evidence_classes():
    report = build_compatibility_report(
        openai_sdk={
            "status": "passed",
            "evidence_class": "sdk_smoke",
            "response_id": "chatcmpl-live-001",
        },
        agents_sdk={
            "status": "limited",
            "evidence_class": "sdk_smoke",
            "metadata_gaps": ["finish_reason_not_first_class"],
        },
        responses_api={
            "status": "unavailable",
            "http_status": 404,
            "evidence_class": "sdk_smoke",
        },
    )
    rendered = json.dumps(report, sort_keys=True)

    assert report["phase"] == "6.2"
    assert report["decision"] == "limited_sdk"
    assert report["implementation_route"] == "native_orchestrator_with_openai_sdk_provider"
    assert report["openai_sdk"]["evidence_class"] == "sdk_smoke"
    assert report["agents_sdk"]["metadata_gaps"] == ["finish_reason_not_first_class"]
    assert report["responses_api"]["http_status"] == 404
    assert "secret" not in rendered.lower()


def test_phase6_2_check_openai_compat_cli_writes_report(tmp_path, capsys):
    from scripts.agent import run_phase6_2_cli

    def fake_runner(config):
        assert config["configured"] is True
        return build_compatibility_report(
            openai_sdk={
                "status": "passed",
                "evidence_class": "sdk_smoke",
                "response_id": "chatcmpl-live-001",
            },
            agents_sdk={
                "status": "limited",
                "evidence_class": "sdk_smoke",
                "metadata_gaps": ["finish_reason_not_first_class"],
            },
            responses_api={
                "status": "unavailable",
                "http_status": 404,
                "evidence_class": "sdk_smoke",
            },
        )

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "API_KEY=secret-api-key",
                "OpenAI_BASE_URL=https://api.xiaomimimo.com",
                "TEXT2IFC_MIMO_MODEL=mimo-v2.5-pro",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = run_phase6_2_cli.main(
        [
            "--check-openai-compat",
            "--env-file",
            str(env_file),
            "--output-dir",
            str(tmp_path),
        ],
        compatibility_runner=fake_runner,
    )

    stdout = capsys.readouterr().out
    report_path = tmp_path / "compatibility-report.json"
    markdown_path = tmp_path / "report.md"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert report["decision"] == "limited_sdk"
    assert report["implementation_route"] == "native_orchestrator_with_openai_sdk_provider"
    assert markdown_path.exists()
    assert "limited_sdk" in markdown_path.read_text(encoding="utf-8")
    assert "secret-api-key" not in stdout
    assert "api.xiaomimimo.com" not in stdout
    assert "secret-api-key" not in report_path.read_text(encoding="utf-8")
    assert "secret-api-key" not in markdown_path.read_text(encoding="utf-8")


def test_phase6_2_check_openai_compat_cli_missing_config_is_safe(
    monkeypatch, tmp_path, capsys
):
    from scripts.agent import run_phase6_2_cli

    for name in (
        "API_KEY",
        "MIMO_API_KEY",
        "OPENAI_API_KEY",
        "OpenAI_BASE_URL",
        "OPENAI_BASE_URL",
        "TEXT2IFC_MIMO_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    exit_code = run_phase6_2_cli.main(
        [
            "--check-openai-compat",
            "--env-file",
            str(Path(tmp_path) / "missing.env"),
            "--output-dir",
            str(tmp_path),
        ]
    )

    stdout = capsys.readouterr().out
    report = json.loads((tmp_path / "compatibility-report.json").read_text(encoding="utf-8"))
    assert exit_code == 2
    assert report["decision"] == "blocked"
    assert report["blocker"] == "missing_openai_compatible_config"
    assert "API_KEY or MIMO_API_KEY or OPENAI_API_KEY" in stdout
    assert "https://" not in stdout
