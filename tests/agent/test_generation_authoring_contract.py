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
    assert sent['IFC_AUTHORING_CONTRACT']['geometry_encoding']['rectangle']['anchor'] == 'profile_center_at_extrusion_base'
    trace = json.loads((tmp_path/'generator/trace-manifest.json').read_text(encoding='utf-8'))
    assert trace['template_id'] == 'bim-json-generator.v2.2'
    registry = load_prompt_registry()
    assert 'bim-json-generator.v2.1' in registry
    for template in ['bim-json-generator.v2.2','bim-json-generator-repair.v2.2','bim-json-changeset.v1.2']:
        assert 'IFC_AUTHORING_CONTRACT' in registry[template]['required_inputs']


def test_geometry_contract_version_preserves_legacy_projection():
    from text2ifc_agent.authoring_contract import build_authoring_contract
    old = build_authoring_contract(['IfcWall'], version='1.0')
    new = build_authoring_contract(['IfcWall'])
    assert old['schema_version'].endswith('/1.0') and 'geometry_encoding' not in old
    assert new['schema_version'].endswith('/1.1')
    assert new['classes'] == old['classes']
    assert build_authoring_contract(['IfcWall','IfcWindow'], version='1.0')['contract_hash'] == 'sha256:8c77555d3b673ef5300556b0f0f3be1e035f6ceda137838b85d97ba2d95b4434'
    assert new['geometry_encoding']['placement']['child_origin_formula'] == 'inverse(parent_world) @ requested_world_point'
    with pytest.raises(ValueError):
        build_authoring_contract(version='9.0')


@pytest.mark.parametrize('angle', [0, 90, -90, 180])
@pytest.mark.parametrize('size', [(2800, 180, 2400), (5600, 300, 3200)])
def test_offered_center_anchor_matches_actual_reopened_geometry(tmp_path, angle, size):
    import math
    import ifcopenshell
    import ifcopenshell.geom
    from scripts.presentation.validate_semantic_appearance import candidate
    from text2ifc_compiler import compile_document
    value = candidate('window-single')
    records = {e['id']: e for e in value['entities']}
    wall = records['wall-1']['attributes']
    wall['ObjectPlacement']['origin'] = [1300, -700, 3150]
    radians = math.radians(angle)
    wall['ObjectPlacement']['ref_direction'] = [math.cos(radians), math.sin(radians), 0]
    wall['Representation']['profile'].update(x=size[0], y=size[1])
    wall['Representation']['depth'] = size[2]
    # Keep filling within the explicitly supported host thickness.
    records['door-1']['attributes']['Representation']['depth'] = min(180, size[1])
    records['opening-1']['attributes']['Representation']['profile']['y'] = size[1]
    assert contract(['IfcWall'])['geometry_encoding']['rectangle']['anchor'] == 'profile_center_at_extrusion_base'
    out = tmp_path/'wall.ifc'
    compiled = compile_document(value, out)
    assert compiled.success, compiled
    model = ifcopenshell.open(str(out)); settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    shape = ifcopenshell.geom.create_shape(settings, model.by_type('IfcWall')[0])
    verts = shape.geometry.verts
    spans = [size[0], size[1]] if angle in (0,180) else [size[1],size[0]]
    for axis, center in enumerate([1.3,-.7]):
        assert min(verts[axis::3]) == pytest.approx(center-spans[axis]/2000)
        assert max(verts[axis::3]) == pytest.approx(center+spans[axis]/2000)
    assert min(verts[2::3]) == pytest.approx(3.15)
    assert max(verts[2::3]) == pytest.approx(3.15+size[2]/1000)
