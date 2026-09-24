"""General preparation must retain the details previously confined to probes."""
import json
import pytest
from pathlib import Path

from text2ifc_compiler import compile_document
from text2ifc_ifc2text.compact_pipeline import prepare_compact, write_compact
from text2ifc_ifc2text.observation import all_items
from text2ifc_agent.providers import ProviderOutput


def source(tmp_path):
    doc=json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    doc['schema_version']='bim-json/2.3'
    doc['entities']=[e for e in doc['entities'] if e['id'] in {'project-1','site-1','building-1','storey-1','wall-1'}]
    doc['relationships']=[]
    wall=next(e for e in doc['entities'] if e['id']=='wall-1')
    wall['attributes']['Representation']['profile']={'kind':'polygon','points':[[-2500,-100],[2500,-100],[2300,100],[-2400,100],[-2500,-100]]}
    path=tmp_path/'source.ifc'; assert compile_document(doc,path).success
    return path


def test_default_prepare_and_write_preserve_explicit_polygon(tmp_path):
    path=source(tmp_path); before=path.read_bytes(); out=tmp_path/'prepared'
    result=prepare_compact(path,out)
    facts=json.loads((out/'source-facts.json').read_text(encoding='utf-8'))
    wall=next(i for c,i in all_items(facts) if c=='walls')
    assert wall['solid_detail']['requires_explicit_outline']
    assert result['description_version']=='0.8'
    deterministic=(out/'design-description-deterministic.md').read_text(encoding='utf-8')
    assert '末尾闭合点不可省略' in deterministic
    class Narrator:
        def generate_candidate(self, **kwargs):
            return ProviderOutput(json.dumps({'overview':'建筑按标高展开。','storey_notes':[{'storey':s['label'],'text':'本层构件见明细。'} for s in facts['storeys']]},ensure_ascii=False),{'evidence_class':'offline_fake'})
    write_compact(output=out,provider=Narrator())
    written=(out/'design-description.md').read_text(encoding='utf-8')
    assert '末尾闭合点不可省略' in written
    from scripts.ifc2text.compact_campaign import verify_text
    (out/'content-review.json').write_text(json.dumps({'decision':'allow_diagnostic_reconstruction'}),encoding='utf-8')
    assert verify_text(out)==written
    assert path.read_bytes()==before


def test_general_preparation_applies_host_policy_on_copy(tmp_path):
    import ifcopenshell
    from ifcopenshell.api.root import create_entity
    doc=json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    path=tmp_path/'mixed.ifc'; assert compile_document(doc,path).success
    model=ifcopenshell.open(str(path)); door=model.by_type('IfcDoor')[0]
    target=create_entity(model,ifc_class='IfcBuildingStorey',name='reference')
    target.Elevation=1234.
    for relation in list(door.ContainedInStructure):
        remaining=[e for e in relation.RelatedElements if e!=door]
        if remaining: relation.RelatedElements=remaining
        else: model.remove(relation)
    relation=create_entity(model,ifc_class='IfcRelContainedInSpatialStructure')
    relation.RelatingStructure=target;relation.RelatedElements=[door]
    model.write(str(path)); before=path.read_bytes()
    out=tmp_path/'prepared'; result=prepare_compact(path,out)
    assert result['containment_policy']=='host_storey_for_selected_fillings'
    assert result['normalization']['moved_count']==1
    assert path.read_bytes()==before
    normalized=ifcopenshell.open(result['effective_source_path'])
    ndoor=normalized.by_guid(door.GlobalId)
    host=ndoor.FillsVoids[0].RelatingOpeningElement.VoidsElements[0].RelatingBuildingElement
    assert ndoor.ContainedInStructure[0].RelatingStructure==host.ContainedInStructure[0].RelatingStructure


@pytest.mark.parametrize('version,override,expected', [
    ('0.8', {}, 'bim-json/2.4'),
    ('0.4', {}, None),
    ('0.8', {'bim_json_schema_version': 'bim-json/2.3'}, 'bim-json/2.3'),
])
def test_campaign_selects_new_contract_for_new_description_only(tmp_path,version,override,expected):
    from scripts.ifc2text.compact_campaign import generation_schema_for_prepared
    (tmp_path/'source-facts.json').write_text(json.dumps({'description_policy':{'version':version}}),encoding='utf-8')
    assert generation_schema_for_prepared(override,tmp_path)==expected
