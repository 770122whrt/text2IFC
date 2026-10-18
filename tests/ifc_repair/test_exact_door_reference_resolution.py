"""Exact public Door-copy authority must bind its existing Type before resolution.

Frozen missing-prototype family: mapped and direct-Brep independent scenes,
NOTDEFINED retained truth, arbitrary new-door missing operation, mismatched
prototype, and ambiguous public Type. No live inference or private inputs.

Round-01 formal030's structured summary reached a valid Intent in three
grounding rounds, then DOOR_OPERATION_REQUIRED. Its offered reference had a
unique mapped IfcDoorStyle/SINGLE_SWING_RIGHT; the Intent omitted both door
parameters and prototype_intent. That omission is reproduced below without
reading or replaying Provider reasoning.
"""
from copy import deepcopy
import json

import ifcopenshell
import ifcopenshell.util.element
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from tests.ifc_repair.test_door_installation_anchor import scene
from tests.ifc_repair.test_door_direct_body_reference import brep_scene
from tests.ifc_repair.test_public_door_opening_copy import CopyDoorProvider, request


class OmittedDoorSemanticsProvider(CopyDoorProvider):
    def generate_candidate(self, **kwargs):
        from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent
        from tests.ifc_repair.test_scene_repair_api import scene_query_pages
        prompt = kwargs['prompt']
        pages = scene_query_pages(prompt) if '## Immutable bindings' not in prompt else []
        if not pages:
            return super().generate_candidate(**kwargs)
        self.calls.append(kwargs)
        rows = pages[0]['records']
        reference = next(row for row in rows if row['ifc_class'] == 'IfcDoor')
        target = next(row for row in rows if row['ifc_class'] in {'IfcWall', 'IfcWallStandardCase'}
                      and (row['id'] == self.target_id or row['name'] in self.text))
        body = fixture_intent('door', {'allowed_ifc_classes': ['IfcWall']}, {
            'position': {'reference': 'wall_local_start', 'center_offset_mm': 2650},
            'opening': {'width_mm': 900, 'height_mm': 2100, 'sill_height_mm': 0,
                        'dimension_meaning': 'overall_opening'}})
        op = body['operations'][0]
        op['operation_type'] = 'add_door_with_opening_to_wall'
        op['routing_intent'].update(action='add_with_opening', operation_profile='door.add-with-opening.v0.4')
        op['provenance'][0]['excerpt'] = self.text
        op['prototype_intent'] = None
        response = {'kind': 'intent', 'intent': body, 'bindings': [{
            'operation_id': op['operation_id'], 'target_id': target['id'], 'reference_id': reference['id']}]}
        return ProviderOutput(text=json.dumps(response), metadata={'provider': 'fixture',
            'model': 'offline-door-omitted-semantics', 'evidence_class': 'deterministic_fake'})


@pytest.mark.parametrize('kind,operation', [
    ('mapped', 'SINGLE_SWING_RIGHT'), ('mapped', 'NOTDEFINED'), ('direct', 'SINGLE_SWING_LEFT'),
])
def test_exact_public_copy_inherits_reference_type_without_new_swing_question(tmp_path, kind, operation):
    if kind == 'mapped':
        model, retained, reference, _, _ = scene()
        normal = 75
    else:
        model, retained, reference, _ = brep_scene(millimetres=True)
        normal = 100
    wall = retained.VoidsElements[0].RelatingBuildingElement
    style = ifcopenshell.util.element.get_type(reference)
    style.OperationType = operation
    text = request(normal=normal, wall_name=wall.Name, reference_name=reference.Name)
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    provider = OmittedDoorSemanticsProvider(text)
    api = RepairAPI(tmp_path / 'run', provider=provider, scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'succeeded', (result.status, result.reason_code)
    assert result.clarification is None
    assert api.read_result(result.run_id).successful_artifact_publishable
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / result.artifacts['successful_ifc']))
    created = next(d for d in repaired.by_type('IfcDoor') if d.GlobalId != reference.GlobalId)
    assert ifcopenshell.util.element.get_type(created).GlobalId == style.GlobalId
    assert ifcopenshell.util.element.get_type(created).OperationType == operation
    assert source.read_bytes() == before


def test_reference_id_alone_does_not_supply_missing_new_door_operation(tmp_path):
    model, *_ = scene()
    text = 'Add a 900 by 2100 mm door to Public host at 2650 mm from the wall start.'
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    provider = OmittedDoorSemanticsProvider(text)
    api = RepairAPI(tmp_path / 'run', provider=provider, scene_grounding=True)
    result = api.start(source, text)
    assert result.status == 'clarification_required', (result.status, result.reason_code)
    assert result.reason_code == 'DOOR_OPERATION_REQUIRED'
    assert not result.successful_artifact_publishable
    assert source.read_bytes() == before


@pytest.mark.parametrize('fault', ['conflicting_prototype', 'missing_public_type'])
def test_exact_copy_rejects_conflicting_or_unavailable_public_type(fault):
    from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent
    from tests.ifc_repair.test_public_request_geometry import window_facts, WINDOW
    from text2ifc_ifc_repair.spatial_grounding import bind_spatial_intent, GroundingError
    facts = window_facts()
    facts.records[1]['ifc_class'] = 'IfcDoor'
    text = WINDOW.replace('一扇窗', '一扇门').replace('IfcWindow', 'IfcDoor')
    body = fixture_intent('door', {'allowed_ifc_classes': ['IfcWall']}, {})
    op = body['operations'][0]
    op['operation_type'] = 'add_door_with_opening_to_wall'
    op['provenance'][0]['excerpt'] = text
    op['prototype_intent'] = None
    if fault == 'conflicting_prototype':
        op['prototype_intent'] = {'reference_kind': 'global_id', 'reference': 'different-type',
                                  'source': deepcopy(op['provenance'][0])}
    else:
        facts.records[1]['type_id'] = None
    expected = 'SCENE_REFERENCE_TYPE_MISMATCH' if fault == 'conflicting_prototype' else 'SCENE_REFERENCE_TYPE_UNAVAILABLE'
    with pytest.raises(GroundingError, match=expected):
        bind_spatial_intent(body, [{'operation_id': op['operation_id'], 'target_id': 'wall',
                                  'reference_id': 'peer'}], facts, repair_request=text)


@pytest.mark.parametrize('fault', ['no_type', 'multiple_types'])
def test_exact_copy_never_publishes_missing_or_ambiguous_reference_type(tmp_path, fault):
    import ifcopenshell.guid
    model, _, reference, _, _ = scene()
    relation = next(r for r in reference.IsDefinedBy if r.is_a('IfcRelDefinesByType'))
    if fault == 'no_type':
        model.remove(relation)
    else:
        other = ifcopenshell.util.element.copy(model, relation.RelatingType)
        model.createIfcRelDefinesByType(ifcopenshell.guid.new(), reference.OwnerHistory,
                                       None, None, [reference], other)
    text = request()
    source = tmp_path / 'public.ifc'
    model.write(str(source))
    before = source.read_bytes()
    api = RepairAPI(tmp_path / 'run', provider=OmittedDoorSemanticsProvider(text), scene_grounding=True)
    result = api.start(source, text)
    if fault == 'no_type':
        assert (result.status, result.reason_code) == ('provider_failed', 'SCENE_GROUNDING_EXHAUSTED')
        diagnostic = json.loads((api.store.runs_root / result.run_id / 'intent/scene-diagnostics.json').read_text(encoding='utf-8'))
        assert any('SCENE_REFERENCE_TYPE_UNAVAILABLE' in row['issue_codes'] for row in diagnostic['rounds'])
    else:
        assert (result.status, result.reason_code) == ('invalid_input', 'DOOR_INSTALLATION_REFERENCE_TYPE_AMBIGUOUS')
    assert not result.successful_artifact_publishable
    assert 'successful_ifc' not in result.artifacts
    assert source.read_bytes() == before


def test_revealed_public_door_copy_without_redundant_provider_type(tmp_path, monkeypatch):
    from tests.ifc_repair import test_public_door_opening_copy as copy_family
    # Reuse the public-only unique-coordinate lookup and complete API assertions.
    # Only the synthetic Provider changes: its Intent omits type and swing facts.
    monkeypatch.setattr(copy_family, 'CopyDoorProvider', OmittedDoorSemanticsProvider)
    copy_family.test_revealed_formal030_public_pair_offline_api(tmp_path)
