"""Real public API/applicator/evaluator with only Provider output replaced."""
import hashlib
import json
import time
from pathlib import Path

import ifcopenshell
import ifcopenshell.util.element
import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.api import RepairAPI

ROOT = Path(__file__).resolve().parents[2]
TARGET = '2CsmzAChHF6O6maGXlo6PS'


class PropertyProvider:
    def __init__(self, output, request, mode='complete'):
        self.output = output
        self.request = request
        self.calls = []
        self.mode = mode

    def generate_candidate(self, **kwargs):
        self.calls.append(kwargs)
        version=kwargs['schema']['properties']['schema_version']['const']
        if self.mode == 'malformed_then_corrected' and len(self.calls) == 1:
            return ProviderOutput(text='{"truncated":',metadata={'provider':'offline-test','model':'offline-fixture-v1'})
        if 'intent-body' in version:
            src={'source_kind':'user_request','reference':'request:/text','excerpt':self.request}
            props={'Reference':'240','IsExternal':True,'ExtendToStructure':False,'LoadBearing':False}
            body={'schema_version':version,'operations':[{
                'operation_id':'restore-wall-properties','operation_type':'set_occurrence_properties',
                'routing_intent':{'component_family':'occurrence','action':'set_properties','operation_profile':'occurrence.set-properties','source':src},
                'target_query':{'schema_version':'text2ifc/ifc-target-query/0.1','allowed_ifc_classes':['IfcWallStandardCase'],'global_id':TARGET},
                'parameters':{},'attribute_intents':[],
                'property_intents':[{'intent_kind':'exact_property','set_name':'Pset_WallCommon','property_name':key,'raw_value':value,'raw_unit':None,'requested_value_type':'IfcIdentifier' if key=='Reference' else 'IfcBoolean','scope':'occurrence_direct','source':src} for key,value in props.items()],
                'semantic_bundle_refs':[],'quantity_intents':[],'occurrence_reuse_intent':None,'prototype_intent':None,'appearance_intent':None,'provenance':[src]}],
                'unsupported_requests':[],'semantic_bundles':[],'provenance':[src]}
            if self.mode == 'clarification_resume' and len(self.calls) == 1:
                body['operations'][0]['property_intents'][0]['raw_value'] = None
        else:
            paths=[p for p in self.output.rglob('renderer-input.json') if 'RESOLVED_OPERATIONS' in json.loads(p.read_text(encoding='utf-8'))]
            rendered=json.loads(max(paths,key=lambda p:p.stat().st_mtime_ns).read_text(encoding='utf-8'))
            body={'schema_version':version,'draft_id':'offline-property-draft','base_model_fingerprint':rendered['MODEL_FINGERPRINT'],
                  'source_request_hash':rendered['SOURCE_REQUEST_HASH'],'semantic_manifest_ref':rendered['SEMANTIC_MANIFEST_REF'],
                  'semantic_manifest_sha256':rendered['SEMANTIC_MANIFEST_SHA256'],'semantic_summary':rendered['SEMANTIC_SUMMARY'],
                  **rendered['RESOLVED_OPERATIONS'],'preconditions':[],'postconditions':[]}
        return ProviderOutput(text=json.dumps(body),metadata={'provider':'deterministic-offline-test','model':'offline-fixture-v1','evidence_class':'offline'})


@pytest.mark.parametrize('mode', ['complete', 'malformed_then_corrected', 'clarification_resume'])
def test_dataset_relation_damage_restores_properties_through_public_api(tmp_path, mode):
    source=ROOT/'dataset/external/bimnet/vvo.ifc'
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    model=ifcopenshell.open(str(source))
    target=model.by_guid(TARGET)
    rel=next(r for r in target.IsDefinedBy if r.is_a('IfcRelDefinesByProperties') and r.RelatingPropertyDefinition.Name=='Pset_WallCommon')
    removed_guid=rel.GlobalId
    model.remove(rel)
    damaged=tmp_path/'damaged.ifc';model.write(str(damaged))
    damaged_bytes=damaged.read_bytes()
    request=f'For wall {TARGET}, set occurrence Pset_WallCommon.Reference to string 240, IsExternal true, ExtendToStructure false, LoadBearing false. Preserve all geometry and other facts.'
    output=tmp_path/'public'
    provider=PropertyProvider(output,request,mode)
    started=time.monotonic()
    api=RepairAPI(output,provider=provider)
    result=api.start(damaged,request)
    if mode == 'clarification_resume':
        assert result.status == 'clarification_required', result
        assert not list(output.rglob('successful-repaired.ifc'))
        api = RepairAPI(output, provider=provider)
        result = api.continue_with_answer(result.run_id, clarification_id=result.clarification.clarification_id,
            expected_state_version=result.state_version, answer={'kind':'add_detail','detail':'Reference must be string "240"; the other three Boolean values remain as requested.'})
    (tmp_path/'public-path-result.json').write_text(json.dumps({'status':result.status,'elapsed_seconds':time.monotonic()-started,'calls':len(provider.calls),'source_entities':sum(1 for _ in model)},default=str),encoding='utf-8')
    assert result.status=='succeeded',result
    assert len(provider.calls)==(2 if mode=='complete' else 3)
    public=''.join(call['prompt'] for call in provider.calls)
    assert removed_guid not in public
    assert 'evaluator-private' not in public
    assert max(len(c['prompt']) for c in provider.calls)<262144
    assert damaged.read_bytes()==damaged_bytes
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    paths=list(output.rglob('repaired.ifc'))
    assert paths
    repaired=ifcopenshell.open(str(paths[0]))
    pset=ifcopenshell.util.element.get_pset(repaired.by_guid(TARGET),'Pset_WallCommon',should_inherit=False)
    assert {k:pset[k] for k in ('Reference','IsExternal','ExtendToStructure','LoadBearing')}=={'Reference':'240','IsExternal':True,'ExtendToStructure':False,'LoadBearing':False}
    reopened_api = RepairAPI(output, provider=provider)
    assert reopened_api.store.read_result(result.run_id).status == 'succeeded'
    assert len(provider.calls)==(2 if mode=='complete' else 3)
