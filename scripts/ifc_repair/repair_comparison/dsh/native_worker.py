"""One warm official SDK turn; no model fixture, evaluator or host credential."""
from dataclasses import asdict
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import threading


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def runtime_patches(config):
    patches = [
        {'id':'session-persistence-jsonl','config':{'root':'/state/sessions','compression':'none'}},
        {'id':'session-telemetry-otel','disabled':True},
        {'insert':[
            {'id':'repair-official-ask-user','name':'@deepseek-ai/dsh-tool-ask-user'},
            {'id':'repair-question-bridge','name':'file:///opt/carrier/question-bridge.mjs',
             'config':{'endpoint':config['base_url']+'/questions'}}
        ]}
    ]
    if config.get('web_search') is not None:
        settings = config['web_search']
        patches.append({'id':'web-search-deepseek','config':{
            'baseURL':config['base_url']+'/v1/search',
            'apiKey':'isolated-dsh-search-no-external-credential',
            'model':settings['model'], 'maxTokens':settings['max_tokens'], 'maxUses':settings['max_uses']}})
    return patches


def task_prompt(config, text):
    kind = config.get('task_kind', 'ifc_repair')
    if kind == 'knowledge_qa':
        return text
    if kind != 'ifc_repair':
        raise ValueError('INVALID_NATIVE_TASK_KIND')
    return (text + '\n\nIFC 文件：model.ifc\n提交协议：完成后在最终回复中用 JSON '
        + '{"submitted_ifc":"相对于工作目录的 IFC 文件路径"} 声明唯一产物；需要用户信息时使用提问工具。')


def runtime_environment(config):
    environment = {'DSH_PERMISSION_MODE':'danger-full-access','DSH_TELEMETRY_DISABLED':'1','SHELL':'/bin/bash'}
    if config.get('web_access') == 'proxy':
        environment.update(HTTP_PROXY='http://repair-gateway:8000', HTTPS_PROXY='http://repair-gateway:8000',
                           NO_PROXY='repair-gateway,localhost,127.0.0.1')
    return environment


def main():
    from deepseek_harness import DeepSeekHarness
    config = json.loads(Path('/opt/carrier/runtime.json').read_text())
    state = Path('/state')
    patch = state/'runtime.patch.json'
    write(patch, runtime_patches(config))
    write(state/'versions.json',{'python':sys.version, **{name:importlib.metadata.version(name)
        for name in ('deepseek-harness-sdk','deepseek-harness-runtime-bin','ifcopenshell')}})
    harness = DeepSeekHarness(provider='deepseek-official', model=config['model'],
        profile='sdk', cwd='/workspace', dsh_home='/state/home', patches=(str(patch),),
        reasoning_effort='high', max_tokens=65536, api_key='isolated-dsh-no-external-credential',
        base_url=config['base_url'], initialize_timeout_seconds=120,
        request_timeout_seconds=None,
        env=runtime_environment(config))
    active_children = set()
    lock = threading.Lock()
    def notification(value):
        row = asdict(value)
        with lock:
            with (state/'notifications.jsonl').open('a',encoding='utf8') as stream:
                stream.write(json.dumps(row,ensure_ascii=False)+'\n')
            p = row.get('payload',{})
            sid = p.get('sessionId')
            event = p.get('event') or p
            if sid and sid != config['session_id']:
                if event.get('type')=='turn/start': active_children.add(sid)
                if event.get('type')=='turn/end': active_children.discard(sid)
            write(state/'activity.json',{'active_child_sessions':sorted(active_children)})
    try:
        with harness:
            baseline = [int(p.name) for p in Path('/proc').iterdir() if p.name.isdigit()]
            write(state/'baseline.json',{'pids':baseline})
            write(state/'activity.json',{'active_child_sessions':[]})
            prompt = task_prompt(config, Path('/workspace/task.txt').read_text(encoding='utf8'))
            result = harness.run(prompt, session_id=config['session_id'], on_notification=notification)
            write(state/'result.json',{'ok':True,'result':asdict(result)})
    except BaseException as error:
        write(state/'result.json',{'ok':False,'error':f'{type(error).__name__}: {error}'})
        (state/'diagnostics.txt').write_text(harness.client._runtime_diagnostics(),encoding='utf8')
        raise


if __name__=='__main__':
    main()
