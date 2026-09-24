"""One atomic Agent correction of declared derived wall bounds, before generation."""
import copy
import json
from dataclasses import asdict
from pathlib import Path

from .brief_plan_constraints import VERSION, VERSIONS, derived_bound_paths, fixed_plan_conflict, resolve
from .design_brief import load_design_brief_schema, validate_design_brief
from .live_trace import write_live_trace, write_provider_failure_trace
from .prompt_registry import render_prompt


def _paths(brief,issues):
    indices={int((asdict(i) if hasattr(i,'__dataclass_fields__') else i)['path'].rsplit('/',1)[-1]) for i in issues}
    return derived_bound_paths(brief,indices)


def plan_repair_eligible(brief, issues):
    if not isinstance(brief,dict) or brief.get('schema_version') not in VERSIONS or brief.get('status')!='ready' or not issues:
        return False
    if any((asdict(i) if hasattr(i,'__dataclass_fields__') else i)['code']!='BRIEF_PLAN_GEOMETRY' for i in issues):return False
    try:return bool(_paths(brief,issues)) and not fixed_plan_conflict(brief)
    except (KeyError,TypeError,ValueError,IndexError):return False


def _fixed(brief,paths):
    value=copy.deepcopy(brief)
    for path in paths:
        parent,key=path.rsplit('/',1)
        resolve(value,parent).pop(key)
    return value


def repair_plan_brief(*,provider,output_dir,brief,case,evidence_catalog,session_id):
    from .brief_conversation import require_brief_conversation
    require_brief_conversation(case['conversation'])
    root=Path(output_dir);root.mkdir(parents=True,exist_ok=False)
    def write(name,value):(root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    issues=validate_design_brief(brief,evidence_catalog=evidence_catalog,expected_schema_version=brief['schema_version'],conversation=case['conversation'])
    if not plan_repair_eligible(brief,issues):
        result={'valid':False,'status':'not_eligible','issues':[asdict(i) for i in issues]};write('validation.json',result);return result
    paths=_paths(brief,issues)
    schema=load_design_brief_schema(brief['schema_version'])
    inputs={'USER_REQUEST':case['user_request'],'CONVERSATION':case['conversation'],'PREVIOUS_BRIEF':brief,
        'VALIDATION_ISSUES':[asdict(i) for i in issues],'ALLOWED_PATHS':paths,'DESIGN_BRIEF_SCHEMA':schema}
    rendered=render_prompt(template_id='design-brief-plan-repair.v1.2' if brief['schema_version']=='text2ifc/design-brief/2.8' else 'design-brief-plan-repair.v1.1' if brief['schema_version']=='text2ifc/design-brief/2.7' else 'design-brief-plan-repair.v1',inputs=inputs)
    write('prompt-render-input.json',inputs);write('prompt-identity.json',rendered['metadata'])
    (root/'prompt-rendered.md').write_text(rendered['text'],encoding='utf-8')
    try:
        response=provider.generate_live(session_id=session_id,prompt=rendered['text'],schema=schema,
            state={'case_id':case.get('case_id',session_id),'stage':'design-brief-plan-repair'})
    except Exception as error:
        write_provider_failure_trace(error=error,output_dir=root,stage='design-brief-plan-repair');raise
    write_live_trace(result=response,output_dir=root,trace_level='debug')
    status,parsed,diagnostics=response.output.parse_json();errors=list(diagnostics)
    if status=='ok' and isinstance(parsed,dict) and not errors:
        errors=[asdict(i) for i in validate_design_brief(parsed,evidence_catalog=evidence_catalog,
            expected_schema_version=brief['schema_version'],conversation=case['conversation'])]
        if not errors and _fixed(parsed,paths)!=_fixed(brief,paths):
            errors.append({'code':'BRIEF_PLAN_REPAIR_SCOPE_VIOLATION','path':'/',
                'message':'Only declared derived bounds may change; all other Brief values are frozen.'})
    elif not errors:errors=[{'code':'BRIEF_PLAN_REPAIR_INVALID_JSON','path':'/','message':'Expected a complete strict JSON Brief.'}]
    result={'valid':not errors,'status':'corrected' if not errors else 'blocked','issues':errors,
        'response_id':response.response.get('id'),'evidence_class':response.evidence_class}
    if parsed is not None:write('parsed-output.json',parsed)
    write('validation.json',result)
    if not errors:write('design-brief.json',parsed);result['brief']=parsed
    return result
