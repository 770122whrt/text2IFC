import json

from scripts.ifc_repair import run_case


def test_config_check_loads_redacted_deepseek_env_file(
    tmp_path, capsys, monkeypatch
) -> None:
    for name in (
        "TEXT2IFC_PROVIDER",
        "DEEPSEEK_API_KEY",
        "OPENAI_BASE_URL",
        "TEXT2IFC_DEEPSEEK_MODEL",
        "TEXT2IFC_DEEPSEEK_MAX_TOKENS",
        "TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS",
    ):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            (
                "TEXT2IFC_PROVIDER=deepseek",
                "DEEPSEEK_API_KEY=secret-live-key",
                "OPENAI_BASE_URL=https://api.deepseek.com",
                "TEXT2IFC_DEEPSEEK_MODEL=deepseek-v4-flash",
                "TEXT2IFC_DEEPSEEK_MAX_TOKENS=65536",
                "TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS=65536",
            )
        ),
        encoding="utf-8",
    )

    exit_code = run_case.main(["--check-config", "--env-file", str(env_file)])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["configured"] is True
    assert payload["provider"] == "deepseek-openai-compatible"
    assert payload["model"] == "deepseek-v4-flash"
    assert payload["max_input_tokens"] == 65536
    assert payload["max_completion_tokens"] == 65536
    rendered = json.dumps(payload, ensure_ascii=False)
    assert "secret-live-key" not in rendered
    assert "api.deepseek.com" not in rendered
