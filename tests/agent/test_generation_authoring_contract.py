"""Frozen T1 family: registry parity, scope, forbidden helpers and stage input."""
import copy
import json
from pathlib import Path

import pytest


def contract(classes=None):
    from text2ifc_agent.authoring_contract import build_authoring_contract
    return build_authoring_contract(classes)


@pytest.mark.parametrize('cls,field,valid,invalid', [
    ('IfcWindowStyle', 'ConstructionType', 'ALUMINIUM', 'WINDOW'),
    ('IfcDoorStyle', 'OperationType', 'SINGLE_SWING_LEFT', 'LEFT'),
    ('IfcSlab', 'PredefinedType', 'FLOOR', 'WALL'),
])
def test_enum_choices_match_actual_ifc_validation(cls, field, valid, invalid):
    from text2ifc_contract.validation_v2 import _attribute_type_matches
    from text2ifc_knowledge.registry import load_ifc2x3_registry
    a = contract([cls])['classes'][cls]['attributes'][field]
    registry_field = next(a for a in load_ifc2x3_registry().entity(cls)['attributes'] if a['name'] == field)
    assert valid in a['enum'] and invalid not in a['enum']
    assert all(_attribute_type_matches(v, registry_field) for v in a['enum'])


def test_field_names_and_compiler_boundary_are_not_guessed():
    attrs = contract(['IfcStairFlight'])['classes']['IfcStairFlight']['attributes']
    assert 'NumberOfRiser' in attrs and 'NumberOfRisers' not in attrs
    assert 'OwnerHistory' not in attrs and 'GlobalId' not in attrs
    assert attrs['ObjectPlacement']['encoding'] == 'bim_json_object_placement'


@pytest.mark.parametrize('unsupported', ['IfcNotAClass', 'IfcCartesianPoint', 'IfcOwnerHistory'])
def test_unknown_and_compiler_only_classes_fail_closed(unsupported):
    with pytest.raises(ValueError):
        contract([unsupported])


def test_scoped_contract_hash_is_deterministic_and_no_defaults_invented():
    a = contract(['IfcWindowStyle', 'IfcWall'])
    assert a == contract(['IfcWall', 'IfcWindowStyle', 'IfcWall'])
    assert a['contract_hash'] != contract(['IfcWall'])['contract_hash']
    assert set(a['classes']) == {'IfcWall', 'IfcWindowStyle'}
    assert a['policies']['physical_materials'] == 'explicit_user_only'
    assert a['policies']['ordinary_properties'] == 'omit_unrequested'
    assert all('default' not in v for c in a['classes'].values() for v in c['attributes'].values())


def test_generator_receives_registered_new_contract_without_rewriting_old_prompt(tmp_path):
    from text2ifc_agent.live_pipeline import run_generator_stage
    from text2ifc_agent.prompt_registry import load_prompt_registry
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    root = Path(__file__).resolve().parents[2]
    candidate = json.loads((root/'tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    candidate['schema_version'] = 'bim-json/2.1'
    source = tmp_path/'design-brief'
    source.mkdir()
    (source/'input.txt').write_text('生成一间房间。', encoding='utf-8')
    for name, value in [('conversation', []), ('context-selection', {'evidence': []}),
                        ('design-brief', {'schema_version':'text2ifc/design-brief/2.1','status':'ready','known_facts':{}})]:
        (source/f'{name}.json').write_text(json.dumps(value), encoding='utf-8')
    class RecordingProvider(SequenceProvider):
        def generate_live(self, **kwargs):
            self.sent_prompt = kwargs['prompt']
            return super().generate_live(**kwargs)
    provider = RecordingProvider([copy.deepcopy(candidate)])
    result = run_generator_stage(provider=provider, output_dir=tmp_path/'generator', design_source_dir=source, case_id='contract-family')
    assert result['valid']
    sent = json.loads((tmp_path/'generator/prompt-render-input.json').read_text(encoding='utf-8'))
    assert 'IFC_AUTHORING_CONTRACT' in sent
    assert 'OTHER_CONSTRUCTION' in provider.sent_prompt
    trace = json.loads((tmp_path/'generator/trace-manifest.json').read_text(encoding='utf-8'))
    assert trace['template_id'] == 'bim-json-generator.v2.2'
    registry = load_prompt_registry()
    assert 'bim-json-generator.v2.1' in registry
    for template in ['bim-json-generator.v2.2','bim-json-generator-repair.v2.2','bim-json-changeset.v1.2']:
        assert 'IFC_AUTHORING_CONTRACT' in registry[template]['required_inputs']
