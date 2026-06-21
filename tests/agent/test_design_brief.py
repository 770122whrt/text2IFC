import importlib
import importlib.util


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
