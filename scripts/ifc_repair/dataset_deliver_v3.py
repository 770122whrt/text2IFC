"""Four-round immutable offline delivery, with a separately budgeted property tail."""
from __future__ import annotations

import argparse
from collections import Counter
import contextlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'.deps/python312')]

from scripts.ifc_repair import dataset_deliver_v2 as base
from scripts.ifc_repair import dataset_property_tail as tail

e,q,old=base.e,base.q,base.old
handoff=base.handoff
SCHEMA='text2ifc/dataset-offline-delivery/1.2'


def _environment(repository,code_root=None):
    root,record=base._environment(repository,code_root)
    e._require(Path(__file__).resolve()==root/'scripts/ifc_repair/dataset_deliver_v3.py'
        and Path(tail.__file__).resolve()==root/'scripts/ifc_repair/dataset_property_tail.py',
        'CODE_ROOT_NOT_ACTUALLY_LOADED')
    return root,record


def _mother(root,build,bindings):
    spec=build['source'];target=build['target_added_pairs'];binding=build['baseline_binding']
    folder=root/'sources'/tail.SOURCE_ID
    row=old._read(e._file(folder,'result.json'),bindings)
    e._require(row.get('source')==spec and row.get('source_id')==tail.SOURCE_ID
        and row.get('source_sha256')==spec['source_sha256'] and row.get('source_unchanged') is True
        and row.get('source_native_passed') is True,'PROPERTY_TAIL_RESULT_SOURCE_CHANGED')
    if target:
        old._terminal(row,target,build['max_attempts'])
    else:
        e._require(row.get('status')=='complete' and row.get('stop_reason')=='quota_already_met'
            and row.get('target_pairs')==0 and all(row.get(k)==[] for k in ('pairs','cases','attempts')),
            'ZERO_TARGET_PROPERTY_TAIL_INVALID')
    checkpoint=old._source(folder,spec,bindings)
    expected={'source_sha256':spec['source_sha256'],'source_id':tail.SOURCE_ID,
        'pairs_per_ifc':target,'max_attempts':build['max_attempts'],'seed':build['seed'],
        'profile':q.PROFILE,'code_sha256':build['code_sha256'],'property_tail':binding}
    e._require(checkpoint.get('configuration')==expected
        and checkpoint.get('cache_sha256')==binding['source_cache_sha256']
        and all(checkpoint.get(k)==row.get(k) for k in ('pairs','cases','attempts')),
        'PROPERTY_TAIL_CHECKPOINT_OR_CACHE_CHANGED')
    for digest in checkpoint['cache_sha256'].values():
        e._digest(digest)
    e._require(row['cases']==[a for a in row['attempts'] if a['status']=='passed']
        and isinstance(checkpoint.get('rejected'),list)
        and row.get('candidate_rejection_count')==len(checkpoint['rejected']),
        'PROPERTY_TAIL_CANDIDATE_LEDGER_CHANGED')
    records=[];numbers=[];keys=set(binding['skipped_recipe_keys']);models=set(binding['prior_model_sha256'])
    for number,attempt in enumerate(row['attempts'],1):
        name=f'damage-{number:03d}';path=f'sources/{tail.SOURCE_ID}/cases/{name}'
        e._require(attempt.get('source_id')==tail.SOURCE_ID and attempt.get('case_id')==name
            and attempt.get('path')==path,'PROPERTY_TAIL_ATTEMPT_PATH_INVALID')
        numbers.append(attempt.get('candidate_number'))
        recipe_path=e._file(folder,f'private/attempt-recipes/{name}.json')
        e._bind(recipe_path,bindings,e._digest(attempt.get('attempt_recipe_sha256')))
        recipe=q.read(recipe_path);key=q.recipe_key(recipe)
        e._require(not recipe['deletions'] and bool(recipe.get('property_changes'))
            and recipe.get('family')=='attributes' and key==attempt.get('recipe_key') and key not in keys,
            'PROPERTY_TAIL_RECIPE_NOT_NEW_PROPERTY_ONLY')
        keys.add(key)
        if attempt['status']=='failed':
            e._require(attempt.get('machine_validated') is False,'FAILED_PROPERTY_TAIL_MARKED_VALID')
            continue
        e._require(attempt.get('machine_validated') is True and attempt.get('family')=='attributes'
            and attempt.get('wall_check_applicable') is False and attempt.get('removed_openings')==0,
            'PROPERTY_TAIL_CASE_STATE_INVALID')
        digest=e._digest(attempt.get('model_sha256'))
        e._require(digest not in models,'DUPLICATE_ACCEPTED_DAMAGE_BYTES')
        models.add(digest)
        case=folder/'cases'/name
        e._bind(e._file(case,'private/seal.json'),bindings,e._digest(attempt.get('accepted_seal_sha256')))
        e._require(q.verify_seal(case) and q.read(e._file(case,'private/recipe.json'))==recipe
            and q.recipe_key(q.read(e._file(case,'private/mutation.json')))==key,
            'PROPERTY_TAIL_SEALED_RECIPE_CHANGED')
        modes=attempt.get('prompt_modes')
        e._require(isinstance(modes,list) and len(modes)==len(set(modes)) and 'world' in modes
            and set(modes)<={'world','host_wall'},'PROPERTY_TAIL_MODES_INVALID')
        pairs=tail.rename_pairs(q.make_pair_records(source_id=tail.SOURCE_ID,damage_number=number,
            case_path=path,model_sha256=digest,request_hashes={mode:q.sha256(e._file(case,f'public/request-{mode}.txt'))
                for mode in modes},recipe=recipe,remaining=target-len(records)))
        e._require(bool(pairs),'PROPERTY_TAIL_CASE_WITHOUT_PAIRS')
        checked=e._case(root,pairs[0],bindings)
        e._require(checked['model_sha256']==digest and set(checked['requests'])==set(modes),
            'PROPERTY_TAIL_CASE_BINDING_CHANGED')
        receipt=old._read(e._file(case,'private/property-tail-binding.json'),bindings)
        e._require(receipt=={'schema_version':tail.SCHEMA,'baseline':binding,'code_sha256':build['code_sha256'],
            'geometry_guard':'text2ifc/dataset-geometry-guard/2.0','request_profile':q.PROFILE,
            'source_admission':'hash-bound-r2-reused'},'PROPERTY_TAIL_CASE_RECEIPT_CHANGED')
        records.extend(pairs)
    e._require(all(type(n) is int and n>0 for n in numbers) and numbers==sorted(set(numbers))
        and type(checkpoint.get('candidate_cursor')) is int and checkpoint['candidate_cursor']>=0
        and (not numbers or checkpoint['candidate_cursor']>=numbers[-1]),'PROPERTY_TAIL_CANDIDATE_CURSOR_CHANGED')
    e._require(records==row['pairs'],'PROPERTY_TAIL_PAIR_MAPPING_CHANGED')
    return row


def _collect_inputs(batch,repository,code_root):
    merged,_,bindings,stats,rounds,catalogue=base._collect_inputs(batch,repository,code_root)
    source=next((r for r in merged if r['source_id']==tail.SOURCE_ID),None)
    e._require(source is not None,'PROPERTY_TAIL_SOURCE_MISSING')
    root=batch/'private'/tail.ROUND
    prior_bindings=dict(bindings)
    build=old._read(e._file(root,'build.json'),bindings)
    e._require(build.get('schema_version')==tail.SCHEMA and build.get('round')==tail.ROUND
        and build.get('source')==source['source'] and build.get('provider_calls')==0
        and type(build.get('max_attempts')) is int and 1<=build['max_attempts']<=30
        and all(build.get(k)==v for k,v in tail.plan_target(len(source['pairs']),max_attempts=build['max_attempts']).items())
        and build.get('baseline_binding')==tail.baseline_binding(batch,source)
        and build.get('baseline_bound_hashes')==prior_bindings,'PROPERTY_TAIL_BUILD_OR_BASELINE_CHANGED')
    e._require(build.get('seed')==q.read(batch/'private'/base.x.ROUND/'sources'/tail.SOURCE_ID/
        'private/checkpoint.json')['configuration']['seed'],'PROPERTY_TAIL_SEED_CHANGED')
    old._recheck(build['baseline_bound_hashes'])
    for path,digest in build['baseline_binding']['baseline_files'].items():
        e._bind(e._pair_safe_path(Path(path)),bindings,e._digest(digest))
    old._program(build,root/'code-snapshot',tail.program_bindings(),bindings,code_root)
    base._round_environment(batch,repository,build['execution_environment'],bindings)
    entry=build['execution_environment'].get('executing_entry',{})
    e._require(entry=={'path':str(code_root/'scripts/ifc_repair/dataset_property_tail.py'),
        'sha256':build['code_sha256']['scripts/ifc_repair/dataset_property_tail.py']},
        'PROPERTY_TAIL_EXECUTED_ENTRY_CHANGED')
    e._bind(Path(__file__),bindings)
    e._require({p.name for p in (root/'sources').iterdir()}=={tail.SOURCE_ID},'PROPERTY_TAIL_SOURCE_SET_CHANGED')
    errors=old._read(e._file(root,'worker-errors.json'),bindings)
    e._require(errors==[],'PROPERTY_TAIL_WORKER_ERRORS')
    row=_mother(root,build,bindings)
    summary=old._read(e._file(root,'summary.json'),bindings)
    e._require(summary==tail.summary_record(build,row) and summary['status']=='finished',
        'PROPERTY_TAIL_NOT_TERMINAL_OR_SUMMARY_CHANGED')
    mapped=[{**p,'case_path':p['case_path'].rsplit('/',1)[0]+'/'+tail.ROUND+'-'+p['case_path'].rsplit('/',1)[1]}
            for p in row['pairs']]
    source['pairs']=[*source['pairs'],*mapped]
    source['cases']=[*source['cases'],*[{**c,'origin_path':c['path'],
        'path':c['path'].rsplit('/',1)[0]+'/'+tail.ROUND+'-'+c['path'].rsplit('/',1)[1],
        'attempt_round':tail.ROUND} for c in row['cases']]]
    source['attempts']=[*source['attempts'],*row['attempts']]
    source['attempted_cases']=len(source['attempts']);source['stop_reason']=row['stop_reason']
    pairs=[p for r in merged for p in r['pairs']];cases=[c for r in merged for c in r['cases']]
    base.x.verify_pair_uniqueness(pairs)
    e._require(all(len(r['pairs'])<=base.PER_MOTHER_CAP for r in merged),'FINAL_MOTHER_CAP_EXCEEDED')
    e._require(len({c['model_sha256'] for c in cases})==len(cases),'DUPLICATE_ACCEPTED_DAMAGE_BYTES')
    keys=[(r['source_sha256'],c['recipe_key']) for r in merged for c in r['cases']]
    e._require(len(set(keys))==len(keys),'DUPLICATE_ACCEPTED_RECIPE')
    record={'name':tail.ROUND,'root':str(root),'build_sha256':bindings[str(root/'build.json')],
        'code_sha256':build['code_sha256'],'mothers':1,'pairs':len(mapped),'distinct_damages':len(row['cases']),
        'attempted_cases':row['attempted_cases'],'failed_attempts':summary['failed_attempts'],
        'candidate_rejections':row['candidate_rejection_count'],'stop_reasons':{row['stop_reason']:1},'worker_errors':[]}
    rounds=[*rounds,record]
    per_mother=[dict(v) for v in stats['per_mother']]
    mother=next(v for v in per_mother if v['source_id']==tail.SOURCE_ID)
    mother.update(pairs=len(source['pairs']),total_pairs=len(source['pairs']),distinct_damages=len(source['cases']),
        status='complete' if len(source['pairs'])==base.PER_MOTHER_CAP else 'incomplete',
        missing_pairs=base.PER_MOTHER_CAP-len(source['pairs']),attempted_cases=len(source['attempts']),
        failed_attempts=sum(a['status']=='failed' for a in source['attempts']),stop_reason=row['stop_reason'])
    stats={**stats,'pairs':len(pairs),'distinct_damages':len(cases),'source_models':len({p['source_id'] for p in pairs}),
        'quota_complete':all(len(r['pairs'])==base.PER_MOTHER_CAP for r in merged),
        'missing_pairs':stats['target_pairs']-len(pairs),'completed_mothers':sum(len(r['pairs'])==base.PER_MOTHER_CAP for r in merged),
        'mothers_without_pairs':[r['source_id'] for r in merged if not r['pairs']],'per_mother':per_mother,
        'rounds':rounds,'supplement_rounds':rounds[1:],'failed_counts_by_round':{r['name']:r['failed_attempts'] for r in rounds},
        'attempted_cases':sum(r['attempted_cases'] for r in rounds),'failed_attempts':sum(r['failed_attempts'] for r in rounds),
        'candidate_rejections':sum(r['candidate_rejections'] for r in rounds),
        'damage_families':dict(Counter(c['family'] for c in cases)),'locator_modes':dict(Counter(p['locator_mode'] for p in pairs)),
        'pair_task_kinds':dict(Counter(p['task_kind'] for p in pairs)),
        'budget_levels':dict(Counter(e.budget_level_for_primary_targets(p['primary_target_count']) for p in pairs)),
        'property_tail_pairs':len(mapped),'property_tail_new_damages':len(row['cases']),
        'property_tail_attempted_cases':row['attempted_cases'],'property_tail_failed_attempts':summary['failed_attempts'],
        'property_tail_target_added_pairs':build['target_added_pairs'],'property_tail_baseline_pairs':build['baseline_pairs'],
        'request_transforms_checked':len(pairs),
        'native_evidence':{**stats['native_evidence'],'case_receipts_reused':len(cases),
            'fresh_seal_and_receipt_binding_checks':len(cases),'property_tail_source_receipts_reused':1,
            'new_source_admissions_in_property_tail_round':0}}
    return merged,pairs,bindings,stats,rounds,catalogue


def _copies(batch,merged,catalogue,bindings):
    receipts=base._copies(batch,merged,catalogue,bindings)
    production=batch/'private/production'
    for row in merged:
        for case in row['cases']:
            if case.get('attempt_round')!=tail.ROUND:
                continue
            origin=e._pair_safe_path(batch/'private'/tail.ROUND/e._relative(case['origin_path']))
            target=e._pair_safe_path(production/e._relative(case['path']))
            tree=old._tree(origin)
            if target.exists():
                e._require(q.verify_seal(target) and old._tree(target)==tree,'COLLECTION_COPY_EXISTS_DIFFERENT')
            else:
                shutil.copytree(origin,target,copy_function=shutil.copyfile)
            e._require(q.verify_seal(origin) and q.verify_seal(target) and old._tree(origin)==old._tree(target)==tree,
                'COLLECTION_COPY_CHANGED')
            for name,digest in tree['files'].items():
                e._bind(e._file(origin,name),bindings,digest);e._bind(e._file(target,name),bindings,digest)
            receipts.append({'origin':origin.relative_to(batch).as_posix(),'target':target.relative_to(batch).as_posix(),**tree})
    return receipts


def _check_locked(batch,repository,code_root=None):
    _environment(repository,code_root)
    # Reuse the complete immutable authority/public readback contract, under the new schema.
    previous=base.SCHEMA
    try:
        base.SCHEMA=SCHEMA
        return base._check_locked(batch,repository,code_root)
    finally:
        base.SCHEMA=previous


def check_delivery(batch,*,repository=ROOT,code_root=None):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    with q._exclusive_lock(batch/'private/RUN.lock'):
        return _check_locked(batch,repository,code_root)


def deliver_batch(batch,*,repository=ROOT,code_root=None):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    production,public,evaluation=e._roots(batch/'public',batch/'private/evaluation')
    final=batch/'private/finalization'
    with q._exclusive_lock(batch/'private/RUN.lock'):
        if final.exists():
            return _check_locked(batch,repository,code_root)
        e._require(not public.exists() and not evaluation.exists(),'NEW_OUTPUT_REQUIRED')
        code_root,environment=_environment(repository,code_root)
        merged,pairs,bindings,stats,rounds,catalogue=_collect_inputs(batch,repository,code_root)
        final.mkdir();stage='collect_sealed_cases_and_source_cache'
        try:
            copies=_copies(batch,merged,catalogue,bindings)
            old._recheck(bindings)
            old._write_new(final/'pairs.json',pairs)
            old._write_new(final/'catalogue.json',{'schema_version':SCHEMA,'historical_sources':catalogue,
                'replacements':stats['replacements'],'active_source_models':base.ACTIVE_SOURCES})
            old._write_new(final/'collection.json',{'schema_version':SCHEMA,'status':'collected','batch':str(batch),
                'repository':str(repository),'execution_environment':environment,'rounds':rounds,
                'bound_hashes':bindings,'copied_cases':copies,'pairs_sha256':q.sha256(final/'pairs.json'),
                'provider_calls':0,'scope':'Four immutable rounds; exact new sealed cases and replacement source cache.'})
            old._write_new(final/'checks.json',{'schema_version':SCHEMA,'passed':True,'stats':stats,
                'scope':'All original three-round gates plus property-only tail, independent budget, baseline/code91/cache/seals and cap30.'})
            stage='export_public_pairs'
            exported=handoff.export_pairs(production,public,evaluation,pairs,source_models=stats['source_models'])
            old._recheck(bindings)
            authority={str(p):q.sha256(p) for p in (final/'pairs.json',final/'catalogue.json',final/'collection.json',
                final/'checks.json',evaluation/'export.json')}
            summary={'schema_version':SCHEMA,'status':'complete',**stats,'public_export':exported,
                'authority_sha256':authority,'validation_scope':'All four rounds checked offline; original strict source/native/EXPRESS '
                'receipts reused, exact IFC bytes and all 1.4 public transforms/CSV/whitelist checked. No fresh finalization native or Provider.'}
            old._write_new(final/'summary.json',summary)
            stage='verify_completed_delivery'
            return _check_locked(batch,repository,code_root)
        except Exception as exc:
            old._write_new(final/'failed.json',{'schema_version':SCHEMA,'status':'failed','stage':stage,
                'error':f'{type(exc).__name__}: {exc}','provider_calls':0,
                'scope':'All partial files and errors retained; no automatic deletion, replacement or retry.'})
            raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('deliver','check'))
    parser.add_argument('--batch',required=True);parser.add_argument('--repository',default=str(ROOT))
    parser.add_argument('--code-root');args=parser.parse_args(argv)
    result=(deliver_batch if args.command=='deliver' else check_delivery)(args.batch,
        repository=args.repository,code_root=args.code_root)
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
