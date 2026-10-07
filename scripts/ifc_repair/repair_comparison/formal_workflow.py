"""Freeze and operate one public-input-only four-arm repair comparison.

Task review, scoring and runtime admission stay separate. This controller does
not restart failed tasks, invent model outputs, or read G to answer a question.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from . import demo_workflow as carrier
from .contracts import read_json, write_json, sha256, safe_path
from .formal_batch import check_candidate
from .formal_scoring import score, DEFAULT_POLICY
from .ledger import Ledger, TERMINAL

SCHEMA = 'repair-comparison-formal-plan/0.1'
TARGET_FIELDS = {
    'basis','ifc_class','width_mm','height_mm','opening_center_xy_m','opening_bottom_world_m',
    'match_center_world_m','coarse_match_m','host_guid','storey_guid','reference_guid',
    'opening_width_mm','opening_height_mm','target_center_offset_from_opening_m','target_center_offsets_from_opening_m',
}
REQUIRED_TARGET = {'basis','ifc_class','width_mm','height_mm','opening_center_xy_m',
                   'opening_bottom_world_m','match_center_world_m','host_guid','reference_guid'}
BUDGETS = {
    'S1': {'tokens':1_250_000,'calls':48,'active_seconds':1800,'tool_seconds':120,'extensions':[]},
    'S2': {'tokens':1_750_000,'calls':64,'active_seconds':2400,'tool_seconds':120,'extensions':[]},
    'S3': {'tokens':2_500_000,'calls':80,'active_seconds':3000,'tool_seconds':120,'extensions':[]},
}
SEAL_FILES = ('public/model.ifc','public/request.txt','private/task.json',
              'private/answer-card.json','private/technical-review.json',
              'private/checks.json','private/reference.ifc','private/mutation/damaged.ifc')


def _review_ok(review):
    return (review.get('status') == 'accepted' or
            (review.get('status') == 'accepted_by_delegation'
             and review.get('kind') == 'delegated_technical'
             and review.get('human_viewed') is False
             and review.get('technical_review_passed') is True
             and bool(review.get('authorization',{}).get('user_quote'))))


def target_policy(task):
    targets = {}
    for name, raw in task.get('author_expectations',{}).items():
        value = {k:deepcopy(v) for k,v in raw.items() if k in TARGET_FIELDS}
        if (not REQUIRED_TARGET.issubset(value) or not value['basis']
            or not any(k in value for k in ('target_center_offset_from_opening_m','target_center_offsets_from_opening_m'))):
            raise ValueError('INCOMPLETE_TARGET_CONTRACT:'+name)
        targets[name] = value
    if set(targets) != {f'target-{i+1}' for i in range(task['required_product_count'])}:
        raise ValueError('INCOMPLETE_TARGET_CONTRACT')
    return {**deepcopy(DEFAULT_POLICY),'version':'repair-comparison-formal-policy/0.1',
            'frozen':True,'targets':targets}


def freeze(cases_root, output, *, expected_count=20, budgets=None, models=None):
    cases_root, output = safe_path(Path(cases_root)), safe_path(Path(output))
    if output.exists():
        raise ValueError('PLAN_EXISTS_USE_VERIFY_NO_OVERWRITE')
    paths = sorted(p for p in cases_root.glob('formal-*') if p.is_dir())
    if len(paths) != expected_count:
        raise ValueError('EXPECTED_CASE_COUNT')
    staged, sources, profiles = [], set(), {}
    for case in paths:
        task = read_json(case/'private/task.json')
        checked = check_candidate(case)
        review = task['review']
        if not checked['valid'] or not checked.get('review_accepted') or not _review_ok(review):
            raise ValueError('TASK_REVIEW_REQUIRED:'+case.name)
        if not read_json(case/'private/technical-review.json').get('passed'):
            raise ValueError('TECHNICAL_REVIEW_REQUIRED:'+case.name)
        if task['source_sha256'] in sources:
            raise ValueError('DIFFERENT_SOURCE_IFC_REQUIRED')
        sources.add(task['source_sha256'])
        policy = target_policy(task)
        profiles[case.name] = deepcopy((budgets or {}).get(case.name,BUDGETS[task['damage_profile']['level']]))
        staged.append((case,task,policy))
    configuration = carrier.batch_configuration(cases_root=cases_root, case_ids=[p.name for p in paths],
        budgets=profiles,stage=carrier.FORMAL_STAGE,models=models,scene_grounding=True)
    rows = []
    for case,task,policy in staged:
        task['metrics'] = {'status':'frozen','formal_scoring_frozen':True,
                           'policy_version':policy['version']}
        task['budget'] = {'status':'frozen','limits':profiles[case.name],
                          'provider_calls_allowed':True,'requires_current_stage_admission':True}
        write_json(case/'private/task.json',task)
        rows.append({'case_id':case.name,'source':task['source'],'source_sha256':task['source_sha256'],
                     'damage_profile':task['damage_profile'],'review':task['review'],'policy':policy,
                     'files':{name:sha256(case/name) for name in SEAL_FILES}})
    plan = {'schema_version':SCHEMA,'stage':carrier.FORMAL_STAGE,
            'created_at':datetime.now(timezone.utc).isoformat(), 'configuration':configuration,'cases':rows,
            'budget_basis':'Pre-run scale limits from two-demo evidence (B 55k/310k, C 147k/186k, D 1.09M partial and A 2.19M exhausted); same limit for four arms of a case, no outcome-driven extension.',
            'authorization':{'model_token_target':20_000_000,'over_target_requires_new_approval':False,
                             'review':'Delegated technical review; human_viewed is recorded per case.'},
            'limitations':['Twenty different source IFCs are not twenty independent building families.',
                'IFC native validation and world-coordinate mesh checks do not prove usBIM display compatibility.',
                'Appearance is a public-host-local mesh/style witness; unproven equivalent encodings require review.',
                'Requested DeepSeek aliases across Chat and Messages do not prove identical service weights.',
                'Failures remain in the task denominator; missing usage is unknown, not zero.']}
    write_json(output,plan)
    return plan


def verify_plan(path):
    plan = read_json(safe_path(Path(path)))
    if plan.get('schema_version') != SCHEMA or plan.get('stage') != carrier.FORMAL_STAGE:
        raise ValueError('FORMAL_PLAN_REQUIRED')
    configuration = plan['configuration']
    if [r['case_id'] for r in plan['cases']] != configuration['case_ids']:
        raise ValueError('FROZEN_CASE_ORDER_CHANGED')
    for row in plan['cases']:
        case = Path(configuration['cases_root'])/row['case_id']
        if set(row['files']) != set(SEAL_FILES) or any(sha256(case/name) != value for name,value in row['files'].items()):
            raise ValueError('FROZEN_TASK_CHANGED:'+row['case_id'])
        task = read_json(case/'private/task.json')
        if target_policy(task) != row['policy'] or not task['metrics']['formal_scoring_frozen']:
            raise ValueError('FROZEN_POLICY_CHANGED:'+row['case_id'])
        if not _review_ok(task['review']):
            raise ValueError('FROZEN_REVIEW_CHANGED')
    return plan


def initialize(root, plan_path, *, admission, mode='live'):
    plan = verify_plan(plan_path)
    config = plan['configuration']
    result = carrier.initialize(root,mode=mode,admission=admission,
        cases_root=config['cases_root'],case_ids=config['case_ids'],budgets=config['budgets'],
        models=config['models'],stage=config['stage'],scene_grounding=True)
    write_json(Path(root)/'formal-plan-binding.json',{'path':str(Path(plan_path).resolve()),'sha256':sha256(Path(plan_path))})
    return result


def experiment_plan(root):
    binding = read_json(Path(root)/'formal-plan-binding.json')
    if sha256(Path(binding['path'])) != binding['sha256']:
        raise ValueError('FROZEN_PLAN_CHANGED')
    plan = verify_plan(binding['path'])
    config = read_json(Path(root)/'experiment.json')
    if config['configuration'] != plan['configuration']:
        raise ValueError('FROZEN_CONFIGURATION_CHANGED')
    return plan


def next_task(states):
    active = [s for s in states if s['status'] in {'running','awaiting_user'}]
    if len(active)>1:
        raise ValueError('MULTIPLE_ACTIVE_TASKS')
    if active:
        return active[0]
    return next((s for s in states if s['status']=='ready'),None)


def card_answer(question, card):
    """Return only a requested, pre-approved fact; out-of-card remains pending."""
    if card.get('status') != 'accepted_by_delegation':
        return None
    raw = question['text']
    try:
        native = json.loads(raw)
        raw = native.get('question') or native.get('prompt') or native.get('message') or raw
    except (ValueError,TypeError):
        pass
    text = str(raw).casefold()
    facts = card.get('required_user_facts',[])
    facts = [({'fact_id':fact, **card.get('facts',{}).get(fact,{})} if isinstance(fact,str) else fact) for fact in facts]
    found = [fact for fact in facts if isinstance(fact,dict)
             and any(str(word).casefold() in text for word in fact.get('question_keywords',fact.get('keywords',[])))]
    if not found:
        return None
    return {'text':'\n'.join(f['answer'] for f in found),
            'requested_fact_ids':[f['fact_id'] for f in found],
            'answered_fact_ids':[f['fact_id'] for f in found],
            'source':'delegated_preapproved_card'}


def run_next(root, *, answer_from_card=False):
    plan = experiment_plan(root)
    state = next_task(carrier.status(root))
    if state is None:
        return {'status':'complete'}
    run_id = state['run_id']
    if state['status']=='awaiting_user':
        if not answer_from_card:
            return state
        case = Path(plan['configuration']['cases_root'])/state['case_id']
        value = card_answer(state['question'],read_json(case/'private/answer-card.json'))
        if value is None:
            return state
        value['event_id'] = 'delegated-card:'+state['question']['question_id']
        carrier.answer(root,run_id,value)
        Ledger(Path(root)/'control.sqlite').record(run_id,'delegated_card_answer',
            {**value,'question_id':state['question']['question_id']},event_id=value['event_id']+':provenance')
        if state['arm']=='D':
            # The native DSH process resumes inside the warm gateway; a new
            # dispatch would start a second owner for the same task.
            return Ledger(Path(root)/'control.sqlite').snapshot(run_id)
    return carrier.run(root,run_id)


def _ratio(numerator,denominator):
    return {'numerator':numerator,'denominator':denominator,
            'value':numerator/denominator if numerator is not None and denominator else None}


def summarize(rows):
    result = {}
    for arm in 'ABCD':
        selected = [r for r in rows if r['arm']==arm]
        if not selected:
            continue
        counts = Counter(r['status'] for r in selected)
        complete = all(r['status'] in TERMINAL for r in selected)
        confirmed_successes=sum(r['success'] is True for r in selected)
        success_known=all(r['success'] is not None for r in selected)
        summary = {'tasks':len(selected),'terminal_tasks':sum(r['status'] in TERMINAL for r in selected),
                   'statuses':dict(counts),'task_success':_ratio(confirmed_successes if success_known else None,len(selected)),
                   'confirmed_successes':confirmed_successes,
                   'complete':complete,'needs_review':sum(r.get('needs_review',False) for r in selected),
                   'known_tokens':sum(r['known_tokens'] for r in selected),
                   'unknown_calls':sum(r['unknown_calls'] for r in selected),
                   'active_seconds':sum(r['active_seconds'] for r in selected)}
        for key in ('quantity','components','relations'):
            values = [r[key] for r in selected]
            known=all(v['numerator'] is not None and v.get('status') not in {'pending','not_run','not_evaluable','needs_review'} for v in values)
            summary[key] = _ratio(sum(v['numerator'] for v in values) if known else None,
                                  sum(v['denominator'] for v in values))
        summary['total_tokens'] = summary['known_tokens'] if not summary['unknown_calls'] else None
        result[arm] = summary
    return result


def evaluate(root, *, output=None):
    root = safe_path(Path(root))
    plan = experiment_plan(root)
    ledger = Ledger(root/'control.sqlite')
    policies = {r['case_id']:r['policy'] for r in plan['cases']}
    output = safe_path(Path(output)) if output else root/'evaluation'
    output.mkdir(parents=True,exist_ok=True)
    rows=[]
    for run_id in plan['configuration']['order']:
        state = ledger.snapshot(run_id)
        artifact = state['artifact']
        result_path = Path(artifact['path']) if artifact else None
        if artifact and sha256(result_path) != artifact['sha256']:
            raise ValueError('FROZEN_ARTIFACT_CHANGED:'+run_id)
        case = Path(plan['configuration']['cases_root'])/state['case_id']
        events = ledger.events(run_id)
        # Provenance is stored separately by the experimental controller. The
        # original answer bytes stay untouched; add the same approved fact ids
        # only to the evaluator's view of its matching answer event.
        approvals = {e['payload']['question_id']:e['payload'] for e in events if e['kind']=='delegated_card_answer'}
        scored_events=deepcopy(events)
        for event in scored_events:
            if event['kind']=='answer' and event['payload'].get('question_id') in approvals:
                source=approvals[event['payload']['question_id']]
                event['payload'].update({k:source[k] for k in ('requested_fact_ids','answered_fact_ids')})
        report = score(case,result_path,terminal=state['status'],events=scored_events,policy=policies[state['case_id']])
        write_json(output/(run_id+'.json'),report)
        metrics=report['metrics']
        row={'run_id':run_id,'case_id':state['case_id'],'arm':state['arm'],'status':state['status'],
             'metric_status':report['status'],'evidence_class':state['mode'],
             'model_requested':state['metadata']['runtime']['model_requested'],
             'success':metrics['task_success']['value'],
             'quantity':metrics['quantity_completion'],'components':metrics['component_completion'],
             'relations':metrics['relation_completion'],'ifc_valid':metrics['ifc_validation_pass']['value'],
             'clarification':metrics['clarification'],'needs_review':bool(report['review_required']),
             'known_tokens':state['usage']['known_total_tokens'],'unknown_calls':state['usage']['unknown_calls'],
             'calls':state['usage']['calls'],'active_seconds':state['active_elapsed_s'],
             'artifact':artifact,'score_path':str(output/(run_id+'.json'))}
        rows.append(row)
    report={'schema_version':'repair-comparison-formal-results/0.1','stage':plan['stage'],
            'rows':rows,'summary':summarize(rows),'limitations':plan['limitations']}
    write_json(output/'results.json',report)
    fields=('run_id','case_id','arm','status','metric_status','success','ifc_valid','known_tokens','unknown_calls','calls','active_seconds','needs_review')
    with (output/'results.csv').open('w',encoding='utf-8-sig',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=fields)
        writer.writeheader()
        writer.writerows({k:row[k] for k in fields} for row in rows)
    write_table(output/'REPORT.md',report)
    return report


def write_table(path,report):
    def ratio(value):
        return f"{value['numerator'] if value['numerator'] is not None else '?'} / {value['denominator']}"
    lines=['# Repair 四组评测','',
           '所有尝试与失败均保留。Q 为目标数量，C 为完整构件，Rel 为所需语义关系；待答与待运行不是失败。'
           '严格成功需格式、构件、关系与保全全部通过；未证明等价的外观标为待复核。','',
           '|组|终态任务/总数|严格成功|Q|C|Rel|已知 token|未知用量调用|活动分钟|',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for arm,summary in report['summary'].items():
        lines.append(f"|{arm}|{summary['terminal_tasks']}/{summary['tasks']}|{ratio(summary['task_success'])}|{ratio(summary['quantity'])}|{ratio(summary['components'])}|{ratio(summary['relations'])}|{summary['known_tokens']}|{summary['unknown_calls']}|{summary['active_seconds']/60:.1f}|")
    lines += ['','|题目|A|B|C|D|','|---|---|---|---|---|']
    by_id={r['run_id']:r for r in report['rows']}
    for case_id in dict.fromkeys(r['case_id'] for r in report['rows']):
        cells=[]
        for arm in 'ABCD':
            row=by_id[case_id+'-'+arm]
            verdict='通过' if row['success'] is True else '待复核' if row['needs_review'] else row['status']
            cells.append(f"[{verdict}](./{row['run_id']}.json)；C {ratio(row['components'])}；Rel {ratio(row['relations'])}")
        lines.append('|'+case_id+'|'+'|'.join(cells)+'|')
    lines += ['','[80项逐任务数据](results.csv) · [完整结果和状态统计](results.json)','',
              *['- '+value for value in report['limitations']],'',
              '已知token按实际返回计数。存在未知调用时总量未知；未用目录大小或预估计费替代实际用量。', '']
    Path(path).write_text('\n'.join(lines),encoding='utf8')


def main():
    sys.stdout.reconfigure(encoding='utf8')
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    p=sub.add_parser('freeze');p.add_argument('--cases',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('verify');p.add_argument('--plan',type=Path,required=True)
    p=sub.add_parser('initialize');p.add_argument('--root',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--admission',type=Path)
    p.add_argument('--mode',choices=('offline','live'),default='live')
    p=sub.add_parser('next');p.add_argument('--root',type=Path,required=True);p.add_argument('--answer-from-card',action='store_true')
    p=sub.add_parser('evaluate');p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.action=='freeze':value=freeze(args.cases,args.output)
    elif args.action=='verify':value=verify_plan(args.plan)
    elif args.action=='initialize':value=initialize(args.root,args.plan,admission=args.admission,mode=args.mode)
    elif args.action=='next':value=run_next(args.root,answer_from_card=args.answer_from_card)
    else:value=evaluate(args.root,output=args.output)
    print(json.dumps({'action':args.action,'status':value.get('status','ok')},ensure_ascii=False),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
