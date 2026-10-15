"""Frozen synthetic public beam family; no private original or live Provider."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.util.placement
import ifcopenshell.util.element
import numpy as np
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_ifc_repair.operations.structural_member import create_straight_rectangular_member
from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent, _draft, _section
from tests.ifc_repair.test_window_installation_anchor import scene


REQUEST = ('1. 补建一根梁：归属楼层「Ground」。放置基点世界坐标为（12，3，4）米。'
           '完整形状复制参照：现存IfcBeam世界基点（1，2，4）米。朝向与参照相同。')


def beam_scene(*, millimetres=False, swapped=True, angle=0, defect=None):
    m, wall, _, _, _, unit = scene(millimetres=millimetres)
    floor = m.by_type('IfcBuildingStorey')[0]
    a = math.radians(angle)
    floor.ObjectPlacement.RelativePlacement.RefDirection = m.createIfcDirection((math.cos(a), math.sin(a), 0.))
    member = create_straight_rectangular_member(model=m, occurrence_class='IfcBeam',
        occurrence_global_id=ifcopenshell.guid.new(), operation_id='public-reference',
        axis_start_mm=(1000, 2000, 4000), axis_end_mm=(4000, 2000, 4000),
        section={'shape': 'rectangle', 'width_mm': 300, 'height_mm': 800}, storey=floor,
        owner_history=floor.OwnerHistory, representation_context=m.by_type('IfcGeometricRepresentationContext')[0])['occurrence']
    # Keep the occurrence world pose constant while the containing storey rotates.
    member.ObjectPlacement.RelativePlacement.Location.Coordinates = tuple(float(v) for v in np.array([[math.cos(a), math.sin(a), 0], [-math.sin(a), math.cos(a), 0], [0, 0, 1]]) @ np.array([1000, 2000, 4000]) * unit)
    member.ObjectPlacement.RelativePlacement.RefDirection = m.createIfcDirection((math.cos(a), -math.sin(a), 0.))
    solid = member.Representation.Representations[0].Items[0]
    solid.Position.Location.Coordinates = (173 * unit, 27 * unit, -400 * unit)
    solid.SweptArea.Position.Location.Coordinates = (13 * unit, 21 * unit)
    if swapped:
        solid.Position.RefDirection.DirectionRatios = (0., 0., 1.)
        solid.SweptArea.XDim, solid.SweptArea.YDim = 800 * unit, 300 * unit
    from text2ifc_presentation import AppearanceSpec, assign_item_appearance
    assign_item_appearance(m, item=solid, spec=AppearanceSpec('Public beam paint', .2, .3, .4))
    relation = floor.ContainsElements[0]
    relation.RelatedElements = [*relation.RelatedElements, member]
    if defect == 'missing': member.Representation = None
    elif defect == 'multiple': member.Representation.Representations = [member.Representation.Representations[0], member.Representation.Representations[0]]
    elif defect == 'nonrectangle': solid.SweptArea = m.createIfcCircleProfileDef('AREA', None, solid.SweptArea.Position, 100 * unit)
    elif defect == 'duplicate':
        duplicate = m.create_entity('IfcBeam', GlobalId=ifcopenshell.guid.new(), OwnerHistory=floor.OwnerHistory,
            ObjectPlacement=member.ObjectPlacement, Representation=member.Representation)
        relation.RelatedElements = [*relation.RelatedElements, duplicate]
    elif defect == 'opening':
        m.create_entity('IfcRelVoidsElement', GlobalId=ifcopenshell.guid.new(), OwnerHistory=floor.OwnerHistory,
            RelatingBuildingElement=member, RelatedOpeningElement=m.by_type('IfcOpeningElement')[0])
    return m, member, floor


class BeamProvider:
    def __init__(self, request=REQUEST, reference_id=None):
        self.request, self.reference_id = request, reference_id
        self.calls = []

    def generate_candidate(self, **kw):
        self.calls.append(kw)
        prompt = kw['prompt']
        if '## Immutable bindings' in prompt:
            value = _draft(prompt, kw['schema'])
        else:
            from tests.ifc_repair.test_scene_repair_api import scene_query_pages
            pages = scene_query_pages(prompt)
            if not pages:
                query = {'ifc_classes': ['IfcBeam']}
                if self.reference_id: query['ids'] = [self.reference_id]
                value = {'kind': 'query', 'query': query}
            else:
                floor = next(f for f in _section(prompt, 'Current public scene')['storeys']
                             if f['name'] == re.findall(r'归属楼层「([^」]+)」', self.request)[0])
                ref = pages[0]['records'][0]
                body = fixture_intent('window', {'allowed_ifc_classes': ['IfcBuildingStorey']}, {
                    'axis': {'start': {'x_mm': 1, 'y_mm': 2, 'z_mm': 3}, 'end': {'x_mm': 1001, 'y_mm': 2, 'z_mm': 3}},
                    'section': {'shape': 'rectangle', 'width_mm': 1, 'height_mm': 1}})
                op = body['operations'][0]
                op['operation_type'] = 'add_beam'
                op['routing_intent'].update(component_family='beam', action='add', operation_profile='beam.add.v0.3')
                op['provenance'][0]['excerpt'] = self.request
                if ref.get('type_id'):
                    op['prototype_intent'] = {'reference_kind': 'global_id', 'reference': ref['type_id'],
                        'source': deepcopy(op['provenance'][0])}
                value = {'kind': 'intent', 'intent': body, 'bindings': [{'operation_id': op['operation_id'],
                    'target_id': floor['id'], 'reference_id': ref['id']}]}
        return ProviderOutput(text=json.dumps(value), metadata={'model': 'offline-beam', 'evidence_class': 'deterministic_fake'})


@pytest.mark.parametrize('millimetres,swapped,angle', [(False, True, 0), (True, True, 37), (False, False, 90)])
def test_public_api_exact_body_copy_preserves_offsets_and_world_pose(tmp_path, monkeypatch, millimetres, swapped, angle):
    m, reference, floor = beam_scene(millimetres=millimetres, swapped=swapped, angle=angle)
    from text2ifc_ifc_repair.operations import structural_member
    def forbidden_style_mutation(*args, **kwargs):
        raise AssertionError('Shared exact public Body must not be restyled')
    monkeypatch.setattr(structural_member, 'apply_repair_appearance_on_occurrence', forbidden_style_mutation)
    styled = {e.id(): e.to_string() for e in m.by_type('IfcStyledItem')}
    source = tmp_path / 'source.ifc'; m.write(str(source)); before = source.read_bytes()
    api = RepairAPI(tmp_path / 'runs', provider=BeamProvider(), scene_grounding=True)
    result = api.start(source, REQUEST)
    assert result.status == 'succeeded', result.to_dict()
    run = api.store.runs_root / result.run_id
    after = ifcopenshell.open(str(run / result.artifacts['successful_ifc']))
    beam = next(b for b in after.by_type('IfcBeam') if b.GlobalId != reference.GlobalId)
    from text2ifc_ifc_repair.public_beam_copy import measure_beam, body_signature, measure_beam_installation
    assert body_signature(beam) == body_signature(reference)
    assert all(after.by_id(key).to_string() == value for key, value in styled.items())
    assert beam.Representation.id() != after.by_guid(reference.GlobalId).Representation.id()
    assert measure_beam(beam)['section'] == {'shape': 'rectangle', 'width_mm': 300., 'height_mm': 800.}
    context = json.loads((run / 'api-context.json').read_text(encoding='utf-8'))
    requirement = next(iter(context['public_geometry_requirements'].values()))
    assert measure_beam_installation(beam, requirement, reference_model=m)['valid']
    assert source.read_bytes() == before
    report = json.loads((run / result.artifacts['evaluation']).read_text(encoding='utf-8'))
    checks = [c for op in report['operations'] for level in op['levels'] for c in level['checks']]
    assert any(c['check_id'] == 'l2.public-request-geometry' and c['status'] == 'passed' for c in checks)
    from text2ifc_ifc_repair.public_geometry import public_geometry_check
    args = dict(requirement=requirement, repair_request=REQUEST, damaged_model=m, repaired_model=after, roles={'beam': beam.GlobalId})
    assert public_geometry_check(**args).status.value == 'passed'
    # Translate the internal Body while compensating the object placement: an
    # identical world envelope still cannot establish exact local Body copying.
    solid = beam.Representation.Representations[0].Items[0]
    beam.Representation.Representations[0].Items = [ifcopenshell.util.element.copy_deep(after, solid)]
    solid = beam.Representation.Representations[0].Items[0]
    xyz = list(solid.Position.Location.Coordinates); xyz[0] += 10 * (1 if millimetres else .001)
    solid.Position.Location.Coordinates = tuple(xyz)
    assert public_geometry_check(**args).status.value == 'failed'


@pytest.mark.parametrize('defect', ['missing', 'multiple', 'nonrectangle', 'duplicate', 'opening'])
def test_public_reference_unsupported_or_ambiguous_fails_closed(tmp_path, defect):
    m, _, _ = beam_scene(defect=defect)
    source = tmp_path / 'source.ifc'; m.write(str(source)); before = source.read_bytes()
    provider = BeamProvider()
    api = RepairAPI(tmp_path / 'runs', provider=provider, scene_grounding=True)
    result = api.start(source, REQUEST)
    assert result.status != 'succeeded'
    assert not result.successful_artifact_publishable
    assert source.read_bytes() == before
    if defect != 'duplicate':
        assert result.reason_code == 'PUBLIC_GEOMETRY_BEAM_BODY_UNSUPPORTED'
        assert len(provider.calls) == 2


@pytest.mark.parametrize('kind', ['missing_reference', 'legacy_version', 'anchor_outside_tolerance', 'rotation'])
def test_exact_reference_authority_and_legacy_scope_fail_closed(kind):
    from text2ifc_ifc_repair.public_geometry import _CurrentIfcFacts, calibrate_request_geometry, VERSION
    m, reference, floor = beam_scene()
    binding = {'target_id': floor.GlobalId, 'reference_id': reference.GlobalId}
    request, version = REQUEST, VERSION
    if kind == 'missing_reference': binding.pop('reference_id')
    elif kind == 'legacy_version': version = 'text2ifc/public-request-geometry/0.2'
    elif kind == 'anchor_outside_tolerance': request = request.replace('（1，2，4）', '（1.001，2，4）')
    else: request = request.replace('朝向与参照相同', '朝向相对参照，按自身高、厚、宽轴依次旋转90度、0度、0度')
    with pytest.raises(ValueError, match='PUBLIC_GEOMETRY_'):
        calibrate_request_geometry({'operation_id': 'b', 'operation_type': 'add_beam', 'parameters': {}},
            binding, _CurrentIfcFacts(m, (floor.GlobalId, reference.GlobalId)), request, version=version)


def test_reference_anchor_accepts_half_millimetre_public_rounding_boundary():
    from text2ifc_ifc_repair.public_geometry import _CurrentIfcFacts, calibrate_request_geometry
    m, reference, floor = beam_scene()
    request = REQUEST.replace('（1，2，4）', '（1.0005，2，4）')
    result = calibrate_request_geometry({'operation_id': 'b', 'operation_type': 'add_beam', 'parameters': {}},
        {'target_id': floor.GlobalId, 'reference_id': reference.GlobalId},
        _CurrentIfcFacts(m, (floor.GlobalId, reference.GlobalId)), request)
    assert result['reference_id'] == reference.GlobalId


def test_revealed_formal_public_reference_api_regression(tmp_path):
    """Revealed public input regression; not a holdout/capability measurement."""
    public = Path(__file__).resolve().parents[2] / '.tmp/repair-formal-1200-20261011/full/cases/formal-020-d004-world/public'
    source = public / 'model.ifc'
    if not source.is_file() or not (public / 'request.txt').is_file():
        pytest.skip('requires the local frozen formal-020 public fixture; not admission when skipped')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == '1bf0a355205df683960f15878952bfdd35c1ed2c4b32cdae0b891a1aded92d9f'
    request = (public / 'request.txt').read_text(encoding='utf-8')
    original = ifcopenshell.open(str(source))
    reference_id = '3YKw5eLx5EQ8GyWh_7Omdo'
    reference = original.by_guid(reference_id)
    roots = {e.id(): e.to_string() for cls in ('IfcTypeProduct', 'IfcMaterial') for e in original.by_type(cls)}
    api = RepairAPI(tmp_path / 'runs', provider=BeamProvider(request, reference_id), scene_grounding=True)
    result = api.start(source, request)
    assert result.status == 'succeeded', result.to_dict()
    after = ifcopenshell.open(str(api.store.runs_root / result.run_id / result.artifacts['successful_ifc']))
    new_ids = {e.GlobalId for e in after.by_type('IfcBeam')} - {e.GlobalId for e in original.by_type('IfcBeam')}
    assert len(new_ids) == 1
    beam = after.by_guid(new_ids.pop())
    from text2ifc_ifc_repair.public_beam_copy import body_signature, measure_beam
    assert body_signature(beam) == body_signature(reference)
    assert measure_beam(beam)['section'] == {'shape': 'rectangle', 'width_mm': 300., 'height_mm': 812.8}
    pose = ifcopenshell.util.placement.get_local_placement(beam.ObjectPlacement)
    import ifcopenshell.util.unit as units
    assert pose[:3, 3] * units.calculate_unit_scale(after) * 1000 == pytest.approx([-23512, -5187, 9200], abs=.001)
    assert pose[:3, :3] == pytest.approx(ifcopenshell.util.placement.get_local_placement(reference.ObjectPlacement)[:3, :3], abs=1e-7)
    assert all(after.by_id(key).to_string() == value for key, value in roots.items())
    assert body_signature(after.by_guid(reference_id)) == body_signature(reference)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == '1bf0a355205df683960f15878952bfdd35c1ed2c4b32cdae0b891a1aded92d9f'
