"""External lifetime control of the unmodified official DSH SDK/runtime."""
from __future__ import annotations
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.parse import urlsplit

from .container_tools import docker
from .contracts import relative_path, safe_path, write_json

IMAGE='text2ifc/repair-dsh:0.2.0rc1'


def submitted_path(text):
    """Read one declaration, optionally in the sole final top-level JSON fence.

    Explanatory prose is not parsed for JSON. Marked examples/quotes and any
    competing declaration or code fence are ambiguous, so they fail closed.
    """
    text = text.strip()
    if '```' in text or '~~~' in text:
        if text.count('```')>2:
            declarations=0
            for body in re.findall(r'^```json[ \t]*\r?\n(.*?)\r?\n```[ \t]*\r?$',text,re.DOTALL|re.MULTILINE):
                try:
                    candidate=json.loads(body)
                except (json.JSONDecodeError,TypeError):
                    continue
                declarations+=isinstance(candidate,dict) and 'submitted_ifc' in candidate
            if declarations>1:
                raise ValueError('ONE_EXPLICIT_IFC_REQUIRED')
        match=re.fullmatch(r'(.*?)^```json[ \t]*\r?\n(.*?)\r?\n```',text,re.DOTALL|re.MULTILINE)
        if not match or text.count('```')!=2 or '~~~' in text:
            return None
        prefix,body=match.groups()
        # No extraction from nested objects, inline references, quotes or
        # examples. These lexical markers deliberately err toward no output.
        if (any(marker in prefix for marker in ('{','}','submitted_ifc','<!--'))
                or re.search(r'^\s*>|<blockquote\b',prefix,re.MULTILINE|re.IGNORECASE)
                or re.search(r'\b(?:example|sample|illustration|illustrative|quoted?|quotation|template)\b'
                             r'|\be\.g\.|\bdo not submit\b|\bnot (?:a )?submission\b'
                             r'|示例|例如|举例|范例|样例|引用|模板|仅供|不要提交|未提交',prefix,re.IGNORECASE)):
            return None
        text=body.strip()

    def unique_keys(pairs):
        value={}
        for key,item in pairs:
            if key in value:
                raise ValueError('ONE_EXPLICIT_IFC_REQUIRED')
            value[key]=item
        return value

    try:
        value=json.loads(text,object_pairs_hook=unique_keys)
    except (json.JSONDecodeError,TypeError):
        return None
    if not isinstance(value,dict) or 'submitted_ifc' not in value:
        return None
    if set(value)!={'submitted_ifc'}:
        raise ValueError('ONE_EXPLICIT_IFC_REQUIRED')
    path=relative_path(value['submitted_ifc'])
    if (path!=value['submitted_ifc'] or path!=path.strip()
            or any(ord(character)<32 or ord(character)==127 for character in path)):
        raise ValueError('INVALID_RELATIVE_PATH')
    if not path.lower().endswith('.ifc'):
        raise ValueError('EXPLICIT_IFC_REQUIRED')
    return path


QUIESCENT_SCRIPT = '''import json,os
from pathlib import Path
base=Path('/state/baseline.json'); activity=Path('/state/activity.json')
if not base.exists() or not activity.exists(): print(json.dumps({'quiescent':False})); raise SystemExit
known=set(json.loads(base.read_text())['pids'])|{os.getpid()}
extra=[]
for p in Path('/proc').iterdir():
 if p.name.isdigit() and int(p.name) not in known:
  try:
   s=(p/'stat').read_text(); state=s[s.rfind(')')+2:].split()[0]
   if state!='Z': extra.append(int(p.name))
  except (FileNotFoundError,ProcessLookupError): pass
children=json.loads(activity.read_text()).get('active_child_sessions',[])
print(json.dumps({'quiescent':not extra and not children,'extra_pids':extra,'active_child_sessions':children}))
'''


class NativeDSH:
    def __init__(self,workspace,control,*,name,state_volume,network,base_url,model,session_id,image=IMAGE):
        for value in (name,state_volume,network,session_id):
            if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,100}',value):
                raise ValueError('INVALID_NATIVE_IDENTIFIER')
        parsed=urlsplit(base_url)
        if network in {'host','bridge','none'} or parsed.scheme!='http' or parsed.hostname!='repair-gateway' or parsed.port!=8000 or not re.fullmatch('/[a-f0-9]{32}',parsed.path) or parsed.query or parsed.fragment:
            raise ValueError('INTERNAL_TASK_GATEWAY_REQUIRED')
        self.workspace,self.control=safe_path(Path(workspace)),safe_path(Path(control))
        self.name,self.volume,self.network,self.image=name,state_volume,network,image
        self.control.mkdir(parents=True,exist_ok=True)
        for filename in ('native_worker.py','question-bridge.mjs'):
            shutil.copyfile(Path(__file__).parent/'dsh'/filename,self.control/filename)
        write_json(self.control/'runtime.json',{'base_url':base_url,'model':model,'session_id':session_id})

    def docker_argv(self):
        return ['docker','create','--name',self.name,'--pull=never','--network='+self.network,
            '--read-only','--user=10001:10001','--cap-drop=ALL','--security-opt=no-new-privileges',
            '--cpus=4','--memory=8g','--memory-swap=8g','--pids-limit=512',
            '--tmpfs=/tmp:rw,exec,nosuid,size=1g','--tmpfs=/cache:rw,exec,nosuid,size=1g',
            '--env=HOME=/state/home','--env=XDG_CACHE_HOME=/cache','--env=PYTHONDONTWRITEBYTECODE=1',
            '--workdir=/workspace','--mount',f'type=bind,source={self.workspace},target=/workspace',
            '--mount',f'type=bind,source={self.control},target=/opt/carrier,readonly',
            '--mount',f'type=volume,source={self.volume},target=/state,volume-nocopy',
            self.image,'python','/opt/carrier/native_worker.py']

    def quiescent(self):
        try:
            row=json.loads(docker('exec',self.name,'python','-c',QUIESCENT_SCRIPT,timeout=10))
            write_json(self.control/'quiescence.json',row)
            return row['quiescent']
        except (RuntimeError,subprocess.TimeoutExpired,ValueError):
            return False

    def stop(self):
        docker('stop','--time','2',self.name)
        info=json.loads(docker('inspect',self.name))[0]
        write_json(self.control/'container.json',info)
        if info['State']['Running'] or info['State']['Pid']!=0:
            raise RuntimeError('NATIVE_PROCESS_STOP_NOT_CONFIRMED')

    def run(self,*,ledger,run_id):
        if docker('network','inspect',self.network,'--format','{{.Internal}}')!='true':
            raise ValueError('NETWORK_NOT_INTERNAL')
        if docker('volume','ls','--filter',f'name=^{self.volume}$','--format','{{.Name}}'):
            raise ValueError('NATIVE_STATE_EXISTS_NO_AUTOMATIC_RESTART')
        docker('volume','create',self.volume)
        docker('run','--rm','--network=none','--read-only','--cap-drop=ALL','--cap-add=CHOWN','--user=0:0',
            '--mount',f'type=volume,source={self.volume},target=/state,volume-nocopy',self.image,
            'python','-c','import os; os.chown("/state",10001,10001)')
        created=subprocess.run(self.docker_argv(),capture_output=True,text=True,encoding='utf8',check=True)
        timeout=False
        with (self.control/'console.txt').open('wb') as console:
            process=subprocess.Popen(['docker','start','--attach',self.name],stdout=console,stderr=subprocess.STDOUT)
            try:
                while process.poll() is None:
                    state=ledger.snapshot(run_id)
                    if state['status']=='running' and state['active_elapsed_s']>=state['limits']['active_seconds']:
                        timeout=True
                        self.stop()
                        break
                    time.sleep(.2)
                process.wait(timeout=10)
            finally:
                self.stop()
        for filename in ('result.json','versions.json','notifications.jsonl','diagnostics.txt','baseline.json','activity.json'):
            result=subprocess.run(['docker','cp',f'{self.name}:/state/{filename}',str(self.control/filename)],capture_output=True)
        # Whole native persistence, including child sessions and summaries.
        docker('cp',f'{self.name}:/state/sessions',str(self.control/'sessions'),timeout=60)
        docker('rm',self.name)
        if timeout:
            return {'ok':False,'error':'ACTIVE_TIME_BUDGET_EXHAUSTED','container_stopped':True}
        result_path=self.control/'result.json'
        if not result_path.exists():
            return {'ok':False,'error':'NATIVE_RESULT_MISSING','container_stopped':True}
        return json.loads(result_path.read_text(encoding='utf8'))
