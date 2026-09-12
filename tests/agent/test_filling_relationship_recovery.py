"""Missing attachment family: frozen endpoints, no geometry or semantic edits."""
import copy
import json

import pytest

from tests.compiler.test_part_appearance import document
from tests.compiler.test_basic_filling import TEMPLATES
from text2ifc_contract.validation_v2 import validate_v2_document


def fixture(template='door-left', version='2.2', missing='both'):
    doc, fill = document(template)
    doc['schema_version'] = 'bim-json/' + version
    fill['part_appearance'] = {'frame': {'color': [.2, .3, .4]}} if version == '2.2' else None
    if version != '2.2':
        fill.pop('part_appearance')
    rel = next(r for r in doc['relationships'] if r['ifc_class'] == 'IfcRelFillsElement')
    opening = rel['attributes']['RelatingOpeningElement']
    host = next(r['attributes']['RelatingBuildingElement'] for r in doc['relationships']
                if r['ifc_class'] == 'IfcRelVoidsElement' and r['attributes']['RelatedOpeningElement'] == opening)
    # Use explicit opaque identities through the same projection consumed in production.
    from text2ifc_agent.expected_facts import build_expected_facts
    collection = 'doors' if template.startswith('door') else 'windows'
    from tests.agent.test_part_appearance_authority import brief as valid_brief
    from tests.agent.test_semantic_authority_completeness import review
    brief = valid_brief()
    brief['known_facts'] = {'semantic_requirements': [], 'semantic_review': review(), 'plan_constraints': [],
        'storeys': [{'id': 'level', 'elevation_mm': 0, 'walls': {'exterior': [{'id': 'host'}]},
                     collection: [{'id': 'filling', 'host_wall': 'host', 'width_mm': 900, 'height_mm': 2100}]}]}
    expected = build_expected_facts(case_id='family', design_brief=brief)
    eid = expected['entity_id_contract'][collection][0]['entity_id']
    hid = expected['entity_id_contract']['walls'][0]['entity_id']
    mapping = {fill['id']: eid, opening: 'opening-' + eid, host: hid}
    def rename(value):
        if isinstance(value, str): return mapping.get(value, value)
        if isinstance(value, list): return [rename(v) for v in value]
        if isinstance(value, dict): return {k: rename(v) for k, v in value.items()}
        return value
    doc = rename(doc)
    assert not validate_v2_document(doc)
    kinds = {'fill': {'IfcRelFillsElement'}, 'void': {'IfcRelVoidsElement'},
             'both': {'IfcRelFillsElement', 'IfcRelVoidsElement'}, 'none': set()}[missing]
    doc['relationships'] = [r for r in doc['relationships'] if r['ifc_class'] not in kinds]
    return doc, brief, eid


def recover(doc, brief):
    from text2ifc_agent.filling_relationship_recovery import recover_filling_relationships
    return recover_filling_relationships(doc, brief, case_id='family')


@pytest.mark.parametrize('template', TEMPLATES)
@pytest.mark.parametrize('version', ['2.1', '2.2'])
@pytest.mark.parametrize('missing', ['fill', 'void', 'both'])
def test_missing_explicit_relationships_recover_without_other_edits(template, version, missing):
    doc, brief, _ = fixture(template, version, missing)
    before = copy.deepcopy(doc)
    result = recover(doc, brief)
    assert result['eligible'], result
    after = result['candidate']
    assert after['entities'] == doc['entities']
    assert after['relationships'][:len(doc['relationships'])] == doc['relationships']
    assert not validate_v2_document(after)
    assert doc == before
    assert not recover(after, brief)['eligible']


@pytest.mark.parametrize('attack', ['no_brief', 'wrong_host', 'wrong_parent', 'duplicate_id',
    'duplicate_fill', 'wrong_fill', 'geometry', 'unknown_version', 'shared_opening', 'missing_entity'])
def test_ambiguous_or_inconsistent_authority_never_mutates_candidate(attack):
    doc, brief, eid = fixture(missing='none' if attack in {'duplicate_fill','wrong_fill','shared_opening'} else 'both')
    target = next(e for e in doc['entities'] if e['id'] == eid)
    if attack == 'no_brief': brief['known_facts'] = {}
    elif attack == 'wrong_host': brief['known_facts']['storeys'][0]['doors'][0]['host_wall'] = 'elsewhere'
    elif attack == 'wrong_parent': target['attributes']['ObjectPlacement']['relative_to'] = 'storey-1'
    elif attack == 'duplicate_id': doc['entities'].append(copy.deepcopy(target))
    elif attack in {'duplicate_fill','wrong_fill','shared_opening'}:
        rel = next(r for r in doc['relationships'] if r['ifc_class'] == 'IfcRelFillsElement')
        if attack == 'wrong_fill': rel['attributes']['RelatingOpeningElement'] = 'other'
        else:
            rel = copy.deepcopy(rel); rel['id'] = 'other-relation'; doc['relationships'].append(rel)
            if attack == 'shared_opening': rel['attributes']['RelatedBuildingElement'] = 'window-1'
    elif attack == 'geometry': target['attributes']['Representation']['width'] = 5000
    elif attack == 'unknown_version': doc['schema_version'] = 'bim-json/99'
    else: doc['entities'] = [e for e in doc['entities'] if e['id'] != 'opening-' + eid]
    before = copy.deepcopy(doc)
    assert not recover(doc, brief)['eligible']
    assert doc == before


def test_public_repair_seam_uses_no_provider_and_preserves_source(tmp_path):
    from text2ifc_agent.live_pipeline import run_repair_stage
    doc, brief, _ = fixture()
    source = tmp_path/'generator'; source.mkdir()
    payloads = {'conversation': [{'turn_id': 'turn-1', 'role': 'user', 'content': '按已确认门洞建模。'}],
        'design-brief': brief, 'parsed-output': doc,
        'validation': {'valid': False, 'issues': [vars(i) for i in validate_v2_document(doc)]},
        'metrics': {'contract_valid': False, 'classification': 'formal'}}
    for name, data in payloads.items():
        (source/(name+'.json')).write_text(json.dumps(data), encoding='utf-8')
    (source/'input.txt').write_text('按已确认门洞建模。', encoding='utf-8')
    def forbidden(): raise AssertionError('No Provider is needed for frozen attachment endpoints')
    result = run_repair_stage(provider_factory=forbidden, output_dir=tmp_path/'repair',
                             generator_source_dir=source, case_id='family')
    assert result['valid'] and result['provider_call_count'] == 0
    repaired = json.loads((tmp_path/'repair/repaired-candidate.json').read_text(encoding='utf-8'))
    assert repaired['entities'] == doc['entities']
    assert json.loads((source/'parsed-output.json').read_text(encoding='utf-8')) == doc


@pytest.mark.parametrize('bad_second', [False, True])
def test_batch_is_atomic_when_one_target_conflicts(bad_second):
    doc, brief, eid = fixture()
    from text2ifc_agent.expected_facts import build_expected_facts
    row = copy.deepcopy(brief['known_facts']['storeys'][0]['doors'][0]); row['id'] = 'another'
    brief['known_facts']['storeys'][0]['doors'].append(row)
    expected = build_expected_facts(case_id='family', design_brief=brief)
    second = expected['entity_id_contract']['doors'][1]['entity_id']
    for source_id, target_id in [(eid, second), ('opening-'+eid, 'opening-'+second)]:
        record = copy.deepcopy(next(e for e in doc['entities'] if e['id'] == source_id))
        record['id'] = target_id
        if source_id == eid:
            record['attributes']['ObjectPlacement']['relative_to'] = 'opening-'+second
            if bad_second: record['attributes']['ObjectPlacement']['origin'][0] = 9999
        else: record['attributes']['ObjectPlacement']['origin'][0] = 1000
        doc['entities'].append(record)
    before = copy.deepcopy(doc); result = recover(doc, brief)
    assert result['eligible'] is not bad_second
    assert doc == before
    if not bad_second:
        assert len(result['added_relationships']) == 4
        assert result['candidate']['entities'] == before['entities']
    else: assert result['candidate'] is None


@pytest.mark.parametrize('strategy', ['legacy_full', 'staged'])
def test_public_loop_reopens_recovered_ifc_and_keeps_parts(tmp_path, strategy):
    from pathlib import Path
    import shutil
    from tests.agent import filling_recovery_support as module
    brief, candidate = module.fixture()
    # Old C test assets use legacy raw IDs. Freeze a canonical-ID variant for
    # this new bounded recovery contract; do not add aliases to production.
    from text2ifc_agent.expected_facts import build_expected_facts
    expected = build_expected_facts(case_id='family', design_brief=brief)
    mapping = {r['brief_id']: r['entity_id'] for key in ['walls','doors','windows']
               for r in expected['entity_id_contract'][key]}
    mapping.update({'opening-'+r['brief_id']: 'opening-'+r['entity_id']
                    for key in ['doors','windows'] for r in expected['entity_id_contract'][key]})
    def rename(value):
        if isinstance(value, str): return mapping.get(value, value)
        if isinstance(value, list): return [rename(v) for v in value]
        if isinstance(value, dict): return {k:rename(v) for k,v in value.items()}
        return value
    if strategy == 'legacy_full':
        candidate = rename(candidate)
        brief['known_facts']['semantic_requirements'] = rename(brief['known_facts']['semantic_requirements'])
    missing = copy.deepcopy(candidate)
    fillings = {e['id'] for e in missing['entities'] if e['ifc_class'] in {'IfcDoor','IfcWindow'}}
    openings = {'opening-'+i for i in fillings}
    missing['relationships'] = [r for r in missing['relationships'] if not (
        r['ifc_class'] == 'IfcRelFillsElement' or
        (r['ifc_class'] == 'IfcRelVoidsElement' and r['attributes']['RelatedOpeningElement'] in openings))]
    class Provider(module.Provider):
        def generate_live(self, **kwargs):
            if kwargs['state']['stage'] == 'generate':
                from tests.agent.test_phase6_5_staged_generation import SequenceProvider
                return SequenceProvider([missing]).generate_live(**kwargs)
            return super().generate_live(**kwargs)
    runner = module.runner(tmp_path)
    for name in ['request.txt','conversation.json']: shutil.copyfile(module.SOURCE/name, tmp_path/name)
    provider = Provider(brief, candidate)
    result = runner.execute(output=tmp_path/'run', provider_factory=lambda:provider,
                            evidence_class='offline_fake_attachment_family', strategy=strategy)
    assert result['status'] == 'compiled', result
    run = Path(result['run_dir'])
    if strategy == 'legacy_full':
        assert json.loads((run/'generator/parsed-output.json').read_text(encoding='utf-8')) == missing
        after = json.loads((run/'repair/repaired-candidate.json').read_text(encoding='utf-8'))
        assert after['entities'] == missing['entities']
        assert json.loads((run/'repair/metrics.json').read_text(encoding='utf-8'))['provider_call_count'] == 0
        assert not (run/'scaffold/candidate.json').exists()
    import ifcopenshell
    model = ifcopenshell.open(result['result']['ifc_path'])
    assert len(model.by_type('IfcRelFillsElement')) == len(fillings)
    assert result['prior_budget_unchanged']
