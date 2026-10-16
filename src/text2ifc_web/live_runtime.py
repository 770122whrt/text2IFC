"""Explicit local live-mode configuration; importing this module never makes a model call.

A server-side approval references the reviewed stage-admission record. These are local
operator files, not HTTP inputs. Preparing a request and viewing examples remain keyless.
The caller is responsible for completing the current stage checks before approving live use.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import math
import os
import re


def read_approval(path, root):
    path=Path(path).resolve();root=Path(root).resolve()
    if not path.is_relative_to(root) or path.is_symlink():
        raise ValueError('LIVE_APPROVAL_OUTSIDE_WORKSPACE')
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('scope')!='repair-ui-local' or data.get('approved') is not True:
        raise ValueError('LIVE_APPROVAL_REQUIRED')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',data.get('approval_id','')):
        raise ValueError('LIVE_APPROVAL_ID_INVALID')
    for key in ('max_calls','max_tokens','max_active_seconds'):
        value=data.get(key)
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:
            raise ValueError('LIVE_BUDGET_REQUIRED')
        if key!='max_active_seconds' and type(value) is not int:
            raise ValueError('LIVE_BUDGET_INVALID')
    admission=(path.parent/str(data.get('admission_file',''))).resolve()
    if not admission.is_relative_to(root) or not admission.is_file():
        raise ValueError('LIVE_STAGE_ADMISSION_REQUIRED')
    record=json.loads(admission.read_text(encoding='utf-8'))
    checks=record.get('checks')
    if record.get('scope')!='repair-ui-local' or record.get('status')!='passed' or not isinstance(checks,list) or not checks:
        raise ValueError('LIVE_STAGE_ADMISSION_NOT_PASSED')
    if any(c.get('passed') is not True or c.get('exit_code')!=0 for c in checks):
        raise ValueError('LIVE_STAGE_ADMISSION_NOT_PASSED')
    maximum=data.get('max_tasks',3)
    if type(maximum) is not int or maximum<1:
        raise ValueError('LIVE_TASK_BUDGET_INVALID')
    return data


@dataclass(frozen=True)
class LocalLiveFactory:
    workspace: str
    approval_path: str
    evidence_class: str = 'live'

    def task_limit(self):
        approval=read_approval(self.approval_path,self.workspace)
        return approval['approval_id'],approval.get('max_tasks',3)

    def __call__(self, output_root):
        from text2ifc_ifc_repair.api import RepairAPI
        from text2ifc_agent.generation_budget import BudgetLimits,GenerationBudget,BudgetedProvider
        approval=read_approval(self.approval_path,self.workspace)
        # Existing provider config/SDK only; secrets are not stored in the task database.
        environment=load_local_provider_environment(self.workspace)
        if not environment.get('DEEPSEEK_API_KEY'):
            raise ValueError('DEEPSEEK_CONFIGURATION_REQUIRED')
        api=RepairAPI.from_environment(output_root,environment=environment,scene_grounding=True)
        # A transport request is not automatically retried behind the budget ledger.
        api.provider.connection_max_attempts=1
        limits=BudgetLimits(max_calls=approval['max_calls'],max_tokens=approval['max_tokens'],max_active_seconds=approval['max_active_seconds'])
        budget=GenerationBudget(Path(output_root).parent/'live-budget'/approval['approval_id'],limits)
        api.provider=BudgetedProvider(api.provider,budget)
        api.integration_budget=budget
        return api


def local_live_factory(workspace,environment=None):
    """Return an explicit factory and a public status; never auto-enable from a key."""
    env=dict(os.environ) if environment is None else dict(environment)
    status={'enabled':False,'mode':'prepare_only','reason':'LIVE_NOT_REQUESTED'}
    if env.get('TEXT2IFC_UI_LIVE')!='1':return None,status
    path=env.get('TEXT2IFC_UI_LIVE_APPROVAL')
    if not path:return None,{**status,'reason':'LIVE_APPROVAL_REQUIRED'}
    try:
        path=Path(path)
        if not path.is_absolute():path=Path(workspace)/path
        approval=read_approval(path,workspace)
        from text2ifc_agent.openai_compat import load_openai_compatible_config
        env=load_local_provider_environment(workspace,env)
        config=load_openai_compatible_config(env)
        if not env.get('DEEPSEEK_API_KEY'):
            return None,{**status,'reason':'DEEPSEEK_CONFIGURATION_REQUIRED'}
        if not config.get('configured'):
            return None,{**status,'reason':'PROVIDER_CONFIG_INCOMPLETE','missing':config.get('missing',[])}
        factory=LocalLiveFactory(str(Path(workspace).resolve()),str(path.resolve()))
        return factory,{'enabled':True,'mode':'live','reason':None,'provider':config['provider_key'],'model':config['model'],'approval_id':approval['approval_id'],
                        'limits':{k:approval[k] for k in ('max_calls','max_tokens','max_active_seconds')}}
    except (OSError,ValueError,TypeError,KeyError):
        return None,{**status,'reason':'LIVE_APPROVAL_OR_CONFIG_INVALID'}


def load_local_provider_environment(workspace,environment=None):
    """Use the same workspace-local dotenv convention as the existing Repair service.

    Secrets remain in this process and are passed only to the native Provider constructor.
    No parent-worktree search, secret output, HTTP credential input, or credential copying.
    """
    from dotenv import dotenv_values
    root=Path(workspace).resolve()
    path=root/'.env'
    allowed={'DEEPSEEK_API_KEY','OPENAI_BASE_URL','OpenAI_BASE_URL','TEXT2IFC_DEEPSEEK_MODEL',
             'TEXT2IFC_DEEPSEEK_MAX_TOKENS','TEXT2IFC_DEEPSEEK_MAX_INPUT_TOKENS','TEXT2IFC_PROVIDER_TIMEOUT_SECONDS'}
    if path.is_symlink():raise ValueError('PROVIDER_CONFIG_SYMLINK_NOT_SUPPORTED')
    local=dotenv_values(path) if path.is_file() else {}
    merged={k:v for k,v in local.items() if k in allowed and isinstance(v,str) and v}
    merged.update(dict(os.environ) if environment is None else environment)
    merged['TEXT2IFC_PROVIDER']='deepseek'
    # Default only on DeepSeek's own endpoint, never rewrite a configured private gateway.
    base=merged.get('OPENAI_BASE_URL') or merged.get('OpenAI_BASE_URL')
    if not merged.get('TEXT2IFC_DEEPSEEK_MODEL') and base and base.rstrip('/') in ('https://api.deepseek.com','https://api.deepseek.com/v1'):
        merged['TEXT2IFC_DEEPSEEK_MODEL']='deepseek-flash'
    return merged


def provider_configuration_status(workspace=None):
    """Operator diagnosis using the existing config loader. No keys/URLs or requests."""
    from text2ifc_agent.openai_compat import load_openai_compatible_config
    environment=load_local_provider_environment(workspace or Path(__file__).resolve().parents[2])
    status=load_openai_compatible_config(environment)
    return {key:status[key] for key in ('configured','provider_key','model','missing','api_key_configured','base_url_configured')}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Inspect the local DeepSeek configuration without sending a model request.')
    parser.add_argument('action',choices=['status'])
    parser.parse_args()
    print(json.dumps(provider_configuration_status(),ensure_ascii=False))
