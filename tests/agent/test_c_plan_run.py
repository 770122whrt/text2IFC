"""Exact public loop, both strategies; synthetic provider, frozen IFC evaluator."""
import copy
import json
from pathlib import Path
import pytest
from tests.agent.test_c_wall_join_run import module,ROOT,SOURCE,ORIGINAL
from tests.agent.test_phase6_5_staged_generation import SequenceProvider


def fixture():
    m=module('c_plan_fixture',ORIGINAL/'offline_case.py');m.OUT=SOURCE
    brief,candidate=m.build();brief['schema_version']='text2ifc/design-brief/2.4'
    k=brief['known_facts'];slab=next(e for e in candidate['entities'] if e['ifc_class']=='IfcSlab')
    k['building']['outline']['polygon']=copy.deepcopy(slab['attributes']['Representation']['profile']['points'])
    k['plan_constraints']=[{'id':f'envelope-{i}','kind':'inside_wall_envelope',
        'outline_ref':'/known_facts/building/outline/polygon','storey_ref':f'/known_facts/storeys/{i}',
        'thickness_mm':200,'derived_wall_ids':[w['id'] for w in s['walls']['exterior']],
        'source_turns':['turn-user-001']} for i,s in enumerate(k['storeys'])]
    return brief,candidate


class Provider(SequenceProvider):
    def __init__(self,brief,candidate):
        super().__init__([]);self.brief=brief;self.candidate=candidate

    def generate_live(self,**args):
        stage=args['state']['stage'];text=args['prompt']
        if stage=='design-brief':
            payload=copy.deepcopy(self.brief)
            payload['known_facts']['storeys'][0]['walls']['exterior'][0]['bounds']['y']=[-200,0]
        elif stage=='design-brief-plan-repair':payload=self.brief
        elif stage=='generate':payload=self.candidate
        elif stage=='changeset':
            def extract(label):return json.JSONDecoder().raw_decode(text.split(label,1)[1].lstrip())[0]
            scope=extract('允许修改范围：');revision=extract('基础 Revision：')
            records={r['id']:r for r in self.candidate['entities']+self.candidate['relationships']}
            # Hand-authored legacy fixture relation IDs differ from staged's
            # explicit contract. Only fixture IDs are adapted, never production.
            for r in self.candidate['relationships']:
                attrs=r['attributes'];target=None
                if r['ifc_class']=='IfcRelVoidsElement':
                    opening=attrs['RelatedOpeningElement']
                    target='rel-voids-'+(opening.removeprefix('opening-') if opening.startswith('opening-') else attrs['RelatingBuildingElement'])
                elif r['ifc_class']=='IfcRelFillsElement':target='rel-fills-'+attrs['RelatedBuildingElement']
                elif r['ifc_class']=='IfcRelAggregates' and attrs['RelatingObject'].startswith('stair-'):
                    target='aggregate-'+attrs['RelatingObject']+'-flight'
                if target:
                    records[target]=copy.deepcopy(r);records[target]['id']=target
            payload={'schema_version':'text2ifc/bim-json-changeset/1.0','changeset_id':f'fake-{len(self.calls)}',
                'base_revision_id':revision['revision_id'],'base_candidate_hash':revision['candidate_hash'],
                'expected_facts_hash':revision['expected_facts_hash'],'scope_id':scope['scope_id'],
                'source_issue_ids':scope['source_issue_ids'],'operations':[]}
            for target in scope['entity_ids']+scope['relationship_ids']:
                value=copy.deepcopy(records[target])
                payload['operations'].append({'operation_id':'add-'+target,'op':'add_relationship' if value['ifc_class'].startswith('IfcRel') else 'add_entity',
                    'target_id':target,'value':value,'evidence_refs':[i+':/expected' for i in scope['source_issue_ids']]})
        elif stage=='audit':payload={'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
            'deterministic_gate_status':'passed','findings':[],'evidence_paths':['generator/candidate.json','repair/route.json']}
        else:raise AssertionError('Unexpected stage: '+stage)
        self.payloads.append(payload)
        return super().generate_live(**args)


@pytest.mark.parametrize('strategy',['legacy_full','staged'])
def test_exact_c_loop_plan_correction_reopens_final_ifc(tmp_path,strategy):
    from text2ifc_agent.brief_plan_constraints import validate_plan_constraints
    runner=module('c_plan_runner',ROOT/'c-shaped-plan-constraints-20260911/run_case.py')
    brief,candidate=fixture();assert not validate_plan_constraints(brief)
    provider=Provider(brief,candidate);before=runner.PRIOR_BUDGET.read_bytes()
    result=runner.execute(output=tmp_path/'run',provider_factory=lambda:provider,evidence_class='fake',strategy=strategy)
    assert result['status']=='compiled',result
    assert result['budget_before']['calls_used']==11 and result['budget_before']['tokens_used_or_reserved']==831626
    assert runner.PRIOR_BUDGET.read_bytes()==before
    checker=module('c_plan_checker',SOURCE/'check_ifc.py')
    checked=checker.check_ifc(Path(result['result']['ifc_path']))
    assert checked['status']=='passed',checked
    assert provider.calls[1]['state']['stage']=='design-brief-plan-repair'
