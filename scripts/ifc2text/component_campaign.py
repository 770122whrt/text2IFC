"""Versioned component text-loop experiment through the production public API.

IFC2Text is deterministic here. Only its frozen public description enters Brief;
source IFC and independent comparison remain outside the model request.
"""
from pathlib import Path
import argparse
import compileall
import contextlib
import json
import platform
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'.deps/python312')]
from scripts.ifc2text.rerun_v10 import digest,now,load,save,fingerprint
from scripts.ifc2text.run_goal import git
from scripts.ifc2text.compact_campaign import runtime
from scripts.ifc2text.continue_audit_v12 import budget
from text2ifc_ifc2text.goal_budget import GoalStopped

SCOPE=['src/text2ifc_agent','src/text2ifc_ifc2text','src/text2ifc_contract',
       'src/text2ifc_compiler','src/text2ifc_quality','src/text2ifc_extractor',
       'src/text2ifc_knowledge','src/text2ifc_text','src/text2ifc_presentation',
       'prompts/agent','schemas','scripts/ifc2text','scripts/agent/run_phase6_2_cli.py',
       'tests/ifc2text','tests/agent','tests/compiler','tests/ifc_quality','pyproject.toml']
TARGETS=[
    'tests/ifc2text/test_component_review.py',
    'tests/agent/test_component_world_placement.py',
    'tests/agent/test_audit_dynamic_gate_evidence.py',
    'tests/agent/test_brief_request_echo.py',
    'tests/ifc2text/test_component_budget.py',
    'tests/ifc2text/test_hosted_source.py',
    'tests/ifc2text/test_component_hosted_public_chain.py',
    'tests/agent/test_component_public_identity.py',
    'tests/ifc2text/test_component_campaign.py',
    'tests/ifc2text/test_component_public_chain_v10.py',
    'tests/ifc2text/test_component_description_v10.py',
    'tests/ifc2text/test_component_extraction_v10.py',
    'tests/ifc2text/test_filling_compare_v12.py',
    'tests/ifc2text/test_isolated_source.py',
    'tests/ifc2text/test_precision_compare_v10.py',
    'tests/ifc2text/test_opening_details_v09.py',
    'tests/ifc2text/test_offline_public_bridge.py',
    'tests/ifc2text/test_budget_transport_classification.py',
    'tests/agent/test_component_requirements_v26.py',
    'tests/agent/test_component_generation_v26_route.py',
    'tests/agent/test_component_installation_v26.py',
    'tests/agent/test_brief_duplicate_normalization.py',
    'tests/ifc2text/test_component_description_v11.py',
    'tests/compiler/test_component_geometry_v26.py',
    'tests/compiler/test_polygon_wall_hosts_v24.py',
    'tests/compiler/test_material_list_v25.py',
    'tests/agent/test_generation_v24_route.py',
    'tests/agent/test_material_list_v25_route.py',
    'tests/agent/test_space_geometry_projection_v12.py',
    'tests/agent/test_prompt_registry.py',
    'tests/agent/test_interactive_cli_generation.py',
    'tests/agent/test_interactive_cli_session.py',
    'tests/agent/test_phase6_2_openai_compat.py',
    'tests/agent/test_public_brief_failure_evidence.py',
    'tests/agent/test_clarification_resume_preservation.py',
    'tests/agent/test_phase6_5_changeset_apply.py',
    'tests/agent/test_phase6_3_gate_audit_bundle.py',
    'tests/agent/test_audit_failure_terminal.py',
    'tests/ifc_quality/test_generated_ifc_gate.py',
]


def budget_for(cfg):
    allocation=cfg.get('budget_allocation')
    if allocation is None:return budget()
    path=ROOT/allocation['path']
    if digest(path)!=allocation['sha256']:raise GoalStopped('BUDGET_ALLOCATION_CHANGED')
    from scripts.ifc2text.component_budget import open_allocation
    return open_allocation(path)


def frozen_text(case):
    if digest(ROOT/case['source'])!=case['source_sha256']:
        raise ValueError('SOURCE_CHANGED')
    if digest(ROOT/case['text'])!=case['text_sha256']:
        raise ValueError('PUBLIC_TEXT_CHANGED')
    text = (ROOT/case['text']).read_text(encoding='utf-8')
    if case.get('component_review'):
        from text2ifc_agent.session_store import SessionStore
        from text2ifc_ifc2text.component_review import approved_description
        ref = case['component_review']; database = ROOT/ref['database']
        if not database.is_file():raise ValueError('COMPONENT_REVIEW_REQUIRED')
        with SessionStore.open(database) as store:
            packet = approved_description(store=store, session_id=ref['session_id'])
        if packet['review_sha256'] != ref['review_sha256']:raise ValueError('STALE_REVIEW')
        if packet['description'] != text:raise ValueError('REVIEW_DESCRIPTION_CHANGED')
    return text


def validate(cfg):
    import pytest,ifcopenshell,shapely
    from scripts.ifc2text.validate_goal import OfflineRecorder
    out=ROOT/cfg['output'];directory=out/'validation'
    directory.mkdir(parents=True,exist_ok=False)
    if git('status','--porcelain','--untracked-files=all','--',*SCOPE):
        raise GoalStopped('COMMIT_EXECUTION_SCOPE_BEFORE_ADMISSION')
    for case in cfg['cases']:frozen_text(case)
    before=fingerprint(scope=SCOPE);save(directory/'source-snapshot.json',before)
    save(out/'config.json',cfg)
    args=[*TARGETS,'-q','--import-mode=importlib','-p','no:cacheprovider','--basetemp='+str(directory/'pytest-temp'),
          '--junitxml='+str(directory/'tests.xml')]
    observer=OfflineRecorder();start=now()
    with (directory/'pytest.log').open('w',encoding='utf-8') as stream:
        with observer.network_guard(),contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
            code=int(pytest.main(args,plugins=[observer]))
    test_end=now()
    compiled=all(compileall.compile_dir(str(ROOT/p),quiet=1) for p in SCOPE
                 if p.startswith(('src/','tests/','scripts/')) and (ROOT/p).is_dir())
    diff=git('diff','--check','--',*SCOPE)
    valid=code==0 and observer.counts['passed']>0 and not observer.counts['failed'] and not observer.counts['skipped'] \
        and not observer.setup_errors and not observer.network_attempts and compiled and not diff and before==fingerprint(scope=SCOPE)
    stage = 'reviewed partial-building text-loop' if any(c.get('component_review') for c in cfg['cases']) else 'component single-product and hosted text-loop'
    record={'status':'admitted' if valid else 'blocked','stage':stage+' / Brief 2.9 / BIM 2.6 / Compare 1.2',
        'code_commit':git('rev-parse','HEAD'),'worktree_status':git('status','--porcelain','--untracked-files=all','--',*SCOPE),
        'snapshot_sha256':digest(directory/'source-snapshot.json'),'config_sha256':digest(out/'config.json'),
        'started_at':start,'finished_at':now(),'python':platform.python_version(),'platform':platform.platform(),
        'ifcopenshell':ifcopenshell.version,'shapely':shapely.__version__,
        'commands':[{'argv':['pytest.main',*args],'started_at':start,'finished_at':test_end,'exit_code':code,
                     'timeout':False,'skips':observer.counts['skipped'],'log_sha256':digest(directory/'pytest.log')},
                    {'call':'compileall.compile_dir for code directories in source_scope','passed':compiled},
                    {'argv':['git','diff','--check','--',*SCOPE],'passed':not diff}],
        'tests':observer.counts,'setup_errors':observer.setup_errors,'nodeids':observer.nodeids,
        'network_transport_attempted':bool(observer.network_attempts),'full_preflight':False,'source_scope':SCOPE,
        'matrix':{'public_complete_door_and_window':'test_component_public_chain_v10.py',
            'human_pause_exact_exclusion_restart_and_public_generation':'test_component_review.py',
            'clarification_unsupported_malformed_restart':'test_component_public_chain_v10.py',
            'real_building_context_time_memory':'test_component_campaign.py',
            'transport_failures_and_context_limits':'test_phase6_2_openai_compat.py',
            'atomic_compile_and_actual_geometry':'test_component_geometry_v26.py',
            'independent_source_body_compare':'test_filling_compare_v12.py',
            'publication_and_l0_l1_l2':'test_interactive_cli_generation.py',
            'source_immutability_and_native_selection':'test_isolated_source.py',
            'changeset_atomic_rollback':'test_phase6_5_changeset_apply.py'},
        'not_applicable':['damaged IFC repair and mutation recipe access; this stage generates a new IFC'],
        'invalidation':'Any source-snapshot or configuration or frozen input change requires revalidation before another live call',
        'claim':'Offline engineering admission only. Real runs are diagnostics, not unseen capability improvement.'}
    save(directory/'admission.json',record)
    print(json.dumps({k:record[k] for k in ('status','tests','network_transport_attempted')},indent=2))
    return 0 if valid else 1


def admitted(cfg):
    out=ROOT/cfg['output'];record=load(out/'validation/admission.json')
    if record['status']!='admitted':raise GoalStopped('ADMISSION_REQUIRED')
    snapshot=out/'validation/source-snapshot.json'
    if digest(snapshot)!=record['snapshot_sha256'] or load(snapshot)!=fingerprint(scope=SCOPE):raise GoalStopped('CODE_CHANGED_SINCE_ADMISSION')
    if digest(out/'config.json')!=record['config_sha256'] or cfg!=load(out/'config.json'):raise GoalStopped('CONFIG_CHANGED')
    for case in cfg['cases']:frozen_text(case)
    return record


def live(cfg,case,stage):
    record=admitted(cfg);text=frozen_text(case);out=ROOT/cfg['output']/case['id']
    out.mkdir(parents=True,exist_ok=True)
    marker=out/(stage+'-started.json')
    if marker.exists():raise GoalStopped('ATTEMPT_ALREADY_STARTED')
    b=budget_for(cfg);b.check_capacity('reconstruction')
    cap=cfg['brief_output_tokens'] if stage=='brief' else cfg['generation_output_tokens']
    conf,client,provider=runtime(cfg,b,'reconstruction',cap)
    save(marker,{'at':now(),'stage':stage,'code_commit':record['code_commit'],'budget_before':b.snapshot()})
    save(out/(stage+'-runtime.json'),{'model':conf.model,'provider':conf.provider_label,
        'max_input_tokens':conf.max_input_tokens,'max_output_tokens':cap,'sdk_retries':0,'provider_retries':0})
    from text2ifc_agent.session_store import SessionStore
    from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker,run_design_brief_clarification_loop,run_ready_session_to_ifc
    from text2ifc_agent.generation_budget import GenerationBudget,BudgetLimits
    limits=BudgetLimits(max_calls=cfg['max_calls_per_case'],max_tokens=cfg['max_tokens_per_case'])
    try:
        with SessionStore.open(out/'sessions.sqlite',artifact_root=out) as store:
            if stage=='brief':
                session=store.create_session(original_input=text)
                GenerationBudget(session.run_dir,limits=limits)
                save(out/'session.json',{'id':session.session_id,'run_dir':str(session.run_dir)})
                invoker=make_openai_design_brief_invoker(config=conf,run_dir=session.run_dir,
                    client_factory=lambda **_:client,design_review_enabled=False,
                    design_brief_schema_version='text2ifc/design-brief/2.9')
                result=run_design_brief_clarification_loop(store=store,session=session.session_id,
                    invoke_design_brief=invoker,user_answers=())
                report={'status':result.status,'session_id':session.session_id,'run_dir':str(session.run_dir)}
            else:
                if load(out/'brief-result.json')['status']!='ready':raise GoalStopped('READY_BRIEF_REQUIRED')
                session=store.get_session(load(out/'session.json')['id'])
                if session.original_input!=text:raise GoalStopped('SESSION_TEXT_CHANGED')
                result=run_ready_session_to_ifc(store=store,session=session.session_id,provider_factory=lambda:provider,
                    generation_strategy='legacy_full',bim_json_schema_version='bim-json/2.6',
                    trace_level='debug',budget_limits=limits)
                report={'status':result.status,'ifc_path':str(result.ifc_path) if result.ifc_path else None,
                        'generator_status':result.generator_status,'audit_status':result.audit_status}
        frozen_text(case)
        report.update(budget=b.snapshot(),finished_at=now());save(out/(stage+'-result.json'),report)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as error:
        save(out/(stage+'-terminal.json'),{'status':'failed','error_type':type(error).__name__,
            'message':str(error) if isinstance(error,(GoalStopped,ValueError)) else 'See preserved Provider evidence',
            'budget':b.snapshot(),'finished_at':now()})
        raise


def compare(cfg,case):
    from text2ifc_ifc2text.precision_compare_v12 import compare_roundtrip
    out=ROOT/cfg['output']/case['id'];result=load(out/'generate-result.json')
    if not result.get('ifc_path'):raise GoalStopped('NO_GENERATED_IFC')
    path=out/'compare-v1.2.json'
    if path.exists():raise GoalStopped('COMPARISON_ALREADY_EXISTS')
    frozen_text(case)
    report=compare_roundtrip(ROOT/case['source'],result['ifc_path'])
    report['generation_publication_status']=result['status']
    report['evidence_role']='Actual text-only Brief and Generator output; revealed diagnostic case'
    save(path,report);print(json.dumps(report['status'],indent=2))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['validate','brief','generate','compare','status'])
    parser.add_argument('--config',required=True);parser.add_argument('--case')
    args=parser.parse_args();cfg=load(ROOT/args.config)
    if args.command=='validate':return validate(cfg)
    if args.command=='status':print(json.dumps(budget_for(cfg).snapshot(),indent=2));return 0
    case=next(c for c in cfg['cases'] if c['id']==args.case)
    if args.command=='compare':compare(cfg,case)
    else:live(cfg,case,args.command)
    return 0


if __name__=='__main__':raise SystemExit(main())
