import json
import subprocess
import sys
from pathlib import Path


def test_mimo_check_config_reads_export_style_env_file_without_echoing_values(
    tmp_path: Path,
):
    env_file = tmp_path / "mimo.env"
    env_file.write_text(
        "\n".join(
            [
                'export ANTHROPIC_AUTH_TOKEN="redacted-test-token-value"',
                'export ANTHROPIC_BASE_URL="https://example.invalid/anthropic"',
                "TEXT2IFC_MIMO_MODEL=mimo-v2.5-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/agent/run_mimo_smoke.py",
            "--check-config",
            "--env-file",
            str(env_file),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["configured"] is True
    assert payload["token_configured"] is True
    assert payload["base_url_configured"] is True
    assert payload["model"] == "mimo-v2.5-pro"
    assert "redacted-test-token-value" not in result.stdout
    assert "https://example.invalid/anthropic" not in result.stdout
