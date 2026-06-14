from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from text2ifc_text.baseline import FakeProvider

from scripts.text2json.run_e2e_demo import run_demo, select_spatial_sample


PAIRS = Path("dataset/processed/text2json/pairs")


def _target(record: dict[str, Any]) -> dict[str, Any]:
    return json.loads(Path(record["target_json_path"]).read_text(encoding="utf-8"))


def _provider(record: dict[str, Any], payload: dict[str, Any] | str) -> FakeProvider:
    text = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    return FakeProvider({record["record_id"]: {"text": text, "metadata": {"mode": "test"}}})


def test_check_selects_one_formal_spatial_validation_or_test_sample() -> None:
    record = select_spatial_sample(PAIRS)

    assert record["target_kind"] == "formal"
    assert record["text_style"] == "spatial"
    assert record["split"] in {"validation", "test"}
    assert Path(record["target_json_path"]).is_file()


def test_check_writes_complete_demo_artifacts(tmp_path: Path) -> None:
    result = run_demo(output_dir=tmp_path, check=True)

    assert result["success"] is True
    assert result["sample"]["text_style"] == "spatial"
    for relative in (
        "input.txt",
        "prediction.json",
        "diagnostics.json",
        "output.ifc",
        "metrics.json",
        "report.md",
    ):
        assert (tmp_path / relative).is_file()
    diagnostics = json.loads((tmp_path / "diagnostics.json").read_text(encoding="utf-8"))
    assert diagnostics["compiled_ifc"]["success"] is True
    assert diagnostics["validation"]["issues"] == []


def test_invalid_prediction_fails_without_compiling_ifc(tmp_path: Path) -> None:
    record = select_spatial_sample(PAIRS)

    result = run_demo(
        output_dir=tmp_path,
        check=True,
        provider=_provider(record, "{"),
        sample=record,
    )

    assert result["success"] is False
    assert (tmp_path / "diagnostics.json").is_file()
    assert not (tmp_path / "output.ifc").exists()
    diagnostics = json.loads((tmp_path / "diagnostics.json").read_text(encoding="utf-8"))
    assert diagnostics["validation"]["stage"] == "parse"


def test_draft_or_missing_required_prediction_fails_without_defaulting(
    tmp_path: Path,
) -> None:
    record = select_spatial_sample(PAIRS)
    target = _target(record)
    draft = {
        "draft_version": "bim-json-draft/1.0",
        "partial_document": target,
        "missing_required": [{"path": "/entities/0/attributes/ObjectPlacement"}],
        "unsupported_items": [],
        "provenance": {"source": "test"},
    }
    missing_required = copy.deepcopy(target)
    del missing_required["units"]

    for name, payload in {"draft": draft, "missing": missing_required}.items():
        output_dir = tmp_path / name
        result = run_demo(
            output_dir=output_dir,
            check=True,
            provider=_provider(record, payload),
            sample=record,
        )

        assert result["success"] is False
        assert not (output_dir / "output.ifc").exists()
        diagnostics = json.loads(
            (output_dir / "diagnostics.json").read_text(encoding="utf-8")
        )
        assert diagnostics["compiled_ifc"]["attempted"] is False


def test_report_includes_reproduction_commands(tmp_path: Path) -> None:
    result = run_demo(output_dir=tmp_path, check=True)

    assert result["success"] is True
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "python scripts/text2json/run_e2e_demo.py --check" in report
    assert "python scripts/text2json/run_baseline.py --provider fake --split validation --evaluate" in report
    assert "python scripts/text2json/evaluate.py --check-fixtures" in report
