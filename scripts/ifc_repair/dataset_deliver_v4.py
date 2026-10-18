"""Frozen collection correction: catalogue seed offsets, property tail and delivery.

The 1.2 collector and tail stay byte immutable. Only the independently derived
expected seed is corrected before the original complete checkpoint comparison.
All native/source/seal/export gates remain in their original implementations.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'.deps/python312')]

from scripts.ifc_repair import dataset_deliver_v3 as previous

base,tail=previous.base,previous.tail
old,e,q,s=base.old,base.e,base.q,base.old.s
SCHEMA='text2ifc/dataset-offline-delivery/1.3'
ENTRY='scripts/ifc_repair/dataset_deliver_v4.py'
TAIL_PROGRAM_BINDINGS=tail.program_bindings
TAIL_EXECUTION_ENVIRONMENT=tail.execution_environment


def catalogue_seeds(specs,seed):
    e._require(type(seed) is int and isinstance(specs,list) and bool(specs), 'SEED_CATALOGUE_INVALID')
    ids=[spec.get('source_id') for spec in specs if isinstance(spec,dict)]
    e._require(len(ids)==len(specs) and all(q._valid_source_id(sid) for sid in ids)
        and len({sid.casefold() for sid in ids})==len(ids), 'SEED_CATALOGUE_INVALID')
    return {sid:seed+ordinal for ordinal,sid in enumerate(ids)}


def check_dispatch_rule():
    """Check the pinned producer syntax; frozen SHA/snapshot gates still run afterwards."""
    tree=ast.parse(Path(q.__file__).read_text(encoding='utf-8'))
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='_run_locked')
    dump=lambda node:ast.dump(node,include_attributes=False)
    assignment=ast.parse('waiting = iter(enumerate(specs))').body[0]
    index=ast.parse('i, spec = next(waiting)').body[0]
    dispatch=any(isinstance(node,ast.Call) and len(node.args)>0
        and isinstance(node.args[0],ast.Name) and node.args[0].id=='process_mother'
        and any(k.arg=='seed' and dump(k.value)==dump(ast.parse('seed + i',mode='eval').body)
                for k in node.keywords) for node in ast.walk(function))
    e._require(any(dump(node)==dump(assignment) for node in ast.walk(function))
        and any(dump(node)==dump(index) for node in ast.walk(function)) and dispatch,
        'FROZEN_FIRST_PASS_SEED_DISPATCH_CHANGED')
    supplement=ast.parse(Path(s.__file__).read_text(encoding='utf-8'))
    function=next(node for node in supplement.body if isinstance(node,ast.FunctionDef) and node.name=='supplement_mother')
    inherited=ast.parse("seed = checkpoint['configuration']['seed'] if seed is None else seed").body[0]
    e._require(any(dump(node)==dump(inherited) for node in ast.walk(function)),
        'FROZEN_SUPPLEMENT_SEED_INHERITANCE_CHANGED')


@contextlib.contextmanager
def corrected_seeds(batch):
    check_dispatch_rule()
    production=batch/'private/production'
    build=q.read(e._file(production,'build.json'))
    specs=q.read(e._file(production,'mother-sources.json'))['sources']
    seeds=catalogue_seeds(specs,build['seed']);by_id={spec['source_id']:spec for spec in specs}
    original=old._mother
    checked={'first_pass':set(),s.ROUND:set()}
    def mother(round_root,spec,row,config,bindings,*,supplement=False):
        name=s.ROUND if supplement else 'first_pass'
        expected_root=batch/'private'/s.ROUND if supplement else production
        sid=spec.get('source_id')
        e._require(round_root==expected_root and sid in by_id and spec==by_id[sid]
            and config.get('seed')==build['seed'], 'SEED_CORRECTION_SCOPE_INVALID')
        result=original(round_root,spec,row,{**config,'seed':seeds[sid]},bindings,supplement=supplement)
        checked[name].add(sid)
        return result
    try:
        old._mother=mother
        yield checked
    finally:
        old._mother=original


def seed_record(checked):
    return {'first_pass':'build.seed + mother-sources.json ordered index',
        s.ROUND:'same source verified first-pass seed; no eligible-list reindexing',
        'checked_source_configurations':{name:len(ids) for name,ids in checked.items()},
        'complete_original_configuration_comparison':True}


def tail_program_bindings():
    return {**TAIL_PROGRAM_BINDINGS(),ENTRY:q.sha256(Path(__file__))}


def dispatch_entry():
    return {'path':str(Path(__file__).resolve()),'sha256':q.sha256(Path(__file__))}


def execution_environment(root,record):
    # The frozen function executes the generation; this bound entry dispatches it.
    return {**TAIL_EXECUTION_ENVIRONMENT(root,record),'dispatch_entry':dispatch_entry()}


@contextlib.contextmanager
def delivery_adapter(batch):
    before=(tail.program_bindings,tail.execution_environment,previous.SCHEMA)
    try:
        tail.program_bindings=tail_program_bindings
        tail.execution_environment=execution_environment
        previous.SCHEMA=SCHEMA
        with corrected_seeds(batch) as checked:
            yield checked
    finally:
        tail.program_bindings,tail.execution_environment,previous.SCHEMA=before


def _environment(repository,code_root=None):
    root,record=previous._environment(repository,code_root)
    e._require(root==ROOT.resolve() and Path(__file__).resolve()==root/ENTRY,
        'CODE_ROOT_NOT_ACTUALLY_LOADED')
    return root,record


def preflight(batch,*,repository=ROOT,code_root=None):
    """Read-only full parent collection; no IFC parsing, native, copies or export."""
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    with q._exclusive_lock(batch/'private/RUN.lock'):
        root,environment=_environment(repository,code_root)
        with delivery_adapter(batch) as checked:
            rows,pairs,bindings,stats,rounds,_=base._collect_inputs(batch,repository,root)
            source=next(row for row in rows if row['source_id']==tail.SOURCE_ID)
            old._recheck(bindings)
            return {'schema_version':SCHEMA,'status':'ready','pairs':len(pairs),
                'distinct_damages':stats['distinct_damages'],'source_models':stats['source_models'],
                'tail_plan':tail.plan_target(len(source['pairs'])),'checkpoint_seed_rules':seed_record(checked),
                'tail_program_files':len(tail_program_bindings()),'dispatch_entry':dispatch_entry(),
                'execution_environment':environment,'rounds':rounds,'bound_file_count':len(bindings),
                'native_validations':0,'ifc_parses':0,'provider_calls':0,
                'scope':'Full three-round source/code/config/cache/seal/receipt gates; no generated or exported files.'}


def run_tail(batch,*,repository=ROOT,code_root=None,max_attempts=30):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    _environment(repository,code_root)
    with delivery_adapter(batch):
        return tail.run_round(batch,repository=repository,code_root=code_root,max_attempts=max_attempts)


def check_delivery(batch,*,repository=ROOT,code_root=None):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    _environment(repository,code_root)
    with delivery_adapter(batch):
        return previous.check_delivery(batch,repository=repository,code_root=code_root)


def deliver_batch(batch,*,repository=ROOT,code_root=None):
    batch,repository=e._pair_safe_path(Path(batch)),e._pair_safe_path(Path(repository))
    production,public,evaluation=e._roots(batch/'public',batch/'private/evaluation')
    final=batch/'private/finalization'
    with q._exclusive_lock(batch/'private/RUN.lock'):
        with delivery_adapter(batch) as checked:
            code_root,environment=_environment(repository,code_root)
            if final.exists():
                return previous._check_locked(batch,repository,code_root)
            e._require(not public.exists() and not evaluation.exists(),'NEW_OUTPUT_REQUIRED')
            merged,pairs,bindings,stats,rounds,catalogue=previous._collect_inputs(batch,repository,code_root)
            build=q.read(e._file(batch/'private'/tail.ROUND,'build.json'))
            e._require(build['execution_environment'].get('dispatch_entry')==dispatch_entry(),
                'PROPERTY_TAIL_DISPATCH_ENTRY_CHANGED')
            e._bind(Path(__file__),bindings)
            stats={**stats,'checkpoint_seed_rules':seed_record(checked),
                'property_tail_program_files':len(tail_program_bindings())}
            final.mkdir();stage='collect_sealed_cases_and_source_cache'
            try:
                copies=previous._copies(batch,merged,catalogue,bindings)
                old._recheck(bindings)
                old._write_new(final/'pairs.json',pairs)
                old._write_new(final/'catalogue.json',{'schema_version':SCHEMA,'historical_sources':catalogue,
                    'replacements':stats['replacements'],'active_source_models':base.ACTIVE_SOURCES})
                old._write_new(final/'collection.json',{'schema_version':SCHEMA,'status':'collected','batch':str(batch),
                    'repository':str(repository),'execution_environment':environment,'rounds':rounds,
                    'bound_hashes':bindings,'copied_cases':copies,'pairs_sha256':q.sha256(final/'pairs.json'),
                    'provider_calls':0,'scope':'Four immutable rounds; frozen dispatch seed rule corrected and full original gates retained.'})
                old._write_new(final/'checks.json',{'schema_version':SCHEMA,'passed':True,'stats':stats,
                    'scope':f'All three-round gates plus separate property-only tail, code{len(tail_program_bindings())}, '
                    'independent budget, source/cache/seals/cap30 and exact checkpoint configuration comparison.'})
                stage='export_public_pairs'
                exported=previous.handoff.export_pairs(production,public,evaluation,pairs,source_models=stats['source_models'])
                old._recheck(bindings)
                authority={str(p):q.sha256(p) for p in (final/'pairs.json',final/'catalogue.json',final/'collection.json',
                    final/'checks.json',evaluation/'export.json')}
                summary={'schema_version':SCHEMA,'status':'complete',**stats,'public_export':exported,
                    'authority_sha256':authority,'validation_scope':'All four rounds checked offline; source/native/EXPRESS receipts reused; '
                    'exact IFC bytes and every public 1.4 transform/CSV/whitelist checked. No fresh finalization native or Provider.'}
                old._write_new(final/'summary.json',summary)
                stage='verify_completed_delivery'
                return previous._check_locked(batch,repository,code_root)
            except Exception as exc:
                old._write_new(final/'failed.json',{'schema_version':SCHEMA,'status':'failed','stage':stage,
                    'error':f'{type(exc).__name__}: {exc}','provider_calls':0,
                    'scope':'All partial files and errors retained; no automatic deletion, replacement or retry.'})
                raise


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('preflight','run-tail','deliver','check'))
    parser.add_argument('--batch',required=True);parser.add_argument('--repository',default=str(ROOT))
    parser.add_argument('--code-root');parser.add_argument('--max-attempts',type=int,default=30)
    args=parser.parse_args(argv)
    kwargs={'repository':args.repository,'code_root':args.code_root}
    if args.command=='run-tail':
        kwargs['max_attempts']=args.max_attempts
    function={'preflight':preflight,'run-tail':run_tail,'deliver':deliver_batch,'check':check_delivery}[args.command]
    print(json.dumps(function(args.batch,**kwargs),ensure_ascii=False),flush=True)


if __name__=='__main__':
    main()
