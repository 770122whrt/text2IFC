"""Offline public Brief -> registered Generator stage -> compiler diagnostic seam."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import shutil
import pytest
from scripts.ifc2text.recover_wall_v07 import generator_diagnostic, single_wall_text
from scripts.ifc2text.attribution_probe_v01 import run_public_brief


def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def test_public_brief_and_generator_compile_without_source_side_channel(tmp_path):
    seam=load_module('tests/ifc2text/test_attribution_probe_v01.py','attribution_fixture_v07')
    cfg,client,calls=seam.fake_client()
    public=json.loads(seam.BASE.read_text(encoding='utf-8'))['original_request']  # Frozen response belongs to this public context.
    r=run_public_brief(public,tmp_path/'brief',cfg,client,evidence_kind='offline_replay')
    assert r['controller_status']=='ready'
    call=Path(r['run_dir'])/'calls/01-design-brief'
    design=tmp_path/'design-source';design.mkdir()
    for name in ('design-brief.json','conversation.json','context-selection.json'):
        shutil.copyfile(call/name,design/name)
    (design/'input.txt').write_text(public,encoding='utf-8')
    graph=json.loads(Path('tests/contract_v2/fixtures/complete.json').read_text(encoding='utf-8'))
    graph['schema_version']='bim-json/2.3'
    graph['entities']=[e for e in graph['entities'] if e['id'] in {'project-1','site-1','building-1','storey-1','wall-1'}]
    graph['relationships']=[]
    wall=next(e for e in graph['entities'] if e['id']=='wall-1')
    wall['attributes']['Representation']['profile']={'kind':'polygon','points':[[0,-100],[4000,-100],[4000,100],[200,100],[0,-100]]}
    fixture=load_module('tests/ifc2text/test_offline_public_bridge.py','generation_fixture_v07')
    provider=fixture._SequenceLiveProvider([graph])
    result=generator_diagnostic(design,tmp_path/'generator',provider,evidence_kind='offline_frozen_fixture')
    assert len(provider.session_ids)==1
    assert result['compile_success'] and result['wall_count']==1
    assert result['profiles']==['IfcArbitraryClosedProfileDef']
    assert result['accepted_publication'] is False
    rendered=(tmp_path/'generator/generator/prompt-rendered.md').read_text(encoding='utf-8')
    assert 'single-wall-evaluator-only' not in rendered and 'source-facts.json' not in rendered
    with pytest.raises(ValueError,match='ATTEMPT_EXISTS'):
        generator_diagnostic(design,tmp_path/'generator',provider,evidence_kind='offline')
    assert len(provider.session_ids)==1


def test_micro_text_contains_only_public_detail_and_no_source_ids():
    w={'label':'W011','source_global_id':'PRIVATE_SOURCE_ID',
       'solid_detail':{'status':'supported_vertical_extrusion','bottom_outline_xy_mm':[[0,0],[100,0],[90,20],[0,20],[0,0]],
                       'bottom_z_mm':500.,'height_mm':2000.}}
    text=single_wall_text(w)
    assert 'PRIVATE_SOURCE_ID' not in text
    assert '(100.0,0.0)' in text and '竖直拉伸 2000.0' in text
    assert '不扣任何洞' in text


def test_material_uncertainty_cannot_be_invented_in_narrative():
    from text2ifc_ifc2text.narration_v07 import validate_notes
    context={'storeys':[{'id':'level-A'}]}
    bad={'overview':'按楼层列出空间和构件。','storey_notes':[{'storey':'level-A','text':'本层有覆盖层，材料关联亦未确认。'}]}
    with pytest.raises(ValueError,match='MATERIAL_ASSERTIONS'):
        validate_notes(bad,context)
    good={'overview':'按楼层列出空间和构件，材料随后列示。','storey_notes':[{'storey':'level-A','text':'本层没有空间记录，仅有覆盖层。'}]}
    validate_notes(good,context)


def test_v07_narration_prompt_is_registered_without_overwriting_v06():
    from text2ifc_agent.prompt_registry import render_prompt,load_prompt_registry
    r=load_prompt_registry()
    assert 'ifc2text-compact-narrator.v0.6' in r and 'ifc2text-compact-narrator.v0.7' in r
    text=render_prompt(template_id='ifc2text-compact-narrator.v0.7',inputs={'FACT_SUMMARY':{},'OUTPUT_SCHEMA':{}})['text']
    assert 'global materials list cannot justify' in text
    assert all(x not in text for x in ('hxp','W013','S03'))
