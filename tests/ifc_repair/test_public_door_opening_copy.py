"""Frozen exact Door/Opening copy family: synthetic public IFC and fake Provider.

Before the fix, positive cases stop at DOOR_OPENING_COPY_UNSUPPORTED. The
extended cutter distinguishes a copied opening from a regenerated wall box.
Mapped and direct Body scenes are independent authored public fixture families.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import numpy as np
import pytest

from scripts.ifc_repair.repair_comparison.ours_adapter import _draft, _section, fixture_intent
from tests.ifc_repair.test_door_installation_anchor import scene
from tests.ifc_repair.test_scene_repair_api import scene_query_pages
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.public_geometry import calibrate_request_geometry, public_geometry_check


def request(*, yaw=0, x=2200, normal=75, wall_name="Public host", reference_name="Public reference"):
    return (f'1. 补建一扇门：归属楼层「Ground」。宿主墙「{wall_name}」。'
        f'放置基点距墙长度起端{x}毫米，距墙厚度负向侧{normal}毫米，高出墙底0毫米。'
        f'完整形状复制参照：楼层「Ground」的现存IfcDoor「{reference_name}」。'
        f'朝向相对参照，按自身高、厚、宽轴依次旋转{yaw}度、0度、0度。'
        '洞口复制参照构件所填洞口，保持与新构件相同的相对位置和朝向；在宿主墙上建立洞口并建立门窗填充关系。')


class CopyDoorProvider:
    def __init__(self, text, *, unoffered=False, target_id=None, reference_id=None):
        self.text, self.unoffered, self.calls = text, unoffered, []
        self.target_id, self.reference_id = target_id, reference_id

    def generate_candidate(self, **kw):
        self.calls.append(kw)
        prompt = kw['prompt']
        if '## Immutable bindings' in prompt:
            value = _draft(prompt, kw.get('schema') or _section(prompt, 'Draft schema'))
        else:
            pages = scene_query_pages(prompt)
            if not pages:
                query = ({'ids': [self.target_id, self.reference_id]} if self.target_id else
                         {'ifc_classes': ['IfcWall', 'IfcDoor']})
                value = {'kind': 'query', 'query': query}
            else:
                rows = pages[0]['records']
                reference = next(row for row in rows if row['ifc_class'] == 'IfcDoor')
                target = next(row for row in rows if row['ifc_class'] in {'IfcWall', 'IfcWallStandardCase'}
                              and (row['id'] == self.target_id or row['name'] in self.text))
                body = fixture_intent('door', {'allowed_ifc_classes': ['IfcWall']}, {
                    'position': {'reference': 'wall_local_start', 'center_offset_mm': 2650},
                    'opening': {'width_mm': 900, 'height_mm': 2100, 'sill_height_mm': 0,
                                'dimension_meaning': 'overall_opening'},
                    'door': {'operation_type': reference['type_summary']['formal_attributes']['OperationType'],
                             'formal_enum_explicit': False}})
                op = body['operations'][0]
                op['operation_type'] = 'add_door_with_opening_to_wall'
                op['routing_intent'].update(action='add_with_opening', operation_profile='door.add-with-opening.v0.4')
                op['provenance'][0]['excerpt'] = self.text
                op['prototype_intent'] = {'reference_kind': 'global_id', 'reference': reference['type_id'],
                                         'source': deepcopy(op['provenance'][0])}
                value = {'kind': 'intent', 'intent': body, 'bindings': [{
                    'operation_id': op['operation_id'], 'target_id': target['id'],
                    'reference_id': 'unoffered' if self.unoffered else reference['id']}]}
        return ProviderOutput(text=json.dumps(value), metadata={'provider': 'fixture',
            'model': 'offline-copied-door-opening', 'evidence_class': 'deterministic_fake',
            'network_transport_attempted': False})


@pytest.mark.parametrize('yaw,angle,millimetres,sign', [
    (0, 0, False, 1), (180, 37, True, 1), (0, 90, False, -1),
])
def test_public_api_copies_door_and_extended_opening(tmp_path, yaw, angle, millimetres, sign):
    model, retained, reference, _, unit = scene(angle=angle, millimetres=millimetres, sign=float(sign))
    wall = retained.VoidsElements[0].RelatingBuildingElement
    ref_opening = reference.FillsVoids[0].RelatingOpeningElement
    ref_opening.Representation.Representations[0].Items[0].SweptArea.YDim = 190 * unit
    effective_sign = sign * (-1 if yaw else 1)
    x = 2200 if effective_sign > 0 else 3100
    text = request(yaw=yaw, x=x)
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    api = RepairAPI(tmp_path / 'run', provider=CopyDoorProvider(text), scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'succeeded', result.to_dict()
    assert api.read_result(result.run_id).successful_artifact_publishable
    root = api.store.runs_root / result.run_id
    repaired = ifcopenshell.open(str(root / result.artifacts['successful_ifc']))
    door = next(d for d in repaired.by_type('IfcDoor') if d.GlobalId != reference.GlobalId)
    opening = door.FillsVoids[0].RelatingOpeningElement
    assert opening.GlobalId not in {o.GlobalId for o in model.by_type('IfcOpeningElement')}
    assert opening.VoidsElements[0].RelatingBuildingElement.GlobalId == wall.GlobalId
    assert ifcopenshell.util.element.get_type(door).GlobalId == ifcopenshell.util.element.get_type(reference).GlobalId
    pose = ifcopenshell.util.placement.get_local_placement(door.ObjectPlacement)
    ref_pose = ifcopenshell.util.placement.get_local_placement(reference.ObjectPlacement)
    expected = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement) @ [x * unit, 75 * unit, 0, 1]
    assert pose[:3, 3] / unit == pytest.approx(expected[:3] / unit, abs=.001)
    assert pose[:3, :3] == pytest.approx(ref_pose[:3, :3] @ np.diag([-1, -1, 1] if yaw else [1, 1, 1]), abs=1e-8)
    expected_relative = np.linalg.inv(ref_pose) @ ifcopenshell.util.placement.get_local_placement(ref_opening.ObjectPlacement)
    actual_relative = np.linalg.inv(pose) @ ifcopenshell.util.placement.get_local_placement(opening.ObjectPlacement)
    assert actual_relative == pytest.approx(expected_relative, abs=1e-7)
    assert opening.Representation.Representations[0].Items[0].SweptArea.YDim / unit == pytest.approx(190)
    context = json.loads((root / 'api-context.json').read_text(encoding='utf-8'))
    args = dict(requirement=context['public_geometry_requirements']['offline-repair'], repair_request=text,
                damaged_model=model, repaired_model=repaired, roles={'door': door.GlobalId, 'opening': opening.GlobalId})
    assert public_geometry_check(**args).status.value == 'passed'
    # Same location and wall cut, but a regenerated shallow cutter is not exact.
    opening.Representation.Representations[0].Items[0].SweptArea.YDim = 150 * unit
    assert public_geometry_check(**args).status.value == 'failed'
    assert source.read_bytes() == before


@pytest.mark.parametrize('fault,error', [('wrong_class', 'REFERENCE_CLASS_MISMATCH'),
    ('missing_reference', 'EXACT_REFERENCE_REQUIRED'), ('outside_host', 'OPENING_OUTSIDE_HOST')])
def test_copied_door_binding_rejects_unauthorized_or_incompatible_facts(fault, error):
    from tests.ifc_repair.test_public_request_geometry import window_facts, WINDOW
    facts = window_facts()
    if fault != 'wrong_class':
        facts.records[1]['ifc_class'] = 'IfcDoor'
    text = WINDOW.replace('一扇窗', '一扇门').replace('IfcWindow', 'IfcDoor')
    if fault == 'outside_host':
        text = text.replace('起端3000毫米', '起端10000毫米')
    binding = {'target_id': 'wall', 'reference_id': 'peer'}
    if fault == 'missing_reference':
        binding.pop('reference_id')
    with pytest.raises(ValueError, match='PUBLIC_GEOMETRY_' + error):
        calibrate_request_geometry({'operation_id': 'd', 'operation_type': 'add_door_with_opening_to_wall',
                                    'parameters': {}}, binding, facts, text)


def test_unoffered_door_copy_reference_never_publishes(tmp_path):
    model, *_ = scene()
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    text = request()
    api = RepairAPI(tmp_path / 'run', provider=CopyDoorProvider(text, unoffered=True), scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'provider_failed'
    assert not result.successful_artifact_publishable
    assert 'successful_ifc' not in result.artifacts
    assert source.read_bytes() == before


def test_direct_brep_door_and_nonrectangular_cutter_copy_cross_scene(tmp_path):
    from tests.ifc_repair.test_door_direct_body_reference import brep_scene
    model, target, reference, unit = brep_scene(millimetres=True)
    wall = target.VoidsElements[0].RelatingBuildingElement
    ref_opening = reference.FillsVoids[0].RelatingOpeningElement
    solid = ref_opening.Representation.Representations[0].Items[0]
    points = [model.createIfcCartesianPoint((float(x) * unit, float(y) * unit))
              for x, y in ((0, 0), (900, 0), (900, 150), (40, 150), (0, 110), (0, 0))]
    solid.SweptArea = model.createIfcArbitraryClosedProfileDef('AREA', None,
                                                             model.createIfcPolyline(points))
    text = request(normal=100, wall_name=wall.Name, reference_name=reference.Name)
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    api = RepairAPI(tmp_path / 'run', provider=CopyDoorProvider(text), scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'succeeded', result.to_dict()
    root = api.store.runs_root / result.run_id
    repaired = ifcopenshell.open(str(root / result.artifacts['successful_ifc']))
    door = next(d for d in repaired.by_type('IfcDoor') if d.GlobalId != reference.GlobalId)
    opening = door.FillsVoids[0].RelatingOpeningElement
    assert opening.VoidsElements[0].RelatingBuildingElement.GlobalId == wall.GlobalId
    assert opening.Representation.Representations[0].Items[0].SweptArea.is_a('IfcArbitraryClosedProfileDef')
    context = json.loads((root / 'api-context.json').read_text(encoding='utf-8'))
    assert public_geometry_check(requirement=context['public_geometry_requirements']['offline-repair'],
        repair_request=text, damaged_model=model, repaired_model=repaired,
        roles={'door': door.GlobalId, 'opening': opening.GlobalId}).status.value == 'passed'
    assert source.read_bytes() == before


def test_copied_opening_application_failure_never_publishes(tmp_path, monkeypatch):
    from text2ifc_ifc_repair import public_geometry
    original = public_geometry.place_public_product

    def fail_door(product, parent, placement_world_mm):
        if product.is_a('IfcDoor'):
            raise ValueError('OFFLINE_INJECTED_DOOR_PLACEMENT_FAILURE')
        return original(product, parent, placement_world_mm)

    monkeypatch.setattr(public_geometry, 'place_public_product', fail_door)
    model, *_ = scene()
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    text = request()
    api = RepairAPI(tmp_path / 'run', provider=CopyDoorProvider(text), scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'application_failed', result.to_dict()
    assert not result.successful_artifact_publishable
    assert 'successful_ifc' not in result.artifacts
    assert not list((tmp_path / 'run').rglob('repaired.ifc'))
    assert source.read_bytes() == before


def test_revealed_formal030_public_pair_offline_api(tmp_path):
    """Revealed public-only regression; no private facts or live inference."""
    import ifcopenshell.geom
    import ifcopenshell.util.unit
    public = Path(__file__).resolve().parents[2] / (
        'dataset/processed/ifc-repair/formal-40-pairs-25-20261010/public/cases/formal-030-d001-world')
    hashes = {'model.ifc': '338978fd473d80ea4d1e2233f0d161534778b72847af277c7046d48481a1a184',
              'request.txt': 'd56b5a3a484fb8f725f76d331d21d1f051cecb0df1e679dc25154b5102aaa28a'}
    if not all((public / name).is_file() for name in hashes):
        pytest.skip('Local frozen public pair unavailable; skipped execution is not admission')
    for name, digest in hashes.items():
        assert hashlib.sha256((public / name).read_bytes()).hexdigest() == digest
    text = (public / 'request.txt').read_text(encoding='utf-8')
    source = tmp_path / 'public.ifc'
    source.write_bytes((public / 'model.ifc').read_bytes())
    model = ifcopenshell.open(str(source))
    scale = ifcopenshell.util.unit.calculate_unit_scale(model) * 1000
    vector = r'（([-\d.]+)，([-\d.]+)，([-\d.]+)）'
    ref_point = np.array([float(v) * 1000 for v in re.search('现存IfcDoor世界基点' + vector, text).groups()])
    reference = [door for door in model.by_type('IfcDoor') if np.allclose(
        ifcopenshell.util.placement.get_local_placement(door.ObjectPlacement)[:3, 3] * scale,
        ref_point, atol=1, rtol=0)]
    target_bounds = np.array([float(v) * 1000 for v in re.search(
        '宿主墙未扣洞口的整体范围为' + vector + '至' + vector + '米', text).groups()]).reshape(2, 3)
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, True)
    settings.set('context-identifiers', ['Body'])
    targets = []
    for wall in model.by_type('IfcWall'):
        shape = ifcopenshell.geom.create_shape(settings, wall)
        vertices = np.asarray(shape.geometry.verts).reshape(-1, 3) * 1000
        if np.allclose([vertices.min(axis=0), vertices.max(axis=0)], target_bounds, atol=1, rtol=0):
            targets.append(wall)
    assert len(reference) == len(targets) == 1
    provider = CopyDoorProvider(text, target_id=targets[0].GlobalId, reference_id=reference[0].GlobalId)
    api = RepairAPI(tmp_path / 'run', provider=provider, scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'succeeded', (result.status, result.reason_code)
    assert api.read_result(result.run_id).successful_artifact_publishable
    assert len(provider.calls) == 3
    assert hashlib.sha256(source.read_bytes()).hexdigest() == hashes['model.ifc']
    assert hashlib.sha256((public / 'model.ifc').read_bytes()).hexdigest() == hashes['model.ifc']


@pytest.mark.parametrize('fault', ['reference_origin', 'host_uncut_bounds'])
def test_literal_world_identity_constraints_reject_wrong_public_binding(fault):
    from text2ifc_ifc_repair.public_geometry import _CurrentIfcFacts
    model, retained, reference, _, _ = scene()
    wall = retained.VoidsElements[0].RelatingBuildingElement
    text = request().replace('宿主墙「Public host」',
        '宿主墙未扣洞口的整体范围为（1，2，0）至（7，2.15，3）米').replace(
        '楼层「Ground」的现存IfcDoor「Public reference」', '现存IfcDoor世界基点（4.5，2.075，0）米')
    if fault == 'reference_origin':
        text = text.replace('（4.5，2.075，0）', '（4.51，2.075，0）')
    else:
        text = text.replace('（7，2.15，3）', '（7.01，2.15，3）')
    with pytest.raises(ValueError, match='PUBLIC_GEOMETRY_REFERENCE_OR_HOST_BINDING_MISMATCH'):
        calibrate_request_geometry({'operation_id': 'door', 'operation_type': 'add_door_with_opening_to_wall',
            'parameters': {}}, {'target_id': wall.GlobalId, 'reference_id': reference.GlobalId},
            _CurrentIfcFacts(model, (wall.GlobalId, reference.GlobalId)), text)


def test_world_host_constraint_uses_uncut_mesh_and_existing_millimetre_tolerance():
    from text2ifc_ifc_repair.public_geometry import _CurrentIfcFacts
    model, retained, reference, _, unit = scene()
    wall = retained.VoidsElements[0].RelatingBuildingElement
    # The existing empty cutter removes the full-height right edge. The
    # request expressly identifies the uncut wall, whose endpoint is 7 m.
    retained.ObjectPlacement.RelativePlacement.Location.Coordinates = (5500 * unit, 0., 0.)
    retained.Representation.Representations[0].Items[0].Depth = 3000 * unit
    text = request().replace('宿主墙「Public host」',
        '宿主墙未扣洞口的整体范围为（1，2，0）至（7.0005，2.15，3）米').replace(
        '楼层「Ground」的现存IfcDoor「Public reference」', '现存IfcDoor世界基点（4.5005，2.075，0）米')
    result = calibrate_request_geometry({'operation_id': 'door',
        'operation_type': 'add_door_with_opening_to_wall', 'parameters': {}},
        {'target_id': wall.GlobalId, 'reference_id': reference.GlobalId},
        _CurrentIfcFacts(model, (wall.GlobalId, reference.GlobalId)), text)
    assert result['host_id'] == wall.GlobalId
    assert result['reference_id'] == reference.GlobalId
