"""Four-round metadata fixture, opaque IFC/native receipts and a native-entry double."""
import importlib
from pathlib import Path
import shutil

import pytest

from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_extension as x
from .test_dataset_deliver import simulated_batch, opaque_sealed_pair_source, accepted, result, hashes
from .test_dataset_deliver_v2 import three_round_batch


@pytest.fixture
def four_round_batch(three_round_batch,monkeypatch):
    base,batch,r2,_,spec=three_round_batch
    tail=importlib.import_module('scripts.ifc_repair.dataset_property_tail')
    module=importlib.import_module('scripts.ifc_repair.dataset_deliver_v3')
    monkeypatch.setattr(tail,'SOURCE_ID',spec['source_id'])
    monkeypatch.setattr(tail,'PER_MOTHER_CAP',8)
    monkeypatch.setattr(tail,'check_environment',lambda *a,**k:(q.ROOT,{'fixture_kind':'metadata, not actual runtime'}))
    monkeypatch.setattr(tail,'execution_environment',lambda *a:{'executing_entry':{
        'path':str(Path(tail.__file__).resolve()),'sha256':q.sha256(Path(tail.__file__))}})
    folder=r2/'sources'/spec['source_id']
    row=q.read(folder/'result.json')
    row.update(cases=row['cases'][:3],attempts=row['attempts'][:3],pairs=row['pairs'][:6],
        attempted_cases=3,status='incomplete',stop_reason='candidate_catalogue_exhausted')
    q.write_json(folder/'result.json',row)
    state=q.read(folder/'private/checkpoint.json')
    state.update(cases=row['cases'],attempts=row['attempts'],pairs=row['pairs'],candidate_cursor=3)
    q.write_json(folder/'private/checkpoint.json',state)
    summary=q.read(folder/'mother-summary.json')
    summary.update(status='incomplete',new_damage_pairs=6,added_pairs=6,total_pairs=6,
        missing_added_pairs=2,new_damages=3,attempted_cases=3,stop_reason=row['stop_reason'],pairs=summary['pairs'][:6],
        result_sha256=q.sha256(folder/'result.json'))
    q.write_json(folder/'mother-summary.json',summary)
    aggregate=x.round_status(batch);aggregate['completed_active_mothers']=1
    q.write_json(r2/'summary.json',aggregate)
    calls=[]
    def metadata_native_entry(item,repository,root,*,pairs_per_ifc,max_attempts,seed,resume):
        """Explicit double: production still calls the untouched guarded/native entry."""
        calls.append((pairs_per_ifc,max_attempts,resume))
        mother=root/'sources'/item['source_id'];case=mother/'cases/damage-001'
        template=batch/'private/production/sources/formal-021/cases/damage-001'
        shutil.copytree(template,case)
        (case/'public/model.ifc').write_bytes(b'OPAQUE PROPERTY TAIL, NOT A NATIVE IFC')
        digest=q.sha256(case/'public/model.ifc')
        change={'guid':'private-tail-fixture-door','ifc_class':'IfcDoor','pset_name':'Fixture',
            'property_name':'Label','value_type':'IfcLabel','before':'original','after':'original [damage-00]'}
        recipe={'family':'attributes','severity':'light','deletions':[],'property_changes':[change]}
        mutation=q.read(case/'private/mutation.json')
        mutation.update(source_sha256=item['source_sha256'],damaged_sha256=digest,deletions=[],property_changes=[change])
        q.write_json(case/'private/mutation.json',mutation)
        meta=q.read(case/'case.json')
        meta.update(source_sha256=item['source_sha256'],damaged_sha256=digest,family='attributes',
            deleted_counts={k:0 for k in q.CLASSES},property_changes=1,primary_target_count=1,
            property_target_count=1,wall_check_applicable=False,generator_property_tail=tail.SCHEMA,
            additional_evidence=[*meta['additional_evidence'],'private/property-tail-binding.json'])
        q.write_json(case/'case.json',meta)
        wall=q.read(case/'private/wall-check.json');wall['applicable']=False
        if 'input_sha256' in wall:
            wall['input_sha256']={'reference':item['source_sha256'],'damaged':digest}
        q.write_json(case/'private/wall-check.json',wall)
        state=q.read(mother/'private/checkpoint.json');binding=state['configuration']['property_tail']
        q.write_json(case/'private/property-tail-binding.json',{'schema_version':tail.SCHEMA,'baseline':binding,
            'code_sha256':tail.program_bindings(),'geometry_guard':'text2ifc/dataset-geometry-guard/2.0',
            'request_profile':q.PROFILE,'source_admission':'hash-bound-r2-reused'})
        attempt=accepted(mother,case,recipe);attempt.update(wall_check_applicable=False,removed_openings=0)
        pairs=q.make_pair_records(source_id=item['source_id'],damage_number=1,case_path=attempt['path'],
            model_sha256=digest,request_hashes={m:q.sha256(case/f'public/request-{m}.txt') for m in attempt['prompt_modes']},
            recipe=recipe,remaining=pairs_per_ifc)
        completed=result(item,[attempt],pairs,target=pairs_per_ifc,reason='pair_quota_met')
        state.update(attempts=completed['attempts'],cases=completed['cases'],pairs=pairs,candidate_cursor=1)
        q.write_json(mother/'private/checkpoint.json',state);q.write_json(mother/'result.json',completed)
        return completed
    monkeypatch.setattr(x,'process_mother_up_to_30',metadata_native_entry)
    before={str(p):q.sha256(p) for directory in (batch/'private/production',batch/'private/supplement-r1',r2)
            for p in directory.rglob('*') if p.is_file()}
    generated=tail.run_round(batch,repository=q.ROOT)
    return module,tail,batch,batch/'private'/tail.ROUND,before,calls,generated


def test_tail_completes_only_actual_deficit_and_four_round_delivery_is_idempotent(four_round_batch):
    module,tail,batch,root,before,calls,generated=four_round_batch
    assert calls==[(2,30,True)] and generated['total_pairs']==8 and generated['added_pairs']==2
    summary=module.deliver_batch(batch)
    assert summary['schema_version']==module.SCHEMA and summary['pairs']==16 and summary['quota_complete']
    assert summary['distinct_damages']==8 and summary['property_tail_new_damages']==1
    assert summary['property_tail_baseline_pairs']==6 and summary['property_tail_pairs']==2
    assert summary['rounds'][-2]['pairs']==11 and summary['rounds'][-1]['pairs']==2
    assert summary['borrowed_pairs']==1
    assert summary['historical_source_models']==3 and summary['active_source_models']==2
    assert all(q.sha256(Path(path))==digest for path,digest in before.items())
    assert module.check_delivery(batch)==module.deliver_batch(batch)==summary
    assert len([p for p in (batch/'public').rglob('*') if p.is_file()])==33
    assert summary['native_evidence']['new_source_admissions_in_property_tail_round']==0


@pytest.mark.parametrize('change,code',[
    ('worker','PROPERTY_TAIL_WORKER_ERRORS'),('binding','PROPERTY_TAIL_BUILD_OR_BASELINE_CHANGED'),
    ('seal','SHA256|HASH|DIGEST'),('cache','HASH')])
def test_tail_changes_fail_closed_before_public_or_finalization(four_round_batch,change,code):
    module,_,batch,root,_,_,_=four_round_batch
    mother=next((root/'sources').iterdir())
    if change=='worker':
        q.write_json(root/'worker-errors.json',[{'error':'explicit simulated failure'}])
    elif change=='binding':
        value=q.read(root/'build.json');value['baseline_binding']['skipped_recipe_keys']=[]
        q.write_json(root/'build.json',value)
    elif change=='seal':
        value=q.read(mother/'result.json');value['attempts'][0]['accepted_seal_sha256']=None
        value['cases']=value['attempts']
        q.write_json(mother/'result.json',value)
        state=q.read(mother/'private/checkpoint.json');state['attempts']=state['cases']=value['attempts']
        q.write_json(mother/'private/checkpoint.json',state)
    else:
        (mother/'private/inventory.json').write_bytes(b'changed fixture cache')
    with pytest.raises(ValueError,match=code):
        module.deliver_batch(batch)
    assert not (batch/'public').exists() and not (batch/'private/finalization').exists()


def test_new_version_keeps_partial_export_and_never_automatically_retries(four_round_batch,monkeypatch):
    module,_,batch,_,_,_,_=four_round_batch
    calls=[]
    def broken(source,public,evaluation,pairs,*,source_models):
        calls.append(1);public.mkdir();evaluation.mkdir()
        (public/'partial.txt').write_bytes(b'partial metadata output')
        q.write_json(evaluation/'export-failed.json',{'error':'preserved fixture failure'})
        raise ValueError('EXPLICIT_FIXTURE_EXPORT_FAILURE')
    monkeypatch.setattr(module.handoff,'export_pairs',broken)
    with pytest.raises(ValueError,match='EXPLICIT_FIXTURE_EXPORT_FAILURE'):
        module.deliver_batch(batch)
    with pytest.raises(ValueError,match='INCOMPLETE_OR_FAILED_DELIVERY'):
        module.deliver_batch(batch)
    assert calls==[1] and (batch/'public/partial.txt').read_bytes()==b'partial metadata output'
    assert (batch/'private/finalization/failed.json').exists()
