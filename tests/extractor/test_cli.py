from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from text2ifc_contract.draft import validate_draft

from .conftest import HXP, ROOT


SCRIPT = ROOT / "scripts" / "ifc_pipeline_v2" / "extract.py"
IFC4 = (
    ROOT
    / "dataset"
    / "external"
    / "buildingsmart-official"
    / "ifc4"
    / "iso-reference-view"
    / "wall-with-opening-and-window.ifc"
)


def test_extraction_cli_writes_atomic_valid_draft(tmp_path: Path) -> None:
    output = tmp_path / "hxp.json"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(HXP), str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    value = json.loads(output.read_text(encoding="utf-8"))
    assert validate_draft(value) == []
    summary = json.loads(completed.stdout)
    assert summary["document_kind"] == "draft"
    assert summary["source_sha256"]


def test_extraction_cli_preserves_destination_on_schema_failure(
    tmp_path: Path,
) -> None:
    output = tmp_path / "sentinel.json"
    output.write_text("sentinel", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(IFC4), str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert output.read_text(encoding="utf-8") == "sentinel"
    assert completed.stdout
    assert json.loads(completed.stdout)["error"]["code"] == "UNSUPPORTED_SCHEMA"
