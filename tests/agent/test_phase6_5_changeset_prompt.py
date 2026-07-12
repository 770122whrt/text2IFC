import json

from text2ifc_agent.changeset_stage import FEW_SHOT_PATHS
from text2ifc_agent.prompt_registry import load_prompt_registry, render_prompt


def _inputs() -> dict:
    return {
        "USER_REQUEST": "修正二层楼梯终点，不要修改其他构件。",
        "CONVERSATION": [{"role": "user", "content": "楼梯终点应为3150毫米。"}],
        "DESIGN_BRIEF": {"status": "ready", "known_facts": {"stair_top": 3150}},
        "EXPECTED_FACTS": {"stairs": [{"id": "stair-a", "top": 3150}]},
        "SCOPED_COMPONENTS": {
            "stair-a": {"id": "stair-a", "ifc_class": "IfcStair", "attributes": {}}
        },
        "BASE_REVISION": {
            "revision_id": "revision-00",
            "candidate_hash": "sha256:" + "a" * 64,
            "expected_facts_hash": "sha256:" + "b" * 64,
        },
        "CHANGE_SCOPE": {
            "scope_id": "scope-revision-01",
            "entity_ids": ["stair-a"],
            "relationship_ids": [],
            "allowed_paths": {"stair-a": ["/attributes/ObjectPlacement"]},
            "forbidden_ids": ["wall-unrelated"],
        },
        "ISSUES": [
            {
                "issue_id": "issue-stair-001",
                "actual_ref": "entity:stair-a#/attributes/ObjectPlacement",
                "expected": {"top": 3150},
                "actual": {"top": 3000},
            }
        ],
        "CHANGESET_SCHEMA": {"title": "text2IFC BIM JSON ChangeSet 1.0"},
        "DRAFT_SCHEMA": {"title": "BIM JSON Draft Envelope 1.0"},
        "FEW_SHOTS": [
            {"few_shot_id": "changeset.single-component", "output": {"operations": []}},
            {"few_shot_id": "changeset.coupled-dependency", "output": {"operations": []}},
        ],
    }


def test_changeset_prompt_is_registered_as_a_dedicated_mode():
    registry = load_prompt_registry()

    template = registry["bim-json-changeset.v1"]

    assert template["role"] == "bim_json_generator"
    assert template["mode"] == "changeset"
    assert template["sha256"].startswith("sha256:")
    assert "raw_ifc" in template["forbidden_outputs"]
    assert "full_bim_json_replacement" in template["forbidden_outputs"]


def test_changeset_prompt_renders_all_scope_and_evidence_inputs():
    rendered = render_prompt(template_id="bim-json-changeset.v1", inputs=_inputs())
    text = rendered["text"]

    assert "revision-00" in text
    assert "scope-revision-01" in text
    assert "issue-stair-001" in text
    assert "wall-unrelated" in text
    assert '"top": 3150' in text
    assert '"top": 3000' in text
    assert "text2IFC BIM JSON ChangeSet 1.0" in text
    assert "BIM JSON Draft Envelope 1.0" in text
    assert "changeset.single-component" in text
    assert "changeset.coupled-dependency" in text
    assert "不得输出完整 BIM JSON" in text
    assert "不得使用数组索引定位实体或关系" in text
    assert "只能修改 CHANGE_SCOPE 明确允许的 ID 和字段路径" in text
    for name in _inputs():
        assert "{{" + name + "}}" not in text


def test_changeset_few_shots_are_generic_and_schema_valid_json():
    root = load_prompt_registry()["bim-json-changeset.v1"]["path"]
    assert root.endswith("bim-json-changeset-v1.md")
    examples = [
        json.loads(open("prompts/agent/few-shot/changeset-single-component.json", encoding="utf-8").read()),
        json.loads(open("prompts/agent/few-shot/changeset-coupled-dependency.json", encoding="utf-8").read()),
    ]

    serialized = json.dumps(examples, ensure_ascii=False).lower()
    assert "living_room" not in serialized
    assert "storey-1" not in serialized
    assert "storey-2" not in serialized
    assert "10000" not in serialized
    assert {example["few_shot_id"] for example in examples} == {
        "changeset.single-component",
        "changeset.coupled-dependency",
    }


def test_staged_package_prompt_teaches_add_operations_are_generator_owned():
    rendered = render_prompt(template_id="bim-json-changeset.v1", inputs=_inputs())

    assert "Implementation JSON is generator-owned" in rendered["text"]
    assert "changeset-staged-package-add" in {path.stem for path in FEW_SHOT_PATHS}
    example = json.loads(
        open(
            "prompts/agent/few-shot/changeset-staged-package-add.json",
            encoding="utf-8",
        ).read()
    )
    operations = example["output"]["operations"]
    assert {operation["op"] for operation in operations} == {
        "add_entity",
        "add_relationship",
    }
    assert any(
        operation.get("value", {}).get("ifc_class") == "IfcRelContainedInSpatialStructure"
        for operation in operations
    )
