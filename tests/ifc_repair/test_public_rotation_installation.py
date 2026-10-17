"""Frozen offline rotation family; only independently authored public IFC."""
import hashlib
import json

import ifcopenshell
import ifcopenshell.util.placement
import numpy as np
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.public_geometry import calibrate_request_geometry
from tests.ifc_repair.test_public_request_geometry import window_facts, WINDOW
from tests.ifc_repair.test_window_installation_anchor import scene, PublicWindowProvider


def request(yaw=180):
    # Reference base is 45 mm on the negative side of the wall centre.
    # A half turn about its base reflects the public opening offset too.
    normal = 120 if yaw == 180 else 30
    return (f'1. 补建一扇窗：归属楼层「Ground」。宿主墙「Public straight host」。'
        f'放置基点距墙长度起端2400毫米，距墙厚度负向侧{normal}毫米，高出墙底700毫米。'
        '完整形状复制参照：楼层「Ground」的现存IfcWindow「Public reference window」。'
        f'朝向相对参照，按自身高、厚、宽轴依次旋转{yaw}度、0度、0度。'
        '洞口复制参照构件所填洞口，保持与新构件相同的相对位置和朝向；在宿主墙上建立洞口并建立门窗填充关系。')


class RotationProvider(PublicWindowProvider):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def generate_candidate(self, **kwargs):
        value = json.loads(super().generate_candidate(**kwargs).text)
        if value.get('kind') == 'intent':
            value['intent']['operations'][0]['provenance'][0]['excerpt'] = self.text
        return ProviderOutput(text=json.dumps(value), metadata={'model': 'offline-public-rotation',
                                                               'evidence_class': 'deterministic_fake'})


@pytest.mark.parametrize('yaw,angle,millimetres,sign', [
    (180, 0, False, -1), (180, 37, True, -1),
    (180, 90, False, 1), (0, 180, True, -1),
])
def test_public_api_applies_exact_reference_pose_and_copied_opening(tmp_path, yaw, angle, millimetres, sign):
    model, wall, original_opening, reference, _, unit = scene(
        angle=angle, millimetres=millimetres, sign=float(sign), extension=25.)
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    text = request(yaw)
    api = RepairAPI(tmp_path / 'run', provider=RotationProvider(text), scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'succeeded', result.to_dict()
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / result.artifacts['successful_ifc']))
    window = next(w for w in repaired.by_type('IfcWindow') if w.GlobalId != reference.GlobalId)
    actual = ifcopenshell.util.placement.get_local_placement(window.ObjectPlacement)
    ref_pose = ifcopenshell.util.placement.get_local_placement(reference.ObjectPlacement)
    expected_rotation = ref_pose[:3, :3] @ np.diag([-1., -1., 1.] if yaw == 180 else [1., 1., 1.])
    expected_base = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement) @ [
        2400 * unit, (45 if yaw == 180 else -45) * unit, 700 * unit, 1.]
    assert actual[:3, :3] == pytest.approx(expected_rotation, abs=1e-8)
    assert actual[:3, 3] / unit == pytest.approx(expected_base[:3] / unit, abs=.001)
    expected_relative = np.linalg.inv(ref_pose) @ ifcopenshell.util.placement.get_local_placement(original_opening.ObjectPlacement)
    opening = window.FillsVoids[0].RelatingOpeningElement
    actual_relative = np.linalg.inv(actual) @ ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement)
    assert actual_relative[:3, :3] == pytest.approx(expected_relative[:3, :3], abs=1e-8)
    assert actual_relative[:3, 3] / unit == pytest.approx(expected_relative[:3, 3] / unit, abs=.001)
    assert source.read_bytes() and hashlib.sha256(source.read_bytes()).hexdigest() == digest
    from text2ifc_ifc_repair.public_geometry import public_geometry_check
    context = json.loads((api.store.runs_root / result.run_id / 'api-context.json').read_text(encoding='utf-8'))
    args = dict(requirement=context['public_geometry_requirements']['offline-window-0'],
        repair_request=text, damaged_model=model, repaired_model=repaired,
        roles={'window': window.GlobalId, 'opening': opening.GlobalId})
    assert public_geometry_check(**args).status.value == 'passed'
    if yaw == 0:
        from text2ifc_ifc_repair.public_geometry import LEGACY_VERSION, _CurrentIfcFacts
        legacy_text = text.replace('朝向相对参照，按自身高、厚、宽轴依次旋转0度、0度、0度', '朝向与参照相同')
        legacy = calibrate_request_geometry({'operation_id': 'offline-window-0',
            'operation_type': 'add_window_with_opening_to_wall', 'parameters': {}},
            {'target_id': wall.GlobalId, 'reference_id': reference.GlobalId},
            _CurrentIfcFacts(model, (wall.GlobalId, reference.GlobalId)), legacy_text, version=LEGACY_VERSION)
        assert 'placement_world_mm' not in legacy
        assert public_geometry_check(**{**args, 'requirement': legacy, 'repair_request': legacy_text}).status.value == 'passed'
    window.ObjectPlacement.RelativePlacement.RefDirection.DirectionRatios = tuple(-v for v in window.ObjectPlacement.RelativePlacement.RefDirection.DirectionRatios)
    assert public_geometry_check(**args).status.value == 'failed'


@pytest.mark.parametrize('angles', ['90度、0度、0度', '180度、1度、0度', '180度、0度、1度'])
def test_unsupported_relative_rotation_fails_before_application(angles):
    text = WINDOW.replace('朝向与参照相同', '朝向相对参照，按自身高、厚、宽轴依次旋转' + angles)
    with pytest.raises(ValueError, match='PUBLIC_GEOMETRY_REFERENCE_ROTATION_UNSUPPORTED'):
        calibrate_request_geometry({'operation_id': 'w', 'operation_type': 'add_window_with_opening_to_wall',
            'parameters': {}}, {'target_id': 'wall', 'reference_id': 'peer'}, window_facts(), text)


def test_door_unscoped_nominal_attributes_use_door_semantic_scope(tmp_path):
    from tests.ifc_repair.test_door_installation_anchor import scene as door_scene, PublicOnlyProvider
    class NominalDoorProvider(PublicOnlyProvider):
        def generate_candidate(self, **kwargs):
            output = super().generate_candidate(**kwargs)
            value = json.loads(output.text)
            if value.get('kind') == 'intent':
                op = value['intent']['operations'][0]
                op['attribute_intents'] = [{'intent_kind': 'attribute', 'name': name, 'value': number,
                    'source': op['provenance'][0]} for name, number in [('OverallWidth', 900.), ('OverallHeight', 2100.)]]
            return ProviderOutput(text=json.dumps(value), metadata=output.metadata)
    model, _, _, _, _ = door_scene()
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    api = RepairAPI(tmp_path / 'run', provider=NominalDoorProvider(), scene_grounding=True)
    result = api.start(
        source, 'Fill the empty opening with a 900 by 2100 mm door, using the retained public reference.')
    assert result.status == 'succeeded', result.to_dict()
    from text2ifc_ifc_repair.apply import apply_changeset
    from text2ifc_ifc_repair.operations import create_default_registry
    changeset = json.loads((api.store.runs_root / result.run_id / 'changeset.json').read_text(encoding='utf-8'))
    for assignment in changeset['operations'][0]['semantic_assignments']:
        assignment['scope'] = 'window_occurrence'
    rejected = apply_changeset(damaged_ifc_path=source,
        repair_request='Fill the empty opening with a 900 by 2100 mm door, using the retained public reference.',
        changeset=changeset, output_path=tmp_path / 'invalid-scope.ifc', registry=create_default_registry())
    assert not rejected['valid'] and not (tmp_path / 'invalid-scope.ifc').exists()
    assert any(issue['code'] == 'SCHEMA_VALIDATION_ERROR' and 'scope' in issue['message']
               for issue in rejected['issues'])


@pytest.mark.parametrize('yaw,angle,millimetres', [(180, 0, False), (180, 37, True), (0, 90, True)])
def test_public_door_rotation_preserves_retained_opening(tmp_path, yaw, angle, millimetres):
    from tests.ifc_repair.test_door_installation_anchor import scene as door_scene, PublicOnlyProvider
    class DoorRotationProvider(PublicOnlyProvider):
        def generate_candidate(self, **kwargs):
            output = super().generate_candidate(**kwargs)
            value = json.loads(output.text)
            if value.get('kind') == 'query':
                value['query']['ifc_classes'].append('IfcWall')
            elif value.get('kind') == 'intent':
                value['intent']['operations'][0]['provenance'][0]['excerpt'] = text
            return ProviderOutput(text=json.dumps(value), metadata=output.metadata)
    model, retained, reference, _, unit = door_scene(angle=angle, millimetres=millimetres)
    text = ('1. 补建一扇门：归属楼层「Ground」。宿主墙「Public host」。'
        f'放置基点距墙长度起端{1400 if yaw == 180 else 500}毫米，距墙厚度负向侧75毫米，高出墙底0毫米。'
        '完整形状复制参照：楼层「Ground」的现存IfcDoor「Public reference」。'
        f'朝向相对参照，按自身高、厚、宽轴依次旋转{yaw}度、0度、0度。'
        '保留现有洞口：距墙长度起端500毫米，距墙厚度负向侧0毫米，高出墙底0毫米；将新构件填入并建立门窗填充关系。')
    source = tmp_path / 'door.ifc'
    model.write(str(source))
    before = source.read_bytes()
    api = RepairAPI(tmp_path / 'run', provider=DoorRotationProvider(), scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'succeeded', result.to_dict()
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / result.artifacts['successful_ifc']))
    door = next(d for d in repaired.by_type('IfcDoor') if d.GlobalId != reference.GlobalId)
    assert door.FillsVoids[0].RelatingOpeningElement.GlobalId == retained.GlobalId
    actual = ifcopenshell.util.placement.get_local_placement(door.ObjectPlacement)
    ref = ifcopenshell.util.placement.get_local_placement(reference.ObjectPlacement)
    assert actual[:3, :3] == pytest.approx(ref[:3, :3] @ np.diag([-1., -1., 1.] if yaw == 180 else [1., 1., 1.]), abs=1e-8)
    original_opening = ifcopenshell.util.placement.get_local_placement(retained.ObjectPlacement)
    assert ifcopenshell.util.placement.get_local_placement(repaired.by_guid(retained.GlobalId).ObjectPlacement) == pytest.approx(original_opening)
    assert source.read_bytes() == before


def test_legacy_manifest_primary_scope_preserves_versioned_explicit_scopes():
    from dataclasses import replace
    from tests.ifc_repair.test_semantic_authoring import valid_manifest
    from text2ifc_ifc_repair.semantic_authoring import parse_semantic_manifest, semantic_manifest_expected_facts
    legacy = parse_semantic_manifest(valid_manifest())
    assert {f.occurrence_scope for f in semantic_manifest_expected_facts(legacy)} == {'window_occurrence'}
    assert {f.occurrence_scope for f in semantic_manifest_expected_facts(legacy, primary_scope='door_occurrence')} == {'door_occurrence'}
    scoped = replace(legacy, schema_version='text2ifc/ifc-repair-semantic-manifest/0.3',
        assignments=tuple(replace(a, scope='opening_occurrence') for a in legacy.assignments))
    assert {f.occurrence_scope for f in semantic_manifest_expected_facts(scoped, primary_scope='door_occurrence')} == {'opening_occurrence'}
