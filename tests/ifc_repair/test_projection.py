import json

from text2ifc_ifc_repair.projection import (
    project_public_repair_spec,
    render_repair_request,
)


PRIVATE_MANIFEST = {
    "schema_version": "text2ifc/ifc-repair-mutation-private/0.1",
    "mutation_type": "remove_window_and_opening",
    "source": {
        "path": "C:/private/case/source.ifc",
        "sha256": "source-hash",
    },
    "target": {
        "wall": {
            "ifc_class": "IfcWallStandardCase",
            "step_id": 1105,
            "global_id": "wall-public-candidate-id",
            "name": "Basic Wall:Outside wall:346660",
            "storey": "Level 1",
            "local_reference": "wall_local_start",
        },
        "opening": {
            "step_id": 35174,
            "global_id": "secret-opening-global-id",
            "wall_local_origin_mm": [3500.0, 100.0, 305.0],
            "geometric_center_offset_mm": 3042.5,
            "sill_height_mm": 305.0,
        },
        "window": {
            "step_id": 13695,
            "global_id": "secret-window-global-id",
            "name": "secret-original-window-name",
            "width_mm": 915.0,
            "height_mm": 1830.0,
        },
        "relationships": {
            "fills_step_id": 35191,
            "voids_step_id": 35179,
        },
    },
    "gold_changeset": {"secret": True},
}


def test_public_projection_is_an_explicit_allowlist() -> None:
    public_spec = project_public_repair_spec(
        PRIVATE_MANIFEST,
        request_id="large-building-window-repair-001",
    )

    assert public_spec == {
        "schema_version": "text2ifc/ifc-repair-spec/0.1",
        "request_id": "large-building-window-repair-001",
        "requested_operation_type": "add_window_with_opening_to_wall",
        "storey": {"name": "Level 1"},
        "target": {
            "ifc_class": "IfcWall",
            "description": "Basic Wall:Outside wall:346660",
            "local_reference": {
                "reference": "wall_local_start",
                "meaning": "宿主墙 Axis 表示的第一个点，沿 Axis 正方向测量",
                "opening_center_offset_mm": 3042.5,
            },
        },
        "opening": {
            "width_mm": 915.0,
            "height_mm": 1830.0,
            "sill_height_mm": 305.0,
        },
        "window": {"fit_opening": True},
        "preservation_requirements": [
            "保持宿主墙的身份、放置、材质、类型和属性不变",
            "保持楼层、空间布局和其他构件不变",
        ],
    }

    provider_input = json.dumps(public_spec, ensure_ascii=False) + render_repair_request(
        public_spec
    )
    for forbidden in (
        "secret-opening-global-id",
        "secret-window-global-id",
        "secret-original-window-name",
        "35174",
        "13695",
        "35191",
        "35179",
        "C:/private/case/source.ifc",
        "gold_changeset",
    ):
        assert forbidden not in provider_input
