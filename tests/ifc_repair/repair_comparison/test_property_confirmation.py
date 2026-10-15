"""Synthetic public-only fixtures for the delegated host confirmation policy."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import re

import ifcopenshell
import ifcopenshell.guid
import pytest

from scripts.ifc_repair.repair_comparison.property_confirmation import verified_answer
from text2ifc_ifc_repair.property_intent import PropertyConfirmationBatch, PropertyConfirmationPreview
from text2ifc_ifc_repair.repair_intent import hash_request
from text2ifc_ifc_repair.run_models import Clarification, RunStage
from text2ifc_ifc_repair.run_models import hash_json


HEADER = '请按以下要求修复模型。距离和放置坐标单位为米，几何尺寸单位为毫米。'
WORLD = '世界坐标采用IFC模型的项目放置坐标系。'
HOST = '采用各宿主墙已有的自身放置原点及轴方向。'
FOOTER = '除以上补建、洞口关系及指定实例属性外，其余构件、楼层、尺寸、位置、类型和材料保持原样。'
AXES = '（1,0,0）、（0,1,0）、（0,0,1）。'


def _fixture(tmp_path, *, count=1, host=False, value_type='IfcLabel', requested='B02', same_target=False):
    model = ifcopenshell.file(schema='IFC2X3')
    guid = ifcopenshell.guid.new
    unit = model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE')
    model.create_entity('IfcProject', GlobalId=guid(), UnitsInContext=model.create_entity('IfcUnitAssignment', Units=[unit]))
    floor = model.create_entity('IfcBuildingStorey', GlobalId=guid(), Name='L1')

    def entity(kind, x=0.0, name=None):
        axis = model.create_entity('IfcAxis2Placement3D', Location=model.create_entity('IfcCartesianPoint', Coordinates=(float(x), 0., 0.)))
        return model.create_entity(kind, GlobalId=guid(), Name=name, ObjectPlacement=model.create_entity('IfcLocalPlacement', RelativePlacement=axis))

    wall = entity('IfcWall', name='Host') if host else None
    rows, specs, targets = [], [], []
    for index in range(count):
        target = targets[0] if same_target and targets else entity('IfcWindow' if host else 'IfcBeam', index)
        if target not in targets:
            targets.append(target)
        if host:
            opening = entity('IfcOpeningElement', index)
            model.create_entity('IfcRelVoidsElement', GlobalId=guid(), RelatingBuildingElement=wall, RelatedOpeningElement=opening)
            model.create_entity('IfcRelFillsElement', GlobalId=guid(), RelatingOpeningElement=opening, RelatedBuildingElement=target)
        prop_name = 'Assembly mark' if index == 0 else f'Property{index}'
        old = 'B01' if value_type in {'IfcLabel', 'IfcText'} else (False if value_type == 'IfcBoolean' else 1)
        prop = model.create_entity('IfcPropertySingleValue', Name=prop_name, NominalValue=model.create_entity(value_type, old))
        pset = model.create_entity('IfcPropertySet', GlobalId=guid(), Name='Tekla Common', HasProperties=[prop])
        model.create_entity('IfcRelDefinesByProperties', GlobalId=guid(), RelatedObjects=[target], RelatingPropertyDefinition=pset)
        locator = (f'宿主墙「Host」，补建或修改位置在该墙自身X轴正向一侧。放置原点相对墙自身放置原点，沿墙自身X方向距离{index}米，Y方向距离0米，Z方向距离0米。构件自身X/Y/Z轴相对墙自身坐标系的方向分别为' if host else f'放置原点的世界坐标为（{0 if same_target else index},0,0）米。世界X/Y/Z轴分别为') + AXES
        token = '是' if requested is True else '否' if requested is False else json.dumps(requested, ensure_ascii=False)
        row = f'属性更改{index + 1}：现有{target.is_a()}，归属楼层「L1」。{locator}将实例属性「Tekla Common.{prop_name}」改为{token}，保留其原属性类型。'
        rows.append(row)
        specs.append((target, prop_name))
    model.create_entity('IfcRelContainedInSpatialStructure', GlobalId=guid(), RelatedElements=targets + ([wall] if wall else []), RelatingStructure=floor)
    ifc = tmp_path / 'damaged.ifc'
    model.write(str(ifc))
    request = tmp_path / 'request.txt'
    text = '\n'.join([HEADER + (HOST if host else WORLD), *rows, FOOTER]) + '\n'
    request.write_text(text, encoding='utf-8')
    previews = []
    for index, (target, prop_name) in enumerate(specs):
        item = {'operation_id': 'op-0' if same_target else f'op-{index}', 'target_global_id': target.GlobalId,
                'request_hash': hash_request(text), 'model_fingerprint': hash_request('offline-model'),
                'set_name': 'Tekla Common', 'property_name': prop_name, 'value': requested,
                'value_type': value_type, 'unit': None, 'scope': 'occurrence_direct',
                'source': {'source_kind': 'user_request', 'reference': 'request:/text', 'excerpt': rows[index]}}
        item['preview_hash'] = hash_json(item)
        previews.append(item)
    if count == 1:
        preview = previews[0]
    elif same_target:
        preview = PropertyConfirmationBatch.create([PropertyConfirmationPreview.from_dict(item) for item in previews]).to_dict()
    else:
        batches = [PropertyConfirmationBatch.create([PropertyConfirmationPreview.from_dict(item)]).to_dict() for item in previews]
        canonical = {'preview_kind': 'property_transaction', 'request_hash': hash_request(text),
                     'model_fingerprint': hash_request('offline-model'), 'batch_hashes': [batch['preview_hash'] for batch in batches]}
        preview = {**canonical, 'batches': batches, 'preview_hash': hash_json(canonical)}
    q = Clarification(clarification_id='clarify-004', run_id='native-test', state_version=4,
                      operation_id='op-0', stage=RunStage.TARGETS_RESOLVED, resume_stage=RunStage.INTENT_READY,
                      reason_code='property_confirmation', question='Confirm?',
                      answer_modes=('confirm_property', 'reject_property', 'cancel'), property_preview=preview).to_dict()
    state = {'run_id': 'test-E', 'arm': 'E', 'status': 'awaiting_user',
             'metadata': {'input_sha256': hashlib.sha256(ifc.read_bytes()).hexdigest(), 'runtime': {'model_requested': 'offline-model'}},
             'question': {'question_id': q['clarification_id'], 'binding': {'native_question': q, 'state_version': 4}}}
    return state, ifc, request, model


def _preview(state):
    return state['question']['binding']['native_question']['property_preview']


def _rehash(preview):
    preview['preview_hash'] = hash_json({key: value for key, value in preview.items() if key != 'preview_hash'})


@pytest.mark.parametrize('change', ['none', 'reverse', 'invented', 'negated'])
def test_separate_public_sentences_keep_verifiable_provenance(tmp_path, change):
    """Native previews may quote a property row and a later unit convention."""
    from scripts.ifc_repair.repair_comparison.property_confirmation import _UNIT_APPENDIX

    state, ifc, request, _ = _fixture(tmp_path)
    text = request.read_text(encoding='utf-8').strip() + '\n' + _UNIT_APPENDIX + '\n'
    request.write_text(text, encoding='utf-8')
    preview = _preview(state)
    first = preview['source']['excerpt'].rstrip('。')
    second = _UNIT_APPENDIX.split('；')[0]
    excerpt = first + '。' + second
    if change == 'reverse':
        excerpt = second + '。' + first
    elif change == 'invented':
        excerpt += '。这是未提供的事实'
    elif change == 'negated':
        excerpt = first + '。不要' + second
    preview['source']['excerpt'] = excerpt
    preview['request_hash'] = hash_request(text)
    _rehash(preview)

    answer = verified_answer(state, ifc, request)
    assert (answer is not None) is (change == 'none')


@pytest.mark.parametrize('options', [{}, {'host': True}, {'count': 2, 'same_target': True}, {'count': 2}, {'value_type': 'IfcBoolean', 'requested': True}, {'value_type': 'IfcInteger', 'requested': 4}])
def test_exact_existing_public_edits_receive_hash_bound_delegated_answer(tmp_path, options):
    state, ifc, request, _ = _fixture(tmp_path, **options)
    before = (ifc.read_bytes(), request.read_bytes(), deepcopy(state))
    answer = verified_answer(state, ifc, request)
    assert answer is not None
    assert answer['source'] == 'user_confirmed'
    assert answer['question_id'] == state['question']['question_id']
    assert answer['native_answer'] == {'kind': 'confirm_property', 'preview_hash': _preview(state)['preview_hash']}
    assert answer['event_id'] == verified_answer(state, ifc, request)['event_id']
    assert answer['provenance']['human_reviewed'] is False
    assert answer['provenance']['evidence_sources'] == ['public_request', 'damaged_ifc']
    assert '逐项人工审阅' in answer['text']
    assert before == (ifc.read_bytes(), request.read_bytes(), state)


@pytest.mark.parametrize(('field', 'value'), [
    ('value', 'WRONG'), ('value', True), ('target_global_id', 'absent'), ('property_name', 'NewProperty'),
    ('value_type', 'IfcText'), ('scope', 'type_owned'), ('unit', 'mm'), ('request_hash', 'sha256:' + '0' * 64),
    ('model_fingerprint', 'sha256:' + '0' * 64),
    ('source', {'source_kind': 'private_gold', 'reference': 'private', 'excerpt': 'B02'}),
    ('source', {'source_kind': 'user_request', 'reference': 'request:/text', 'excerpt': 'invented fact'}),
])
def test_preview_disagreement_never_confirms_even_with_valid_hash(tmp_path, field, value):
    state, ifc, request, _ = _fixture(tmp_path)
    _preview(state)[field] = value
    _rehash(_preview(state))
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize('change', ['hash', 'question', 'reason', 'version', 'running', 'model', 'ifc_binding', 'unknown_extra', 'bad_schema'])
def test_stale_or_unsupported_bindings_fail_closed(tmp_path, change):
    state, ifc, request, _ = _fixture(tmp_path)
    q = state['question']['binding']['native_question']
    if change == 'hash': _preview(state)['preview_hash'] = 'sha256:' + '0' * 64
    elif change == 'question': state['question']['question_id'] = 'other-question'
    elif change == 'reason': q['reason_code'] = 'additional_target_detail'
    elif change == 'version': state['question']['binding']['state_version'] = 5
    elif change == 'running': state['status'] = 'running'
    elif change == 'model': state['metadata']['runtime']['model_requested'] = 'different-model'
    elif change == 'ifc_binding': state['metadata']['input_sha256'] = '0' * 64
    elif change == 'unknown_extra': _preview(state)['unparsed'] = 'extra authorization'
    elif change == 'bad_schema': q['answer_schema']['properties']['kind']['enum'] = ['cancel']
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize('change', ['missing_row', 'extra_row', 'duplicate_row', 'inline_instruction', 'unknown_language', 'missing_units', 'tampered_bytes'])
def test_request_is_complete_and_contains_no_unparsed_property_instructions(tmp_path, change):
    state, ifc, request, _ = _fixture(tmp_path)
    text = request.read_text(encoding='utf-8')
    row = text.splitlines()[1]
    if change == 'missing_row': text = text.replace(row, '')
    elif change == 'extra_row': text = text.replace(row, row + '\n' + row.replace('属性更改1', '属性更改2').replace('"B02"', '"B03"'))
    elif change == 'duplicate_row': text = text.replace(row, row + '\n' + row.replace('属性更改1', '属性更改2'))
    elif change == 'inline_instruction': text = text.replace('将实例属性', '也修改共享类型。将实例属性')
    elif change == 'unknown_language': text += 'Also change all beam codes.\n'
    elif change == 'missing_units': text = text.replace('距离和放置坐标单位为米，几何尺寸单位为毫米。', '')
    elif change == 'tampered_bytes': text = text.replace('"B02"', '"B03"')
    request.write_text(text, encoding='utf-8')
    if change != 'tampered_bytes':
        _preview(state)['request_hash'] = hash_request(text)
        _preview(state)['source']['excerpt'] = text.splitlines()[0]
        _rehash(_preview(state))
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize('change', ['ambiguous_target', 'duplicate_property', 'absent_property', 'explicit_unit', 'duplicate_guid'])
def test_public_ifc_must_prove_unique_direct_property(tmp_path, change):
    state, ifc, request, model = _fixture(tmp_path)
    beam = model.by_type('IfcBeam')[0]
    prop = model.by_type('IfcPropertySingleValue')[0]
    if change == 'ambiguous_target':
        other = model.create_entity('IfcBeam', GlobalId=ifcopenshell.guid.new(), ObjectPlacement=beam.ObjectPlacement)
        model.by_type('IfcRelContainedInSpatialStructure')[0].RelatedElements = [beam, other]
    elif change == 'duplicate_property':
        pset = model.by_type('IfcPropertySet')[0]
        pset.HasProperties = [prop, model.create_entity('IfcPropertySingleValue', Name=prop.Name, NominalValue=model.create_entity('IfcLabel', 'extra'))]
    elif change == 'absent_property': prop.Name = 'Absent'
    elif change == 'explicit_unit': prop.Unit = model.by_type('IfcSIUnit')[0]
    elif change == 'duplicate_guid': model.by_type('IfcBuildingStorey')[0].GlobalId = beam.GlobalId
    model.write(str(ifc))
    state['metadata']['input_sha256'] = hashlib.sha256(ifc.read_bytes()).hexdigest()
    assert verified_answer(state, ifc, request) is None


def test_redacted_public_transaction_is_insufficient(tmp_path):
    state, ifc, request, _ = _fixture(tmp_path, count=2)
    from text2ifc_ifc_repair.api import _public_property_preview
    state['question']['binding']['native_question']['property_preview'] = _public_property_preview(_preview(state))
    assert verified_answer(state, ifc, request) is None


def test_numeric_measure_without_explicit_property_unit_requires_clarification(tmp_path):
    state, ifc, request, _ = _fixture(tmp_path, value_type='IfcLengthMeasure', requested=2.0)
    assert verified_answer(state, ifc, request) is None


def _foot_unit(model):
    return model.create_entity('IfcConversionBasedUnit', UnitType='LENGTHUNIT', Name='FOOT',
        Dimensions=model.create_entity('IfcDimensionalExponents', 1, 0, 0, 0, 0, 0, 0),
        ConversionFactor=model.create_entity('IfcMeasureWithUnit', ValueComponent=model.create_entity('IfcRatioMeasure', .3048),
            UnitComponent=model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE')))


def _measure_fixture(tmp_path, *, value_type='IfcLengthMeasure', project_units=('mm',), explicit=None, requested=75, preview_value=75.0, preview_unit='mm'):
    state, ifc, request, model = _fixture(tmp_path, value_type=value_type, requested=requested)
    kind, name = {'IfcAreaMeasure': ('AREAUNIT', 'SQUARE_METRE'), 'IfcVolumeMeasure': ('VOLUMEUNIT', 'CUBIC_METRE')}.get(value_type, ('LENGTHUNIT', 'METRE'))

    def unit(token):
        if token == 'FOOT':
            return _foot_unit(model)
        return model.create_entity('IfcSIUnit', UnitType=kind, Name=name,
                                   Prefix={'mm': 'MILLI', 'cm': 'CENTI', 'km': 'KILO', 'm': None}[token])

    assignment = model.by_type('IfcProject')[0].UnitsInContext
    if project_units is None:
        model.remove(model.by_type('IfcProject')[0])
    else:
        assignment.Units = [unit(token) for token in project_units]
        if kind != 'LENGTHUNIT':
            assignment.Units = [*assignment.Units, model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE')]
    if explicit is not None:
        model.by_type('IfcPropertySingleValue')[0].Unit = unit(explicit)
    model.write(str(ifc))
    state['metadata']['input_sha256'] = hashlib.sha256(ifc.read_bytes()).hexdigest()
    _preview(state).update(value=preview_value, unit=preview_unit)
    if type(preview_value) is not float or math.isfinite(preview_value):
        _rehash(_preview(state))
    return state, ifc, request, model


@pytest.mark.parametrize(('value_type', 'project_units', 'explicit', 'token'), [
    ('IfcLengthMeasure', ('mm',), None, 'mm'),
    ('IfcLengthMeasure', ('m',), None, 'm'),
    ('IfcLengthMeasure', ('cm',), None, 'cm'),
    ('IfcPositiveLengthMeasure', ('mm',), None, 'mm'),
    ('IfcLengthMeasure', ('m',), 'mm', 'mm'),
    ('IfcLengthMeasure', ('mm',), 'm', 'm'),
    ('IfcLengthMeasure', None, 'mm', 'mm'),
    ('IfcAreaMeasure', ('mm',), None, 'mm2'),
    ('IfcAreaMeasure', ('m',), None, 'm2'),
    ('IfcVolumeMeasure', ('cm',), None, 'cm3'),
    ('IfcLengthMeasure', ('FOOT',), None, 'FOOT'),
    ('IfcPositiveLengthMeasure', ('FOOT',), None, 'FOOT'),
    ('IfcLengthMeasure', ('m',), 'FOOT', 'FOOT'),
    ('IfcLengthMeasure', ('FOOT',), 'm', 'm'),
])
def test_existing_measure_uses_exact_public_effective_unit_without_converting_raw_value(tmp_path, value_type, project_units, explicit, token):
    state, ifc, request, _ = _measure_fixture(tmp_path, value_type=value_type, project_units=project_units, explicit=explicit, preview_unit=token)
    before = ifc.read_bytes(), request.read_bytes(), deepcopy(state)
    answer = verified_answer(state, ifc, request)
    assert answer is not None
    assert answer['native_answer']['preview_hash'] == _preview(state)['preview_hash']
    assert before == (ifc.read_bytes(), request.read_bytes(), state)


@pytest.mark.parametrize(('project_units', 'preview_unit'), [
    (None, 'mm'), ((), 'mm'), (('mm', 'm'), 'mm'), (('mm', 'mm'), 'mm'),
    (('mm',), None), (('mm',), 'm'), (('m',), 'mm'), (('km',), 'km'),
])
def test_measure_units_require_one_matching_supported_public_source(tmp_path, project_units, preview_unit):
    state, ifc, request, _ = _measure_fixture(tmp_path, project_units=project_units, preview_unit=preview_unit)
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize('change', ['multiple_projects', 'wrong_unit_type', 'wrong_unit_name', 'unsupported_explicit', 'area_has_only_length', 'unknown_measure', 'new_property'])
def test_measure_unit_proof_rejects_ambiguity_and_incompatible_sources(tmp_path, change):
    state, ifc, request, model = _measure_fixture(tmp_path, value_type='IfcAreaMeasure' if change == 'area_has_only_length' else 'IfcLengthMeasure')
    prop = model.by_type('IfcPropertySingleValue')[0]
    if change == 'multiple_projects':
        project = model.by_type('IfcProject')[0]
        model.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), UnitsInContext=project.UnitsInContext)
    elif change == 'wrong_unit_type':
        prop.Unit = model.create_entity('IfcSIUnit', UnitType='AREAUNIT', Name='SQUARE_METRE', Prefix='MILLI')
    elif change == 'wrong_unit_name':
        prop.Unit = model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='SQUARE_METRE', Prefix='MILLI')
    elif change == 'unsupported_explicit':
        prop.Unit = model.create_entity('IfcContextDependentUnit', Dimensions=model.create_entity('IfcDimensionalExponents', 1, 0, 0, 0, 0, 0, 0), UnitType='LENGTHUNIT', Name='mm')
    elif change == 'area_has_only_length':
        assignment = model.by_type('IfcProject')[0].UnitsInContext
        assignment.Units = [unit for unit in assignment.Units if unit.UnitType == 'LENGTHUNIT']
        _preview(state)['unit'] = 'm2'
    elif change == 'unknown_measure':
        prop.NominalValue = model.create_entity('IfcMassMeasure', 1.)
        _preview(state)['value_type'] = 'IfcMassMeasure'
    else:
        prop.Name = 'DifferentProperty'
    model.write(str(ifc))
    state['metadata']['input_sha256'] = hashlib.sha256(ifc.read_bytes()).hexdigest()
    _rehash(_preview(state))
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize('preview_value', [True, '75', float('nan'), float('inf'), .075, 75000.])
def test_measure_preview_cannot_change_numeric_value_or_primitive_kind(tmp_path, preview_value):
    state, ifc, request, _ = _measure_fixture(tmp_path, preview_value=preview_value)
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize('explicit', [False, True])
@pytest.mark.parametrize('damage', ['factor', 'factor_near', 'dimension', 'unit_type', 'base_prefix', 'base_type', 'base_name', 'bool_factor', 'nonfinite_factor', 'name', 'missing_factor'])
def test_existing_foot_requires_exact_supported_conversion_definition(tmp_path, explicit, damage):
    state, ifc, request, model = _measure_fixture(tmp_path, project_units=('m' if explicit else 'FOOT',),
        explicit='FOOT' if explicit else None, preview_unit='FOOT')
    foot = model.by_type('IfcConversionBasedUnit')[0]
    if damage in {'factor', 'factor_near'}:
        value = .3 if damage == 'factor' else .3048000001
        foot.ConversionFactor.ValueComponent = model.create_entity('IfcReal', value)
    elif damage == 'nonfinite_factor': pass  # Create malformed STEP after the writer's finite-value guard.
    elif damage == 'dimension': foot.Dimensions.TimeExponent = 1
    elif damage == 'unit_type': foot.UnitType = 'AREAUNIT'
    elif damage == 'base_prefix': foot.ConversionFactor.UnitComponent.Prefix = 'MILLI'
    elif damage == 'base_type': foot.ConversionFactor.UnitComponent.UnitType = 'AREAUNIT'
    elif damage == 'base_name': foot.ConversionFactor.UnitComponent.Name = 'GRAM'
    elif damage == 'bool_factor': foot.ConversionFactor.ValueComponent = model.create_entity('IfcBoolean', True)
    elif damage == 'name': foot.Name = 'INCH'
    else:
        incomplete = model.create_entity('IfcConversionBasedUnit', Dimensions=foot.Dimensions, UnitType='LENGTHUNIT', Name='FOOT')
        if explicit:
            model.by_type('IfcPropertySingleValue')[0].Unit = incomplete
        else:
            model.by_type('IfcProject')[0].UnitsInContext.Units = [incomplete]
    model.write(str(ifc))
    if damage == 'nonfinite_factor':
        encoded = ifc.read_bytes()
        corrupted, count = re.subn(rb'IFCRATIOMEASURE\([0-9.]+\)', b'IFCRATIOMEASURE(1.E999)', encoded)
        assert count == 1
        ifc.write_bytes(corrupted)
    state['metadata']['input_sha256'] = hashlib.sha256(ifc.read_bytes()).hexdigest()
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize('change', ['conflicting_defaults', 'duplicate_defaults', 'changed_preview_unit', 'changed_raw_value', 'new_property', 'wrong_measure_dimension'])
def test_existing_foot_rejects_unproven_unit_or_new_authorization(tmp_path, change):
    state, ifc, request, model = _measure_fixture(tmp_path, project_units=('FOOT',), preview_unit='FOOT')
    if change in {'conflicting_defaults', 'duplicate_defaults'}:
        assignment = model.by_type('IfcProject')[0].UnitsInContext
        other = _foot_unit(model) if change == 'duplicate_defaults' else model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE')
        assignment.Units = [*assignment.Units, other]
    elif change == 'changed_preview_unit': _preview(state)['unit'] = 'm'
    elif change == 'changed_raw_value': _preview(state)['value'] = 22.86
    elif change == 'wrong_measure_dimension':
        model.by_type('IfcPropertySingleValue')[0].NominalValue = model.create_entity('IfcAreaMeasure', 25.)
        _preview(state)['value_type'] = 'IfcAreaMeasure'
    else: model.by_type('IfcPropertySingleValue')[0].Name = 'DifferentProperty'
    model.write(str(ifc))
    state['metadata']['input_sha256'] = hashlib.sha256(ifc.read_bytes()).hexdigest()
    _rehash(_preview(state))
    assert verified_answer(state, ifc, request) is None


@pytest.mark.parametrize(('value_type', 'requested', 'preview_value', 'allowed'), [
    ('IfcLengthMeasure', True, 1., False),
    ('IfcLengthMeasure', '75', 75., False),
    ('IfcPositiveLengthMeasure', 0, 0., False),
    ('IfcPositiveLengthMeasure', -1, -1., False),
    ('IfcLengthMeasure', -1, -1., True),
    ('IfcReal', 75, 75., True),
    ('IfcInteger', 75, 75., False),
])
def test_numeric_comparison_preserves_original_ifc_type_constraints(tmp_path, value_type, requested, preview_value, allowed):
    if value_type in {'IfcReal', 'IfcInteger'}:
        state, ifc, request, _ = _fixture(tmp_path, value_type=value_type, requested=requested)
        _preview(state)['value'] = preview_value
        _rehash(_preview(state))
    else:
        state, ifc, request, _ = _measure_fixture(tmp_path, value_type=value_type, requested=requested, preview_value=preview_value)
    assert (verified_answer(state, ifc, request) is not None) is allowed


def _modern_request(state, request, *, prefix=True):
    from scripts.ifc_repair.dataset_request_v4 import HEADER as NEW_HEADER, PREFIX
    text = request.read_text(encoding='utf-8')
    text = text.replace(HEADER + WORLD, NEW_HEADER)
    text = text.replace('放置原点的世界坐标为（0,0,0）米。世界X/Y/Z轴分别为' + AXES, '放置基点世界坐标为（0，0，0）米。')
    if prefix:
        text = PREFIX + text
    request.write_text(text, encoding='utf-8')
    _preview(state)['request_hash'] = hash_request(text)
    _preview(state)['source']['excerpt'] = next(row for row in text.splitlines() if row.startswith('属性更改'))
    _rehash(_preview(state))


@pytest.mark.parametrize('binding', ['current', 'old_hash_with_appendix', 'new_hash_without_appendix'])
def test_property_unit_appendix_preserves_full_request_hash_binding(tmp_path, binding):
    state, ifc, request, _ = _measure_fixture(tmp_path)
    _modern_request(state, request)
    original = request.read_text(encoding='utf-8')
    appendix = ('属性更改中的数值沿用该属性在 IFC 中的有效单位（属性未单独指定时沿用项目对应单位），'
                '保留原属性类型和单位；上述几何尺寸的毫米约定不适用于属性值。单位缺失或冲突时请提出澄清。')
    appended = original.rstrip() + '\n' + appendix + '\n'
    request.write_text(original if binding == 'new_hash_without_appendix' else appended, encoding='utf-8')
    _preview(state)['request_hash'] = hash_request(original if binding == 'old_hash_with_appendix' else appended)
    _rehash(_preview(state))
    before = ifc.read_bytes(), request.read_bytes()
    answer = verified_answer(state, ifc, request)
    assert (answer is not None) is (binding == 'current')
    if answer:
        assert answer['provenance']['request_hash'] == hash_request(appended)
        assert answer['provenance']['request_hash'] != hash_request(original)
        assert answer['provenance']['effective_units'] == ['mm']
    assert before == (ifc.read_bytes(), request.read_bytes())


@pytest.mark.parametrize('prefix', [False, True])
def test_current_public_request_profiles_have_independent_locator_verification(tmp_path, prefix):
    state, ifc, request, _ = _fixture(tmp_path)
    _modern_request(state, request, prefix=prefix)
    assert verified_answer(state, ifc, request) is not None


@pytest.mark.parametrize('change', ['prefix_changed', 'rounded_collision', 'unparsed_clause'])
def test_current_profile_rejects_unproven_conventions_and_ambiguous_rounded_locator(tmp_path, change):
    state, ifc, request, model = _fixture(tmp_path)
    _modern_request(state, request)
    text = request.read_text(encoding='utf-8')
    if change == 'prefix_changed': text = text.replace('无需地理或地图转换', '需要地图转换')
    elif change == 'unparsed_clause': text = text.replace('将实例属性', '另加一个属性。将实例属性')
    else:
        beam = model.by_type('IfcBeam')[0]
        position = model.create_entity('IfcLocalPlacement', RelativePlacement=model.create_entity('IfcAxis2Placement3D', Location=model.create_entity('IfcCartesianPoint', Coordinates=(.0004, 0., 0.))))
        other = model.create_entity('IfcBeam', GlobalId=ifcopenshell.guid.new(), ObjectPlacement=position)
        model.by_type('IfcRelContainedInSpatialStructure')[0].RelatedElements = [beam, other]
        model.write(str(ifc))
        state['metadata']['input_sha256'] = hashlib.sha256(ifc.read_bytes()).hexdigest()
    request.write_text(text, encoding='utf-8')
    _preview(state)['request_hash'] = hash_request(text)
    _rehash(_preview(state))
    assert verified_answer(state, ifc, request) is None


def test_current_host_wall_profile_resolves_direct_instance_property(tmp_path):
    import ifcopenshell.api.geometry
    from scripts.ifc_repair.dataset_request_v4 import HOST_HEADER, PREFIX
    state, ifc, request, model = _fixture(tmp_path, host=True)
    wall = model.by_type('IfcWall')[0]
    context = model.create_entity('IfcGeometricRepresentationContext', ContextIdentifier='Body', ContextType='Model',
        CoordinateSpaceDimension=3, Precision=1e-7, WorldCoordinateSystem=wall.ObjectPlacement.RelativePlacement)
    representation = ifcopenshell.api.geometry.add_wall_representation(model, context=context, length=2., height=3., thickness=.2)
    wall.Representation = model.create_entity('IfcProductDefinitionShape', Representations=[representation])
    model.write(str(ifc))
    state['metadata']['input_sha256'] = hashlib.sha256(ifc.read_bytes()).hexdigest()
    row = ('属性更改1：现有IfcWindow，归属楼层「L1」。宿主墙「Host」，长度正向大致朝东，厚度正向大致朝北。'
           '放置基点距墙长度起端0毫米，距墙厚度负向侧0毫米，高出墙底0毫米。'
           '将实例属性「Tekla Common.Assembly mark」改为"B02"，保留其原属性类型。')
    text = PREFIX + '\n'.join([HOST_HEADER, row, FOOTER]) + '\n'
    request.write_text(text, encoding='utf-8')
    _preview(state)['request_hash'] = hash_request(text)
    _preview(state)['source']['excerpt'] = row
    _rehash(_preview(state))
    assert verified_answer(state, ifc, request) is not None


@pytest.mark.parametrize('change', ['missing', 'extra', 'duplicate'])
def test_batch_requires_complete_exact_property_set(tmp_path, change):
    state, ifc, request, _ = _fixture(tmp_path, count=2, same_target=True)
    items = _preview(state)['items']
    if change == 'missing': items = items[:1]
    elif change == 'extra':
        extra = deepcopy(items[0])
        extra['property_name'] = 'NotRequested'
        _rehash(extra)
        items = [*items, extra]
    else:
        _preview(state)['items'] = [items[0], items[0]]
        assert verified_answer(state, ifc, request) is None
        return
    state['question']['binding']['native_question']['property_preview'] = PropertyConfirmationBatch.create(
        [PropertyConfirmationPreview.from_dict(item) for item in items]).to_dict()
    assert verified_answer(state, ifc, request) is None


def test_malformed_inputs_leave_question_pending(tmp_path):
    assert verified_answer({}, tmp_path / 'missing.ifc', tmp_path / 'missing.txt') is None


@pytest.mark.parametrize(('value_type', 'requested', 'project_prefix', 'explicit_token'), [
    ('IfcLabel', 'replacement', None, None),
    ('IfcLengthMeasure', 75, 'MILLI', None),
    ('IfcLengthMeasure', 75, None, None),
    ('IfcLengthMeasure', 75, None, 'mm'),
    ('IfcLengthMeasure', 75, 'FOOT', None),
    ('IfcLengthMeasure', 75, None, 'FOOT'),
])
def test_actual_public_api_question_accepts_delegated_answer_and_publishes_repair(tmp_path, value_type, requested, project_prefix, explicit_token):
    """Deterministic Intent/Provider fixture; real API binding, apply and gates."""
    from tests.ifc_repair.test_existing_property_type_preservation import (
        TARGET_ID, _DraftProvider, _api, _nominal, _source,
    )
    state, ifc, request, _ = _fixture(tmp_path, value_type=value_type, requested=requested)
    _source(ifc, 'IfcBeam', 'Tekla Common', 'Assembly mark', value_type, False,
            value='old' if value_type == 'IfcLabel' else 25.)
    model = ifcopenshell.open(str(ifc))
    history = model.by_type('IfcOwnerHistory')[0]
    unit = (_foot_unit(model) if project_prefix == 'FOOT' else
            model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE', Prefix=project_prefix))
    model.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), OwnerHistory=history,
                        UnitsInContext=model.create_entity('IfcUnitAssignment', Units=[unit]))
    floor = model.create_entity('IfcBuildingStorey', GlobalId=ifcopenshell.guid.new(), OwnerHistory=history, Name='L1')
    target = model.by_guid(TARGET_ID)
    if explicit_token:
        model.by_type('IfcPropertySingleValue')[0].Unit = (_foot_unit(model) if explicit_token == 'FOOT' else
            model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE', Prefix='MILLI'))
    target.ObjectPlacement = model.create_entity('IfcLocalPlacement', RelativePlacement=model.create_entity(
        'IfcAxis2Placement3D', Location=model.create_entity('IfcCartesianPoint', Coordinates=(0., 0., 0.))))
    model.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(), OwnerHistory=history,
                        RelatedElements=[target], RelatingStructure=floor)
    model.write(str(ifc))
    before = ifc.read_bytes()
    provider = _DraftProvider()
    api = _api(tmp_path / 'api', 'IfcBeam', 'Tekla Common', 'Assembly mark', provider, value=requested)
    result = api.start(ifc, request.read_text(encoding='utf-8'))
    assert result.status == 'clarification_required', result.to_dict()
    assert provider.calls == []
    q = result.clarification.to_dict()
    state['question'] = {'question_id': q['clarification_id'], 'binding': {'native_question': q, 'state_version': result.state_version}}
    state['metadata']['input_sha256'] = hashlib.sha256(before).hexdigest()
    state['metadata']['runtime']['model_requested'] = 'offline-type-preservation'
    answer = verified_answer(state, ifc, request)
    assert answer is not None
    expected_unit = None if value_type == 'IfcLabel' else (explicit_token or ('FOOT' if project_prefix == 'FOOT' else 'mm' if project_prefix == 'MILLI' else 'm'))
    assert q['property_preview']['unit'] == expected_unit
    confirmed = api.continue_with_answer(result.run_id, answer['native_answer'],
        clarification_id=q['clarification_id'], expected_state_version=result.state_version)
    assert confirmed.status == 'succeeded', confirmed.to_dict()
    assert confirmed.successful_artifact_publishable
    assert len(provider.calls) == 1
    repaired = ifcopenshell.open(str(api.store.runs_root / result.run_id / confirmed.artifacts['successful_ifc']))
    assert _nominal(repaired, TARGET_ID, 'Tekla Common', 'Assembly mark') == (value_type, requested)
    repaired_prop = repaired.by_type('IfcPropertySingleValue')[0]
    assert (repaired_prop.Unit is None) is (explicit_token is None)
    if expected_unit == 'FOOT':
        effective = ifcopenshell.util.unit.get_property_unit(repaired_prop, repaired)
        assert effective.Name == 'FOOT'
        assert tuple(effective.Dimensions) == (1, 0, 0, 0, 0, 0, 0)
        assert effective.ConversionFactor.ValueComponent.wrappedValue == .3048
        assert effective.ConversionFactor.UnitComponent.Name == 'METRE'
        assert effective.ConversionFactor.UnitComponent.Prefix is None
        assert repaired_prop.NominalValue.wrappedValue == 75.
    elif explicit_token:
        assert (repaired_prop.Unit.UnitType, repaired_prop.Unit.Name, repaired_prop.Unit.Prefix) == ('LENGTHUNIT', 'METRE', 'MILLI')
    assert ifc.read_bytes() == before
