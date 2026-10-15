"""Persistent sequential batch owner; publish changes and stop for decisions."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from . import demo_workflow as carrier, formal_workflow as formal
from .contracts import read_json, write_json
from .ledger import Ledger, TERMINAL


def compact(states):
    active=formal.next_task(states)
    return {'terminal':sum(s['status'] in TERMINAL for s in states),'tasks':len(states),
            'active':None if active is None else {k:active.get(k) for k in ('run_id','status')},
            'known_tokens':sum(s['usage']['known_total_tokens'] for s in states),
            'reserved_tokens':sum(s['usage']['reserved_tokens'] for s in states),
            'unknown_calls':sum(s['usage']['unknown_calls'] for s in states),
            'question_id':(active.get('question') or {}).get('question_id') if active else None}


def change_key(summary):
    return {key:summary[key] for key in ('terminal','tasks','active','question_id')}


def accounted_usage(root, states):
    """Explicit rechecks consume the same authorization, never a fresh 20M."""
    rows=list(states);seen={Path(root).resolve()}
    archived={key:0 for key in ('known_tokens','reserved_tokens','unknown_calls')}
    registry=Path(root)/'operator/additional-attempts.json'
    if registry.exists():
        saved=read_json(registry)
        if 'archived_usage' in saved:
            values=saved['archived_usage']
            if (not isinstance(values,dict) or set(values)!=set(archived) or any(
                    type(value) is not int or value<0 for value in values.values())):
                raise ValueError('INVALID_ARCHIVED_USAGE')
            archived=values
        for name in saved.get('roots',[]):
            other=Path(name).resolve()
            if other in seen:raise ValueError('DUPLICATE_ATTEMPT_ROOT')
            seen.add(other);rows.extend(carrier.status(other))
    return {key:archived[key]+sum(s['usage'][field] for s in rows) for key,field in (
        ('known_tokens','known_total_tokens'),('reserved_tokens','reserved_tokens'),('unknown_calls','unknown_calls'))}


def budget_allows_next(usage, next_limit, total_limit):
    return usage['known_tokens']+usage['reserved_tokens']+next_limit<=total_limit


def card_proposal(state, card):
    question=state['question'];value=formal.card_answer(question,card)
    if state['arm']!='D':return value
    packet=question.get('binding',{}).get('native_packet',{})
    questions=packet.get('questions',[])
    if len(questions)<=1:return value
    answers=[];facts=[]
    for item in questions:
        answer=formal.card_answer({'text':json.dumps(item,ensure_ascii=False)},card)
        if answer is None:return None
        answers.append({'id':item['id'],'selected':[],'custom':answer['text']})
        facts.extend(answer['answered_fact_ids'])
    facts=list(dict.fromkeys(facts))
    return {'text':'\n'.join(a['custom'] for a in answers),'answers':answers,
            'requested_fact_ids':facts,'answered_fact_ids':facts,'source':'delegated_preapproved_card'}


def failure_signature(state):
    if state['arm']!='B' or state['status'] not in {'runtime_error','no_output','unsupported'}:
        return None
    native=state.get('native',{}).get('result',{})
    parts={'status':native.get('status'),'error_code':native.get('error_code'),
           'reason_code':native.get('reason_code'),'detail':state.get('detail')}
    return hashlib.sha256(json.dumps(parts,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:16]


def common_candidates(states, reviewed=()):
    signatures={s['run_id']:failure_signature(s) for s in states}
    counts=Counter(s for s in signatures.values() if s and s not in reviewed)
    return {signature:[run_id for run_id,value in signatures.items() if value==signature]
            for signature,count in counts.items() if count>=2}


def records(root, states):
    """Raw terminal facts only. Submission is never labelled repair success."""
    return {'metrics_status':'deferred','experiment_root':str(root),
            'rows':[{k:s.get(k) for k in ('run_id','case_id','arm','status','mode','artifact',
                                        'usage','active_elapsed_s','human_wait_s','detail')}
                    for s in states], 'usage':{k:v for k,v in compact(states).items()
                                               if k in {'known_tokens','reserved_tokens','unknown_calls'}}}


def publish(root, states, table_path=None):
    operator=root/'operator';operator.mkdir(exist_ok=True)
    result=records(root,states);write_json(operator/'execution-results.json',result)
    if table_path is None:return
    labels={'ready':'未启动','running':'运行中','awaiting_user':'待澄清','submitted':'已提交，待评分',
            'budget_exhausted':'预算停止','runtime_error':'运行失败','no_output':'无输出','refused':'拒绝'}
    lookup={r['run_id']:r for r in result['rows']}
    cases=list(dict.fromkeys(r['case_id'] for r in result['rows']))
    lines=['<!-- later-ten-batch:start -->','## 011～020 四组批次','',
           '指标待定。本表记录真实运行终态；“已提交”不表示修复通过。原始失败和各次版本保留。','',
           '|题目|A|B|C|D|','|---|---|---|---|---|']
    for case in cases:
        cells=[]
        for arm in 'ABCD':
            row=lookup[case+'-'+arm];label=labels.get(row['status'],row['status'])
            artifact=row.get('artifact')
            if artifact and artifact.get('path'):
                label=f'[{label}](<{Path(artifact["path"]).as_posix()}>)'
            cells.append(label)
        lines.append('|'+case+'|'+'|'.join(cells)+'|')
    usage=result['usage']
    lines += ['','实际返回已知token：'+format(usage['known_tokens'],',')+
              '；未知调用：'+str(usage['unknown_calls'])+'；未结算预留token：'+format(usage['reserved_tokens'],','),
              '',f'[本批机器记录](<{(operator/"execution-results.json").as_posix()}>)。指标尚未计算。',
              '<!-- later-ten-batch:end -->']
    content=Path(table_path).read_text(encoding='utf8')
    start='<!-- later-ten-batch:start -->';end='<!-- later-ten-batch:end -->'
    block='\n'.join(lines)
    if start in content:
        before,rest=content.split(start,1);_,after=rest.split(end,1);content=before+block+after
    else:content=content.rstrip()+'\n\n'+block+'\n'
    Path(table_path).write_text(content,encoding='utf8')


def run(root, *, table_path=None, results_path=None):
    root=Path(root).resolve()
    if read_json(root/'experiment.json').get('role')=='Completed financial checkpoint; not runnable.':
        raise ValueError('FINANCIAL_CHECKPOINT_NOT_RUNNABLE')
    plan=formal.experiment_plan(root)
    ledger=Ledger(root/'control.sqlite');operator=root/'operator';logs=operator/'logs';logs.mkdir(parents=True,exist_ok=True)
    total_limit=plan['authorization']['total_api_token_limit']
    job=None;handle=None;previous=None;job_log=None
    sequence=max((int(p.name.split('-',1)[0]) for p in logs.glob('*.log') if p.name.split('-',1)[0].isdigit()),default=0)
    while True:
        states=carrier.status(root);summary=compact(states);summary.update(accounted_usage(root,states));state=formal.next_task(states)
        key=change_key(summary)
        if key!=previous:
            write_json(operator/'progress.json',summary);publish(root,states,table_path)
            print(json.dumps({'event':'progress',**summary},ensure_ascii=False),flush=True);previous=key
        if job is not None and job.poll() is not None:
            code=job.returncode;handle.close();job=None;handle=None
            if code:
                value={'reason':'RUN_PROCESS_EXITED','exit_code':code,'log':str(job_log)}
                write_json(operator/'attention.json',value);print(json.dumps({'event':'attention',**value}),flush=True);return 2
        if job is None and not any(s['status'] in {'running','awaiting_user'} for s in states):
            reviewed=read_json(operator/'reviewed-failures.json').get('signatures',[]) if (operator/'reviewed-failures.json').exists() else []
            candidates=common_candidates(states,reviewed)
            if candidates:
                value={'reason':'B_COMMON_FAILURE_CANDIDATE','signatures':candidates}
                write_json(operator/'attention.json',value);print(json.dumps({'event':'attention',**value}),flush=True);return 2
            if (operator/'pause-requested.json').exists():
                write_json(operator/'paused.json',{'reason':'requested_between_tasks','progress':summary});return 0
        if state is None:
            if job is not None:time.sleep(.5);continue
            if results_path is not None:
                from .results import export_experiment
                export_experiment(root,results_path)
            write_json(operator/'complete.json',{'all_terminal':True,'tasks':len(states),'metrics_status':'deferred'})
            print(json.dumps({'event':'complete','tasks':len(states)}),flush=True);return 0
        if state['status']=='awaiting_user':
            question=state['question'];case=Path(plan['configuration']['cases_root'])/state['case_id']
            value=card_proposal(state,read_json(case/'private/answer-card.json'))
            key=hashlib.sha256(question['question_id'].encode()).hexdigest()[:16]
            answer_path=operator/f'answer-{state["run_id"]}-{key}.json'
            if value is not None:
                value['question_id']=question['question_id'];write_json(answer_path,value)
            if answer_path.exists():
                value=read_json(answer_path)
                if (value.get('question_id')!=question['question_id'] or value.get('source') not in
                        {'delegated_preapproved_card','public_request_restatement','user_confirmed'}):
                    raise ValueError('OPERATOR_ANSWER_PROVENANCE_REQUIRED')
                value['event_id']='operator:'+state['run_id']+':'+question['question_id']
                carrier.answer(root,state['run_id'],value)
                ledger.record(state['run_id'],'delegated_card_answer',value,event_id=value['event_id']+':provenance')
            else:
                pending={'reason':'OUTSIDE_CARD_QUESTION','run_id':state['run_id'],'question':question,'answer_file':str(answer_path)}
                path=operator/'pending.json'
                if not path.exists() or read_json(path)!=pending:
                    write_json(path,pending);print(json.dumps({'event':'attention','reason':pending['reason'],'run_id':state['run_id'],'pending_file':str(path)}),flush=True)
                time.sleep(.5);continue
        if job is not None:time.sleep(.5);continue
        current=ledger.snapshot(state['run_id'])
        if current['status'] in TERMINAL:continue
        if current['arm']=='D' and any(e['kind']=='d_native_started' for e in ledger.events(current['run_id'])):
            raise ValueError('D_WARM_OWNER_MISSING_NO_COLD_RESTART')
        if current['status']=='ready' and not budget_allows_next(summary,current['limits']['tokens'],total_limit):
            value={'reason':'TOTAL_API_TOKEN_LIMIT','progress':summary,'next_run_id':current['run_id']}
            write_json(operator/'attention.json',value);print(json.dumps({'event':'attention',**value}),flush=True);return 2
        sequence+=1;job_log=logs/f'{sequence:03d}-{current["run_id"]}.log';handle=job_log.open('wb')
        command=[sys.executable,'-m','scripts.ifc_repair.repair_comparison.formal_workflow','next','--root',str(root)]
        ledger.record(current['run_id'],'operator_dispatch',{'command':command,'log':str(job_log)})
        job=subprocess.Popen(command,cwd=Path(__file__).resolve().parents[3],stdout=handle,stderr=subprocess.STDOUT)
        write_json(operator/'job.json',{'pid':job.pid,'run_id':current['run_id'],'log':str(job_log)})
        time.sleep(.5)


def main():
    if len(sys.argv)==1 or sys.argv[1] in {'prepare','gate','admit','run','pause','resume','status','debug-export','hold-groups','release-groups','--help','-h'}:
        from .batch_workflow import main as scalable_main
        return scalable_main(sys.argv[1:])
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--table',type=Path)
    parser.add_argument('--results',type=Path,help='Export compact terminal IFCs, comparison facts and returned reasoning.')
    args=parser.parse_args()
    return run(args.root,table_path=args.table,results_path=args.results)


if __name__=='__main__':raise SystemExit(main())
