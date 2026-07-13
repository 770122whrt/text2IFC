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
        "CONTEXT_ISSUES": [],
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
    assert not any(
        operation.get("value", {}).get("ifc_class") == "IfcRelContainedInSpatialStructure"
        for operation in operations
    )
    assert {"IfcRelVoidsElement", "IfcRelFillsElement"} <= {
        operation.get("value", {}).get("ifc_class") for operation in operations
    }


def test_staged_package_prompt_requires_exact_authorized_ids_without_rewriting():
    rendered = render_prompt(template_id="bim-json-changeset.v1", inputs=_inputs())
    text = rendered["text"]

    assert "copy an authorized ID character-for-character" in text
    assert "target_id and value.id must be identical" in text
    assert "Do not add, remove, translate, normalize, or duplicate prefixes or suffixes" in text


def test_staged_package_prompt_forbids_copying_another_storey_display_name():
    rendered = render_prompt(template_id="bim-json-changeset.v1", inputs=_inputs())

    assert "Never copy a display-name storey label from a sibling package" in rendered["text"]
    assert "use the current package storey name or a storey-neutral Name" in rendered["text"]


def test_staged_cross_storey_few_shot_teaches_flight_and_slab_opening_graph():
    assert "changeset-staged-cross-storey" in {path.stem for path in FEW_SHOT_PATHS}
    example = json.loads(
        open(
            "prompts/agent/few-shot/changeset-staged-cross-storey.json",
            encoding="utf-8",
        ).read()
    )

    classes = {
        operation.get("value", {}).get("ifc_class")
        for operation in example["output"]["operations"]
    }
    assert {
        "IfcSlab",
        "IfcOpeningElement",
        "IfcStair",
        "IfcStairFlight",
        "IfcRelVoidsElement",
        "IfcRelAggregates",
    } <= classes
    stair = next(
        operation["value"]
        for operation in example["output"]["operations"]
        if operation.get("value", {}).get("ifc_class") == "IfcStair"
    )
    assert "Representation" not in stair["attributes"]

    expected_stair = example["input"]["expected_facts"]["stair"]
    flight = next(
        operation["value"]
        for operation in example["output"]["operations"]
        if operation.get("value", {}).get("ifc_class") == "IfcStairFlight"
    )
    points = flight["attributes"]["Representation"]["profile"]["points"]
    assert expected_stair["number_of_risers"] == 3
    assert expected_stair["riser_height"] == 1000
    assert expected_stair["tread_depth"] == 1200
    assert points[:3] == [[0, 0], [3600, 0], [3600, 3000]]
    assert points[-2:] == [[0, 1000], [0, 0]]


def test_staged_package_prompt_defines_local_simple_stair_profile_convention():
    rendered = render_prompt(template_id="bim-json-changeset.v1", inputs=_inputs())
    text = rendered["text"]

    assert "local [run, rise] coordinates" in text
    assert "must not overlap its closing edges" in text
    assert "number_of_risers * tread_depth" in text


def test_orthogonal_wall_few_shot_uses_two_independent_straight_walls():
    assert "changeset-staged-orthogonal-walls" in {path.stem for path in FEW_SHOT_PATHS}
    example = json.loads(
        open(
            "prompts/agent/few-shot/changeset-staged-orthogonal-walls.json",
            encoding="utf-8",
        ).read()
    )

    walls = [
        operation["value"]
        for operation in example["output"]["operations"]
        if operation.get("value", {}).get("ifc_class") == "IfcWall"
    ]
    assert len(walls) == 2
    assert {tuple(wall["attributes"]["ObjectPlacement"]["ref_direction"]) for wall in walls} == {
        (1, 0, 0),
        (0, 1, 0),
    }
    assert all(
        wall["attributes"]["Representation"]["profile"]["kind"] == "rectangle"
        for wall in walls
    )


def test_prompt_defines_one_canonical_geometry_authoring_contract():
    text = render_prompt(template_id="bim-json-changeset.v1", inputs=_inputs())[
        "text"
    ]

    assert "Rectangle profiles are centered on ObjectPlacement.origin" in text
    assert "origin_x = (x_min + x_max) / 2" in text
    assert "origin_y = (y_min + y_max) / 2" in text
    assert "derive an interior wall only from the unique shared boundary" in text
    assert "Do not guess a wall axis or coordinate" in text
    assert "encode stair plan orientation exactly once" in text
    assert "Do not rotate both the parent stair and the child flight" in text
    assert "Do not silently repair or translate geometry" in text


def test_storey_package_few_shot_places_rectangle_at_bounds_center():
    example = json.loads(
        open(
            "prompts/agent/few-shot/changeset-staged-package-add.json",
            encoding="utf-8",
        ).read()
    )
    expected_space = example["input"]["expected_facts"]["space"]
    space = next(
        operation["value"]
        for operation in example["output"]["operations"]
        if operation.get("value", {}).get("ifc_class") == "IfcSpace"
    )

    assert expected_space["bounds"] == {"x": [0, 6000], "y": [0, 6000]}
    assert space["attributes"]["ObjectPlacement"]["origin"] == [3000, 3000, 0]


def test_cross_storey_few_shot_uses_canonical_bounds_and_single_orientation():
    example = json.loads(
        open(
            "prompts/agent/few-shot/changeset-staged-cross-storey.json",
            encoding="utf-8",
        ).read()
    )
    facts = example["input"]["expected_facts"]
    stair = next(
        operation["value"]
        for operation in example["output"]["operations"]
        if operation.get("value", {}).get("ifc_class") == "IfcStair"
    )
    flight = next(
        operation["value"]
        for operation in example["output"]["operations"]
        if operation.get("value", {}).get("ifc_class") == "IfcStairFlight"
    )

    assert facts["stair"]["bounds"] == {"x": [6500, 7500], "y": [1500, 5100]}
    assert facts["opening"]["bounds"] == {"x": [6000, 8000], "y": [1000, 6000]}
    assert stair["attributes"]["ObjectPlacement"]["ref_direction"] == [1, 0, 0]
    assert flight["attributes"]["ObjectPlacement"]["ref_direction"] == [1, 0, 0]
    assert flight["attributes"]["Representation"]["direction"] == [1, 0, 0]
