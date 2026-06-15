import subprocess
import sys
from pathlib import Path


def test_artifact_scan_passes_clean_tree(tmp_path: Path):
    (tmp_path / "report.md").write_text(
        "ANTHROPIC_AUTH_TOKEN may be configured in the environment.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/agent/scan_agent_artifacts.py",
            "--path",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert '"finding_count": 0' in result.stdout


def test_artifact_scan_fails_secret_like_content(tmp_path: Path):
    (tmp_path / "diagnostics.json").write_text(
        '{"authorization": "Bearer should-not-appear"}\n',
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/agent/scan_agent_artifacts.py",
            "--path",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "diagnostics.json" in result.stdout
    assert "SECRET_LIKE_PATTERN" in result.stdout

