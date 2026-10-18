"""Aggregate earned offline evidence for this formal stage; never runs models.

Receipts are provenance records from the trusted test controller, not signed CI
attestations. They bind actual logs, selected test sources and relevant executable
sources. A passed flag alone is never an admission. This command runs no tests,
installs nothing and does not read credentials or silently launch Full Preflight.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import uuid

from . import demo_workflow as carrier
from . import formal_workflow as formal
from .contracts import PUBLIC_FILES, read_json, safe_path, sha256, write_json
from .ledger import Ledger, TERMINAL

ROOT = carrier.REPO
HERE = 'scripts/ifc_repair/repair_comparison/'
TESTS = 'tests/ifc_repair/repair_comparison/'
SCHEMA = 'repair-comparison-formal-admission/0.1'
RUNTIME_FILES = {
    'budget.py','container_command.py','container_relay.py','container_tools.py','contracts.py',
    'controller_owner.py','demo_workflow.py','direct_runner.py','experiment.py','isolated_b.py',
    'isolated_direct.py','isolated_dsh.py','ledger.py','ours_adapter.py','provider_observer.py',
    'neutral_tools.py','wire_gateway.py','dsh_search.py','dsh/native_worker.py','dsh/question-bridge.mjs',
}
FORMAL_FILES = {'formal_workflow.py','formal_scoring.py','formal_batch.py','task_review.py',
                'authoring.py','damage_geometry.py','inspection.py','viewer.py','viewer_compatibility.py'}
TECHNICAL_CHECKS = {
    'author_contract_bound','clarification_contract_bound','damage_and_preservation_recomputed',
    'denominators_match','exact_removed_product_set','input_hash_bindings','native_recomputed',
    'public_facts_match_measurements','public_files_only','public_request_bound',
    'relation_edges_recomputed','removed_targets_not_visible','retained_geometry_recomputed',
    'retained_reference_geometry_unchanged','wall_closure_recomputed',
}
# Coverage comes from concrete executed targets, not caller-provided check labels.
COVERAGE = {
    TESTS+'test_public_repair_flow.py': {'complete','apply_compile','reopen','source_immutability'},
    TESTS+'test_b_publication_control.py': {'terminal_publication'},
    TESTS+'test_ours_adapter.py': {'clarification','resume','malformed','deterministic_binding'},
    TESTS+'test_wire_gateway.py': {'truncated','wire_accounting'},
    TESTS+'test_ledger.py': {'persistence','budget'},
    TESTS+'test_direct_runner.py': {'private_isolation','unique_submission'},
    TESTS+'test_experiment_cli.py': {'cli'},
    TESTS+'test_formal_workflow.py': {'order','freeze','scoring_summary'},
    TESTS+'test_formal_scoring.py': {'scoring'},
    'tests/ifc_repair/test_scene_repair_api.py::test_scene_application_write_failure_is_atomic_and_source_is_immutable': {'atomic_rollback'},
    'tests/test_formal_admission.py::test_public_scene_unsupported_is_terminal_and_keeps_source': {'unsupported'},
    'tests/test_formal_admission.py': {'admission_guard'},
}
REQUIRED_CONTRACTS = set().union(*COVERAGE.values())
REVISION_SCHEMA = 'repair-comparison-formal-admission-revision/0.1'
REVISION_SUITE_SCHEMA = 'repair-comparison-revision-suite/0.1'
REVISION_SOURCES = {
    HERE+'formal_admission.py': 'admission',
    HERE+'isolated_direct.py': 'AC', HERE+'direct_runner.py': 'AC',
    HERE+'demo_workflow.py': 'D',
    HERE+'isolated_dsh.py': 'D',
    **{'src/text2ifc_ifc_repair/'+name: 'B' for name in
       ('door_geometry.py','door_resolution.py','operations/door.py','geometry.py','operations/hosted_opening.py',
        'window_geometry.py','operations/window.py','production_evidence.py','scene_grounding.py','api.py','resolution_flow.py')},
}
REVISION_TESTS = {
    'tests/test_formal_admission.py': {'admission'},
    TESTS+'test_submission_protocol.py': {'AC'},
    TESTS+'test_d_budget_terminal.py': {'D'},
    TESTS+'test_d_submission_envelope.py': {'D'},
    TESTS+'test_d_submission_native_seam.py': {'D'},
    TESTS+'test_d_submission_admission.py': {'admission'},
    'tests/ifc_repair/test_door_installation_anchor.py': {'B'},
    'tests/ifc_repair/test_door_installation_legacy_compatibility.py': {'B'},
    'tests/ifc_repair/test_window_installation_anchor.py': {'B'},
    'tests/ifc_repair/test_public_semantic_and_base_authority.py': {'B'},
    'tests/ifc_repair/test_door_direct_body_reference.py': {'B'},
    'tests/ifc_repair/test_door_resolution.py': {'B'},
    'tests/ifc_repair/test_hosted_opening_normal_origin.py': {'B'},
    'tests/ifc_repair/test_host_body_context.py': {'B'},
    TESTS+'test_b_common_installation_native_seam.py': {'B'},
}
REVISION_NATIVE_TEST = TESTS+'test_formal_revision_seams.py'
REVISION_D_SUBMISSION_NATIVE_TEST = TESTS+'test_d_submission_native_seam.py'
REVISION_B_INSTALLATION_NATIVE_TEST = TESTS+'test_b_common_installation_native_seam.py'
REVISION_EXTRA_TESTS = {TESTS+name for name in ('test_direct_runner.py','test_isolated_direct.py',
    'test_formal_public_path.py','test_batch_workflow.py','test_wire_gateway.py')}
REVISION_EXTRA_TESTS.update('tests/ifc_repair/'+name for name in (
    'test_window_application.py','test_window_placement_direction.py','test_window_semantic_authoring.py',
    'test_production_evidence.py','test_semantic_attribute_units.py','test_scene_grounding.py',
    'test_resolution_flow.py','test_draft_authority_set_semantics.py'))
REVISION_EXTRA_TESTS.add('tests/ifc_repair/test_door_application.py')


def _need(condition, code):
    if not condition:
        raise ValueError(code)


def run_revision_suite(command, log, *, phase='green'):
    """Execute a focused pytest command and capture its actual before/after state.

    Call this before applying a fix for phase='red'. A red log is immutable
    historical evidence, not a green admission. No live-model env is enabled here.
    """
    _need(phase in {'red','green'}, 'REVISION_PHASE_REQUIRED')
    targets=_targets(command)
    _need(all(t.split('::')[0] in {*REVISION_TESTS,*REVISION_EXTRA_TESTS,REVISION_NATIVE_TEST} for t in targets),
          'REVISION_TEST_TARGET_NOT_REGISTERED')
    log=safe_path(Path(log)); _need(not log.exists(), 'REVISION_LOG_EXISTS')
    receipt_path=log.with_suffix(log.suffix+'.receipt.json')
    _need(not receipt_path.exists(), 'REVISION_RECEIPT_EXISTS')
    before=capture_sources('admission')
    tests={t.split('::')[0]:sha256(ROOT/t.split('::')[0]) for t in targets}
    started=datetime.now(timezone.utc).isoformat()
    completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',errors='replace')
    ended=datetime.now(timezone.utc).isoformat()
    after=capture_sources('admission')
    test_after={path:sha256(ROOT/path) for path in tests}
    log.parent.mkdir(parents=True,exist_ok=True)
    log.write_text(completed.stdout+completed.stderr,encoding='utf8')
    receipt={'schema_version':REVISION_SUITE_SCHEMA,'stage':carrier.FORMAL_STAGE,
        'phase':phase,'command':command,'exit_code':completed.returncode,
        'run_id':uuid.uuid4().hex,'started_at':started,'ended_at':ended,
        'capture_source':'actual subprocess stdout/stderr; source and test hashes before and after',
        'source_bindings_before':before,'source_bindings_after':after,
        'test_bindings_before':tests,'test_bindings_after':test_after,'log':file_ref(log)}
    write_json(receipt_path,receipt)
    return receipt_path


def file_ref(path):
    path = safe_path(Path(path))
    _need(path.is_file(), 'EVIDENCE_FILE_REQUIRED:'+str(path))
    return {'path':str(path),'sha256':sha256(path)}


def _ref(ref):
    path = safe_path(Path(ref['path']))
    _need(path.is_file() and sha256(path)==ref['sha256'], 'EVIDENCE_CHANGED:'+str(path))
    return path


def capture_sources(scope):
    """Capture before a scoped run; compare again afterwards before receipt use."""
    _need(scope in {'runtime','formal','admission','execution'}, 'UNKNOWN_RECEIPT_SCOPE')
    names = set(RUNTIME_FILES)
    if scope in {'formal','admission','execution'}: names |= FORMAL_FILES
    if scope in {'admission','execution'}: names.add('formal_admission.py')
    if scope=='execution': names.add('batch_operator.py')
    paths = {ROOT/HERE/name for name in names}
    for folder in ('src/text2ifc_ifc_repair','src/text2ifc_agent'):
        paths.update((ROOT/folder).rglob('*.py'))
    for folder in ('schemas/agent','prompts/agent'):
        paths.update((ROOT/folder).rglob('*.json'))
    if scope=='execution':
        paths.update((ROOT/'src/text2ifc_knowledge').rglob('*.py'))
        paths.update((ROOT/'schemas/ifc/knowledge').rglob('*.json'))
    _need(all(p.is_file() for p in paths), 'RECEIPT_SOURCE_MISSING')
    return {p.relative_to(ROOT).as_posix():sha256(p) for p in sorted(paths)}


def _pytest_summary(text, exit_code):
    _need(exit_code==0, 'PYTEST_EXIT_NOT_ZERO')
    counts = re.findall(r'\b([0-9]+) passed\b', text)
    _need(bool(counts) and int(counts[-1])>0, 'PYTEST_SUCCESS_SUMMARY_REQUIRED')
    _need(not re.search(r'\b[1-9][0-9]* (?:failed|errors?|skipped|xfailed|xpassed|deselected)\b', text),
          'PYTEST_FAILED_OR_PARTIAL_SELECTION')
    return int(counts[-1])


def _targets(command):
    _need(isinstance(command,list) and all(isinstance(a,str) for a in command), 'PYTEST_COMMAND_REQUIRED')
    try: args=command[command.index('pytest')+1:]
    except ValueError as error: raise ValueError('PYTEST_COMMAND_REQUIRED') from error
    _need(not any(a in {'-k','-m','--collect-only','--lf','--last-failed','--ff','--failed-first'}
                  or a.startswith(('--deselect','--ignore','-k=','-m=')) for a in args), 'PYTEST_SELECTION_NOT_COMPLETE')
    targets=[a.replace('\\','/') for a in args if a.replace('\\','/').startswith('tests/') and '.py' in a]
    _need(bool(targets), 'PYTEST_TEST_TARGETS_REQUIRED')
    return targets


def make_suite_receipt(log, *, command, exit_code, scope, source_bindings, capture_source):
    """Record an already earned run, retaining how its output was captured.

    source_bindings must describe that run's unchanged sources. This function
    does not run pytest and cannot turn a historical log into a fresh test run.
    Tool-output transcripts must say so; do not label them shell redirections.
    """
    targets=_targets(command)
    log=file_ref(log)
    count=_pytest_summary(Path(log['path']).read_text(encoding='utf8'),exit_code)
    return {'schema_version':'repair-comparison-scoped-receipt/0.1','stage':carrier.FORMAL_STAGE,
            'scope':scope,'command':command,'exit_code':exit_code,'passed_count':count,
            'log':log,'capture_source':capture_source,'source_bindings':source_bindings,
            'test_bindings':{t.split('::')[0]:sha256(ROOT/t.split('::')[0]) for t in targets}}


def validate_suite_receipt(receipt, *, revalidated_sources=frozenset()):
    if not isinstance(receipt,dict): receipt=read_json(safe_path(Path(receipt)))
    _need(receipt.get('schema_version')=='repair-comparison-scoped-receipt/0.1'
          and receipt.get('stage')==carrier.FORMAL_STAGE and receipt.get('capture_source'), 'SCOPED_RECEIPT_REQUIRED')
    targets=_targets(receipt['command'])
    for target in targets:
        name=Path(target.split('::')[0]).name
        if name in {'test_formal_workflow.py','test_formal_scoring.py','test_formal_public_path.py'}:
            _need(receipt['scope'] in {'formal','admission','execution'}, 'FORMAL_SUITE_SCOPE_REQUIRED')
        if name=='test_formal_admission.py':
            _need(receipt['scope'] in {'admission','execution'}, 'ADMISSION_SUITE_SCOPE_REQUIRED')
    count=_pytest_summary(_ref(receipt['log']).read_text(encoding='utf8'),receipt['exit_code'])
    _need(count==receipt['passed_count'], 'PYTEST_COUNT_CHANGED')
    current=capture_sources(receipt['scope'])
    _need(set(receipt['source_bindings'])==set(current) and all(
        receipt['source_bindings'][path]==value or path in revalidated_sources
        for path,value in current.items()), 'SCOPED_SOURCE_BINDING_STALE')
    expected={t.split('::')[0]:sha256(ROOT/t.split('::')[0]) for t in targets}
    _need(expected==receipt['test_bindings'], 'SCOPED_TEST_BINDING_STALE')
    coverage=set()
    for target, contracts in COVERAGE.items():
        if any(selected==target or ('::' not in selected and target.startswith(selected+'::')) for selected in targets):
            coverage |= contracts
    return coverage


EXECUTION_TEST = TESTS+'test_later_ten_execution.py'
EXECUTION_NATIVE_TEST = TESTS+'test_later_ten_native.py'
EXECUTION_EXTRA_CONTRACTS = {'deferred_metrics','batch_budget','operator_alerts','card_scope','property_runtime_binding'}
COVERAGE[EXECUTION_TEST] = {'order','freeze',*EXECUTION_EXTRA_CONTRACTS}
EXECUTION_REQUIRED_CONTRACTS = (REQUIRED_CONTRACTS - {'scoring','scoring_summary'}) | EXECUTION_EXTRA_CONTRACTS


def build_execution_admission(plan_path, *, suite_receipts, native_report, native_suite_log=None, output=None):
    """Admit real execution with deferred scoring; retain every safety gate."""
    plan=formal.verify_execution_plan(plan_path)
    configuration=plan['configuration'];bindings=carrier.bindings(configuration)
    coverage=set();targets=set();sealed=[]
    receipts=[read_json(safe_path(Path(path))) for path in suite_receipts]
    # Only admission aggregation changed after the broad gate. Its own fresh
    # guard tests permit reuse of unchanged runtime tests, not new runtime code.
    aggregation_revalidated=any(receipt.get('source_bindings')==capture_sources('execution')
        and {'tests/test_formal_admission.py',EXECUTION_TEST,TESTS+'test_execution_admission_reuse.py'}
            <= set(_targets(receipt['command'])) for receipt in receipts)
    refreshed={HERE+'formal_admission.py'} if aggregation_revalidated else set()
    for receipt_path in suite_receipts:
        receipt=read_json(safe_path(Path(receipt_path)))
        _need(receipt.get('scope')=='execution', 'EXECUTION_RECEIPT_SCOPE_REQUIRED')
        coverage |= validate_suite_receipt(receipt,revalidated_sources=refreshed)
        targets.update(_targets(receipt['command']));sealed.append(file_ref(receipt_path))
    missing=EXECUTION_REQUIRED_CONTRACTS-coverage
    _need(not missing, 'MISSING_EXECUTION_CONTRACTS:'+','.join(sorted(missing)))
    if EXECUTION_NATIVE_TEST not in targets:
        # The actual four-runtime test passed in a mixed run whose separate RSS
        # fixture could not import pytest inside the image. Recheck that fixture
        # alone; never relabel the mixed run green or rerun the passed runtimes.
        _need(native_suite_log is not None and TESTS+'test_later_ten_rss_native.py' in targets,
              'FOUR_REAL_RUNTIMES_NOT_TESTED')
        mixed=Path(native_suite_log).read_text(encoding='utf8')
        failed=re.findall(r'^FAILED ([^\s]+)',mixed,re.MULTILINE)
        _need(failed==[EXECUTION_NATIVE_TEST+'::test_linux_worker_rss_is_independent_of_warmed_parent']
              and re.search(r'\b1 failed, 1 passed\b',mixed)
              and "No module named 'pytest'" in mixed, 'UNRESOLVED_NATIVE_GATE_FAILURE')
    native=read_json(safe_path(Path(native_report)))
    _need(native.get('all_passed') is True and native.get('real_models_called') is False
          and native.get('property_b_image')==configuration['b']['image'], 'KEYLESS_NATIVE_EVIDENCE_REQUIRED')
    current=capture_sources('execution');prior=native.get('source_bindings',{})
    _need(set(prior)==set(current) and all(prior[path]==value or path in refreshed
          for path,value in current.items()), 'NATIVE_EXECUTION_SOURCES_STALE')
    rows=native.get('four_runtime_clarification_resume',[])
    _need(len(rows)==4 and {r['arm'] for r in rows}==set('ABCD'), 'FOUR_RUNTIME_ROWS_REQUIRED')
    root=safe_path(Path(native['root']));ledger=Ledger(root/'control.sqlite')
    native_bindings=[]
    for row in rows:
        _need(all(row.get(k) is True for k in ('source_unchanged','budget_persisted','submitted')),
              'NATIVE_SAFETY_OR_RESUME_FAILED')
        state=ledger.snapshot(row['run_id']);artifact=state.get('artifact')
        _need(state['status']=='submitted' and state['arm']==row['arm']
              and state['mode']=='real_runtime_fake_model' and state['usage']['coverage']=='complete',
              'NATIVE_TERMINAL_OR_ACCOUNTING_REQUIRED')
        _need(artifact and sha256(safe_path(Path(artifact['path'])))==artifact['sha256'], 'NATIVE_ARTIFACT_CHANGED')
        native_bindings.append(file_ref(artifact['path']))
    _need(carrier.bindings(configuration)==bindings and formal.verify_execution_plan(plan_path)==plan,
          'EXECUTION_CHANGED_DURING_ADMISSION')
    result={'schema_version':'repair-comparison-execution-admission/0.1','stage':carrier.FORMAL_STAGE,
            'passed':True,'configuration':configuration,'bindings':bindings,'plan':file_ref(plan_path),
            'suite_receipts':sealed,'native_report':file_ref(native_report),'native_artifacts':native_bindings,
            'covered_contracts':sorted(coverage),'metrics_status':'deferred','real_models_called':False,
            'scope':'Current reviewed batch execution; no scoring or capability conclusion.',
            'created_at':datetime.now(timezone.utc).isoformat()}
    if native_suite_log:result['mixed_native_log']=file_ref(native_suite_log)
    if output:write_json(output,result)
    return result


EXECUTION_COMMON_FIXES = {
    'storey': ('src/text2ifc_ifc_repair/scene_context.py', {
        'tests/ifc_repair/test_scene_storey_authority.py','tests/ifc_repair/test_scene_context.py',
        'tests/ifc_repair/test_spatial_grounding.py','tests/ifc_repair/test_scene_grounding.py'}),
    'parameter_clarification': ('src/text2ifc_ifc_repair/api.py', {
        'tests/ifc_repair/test_structural_clarification_family.py',
        'tests/ifc_repair/test_clarification_state.py','tests/ifc_repair/test_scene_repair_api.py'}),
    'validation_process': ('src/text2ifc_ifc_repair/evaluation.py', {
        'tests/ifc_repair/test_validation_process_isolation.py',
        'tests/ifc_repair/test_validation_acceleration.py','tests/ifc_repair/test_validation_cache.py'}),
}


def execution_revision_changes(previous,current, *, common_scope='storey'):
    """Narrow common fix: no model, budget, prompt, schema or other lane drift."""
    _need({k:v for k,v in previous.items() if k!='files'}==
          {k:v for k,v in current.items() if k!='files'}, 'EXECUTION_REVISION_RUNTIME_DRIFT')
    old,new=previous['files'],current['files']
    _need(old.keys()==new.keys(),'EXECUTION_REVISION_FILE_SET_CHANGED')
    changed={name:{'before':old[name],'after':value} for name,value in new.items() if old[name]!=value}
    _need(common_scope in EXECUTION_COMMON_FIXES,'EXECUTION_REVISION_SCOPE_UNKNOWN')
    allowed={HERE+'formal_admission.py',EXECUTION_COMMON_FIXES[common_scope][0]}
    _need(bool(changed) and set(changed)<=allowed,'EXECUTION_REVISION_OUTSIDE_COMMON_SCOPE')
    return changed


def validate_process_native_row(row):
    """A process revision must keep the real default validator and its bounds."""
    metrics=row.get('validation_metrics',{})
    peak=metrics.get('peak_rss_bytes');wall=metrics.get('wall_seconds')
    _need(row.get('validation_status')=='passed'
          and row.get('baseline_model_reused') is False
          and row.get('candidate_model_reused') is False
          and metrics.get('mode')=='accelerated' and metrics.get('worker_count')==2
          and metrics.get('rss_limit_bytes')==4*1024**3
          and isinstance(peak,(int,float)) and 0<peak<=4*1024**3
          and isinstance(wall,(int,float)) and 0<=wall<=180,
          'EXECUTION_NATIVE_VALIDATION_BOUNDS_REQUIRED')


def build_execution_revision(parent_path, *, suite_receipts, red_log, native_report, baseline_source,
                             common_scope='storey', output=None):
    parent=read_json(safe_path(Path(parent_path)))
    _need(parent.get('schema_version') in {'repair-comparison-execution-admission/0.1',
                                         'repair-comparison-execution-revision/0.1'}
          and parent.get('passed') is True and parent.get('metrics_status')=='deferred', 'EXECUTION_PARENT_REQUIRED')
    _sealed_references(parent)
    plan=formal.verify_execution_plan(_ref(parent['plan']))
    configuration=plan['configuration'];current=carrier.bindings(configuration)
    _need(configuration==parent['configuration'],'EXECUTION_REVISION_CONFIGURATION_DRIFT')
    changed=execution_revision_changes(parent['bindings'],current,common_scope=common_scope)
    product,required_tests=EXECUTION_COMMON_FIXES[common_scope]
    _need(product in changed and sha256(Path(baseline_source))==changed[product]['before'],
          'EXECUTION_BASELINE_SOURCE_REQUIRED')
    red=file_ref(red_log);text=Path(red['path']).read_text(encoding='utf8')
    _need(re.search(r'\b[1-9][0-9]* failed\b',text),'EXECUTION_RED_REQUIRED')
    receipts=[read_json(Path(p)) for p in suite_receipts]
    current_sources=capture_sources('execution')
    guard=TESTS+'test_execution_revision_guard.py'
    _need(any(r['source_bindings']==current_sources and guard in _targets(r['command']) for r in receipts),
          'EXECUTION_REVISION_FRESH_GUARD_REQUIRED')
    targets=set()
    for receipt in receipts:
        validate_suite_receipt(receipt,revalidated_sources={HERE+'formal_admission.py'})
        targets.update(_targets(receipt['command']))
    _need(required_tests<=targets,'EXECUTION_COMMON_FAMILY_REQUIRED')
    native=read_json(safe_path(Path(native_report)))
    _need(native.get('real_models_called') is False and native.get('all_passed') is True,
          'EXECUTION_OFFLINE_NATIVE_REQUIRED')
    rows=native.get('rows',[])
    expected_cases={
        'storey': {'formal-011','formal-012'},
        'parameter_clarification': {'formal-014'},
        'validation_process': {'formal-013','formal-018'},
    }[common_scope]
    _need({r.get('case') for r in rows}==expected_cases and len(rows)==len(expected_cases),
          'EXECUTION_PUBLIC_NATIVE_CASES_REQUIRED')
    for row in rows:
        _need(row.get('status')=='succeeded' and row.get('publishable') is True
              and row.get('source_unchanged') is True, 'EXECUTION_NATIVE_SAFETY_FAILED')
        _need(sha256(Path(row['source_path']))==row['source_sha256'], 'EXECUTION_NATIVE_SOURCE_CHANGED')
        _need(sha256(Path(row['artifact_path']))==row['artifact_sha256'], 'EXECUTION_NATIVE_ARTIFACT_CHANGED')
        if common_scope=='parameter_clarification':
            _need(all(row.get(key) is True for key in ('clarification_observed','no_early_publication',
                  'same_run','budget_persisted')), 'EXECUTION_NATIVE_RESUME_REQUIRED')
        if common_scope=='validation_process':
            validate_process_native_row(row)
    binding_key={
        'storey':'scene_context_sha256', 'parameter_clarification':'api_sha256',
        'validation_process':'evaluation_sha256',
    }[common_scope]
    _need(native.get(binding_key)==current['files'][product], 'EXECUTION_NATIVE_PRODUCT_STALE')
    result={'schema_version':'repair-comparison-execution-revision/0.1','stage':carrier.FORMAL_STAGE,
        'passed':True,'configuration':configuration,'bindings':current,'plan':parent['plan'],
        'parent_admission':file_ref(parent_path),'changed_sources':changed,'common_scope':common_scope,
        'suite_receipts':[file_ref(p) for p in suite_receipts],'red_log':red,
        'native_report':file_ref(native_report),'baseline_source':file_ref(baseline_source),
        'metrics_status':'deferred','real_models_called':False,
        'scope':'Common '+common_scope+' defect; revealed-case offline replay, not blind improvement.',
        'created_at':datetime.now(timezone.utc).isoformat()}
    if output:write_json(output,result)
    return result


def require_contracts(coverage):
    missing=REQUIRED_CONTRACTS-set(coverage)
    _need(not missing, 'MISSING_CONTRACTS:'+','.join(sorted(missing)))


def validate_technical_plan(plan_path):
    from .task_review import _binding
    plan=formal.verify_plan(plan_path)
    config=plan['configuration']
    _need(len(plan['cases'])==len(config['case_ids'])==20 and len(config['order'])==80, 'TWENTY_FROZEN_CASES_REQUIRED')
    normalized=carrier.batch_configuration(cases_root=config['cases_root'],case_ids=config['case_ids'],
        budgets=config['budgets'],stage=carrier.FORMAL_STAGE,models=config['models'],scene_grounding=True,
        b=config.get('b'),d_web_search=config.get('d_web_search'),d_web_access=config.get('d_web_access'),
        b_validation_corrections=config.get('b_validation_corrections'))
    _need(config==normalized, 'FORMAL_CONFIGURATION_CHANGED')
    sources=set()
    evidence=[]
    for row in plan['cases']:
        case=safe_path(Path(config['cases_root'])/row['case_id'])
        task=read_json(case/'private/task.json')
        report=read_json(case/'private/technical-review.json')
        checked=formal.check_candidate(case)
        _need(checked['valid'] and checked.get('review_accepted'), 'TASK_CHECK_FAILED:'+case.name)
        _need(report.get('schema_version')=='repair-comparison-technical-review/0.1' and report.get('case_id')==case.name
              and report.get('passed') is True and report.get('accepted') is True and not report.get('errors'), 'TECHNICAL_REVIEW_REQUIRED:'+case.name)
        _need(TECHNICAL_CHECKS <= set(report.get('checks',{})) and all(v is True for v in report['checks'].values()), 'TECHNICAL_CHECKS_MISSING_OR_FAILED:'+case.name)
        current=_binding(case,task)
        _need(report.get('input_bindings')==current and task['review'].get('input_bindings')==current, 'TECHNICAL_REVIEW_STALE:'+case.name)
        _need(current['G']==task['source_sha256'] and task['source_sha256'] not in sources, 'DIFFERENT_SOURCE_IFC_REQUIRED')
        sources.add(task['source_sha256'])
        for role in ('G','D'):
            native=report.get('native_validation',{}).get(role,{})
            _need(native.get('passed') is True and native.get('express_rules') is True and native.get('diagnostic_count')==0, 'NATIVE_VALIDATION_REQUIRED:'+case.name)
        evidence.append({'case_id':case.name,'technical_review':file_ref(case/'private/technical-review.json')})
    return plan,evidence


def validate_runtime_evidence(report_path, log_path, *, configuration, current_bindings):
    report=read_json(safe_path(Path(report_path)))
    _pytest_summary(safe_path(Path(log_path)).read_text(encoding='utf8'),0)
    _need(report.get('stage')==carrier.FORMAL_STAGE and report.get('real_models_called') is False
          and report.get('evidence_class')=='real_runtime_fake_model' and not report.get('error'), 'REAL_RUNTIME_OFFLINE_RECEIPT_REQUIRED')
    required={'a_c_same_generic_tools','abcd_two_complete_public_inputs','b_scene_02_two_operations',
              'd_native_budget_stop','formal_binding_recorded','service_safe_restart'}
    _need(all(report.get('checks',{}).get(c) is True for c in required), 'RUNTIME_SEAMS_INCOMPLETE')
    bound=report['bindings']
    _need(bound['images']==current_bindings['images'] and bound['models']==configuration['models'], 'RUNTIME_IMAGE_OR_MODEL_CHANGED')
    expected=capture_sources('runtime')
    _need(all(bound['files'].get(k)==v for k,v in expected.items()), 'RUNTIME_SOURCE_BINDING_STALE')
    groups={}; resumed=set(); stopped=False
    root=Path(report_path).resolve().parent/'experiment'
    _need((root/'control.sqlite').is_file(), 'RUNTIME_LEDGER_REQUIRED')
    ledger=Ledger(root/'control.sqlite')
    for row in report.get('runs',[]):
        state=row['state']; run_id=row['run_id']; current=ledger.snapshot(run_id)
        _need(state['mode']=='real_runtime_fake_model' and current['status']==state['status']
              and current['artifact']==state['artifact'] and not current['activities'], 'RUNTIME_LEDGER_CHANGED')
        _need(not any(c['state']=='inflight' for c in ledger.calls(run_id)), 'RUNTIME_REQUEST_STILL_INFLIGHT')
        if state['status']=='submitted':
            _need(row.get('reopen') is True and row.get('native_schema_express') is True and row.get('new_windows')==2, 'RUNTIME_RESULT_CHECKS_REQUIRED')
            _need(sha256(safe_path(Path(state['artifact']['path'])))==state['artifact']['sha256'], 'RUNTIME_ARTIFACT_CHANGED')
            groups.setdefault(state['case_id'],set()).add(state['arm'])
            events=ledger.events(run_id)
            if any(e['kind']=='question' for e in events) and any(e['kind']=='answer' for e in events): resumed.add(state['arm'])
            if state['arm']=='B':
                _need(state['native']['result'].get('successful_artifact_publishable') is True, 'B_NATIVE_PUBLICATION_REQUIRED')
        elif state['arm']=='D' and state['status']=='budget_exhausted':
            info=read_json(root/'runtime'/run_id/'container.json')
            stopped=(row.get('process_stopped') is True and row.get('heartbeat_stopped') is True
                     and info['State']['Running'] is False and info['State']['Pid']==0 and state['artifact'] is None)
    _need(sum(arms==set('ABCD') for arms in groups.values())>=2 and resumed==set('ABCD') and stopped, 'RUNTIME_FULL_CHAIN_NOT_PROVEN')
    for case,digest in report['public_inputs'].items():
        source=Path(report['configuration']['cases_root'])/case/'public/model.ifc'
        _need(sha256(source)==digest, 'RUNTIME_SOURCE_CHANGED')
    return {'report':file_ref(report_path),'log':file_ref(log_path),'scope':'Two synthetic ABCD completions, same-task resume and real D process-stop; fake HTTP only.'}


def validate_public_path(receipt):
    if not isinstance(receipt,dict): receipt=read_json(safe_path(Path(receipt)))
    _need(receipt.get('schema_version')=='repair-comparison-formal-public-path/0.1' and receipt.get('mode')=='offline', 'PUBLIC_PATH_RECEIPT_REQUIRED')
    _need(receipt.get('source_bindings')==capture_sources('formal'), 'PUBLIC_PATH_SOURCE_BINDING_STALE')
    plan_path=_ref(receipt['plan']); plan=formal.verify_plan(plan_path)
    config=plan['configuration']; root=safe_path(Path(receipt['experiment_root']))
    _need(config==receipt['configuration'] and len(config['case_ids'])==20 and len(config['order'])==80, 'PUBLIC_PATH_CONFIGURATION_REQUIRED')
    _need(formal.experiment_plan(root)['configuration']==config, 'PUBLIC_PATH_PLAN_BINDING_CHANGED')
    experiment=read_json(root/'experiment.json')
    _need(experiment['mode']=='offline', 'PUBLIC_PATH_MUST_BE_OFFLINE')
    carrier.validate_configuration(experiment)
    _need(receipt.get('logs') and receipt.get('commands'), 'PUBLIC_CLI_LOGS_REQUIRED')
    for ref in receipt['logs']: _ref(ref)
    commands=json.dumps(receipt['commands'])
    _need(all(action in commands for action in ('freeze','initialize','next','evaluate')), 'FULL_PUBLIC_CLI_PATH_REQUIRED')
    result=read_json(_ref(receipt['results']))
    rows={r['run_id']:r for r in result['rows']}
    _need(len(result['rows'])==len(rows)==80 and set(rows)==set(config['order']), 'EIGHTY_SCORE_ROWS_REQUIRED')
    ledger=Ledger(root/'control.sqlite'); started=[]; artifacts=set(); statuses=set(); answered=False
    for run_id in config['order']:
        state=ledger.snapshot(run_id); row=rows[run_id]; statuses.add(state['status'])
        _need(state['mode']=='real_runtime_fake_model' and state['budget']==config['budgets'][state['case_id']], 'PUBLIC_PATH_LEDGER_MISMATCH')
        _need(row['status']==state['status'] and row['evidence_class']==state['mode'] and row['artifact']==state['artifact'], 'PUBLIC_PATH_SCORING_STATE_MISMATCH')
        _need(row['metric_status']!='evaluator_error', 'PUBLIC_PATH_EVALUATOR_FAILED')
        if state['status'] not in TERMINAL: _need(row['success'] is None, 'PENDING_TASK_SCORED_AS_FAILURE')
        work=safe_path(Path(state['metadata']['workspace']))
        _need(work==root/'workspaces'/run_id and {p.name for p in work.iterdir()}=={'model.ifc','task.txt','work','output'}, 'PUBLIC_WORKSPACE_ISOLATION_FAILED')
        public=Path(config['cases_root'])/state['case_id']/'public'
        _need(set(p.name for p in public.iterdir())==PUBLIC_FILES and sha256(work/'model.ifc')==sha256(public/'model.ifc'), 'PUBLIC_INPUT_CHANGED')
        _need((work/'task.txt').read_text(encoding='utf8').strip()==(public/'request.txt').read_text(encoding='utf8').strip(), 'PRIVATE_TEXT_IN_RUNTIME_REQUEST')
        if state['artifact']:
            path=safe_path(Path(state['artifact']['path']))
            _need(path not in artifacts and path.is_relative_to(root/'artifacts'/run_id) and sha256(path)==state['artifact']['sha256'], 'UNIQUE_FROZEN_ARTIFACT_REQUIRED')
            artifacts.add(path)
        events=ledger.events(run_id)
        begins=[e for e in events if e['kind']=='started']
        _need(len(begins)<=1, 'TASK_RESTARTED')
        if begins: started.append((begins[0]['seq'],run_id))
        questions={e['payload']['question_id'] for e in events if e['kind']=='question'}
        for event in events:
            if event['kind']=='answer':
                _need(event['payload']['question_id'] in questions, 'ANSWER_BINDING_NOT_PROVEN')
                answered=True
    ordered=[run for _,run in sorted(started)]
    _need(len(ordered)>=8 and ordered==config['order'][:len(ordered)], 'PUBLIC_EXECUTION_ORDER_NOT_PROVEN')
    _need('submitted' in statuses and bool((TERMINAL-{'submitted'})&statuses) and answered, 'PUBLIC_COMPLETE_FAILURE_RESUME_REQUIRED')
    _need(formal.summarize(result['rows'])==result['summary'], 'PUBLIC_SUMMARY_MISMATCH')
    return {'plan':receipt['plan'],'results':receipt['results'],'logs':receipt['logs'],
            'executed_tasks':len(ordered),'ledger_tasks':80,'fixture_kind':receipt.get('fixture_kind','offline_public_path')}


def build_admission(plan_path, *, runtime_evidence, runtime_log, suite_receipts, public_path_receipt, output=None):
    plan,technical=validate_technical_plan(plan_path)
    configuration=plan['configuration']; current=carrier.bindings(configuration)
    runtime=validate_runtime_evidence(runtime_evidence,runtime_log,configuration=configuration,current_bindings=current)
    coverage=set(); suites=[]
    for receipt in suite_receipts:
        coverage |= validate_suite_receipt(receipt)
        suites.append(file_ref(receipt) if not isinstance(receipt,dict) else receipt)
    require_contracts(coverage)
    public=validate_public_path(public_path_receipt)
    # Guard changes made during aggregation; never refresh old evidence silently.
    _need(carrier.bindings(configuration)==current, 'BINDINGS_CHANGED_DURING_ADMISSION')
    _need(formal.verify_plan(plan_path)==plan, 'PLAN_CHANGED_DURING_ADMISSION')
    result={'schema_version':SCHEMA,'stage':carrier.FORMAL_STAGE,'passed':True,
        'created_at':datetime.now(timezone.utc).isoformat(),'configuration':configuration,'bindings':current,
        'plan':file_ref(plan_path),'technical_reviews':technical,'runtime_evidence':runtime,
        'suite_receipts':suites,'covered_contracts':sorted(coverage),'public_path_evidence':public,
        'real_models_called':False,'scope':'Formal-stage offline admission only; no real-model results or capability claim.'}
    if output:
        output=safe_path(Path(output))
        _need(not output.exists(), 'ADMISSION_EXISTS_NO_OVERWRITE')
        output.parent.mkdir(parents=True,exist_ok=True)
        write_json(output,result)
    return result


def revision_changes(previous, current):
    """Only registered ordinary fixes may inherit this stage's prior evidence."""
    _need({k:v for k,v in previous.items() if k!='files'}==
          {k:v for k,v in current.items() if k!='files'}, 'REVISION_CONTRACT_CHANGED')
    old,new=previous['files'],current['files']
    changes={path:{'before':old.get(path),'after':new.get(path)}
             for path in old.keys()|new.keys() if old.get(path)!=new.get(path)}
    _need(bool(changes), 'REVISION_HAS_NO_CHANGES')
    _need(all(path in REVISION_SOURCES and value['before'] and value['after']
              for path,value in changes.items()), 'UNCOVERED_REVISION_SOURCE:'+','.join(sorted(changes)))
    return changes,{REVISION_SOURCES[path] for path in changes}


def _external_red(capture):
    capture_ref=file_ref(capture); original=read_json(Path(capture_ref['path']))
    targets=_targets(original['argv'])
    _need(original['exit_code']==1, 'REVISION_RED_FAILURE_REQUIRED')
    paths={t.split('::')[0] for t in targets}
    before,after=original['source_bindings_before'],original['source_bindings_after']
    _need(paths<=before.keys() and paths<=after.keys(), 'EXTERNAL_RED_TEST_BINDINGS_REQUIRED')
    _ref(original['log'])
    return {'schema_version':REVISION_SUITE_SCHEMA,'stage':carrier.FORMAL_STAGE,'phase':'red',
        'command':original['argv'],'exit_code':original['exit_code'],'external_capture':capture_ref,
        'capture_source':'Source-scoped actual subprocess capture; original timestamps were not recorded.',
        'started_at':None,'ended_at':None,
        'source_bindings_before':{k:v for k,v in before.items() if k not in paths},
        'source_bindings_after':{k:v for k,v in after.items() if k not in paths},
        'test_bindings_before':{k:before[k] for k in paths},
        'test_bindings_after':{k:after[k] for k in paths},'log':original['log']}


def import_red_receipt(capture, output):
    """Normalize an existing honest source-scoped red capture without new hashes."""
    result=_external_red(capture)
    validate_revision_suite(result,phase='red')
    output=safe_path(Path(output)); _need(not output.exists(), 'REVISION_RECEIPT_EXISTS')
    output.parent.mkdir(parents=True,exist_ok=True); write_json(output,result)
    return output


def validate_revision_suite(receipt, *, phase):
    if not isinstance(receipt,dict): receipt=read_json(safe_path(Path(receipt)))
    _need(receipt.get('schema_version')==REVISION_SUITE_SCHEMA and receipt.get('phase')==phase
          and receipt.get('stage')==carrier.FORMAL_STAGE and receipt.get('capture_source'),
          'REVISION_RUN_RECEIPT_REQUIRED')
    targets=_targets(receipt['command'])
    _need(all(t.split('::')[0] in {*REVISION_TESTS,*REVISION_EXTRA_TESTS,REVISION_NATIVE_TEST}
              for t in targets), 'REVISION_TEST_TARGET_NOT_REGISTERED')
    families=set().union(*(REVISION_TESTS.get(t if phase=='green' else t.split('::')[0],set()) for t in targets))
    before,after=receipt['source_bindings_before'],receipt['source_bindings_after']
    tests=receipt['test_bindings_before']
    _need(tests==receipt['test_bindings_after'] and set(tests)=={t.split('::')[0] for t in targets},
          'REVISION_TEST_CHANGED_DURING_RUN')
    if phase=='red' and receipt.get('external_capture'):
        _need(receipt==_external_red(_ref(receipt['external_capture'])), 'EXTERNAL_RED_CAPTURE_CHANGED')
    else:
        began,ended=(datetime.fromisoformat(receipt[k]) for k in ('started_at','ended_at'))
        _need(began.tzinfo is not None and ended>=began, 'REVISION_RUN_TIMESTAMPS_REQUIRED')
    log=_ref(receipt['log']).read_text(encoding='utf8')
    if phase=='green':
        _pytest_summary(log,receipt['exit_code'])
        current=capture_sources('admission')
        _need(before.keys()==after.keys()==current.keys(), 'REVISION_GREEN_SOURCE_CAPTURE_INCOMPLETE')
        # Keep the full, honest pre/post capture, but unit families depend only
        # on their registered source owners and all unmapped shared sources.
        # Other changed owners require their own green family below. The final
        # native seam always binds every current source at once.
        dependencies={path for path in current if ({REVISION_NATIVE_TEST, REVISION_D_SUBMISSION_NATIVE_TEST,
                                                   REVISION_B_INSTALLATION_NATIVE_TEST} & set(targets))
                      or path not in REVISION_SOURCES or REVISION_SOURCES[path] in families}
        _need(all(before[path]==after[path]==current[path] for path in dependencies), 'REVISION_GREEN_SOURCE_STALE')
        _need(tests=={path:sha256(ROOT/path) for path in tests}, 'REVISION_GREEN_TEST_STALE')
    else:
        _need(receipt['exit_code']==1 and re.search(r'\b[1-9][0-9]* failed\b',log), 'REVISION_RED_FAILURE_REQUIRED')
        _need(not re.search(r'\b[1-9][0-9]* (?:errors?|skipped|deselected)\b',log), 'REVISION_RED_INCOMPLETE')
    # A selected red node can prove a reproduction. Green coverage requires the
    # complete registered family, including negative and boundary siblings.
    return {'receipt':receipt,'families':families,'targets':targets}


def _sealed_references(value, seen=None):
    """Verify historical evidence bytes without pretending old code is current."""
    seen=set() if seen is None else seen
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):
            path=_ref(value)
            if path.suffix=='.json' and path not in seen:
                seen.add(path); _sealed_references(read_json(path),seen)
        else:
            for item in value.values(): _sealed_references(item,seen)
    elif isinstance(value,list):
        for item in value: _sealed_references(item,seen)


def require_d_submission_scenarios(rows):
    expected = [('bare_json', 'submitted'), ('fenced_with_prose', 'submitted'),
                ('duplicate_declarations', 'runtime_error')]
    _need(sorted(rows) == sorted(expected), 'REVISION_D_SUBMISSION_SCENARIOS_REQUIRED')


def require_b_installation_scenarios(rows):
    expected = [('complete', 'submitted'), ('confirmation', 'submitted'),
                ('incompatible', 'no_output'), ('cohort', 'submitted'), ('door-base', 'submitted'),
                ('door-direct', 'submitted'), ('door-direct-denied', 'no_output')]
    _need(sorted(rows) == sorted(expected), 'REVISION_B_INSTALLATION_SCENARIOS_REQUIRED')


def validate_revision_seams(receipt, *, current_bindings, families):
    if not isinstance(receipt,dict): receipt=read_json(safe_path(Path(receipt)))
    submission_seam = receipt.get('schema_version') == 'repair-comparison-d-submission-native-seams/0.1'
    installation_seam = receipt.get('schema_version') == 'repair-comparison-b-installation-native-seams/0.1'
    if submission_seam:
        _need('D' in families and families <= {'D', 'admission'}, 'REVISION_D_SUBMISSION_SCOPE_REQUIRED')
    if installation_seam:
        _need('B' in families and families <= {'B', 'admission'}, 'REVISION_B_INSTALLATION_SCOPE_REQUIRED')
        for helper in receipt.get('fixture_helpers', []):
            _ref(helper)
    _need((submission_seam or installation_seam or receipt.get('schema_version')=='repair-comparison-revision-seams/0.1')
          and receipt.get('real_models_called') is False, 'REVISION_NATIVE_SEAMS_REQUIRED')
    _need(receipt.get('source_bindings')==capture_sources('admission')
          and receipt.get('images')==current_bindings['images'], 'REVISION_NATIVE_BINDING_STALE')
    suite=validate_revision_suite(_ref(receipt['suite_receipt']),phase='green')
    native_test = (REVISION_B_INSTALLATION_NATIVE_TEST if installation_seam else
                   REVISION_D_SUBMISSION_NATIVE_TEST if submission_seam else REVISION_NATIVE_TEST)
    _need(native_test in suite['targets'], 'REVISION_NATIVE_TEST_NOT_RUN')
    observed={}; resumed=False; submission_scenarios=[]; installation_scenarios=[]
    for row in receipt.get('runs',[]):
        family=row['family']; root=safe_path(Path(row['experiment_root']))
        _need((root/'control.sqlite').is_file(), 'REVISION_NATIVE_LEDGER_REQUIRED')
        ledger=Ledger(root/'control.sqlite'); state=ledger.snapshot(row['run_id'])
        _need(state['mode']=='real_runtime_fake_model' and state['status']==row['expected_status']
              and state['status'] in TERMINAL and not state['activities'], 'REVISION_NATIVE_TERMINAL_REQUIRED')
        _need(not any(c['state']=='inflight' for c in ledger.calls(row['run_id'])), 'REVISION_NATIVE_CALL_INFLIGHT')
        expected_family={'A':'AC','C':'AC','B':'B','D':'D'}[state['arm']]
        _need(family==expected_family, 'REVISION_NATIVE_ARM_MISMATCH')
        if submission_seam:
            _need(family == 'D', 'REVISION_D_SUBMISSION_SCOPE_REQUIRED')
            submission_scenarios.append((row.get('scenario', ''), state['status']))
        if installation_seam:
            _need(family == 'B', 'REVISION_B_INSTALLATION_SCOPE_REQUIRED')
            installation_scenarios.append((row.get('scenario', ''), state['status']))
        source=_ref(row['public_source'])
        _need(sha256(source)==state['metadata']['input_sha256'] and
              sha256(Path(state['metadata']['input_dir'])/'model.ifc')==sha256(source), 'REVISION_NATIVE_SOURCE_CHANGED')
        artifact=state['artifact']
        if state['status']=='submitted':
            _need(bool(artifact), 'REVISION_NATIVE_ARTIFACT_REQUIRED')
            path=safe_path(Path(artifact['path']))
            _need(path.is_relative_to(root/'artifacts'/state['run_id']) and sha256(path)==artifact['sha256'],
                  'REVISION_NATIVE_ARTIFACT_CHANGED')
            if submission_seam or installation_seam:
                import ifcopenshell
                from .inspection import native_validation
                validation = native_validation(ifcopenshell.open(str(path)))
                _need(validation['passed'] and validation['express_rules'] and validation['diagnostic_count'] == 0,
                      'REVISION_NATIVE_SCHEMA_VALIDATION_FAILED')
        else: _need(artifact is None, 'REVISION_NATIVE_FAILURE_HAS_ARTIFACT')
        events=ledger.events(row['run_id'])
        observed.setdefault(family,set()).add((state['arm'],state['status']))
        if family=='AC':
            commands=read_json(_ref(row['command_records']))
            _need(commands and all(command['network_mode']=='none' and not command['state']['Running']
                  and command['state']['Pid']==0 and command['image']==current_bindings['images'][carrier.IMAGE]
                  for command in commands), 'REVISION_AC_CONTAINER_EVIDENCE_REQUIRED')
        else:
            container=read_json(_ref(row['container_state']))
            _need(not container['State']['Running'] and container['State']['Pid']==0,
                  'REVISION_NATIVE_PROCESS_NOT_STOPPED')
            expected_image=current_bindings['images'][carrier.DSH_IMAGE if family=='D' else carrier.IMAGE]
            _need(container['Image']==expected_image, 'REVISION_NATIVE_CONTAINER_IMAGE_CHANGED')
            if family=='B' and state['status']=='submitted':
                _need(state.get('native',{}).get('result',{}).get('successful_artifact_publishable') is True,
                      'REVISION_B_NATIVE_PUBLICATION_REQUIRED')
                questions={e['payload']['question_id'] for e in events if e['kind']=='question'}
                resumed |= any(e['kind']=='answer' and e['payload']['question_id'] in questions for e in events)
            if family=='D' and state['status']=='budget_exhausted':
                _need(any(e['kind']=='controller_request_rejected' and e['payload'].get('origin')=='repair-controller'
                      and e['payload'].get('error') in {'TOKEN_BUDGET_EXHAUSTED','CALL_BUDGET_EXHAUSTED','TIME_BUDGET_EXHAUSTED'}
                      for e in events), 'REVISION_D_TRUSTED_BUDGET_DENIAL_REQUIRED')
    if 'AC' in families:
        _need({('A','submitted'),('C','submitted')}<=observed.get('AC',set()), 'REVISION_AC_PUBLIC_PATH_REQUIRED')
    if 'B' in families:
        _need(('B','submitted') in observed.get('B',set()) and resumed, 'REVISION_B_PUBLIC_RESUME_REQUIRED')
        if installation_seam:
            require_b_installation_scenarios(installation_scenarios)
    if 'D' in families:
        if submission_seam:
            require_d_submission_scenarios(submission_scenarios)
        else:
            _need({('D','budget_exhausted'),('D','runtime_error')}<=observed.get('D',set()), 'REVISION_D_DENIAL_FAMILY_REQUIRED')
    return receipt


def build_revision(parent_admission, *, suite_receipts, red_receipts, seam_receipt=None, output=None):
    """Inherit sealed stage evidence and revalidate only explicitly affected paths."""
    parent_ref=file_ref(parent_admission); parent=read_json(Path(parent_ref['path']))
    _need(parent.get('schema_version') in {SCHEMA,REVISION_SCHEMA} and parent.get('passed') is True
          and parent.get('stage')==carrier.FORMAL_STAGE, 'SAME_STAGE_PARENT_ADMISSION_REQUIRED')
    _sealed_references(parent)
    configuration=parent['configuration']; plan_path=_ref(parent['plan'])
    base=read_json(_ref(parent['base_admission'])) if parent.get('base_admission') else parent
    _need(base.get('schema_version')==SCHEMA and base.get('passed') is True
          and base.get('configuration')==configuration
          and REQUIRED_CONTRACTS<=set(base.get('covered_contracts',[]))
          and len(base.get('technical_reviews',[]))==20
          and {r['case_id'] for r in base['technical_reviews']}==set(configuration['case_ids'])
          and base.get('runtime_evidence') and base.get('public_path_evidence') and base.get('suite_receipts'),
          'COMPLETE_SEALED_BASE_ADMISSION_REQUIRED')
    _need(formal.verify_plan(plan_path)['configuration']==configuration, 'REVISION_PLAN_CONFIGURATION_CHANGED')
    current=carrier.bindings(configuration)
    changes,families=revision_changes(parent['bindings'],current)
    green=[validate_revision_suite(receipt,phase='green') for receipt in suite_receipts]
    green_families=set().union(*(r['families'] for r in green))
    _need(families<=green_families, 'REVISION_GREEN_FAMILY_MISSING:'+','.join(sorted(families-green_families)))
    red=[validate_revision_suite(receipt,phase='red') for receipt in red_receipts]
    reproduced=set()
    for item in red:
        receipt=item['receipt']
        for family in item['families']:
            paths=[path for path in changes if REVISION_SOURCES[path]==family]
            if paths and all(receipt['source_bindings_before'].get(path)==receipt['source_bindings_after'].get(path)==
                             changes[path]['before'] for path in paths):
                reproduced.add(family)
    _need(families-{'admission'}<=reproduced, 'REVISION_RED_PARENT_REPRODUCTION_MISSING')
    seams=None
    if families-{'admission'}:
        _need(seam_receipt is not None, 'REVISION_NATIVE_SEAMS_REQUIRED')
        seams=validate_revision_seams(seam_receipt,current_bindings=current,families=families)
    _need(carrier.bindings(configuration)==current and file_ref(parent_admission)==parent_ref,
          'REVISION_BINDINGS_CHANGED_DURING_AGGREGATION')
    _sealed_references(parent)
    result={'schema_version':REVISION_SCHEMA,'stage':carrier.FORMAL_STAGE,'passed':True,
        'created_at':datetime.now(timezone.utc).isoformat(),'configuration':configuration,'bindings':current,
        'parent_admission':parent_ref,'base_admission':parent.get('base_admission',parent_ref),
        'plan':parent['plan'],'changed_sources':changes,'affected_families':sorted(families),
        'focused_green_receipts':[file_ref(r) if not isinstance(r,dict) else r for r in suite_receipts],
        'focused_red_receipts':[file_ref(r) if not isinstance(r,dict) else r for r in red_receipts],
        'native_seams':file_ref(seam_receipt) if seam_receipt and not isinstance(seam_receipt,dict) else seams,
        'real_models_called':False,'scope':'Same-stage scoped revision; original admission, attempts and evidence remain immutable.'}
    if output:
        output=safe_path(Path(output)); _need(not output.exists(), 'ADMISSION_EXISTS_NO_OVERWRITE')
        output.parent.mkdir(parents=True,exist_ok=True); write_json(output,result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',required=True,type=Path)
    parser.add_argument('--runtime-evidence',required=True,type=Path)
    parser.add_argument('--runtime-log',required=True,type=Path)
    parser.add_argument('--suite',required=True,action='append',type=Path)
    parser.add_argument('--public-path-receipt',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=build_admission(args.plan,runtime_evidence=args.runtime_evidence,runtime_log=args.runtime_log,
        suite_receipts=args.suite,public_path_receipt=args.public_path_receipt,output=args.output)
    print(json.dumps({'stage':result['stage'],'passed':result['passed'],'output':str(args.output)},ensure_ascii=False))


if __name__=='__main__': main()
