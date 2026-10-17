"""Three-round metadata/copy boundaries use explicitly opaque IFC receipts."""
from __future__ import annotations

import importlib
from pathlib import Path
import shutil

import pytest

from scripts.ifc_repair import dataset_extension as x
from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_supplement as s
from .test_pair_export import opaque_sealed_pair_source
from .test_dataset_deliver import (simulated_batch, add_supplement_case, add_empty_mother,
    accepted, checkpoint, hashes, result)


def api():
    return importlib.import_module('scripts.ifc_repair.dataset_deliver_v2')


def new_case(root, template, spec, number, config):
    folder = root / 'cases' / f'damage-{number:03d}'
    shutil.copytree(template, folder)
    for name in ('private/supplement-binding.json',):
        if (folder / name).exists():
            # Opaque fixture directory only, no historical/source evidence removal.
            (folder / name).unlink()
    (folder / 'public/model.ifc').write_bytes(f'OPAQUE R2 {spec["source_id"]} {number}'.encode())
    digest = q.sha256(folder / 'public/model.ifc')
    identity = f'private-r2-{spec["source_id"]}-{number}'
    mutation = q.read(folder / 'private/mutation.json')
    mutation.update(source_sha256=spec['source_sha256'], damaged_sha256=digest,
        deletions=[{'guid': identity, 'ifc_class': 'IfcWindow'}])
    q.write_json(folder / 'private/mutation.json', mutation)
    meta = q.read(folder / 'case.json')
    meta.update(source_sha256=spec['source_sha256'], damaged_sha256=digest,
        generator_extension=x.SCHEMA, additional_evidence=[*q.read(template / 'case.json')['additional_evidence'],
            'private/extension-binding.json'])
    q.write_json(folder / 'case.json', meta)
    q.write_json(folder / 'private/extension-binding.json', {'schema_version': x.SCHEMA,
        'baseline': config['extension'], 'code_sha256': x.program_bindings(),
        'geometry_guard': 'text2ifc/dataset-geometry-guard/2.0', 'request_profile': q.PROFILE,
        'source_admission': 'fresh-this-round' if config['extension']['replacement'] else 'hash-bound-first-pass-reused'})
    recipe = {'family': 'window', 'severity': 'light', 'deletions': [{
        'guid': identity, 'ifc_class': 'IfcWindow', 'preserve_opening': False}], 'property_changes': []}
    attempt = accepted(root, folder, recipe)
    attempt['candidate_number'] = number
    records = q.make_pair_records(source_id=spec['source_id'], damage_number=number,
        case_path=attempt['path'], model_sha256=digest,
        request_hashes={m:q.sha256(folder / f'public/request-{m}.txt') for m in attempt['prompt_modes']},
        recipe=recipe, remaining=99)
    return attempt, [{**p, 'case_id':p['case_id'].replace('-d','-e2-d'),
        'damage_id':p['damage_id'].replace('-d','-e2-d')} for p in records]


@pytest.fixture
def three_round_batch(simulated_batch, monkeypatch):
    """Three small catalogued mothers, two active, cap8: metadata-only evidence."""
    _, batch, source, _, spec = simulated_batch
    add_supplement_case(simulated_batch)
    add_empty_mother(simulated_batch, monkeypatch)
    module = api()
    monkeypatch.setattr(module, 'ACTIVE_SOURCES', 2)
    monkeypatch.setattr(module, 'PER_MOTHER_CAP', 8)
    monkeypatch.setattr(module, 'EXCLUDED_SOURCE', 'formal-022')
    monkeypatch.setattr(module, 'REPLACEMENT_SOURCE', 'formal-023')
    # Runtime/ancillary/actual load isolation has its own real subprocess tests.
    monkeypatch.setattr(module, '_environment', lambda repository, code_root=None:
        (q.ROOT, {'fixture_kind':'simulated environment, not an execution claim'}))
    monkeypatch.setattr(module, '_round_environment', lambda *args: None)
    monkeypatch.setattr(x, 'program_bindings', lambda: {**s.program_bindings(),
        'scripts/ifc_repair/dataset_extension.py':q.sha256(Path(x.__file__))})
    root = batch / 'private' / x.ROUND
    existing = x.baseline_rows(batch)
    old = next(r for r in existing if r['source_id']==spec['source_id'])
    borrowed, borrowed_hashes = x._borrowed(batch, old)
    replacement_root = root / 'sources/formal-023'
    replacement_root.joinpath('private').mkdir(parents=True)
    replacement_root.joinpath('private/reference.ifc').write_bytes(b'OPAQUE NEW SOURCE, NO NATIVE EXECUTION')
    replacement = {**spec, 'source_id':'formal-023',
        'input_path':str(replacement_root / 'private/reference.ifc'),
        'source_sha256':q.sha256(replacement_root / 'private/reference.ifc')}
    specs = [spec, replacement]
    plans, summaries = [], []
    for item in specs:
        new = item is replacement
        numbers = x.plan_targets(0 if new else 3, 0 if new else len(borrowed), replacement=new, cap=8)
        chosen = [] if new else borrowed[:numbers['borrowed_pairs']]
        binding = {'round':x.ROUND,'source_id':item['source_id'],'replacement':new,
            'baseline':{} if new else x._baseline_binding(batch,item['source_id']),
            'borrowed_bound_hashes':{} if new else borrowed_hashes,
            'target_added_pairs':numbers['target_added_pairs'],'per_mother_cap':8}
        plan = {'source_id':item['source_id'],'replacement':new,**numbers,
            'borrowed_variants':chosen,'borrowed_bound_hashes':binding['borrowed_bound_hashes'],
            'baseline_binding':binding,'seed':20261010 if new else 17,'max_attempts':30}
        plans.append(plan)
        folder = root / 'sources' / item['source_id']
        for name in q.read(source / 'private/checkpoint.json')['cache_sha256']:
            target = folder / name
            if not target.exists():
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source / name,target)
        q.write_json(folder / 'private/source.json',item)
        admission = q.read(folder / 'private/source-validation.json')
        admission['input_sha256'] = item['source_sha256']
        q.write_json(folder / 'private/source-validation.json',admission)
        config = {**q._configuration(item,pairs_per_ifc=plan['target_new_damage_pairs'],max_attempts=30,seed=plan['seed']),
            'code_sha256':x.program_bindings(),'extension':binding}
        cases, pairs = [], []
        for number in range(1,plan['target_new_damage_pairs']//2+1):
            attempt, records = new_case(folder,source / 'cases/damage-001',item,number,config)
            cases.append(attempt)
            pairs.extend(records)
        row = result(item,cases,pairs,target=plan['target_new_damage_pairs'],reason='pair_quota_met')
        checkpoint(folder,item,row,config)
        added = [*[p['pair'] for p in chosen], *[{**p,'case_path':p['case_path'].rsplit('/',1)[0]+'/'+x.ROUND+'-'+p['case_path'].rsplit('/',1)[1]} for p in pairs]]
        summary = {'schema_version':x.SCHEMA,'source_id':item['source_id'],'replacement':new,'status':'complete',
            'baseline_pairs':plan['baseline_pairs'],'target_added_pairs':plan['target_added_pairs'],
            'target_new_damage_pairs':plan['target_new_damage_pairs'],'borrowed_pairs':len(chosen),
            'new_damage_pairs':len(pairs),'added_pairs':len(added),'total_pairs':plan['baseline_pairs']+len(added),
            'missing_added_pairs':0,'new_damages':len(cases),'attempted_cases':len(cases),'failed_attempts':0,
            'stop_reason':row['stop_reason'],'source_unchanged':True,'borrowed_variants':chosen,'pairs':added,
            'result_sha256':q.sha256(folder/'result.json'),'baseline_binding':binding,'provider_calls':0,
            'human_review':'pending_human_review'}
        q.write_json(folder/'mother-summary.json',summary)
        summaries.append(summary)
    removed = next(r for r in existing if r['source_id']=='formal-022')
    build = {'schema_version':x.SCHEMA,'round':x.ROUND,'per_mother_cap':8,'append_existing_pairs':5,
        'target_total_pairs':16,'max_attempts':30,'workers':1,'sources':specs,'plans':plans,
        'replacements':[{'old_source_id':'formal-022','old_source_sha256':removed['source_sha256'],
            'new_source_id':'formal-023','new_source_sha256':replacement['source_sha256'],
            'reason':'Explicitly simulated zero-pair replacement'}], 'code_sha256':x.program_bindings(),
        'execution_environment':{},'provider_calls':0}
    q.write_json(root/'build.json',build)
    for name in build['code_sha256']:
        target = root/'code-snapshot'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(q.ROOT/name,target)
    round_summary = x.round_status(batch)
    # Producer uses its real cap30. This metadata fixture has an explicit cap8.
    round_summary['completed_active_mothers'] = sum(r['total_pairs'] == 8 for r in summaries)
    q.write_json(root/'summary.json',round_summary)
    return module,batch,root,spec,replacement


@pytest.fixture
def metadata_handoff(monkeypatch):
    """Control-only export double; the stitched positive test retains real exporter gates."""
    module=api()
    def check(public,evaluation):
        return q.read(evaluation/'export.json')['fixture_summary']
    def export(source,public,evaluation,pairs,*,source_models):
        public.mkdir()
        evaluation.mkdir()
        (public/'fixture.txt').write_text('Explicit metadata handoff double; no IFC/native claim.',encoding='utf-8')
        summary={'status':'complete','pairs':len(pairs),'source_models':source_models,
            'distinct_damages':len({p['damage_id'] for p in pairs}),
            'fixture_kind':'metadata export double, not public whitelist evidence'}
        q.write_json(evaluation/'export.json',{'pair_provenance':pairs,'fixture_summary':summary})
        return check(public,evaluation)
    monkeypatch.setattr(module.handoff,'export_pairs',export)
    monkeypatch.setattr(module.handoff,'check_pair_export_v2',check)


def test_three_round_delivery_tracks_borrowed_damage_and_replacement_without_overwrite(three_round_batch):
    module,batch,root,_,_ = three_round_batch
    frozen = hashes(batch/'private/production'),hashes(root),hashes(batch/'private/supplement-r1')
    summary = module.deliver_batch(batch)
    assert summary['pairs']==16 and summary['distinct_damages']==8
    assert summary['borrowed_pairs']==1 and summary['extension_new_damage_pairs']==12
    assert summary['historical_source_models']==3 and summary['active_source_models']==summary['source_models']==2
    assert summary['target_pairs']==16 and summary['quota_complete']
    assert [r['name'] for r in summary['rounds']]==['first_pass',s.ROUND,x.ROUND]
    assert summary['per_mother'][1]['active'] is False
    for directory,before in zip((batch/'private/production',root,batch/'private/supplement-r1'),frozen):
        assert all(q.sha256(directory/name)==digest for name,digest in before.items())
    assert module.check_delivery(batch)==module.deliver_batch(batch)==summary


def test_readback_checks_pinned_environment_without_requiring_same_lazy_import_inventory(three_round_batch,monkeypatch,metadata_handoff):
    module,batch,_,_,_ = three_round_batch
    record = {'code_root':str(q.ROOT),'source_repository':str(q.ROOT),
        'loaded_modules':{'first':'bound first module'},'scope':'opaque metadata fixture',
        'pinned_runtime':{'manifest_sha256':'a'*64,'runtime_root':str(q.ROOT),
            'loaded_project_modules':{'first':{'path':'opaque bound first'}},'main_project_fallbacks':[]}}
    monkeypatch.setattr(module,'_environment',lambda *args:(q.ROOT,record.copy()))
    module.deliver_batch(batch)
    record['loaded_modules']={**record['loaded_modules'],'later':'bound later module'}
    record['pinned_runtime']={**record['pinned_runtime'],'loaded_project_modules':{
        **record['pinned_runtime']['loaded_project_modules'],'later':{'path':'opaque bound later'}}}
    assert module.check_delivery(batch)['status']=='complete'
    record['pinned_runtime']={**record['pinned_runtime'],'manifest_sha256':'b'*64}
    with pytest.raises(ValueError,match='DELIVERY_LOADED_ENVIRONMENT_CHANGED'):
        module.check_delivery(batch)


@pytest.mark.parametrize('change',['unfinished','worker_errors','borrowed_duplicate','borrowed_hash','summary_count',
    'replacement_hash','code_snapshot','checkpoint','extension_seal','source_native'])
def test_r2_metadata_or_authority_changes_fail_closed_before_public(three_round_batch,change):
    module,batch,root,_,_ = three_round_batch
    if change in {'unfinished','worker_errors'}:
        path=root/'summary.json'; row=q.read(path)
        if change=='unfinished': row['status']='running'
        else: row['worker_errors']=[{'error':'retained failure'}]
    elif change in {'borrowed_duplicate','borrowed_hash','replacement_hash'}:
        path=root/'build.json'; row=q.read(path)
        if change=='borrowed_duplicate': row['plans'][0]['borrowed_variants'].append(row['plans'][0]['borrowed_variants'][0])
        elif change=='borrowed_hash': row['plans'][0]['borrowed_variants'][0]['pair']['request_sha256']='0'*64
        else: row['replacements'][0]['new_source_sha256']='0'*64
    elif change=='summary_count':
        path=root/'sources/formal-021/mother-summary.json'; row=q.read(path); row['total_pairs']+=1
    elif change=='checkpoint':
        path=root/'sources/formal-021/private/checkpoint.json'; row=q.read(path); row['pairs']=[]
    elif change=='source_native':
        path=root/'sources/formal-023/private/source-validation.json'; row=q.read(path); row['finding_count']=1
    elif change=='extension_seal':
        path=root/'sources/formal-021/cases/damage-001/private/extension-binding.json'; row=q.read(path); row['baseline']={}
    else:
        (root/'code-snapshot/scripts/ifc_repair/dataset_extension.py').write_bytes(b'# changed\n')
        path=None
    if path is not None: q.write_json(path,row)
    with pytest.raises(ValueError): module.deliver_batch(batch)
    assert not (batch/'public').exists() and not (batch/'private/finalization').exists()


@pytest.mark.parametrize('available',[6,0])
def test_terminal_capacity_deficit_is_deliverable_and_missing_count_is_exact(three_round_batch,metadata_handoff,available):
    module,batch,root,_,replacement = three_round_batch
    folder=root/'sources'/replacement['source_id']
    row=q.read(folder/'result.json')
    row.update(cases=row['cases'][:available//2],attempts=row['attempts'][:available//2],pairs=row['pairs'][:available],
        attempted_cases=available//2,status='incomplete',stop_reason='candidate_catalogue_exhausted')
    config=q.read(folder/'private/checkpoint.json')['configuration']
    checkpoint(folder,replacement,row,config)
    report=q.read(folder/'mother-summary.json')
    report.update(status='incomplete',new_damage_pairs=available,added_pairs=available,total_pairs=available,missing_added_pairs=8-available,
        new_damages=available//2,attempted_cases=available//2,stop_reason=row['stop_reason'],pairs=report['pairs'][:available],
        result_sha256=q.sha256(folder/'result.json'))
    q.write_json(folder/'mother-summary.json',report)
    round_summary=x.round_status(batch)
    round_summary['completed_active_mothers']=1
    q.write_json(root/'summary.json',round_summary)
    summary=module.deliver_batch(batch)
    assert summary['status']=='complete' and not summary['quota_complete']
    assert summary['pairs']==8+available and summary['missing_pairs']==8-available
    assert summary['distinct_damages']==4+available//2
    assert summary['source_models']==(2 if available else 1) and summary['active_source_models']==2
    assert summary['per_mother'][-1]['status']=='incomplete'
    assert summary['rounds'][-1]['failed_attempts']==0


def test_existing_extension_case_copy_must_match_and_is_never_overwritten(three_round_batch):
    module,batch,root,_,_ = three_round_batch
    origin=root/'sources/formal-021/cases/damage-001'
    target=batch/'private/production/sources/formal-021/cases/extension-r2-damage-001'
    shutil.copytree(origin,target)
    (target/'public/model.ifc').write_bytes(b'EXISTING DIFFERENT COPY MUST REMAIN')
    before=hashes(target)
    with pytest.raises(ValueError,match='COLLECTION_COPY_EXISTS_DIFFERENT'):
        module.deliver_batch(batch)
    assert hashes(target)==before
    assert q.read(batch/'private/finalization/failed.json')['stage']=='collect_sealed_cases_and_source_cache'
    assert not (batch/'public').exists()
    with pytest.raises(ValueError,match='INCOMPLETE_OR_FAILED_DELIVERY'):
        module.deliver_batch(batch)


def test_new_replacement_cache_copy_does_not_overwrite_existing_bytes(three_round_batch):
    module,batch,_,_,replacement = three_round_batch
    merged,_,bindings,_,_,catalogue=module._collect_inputs(batch,q.ROOT,q.ROOT)
    target=batch/'private/production/sources'/replacement['source_id']
    target.joinpath('private').mkdir(parents=True)
    target.joinpath('private/reference.ifc').write_bytes(b'DIFFERENT CACHE RETAINED')
    before=hashes(target)
    with pytest.raises(ValueError,match='NEW_SOURCE_CACHE_EXISTS_DIFFERENT'):
        module._copies(batch,merged,catalogue,bindings)
    assert hashes(target)==before


def test_export_failure_retains_partial_outputs_and_rejects_automatic_retry(three_round_batch,monkeypatch):
    module,batch,_,_,_ = three_round_batch
    def fail(source,public,evaluation,pairs,*,source_models):
        public.mkdir()
        evaluation.mkdir()
        (public/'partial.txt').write_bytes(b'PRESERVED PARTIAL PUBLIC OUTPUT')
        q.write_json(evaluation/'export-failed.json',{'status':'failed','error':'simulated exporter failure'})
        raise RuntimeError('simulated exporter failure')
    monkeypatch.setattr(module.handoff,'export_pairs',fail)
    with pytest.raises(RuntimeError,match='simulated exporter failure'):
        module.deliver_batch(batch)
    before=hashes(batch)
    with pytest.raises(ValueError,match='INCOMPLETE_OR_FAILED_DELIVERY'):
        module.deliver_batch(batch)
    assert hashes(batch)==before
    failure=q.read(batch/'private/finalization/failed.json')
    assert failure['stage']=='export_public_pairs' and 'simulated exporter failure' in failure['error']
    assert (batch/'private/evaluation/export-failed.json').exists()


def test_readback_rejects_summary_or_copy_tampering(three_round_batch,metadata_handoff):
    module,batch,_,_,_ = three_round_batch
    summary=module.deliver_batch(batch)
    path=batch/'private/finalization/summary.json'
    q.write_json(path,{**summary,'borrowed_pairs':0})
    with pytest.raises(ValueError,match='DELIVERY_STATS_CHANGED'):
        module.check_delivery(batch)
    q.write_json(path,summary)
    target=batch/'private/production/sources/formal-041'
    assert not target.exists()  # Fixture replacement uses its explicit formal-023 ID.
    target=batch/'private/production/sources/formal-023/private/reference.ifc'
    target.write_bytes(b'CHANGED SOURCE CACHE COPY')
    with pytest.raises(ValueError,match='DELIVERY_BINDING_CHANGED'):
        module.check_delivery(batch)


def test_controller_rejects_a_code_root_that_is_not_actually_loaded(tmp_path):
    with pytest.raises(ValueError,match='CODE_ROOT_NOT_ACTUALLY_LOADED'):
        api()._environment(q.ROOT,tmp_path)


@pytest.mark.parametrize('field',['attempt_recipe_sha256','accepted_seal_sha256','cache_sha256'])
def test_missing_required_extension_hash_is_not_treated_as_an_optional_binding(three_round_batch,field):
    module,batch,root,_,replacement = three_round_batch
    folder=root/'sources'/replacement['source_id']
    cursor=q.read(folder/'private/checkpoint.json')
    if field=='cache_sha256':
        cursor[field]['private/inventory.json']=None
    else:
        row=q.read(folder/'result.json')
        row['cases'][0][field]=row['attempts'][0][field]=None
        cursor['cases'],cursor['attempts']=row['cases'],row['attempts']
        q.write_json(folder/'result.json',row)
        summary=q.read(folder/'mother-summary.json')
        summary['result_sha256']=q.sha256(folder/'result.json')
        q.write_json(folder/'mother-summary.json',summary)
    q.write_json(folder/'private/checkpoint.json',cursor)
    with pytest.raises(ValueError):
        module._collect_inputs(batch,q.ROOT,q.ROOT)
    assert not (batch/'public').exists() and not (batch/'private/finalization').exists()
