from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from text2ifc_agent.prompt_registry import load_prompt_registry, render_prompt
from text2ifc_ifc2text.writing import assemble_sectioned_description, build_fact_index


ROOT = Path(__file__).resolve().parents[2]


def _load_schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / "ifc2text" / name).read_text(encoding="utf-8"))


def test_ifc2text_prompt_versions_are_registered_and_renderable() -> None:
    registry = load_prompt_registry()
    expected = {
        "ifc2text-outline.v0.1": "ifc2text_outline",
        "ifc2text-section-writer.v0.1": "ifc2text_section_writer",
        "ifc2text-merge.v0.1": "ifc2text_merge",
    }
    for template_id, role in expected.items():
        assert template_id in registry
        assert registry[template_id]["role"] == role
        assert registry[template_id]["sha256"].startswith("sha256:")

    outline = render_prompt(
        template_id="ifc2text-outline.v0.1",
        inputs={
            "BUILDING_FACTS": {"storey_count": 2},
            "FACT_INDEX": {"records": [{"fact_ref": "S01"}]},
            "EXTRACTION_ISSUES": [],
            "OUTLINE_SCHEMA": _load_schema("outline-0.1.schema.json"),
        },
    )
    section = render_prompt(
        template_id="ifc2text-section-writer.v0.1",
        inputs={
            "SECTION_PLAN": {"section_id": "s1", "allowed_fact_refs": ["W001"]},
            "SECTION_FACTS": [{"fact_ref": "W001", "length_mm": 5000}],
            "WRITING_CONTEXT": {"coordinate_system": "ifc_world"},
            "SECTION_LIMITATIONS": [],
            "SECTION_SCHEMA": _load_schema("section-0.1.schema.json"),
        },
    )
    merge = render_prompt(
        template_id="ifc2text-merge.v0.1",
        inputs={
            "OUTLINE": {"sections": [{"section_id": "s1"}]},
            "SECTION_RESULTS": [{"section_id": "s1", "text": "墙体说明"}],
            "GLOBAL_FACTS_AND_LIMITATIONS": {"limitations": []},
            "MERGE_SCHEMA": _load_schema("merge-0.1.schema.json"),
        },
    )
    for rendered in (outline, section, merge):
        assert "{{" not in rendered["text"]
        assert rendered["metadata"]["template_hash"].startswith("sha256:")


def test_ifc2text_output_schemas_accept_minimal_valid_contracts() -> None:
    outline = {
        "schema_version": "text2ifc/ifc2text-outline/0.1",
        "structure": "total-part-total",
        "sections": [
            {
                "section_id": "opening",
                "kind": "opening_overview",
                "title": "整体概况",
                "storey": None,
                "allowed_fact_refs": ["building"],
                "required_fact_refs": ["building"],
                "primary_owned_fact_refs": ["building"],
                "required_limitations": [],
            },
            {
                "section_id": "closing",
                "kind": "closing_summary",
                "title": "总结",
                "storey": None,
                "allowed_fact_refs": [],
                "required_fact_refs": [],
                "primary_owned_fact_refs": [],
                "required_limitations": [],
            },
        ],
        "unresolved_fact_refs": [],
    }
    section = {
        "schema_version": "text2ifc/ifc2text-section/0.1",
        "section_id": "opening",
        "text": "建筑共两层。",
        "used_fact_refs": ["building"],
        "omitted_required_fact_refs": [],
        "unresolved_fact_refs": [],
    }
    merge = {
        "schema_version": "text2ifc/ifc2text-merge/0.1",
        "section_order": ["opening", "closing"],
        "transition_text": [],
        "limitations": [],
        "blocked_sections": [],
    }
    Draft202012Validator(_load_schema("outline-0.1.schema.json")).validate(outline)
    Draft202012Validator(_load_schema("section-0.1.schema.json")).validate(section)
    Draft202012Validator(_load_schema("merge-0.1.schema.json")).validate(merge)


def test_fact_index_excludes_source_identity_and_merge_cannot_rewrite_section_body() -> None:
    facts = {
        "building": {"building_name": "B", "project_name": "P", "storey_count": 1},
        "storeys": [
            {
                "label": "S01",
                "name": "一层",
                "elevation_mm": 0,
                "spaces": [],
                "derived_spaces": [],
                "walls": [
                    {
                        "label": "W001",
                        "name": "Wall",
                        "source_global_id": "secret-guid",
                        "host_global_id": "another-secret",
                        "axis_start_mm": [0, 0, 0],
                        "axis_end_mm": [5000, 0, 0],
                    }
                ],
                "openings": [],
                "doors": [],
                "windows": [],
                "stairs": [],
            }
        ],
        "issues": [],
    }
    index = build_fact_index(facts)
    rendered = json.dumps(index, ensure_ascii=False)
    assert "secret-guid" not in rendered
    assert "another-secret" not in rendered
    assert any(record["fact_ref"] == "W001" for record in index["records"])

    outline = {
        "sections": [
            {"section_id": "opening"},
            {"section_id": "walls"},
            {"section_id": "closing"},
        ]
    }
    sections = [
        {
            "section_id": "opening",
            "text": "原样开头正文。",
            "omitted_required_fact_refs": [],
        },
        {
            "section_id": "walls",
            "text": "原样墙体正文，长度 5.000 m。",
            "omitted_required_fact_refs": [],
        },
        {
            "section_id": "closing",
            "text": "原样结尾总结。",
            "omitted_required_fact_refs": [],
        },
    ]
    merge = {
        "section_order": ["opening", "walls", "closing"],
        "transition_text": [{"before_section_id": "walls", "text": "下面进入墙体。"}],
        "limitations": [],
        "blocked_sections": [],
        "rewritten_section_body": "这段即使出现也没有接口进入最终正文",
    }
    text = assemble_sectioned_description(
        outline=outline,
        section_results=sections,
        merge_result=merge,
    )
    assert "原样开头正文。" in text
    assert "原样墙体正文，长度 5.000 m。" in text
    assert "原样结尾总结。" in text
    assert "这段即使出现也没有接口进入最终正文" not in text


def test_merge_blocks_section_with_omitted_required_fact() -> None:
    with pytest.raises(ValueError, match="IFC2TEXT_SECTION_REQUIRED_FACT_OMITTED"):
        assemble_sectioned_description(
            outline={"sections": [{"section_id": "walls"}]},
            section_results=[
                {
                    "section_id": "walls",
                    "text": "不完整正文",
                    "omitted_required_fact_refs": ["W002"],
                }
            ],
            merge_result={
                "section_order": ["walls"],
                "transition_text": [],
                "limitations": [],
                "blocked_sections": [],
            },
        )
