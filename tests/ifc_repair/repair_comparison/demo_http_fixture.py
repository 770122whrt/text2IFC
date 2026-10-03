"""Keyless HTTP-only fixture. Never imported in live mode or model containers."""
import json
from pathlib import Path
import shlex

import httpx


class FakeDemoTransport:
    def __init__(self,root,config):
        self.root,self.config=Path(root),config
        self.counts={}

    def __call__(self,request):
        run_id=request.url.path.strip('/').split('/')[0]
        arm=run_id[-1]; kind='window' if run_id.startswith('case-001') else 'door'
        step=self.counts.get(run_id,0); self.counts[run_id]=step+1
        body=json.loads(request.content)
        scenario=self.config.get('fixture_scenarios',{}).get(run_id)
        code=Path(__file__).with_name('public_repair_fixture.py').read_text(encoding='utf8')
        if arm=='D':
            from tests.ifc_repair.repair_comparison.dsh_fake_gateway import chunks
            if scenario=='question' and step==0:
                events=chunks(tool=('ask_user_question',{'questions':[{'id':'opening','question':'请确认要补的是二层空门洞？'}]},'offline-question'))
                return httpx.Response(200,headers={'Content-Type':'text/event-stream'},content=''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode())
            if step==(1 if scenario=='question' else 0):
                command='mkdir -p work output && cat > work/fixture.py <<\'OFFLINE_SCRIPT\'\n'+code+'\nOFFLINE_SCRIPT\npython work/fixture.py '+kind
                events=chunks(tool=('bash',{'command':command,'description':'Deterministic public-only offline fixture','timeoutMs':120000},'offline-repair'))
            else:events=chunks(text='{"submitted_ifc":"output/repaired.ifc"}')
            return httpx.Response(200,headers={'Content-Type':'text/event-stream'},content=''.join('event: '+e['type']+'\ndata: '+json.dumps(e)+'\n\n' for e in events).encode())
        if arm=='B':
            from scripts.ifc_repair.repair_comparison.ours_adapter import _draft,_section
            prompt=body['messages'][0]['content']
            value=_draft(prompt,_section(prompt,'Draft schema')) if '## Immutable bindings' in prompt else intent(self.root/'workspaces'/run_id,kind)
            if scenario=='question' and step==0:
                value['operations'][0]['parameters'].pop('door',None)
            message={'role':'assistant','content':json.dumps(value),'reasoning_content':'Deterministic fixture; no model inference.'}
            finish='stop'
        else:
            if scenario=='question' and step==0:
                return httpx.Response(200,json={'id':'offline-question','model':body['model'],'choices':[
                    {'index':0,'finish_reason':'tool_calls','message':{'role':'assistant','tool_calls':[
                        {'id':'question','type':'function','function':{'name':'ask_user','arguments':'{"question":"请确认要补的是二层空门洞？"}'}}]}}],
                    'usage':{'prompt_tokens':11,'completion_tokens':7}})
            if scenario=='question':step-=1
            actions=[('write_file',{'path':'work/fixture.py','text':code}),
                     ('execute',{'argv':['python','work/fixture.py',kind],'timeout_s':120}),
                     ('submit',{'path':'output/repaired.ifc'})]
            if step>=len(actions):raise AssertionError('Fixture exhausted; inspect prior tool failure')
            name,args=actions[step]
            message={'role':'assistant','content':None,'reasoning_content':'Deterministic fixture; no model inference.',
                     'tool_calls':[{'type':'function','id':'offline-'+str(step),'function':{'name':name,'arguments':json.dumps(args)}}]}
            finish='tool_calls'
        return httpx.Response(200,json={'id':'fake-'+str(step),'model':body['model'],'object':'chat.completion','created':0,
            'choices':[{'index':0,'message':message,'finish_reason':finish}],
            'usage':{'prompt_tokens':11,'completion_tokens':7,'total_tokens':18}})


def intent(workspace,kind):
    # Derive from PUBLIC D. This does not read source G, a private recipe or
    # deleted identities and is not exposed as a localization helper to models.
    import ifcopenshell
    import ifcopenshell.util.unit
    import ifcopenshell.util.placement
    import numpy as np
    from scripts.ifc_repair.repair_comparison.inspection import geometry_snapshot
    from scripts.ifc_repair.repair_comparison.ours_adapter import fixture_intent
    model=ifcopenshell.open(str(workspace/'model.ifc'))
    def bounds(p):return np.array(geometry_snapshot(p)['bounds_world_m'])
    if kind=='door':
        opening=next(o for o in model.by_type('IfcOpeningElement') if not o.HasFillings and o.VoidsElements
                     and abs(bounds(o)[2][0]-3.1)<.001)
        return fixture_intent('door',{'allowed_ifc_classes':['IfcOpeningElement'],'global_id':opening.GlobalId},
                             {'fit_existing_opening':True,'door':{'operation_type':'SINGLE_SWING_LEFT','formal_enum_explicit':True}})
    walls=[(bounds(w)[0].mean(),w) for w in model.by_type('IfcWall')
           if bounds(w)[0,1]-bounds(w)[0,0]<.3 and bounds(w)[1,1]-bounds(w)[1,0]>10 and abs(bounds(w)[2,0])<.001]
    host=min(walls,key=lambda item:item[0])[1]
    windows=[f.RelatedBuildingElement for v in host.HasOpenings for f in v.RelatedOpeningElement.HasFillings
             if f.RelatedBuildingElement.is_a('IfcWindow')]
    windows.sort(key=lambda w:bounds(w)[1].mean(),reverse=True)
    center=(bounds(windows[1]).mean(axis=1)+bounds(windows[2]).mean(axis=1))/2
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    local=np.linalg.inv(ifcopenshell.util.placement.get_local_placement(host.ObjectPlacement))@np.append(center/scale,1.)
    return fixture_intent('window',{'allowed_ifc_classes':['IfcWall'],'global_id':host.GlobalId},
        {'position':{'reference':'wall_local_start','center_offset_mm':float(local[0]*scale*1000)},
         'opening':{'width_mm':915.,'height_mm':1830.,'sill_height_mm':305.},'window':{'fit_opening':True}})
