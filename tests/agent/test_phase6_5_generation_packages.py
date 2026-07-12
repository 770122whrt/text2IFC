import pytest

from text2ifc_agent.expected_facts import build_expected_facts
from text2ifc_agent.generation_packages import build_generation_package_manifest


def _expected(storey_count):
    storeys = [
        {"id": f"storey-{index}", "elevation_mm": (index - 1) * 3150}
        for index in range(1, storey_count + 1)
    ]
    return {
        "schema_version": "text2ifc/expected-facts/1.0",
        "case_id": "case-a",
        "storeys": storeys,
        "spaces": [
            {"id": f"space-{storey['id']}", "storey": storey["id"]}
            for storey in storeys
        ],
        "doors": [],
        "windows": [],
        "slabs": [
            {
                "id": f"slab-{storey['id']}",
                "storey": storey["id"],
                "elevation_mm": storey["elevation_mm"],
            }
            for storey in storeys
        ],
        "roof": {"id": "roof-main", "elevation_mm": storey_count * 3150},
        "stairs": [
            {
                "id": f"stair-{index}-{index + 1}",
                "from_storey": f"storey-{index}",
                "to_storey": f"storey-{index + 1}",
            }
            for index in range(1, storey_count)
        ],
        "entity_id_contract": {"spaces": [], "doors": [], "windows": []},
        "unresolved_expectations": [],
    }


@pytest.mark.parametrize("storey_count", [2, 3, 5])
def test_manifest_discovers_one_local_package_per_explicit_storey(storey_count):
    manifest = build_generation_package_manifest(_expected(storey_count))

    assert manifest["status"] == "ready"
    assert manifest["storey_count"] == storey_count
    assert [package["package_id"] for package in manifest["packages"]] == [
        "package-skeleton",
        *[f"package-storey-{index}" for index in range(1, storey_count + 1)],
        "package-cross-storey",
    ]
    local = [package for package in manifest["packages"] if package["kind"] == "storey_local"]
    assert [package["storey_id"] for package in local] == [
        f"storey-{index}" for index in range(1, storey_count + 1)
    ]
    assert manifest["packages"][-1]["owned_component_ids"] == [
        *[f"slab-storey-{index}" for index in range(1, storey_count + 1)],
        *[f"stair-{index}-{index + 1}" for index in range(1, storey_count)],
        "roof-main",
    ]


def test_manifest_routes_missing_elevation_to_draft_instead_of_guessing():
    expected = _expected(2)
    del expected["storeys"][1]["elevation_mm"]

    manifest = build_generation_package_manifest(expected)

    assert manifest["status"] == "draft_required"
    assert manifest["packages"] == []
    assert manifest["issues"][0]["code"] == "PACKAGE_STOREY_ELEVATION_MISSING"
    assert manifest["issues"][0]["path"] == "/storeys/1/elevation_mm"


def test_manifest_routes_unknown_stair_endpoint_to_draft():
    expected = _expected(3)
    expected["stairs"][0]["to_storey"] = "storey-missing"

    manifest = build_generation_package_manifest(expected)

    assert manifest["status"] == "draft_required"
    assert "PACKAGE_CROSS_STOREY_ENDPOINT_UNRESOLVED" in {
        issue["code"] for issue in manifest["issues"]
    }


def test_expected_facts_embeds_the_same_generation_package_manifest():
    brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {"id": "storey-a", "elevation_mm": 0},
                {"id": "storey-b", "elevation_mm": 3150},
            ],
            "spaces": [],
            "doors": [],
            "windows": [],
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
        "fact_sources": [],
    }

    expected = build_expected_facts(case_id="case-brief", design_brief=brief)

    assert expected["generation_package_manifest"]["status"] == "ready"
    assert [
        package["storey_id"]
        for package in expected["generation_package_manifest"]["packages"]
        if package["kind"] == "storey_local"
    ] == ["storey-a", "storey-b"]


def test_expected_facts_preserves_explicit_storey_owned_wall_inventory():
    brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {"id": "storey-a", "elevation_mm": 0},
                {"id": "storey-b", "elevation_mm": 3150},
            ],
            "walls": [
                {"id": "wall-a-north", "storey": "storey-a", "axis": "north"},
                {"id": "wall-b-north", "storey": "storey-b", "axis": "north"},
            ],
            "spaces": [],
            "doors": [],
            "windows": [],
        },
        "missing_facts": [],
        "ambiguities": [],
        "unsupported_requests": [],
        "fact_sources": [],
    }

    expected = build_expected_facts(case_id="case-walls", design_brief=brief)

    assert expected["walls"] == brief["known_facts"]["walls"]
    local = {
        package["storey_id"]: package["owned_component_ids"]
        for package in expected["generation_package_manifest"]["packages"]
        if package["kind"] == "storey_local"
    }
    assert "wall-a-north" in local["storey-a"]
    assert "wall-b-north" in local["storey-b"]
