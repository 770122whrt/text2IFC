import json

from text2ifc_ifc_repair.projection import (
    project_public_batch_repair_spec,
    render_batch_repair_request,
)


def _private_target(index: int) -> dict:
    return {
        "target_id": f"window-repair-{index:03d}",
        "wall": {
            "ifc_class": "IfcWallStandardCase",
            "global_id": f"wall-{index}",
            "name": f"基本墙:{index}",
            "storey": f"标高 {index}",
            "local_reference": "wall_local_start",
        },
        "opening": {
            "global_id": f"private-opening-{index}",
            "geometric_center_offset_mm": 1000.0 + index,
            "sill_height_mm": 900.0,
        },
        "window": {
            "global_id": f"private-window-{index}",
            "name": f"private-name-{index}",
            "width_mm": 1200.0,
            "height_mm": 1500.0,
        },
        "prototype_evidence": {
            "source": "damaged_ifc_surviving_type",
            "ifc_class": "IfcWindowStyle",
            "global_id": f"style-{index}",
            "name": f"1200x1500-{index}",
            "surviving_occurrence_count": 1,
        },
    }


def test_batch_projection_is_bounded_ordered_and_gold_free() -> None:
    manifest = {
        "schema_version": "text2ifc/ifc-repair-mutation-private/0.2",
        "mutation_type": "remove_windows_and_openings_batch",
        "source": {"path": "C:/private/vvo.ifc", "sha256": "secret-source"},
        "targets": [_private_target(index) for index in range(1, 6)],
        "ground_truth": {"secret": True},
    }

    public_spec = project_public_batch_repair_spec(
        manifest,
        request_id="vvo-five-window-001",
    )
    request = render_batch_repair_request(public_spec)

    assert public_spec["schema_version"] == "text2ifc/ifc-repair-spec/0.2"
    assert len(public_spec["operations"]) == 5
    assert [item["operation_id"] for item in public_spec["operations"]] == [
        f"window-repair-{index:03d}" for index in range(1, 6)
    ]
    assert [item["target"]["global_id"] for item in public_spec["operations"]] == [
        f"wall-{index}" for index in range(1, 6)
    ]
    assert "共 5 扇窗" in request
    assert "wall-1" in request
    assert "1200x1500-1" in request

    provider_input = json.dumps(public_spec, ensure_ascii=False) + request
    for index in range(1, 6):
        assert f"private-opening-{index}" not in provider_input
        assert f"private-window-{index}" not in provider_input
        assert f"private-name-{index}" not in provider_input
    for forbidden in ("C:/private/vvo.ifc", "secret-source", "ground_truth"):
        assert forbidden not in provider_input

