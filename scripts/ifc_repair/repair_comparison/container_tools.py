"""Generic commands: disposable non-root containers with one workspace mount."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import time
import uuid

from .neutral_tools import NeutralTools
from .budget import positive

IMAGE='text2ifc/repair-tools:py312-ifc085-v2'


def docker(*args,timeout=60,input=None):
    result=subprocess.run(['docker',*map(str,args)],input=input,capture_output=True,text=True,encoding='utf8',errors='replace',timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'DOCKER_{args[0].upper()}_FAILED: {result.stderr[-2000:]}')
    return result.stdout.strip()


class ContainerTools(NeutralTools):
    def __init__(self,workspace,*,tool_seconds,image=IMAGE):
        super().__init__(workspace,tool_seconds=tool_seconds)
        self.image=image
        self.records=[]
        self.quiescent=True

    def execute(self,argv,timeout_s=None):
        timeout=self.tool_seconds if timeout_s is None else timeout_s
        if not positive(timeout):
            raise ValueError('INVALID_TOOL_TIMEOUT')
        timeout=min(timeout,self.tool_seconds)
        name='text2ifc-repair-command-'+uuid.uuid4().hex[:12]
        worker=Path(__file__).with_name('container_command.py').resolve()
        began=time.monotonic()
        self.quiescent=False
        docker('create','--name',name,'--pull','never','--network','none','--read-only',
            '--user','10001:10001','--cap-drop','ALL','--security-opt','no-new-privileges',
            '--cpus','4','--memory','8g','--memory-swap','8g','--pids-limit','256',
            '--tmpfs','/tmp:rw,exec,nosuid,size=1g','--env','HOME=/tmp/home',
            '--mount',f'type=bind,source={self.workspace},target=/workspace',
            '--mount',f'type=bind,source={worker},target=/opt/tools/command.py,readonly',
            '--workdir','/workspace','--interactive',self.image,'python','/opt/tools/command.py')
        result=None
        try:
            text=docker('start','--attach','--interactive',name,input=json.dumps({'argv':argv,'timeout_s':timeout}),timeout=timeout+20)
            result=json.loads(text)
        except subprocess.TimeoutExpired:
            result={'exit_code':None,'stdout':'','stderr':'External command timeout','timed_out':True}
        finally:
            docker('stop','--time','2',name)
            state=json.loads(docker('inspect',name))[0]
            self.records.append({'container':name,'state':state['State'],'mounts':state['Mounts'],
                'network_mode':state['HostConfig']['NetworkMode'],'image':state['Image']})
            quiescent=not state['State']['Running'] and state['State']['Pid']==0
            self.quiescent=quiescent
            if quiescent:
                docker('rm',name)
            else:
                raise RuntimeError('CONTAINER_STOP_NOT_CONFIRMED')
        return {**result,'quiescent':quiescent,'wall_duration_s':time.monotonic()-began,'container':name}
