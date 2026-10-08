"""Real Linux BGE/Qdrant and B worker/SDK; only HTTP decisions are authored.

This is an explicit expensive scoped test, not a default dependency installer.
The approved image and pre-existing read-only model/cache must already exist.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

MODES=('english','chinese','clarification','invalid_value','malformed','mixed','mixed_write_failure')
VERSION='text2ifc/isolated-b-property-runtime/0.1'
IMAGE='text2ifc/repair-tools:py312-ifc085-property-v1'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def section(prompt,heading):
    return json.JSONDecoder().raw_decode(prompt.split(f'## {heading}',1)[1].strip())[0]


def draft(prompt):
    from text2ifc_ifc_repair.operations import create_default_registry
    schema=section(prompt,'Draft schema')
    raw=section(prompt,'Resolved operation projection')['operations']
    if isinstance(raw,dict):
        registry=create_default_registry()
        raw=[{'operation_id':key,**value,
              'target':registry.bind_resolved_target(value['operation_type'],value['target_global_id']),
              'evidence_refs':value['evidence_pointers']} for key,value in raw.items()]
    operations=[];scope=[];evidence=[]
    for op in raw:
        operations.append({k:op[k] for k in ('operation_id','operation_type','target','parameters','evidence_refs')})
        scope.extend(op.get('scope_ids') or op['target'].values());evidence.extend(op['evidence_refs'])
    lines=prompt.split('## Immutable bindings',1)[1].split('## Resolved operation projection',1)[0]
    bindings=dict(re.findall(r'^- ([^:]+): (.+)$',lines,re.MULTILINE))
    return {'schema_version':schema['$id'],'draft_id':'offline-property-draft',
        'base_model_fingerprint':bindings['model'],'source_request_hash':bindings['source request'],
        'semantic_manifest_ref':bindings['semantic manifest ref'],'semantic_manifest_sha256':bindings['semantic manifest hash'],
        'semantic_summary':section(prompt,'Semantic group counts'),
        'scope':{'target_ids':sorted(set(scope)),'forbidden_ids':[]},'evidence_refs':sorted(set(evidence)),
        'preconditions':[],'postconditions':[],'operations':operations}


def response(prompt,mode,records):
    if '## Immutable bindings' in prompt:
        records.append({'stage':'stage2'});return draft(prompt)
    if 'PROPERTY_QUERY:' in prompt and 'CANDIDATE_SET:' in prompt:
        query=json.JSONDecoder().raw_decode(prompt.split('PROPERTY_QUERY:',1)[1].strip())[0]
        candidates=json.JSONDecoder().raw_decode(prompt.split('CANDIDATE_SET:',1)[1].strip())[0]['candidates']
        records.append({'stage':'stage1.5','query':query,'candidates':candidates})
        if mode=='malformed':return '{'
        selected=next(c for c in candidates if c['canonical_path']=='Pset_BeamCommon.LoadBearing')
        if mode=='clarification':
            return {'schema_version':'text2ifc/ifc-property-rerank-decision/0.1',
                'decision':'clarification_required','selected_candidate_id':None,
                'conflicting_candidate_ids':[selected['candidate_id']],
                'clarification_question':'Confirm the offered load-bearing property for this beam.'}
        return {'schema_version':'text2ifc/ifc-property-rerank-decision/0.1','decision':'confirmed',
            'selected_candidate_id':selected['candidate_id'],'conflicting_candidate_ids':[],
            'clarification_question':None}
    pages=section(prompt,'Read-only query results so far')
    if not pages:
        records.append({'stage':'query'})
        return {'kind':'query','query':{'ifc_classes':['IfcBeam','IfcWall','IfcWindow']}}
    rows=[r for page in pages for r in page['records']]
    beam=next(r for r in rows if r['ifc_class']=='IfcBeam' and r['name']=='Public target beam')
    provenance={'source_kind':'user_request','reference':'request:/text','excerpt':'Set the selected beam load bearing to true.'}
    common={'attribute_intents':[],'semantic_bundle_refs':[],'quantity_intents':[],
            'occurrence_reuse_intent':None,'prototype_intent':None,'appearance_intent':None,'provenance':[provenance]}
    operations=[{**common,'operation_id':'public-property-0','operation_type':'set_occurrence_properties',
        'routing_intent':{'component_family':'occurrence','action':'set_properties','operation_profile':'occurrence.set-properties','source':provenance},
        'target_query':{'schema_version':'text2ifc/ifc-target-query/0.1','allowed_ifc_classes':['IfcBeam']},
        'parameters':{},'property_intents':[{'intent_kind':'natural_language_property',
            'property_phrase':'承载' if mode=='chinese' else 'load bearing',
            'raw_value':'maybe' if mode=='invalid_value' else True,'raw_unit':None,
            'scope':'occurrence_direct','source':provenance}]}]
    bindings=[{'operation_id':'public-property-0','target_id':beam['id']}]
    if mode in ('mixed','mixed_write_failure'):
        wall=next(r for r in rows if r['ifc_class']=='IfcWall')
        reference=next(r for r in rows if r['ifc_class']=='IfcWindow')
        operations.append({**common,'operation_id':'public-window-1','operation_type':'add_window_with_opening_to_wall',
            'routing_intent':{'component_family':'window','action':'add_with_opening','operation_profile':'window.add-with-opening.v0.3','source':provenance},
            'target_query':{'schema_version':'text2ifc/ifc-target-query/0.1','allowed_ifc_classes':['IfcWall']},
            'parameters':{'opening':{'width_mm':900.,'height_mm':1200.,'sill_height_mm':700.},'window':{'fit_opening':True}},
            'prototype_intent':{'reference_kind':'global_id','reference':reference['type_id'],'source':provenance},
            'attribute_intents':[{'intent_kind':'attribute','name':name,'value':value,'source':provenance}
                                 for name,value in [('OverallWidth',900.),('OverallHeight',1200.)]],'property_intents':[]})
        axis=wall['wall_axis']
        bindings.append({'operation_id':'public-window-1','target_id':wall['id'],'reference_id':reference['id'],
            'position':{'kind':'world_point','point_world_mm':[axis['start_world_mm'][i]+1500.*axis['direction_world'][i] for i in range(3)]}})
    records.append({'stage':'stage1','offered_target':beam['id']})
    return {'kind':'intent','bindings':bindings,'intent':{
        'schema_version':'text2ifc/ifc-repair-intent-body/0.10','operations':operations,
        'unsupported_requests':[],'semantic_bundles':[],'provenance':[provenance]}}


def source_fixture(path, *, shared=False):
    import ifcopenshell.api.geometry
    import ifcopenshell.guid
    from tests.ifc_repair.test_window_installation_anchor import scene
    from text2ifc_ifc_repair.operations.hosted_opening import local_placement
    model,wall,_,_,_,unit=scene(extension=0.)
    storey=wall.ContainedInStructure[0].RelatingStructure
    context=model.by_type('IfcGeometricRepresentationContext')[0]
    beams=[]
    for i,name in enumerate(('Public target beam','Public peer beam')):
        beam=model.createIfcBeam(ifcopenshell.guid.new(),wall.OwnerHistory,name)
        beam.ObjectPlacement=local_placement(model,relative_to=storey.ObjectPlacement,
            location=(2000*unit,(5000+1000*i)*unit,2500*unit))
        representation=ifcopenshell.api.geometry.add_wall_representation(model,context=context,length=3.,height=.3,thickness=.2,offset=-.1)
        beam.Representation=model.createIfcProductDefinitionShape(None,None,[representation]);beams.append(beam)
    style=model.create_entity('IfcBeamType',GlobalId=ifcopenshell.guid.new(),OwnerHistory=wall.OwnerHistory,
                              Name='Public shared beam type',PredefinedType='BEAM')
    model.createIfcRelDefinesByType(ifcopenshell.guid.new(),wall.OwnerHistory,None,None,beams,style)
    for owners in ([beams] if shared else [[beam] for beam in beams]):
        pset=model.createIfcPropertySet(ifcopenshell.guid.new(),wall.OwnerHistory,'Pset_BeamCommon',None,[
            model.createIfcPropertySingleValue('LoadBearing',None,model.createIfcBoolean(False),None)])
        model.createIfcRelDefinesByProperties(ifcopenshell.guid.new(),wall.OwnerHistory,None,None,owners,pset)
    containment=wall.ContainedInStructure[0];containment.RelatedElements=[*containment.RelatedElements,*beams]
    model.write(str(path))


def native(mode):
    import importlib.metadata
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element
    import ifcopenshell.validate
    workspace=Path('/workspace');state=Path('/state');records=[];errors=[]
    source=workspace/'model.ifc';source_hash=digest(source)
    seed=Path('/seed-qdrant');cache=state/'property-runtime/qdrant'
    shutil.copytree(seed,cache)
    try:
        (Path('/models/bge-m3')/'unwanted-write.probe').write_text('forbidden')
        raise AssertionError('model mount was writable')
    except OSError:pass
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                assert self.path=='/v1/chat/completions'
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                prompt=body['messages'][0]['content']
                assert all(c not in prompt for c in ('benchmark_gold','mutation_mapping','private_original'))
                value=response(prompt,mode,records)
                value=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
                reply={'id':f'offline-{len(records)}','object':'chat.completion','created':0,'model':body['model'],
                    'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':value,
                        'reasoning_content':'Deterministic fake HTTP; local retrieval remains real.'}}],
                    'usage':{'prompt_tokens':5,'completion_tokens':7,'total_tokens':12}}
                data=json.dumps(reply).encode();self.send_response(200);self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            except Exception as error:
                errors.append(f'{type(error).__name__}: {error}');self.send_error(500,'offline fixture error')
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    os.environ['NO_PROXY']='127.0.0.1,localhost'
    payload={'action':'start','run_id':f'property-{mode}','base_url':f'http://127.0.0.1:{server.server_port}/v1',
        'evidence_class':'deterministic_fake_http','scene_grounding_version':'text2ifc/ifc-scene-grounding/0.2',
        'property_runtime_version':VERSION,'timeout_seconds':600}
    def call(action,**extra):
        args=[sys.executable,'/runtime/isolated_b.py','worker']
        if mode=='mixed_write_failure' and action=='start':args=[sys.executable,__file__,'--rollback-worker']
        completed=subprocess.run(args,input=json.dumps({**payload,'action':action,**extra}),
            capture_output=True,text=True,encoding='utf8',timeout=900)
        (state/f'{action}-{len(records):02d}.stderr.txt').write_text(completed.stderr,encoding='utf8')
        found=[line.split('=',1)[1] for line in completed.stdout.splitlines() if line.startswith('ISOLATED_B_RESULT=')]
        assert len(found)==1,(completed.returncode,completed.stdout[-3000:],completed.stderr[-3000:])
        result=json.loads(found[0]);(state/f'{action}-{len(records):02d}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
        assert not errors,errors
        assert result['ok'],result
        return result
    report={'role':'real_linux_property_runtime_fake_provider_not_model_result','mode':mode,
        'versions':{name:importlib.metadata.version(name) for name in ('torch','qdrant-client','sentence-transformers','transformers')},
        'seed_cache':'readonly copy of pre-existing standard Qdrant; production factory must verify collection version',
        'source_sha256_before':source_hash,'network_mode':'none'}
    try:
        first=call('start');final=first
        if mode=='clarification':
            question=first['result']['clarification'];assert question
            calls=len(records)
            assert call('read')['result']==first['result'] and len(records)==calls
            token=next(c['token'] for c in question['candidates'] if 'LoadBearing' in c['token'])
            final=call('answer',answer={'kind':'select_candidate','candidate_token':token},
                clarification_id=question['clarification_id'],expected_state_version=first['result']['state_version'])
            assert sum(r['stage']=='stage1.5' for r in records)==1
        success=mode in ('english','chinese','clarification','mixed','shared')
        report['terminal']=final['result']['status'];report['stages']=records
        report['artifact_relative']=final['artifact_relative']
        assert final['result']['successful_artifact_publishable'] is success,final
        assert bool(final['artifact_relative']) is success
        if success:
            original=ifcopenshell.open(str(source));output=ifcopenshell.open(str(workspace/final['artifact_relative']))
            target=next(b for b in output.by_type('IfcBeam') if b.Name=='Public target beam')
            peer=next(b for b in output.by_type('IfcBeam') if b.Name=='Public peer beam')
            assert ifcopenshell.util.element.get_psets(target,should_inherit=False)['Pset_BeamCommon']['LoadBearing'] is True
            assert ifcopenshell.util.element.get_psets(peer,should_inherit=False)['Pset_BeamCommon']['LoadBearing'] is False
            prop=next(p for rel in target.IsDefinedBy if rel.is_a('IfcRelDefinesByProperties')
                      for p in rel.RelatingPropertyDefinition.HasProperties if p.Name=='LoadBearing')
            assert prop.NominalValue.is_a()=='IfcBoolean'
            for product in original.by_type('IfcProduct'):
                if not product.Representation:continue
                after=output.by_guid(product.GlobalId)
                assert product.ObjectPlacement.to_string()==after.ObjectPlacement.to_string()
                before_shape=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),product)
                after_shape=ifcopenshell.geom.create_shape(ifcopenshell.geom.settings(),after)
                if mode=='mixed' and product.is_a('IfcWall'):continue
                assert before_shape.geometry.verts==after_shape.geometry.verts
                assert before_shape.geometry.faces==after_shape.geometry.faces
            for entity in original.by_type('IfcTypeObject'):assert output.by_guid(entity.GlobalId).to_string()==entity.to_string()
            expected_windows=len(original.by_type('IfcWindow'))+(mode=='mixed')
            assert len(output.by_type('IfcWindow'))==expected_windows
            # Full EXPRESS is independently run on the host below: the approved
            # runtime image intentionally does not install pytest's rule compiler.
            logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(output,logger,express_rules=False)
            assert not logger.statements,logger.statements
            calls=len(records);assert call('read')['artifact_relative']==final['artifact_relative'] and len(records)==calls
            report['output_sha256']=digest(workspace/final['artifact_relative']);report['schema_diagnostics']=0
        else:
            assert not list((workspace/'output').iterdir())
            if mode=='mixed_write_failure':
                assert (state/'write-failure-injected.json').exists()
                assert not list(state.rglob('application-candidate.ifc'))
                assert not list(state.rglob('repaired.ifc'))
        retrievals=[p for p in state.rglob('*.json') if p.name in ('query.json','candidate-set.json','decision.json') and 'property-resolution' in p.parts]
        report['runtime_evidence_files']=[str(p.relative_to(state)) for p in retrievals]
        report['terminal']=final['result']['status'];report['stages']=records
        assert any(r['stage']=='stage1.5' and r.get('candidates') for r in records)
        assert digest(source)==source_hash
        report['source_unchanged']=True;report['checks_passed']=True
    finally:
        server.shutdown();server.server_close();thread.join(5)
        report['fixture_errors']=errors
        (state/'native-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'mode':mode,'checks_passed':True,'terminal':report['terminal'],'http_calls':len(records)}))


def _run_native_modes(modes, *, shared=False):
    import ifcopenshell
    import ifcopenshell.validate
    from scripts.ifc_repair.repair_comparison.isolated_b import build_runtime_bundle
    root=Path(__file__).resolve().parents[3]
    label=os.environ.get('B_PROPERTY_RUNTIME_RUN_LABEL','01')
    assert re.fullmatch(r'[0-9]{2}',label)
    evidence=root/f'.tmp/repair-comparison-formal-expansion/b-property-runtime-native-{label}'
    assert not evidence.exists(),'keep prior evidence; select a new numbered directory for a new run'
    evidence.mkdir();bundle=evidence/'bundle';build_runtime_bundle(root,bundle)
    image=subprocess.check_output(['docker','image','inspect',IMAGE,'--format','{{.Id}}'],text=True).strip()
    seeds=Path(os.environ.get('B_PROPERTY_RUNTIME_SEED',str(root/'.cache/property-resolution/qdrant'))).resolve()
    assert seeds.is_relative_to(root) and (seeds/'meta.json').is_file()
    models=root/'.cache/models/BAAI-bge-m3'
    source_fixture(evidence/'public.ifc',shared=shared)
    logger=ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(ifcopenshell.open(str(evidence/'public.ifc')),logger,express_rules=True)
    assert not logger.statements,logger.statements
    report=[]
    for mode in modes:
        case=evidence/mode;work=case/'work';state=case/'state';work.mkdir(parents=True);state.mkdir();(work/'output').mkdir()
        shutil.copyfile(evidence/'public.ifc',work/'model.ifc')
        request='Set Public target beam load bearing to true. Keep its type, geometry and the peer beam unchanged.'
        if mode=='chinese':request='请将公开目标梁的承载属性设为真，保留类型、几何及另一根梁不变。'
        if mode=='invalid_value':request='Set Public target beam load bearing to maybe; preserve all other objects.'
        if mode.startswith('mixed'):request+=' Also add a 900 by 1200 mm window at 1500 mm along the wall, sill 700 mm, using the retained window type and installation.'
        (work/'task.txt').write_text(request,encoding='utf8')
        name='b-property-runtime-'+mode.replace('_','-')
        command=['docker','run','--rm','--pull=never','--name',name,'--network=none','--read-only',
            '--user=65532:65532','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=8g','--cpus=4','--pids-limit=256',
            '--tmpfs=/tmp:rw,noexec,nosuid,size=512m','--env=PYTHONPATH=/runtime/src','--env=PYTHONDONTWRITEBYTECODE=1','--env=HOME=/tmp',
            '--env=NO_PROXY=127.0.0.1,localhost',
            '--mount',f'type=bind,source={bundle},target=/runtime,readonly',
            '--mount',f'type=bind,source={models},target=/models/bge-m3,readonly',
            '--mount',f'type=bind,source={seeds},target=/seed-qdrant,readonly',
            '--mount',f'type=bind,source={Path(__file__)},target=/checks/property_native.py,readonly',
            '--mount',f'type=bind,source={work/"model.ifc"},target=/workspace/model.ifc,readonly',
            '--mount',f'type=bind,source={work/"task.txt"},target=/workspace/task.txt,readonly',
            '--mount',f'type=bind,source={work/"output"},target=/workspace/output',
            '--mount',f'type=bind,source={state},target=/state',
            IMAGE,'python','/checks/property_native.py','--native',mode]
        start=time.monotonic();samples=[]
        with (case/'container.log').open('x',encoding='utf8') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            try:
                while process.poll() is None:
                    if time.monotonic()-start>1000:raise TimeoutError('offline native case timeout')
                    stats=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}',name],capture_output=True,text=True,timeout=20)
                    if stats.returncode==0 and stats.stdout.strip():samples.append(stats.stdout.strip())
                    time.sleep(2)
            finally:
                if process.poll() is None:subprocess.run(['docker','stop','--time','5',name],capture_output=True)
                process.wait(timeout=30)
        record={'mode':mode,'command':command,'image_id':image,'exit_code':process.returncode,
                'elapsed_seconds':time.monotonic()-start,'stats':samples,'log_sha256':digest(case/'container.log')}
        (case/'receipt.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8');report.append(record)
        (evidence/'run-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
        assert process.returncode==0,(mode,(case/'container.log').read_text(encoding='utf8')[-8000:])
        native_report=json.loads((state/'native-check.json').read_text(encoding='utf8'))
        independent={'source_express_diagnostics':0,'validator':'host IfcOpenShell '+ifcopenshell.version,
            'source_sha256':digest(work/'model.ifc'),'artifact_relative':native_report['artifact_relative']}
        if native_report['artifact_relative']:
            artifact=work/native_report['artifact_relative']
            logger=ifcopenshell.validate.json_logger()
            ifcopenshell.validate.validate(ifcopenshell.open(str(artifact)),logger,express_rules=True)
            independent['output_sha256']=digest(artifact)
            independent['output_express_diagnostics']=len(logger.statements)
            (case/'independent-express.json').write_text(json.dumps(independent,indent=2),encoding='utf8')
            assert not logger.statements,logger.statements
        else:(case/'independent-express.json').write_text(json.dumps(independent,indent=2),encoding='utf8')
        # Each later task still receives a separate writable copy. The factory
        # verifies the real first task's completed collection instead of doing
        # seven identical corpus rebuilds; the host cache is never modified.
        seeds=state/'property-runtime/qdrant'


def test_real_property_runtime_in_isolated_linux():
    _run_native_modes(MODES)


def test_real_shared_pset_runtime_in_isolated_linux():
    _run_native_modes(('shared',),shared=True)


if __name__=='__main__':
    if sys.argv[1:2]==['--native']:native(sys.argv[2])
    elif sys.argv[1:]==['--rollback-worker']:
        import ifcopenshell
        import runpy
        original=ifcopenshell.file.write
        def fail_after_candidate(model,path,*args,**kwargs):
            result=original(model,path,*args,**kwargs)
            if 'application-candidate.ifc-' in str(path):
                Path('/state/write-failure-injected.json').write_text(json.dumps({'test_only_injection':'after candidate write'}))
                raise OSError('offline property mixed publication failure')
            return result
        ifcopenshell.file.write=fail_after_candidate
        sys.argv=['/runtime/isolated_b.py','worker'];runpy.run_path('/runtime/isolated_b.py',run_name='__main__')
    else:raise SystemExit('explicit native mode required')
