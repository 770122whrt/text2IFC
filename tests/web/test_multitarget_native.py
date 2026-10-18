"""Two selected walls through HTTP and the real Apply/Evaluation path; Provider only is a fixture."""
import copy
import json
import pytest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from fastapi.testclient import TestClient
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI
from text2ifc_web.app import create_app
from tests.web.test_native_chain import PUBLIC,wait
from tests.ifc_repair.test_scene_repair_api import _reuse_type,scene_query_pages
from scripts.ifc_repair.repair_comparison.ours_adapter import _draft,fixture_intent


def two_target_source():
    m=ifcopenshell.open(str(PUBLIC/'case-001/public/model.ifc'))
    base=m.by_guid('2cXV28XOjE6f6irgi0COkg')  # Surviving public host, not deleted/private truth.
    refs=[];scale=ifcopenshell.util.unit.calculate_unit_scale(m)
    for i in range(2):
        wall=ifcopenshell.util.element.copy(m,base);wall.Name='UI batch wall '+str(i+1)
        # ProductDefinitionShape belongs to one product; do not share the source wall's wrapper.
        wall.Representation=ifcopenshell.util.element.copy_deep(m,base.Representation,exclude=('IfcGeometricRepresentationContext',))
        # copy() does not carry inverse associations. Standard walls require their layer-set usage.
        for relation in tuple(base.HasAssociations):
            if not relation.is_a('IfcRelAssociatesMaterial'):continue
            association=ifcopenshell.util.element.copy(m,relation)
            association.RelatedObjects=(wall,)
            if relation.RelatingMaterial.is_a('IfcMaterialLayerSetUsage'):
                association.RelatingMaterial=ifcopenshell.util.element.copy(m,relation.RelatingMaterial)
        p=base.ObjectPlacement.RelativePlacement
        coords=list(p.Location.Coordinates);coords[0]+=(40+i*30)/scale
        pos=m.create_entity('IfcAxis2Placement3D',Location=m.create_entity('IfcCartesianPoint',Coordinates=coords),Axis=p.Axis,RefDirection=p.RefDirection)
        wall.ObjectPlacement=m.create_entity('IfcLocalPlacement',PlacementRelTo=base.ObjectPlacement.PlacementRelTo,RelativePlacement=pos)
        for rel in base.ContainedInStructure:rel.RelatedElements=tuple(rel.RelatedElements)+(wall,)
        for rel in base.IsDefinedBy:
            if hasattr(rel,'RelatedObjects'):rel.RelatedObjects=tuple(rel.RelatedObjects)+(wall,)
        refs.append(wall)
    return m.to_string().encode('utf-8'),refs


class BatchProvider:
    def generate_candidate(self,**kw):
        prompt=kw['prompt']
        if '## Immutable bindings' in prompt:
            value=_draft(prompt,kw['schema'])
        else:
            pages=scene_query_pages(prompt)
            if not pages:value={'kind':'query','query':{'ifc_classes':['IfcWall'],'limit':80}}
            elif len(pages)==1:value={'kind':'query','query':{'ifc_classes':['IfcWindow'],'limit':80}}
            else:
                walls=sorted([r for r in pages[0]['records'] if (r.get('name') or '').startswith('UI batch wall ')],key=lambda r:r['name'])
                reference=next(r for r in pages[1]['records'] if r.get('type_id'))
                body=fixture_intent('window',{'allowed_ifc_classes':['IfcWall']},{'position':{'reference':'wall_local_start','center_offset_mm':1000.0},'opening':{'width_mm':915.0,'height_mm':1830.0,'sill_height_mm':305.0},'window':{'fit_opening':True}})
                _reuse_type(body,reference);template=body['operations'][0];body['operations']=[];bindings=[]
                for i,wall in enumerate(walls):
                    op=copy.deepcopy(template);op['operation_id']='ui-batch-'+str(i+1);body['operations'].append(op)
                    bindings.append({'operation_id':op['operation_id'],'target_id':wall['id'],'reference_id':reference['id']})
                value={'kind':'intent','intent':body,'bindings':bindings}
        return ProviderOutput(text=json.dumps(value),metadata={'provider':'fixture','model':'offline-two-target','usage':{'input_tokens':11,'output_tokens':7}})


def factory(root):return RepairAPI(root,provider=BatchProvider(),scene_grounding=True)


def test_multitarget_source_is_valid_before_repair_and_has_independent_shapes():
    """The UI fixture itself must satisfy IFC2X3, not only reopen/render."""
    import ifcopenshell.validate
    source, targets = two_target_source()
    model = ifcopenshell.file.from_string(source.decode('utf-8'))
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger, express_rules=True)
    assert not logger.statements, [(x.get('attribute'), str(x.get('instance'))) for x in logger.statements]
    product_shapes = [model.by_guid(t.GlobalId).Representation for t in targets]
    assert len({s.id() for s in product_shapes}) == len(targets)
    for shape in product_shapes:
        assert len(shape.ShapeOfProduct) == 1
    for target in targets:
        obj = model.by_guid(target.GlobalId)
        usages = [r for r in obj.HasAssociations if r.is_a('IfcRelAssociatesMaterial') and r.RelatingMaterial.is_a('IfcMaterialLayerSetUsage')]
        assert len(usages) == 1


def test_two_selected_walls_publish_two_actual_windows_and_per_operation_summary(tmp_path):
    source,targets=two_target_source()
    with ThreadPoolExecutor(max_workers=1) as executor:
        with TestClient(create_app(tmp_path/'web',api_factory=factory,executor=executor,allowed_hosts=('testserver',))) as c:
            inp=c.post('/api/ifc-inputs',files={'file':('two-target.ifc',source)}).json()
            prepared=c.post('/api/repair-requests/prepare',json={'input_id':inp['input_id'],'view_version':'batch-source','targets':[{'step_id':o.id(),'global_id':o.GlobalId,'view_version':'batch-source'} for o in targets],
                'user_text':'在 UI batch wall 1 和 UI batch wall 2 上各新增一扇窗，窗中心距各墙局部起点1000毫米，宽915毫米、高1830毫米、窗台305毫米，使用现有窗的类型。'})
            assert prepared.status_code==201,prepared.text
            r=c.post('/api/repair-tasks',json={'prepared_request_id':prepared.json()['prepared_request_id'],'client_request_id':'batch-live-seam'})
            assert r.status_code==202,r.text
            done=wait(c,r.json()['task_id'],seconds=180)
            assert done['status']=='succeeded',done
            files=c.get(done['artifacts_url']).json()['artifacts'];result=c.get(next(x['download_url'] for x in files if x['role']=='successful_ifc')).content
            m=ifcopenshell.file.from_string(result.decode());before=ifcopenshell.file.from_string(source.decode())
            assert len(m.by_type('IfcWindow'))==len(before.by_type('IfcWindow'))+2
            from ifcopenshell import validate as ifc_validate
            logger=ifc_validate.json_logger()
            ifc_validate.validate(m,logger,express_rules=True)
            assert not logger.statements, [(x.get('attribute'),str(x.get('instance'))) for x in logger.statements]
            summary=c.get('/api/repair-tasks/'+done['task_id']+'/summary').json()
            assert summary['available'] and summary['published_operations']==summary['operation_total']==2
            assert sum(len(r['created']) for r in summary['rows'])==2
            assert c.get(inp['download_url']).content==source


@pytest.mark.parametrize('failure',['second_operation','temporary_write'])
def test_multitarget_failure_never_publishes_partial_ifc(tmp_path,monkeypatch,failure):
    from text2ifc_ifc_repair.registry import OperationRegistry
    observed=[]
    dispatch=OperationRegistry.dispatch
    def checked_dispatch(self,capability_name,operation,**kwargs):
        if capability_name=='applicator':
            observed.append(operation['operation_id'])
            if failure=='second_operation' and len(observed)==2:
                raise OSError('Injected second-operation failure')
        return dispatch(self,capability_name,operation,**kwargs)
    monkeypatch.setattr(OperationRegistry,'dispatch',checked_dispatch)
    if failure=='temporary_write':
        write=ifcopenshell.file.write
        def fail_write(model,path,*args,**kwargs):
            result=write(model,path,*args,**kwargs)
            if 'application-candidate.ifc-' in str(path):raise OSError('Injected write failure')
            return result
        monkeypatch.setattr(ifcopenshell.file,'write',fail_write)
    source,targets=two_target_source()
    with ThreadPoolExecutor(max_workers=1) as executor:
        with TestClient(create_app(tmp_path/'web',api_factory=factory,executor=executor,allowed_hosts=('testserver',))) as c:
            inp=c.post('/api/ifc-inputs',files={'file':('two-target.ifc',source)}).json()
            prepared=c.post('/api/repair-requests/prepare',json={'input_id':inp['input_id'],'view_version':'v',
                'targets':[{'step_id':o.id(),'global_id':o.GlobalId,'view_version':'v'} for o in targets],
                'user_text':'在这两面墙上各增加一扇窗，宽915毫米、高1830毫米，窗台305毫米，距墙局部起点1000毫米。'}).json()
            response=c.post('/api/repair-tasks',json={'prepared_request_id':prepared['prepared_request_id'],'client_request_id':'injected-transaction'})
            assert response.status_code==202,response.text
            done=wait(c,response.json()['task_id'],seconds=180)
            assert len(observed)==2
            assert done['status']!='succeeded' and not done['successful_artifact_publishable']
            assert c.get(inp['download_url']).content==source
            files=c.get(done['artifacts_url']).json()['artifacts']
            assert not any(f['role']=='successful_ifc' for f in files)
            assert not list((tmp_path/'web/native/runs').rglob('successful/repaired.ifc'))
