import importlib
import importlib.util
import hashlib


MODULE_NAME = "text2ifc_agent.design_brief"


def _module():
    assert importlib.util.find_spec(MODULE_NAME) is not None, (
        "Design Brief schema validator is missing"
    )
    return importlib.import_module(MODULE_NAME)


def _brief(**overrides):
    document = {
        "schema_version": "text2ifc/design-brief/1.0",
        "language": "zh-CN",
        "original_request": "创建一个长6米、宽4米、高3米的单层房间。",
        "known_facts": {
            "storey_count": 1,
            "space": {"length_mm": 6000, "width_mm": 4000, "height_mm": 3000},
        },
        "missing_facts": [],
        "ambiguities": [],
        "user_corrections": [],
        "clarification_questions": [],
        "provenance": {"source": "user_request"},
    }
    document.update(overrides)
    return document


def test_complete_chinese_room_request_becomes_known_facts():
    design_brief = _module()
    document = _brief()

    assert design_brief.validate_design_brief(document) == []
    assert document["known_facts"]["space"]["length_mm"] == 6000
    assert document["clarification_questions"] == []


def test_weak_request_keeps_missing_dimensions():
    design_brief = _module()
    document = _brief(
        original_request="创建一个房间。",
        known_facts={"object_kind": "room"},
        missing_facts=[
            {
                "id": "room-dimensions",
                "code": "ROOM_DIMENSIONS_MISSING",
                "path": "/known_facts/space",
                "message": "房间长、宽、高尚未提供。",
            }
        ],
        clarification_questions=["请提供房间的长、宽、高。"],
    )

    assert design_brief.validate_design_brief(document) == []
    assert document["known_facts"] == {"object_kind": "room"}
    assert document["missing_facts"][0]["code"] == "ROOM_DIMENSIONS_MISSING"


def test_design_brief_rejects_bim_json_entities():
    design_brief = _module()
    document = _brief(entities=[])

    issues = design_brief.validate_design_brief(document)

    assert any(issue.code == "UNSUPPORTED_FIELD" for issue in issues)
    assert any("entities" in issue.message for issue in issues)


def _v2_evidence_catalog():
    return [
        {"evidence_id": "schema:bim-json-v2:entity"},
        {"evidence_id": "schema:bim-json-v2:representation"},
        {"evidence_id": "capability:IFC2X3:IfcSpace"},
        {"evidence_id": "few-shot:design-brief-v2:incomplete-room"},
    ]


def _brief_v2(**overrides):
    document = {
        "schema_version": "text2ifc/design-brief/2.0",
        "language": "zh-CN",
        "original_request": "创建一个长6米、宽4米、高3米的矩形房间。",
        "status": "ready",
        "known_facts": {
            "space": {"length_mm": 6000, "width_mm": 4000, "height_mm": 3000}
        },
        "fact_sources": [
            {
                "path": "/known_facts/space",
                "source_turns": ["turn-user-001"],
                "evidence_refs": ["schema:bim-json-v2:entity"],
            }
        ],
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
        "user_corrections": [],
        "clarification_questions": [],
        "provenance": {
            "source_turns": ["turn-user-001"],
            "selected_evidence_ids": [
                "schema:bim-json-v2:entity",
                "capability:IFC2X3:IfcSpace",
            ],
            "few_shot_ids": [],
        },
    }
    document.update(overrides)
    return document


def test_v2_ready_brief_is_schema_and_evidence_valid():
    design_brief = _module()

    issues = design_brief.validate_design_brief(
        _brief_v2(), evidence_catalog=_v2_evidence_catalog()
    )

    assert issues == []


def test_v2_rejects_storey_local_floor_slab_dialects():
    design_brief = _module()
    document = _brief_v2(
        known_facts={
            "storeys": [
                {
                    "id": "storey-1",
                    "elevation_mm": 0,
                    "floor_thickness_mm": 150,
                },
                {
                    "id": "storey-2",
                    "elevation_mm": 3150,
                    "floor_slabs": [
                        {
                            "id": "slab-storey-2",
                            "storey": "storey-2",
                            "top_elevation_mm": 3150,
                            "thickness_mm": 150,
                        }
                    ],
                },
            ]
        }
    )

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    slab_issues = [
        issue for issue in issues if issue.code == "NON_CANONICAL_FLOOR_SLAB_LOCATION"
    ]
    assert [issue.path for issue in slab_issues] == [
        "/known_facts/storeys/0/floor_thickness_mm",
        "/known_facts/storeys/1/floor_slabs",
    ]


def test_v2_rejects_multiple_host_centerline_openings_on_one_wall():
    design_brief = _module()
    document = _brief_v2(
        known_facts={
            "storeys": [
                {
                    "id": "storey-1",
                    "elevation_mm": 0,
                    "walls": {
                        "exterior": [{"id": "wall-north"}],
                        "interior": [],
                    },
                    "doors": [],
                    "windows": [
                        {
                            "id": "window-a",
                            "host_wall": "wall-north",
                            "alignment": "host_centerline",
                        },
                        {
                            "id": "window-b",
                            "host_wall": "wall-north",
                            "alignment": "host_centerline",
                        },
                    ],
                }
            ]
        }
    )

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    conflict = next(
        issue for issue in issues if issue.code == "AMBIGUOUS_HOST_CENTERLINE"
    )
    assert conflict.path == "/known_facts/storeys/0/windows/1/alignment"


def test_v2_rejects_question_evidence_not_supplied_to_model():
    design_brief = _module()
    document = _brief_v2(
        status="needs_clarification",
        missing_facts=[
            {
                "id": "mf-wall-thickness",
                "code": "WALL_THICKNESS_MISSING",
                "path": "/known_facts/walls/thickness_mm",
                "message": "墙体厚度尚未提供。",
                "reason": "请求要求生成具有实体厚度的墙体。",
                "blocking": True,
                "evidence_refs": ["schema:bim-json-v2:representation"],
                "source_turns": ["turn-user-001"],
            }
        ],
        clarification_questions=[
            {
                "id": "q-wall-thickness",
                "text": "墙体厚度是多少？",
                "targets": ["mf-wall-thickness"],
                "reason": "缺少该值无法生成用户要求的墙体实体。",
                "evidence_refs": ["schema:not-supplied"],
            }
        ],
    )

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    assert any(issue.code == "UNKNOWN_EVIDENCE_REF" for issue in issues)
    assert any(
        issue.path == "/clarification_questions/0/evidence_refs/0"
        for issue in issues
    )


def test_v2_rejects_question_without_matching_blocker():
    design_brief = _module()
    document = _brief_v2(
        status="needs_clarification",
        missing_facts=[
            {
                "id": "mf-room-width",
                "code": "ROOM_WIDTH_MISSING",
                "path": "/known_facts/space/width_mm",
                "message": "房间宽度尚未提供。",
                "reason": "矩形空间轮廓需要宽度。",
                "blocking": True,
                "evidence_refs": ["schema:bim-json-v2:representation"],
                "source_turns": ["turn-user-001"],
            }
        ],
        clarification_questions=[
            {
                "id": "q-height",
                "text": "房间高度是多少？",
                "targets": ["mf-room-height"],
                "reason": "需要确认高度。",
                "evidence_refs": ["schema:bim-json-v2:representation"],
            }
        ],
    )

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    assert any(issue.code == "UNKNOWN_CLARIFICATION_TARGET" for issue in issues)


def test_v2_ready_status_rejects_blocking_missing_fact():
    design_brief = _module()
    document = _brief_v2(
        missing_facts=[
            {
                "id": "mf-room-width",
                "code": "ROOM_WIDTH_MISSING",
                "path": "/known_facts/space/width_mm",
                "message": "房间宽度尚未提供。",
                "reason": "矩形空间轮廓需要宽度。",
                "blocking": True,
                "evidence_refs": ["schema:bim-json-v2:representation"],
                "source_turns": ["turn-user-001"],
            }
        ]
    )

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    assert any(issue.code == "READINESS_CONFLICT" for issue in issues)


def test_v2_ready_status_rejects_blocking_unsupported_request():
    design_brief = _module()
    document = _brief_v2(
        unsupported_requests=[
            {
                "id": "unsupported-window-operation",
                "path": "/known_facts/windows/0/operation_type",
                "message": "当前生成能力不支持该窗扇开启机构。",
                "reason": "用户明确要求保留该语义，但能力证据标记为 unsupported。",
                "blocking": True,
                "requested_value": "复杂联动上悬窗",
                "evidence_refs": ["capability:IFC2X3:IfcSpace"],
                "source_turns": ["turn-user-001"],
            }
        ]
    )

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    assert any(issue.code == "READINESS_CONFLICT" for issue in issues)


def test_v2_needs_clarification_requires_one_to_three_questions():
    design_brief = _module()
    document = _brief_v2(status="needs_clarification")

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    assert any(issue.path == "/clarification_questions" for issue in issues)


def test_v2_terminal_statuses_reject_clarification_questions():
    design_brief = _module()

    for status in ("draft_required", "blocked"):
        document = _brief_v2(
            status=status,
            missing_facts=[
                {
                    "id": "mf-room-height",
                    "code": "ROOM_HEIGHT_MISSING",
                    "path": "/known_facts/space/height_mm",
                    "message": "房间高度尚未确定。",
                    "reason": "矩形空间需要高度才能生成几何。",
                    "blocking": True,
                    "evidence_refs": ["schema:bim-json-v2:representation"],
                    "source_turns": ["turn-user-001"],
                }
            ],
            clarification_questions=[
                {
                    "id": "q-room-height",
                    "text": "房间高度是多少？",
                    "targets": ["mf-room-height"],
                    "reason": "如果仍可询问用户，应使用 needs_clarification。",
                    "evidence_refs": ["schema:bim-json-v2:representation"],
                }
            ],
        )

        issues = design_brief.validate_design_brief(
            document, evidence_catalog=_v2_evidence_catalog()
        )

        assert any(
            issue.code == "READINESS_CONFLICT"
            and issue.path == "/clarification_questions"
            for issue in issues
        )


def test_v2_correction_requires_source_turn_and_evidence():
    design_brief = _module()
    document = _brief_v2(
        user_corrections=[
            {
                "path": "/known_facts/walls/thickness_mm",
                "value": 300,
                "source_turn": "turn-user-002",
                "replaces": None,
            }
        ]
    )

    issues = design_brief.validate_design_brief(
        document, evidence_catalog=_v2_evidence_catalog()
    )

    assert any(
        issue.path == "/user_corrections/0/evidence_refs" for issue in issues
    )


def test_context_selector_returns_hash_verified_existing_evidence():
    assert importlib.util.find_spec("text2ifc_agent.context_selection") is not None, (
        "Design Brief context selector is missing"
    )
    selector = importlib.import_module("text2ifc_agent.context_selection")

    selection = selector.select_design_brief_context(
        user_request=(
            "创建一个矩形房间，四面墙闭合，南墙有门，北墙有窗，墙厚300毫米。"
        ),
        conversation=[
            {"turn_id": "turn-user-001", "role": "user", "content": "创建房间。"}
        ],
    )

    evidence = selection["evidence"]
    evidence_ids = {record["evidence_id"] for record in evidence}
    assert {
        "capability:IFC2X3:IfcSpace",
        "capability:IFC2X3:IfcWall",
        "capability:IFC2X3:IfcDoor",
        "capability:IFC2X3:IfcWindow",
        "schema:bim-json-v2:entity",
        "schema:bim-json-v2:representation",
    } <= evidence_ids
    assert len(evidence_ids) == len(evidence)
    for record in evidence:
        source = selector.PROJECT_ROOT / record["source_path"]
        assert source.is_file()
        assert record["source_sha256"] == (
            "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
        )
        assert record["json_pointer"].startswith("/")
    assert selection["request_sha256"].startswith("sha256:")


def test_context_selector_supplies_ifc_building_when_request_names_it():
    selector = importlib.import_module("text2ifc_agent.context_selection")

    selection = selector.select_design_brief_context(
        user_request="请生成 IfcBuilding、两个 IfcBuildingStorey、IfcSpace、IfcWall、IfcDoor。",
        conversation=[],
    )

    evidence_ids = {record["evidence_id"] for record in selection["evidence"]}
    assert "capability:IFC2X3:IfcBuilding" in evidence_ids
    assert "IfcBuilding" in selection["selected_ifc_classes"]


def test_context_selector_supplies_ifc_stair_for_english_stair_requests():
    selector = importlib.import_module("text2ifc_agent.context_selection")

    selection = selector.select_design_brief_context(
        user_request=(
            "Create a two-storey building with a straight stair from the ground "
            "storey stairwell to the first storey stair landing."
        ),
        conversation=[],
    )

    evidence_ids = {record["evidence_id"] for record in selection["evidence"]}
    assert "capability:IFC2X3:IfcStair" in evidence_ids


def test_context_selector_matches_english_ifc_terms_case_insensitively():
    selector = importlib.import_module("text2ifc_agent.context_selection")

    selection = selector.select_design_brief_context(
        user_request="Generate an IfcStair in a StairRoom with one IfcWindow.",
        conversation=[],
    )

    evidence_ids = {record["evidence_id"] for record in selection["evidence"]}
    assert "capability:IFC2X3:IfcStair" in evidence_ids
    assert "capability:IFC2X3:IfcWindow" in evidence_ids


def test_context_selector_supplies_core_ifc_capabilities_for_english_multistorey_requests():
    selector = importlib.import_module("text2ifc_agent.context_selection")

    selection = selector.select_design_brief_context(
        user_request=(
            "Create a two-storey building with spaces, walls, slabs, stairs, "
            "doors, windows, and openings."
        ),
        conversation=[],
    )

    evidence_ids = {item["evidence_id"] for item in selection["evidence"]}
    assert "capability:IFC2X3:IfcBuilding" in evidence_ids
    assert "capability:IFC2X3:IfcBuildingStorey" in evidence_ids
    assert "capability:IFC2X3:IfcSpace" in evidence_ids
    assert "capability:IFC2X3:IfcWall" in evidence_ids
    assert "capability:IFC2X3:IfcSlab" in evidence_ids
    assert "capability:IFC2X3:IfcStair" in evidence_ids
    assert "capability:IFC2X3:IfcDoor" in evidence_ids
    assert "capability:IFC2X3:IfcWindow" in evidence_ids
    assert "capability:IFC2X3:IfcOpeningElement" in evidence_ids
    assert "IfcStair" in selection["selected_ifc_classes"]


def test_context_selector_supplies_storey_for_chinese_floor_elevation_requests():
    selector = importlib.import_module("text2ifc_agent.context_selection")

    selection = selector.select_design_brief_context(
        user_request=(
            "创建一个双层建筑。首层标高0毫米，二层标高3150毫米，"
            "每层净高3000毫米，每层都有独立四面外墙和楼板。"
        ),
        conversation=[],
    )

    evidence_ids = {item["evidence_id"] for item in selection["evidence"]}
    assert "capability:IFC2X3:IfcBuildingStorey" in evidence_ids
    assert "IfcBuildingStorey" in selection["selected_ifc_classes"]


def test_context_selector_uses_named_conditional_examples_not_policy_lists():
    selector = importlib.import_module("text2ifc_agent.context_selection")

    selection = selector.select_design_brief_context(
        user_request="创建一个房间，但我还不知道宽度。",
        conversation=[],
    )

    few_shot_ids = {record["few_shot_id"] for record in selection["few_shots"]}
    assert "design-brief-v2.incomplete-room" in few_shot_ids
    rendered = repr(selection)
    assert "required_facts" not in rendered
    assert "not_required" not in rendered
    assert "全局必填字段清单" not in rendered
