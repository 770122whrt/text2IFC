from __future__ import annotations

import json
from pathlib import Path

import pytest

from text2ifc_agent.providers import FakeAgentProvider
from text2ifc_ifc2text.llm_pipeline import IFC2TextLLMError, run_llm_description


def _facts() -> dict:
    return {
        "source": {
            "path": "private/source.ifc",
            "sha256": "sha256:secret",
            "ifc_schema": "IFC2X3",
            "size_bytes": 123,
        },
        "units": {"length": "millimetre", "area": "square_metre"},
        "coordinate_system": {"frame": "ifc_world", "axis_convention": "no inferred north"},
        "building": {"project_name": "P", "building_name": "B", "storey_count": 1},
        "capability": {
            "explicit_space_count": 0,
            "derived_space_count": 0,
            "wall_count": 1,
            "door_count": 0,
            "window_count": 0,
            "opening_count": 0,
            "measurement_issue_count": 0,
        },
        "storeys": [
            {
                "label": "S01",
                "source_global_id": "storey-secret-guid",
                "name": "一层",
                "elevation_mm": 0,
                "spaces": [],
                "derived_spaces": [],
                "walls": [
                    {
                        "label": "W001",
                        "source_global_id": "wall-secret-guid",
                        "name": "北侧测试墙",
                        "ifc_class": "IfcWall",
                        "storey": "S01",
                        "axis_start_mm": [0, 0, 0],
                        "axis_end_mm": [5000, 0, 0],
                        "axis_direction": [1, 0, 0],
                        "length_mm": 5000,
                        "thickness_mm": 200,
                        "height_mm": 3000,
                        "measurement_status": "measured",
                        "spaces": [],
                        "openings": [],
                    }
                ],
                "openings": [],
                "doors": [],
                "windows": [],
                "stairs": [],
            }
        ],
        "unassigned": {"walls": [], "openings": [], "doors": [], "windows": [], "spaces": [], "stairs": []},
        "issues": [],
    }


def _outline(*, wall_ref: str = "S01:W001") -> dict:
    return {
        "schema_version": "text2ifc/ifc2text-outline/0.1",
        "structure": "total-part-total",
        "sections": [
            {
                "section_id": "opening",
                "kind": "opening_overview",
                "title": "整体概况",
                "storey": None,
                "allowed_fact_refs": ["building", "S01"],
                "required_fact_refs": ["building", "S01"],
                "primary_owned_fact_refs": ["building", "S01"],
                "required_limitations": [],
            },
            {
                "section_id": "s01-walls",
                "kind": "walls",
                "title": "一层墙体",
                "storey": "S01",
                "allowed_fact_refs": [wall_ref],
                "required_fact_refs": [wall_ref],
                "primary_owned_fact_refs": [wall_ref],
                "required_limitations": [],
            },
            {
                "section_id": "closing",
                "kind": "closing_summary",
                "title": "说明总结",
                "storey": None,
                "allowed_fact_refs": ["building"],
                "required_fact_refs": [],
                "primary_owned_fact_refs": [],
                "required_limitations": [],
            },
        ],
        "unresolved_fact_refs": [],
    }


def _responses(run_id: str) -> dict[str, dict]:
    return {
        f"{run_id}:outline": {"text": json.dumps(_outline(), ensure_ascii=False), "metadata": {"evidence_class": "offline_fake"}},
        f"{run_id}:section:opening": {
            "text": json.dumps(
                {
                    "schema_version": "text2ifc/ifc2text-section/0.1",
                    "section_id": "opening",
                    "text": "该建筑包含一个楼层，使用源 IFC 世界坐标作为定位基准。",
                    "used_fact_refs": ["building", "S01"],
                    "omitted_required_fact_refs": [],
                    "unresolved_fact_refs": [],
                },
                ensure_ascii=False,
            )
        },
        f"{run_id}:section:s01-walls": {
            "text": json.dumps(
                {
                    "schema_version": "text2ifc/ifc2text-section/0.1",
                    "section_id": "s01-walls",
                    "text": "一层 W001 墙体中心轴从 (0, 0, 0) mm 延伸至 (5000, 0, 0) mm，厚 200 mm，高 3000 mm。",
                    "used_fact_refs": ["S01:W001"],
                    "omitted_required_fact_refs": [],
                    "unresolved_fact_refs": [],
                },
                ensure_ascii=False,
            )
        },
        f"{run_id}:section:closing": {
            "text": json.dumps(
                {
                    "schema_version": "text2ifc/ifc2text-section/0.1",
                    "section_id": "closing",
                    "text": "以上说明完整覆盖本基线中可确认的楼层与墙体事实。",
                    "used_fact_refs": ["building"],
                    "omitted_required_fact_refs": [],
                    "unresolved_fact_refs": [],
                },
                ensure_ascii=False,
            )
        },
        f"{run_id}:merge": {
            "text": json.dumps(
                {
                    "schema_version": "text2ifc/ifc2text-merge/0.1",
                    "section_order": ["opening", "s01-walls", "closing"],
                    "transition_text": [{"before_section_id": "s01-walls", "text": "以下按楼层展开。"}],
                    "limitations": [],
                    "blocked_sections": [],
                },
                ensure_ascii=False,
            )
        },
    }


def test_full_fake_pipeline_writes_final_text_and_prompt_safe_trace(tmp_path: Path) -> None:
    run_id = "offline-complete"
    manifest = run_llm_description(
        facts=_facts(),
        output_dir=tmp_path / "run",
        provider=FakeAgentProvider(_responses(run_id)),
        run_id=run_id,
    )
    assert manifest["status"] == "completed"
    text = Path(manifest["description_path"]).read_text(encoding="utf-8")
    assert "一个楼层" in text
    assert "厚 200 mm" in text
    assert "以下按楼层展开" in text
    assert "wall-secret-guid" not in text
    prompt_text = (tmp_path / "run" / "outline" / "prompt-rendered.md").read_text(encoding="utf-8")
    assert "wall-secret-guid" not in prompt_text
    assert "private/source.ifc" not in prompt_text
    assert "S01:W001" in prompt_text
    assert (tmp_path / "run" / "outline" / "provider-evidence.json").is_file()
    assert (tmp_path / "run" / "merge" / "semantic-validation.json").is_file()


def test_outline_section_limit_blocks_runaway_section_calls(tmp_path: Path) -> None:
    run_id = "offline-section-limit"
    responses = _responses(run_id)
    outline = _outline()
    middle = []
    for index in range(23):
        middle.append(
            {
                "section_id": f"extra-{index:02d}",
                "kind": "storey_overview",
                "title": f"额外段落 {index}",
                "storey": "S01",
                "allowed_fact_refs": ["S01"],
                "required_fact_refs": [],
                "primary_owned_fact_refs": [],
                "required_limitations": [],
            }
        )
    outline["sections"] = [outline["sections"][0], *middle, outline["sections"][1], outline["sections"][2]]
    assert len(outline["sections"]) == 26
    responses[f"{run_id}:outline"]["text"] = json.dumps(outline, ensure_ascii=False)
    with pytest.raises(IFC2TextLLMError, match="SECTION_LIMIT_EXCEEDED"):
        run_llm_description(
            facts=_facts(),
            output_dir=tmp_path / "run",
            provider=FakeAgentProvider(responses),
            run_id=run_id,
        )
    assert not (tmp_path / "run" / "sections").exists()


def test_outline_unknown_fact_ref_fails_closed_before_section_calls(tmp_path: Path) -> None:
    run_id = "offline-unknown"
    responses = _responses(run_id)
    responses[f"{run_id}:outline"]["text"] = json.dumps(_outline(wall_ref="S01:W999"), ensure_ascii=False)
    with pytest.raises(IFC2TextLLMError, match="UNKNOWN_ALLOWED_FACT"):
        run_llm_description(
            facts=_facts(),
            output_dir=tmp_path / "run",
            provider=FakeAgentProvider(responses),
            run_id=run_id,
        )
    assert not (tmp_path / "run" / "sections").exists()


def test_malformed_outline_is_preserved_and_fails_closed(tmp_path: Path) -> None:
    run_id = "offline-malformed"
    responses = _responses(run_id)
    responses[f"{run_id}:outline"]["text"] = "{not-json"
    with pytest.raises(IFC2TextLLMError, match="PARSE_ERROR"):
        run_llm_description(
            facts=_facts(),
            output_dir=tmp_path / "run",
            provider=FakeAgentProvider(responses),
            run_id=run_id,
        )
    assert (tmp_path / "run" / "outline" / "raw-response.txt").read_text(encoding="utf-8") == "{not-json"
    assert json.loads((tmp_path / "run" / "outline" / "validation.json").read_text(encoding="utf-8"))["valid"] is False


def test_section_required_fact_self_report_cannot_silently_drop_required_ref(tmp_path: Path) -> None:
    run_id = "offline-section-drop"
    responses = _responses(run_id)
    payload = json.loads(responses[f"{run_id}:section:s01-walls"]["text"])
    payload["used_fact_refs"] = []
    responses[f"{run_id}:section:s01-walls"]["text"] = json.dumps(payload, ensure_ascii=False)
    with pytest.raises(IFC2TextLLMError, match="REQUIRED_FACT_UNACCOUNTED"):
        run_llm_description(
            facts=_facts(),
            output_dir=tmp_path / "run",
            provider=FakeAgentProvider(responses),
            run_id=run_id,
        )


def test_merge_cannot_silently_drop_completed_section(tmp_path: Path) -> None:
    run_id = "offline-merge-drop"
    responses = _responses(run_id)
    payload = json.loads(responses[f"{run_id}:merge"]["text"])
    payload["section_order"] = ["opening", "closing"]
    responses[f"{run_id}:merge"]["text"] = json.dumps(payload, ensure_ascii=False)
    with pytest.raises(IFC2TextLLMError, match="SECTION_ACCOUNTING_INVALID"):
        run_llm_description(
            facts=_facts(),
            output_dir=tmp_path / "run",
            provider=FakeAgentProvider(responses),
            run_id=run_id,
        )
