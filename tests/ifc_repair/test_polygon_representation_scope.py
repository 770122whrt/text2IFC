"""Offline scope checks; they do not test language understanding or live repair."""
import pytest

from scripts.ifc_repair.audit_harness_geometry_scope import polygon_scene, run_probe
from text2ifc_ifc_repair.door_geometry import public_door_installation_anchor
from text2ifc_ifc_repair.window_geometry import public_window_installation_anchor


@pytest.mark.parametrize("kind", ["door", "window"])
def test_public_api_reuses_polygon_frame_complete_mesh_and_preserves_source(tmp_path, kind):
    result = run_probe(tmp_path / kind, kind)
    assert result["exact_reuse_passed"], result["result"]


@pytest.mark.parametrize("kind,code", [
    ("door", "DOOR_INSTALLATION_DIRECT_BODY_UNSUPPORTED"),
    ("window", "WINDOW_INSTALLATION_MAPPED_BODY_REQUIRED"),
])
def test_direct_polygon_body_without_type_map_is_not_a_supported_reference(kind, code):
    _, reference = polygon_scene(kind, mapped=False)
    function = public_door_installation_anchor if kind == "door" else public_window_installation_anchor
    with pytest.raises(ValueError, match=code):
        function(reference)
