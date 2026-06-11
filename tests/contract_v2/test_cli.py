from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "scripts" / "bim_json_v2" / "validate.py"
MIGRATE = ROOT / "scripts" / "bim_json_v2" / "migrate_v1.py"
FORMAL = ROOT / "tests" / "contract_v2" / "fixtures" / "minimal.json"
V1 = ROOT / "tests" / "contract" / "fixtures" / "complete.json"


def run(*args):
    return subprocess.run(
        [sys.executable, *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_validation_cli_emits_stable_formal_success() -> None:
    result = run(VALIDATE, "formal", FORMAL)

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "document_kind": "formal",
        "errors": [],
        "valid": True,
    }


def test_validation_cli_rejects_oversized_input(tmp_path: Path) -> None:
    path = tmp_path / "large.json"
    path.write_bytes(b" " * (10 * 1024 * 1024 + 1))

    result = run(VALIDATE, "formal", path)

    assert result.returncode == 2
    assert json.loads(result.stdout)["errors"][0]["code"] == "FILE_TOO_LARGE"


def test_migration_cli_writes_draft_without_touching_source(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    source.write_bytes(V1.read_bytes())
    before = source.read_bytes()
    output = tmp_path / "output.json"

    result = run(MIGRATE, source, output)

    assert result.returncode == 0, result.stderr
    assert source.read_bytes() == before
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["draft_version"] == "bim-json-draft/1.0"
    assert json.loads(result.stdout)["output_path"] == str(output.resolve())
