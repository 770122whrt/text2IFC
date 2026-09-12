"""Review stage results and scoped resolutions before enabling transport."""
import datetime as dt, hashlib, json, subprocess, sys, time
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909/admission'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=OUT/'admission.json'; record=json.loads(path.read_text(encoding='utf-8'))
    assert record['status']=='blocked'
    assert len(record['commands'])==1 and record['commands'][0]['exit_code']==1 and not record['commands'][0]['timeout']
    tests=list(ET.parse(OUT/'pytest.xml').iter('testcase'))
    failed=[t for t in tests if t.find('failure') is not None or t.find('error') is not None]
    expected={'test_live_repl_ready_session_compiles_ifc_with_fix_acceptance_report',
              'test_live_repl_routes_geometry_failure_through_audit_before_final_status',
              'test_live_repl_records_provider_failure_without_traceback'}
    assert {t.get('name') for t in failed}==expected
    assert not any(t.find('skipped') is not None for t in tests)
    for xml in ['repl-budget-green.xml','unknown-usage-green.xml']:
        cases=list(ET.parse(OUT/xml).iter('testcase'))
        assert cases and all(not any(t.find(tag) is not None for tag in ['failure','error','skipped']) for t in cases)
    scale=json.loads((OUT/'scale-public-04/scale-result.json').read_text(encoding='utf-8'))
    assert scale['passed']
    # Preserve the initial failed stage record before additive resolution.
    with (OUT/'initial-stage-result.json').open('x',encoding='utf-8') as f: json.dump(record,f,ensure_ascii=False,indent=2)
    for number,cmd in enumerate([[sys.executable,'-m','compileall','-q','src','tests','scripts'],
        ['git','diff','--check','--','src','tests','scripts','prompts','schemas','docs']]):
        log=OUT/f'final-check-{number+1}.log'; start=time.monotonic();started=dt.datetime.now(dt.timezone.utc).isoformat()
        with log.open('x',encoding='utf-8') as output:
            result=subprocess.run(cmd,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,timeout=180)
        record['commands'].append({'command':cmd,'started_at':started,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'seconds':time.monotonic()-start,'exit_code':result.returncode,'timeout':False,'log':log.name,'log_sha256':sha(log)})
        assert result.returncode==0
    mapping={
      'public_input_brief_clarification_resume':['test_design_brief','test_live_clarification','test_interactive_cli_flow','test_interactive_cli_session','test_phase6_2_fix_repl_cli'],
      'provider_output_and_bounded_transport_seam':['test_phase6_2_openai_compat','test_design_brief_attempt_preservation','test_phase6_1_live'],
      'prompt_registry_versions_context':['test_generation_authoring_contract','test_generation_semantic_versions','test_changeset_context'],
      'early_field_atomic_scope_type_preservation':['test_early_field_recovery','test_phase6_5_changeset_apply','test_phase6_5_scoped_loop','test_repair_fact_delta'],
      'public_complete_to_final_reopened_ifc':['test_semantic_public_paths','test_interactive_cli_generation'],
      'staged_package_recovery_global_gates':['test_phase6_5_staged_generation','test_phase6_5_revision_gates'],
      'compile_relationships_geometry_semantics':['tests.compiler','tests.contract_v2','tests.ifc_quality','test_generation_semantic_closure'],
      'budget_persistence_failure_publication_cycle':['test_generation_task_budget','test_phase6_4_feedback_loop','test_phase6_5_revision_gates'],
    }
    matrix={}
    for seam,parts in mapping.items():
        matched=[t for t in tests if any(p in t.get('classname','') for p in parts)]
        assert matched,seam
        matrix[seam]={'status':'passed_with_scoped_resolution' if any(t in failed for t in matched) else 'passed',
                      'test_ids':[t.get('classname')+'::'+t.get('name') for t in matched]}
    matrix['scale']={'status':'passed','evidence':'scale-public-04/scale-result.json',
        'limits':'Three storeys only; parent Windows peak working set, no child memory or large-building claim'}
    matrix['repair_source_private_gold']={'status':'not_applicable','reason':'Text-only Generation; no IFC source or private benchmark is supplied. Repair live admission is not covered.'}
    record['matrix']=matrix
    record['scoped_resolution']={'initial_failures':sorted(expected),'cause':'Legacy offline Brief fixture omitted simulated token usage. Conservative unknown-use budget block is correct.',
        'changed_files':['tests/agent/test_phase6_2_fix_repl_cli.py','tests/agent/test_generation_task_budget.py'],
        'evidence':['repl-red.xml','repl-budget-green.xml','unknown-usage-green.xml'],
        'production_source_changed':False,'claims':'Offline stage admission only, not real reliability or system capability'}
    record['scale_harness_attempts']={'scale-public':'Missing report sidecar in hand-authored fixture; no Provider transport',
        'scale-public-02':'Fake Brief empty provenance rejected',
        'scale-public-03':'Compiled; instrumentation accessed a prompt field not retained by fake',
        'scale-public-04':'Measured public path passed'}
    import ifcopenshell, importlib.metadata as md
    record['dependencies']={n:md.version(n) for n in ['ifcopenshell','pytest','jsonschema','openai']}
    record['worktree_scoped']=subprocess.check_output(['git','status','--short','--','src','tests','scripts','prompts','schemas','docs','.planning'],cwd=ROOT,text=True)
    # Include all source dependencies and tests in the frozen transport guard.
    for folder in ['src','tests/agent','tests/compiler','tests/contract_v2','tests/ifc_quality','prompts/agent','schemas','scripts/agent']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.md','.exp'}:
                record['files_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    for p in [ROOT/'.tmp/check_two_storey_review.py',OUT.parent/'frozen-expectations.json',OUT.parent/'request.txt']:
        record['files_sha256'][p.relative_to(ROOT).as_posix()]=sha(p)
    record['evidence_hashes']={p.relative_to(OUT).as_posix():sha(p) for p in OUT.glob('*.xml')}
    record['evidence_hashes']['scale-public-04/scale-result.json']=sha(OUT/'scale-public-04/scale-result.json')
    record['status']='admitted';record['admitted_at']=dt.datetime.now(dt.timezone.utc).isoformat()
    record['invalidation']='Changes to public entry, schema/prompt/transport/truth/transaction or validation rules require fresh scope assessment; ordinary fixes need affected-path revalidation.'
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':record['status'],'initial_tests':record['tests'],'scoped_xml':['19 passed','13 passed'],'seams':list(matrix)},ensure_ascii=False))
if __name__=='__main__':main()
