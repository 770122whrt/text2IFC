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
        *[
            component_id
            for index in range(1, storey_count)
            for component_id in (
                f"stair-{index}-{index + 1}",
                f"stair-flight-{index}-{index + 1}",
            )
        ],
        "roof-main",
    ]
    assert manifest["packages"][-1]["owned_relationship_ids"] == [
        f"aggregate-stair-{index}-{index + 1}-flight"
        for index in range(1, storey_count)
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


def test_expected_facts_flattens_grouped_walls_inside_storey_records():
    brief = {
        "schema_version": "text2ifc/design-brief/2.0",
        "status": "ready",
        "language": "zh-CN",
        "known_facts": {
            "storeys": [
                {
                    "id": "storey-1",
                    "elevation_mm": 0,
                    "walls": {
                        "exterior": [
                            {"id": "wall-south", "side": "south"},
                            {"id": "wall-east", "side": "east"},
                        ],
                        "interior": [{"id": "wall-partition", "axis": "x"}],
                    },
                }
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

    expected = build_expected_facts(case_id="case-grouped-walls", design_brief=brief)

    assert [(wall["id"], wall["storey"]) for wall in expected["walls"]] == [
        ("wall-south", "storey-1"),
        ("wall-east", "storey-1"),
        ("wall-partition", "storey-1"),
    ]
    assert expected["generation_package_manifest"]["packages"][1][
        "owned_component_ids"
    ] == ["wall-south", "wall-east", "wall-partition"]


def test_local_package_declares_deterministic_containment_void_and_fill_relationship_ids():
    expected = _expected(2)
    expected["walls"] = [
        {"id": "wall-storey-1-south", "storey": "storey-1"},
    ]
    expected["doors"] = [
        {
            "id": "door-storey-1-south",
            "storey": "storey-1",
            "host_wall": "wall-storey-1-south",
        }
    ]
    expected["windows"] = [
        {
            "id": "window-storey-1-north",
            "storey": "storey-1",
            "host_wall": "wall-storey-1-north",
        }
    ]

    manifest = build_generation_package_manifest(expected)
    package = next(
        item for item in manifest["packages"] if item["package_id"] == "package-storey-1"
    )

    assert package["owned_relationship_ids"] == [
        "rel-voids-door-storey-1-south",
        "rel-fills-door-storey-1-south",
        "rel-voids-window-storey-1-north",
        "rel-fills-window-storey-1-north",
    ]
    assert not set(package["owned_relationship_ids"]) & set(package["owned_component_ids"])


def test_cross_package_uses_opening_entity_and_void_relation_for_slab_opening_bounds():
    expected = _expected(2)
    expected["slabs"][1]["opening"] = {
        "bounds": {"x_min": 6000, "x_max": 8000, "y_min": 1000, "y_max": 6000}
    }

    manifest = build_generation_package_manifest(expected)
    package = manifest["packages"][-1]

    assert "opening-slab-storey-2" in package["owned_component_ids"]
    assert "rel-voids-slab-storey-2" in package["owned_relationship_ids"]


def test_cross_package_preserves_explicit_plural_slab_opening_id():
    expected = _expected(2)
    expected["slabs"][1]["openings"] = [
        {
            "id": "stair-opening-storey-2",
            "bounds": {"x_min": 6000, "x_max": 8000, "y_min": 1000, "y_max": 6000},
        }
    ]

    package = build_generation_package_manifest(expected)["packages"][-1]

    assert "stair-opening-storey-2" in package["owned_component_ids"]
    assert "rel-voids-slab-storey-2" in package["owned_relationship_ids"]
