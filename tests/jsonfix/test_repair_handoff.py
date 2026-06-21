from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from text2ifc_agent.providers import FakeAgentProvider, FileAgentProvider
from text2ifc_jsonfix.repair_cases import repair_case


def _api():
    try:
        module = importlib.import_module("text2ifc_jsonfix.handoff")
    except ModuleNotFoundError as exc:
        pytest.fail(f"repair provider handoff is not implemented: {exc}")
    return module.render_repair_prompt, module.run_repair_handoff


def _response(case: dict) -> dict:
    return {
        "text": json.dumps(
            case["patch"],
            ensure_ascii=False,
            sort_keys=True,
        ),
        "metadata": {"provider": "deterministic-test"},
    }


def test_prompt_renderer_binds_case_without_mutating_inputs() -> None:
    render_repair_prompt, _ = _api()
    case = repair_case("missing-piece-repair")
    base_before = json.dumps(case["base"], sort_keys=True)

    prompt = render_repair_prompt(
        user_request=case["input_text"],
        base_document=case["base"],
        validation_feedback=[],
    )

    assert case["input_text"] in prompt
    assert "jsonfix-missing-piece-base" in prompt
    assert '"wall-south"' in prompt
    assert '"wall-west"' not in prompt.split(
        "Base BIM JSON semantic summary:", 1
    )[1].split("Validation or review feedback:", 1)[0]
    assert "bim-json-patch/1.0" in prompt
    assert json.dumps(case["base"], sort_keys=True) == base_before


def test_fake_provider_patch_composes_to_expected_document() -> None:
    _, run_repair_handoff = _api()
    case = repair_case("missing-piece-repair")
    provider = FakeAgentProvider({"repair-1": _response(case)})

    result = run_repair_handoff(
        provider=provider,
        session_id="repair-1",
        user_request=case["input_text"],
        base_document=case["base"],
    )

    assert result.success
    assert result.status == "formal_ready"
    assert result.patch == case["patch"]
    assert result.document == case["expected"]
    assert result.provider_metadata == {"provider": "deterministic-test"}


def test_file_provider_replays_the_same_semantic_patch(
    tmp_path: Path,
) -> None:
    _, run_repair_handoff = _api()
    case = repair_case("missing-piece-repair")
    response_path = tmp_path / "repair-file.json"
    response_path.write_text(
        json.dumps(case["patch"], ensure_ascii=False),
        encoding="utf-8",
    )
    provider = FileAgentProvider.from_path(tmp_path)

    result = run_repair_handoff(
        provider=provider,
        session_id="repair-file",
        user_request=case["input_text"],
        base_document=case["base"],
    )

    assert result.success
    assert result.document == case["expected"]
    assert result.provider_metadata["source_path"].endswith(
        "repair-file.json"
    )


def test_invalid_provider_json_remains_diagnostic() -> None:
    _, run_repair_handoff = _api()
    case = repair_case("missing-piece-repair")
    provider = FakeAgentProvider(
        {
            "repair-invalid": {
                "text": "{",
                "metadata": {"provider": "fake"},
            }
        }
    )

    result = run_repair_handoff(
        provider=provider,
        session_id="repair-invalid",
        user_request=case["input_text"],
        base_document=case["base"],
    )

    assert not result.success
    assert result.status == "provider_parse_error"
    assert result.patch is None
    assert result.document is None
    assert result.diagnostics[0]["code"] == "JSON_DECODE_ERROR"
