from pathlib import Path

from scripts.ifc_repair import run_phase9_live_uat


def test_phase9_uat_env_file_overrides_stale_process_provider_values(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("TEXT2IFC_PROVIDER", "mimo")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://stale.example.invalid")
    monkeypatch.setenv("API_KEY", "stale-secret")
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            (
                "TEXT2IFC_PROVIDER=deepseek",
                "OPENAI_BASE_URL=https://api.deepseek.com",
                "API_KEY=current-secret",
                "TEXT2IFC_DEEPSEEK_MODEL=deepseek-v4-flash",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    environment = run_phase9_live_uat._environment(env_file)

    assert environment["TEXT2IFC_PROVIDER"] == "deepseek"
    assert environment["OPENAI_BASE_URL"] == "https://api.deepseek.com"
    assert environment["API_KEY"] == "current-secret"
    assert environment["TEXT2IFC_DEEPSEEK_MODEL"] == "deepseek-v4-flash"
