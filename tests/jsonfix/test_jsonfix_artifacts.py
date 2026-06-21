from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from text2ifc_jsonfix.demo import run_missing_piece_demo


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.artifact_audit")
    except ModuleNotFoundError as exc:
        pytest.fail(f"jsonfix artifact audit is not implemented: {exc}")
    return module.audit_jsonfix_artifacts


def test_clean_demo_artifacts_have_no_secrets_or_silent_overwrites(
    tmp_path: Path,
) -> None:
    audit_jsonfix_artifacts = _api()
    run_missing_piece_demo(output_dir=tmp_path, inventory_roots=[])

    result = audit_jsonfix_artifacts(tmp_path)

    assert result["success"]
    assert result["secret_finding_count"] == 0
    assert result["silent_overwrite_count"] == 0
    assert result["missing_required_artifact_count"] == 0
    assert result["findings"] == []


def test_unreported_changed_previous_value_fails_artifact_audit(
    tmp_path: Path,
) -> None:
    audit_jsonfix_artifacts = _api()
    run_missing_piece_demo(output_dir=tmp_path, inventory_roots=[])
    provenance_path = tmp_path / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    patch_fact = next(
        fact for fact in provenance["facts"] if fact["origin"] == "patch"
    )
    patch_fact["previous_value"] = {"Name": "source-value"}
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False),
        encoding="utf-8",
    )

    result = audit_jsonfix_artifacts(tmp_path)

    assert not result["success"]
    assert result["silent_overwrite_count"] == 1
    assert result["findings"][0]["code"] == "UNDECLARED_SOURCE_OVERWRITE"


def test_secret_like_text_fails_jsonfix_artifact_audit(tmp_path: Path) -> None:
    audit_jsonfix_artifacts = _api()
    run_missing_piece_demo(output_dir=tmp_path, inventory_roots=[])
    (tmp_path / "report.md").write_text(
        "authorization: tp-this-value-must-never-persist\n",
        encoding="utf-8",
    )

    result = audit_jsonfix_artifacts(tmp_path)

    assert not result["success"]
    assert result["secret_finding_count"] >= 1
