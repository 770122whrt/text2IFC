"""Public synthetic siblings for multi-Pset operation evaluation.

The revealed live failure remains separate; no private benchmark input is used.
"""
from copy import deepcopy

import ifcopenshell
import pytest

from tests.ifc_repair.test_existing_property_type_preservation import (
    TARGET_ID, SIBLING_ID, _api, _source, _DraftProvider, _nominal,
)
from text2ifc_ifc_repair.repair_intent import RepairIntent
from text2ifc_ifc_repair.orchestrator import RepairOrchestrator
from text2ifc_ifc_repair.production_evaluation import evaluate_production, _application_role_mapping


@pytest.mark.parametrize('ifc_class,shared', [('IfcDoor', False), ('IfcBeam', True), ('IfcWindow', False)])
def test_two_existing_psets_in_one_public_api_operation(tmp_path, ifc_class, shared):
    source = tmp_path / 'source.ifc'
    _source(source, ifc_class, 'Notes', 'Category', 'IfcText', shared)
    m = ifcopenshell.open(str(source))
    target = m.by_guid(TARGET_ID)
    pset = m.create_entity('IfcPropertySet', GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=target.OwnerHistory, Name='TakeOff', HasProperties=[m.create_entity(
            'IfcPropertySingleValue', Name='Reference', NominalValue=m.create_entity('IfcLabel', 'old'))])
    m.create_entity('IfcRelDefinesByProperties', GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=target.OwnerHistory, RelatedObjects=([target, m.by_guid(SIBLING_ID)] if shared else [target]),
        RelatingPropertyDefinition=pset)
    m.write(str(source)); before = source.read_bytes()
    api = _api(tmp_path / 'runs', ifc_class, 'Notes', 'Category', _DraftProvider(), value='Doors')
    original_intent = api._intent_stage
    def intent_stage(**kwargs):
        result = original_intent(**kwargs)
        body = result['intent'].to_dict()
        second = deepcopy(body['operations'][0]['property_intents'][0])
        second.update(set_name='TakeOff', property_name='Reference', raw_value='36" x 96" - Flush HM- LOUVER')
        body['operations'][0]['property_intents'].append(second)
        result['intent'] = RepairIntent.from_dict(body, registry=kwargs['registry'])
        return result
    api._intent_stage = intent_stage
    errors = []
    def evaluation(inputs):
        try: return evaluate_production(inputs)
        except Exception as error:
            errors.append(f'{type(error).__name__}: {error}')
            raise
    api._orchestrator_factory = lambda **kwargs: RepairOrchestrator(**kwargs, evaluation_stage=evaluation)
    result = api.start(source, 'Set existing Notes.Category to Doors and TakeOff.Reference to 36" x 96" - Flush HM- LOUVER; preserve types and units.')
    for _ in range(3):
        if result.reason_code != 'property_confirmation': break
        question = result.clarification
        result = api.continue_with_answer(result.run_id,
            {'kind': 'confirm_property', 'preview_hash': question.property_preview['preview_hash']},
            clarification_id=question.clarification_id, expected_state_version=result.state_version)
    assert result.status == 'succeeded', (result.to_dict(), errors)
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / result.artifacts['successful_ifc']))
    assert _nominal(repaired, TARGET_ID, 'Notes', 'Category') == ('IfcText', 'Doors')
    assert _nominal(repaired, TARGET_ID, 'TakeOff', 'Reference') == ('IfcLabel', '36" x 96" - Flush HM- LOUVER')
    if shared:
        assert _nominal(repaired, SIBLING_ID, 'Notes', 'Category') == ('IfcText', 'old')
        assert _nominal(repaired, SIBLING_ID, 'TakeOff', 'Reference') == ('IfcLabel', 'old')
    assert source.read_bytes() == before


def test_duplicate_primary_target_still_rejected():
    with pytest.raises(ValueError, match='APPLICATION_ROLE_CARDINALITY_INVALID'):
        _application_role_mapping({'operations': [{'operation_id': 'p', 'changes': {'modified': [
            {'role': 'target', 'global_id': 'a'}, {'role': 'target', 'global_id': 'b'}]}}]})


def test_revealed_public_two_pset_request(tmp_path):
    """Revealed public-only fake API regression, never holdout evidence."""
    from pathlib import Path
    import hashlib
    import ifcopenshell.util.placement
    import ifcopenshell.util.unit
    public = Path(__file__).resolve().parents[2] / '.tmp/repair-formal-1200-20261011/cycle/round-08/batch/cases/formal-025-s1-d003-world/public'
    source = public / 'model.ifc'
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    m = ifcopenshell.open(str(source))
    scale = ifcopenshell.util.unit.calculate_unit_scale(m)
    targets = [door for door in m.by_type('IfcDoor') if all(abs(float(a)*scale-b)<=.000501
        for a,b in zip(ifcopenshell.util.placement.get_local_placement(door.ObjectPlacement)[:3,3], (11.517,19.5,167.996)))]
    assert len(targets) == 1
    target_id = targets[0].GlobalId
    request = (public / 'request.txt').read_text(encoding='utf-8')
    api = _api(tmp_path / 'runs', 'IfcDoor', 'Pset_ProductRequirements', 'Category', _DraftProvider(), value='Doors')
    original = api._intent_stage
    def intent_stage(**kwargs):
        result = original(**kwargs)
        body = result['intent'].to_dict()
        op = body['operations'][0]
        op['target_query']['global_id'] = target_id
        prop = deepcopy(op['property_intents'][0])
        prop.update(set_name='Pset_QuantityTakeOff', property_name='Reference', raw_value='36" x 96" - Flush HM- LOUVER')
        op['property_intents'].append(prop)
        result['intent'] = RepairIntent.from_dict(body, registry=kwargs['registry'])
        return result
    api._intent_stage = intent_stage
    result = api.start(source, request)
    for _ in range(3):
        if result.reason_code != 'property_confirmation': break
        q = result.clarification
        result = api.continue_with_answer(result.run_id,
            {'kind': 'confirm_property', 'preview_hash': q.property_preview['preview_hash']},
            clarification_id=q.clarification_id, expected_state_version=result.state_version)
    assert result.status == 'succeeded', result.to_dict()
    repaired = ifcopenshell.open(str(api.store.runs_root/result.run_id/result.artifacts['successful_ifc']))
    assert _nominal(repaired, target_id, 'Pset_ProductRequirements', 'Category')[1] == 'Doors'
    assert _nominal(repaired, target_id, 'Pset_QuantityTakeOff', 'Reference')[1] == '36" x 96" - Flush HM- LOUVER'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before
