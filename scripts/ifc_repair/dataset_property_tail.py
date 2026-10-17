"""One independent, property-only tail for the actual formal-041 cap30 deficit."""
from __future__ import annotations

import argparse
import contextlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from scripts.ifc_repair import dataset_deliver_v2 as base
from scripts.ifc_repair import dataset_extension as x
from scripts.ifc_repair import dataset_pair_export as e
from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_supplement as s
from scripts.ifc_repair.dataset_batch import engine
from scripts.ifc_repair.dataset_geometry_guard_v2 import guard_geometry

SCHEMA = 'text2ifc/dataset-property-tail-round/1.0'
ROUND = 'property-tail-r3'
SOURCE_ID = 'formal-041'
PER_MOTHER_CAP = 30
BASE_RAW = q.iter_raw_recipes


def plan_target(baseline_pairs, *, max_attempts=30):
    e._require(type(baseline_pairs) is int and 0 <= baseline_pairs <= PER_MOTHER_CAP
        and type(max_attempts) is int and 1 <= max_attempts <= 30, 'PROPERTY_TAIL_CAP_INVALID')
    return {'baseline_pairs':baseline_pairs, 'target_added_pairs':PER_MOTHER_CAP-baseline_pairs,
            'per_mother_cap':PER_MOTHER_CAP, 'max_attempts':max_attempts}


def program_bindings():
    return {**x.program_bindings(), 'scripts/ifc_repair/dataset_property_tail.py':q.sha256(Path(__file__))}


def property_recipes(inventory, skipped_keys, *, original=BASE_RAW, stopped=None, **kwargs):
    """Existing cached fields/wrong values only; failed and accepted recipes both excluded."""
    seen=set(skipped_keys)
    for recipe in s.raw_with_property_subsets(inventory,original=original,stopped=stopped,**kwargs):
        if recipe['deletions'] or not recipe.get('property_changes'):
            continue
        key=q.recipe_key(recipe)
        if key not in seen:
            seen.add(key)
            yield recipe


def rename_pairs(records):
    return [{**row, 'case_id':row['case_id'].replace('-d','-p3-d'),
             'damage_id':row['damage_id'].replace('-d','-p3-d')} for row in records]


@contextlib.contextmanager
def tail_adapter(binding, skipped_keys, prior_bytes):
    names=('_program_bindings','_configuration','iter_raw_recipes','make_pair_records',
           '_candidate_inventory','_check_damage')
    before={name:getattr(q,name) for name in names}
    previous_guard=engine.guard_geometry
    def configuration(*args,**kwargs):
        return {**before['_configuration'](*args,**kwargs),'property_tail':binding}
    def raw(inventory,**kwargs):
        return property_recipes(inventory,skipped_keys,original=before['iter_raw_recipes'],**kwargs)
    def candidates(inventory):
        # The frozen location gate remains; no deletion/shape prefilter or IFC parsing.
        return before['_candidate_inventory']({**inventory,'targets':{family:[] for family in q.CLASSES}})
    def checked(*args,**kwargs):
        result,prompts,walls,meshes=before['_check_damage'](*args,**kwargs)
        e._require(result['damaged_sha256'] not in prior_bytes,'DUPLICATE_DAMAGE_OF_PREVIOUS_ROUNDS')
        folder=Path(kwargs.get('folder',args[-1] if args else None))
        result={**result,'generator_property_tail':SCHEMA,
            'additional_evidence':[*result['additional_evidence'],'private/property-tail-binding.json']}
        q.write_json(folder/'private/property-tail-binding.json',{'schema_version':SCHEMA,
            'baseline':binding,'code_sha256':program_bindings(),
            'geometry_guard':'text2ifc/dataset-geometry-guard/2.0','request_profile':q.PROFILE,
            'source_admission':'hash-bound-r2-reused'})
        q.write_json(folder/'case.json',result)
        q.seal_case(folder)
        e._require(q.verify_seal(folder),'PROPERTY_TAIL_CASE_SEAL_INVALID')
        return result,prompts,walls,meshes
    try:
        q._program_bindings=program_bindings
        q._configuration=configuration
        q.iter_raw_recipes=raw
        q.make_pair_records=lambda **kwargs:rename_pairs(before['make_pair_records'](**kwargs))
        q._candidate_inventory=candidates
        q._check_damage=checked
        engine.guard_geometry=guard_geometry
        yield
    finally:
        for name,value in before.items():
            setattr(q,name,value)
        engine.guard_geometry=previous_guard


def check_environment(repository, code_root=None):
    root,record=base._environment(repository,code_root)
    e._require(root==ROOT.resolve() and Path(__file__).resolve()==root/'scripts/ifc_repair/dataset_property_tail.py',
               'CODE_ROOT_NOT_ACTUALLY_LOADED')
    return root,record


def execution_environment(root, record):
    return {'runtime_root':str(root), 'runtime_manifest_sha256':q.sha256(root/'runtime.json'),
        'loaded_modules':record['pinned_runtime']['loaded_project_modules'],
        'executing_entry':{'path':str(Path(__file__).resolve()),'sha256':q.sha256(Path(__file__))}}


def baseline_binding(batch, row):
    root=batch/'private'/x.ROUND
    folder=root/'sources'/SOURCE_ID
    checkpoint=q.read(e._file(folder,'private/checkpoint.json'))
    paths=[root/'build.json',root/'summary.json',folder/'result.json',folder/'mother-summary.json',
           folder/'private/checkpoint.json']
    paths.extend(folder/name for name in x.CACHE_FILES)
    paths.extend(root/e._relative(case.get('origin_path',case['path']))/'private/seal.json' for case in row['cases'])
    paths.extend(folder/name for name in ('private/attempts.json','private/pairs.json','private/candidate-rejections.json')
                 if (folder/name).is_file())
    hashes={str(e._pair_safe_path(path)):q.sha256(e._pair_safe_path(path)) for path in paths}
    return {'round':ROUND,'source_id':SOURCE_ID,'source_sha256':row['source_sha256'],
        'baseline_pairs':len(row['pairs']),'per_mother_cap':PER_MOTHER_CAP,
        'baseline_files':hashes,'source_cache_sha256':checkpoint['cache_sha256'],
        'skipped_recipe_keys':sorted({a['recipe_key'] for a in row['attempts']}),
        'prior_model_sha256':sorted({a['model_sha256'] for a in row['cases']}),
        'request_profile':q.PROFILE,'selection':'existing-field property-only; all previous attempts skipped'}


def make_build(batch, repository, *, code_root=None, max_attempts=30):
    e._require(not (batch/'PAUSE').exists(),'PAUSED_BATCH_CANNOT_START_PROPERTY_TAIL')
    root,environment=check_environment(repository,code_root)
    rows,_,bindings,_,_,_=base._collect_inputs(batch,repository,root)
    row=next((r for r in rows if r['source_id']==SOURCE_ID),None)
    e._require(row is not None,'PROPERTY_TAIL_SOURCE_MISSING')
    binding=baseline_binding(batch,row)
    base.old._recheck(binding['baseline_files'])
    return {'schema_version':SCHEMA,'round':ROUND,'source':row['source'],
        **plan_target(len(row['pairs']),max_attempts=max_attempts),
        'seed':q.read(batch/'private'/x.ROUND/'sources'/SOURCE_ID/'private/checkpoint.json')['configuration']['seed'],
        'baseline_binding':binding,'baseline_bound_hashes':bindings,
        'code_sha256':program_bindings(),'execution_environment':execution_environment(root,environment),'provider_calls':0}


def summary_record(build, row, errors=None):
    pairs=row.get('pairs',[]) if row else []
    attempts=row.get('attempts',[]) if row else []
    reason=row.get('stop_reason') if row else 'worker_error'
    terminal=row is not None and row.get('status') in ('complete','incomplete') and reason!='cooperative_pause'
    return {'schema_version':SCHEMA,'round':ROUND,'status':'failed' if errors else 'finished' if terminal else 'paused',
        'source_id':build['source']['source_id'],'baseline_pairs':build['baseline_pairs'],
        'target_added_pairs':build['target_added_pairs'],'added_pairs':len(pairs),
        'total_pairs':build['baseline_pairs']+len(pairs),
        'missing_added_pairs':build['target_added_pairs']-len(pairs),
        'new_damages':len(row.get('cases',[])) if row else 0,'attempted_cases':len(attempts),
        'failed_attempts':sum(a['status']=='failed' for a in attempts),
        'candidate_rejections':row.get('candidate_rejection_count',0) if row else 0,
        'stop_reason':reason,'max_attempts':build['max_attempts'],'worker_errors':errors or [],'provider_calls':0}


def run_round(batch, *, repository=ROOT, code_root=None, max_attempts=30):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    root=batch/'private'/ROUND
    with q._exclusive_lock(batch/'private/RUN.lock'):
        wanted=make_build(batch,repository,code_root=code_root,max_attempts=max_attempts)
        if (root/'build.json').exists():
            build=q.read(e._file(root,'build.json'))
            e._require({k:v for k,v in build.items() if k!='execution_environment'}==
                {k:v for k,v in wanted.items() if k!='execution_environment'}
                and base._environment_identity(build['execution_environment'])==base._environment_identity(wanted['execution_environment']),
                'PROPERTY_TAIL_BUILD_OR_BASELINE_CHANGED')
        else:
            e._require(not root.exists(),'PROPERTY_TAIL_BUILD_MISSING_WITH_EXISTING_FILES')
            root.mkdir(parents=True)
            build=wanted
            q.write_json(root/'build.json',build)
            for name,digest in build['code_sha256'].items():
                target=root/'code-snapshot'/name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/name,target)
                e._require(q.sha256(target)==digest,'PROPERTY_TAIL_SNAPSHOT_CHANGED')
        errors=q.read(root/'worker-errors.json') if (root/'worker-errors.json').exists() else []
        e._require(errors==[],'PROPERTY_TAIL_PREVIOUS_WORKER_ERROR_RETAINED')
        base.old._program(build,root/'code-snapshot',program_bindings(),{},ROOT)
        base.old._recheck(build['baseline_bound_hashes'])
        binding=build['baseline_binding']
        base.old._recheck(binding['baseline_files'])
        folder=root/'sources'/SOURCE_ID
        target=build['target_added_pairs']
        try:
            with tail_adapter(binding,set(binding['skipped_recipe_keys']),set(binding['prior_model_sha256'])):
                if not (folder/'private/checkpoint.json').exists():
                    e._require(not folder.exists(),'PROPERTY_TAIL_CHECKPOINT_MISSING_WITH_EXISTING_FILES')
                    folder.mkdir(parents=True)
                    for name,digest in binding['source_cache_sha256'].items():
                        e._digest(digest)
                        source=batch/'private'/x.ROUND/'sources'/SOURCE_ID/e._relative(name)
                        destination=folder/e._relative(name)
                        destination.parent.mkdir(parents=True,exist_ok=True)
                        with destination.open('xb') as stream:
                            stream.write(e._file(source.parent,source.name).read_bytes())
                        e._require(q.sha256(destination)==q.sha256(source)==digest,'PROPERTY_TAIL_CACHE_COPY_CHANGED')
                    config=q._configuration(build['source'],pairs_per_ifc=target,max_attempts=max_attempts,seed=build['seed'])
                    q.write_json(folder/'private/checkpoint.json',{'schema_version':'text2ifc/dataset-pair-checkpoint/1.0',
                        'configuration':config,'cache_sha256':binding['source_cache_sha256'],
                        'attempts':[],'cases':[],'pairs':[],'candidate_cursor':0,'rejected':[]})
                if target:
                    row=x.process_mother_up_to_30(build['source'],repository,root,pairs_per_ifc=target,
                        max_attempts=max_attempts,seed=build['seed'],resume=True)
                else:
                    row={'source_id':SOURCE_ID,'source':build['source'],'source_sha256':build['source']['source_sha256'],
                        'source_unchanged':True,'source_native_passed':True,'status':'complete','target_pairs':0,
                        'pairs':[],'cases':[],'attempts':[],'attempted_cases':0,'candidate_rejection_count':0,
                        'stop_reason':'quota_already_met'}
                    q.write_json(folder/'result.json',row)
            base.old._recheck(build['baseline_bound_hashes'])
            base.old._recheck(binding['baseline_files'])
            summary=summary_record(build,row)
            q.write_json(root/'worker-errors.json',[])
            q.write_json(root/'summary.json',summary)
            return summary
        except Exception as exc:
            errors.append({'source_id':SOURCE_ID,'error':f'{type(exc).__name__}: {exc}'})
            q.write_json(root/'worker-errors.json',errors)
            q.write_json(root/'summary.json',summary_record(build,None,errors))
            raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('run','status'))
    parser.add_argument('--batch',required=True)
    parser.add_argument('--repository',default=str(ROOT))
    parser.add_argument('--code-root')
    parser.add_argument('--max-attempts',type=int,default=30)
    args=parser.parse_args(argv)
    result=run_round(args.batch,repository=args.repository,code_root=args.code_root,max_attempts=args.max_attempts) \
        if args.command=='run' else q.read(Path(args.batch)/'private'/ROUND/'summary.json')
    print(json.dumps(result,ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
