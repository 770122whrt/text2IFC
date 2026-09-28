"""One authorized hxp roundtrip on a hashed worktree, with fresh stage admission."""
from __future__ import annotations
import argparse
import compileall
import contextlib
import hashlib
import io
import json
import platform
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'src'))
from scripts.ifc2text.compact_campaign import runtime, verify_text
from scripts.ifc2text.run_goal import git
from text2ifc_ifc2text.goal_budget import GoalBudget, GoalStopped
from text2ifc_ifc2text.llm_pipeline import _write_json as save

OUT=ROOT/'dataset/processed/experiments/ifc2text-rerun-20260922'
SOURCE=ROOT/'dataset/external/bimnet/hxp.ifc'
PREVIOUS=ROOT/'dataset/processed/experiments/ifc2text-closed-wall-retry-20260921-v08/budget'
SCOPE=['src/text2ifc_agent','src/text2ifc_ifc2text','src/text2ifc_contract','src/text2ifc_compiler',
       'src/text2ifc_quality','src/text2ifc_extractor','src/text2ifc_knowledge','src/text2ifc_text',
       'prompts/agent','schemas','scripts/ifc2text','tests/ifc2text',
       'tests/agent','tests/compiler','tests/ifc_quality','pyproject.toml']
TARGETS=['tests/ifc2text','tests/agent/test_generation_v24_route.py',
    'tests/agent/test_space_geometry_projection_v12.py','tests/compiler/test_polygon_wall_hosts_v24.py',
    'tests/ifc_quality/test_floor_opening_identity.py','tests/ifc_quality/test_generated_ifc_gate.py',
    'tests/agent/test_prompt_registry.py','tests/agent/test_interactive_cli_generation.py',
    'tests/agent/test_phase6_2_openai_compat.py','tests/agent/test_public_brief_failure_evidence.py',
    'tests/agent/test_clarification_resume_preservation.py','tests/agent/test_phase6_5_changeset_apply.py',
    'tests/agent/test_phase6_4_geometry_truth.py','tests/agent/test_phase6_4_geometry_loop.py']

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()

def fingerprint(root=ROOT, scope=SCOPE):
    result={}
    for name in scope:
        path=root/name
        for p in ([path] if path.is_file() else sorted(path.rglob('*'))):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo'}:
                result[p.relative_to(root).as_posix()]=digest(p)
    return result

class RerunBudget(GoalBudget):
    def __init__(self,root,previous,*,inherited_reconstruction=14):
        if any(a['status']=='reserved' for a in previous['attempts']): raise GoalStopped('PREDECESSOR_UNSETTLED')
        self.inherited_reconstruction=inherited_reconstruction
        consumed=previous['historical']['tokens']+sum(a['charged_tokens'] for a in previous['attempts'])
        writing=previous['historical']['writing']+sum(a['stage']=='writing' for a in previous['attempts'])
        super().__init__(root,writing_calls=writing+1,reconstruction_calls=inherited_reconstruction+3,
                         tokens=previous['limits']['tokens'],historical_writing_calls=writing,historical_tokens=consumed)
    def snapshot(self):
        result=super().snapshot();result['calls']['reconstruction']+=self.inherited_reconstruction
        return result

def budget():
    authority=load(OUT/'authorization.json')
    if digest(PREVIOUS/'goal-budget.json')!=authority['predecessor_sha256']: raise GoalStopped('PREDECESSOR_CHANGED')
    return RerunBudget(OUT/'budget',authority['predecessor'])

def prepare():
    if (OUT/'authorization.json').exists(): raise GoalStopped('RUN_ALREADY_PREPARED')
    old=load(PREVIOUS/'goal-budget.json')
    inherited=load(PREVIOUS/'authorization.json')['predecessor_snapshot']['calls']['reconstruction']
    assert inherited+len(old['attempts'])==14
    save(OUT/'authorization.json',{'request':'2026-09-22: 先重跑一次看看',
        'scope':'one hxp pipeline, one writing call and at most three reconstruction-side calls; no outer retries',
        'predecessor':old,'predecessor_sha256':digest(PREVIOUS/'goal-budget.json'),
        'inherited_reconstruction':14,'cumulative_token_limit_unchanged':2000000})
    cfg=load(ROOT/'scripts/ifc2text/compact-campaign-v0.6.json')
    cfg.update(output=str(OUT.relative_to(ROOT)),writing_template='ifc2text-compact-narrator.v0.7',
        bim_json_schema_version='bim-json/2.4',description_version='0.8',
        brief_output_tokens=131072,max_reconstruction_calls=3,position_tolerance_mm=.1,dimension_tolerance_mm=.1)
    save(OUT/'config.json',cfg)
    from text2ifc_ifc2text.compact_pipeline import prepare_compact
    report=prepare_compact(SOURCE,OUT/'hxp')
    save(OUT/'original-source.json',{'path':str(SOURCE),'sha256':digest(SOURCE)})
    print({'prepared':True,'characters':report['characters'],'budget':budget().snapshot()['calls']})

def validate():
    import pytest, ifcopenshell, shapely
    from scripts.ifc2text.validate_goal import OfflineRecorder
    directory=OUT/'validation';directory.mkdir(exist_ok=False)
    before=fingerprint();save(directory/'source-snapshot.json',before)
    start=now(); observer=OfflineRecorder(); stream=io.StringIO()
    args=[*TARGETS,'-q','-p','no:cacheprovider','--basetemp='+str(directory/'pytest-temp'),
          '--junitxml='+str(directory/'tests.xml')]
    with observer.network_guard(),contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        code=int(pytest.main(args,plugins=[observer]))
    log=stream.getvalue();(directory/'pytest.log').write_text(log,encoding='utf-8')
    compiled=all(compileall.compile_dir(str(ROOT/p),quiet=1) for p in SCOPE if (ROOT/p).is_dir() and p.startswith(('src/','scripts/','tests/')))
    diff=git('diff','--check','--',*SCOPE)
    valid=code==0 and not observer.counts['failed'] and not observer.counts['skipped'] and not observer.setup_errors and not observer.network_attempts and compiled and before==fingerprint()
    record={'status':'admitted' if valid else 'blocked','stage':'IFC2Text 0.8 -> public Generation 2.4 -> Compare 1.0',
        'code_commit':git('rev-parse','HEAD'),'worktree_status':git('status','--porcelain','--untracked-files=all','--',*SCOPE),
        'authority':'exact file SHA-256 snapshot including uncommitted/new files; no implicit commit',
        'snapshot_sha256':digest(directory/'source-snapshot.json'),'config_sha256':digest(OUT/'config.json'),
        'started_at':start,'finished_at':now(),'python':platform.python_version(),'platform':platform.platform(),
        'ifcopenshell':ifcopenshell.version,'shapely':shapely.__version__,'command':args,'exit_code':code,
        'tests':observer.counts,'setup_errors':observer.setup_errors,'log_sha256':digest(directory/'pytest.log'),
        'compileall':compiled,'diff_check':not diff,'network_transport_attempted':bool(observer.network_attempts),
        'full_preflight':False,'source_scope':SCOPE,
        'matrix':{'complete_public_chain':['test_compact_public_v04.py','test_generation_v24_route.py'],
            'clarification_resume':'test_clarification_resume_preservation.py',
            'malformed_unsupported_transport':['test_public_brief_failure_evidence.py','test_phase6_2_openai_compat.py'],
            'atomic_change_and_recovery':['test_phase6_5_changeset_apply.py','test_interactive_cli_generation.py'],
            'source_isolation_compare':'tests/ifc2text','compile_reopen_geometry':['test_polygon_wall_hosts_v24.py','test_generated_ifc_gate.py']},
        'not_applicable':['damaged IFC repair operations and private mutation recipes'],
        'claim':'offline engineering admission only, not a model capability result'}
    save(directory/'admission.json',record)
    print({k:record[k] for k in ('status','tests','network_transport_attempted','compileall')});print(log[-2400:])
    return 0 if valid else 1

def admitted():
    record=load(OUT/'validation/admission.json')
    if record['status']!='admitted': raise GoalStopped('ADMISSION_REQUIRED')
    if digest(OUT/'validation/source-snapshot.json')!=record['snapshot_sha256'] or load(OUT/'validation/source-snapshot.json')!=fingerprint(): raise GoalStopped('CODE_CHANGED_SINCE_ADMISSION')
    if digest(OUT/'config.json')!=record['config_sha256']: raise GoalStopped('CONFIG_CHANGED')
    if digest(SOURCE)!=load(OUT/'original-source.json')['sha256']: raise GoalStopped('SOURCE_CHANGED')

def live(stage):
    admitted();cfg=load(OUT/'config.json');b=budget();out=OUT/'hxp';attempt=OUT/'reconstruction'
    marker=OUT/(stage+'-started.json')
    if marker.exists(): raise GoalStopped('SINGLE_ATTEMPT_ALREADY_STARTED')
    save(marker,{'stage':stage,'at':now(),'network_transport_attempted':False})
    cap=cfg['writing_output_tokens'] if stage=='write' else 131072
    conf,client,provider=runtime(cfg,b,'writing' if stage=='write' else 'reconstruction',cap)
    save(OUT/(stage+'-runtime.json'),{'model':conf.model,'provider':conf.provider_label,'max_output_tokens':cap,
        'max_input_tokens':conf.max_input_tokens,'sdk_retries':0,'provider_retries':0})
    try:
        if stage=='write':
            from text2ifc_ifc2text.compact_pipeline import write_compact
            result=write_compact(output=out,provider=provider,budget=b,template_id=cfg['writing_template'])
        else:
            from text2ifc_agent.session_store import SessionStore
            from text2ifc_agent.interactive_cli_flow import make_openai_design_brief_invoker,run_design_brief_clarification_loop,run_ready_session_to_ifc
            from text2ifc_agent.generation_budget import GenerationBudget,BudgetLimits
            limits=BudgetLimits(max_calls=3,max_tokens=2000000)
            text=verify_text(out)
            with SessionStore.open(attempt/'sessions.sqlite',artifact_root=attempt) as store:
                if stage=='brief':
                    session=store.create_session(original_input=text);GenerationBudget(session.run_dir,limits=limits)
                    save(attempt/'session.json',{'id':session.session_id,'run_dir':str(session.run_dir)})
                    invoker=make_openai_design_brief_invoker(config=conf,run_dir=session.run_dir,client_factory=lambda **_:client,
                        design_review_enabled=False,design_brief_schema_version=cfg['design_brief_schema'])
                    value=run_design_brief_clarification_loop(store=store,session=session.session_id,invoke_design_brief=invoker,user_answers=())
                    result={'status':value.status,'session_id':value.session_id,'session_hash':value.session_hash}
                else:
                    if load(OUT/'brief-result.json')['status']!='ready': raise GoalStopped('READY_BRIEF_REQUIRED')
                    value=run_ready_session_to_ifc(store=store,session=load(attempt/'session.json')['id'],provider_factory=lambda:provider,
                        generation_strategy='legacy_full',trace_level='debug',budget_limits=limits,bim_json_schema_version='bim-json/2.4')
                    result={'status':value.status,'session_hash':value.session_hash,'ifc_path':str(value.ifc_path) if value.ifc_path else None,
                        'generator_status':value.generator_status,'audit_status':value.audit_status}
        save(OUT/(stage+'-result.json'),result)
        admitted()
        print(result);print({'calls':b.snapshot()['calls'],'tokens':b.snapshot()['tokens_used_or_reserved']})
    except Exception as error:
        b.halt(stage+'_FAILED');save(OUT/(stage+'-terminal.json'),{'status':'failed','error_type':type(error).__name__,
            'reason':str(error) if isinstance(error,GoalStopped) else 'See preserved stage evidence','budget':b.snapshot()})
        raise

def compare():
    from text2ifc_ifc2text.precision_compare_v10 import compare_roundtrip
    run=Path(load(OUT/'reconstruction/session.json')['run_dir'])
    if not (run/'output.ifc').exists(): raise GoalStopped('NO_GENERATED_IFC')
    report=compare_roundtrip(SOURCE,run/'output.ifc')
    report['generation_result']=load(OUT/'generate-result.json') if (OUT/'generate-result.json').exists() else {'status':'incomplete'}
    save(OUT/'compare-v1.0.json',report);print(report.get('summary',report['status']))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','validate','write','brief','generate','compare','status'])
    args=parser.parse_args()
    if args.command=='validate': raise SystemExit(validate())
    elif args.command in {'write','brief','generate'}: live(args.command)
    elif args.command=='status': print(budget().snapshot())
    else: globals()[args.command]()
