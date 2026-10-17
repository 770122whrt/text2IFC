"""Frozen capability-contract family; fake Provider output is not model evidence."""
import hashlib
import json

import pytest

from text2ifc_agent.prompt_registry import PROJECT_ROOT, load_prompt_registry
from text2ifc_ifc_repair import scene_grounding as grounding
from text2ifc_ifc_repair.public_geometry import calibrate_request_geometry
from tests.ifc_repair.test_scene_grounding import QueueProvider, run
from tests.ifc_repair.test_public_request_geometry import WINDOW, window_facts


def test_rendered_catalog_exposes_exact_geometry_roles_before_first_model_call(tmp_path):
    provider = QueueProvider([{"kind": "query", "query": {"ids": ["wall"]}}])
    run(tmp_path, provider, max_rounds=1)
    inputs = json.loads((tmp_path / "round-001/renderer-input.json").read_text(encoding="utf-8"))
    catalog = {item["operation_type"]: item for item in inputs["SUPPORTED_OPERATIONS"]}
    window = catalog["add_window_with_opening_to_wall"]["public_geometry_capability"]
    assert window["compiler_version"] == "text2ifc/public-request-geometry/0.3"
    assert window["product_geometry"] == "copy_exact_public_reference_body"
    assert window["required_representation"] == "mapped_type_representation_required"
    assert window["opening_geometry"] == "copy_reference_opening_preserving_relative_pose"
    assert window["binding_roles"] == {"target_id": "public_host_wall", "reference_id": "public_reference_occurrence"}
    assert window["relative_rotation_degrees"] == {"height_axis": [0, 180, -180], "thickness_axis": [0], "width_axis": [0]}
    assert "explicit_original_request_clause" in window["required_authority"]
    assert "verified_public_geometry_and_compatible_host" in window["required_authority"]
    door = catalog["fill_existing_opening_with_door"]["public_geometry_capability"]
    assert door["opening_geometry"] == "retain_existing_opening_unchanged"
    assert door["required_representation"] == "mapped_type_or_supported_direct_body_reuse"
    assert door["binding_roles"]["target_id"] == "public_existing_opening"
    new_door = catalog["add_door_with_opening_to_wall"]["public_geometry_capability"]
    assert new_door["exact_reference_copy_supported"] is True
    assert new_door["required_representation"] == "mapped_type_or_supported_direct_body_reuse"
    assert new_door["opening_geometry"] == "copy_reference_opening_preserving_relative_pose"
    assert new_door["binding_roles"]["target_id"] == "public_host_wall"
    assert new_door["relative_rotation_degrees"] == window["relative_rotation_degrees"]
    assert "upright_product_and_opening" in new_door["limits"]
    assert "reference_axes_parallel_to_straight_host" in new_door["limits"]
    assert "public_geometry_capability" not in catalog["set_occurrence_properties"]
    beam = catalog['add_beam']['public_geometry_capability']
    assert beam['required_representation'] == 'single_body_single_rectangular_extruded_area_solid'
    assert 'same_orientation' in beam['limits']
    assert "occurrence_reuse_intent" in provider.calls[0]["prompt"]
    assert "Do not invent a separate operation" in provider.calls[0]["prompt"]
    assert "For add_door_with_opening_to_wall" in provider.calls[0]["prompt"]
    assert "new copied Door opening remains a limitation" not in provider.calls[0]["prompt"]


@pytest.mark.parametrize("angles", ["90度、0度、0度", "180度、1度、0度", "180度、0度、1度"])
def test_catalog_does_not_extend_unsupported_rotation(angles):
    text = WINDOW.replace("朝向与参照相同", "朝向相对参照，按自身高、厚、宽轴依次旋转" + angles)
    with pytest.raises(ValueError, match="PUBLIC_GEOMETRY_REFERENCE_ROTATION_UNSUPPORTED"):
        calibrate_request_geometry({"operation_id": "w", "operation_type": "add_window_with_opening_to_wall", "parameters": {}},
                                   {"target_id": "wall", "reference_id": "peer"}, window_facts(), text)


@pytest.mark.parametrize("mutation,error", [("missing_reference", "EXACT_REFERENCE_REQUIRED"),
    ("missing_authorization", "EXACT_REFERENCE_REQUIRED"), ("wrong_reference_class", "REFERENCE_CLASS_MISMATCH")])
def test_capability_description_never_supplies_missing_authority(mutation, error):
    operation = {"operation_id": "w", "operation_type": "add_window_with_opening_to_wall", "parameters": {}}
    binding = {"target_id": "wall", "reference_id": "peer"}
    text = WINDOW
    if mutation == "missing_reference":
        binding.pop("reference_id")
    elif mutation == "missing_authorization":
        text = text.replace("完整形状复制参照", "外观参考")
    else:
        operation["operation_type"] = "add_door_with_opening_to_wall"
        text = text.replace("补建一扇窗", "补建一扇门").replace("IfcWindow", "IfcDoor")
    with pytest.raises(ValueError, match="PUBLIC_GEOMETRY_" + error):
        calibrate_request_geometry(operation, binding, window_facts(), text)


def test_prompt_upgrade_keeps_response_contract_and_frozen_prompt_bytes():
    registry = load_prompt_registry()
    frozen = PROJECT_ROOT / registry["ifc-scene-grounding.v0.4"]["path"]
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == "5a2b93ec4d26f1a85f73443bcfc0a1ac44137e294a005c0b5d9c56c4ea33ec71"
    v05 = PROJECT_ROOT / registry["ifc-scene-grounding.v0.5"]["path"]
    assert hashlib.sha256(v05.read_bytes()).hexdigest() == "2b36bd7b9e87efe9aa281b2c5ffbbd4eda06686d29674a7ce1a63c5d2c95b7b4"
    v06 = PROJECT_ROOT / registry['ifc-scene-grounding.v0.6']['path']
    assert hashlib.sha256(v06.read_bytes()).hexdigest() == 'b45c062243c86c691a1037658910f2bff587c260b3d1ce09bcf9d3d6bee3dc2b'
    assert grounding.TEMPLATE_ID == "ifc-scene-grounding.v0.7"
    assert grounding.SCENE_GROUNDING_VERSION == "text2ifc/ifc-scene-grounding/0.7"
    assert grounding.load_scene_response_schema()["$id"].endswith("/0.4")


def test_previous_saved_scene_method_requires_its_frozen_runtime():
    from text2ifc_ifc_repair.api import _context_scene_mode
    from text2ifc_ifc_repair.run_models import RunStoreError
    with pytest.raises(RunStoreError, match="no implicit migration"):
        _context_scene_mode({"scene_grounding_version": "text2ifc/ifc-scene-grounding/0.5"})
    assert _context_scene_mode({"scene_grounding_version": grounding.SCENE_GROUNDING_VERSION})


def test_public_api_does_not_coerce_reported_unregistered_request(tmp_path):
    from text2ifc_ifc_repair.api import RepairAPI
    from tests.ifc_repair.test_spatial_grounding import body
    from tests.ifc_repair.test_window_installation_anchor import scene
    model, *_ = scene()
    source = tmp_path / "public.ifc"
    model.write(str(source))
    original = source.read_bytes()
    intent = body()
    intent["operations"] = []
    intent["unsupported_requests"] = [{"unsupported_id": "exact_window_opening_geometry_copy",
        "kind": "unregistered_action", "operation_id": None, "capability_id": "unregistered_operation",
        "source": intent["provenance"][0]}]
    provider = QueueProvider([{"kind": "intent", "intent": intent, "bindings": []}])
    api = RepairAPI(tmp_path / "run", provider=provider, scene_grounding=True)
    result = api.start(source, "A repair request reported as unsupported by the offline fixture.")
    assert result.status == "unsupported", result.to_dict()
    assert len(provider.calls) == 1
    assert "successful_ifc" not in result.artifacts
    assert source.read_bytes() == original
