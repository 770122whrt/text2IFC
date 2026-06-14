from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from text2ifc_contract.validation_v2 import validate_v2_document
from text2ifc_text.baseline import (
    FakeProvider,
    load_prompt_contract,
    run_baseline_records,
)


FIXTURE = Path("tests/contract_v2/fixtures/complete.json")
PROMPT = Path("prompts/text2json/structured-output-v1.md")


def _document() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _pair(tmp_path: Path, *, target_kind: str = "formal") -> dict[str, Any]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    target_path = tmp_path / "gold.json"
    target_path.write_text(json.dumps(_document(), sort_keys=True), encoding="utf-8")
    return {
        "record_id": "fixture-record",
        "split": "validation",
        "source_file_id": "fixture-ifc",
        "scene_family": "fixture",
        "target_kind": target_kind,
        "target_json_path": str(target_path),
        "input_text": "Create the fixture building as BIM JSON 2.0.",
        "target_sha256": "fixture-sha",
    }


def _provider(value: dict[str, Any] | str, **metadata: Any) -> FakeProvider:
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    return FakeProvider({"fixture-record": {"text": text, "metadata": metadata}})


def test_prompt_contract_forbids_raw_ifc_and_low_level_entities() -> None:
    prompt = load_prompt_contract(PROMPT)

    assert 'schema_version: "bim-json/2.0"' in prompt
    assert 'ifc_schema: "IFC2X3"' in prompt
    for forbidden in (
        "raw IFC",
        "STEP text",
        ".ifc files",
        "IfcCartesianPoint",
        "IfcDirection",
        "IfcOwnerHistory",
    ):
        assert forbidden in prompt


def test_valid_formal_prediction_is_accepted_and_written(tmp_path: Path) -> None:
    gold = _document()

    result = run_baseline_records(
        [_pair(tmp_path)],
        provider=_provider(gold, provider="fake"),
        output_dir=tmp_path / "baseline",
        prompt_path=PROMPT,
    )

    record = result["records"]["fixture-record"]
    parsed_path = Path(record["parsed_prediction_path"])
    assert result["accepted_count"] == 1
    assert record["status"] == "accepted"
    assert parsed_path.is_file()
    assert validate_v2_document(json.loads(parsed_path.read_text(encoding="utf-8"))) == []


def test_invalid_outputs_are_rejected_with_raw_response_retained(
    tmp_path: Path,
) -> None:
    gold = _document()
    schema_invalid = copy.deepcopy(gold)
    del schema_invalid["ifc_schema"]
    semantic_invalid = copy.deepcopy(gold)
    semantic_invalid["entities"][4]["ifc_class"] = "IfcBuildingElementProxy"
    draft = {
        "draft_version": "bim-json-draft/1.0",
        "partial_document": gold,
        "missing_required": [],
        "unsupported_items": [],
        "provenance": {"source": "fixture"},
    }

    cases = {
        "invalid-json": ("{", "parse_error"),
        "schema-invalid": (schema_invalid, "schema_error"),
        "semantic-invalid": (semantic_invalid, "semantic_error"),
        "draft": (draft, "draft_rejected"),
    }
    for name, (payload, expected_status) in cases.items():
        pair = _pair(tmp_path / name)
        pair["record_id"] = name
        provider = FakeProvider(
            {
                name: {
                    "text": payload
                    if isinstance(payload, str)
                    else json.dumps(payload, sort_keys=True),
                    "metadata": {"provider": "fake", "case": name},
                }
            }
        )

        result = run_baseline_records(
            [pair],
            provider=provider,
            output_dir=tmp_path / "baseline" / name,
            prompt_path=PROMPT,
        )

        record = result["records"][name]
        assert result["accepted_count"] == 0
        assert record["status"] == expected_status
        assert Path(record["raw_response_path"]).is_file()
        assert "parsed_prediction_path" not in record
        assert record["diagnostics"]


def test_raw_provider_metadata_is_written_separately(tmp_path: Path) -> None:
    result = run_baseline_records(
        [_pair(tmp_path)],
        provider=_provider(_document(), provider="fake", token_count=12),
        output_dir=tmp_path / "baseline",
        prompt_path=PROMPT,
    )

    record = result["records"]["fixture-record"]
    raw_text = Path(record["raw_response_path"]).read_text(encoding="utf-8")
    metadata = json.loads(Path(record["raw_metadata_path"]).read_text(encoding="utf-8"))

    assert "token_count" not in raw_text
    assert metadata["provider_metadata"]["token_count"] == 12
    assert metadata["record_id"] == "fixture-record"


def test_baseline_can_evaluate_written_predictions(tmp_path: Path) -> None:
    result = run_baseline_records(
        [_pair(tmp_path)],
        provider=_provider(_document()),
        output_dir=tmp_path / "baseline",
        prompt_path=PROMPT,
        evaluate=True,
    )

    assert result["evaluation"]["metrics"]["record_count"] == 1
    assert result["evaluation"]["metrics"]["validity"]["semantic_valid_rate"] == 1.0
    assert (tmp_path / "baseline" / "evaluation" / "metrics.json").is_file()
