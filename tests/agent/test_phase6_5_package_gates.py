import pytest

from text2ifc_agent.package_gates import validate_package_changeset


def _entity(entity_id, ifc_class, **attributes):
    if ifc_class in {
        "IfcWall", "IfcSpace", "IfcOpeningElement", "IfcDoor", "IfcWindow",
        "IfcSlab", "IfcStair", "IfcStairFlight", "IfcRoof",
    } and "Representation" not in attributes:
        attributes["Representation"] = {
            "kind": "extruded_profile",
            "profile": {"kind": "rectangle", "x": 1000, "y": 200},
            "depth": 3000,
            "direction": [0, 0, 1],
        }
    return {
        "id": entity_id,
        "ifc_class": ifc_class,
        "attributes": attributes,
        "property_sets": {},
        "provenance": {"source": "test"},
    }


def _relationship(relationship_id, ifc_class, **attributes):
    return {"id": relationship_id, "ifc_class": ifc_class, "attributes": attributes}


def _manifest():
    return {
        "schema_version": "text2ifc/generation-package-manifest/1.0",
        "status": "ready",
        "storey_count": 2,
        "issues": [],
        "packages": [
            {
                "package_id": "package-skeleton",
                "kind": "skeleton",
                "storey_id": None,
                "owned_component_ids": ["project", "site", "building", "storey-1", "storey-2"],
                "allowed_reference_ids": [],
            },
            {
                "package_id": "package-storey-1",
                "kind": "storey_local",
                "storey_id": "storey-1",
                "owned_component_ids": [
                    "wall-1", "space-1", "opening-1", "window-1",
                    "containment-1", "void-1", "fill-1",
                ],
                "allowed_reference_ids": ["storey-1"],
            },
            {
                "package_id": "package-storey-2",
                "kind": "storey_local",
                "storey_id": "storey-2",
                "owned_component_ids": ["wall-2", "space-2", "opening-2", "window-2"],
                "allowed_reference_ids": ["storey-2"],
            },
            {
                "package_id": "package-cross-storey",
                "kind": "cross_storey",
                "storey_id": None,
                "owned_component_ids": ["slab-2", "roof", "stair-1-2"],
                "allowed_reference_ids": ["storey-1", "storey-2"],
            },
        ],
    }


def _workspace():
    return {
        "entities": [
            _entity("project", "IfcProject"),
            _entity("site", "IfcSite"),
            _entity("building", "IfcBuilding"),
            _entity("storey-1", "IfcBuildingStorey"),
            _entity("storey-2", "IfcBuildingStorey"),
        ],
        "relationships": [],
    }


def _changeset(package_id, values):
    return {
        "package_id": package_id,
        "operations": [
            {
                "operation_id": f"add-{value['id']}",
                "op": "add_relationship" if value["ifc_class"].startswith("IfcRel") else "add_entity",
                "target_id": value["id"],
                "value": value,
                "evidence_refs": ["issue-package:/expected"],
            }
            for value in values
        ],
    }


def _valid_local_values():
    return [
        _entity("wall-1", "IfcWall"),
        _entity("space-1", "IfcSpace"),
        _entity("opening-1", "IfcOpeningElement"),
        _entity("window-1", "IfcWindow"),
        _relationship(
            "containment-1",
            "IfcRelContainedInSpatialStructure",
            RelatingStructure="storey-1",
            RelatedElements=["wall-1", "space-1", "opening-1", "window-1"],
        ),
        _relationship(
            "void-1",
            "IfcRelVoidsElement",
            RelatingBuildingElement="wall-1",
            RelatedOpeningElement="opening-1",
        ),
        _relationship(
            "fill-1",
            "IfcRelFillsElement",
            RelatingOpeningElement="opening-1",
            RelatedBuildingElement="window-1",
        ),
    ]


def test_package_gate_accepts_owned_storey_local_graph():
    result = validate_package_changeset(
        manifest=_manifest(),
        package_id="package-storey-1",
        workspace=_workspace(),
        changeset=_changeset("package-storey-1", _valid_local_values()),
    )

    assert result == {"valid": True, "issues": []}


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda workspace, values: workspace["entities"].append(_entity("wall-1", "IfcWall")),
            "PACKAGE_DUPLICATE_COMPONENT_ID",
        ),
        (
            lambda workspace, values: values.append(_entity("slab-local", "IfcSlab")),
            "PACKAGE_COMPONENT_NOT_OWNED",
        ),
        (
            lambda workspace, values: next(
                value for value in values if value["id"] == "fill-1"
            )["attributes"].update({"RelatingOpeningElement": "opening-missing"}),
            "PACKAGE_REFERENCE_UNRESOLVED",
        ),
    ],
)
def test_package_gate_rejects_duplicate_unowned_or_orphan_records(mutation, code):
    workspace = _workspace()
    values = _valid_local_values()
    mutation(workspace, values)

    result = validate_package_changeset(
        manifest=_manifest(),
        package_id="package-storey-1",
        workspace=workspace,
        changeset=_changeset("package-storey-1", values),
    )

    assert result["valid"] is False
    assert code in {issue["code"] for issue in result["issues"]}


def test_package_gate_rejects_window_hosted_by_another_storeys_wall():
    workspace = _workspace()
    workspace["entities"].append(_entity("wall-other", "IfcWall"))
    workspace["relationships"].append(
        _relationship(
            "containment-other",
            "IfcRelContainedInSpatialStructure",
            RelatingStructure="storey-2",
            RelatedElements=["wall-other"],
        )
    )
    values = _valid_local_values()
    next(value for value in values if value["id"] == "void-1")["attributes"][
        "RelatingBuildingElement"
    ] = "wall-other"

    result = validate_package_changeset(
        manifest=_manifest(),
        package_id="package-storey-1",
        workspace=workspace,
        changeset=_changeset("package-storey-1", values),
    )

    assert result["valid"] is False
    mismatch = next(issue for issue in result["issues"] if issue["code"] == "PACKAGE_HOST_STOREY_MISMATCH")
    assert mismatch["component_id"] == "opening-1"
    assert mismatch["related_component_id"] == "wall-other"


def test_cross_storey_package_accepts_only_declared_vertical_components():
    values = [
        _entity("slab-2", "IfcSlab"),
        _entity("roof", "IfcRoof", ShapeType="FLAT_ROOF"),
        _entity("stair-1-2", "IfcStair"),
    ]

    result = validate_package_changeset(
        manifest=_manifest(),
        package_id="package-cross-storey",
        workspace=_workspace(),
        changeset=_changeset("package-cross-storey", values),
    )

    assert result["valid"] is True


def test_package_gate_rejects_declared_owned_components_that_are_not_generated():
    result = validate_package_changeset(
        manifest=_manifest(),
        package_id="package-cross-storey",
        workspace=_workspace(),
        changeset=_changeset(
            "package-cross-storey",
            [_entity("slab-2", "IfcSlab")],
        ),
    )

    missing = {
        issue["component_id"]
        for issue in result["issues"]
        if issue["code"] == "PACKAGE_OWNED_COMPONENT_MISSING"
    }
    assert result["valid"] is False
    assert missing == {"roof", "stair-1-2"}


def test_cross_storey_package_accepts_geometry_on_flight_not_decomposed_stair():
    manifest = _manifest()
    package = manifest["packages"][-1]
    package["owned_component_ids"] = ["stair-1-2", "stair-flight-1-2"]
    package["owned_relationship_ids"] = ["aggregate-stair-1-2-flight"]
    stair = _entity("stair-1-2", "IfcStair")
    stair["attributes"].pop("Representation")
    values = [
        stair,
        _entity("stair-flight-1-2", "IfcStairFlight"),
        _relationship(
            "aggregate-stair-1-2-flight",
            "IfcRelAggregates",
            RelatingObject="stair-1-2",
            RelatedObjects=["stair-flight-1-2"],
        ),
    ]

    result = validate_package_changeset(
        manifest=manifest,
        package_id="package-cross-storey",
        workspace=_workspace(),
        changeset=_changeset("package-cross-storey", values),
    )

    assert result == {"valid": True, "issues": []}


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (
            lambda value: value["attributes"].pop("Representation", None),
            "PACKAGE_REPRESENTATION_MISSING",
        ),
        (
            lambda value: value["attributes"]["Representation"]["profile"].update(
                {"kind": "polygon", "points": [[0, 0], [1, 0], [1, 1]], "holes": []}
            ),
            "PACKAGE_PROFILE_HOLES_UNSUPPORTED",
        ),
    ],
)
def test_package_gate_rejects_missing_geometry_or_polygon_holes(mutate, code):
    manifest = _manifest()
    manifest["packages"][-1]["owned_component_ids"].append("slab-test")
    slab = _entity(
        "slab-test",
        "IfcSlab",
        Representation={
            "kind": "extruded_profile",
            "profile": {"kind": "rectangle", "x": 8000, "y": 6000},
            "depth": 150,
            "direction": [0, 0, 1],
        },
    )
    mutate(slab)

    result = validate_package_changeset(
        manifest=manifest,
        package_id="package-cross-storey",
        workspace=_workspace(),
        changeset=_changeset("package-cross-storey", [slab]),
    )

    assert result["valid"] is False
    assert code in {issue["code"] for issue in result["issues"]}


def test_package_gate_rejects_self_overlapping_polygon_profile():
    manifest = _manifest()
    manifest["packages"][-1]["owned_component_ids"] = ["slab-test"]
    manifest["packages"][-1]["owned_relationship_ids"] = []
    slab = _entity(
        "slab-test",
        "IfcSlab",
        Representation={
            "kind": "extruded_profile",
            "profile": {
                "kind": "polygon",
                "points": [
                    [-1, 1],
                    [0, 1],
                    [0, 2],
                    [1, 2],
                    [1, 1],
                    [-1, 1],
                ],
            },
            "depth": 150,
            "direction": [0, 0, 1],
        },
    )

    result = validate_package_changeset(
        manifest=manifest,
        package_id="package-cross-storey",
        workspace=_workspace(),
        changeset=_changeset("package-cross-storey", [slab]),
    )

    assert result["valid"] is False
    issue = next(
        issue
        for issue in result["issues"]
        if issue["code"] == "PACKAGE_POLYGON_PROFILE_SELF_INTERSECTS"
    )
    assert issue["component_id"] == "slab-test"
    assert issue["path"].endswith("/profile/points")


def test_package_gate_accepts_simple_stepped_flight_profile():
    manifest = _manifest()
    manifest["packages"][-1]["owned_component_ids"] = ["stair-flight-1-2"]
    manifest["packages"][-1]["owned_relationship_ids"] = []
    flight = _entity(
        "stair-flight-1-2",
        "IfcStairFlight",
        Representation={
            "kind": "extruded_profile",
            "profile": {
                "kind": "polygon",
                "points": [
                    [0, 0],
                    [3600, 0],
                    [3600, 3000],
                    [2400, 3000],
                    [2400, 2000],
                    [1200, 2000],
                    [1200, 1000],
                    [0, 1000],
                    [0, 0],
                ],
            },
            "depth": 1000,
            "direction": [1, 0, 0],
        },
    )

    result = validate_package_changeset(
        manifest=manifest,
        package_id="package-cross-storey",
        workspace=_workspace(),
        changeset=_changeset("package-cross-storey", [flight]),
    )

    assert result == {"valid": True, "issues": []}
