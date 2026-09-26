"""A child continuation preserves the failed parent and never resets its budget."""
import json
import copy

import pytest

from tests.agent.test_component_requirements_v26 import component_brief
from tests.agent.test_phase6_5_staged_generation import SequenceProvider
from tests.compiler.test_component_geometry_v26 import document


def source_case(tmp_path, cls=None):
    from text2ifc_agent.live_pipeline import run_generator_stage, run_repair_stage, run_design_brief_stage
    root = tmp_path/'parent'
    root.mkdir()
    source = root/'design-brief'
    brief = component_brief()
    candidate = document('IfcDoor')
    correct = None
    if cls:
        from tests.ifc2text.test_component_hosted_public_chain import hosted_document
        from text2ifc_agent.expected_facts import build_expected_facts
        from text2ifc_contract.placement import world_transform_for
        candidate,label,storey = hosted_document(cls)
        correct = copy.deepcopy(candidate)
        filling = next(e for e in candidate['entities'] if e['id']==label)
        world = world_transform_for(candidate,label)
        filling['attributes']['ObjectPlacement'] = {'relative_to':storey,
            'origin':[world[i][3] for i in range(3)],'axis':[world[i][2] for i in range(3)],
            'ref_direction':[world[i][0] for i in range(3)]}
        facts = brief['known_facts']
        facts.pop('doors')
        facts['storeys'] = [{'id':storey,'elevation_mm':0}]
        facts['walls'] = [{'id':'W001','storey':storey,'start_mm':[-1500,0],
            'end_mm':[1500,0],'thickness_mm':200,'height_mm':3000}]
        facts['openings'] = [{'id':'O001','storey':storey,'host_wall':'W001'}]
        facts['doors' if cls=='IfcDoor' else 'windows'] = [{'id':label,'ifc_class':cls,
            'storey':storey,'host_wall':'W001','opening':'O001','installation':'hosted',
            'placement':{k:v for k,v in filling['attributes']['ObjectPlacement'].items() if k!='relative_to'}}]
        facts['semantic_requirements'][0]['entity_id'] = label
        facts['semantic_requirements'][0]['component_geometry'] = copy.deepcopy(filling['attributes']['Representation'])
    from tests.agent.test_semantic_authority_completeness import valid_brief
    brief_case,_ = valid_brief()
    brief_result = run_design_brief_stage(provider=SequenceProvider([brief]),output_dir=source,
        case=brief_case,design_brief_schema_version='text2ifc/design-brief/2.9')
    assert brief_result['valid'],brief_result
    result = run_generator_stage(provider=SequenceProvider([candidate]),
        output_dir=root/'generator',design_source_dir=source,case_id='offline-parent')
    assert result['valid']
    expected = build_expected_facts(case_id='offline-parent',design_brief=brief) if cls else {}
    for name,value in [('design-brief.json',brief),('expected-facts.json',expected),
        ('generation-contract.json',{'schema_version':'text2ifc/generation-contract-selection/1.0',
            'bim_json_schema_version':'bim-json/2.6','generation_strategy':'legacy_full'}),
        ('generation-budget.json',{'limits':{'max_tokens':750000},'attempts':[{'tokens_charged':123}]}),
        ('generation-budget-decision.json',{'status':'budget_blocked'})]:
        (root/name).write_text(json.dumps(value),encoding='utf-8')
    run_repair_stage(provider_factory=lambda:pytest.fail('Unexpected provider call'),
        output_dir=root/'repair',generator_source_dir=root/'generator',case_id='offline-parent')
    return (root,correct) if cls else root


def test_child_copies_only_public_inputs_and_keeps_parent_immutable(tmp_path):
    from scripts.ifc2text.component_candidate_continuation import prepare_case, verify_lineage
    source = source_case(tmp_path)
    (source/'source.ifc').write_text('private source must not be copied',encoding='utf-8')
    (source/'diagnosis.private.json').write_text('{}',encoding='utf-8')
    before = {p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
    target = tmp_path/'child'
    prepare_case(source,target)
    verify_lineage(target)
    assert not (target/'generation-budget.json').exists()
    assert not (target/'source.ifc').exists()
    assert not (target/'diagnosis.private.json').exists()
    assert (target/'generator/candidate.json').read_bytes()==(source/'generator/candidate.json').read_bytes()
    assert before=={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}


@pytest.mark.parametrize('change', ['parent','brief','budget','generator-brief'])
def test_mutated_parent_or_sealed_public_input_blocks_recovery(tmp_path,change):
    from scripts.ifc2text.component_candidate_continuation import prepare_case, verify_lineage
    source = source_case(tmp_path)
    target = tmp_path/'child'
    prepare_case(source,target)
    path = source/'generator/candidate.json' if change=='parent' else target/'design-brief.json' if change=='brief' else source/'generation-budget.json'
    if change=='generator-brief':
        path=target/'generator/design-brief.json'
    path.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='CHANGED'):
        verify_lineage(target)


def test_existing_target_cannot_be_overwritten(tmp_path):
    from scripts.ifc2text.component_candidate_continuation import prepare_case
    source = source_case(tmp_path)
    target = tmp_path/'child'
    prepare_case(source,target)
    with pytest.raises(FileExistsError):
        prepare_case(source,target)


def test_stage_marker_is_single_attempt(tmp_path):
    from scripts.ifc2text.component_candidate_continuation import start_once
    start_once(tmp_path,'repair')
    with pytest.raises(FileExistsError):
        start_once(tmp_path,'repair')


@pytest.mark.parametrize('cls', ['IfcDoor','IfcWindow'])
def test_saved_candidate_repair_audit_and_final_ifc_with_fake_provider(tmp_path,cls):
    import ifcopenshell
    from scripts.ifc2text.component_candidate_continuation import prepare_case, repair_case, audit_case
    parent,correct = source_case(tmp_path,cls)
    before = {p.relative_to(parent):p.read_bytes() for p in parent.rglob('*') if p.is_file()}
    case = tmp_path/'child'
    prepare_case(parent,case)
    provider = SequenceProvider([correct])
    repair = repair_case(case,lambda:provider)
    assert repair['valid'],repair
    assert len(provider.calls)==1
    audit = {'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
             'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json']}
    result = audit_case(case,SequenceProvider([audit]))
    assert result['status']=='accepted',result
    acceptance = json.loads((case/'continuation-acceptance-result.json').read_text(encoding='utf-8'))
    assert acceptance['valid'],acceptance
    model = ifcopenshell.open(acceptance['ifc_path'])
    filling = model.by_type(cls)[0]
    assert len(filling.FillsVoids)==1
    assert len(filling.Representation.HasShapeAspects)==15
    assert before=={p.relative_to(parent):p.read_bytes() for p in parent.rglob('*') if p.is_file()}


def test_failed_preservation_cannot_promote_or_reach_audit(tmp_path):
    from scripts.ifc2text.component_candidate_continuation import prepare_case,repair_case,audit_case
    parent,correct = source_case(tmp_path,'IfcWindow')
    case = tmp_path/'child'
    prepare_case(parent,case)
    before = (case/'generator/candidate.json').read_bytes()
    filling = next(e for e in correct['entities'] if e['ifc_class']=='IfcWindow')
    filling['attributes']['Representation']['parts'][0]['role'] = 'unrequested-change'
    result = repair_case(case,lambda:SequenceProvider([correct]))
    assert not result['valid']
    assert before==(case/'generator/candidate.json').read_bytes()
    with pytest.raises(ValueError,match='DETERMINISTIC_GATES_BLOCK_AUDIT'):
        audit_case(case,SequenceProvider([]))
    assert not (case/'accepted').exists()


def test_unsettled_parent_is_not_a_new_budget(tmp_path):
    from scripts.ifc2text.component_candidate_continuation import prepare_case
    parent = source_case(tmp_path)
    budget = json.loads((parent/'generation-budget.json').read_text(encoding='utf-8'))
    budget['attempts'][0]['status'] = 'reserved'
    (parent/'generation-budget.json').write_text(json.dumps(budget),encoding='utf-8')
    with pytest.raises(ValueError,match='UNSETTLED_PARENT_BUDGET'):
        prepare_case(parent,tmp_path/'child')
    assert not (tmp_path/'child').exists()


def test_non_ready_parent_cannot_enter_repair(tmp_path):
    from scripts.ifc2text.component_candidate_continuation import prepare_case
    parent = source_case(tmp_path)
    brief = json.loads((parent/'design-brief.json').read_text(encoding='utf-8'))
    brief['status']='draft_required'
    (parent/'design-brief.json').write_text(json.dumps(brief),encoding='utf-8')
    with pytest.raises(ValueError,match='READY_PARENT_BRIEF_REQUIRED'):
        prepare_case(parent,tmp_path/'child')
    assert not (tmp_path/'child').exists()
