"""Offline failure-family checks for a public-Brief-only diagnostic pair."""
from __future__ import annotations
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from scripts.ifc2text.attribution_probe_v01 import request_for, run_public_brief, SUFFIX
from text2ifc_agent.openai_compat import load_openai_compatible_runtime_config

BASE=Path('tests/fixtures/ifc2text/attribution-brief-v01.json')


def fake_client(kind='valid'):
    brief=json.loads(BASE.read_text(encoding='utf-8'))
    content=json.dumps(brief,ensure_ascii=False) if kind=='valid' else '{"status":' if kind=='truncated' else 'not JSON'
    payload={'id':'offline-attribution-replay','model':'fixture','choices':[{'finish_reason':'length' if kind=='truncated' else 'stop','message':{'content':content}}],
        'usage':{'prompt_tokens':20,'completion_tokens':10,'total_tokens':30}}
    calls=[]
    def create(**kwargs):
        calls.append(kwargs)
        return payload
    client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    cfg=load_openai_compatible_runtime_config({'TEXT2IFC_PROVIDER':'deepseek','API_KEY':'test-key',
        'OPENAI_BASE_URL':'https://example.invalid','TEXT2IFC_DEEPSEEK_MODEL':'fixture'})
    return replace(cfg,max_input_tokens=131072,max_completion_tokens=131072),client,calls


def test_public_text_change_is_only_generic_containment_rule():
    for text in ('楼层 A 的窗宿主在 B。','S01 与 S02 同名；位置未知。','Several storeys; no windows.'):
        assert request_for(text,'original')==text
        assert request_for(text,'explicit_containment')==text+SUFFIX
    assert not any(value in SUFFIX for value in ('hxp','N001','W007','GlobalId','S01','S02'))
    with pytest.raises(ValueError):request_for('x','bad')


def test_frozen_brief_replay_uses_public_controller_and_never_publishes_ifc(tmp_path):
    cfg,client,calls=fake_client()
    original=json.loads(BASE.read_text(encoding='utf-8'))['original_request']
    result=run_public_brief(original,tmp_path/'replay',cfg,client,evidence_kind='offline_replay')
    assert len(calls)==1
    assert result['controller_status']=='ready'
    assert result['same_original_text']
    assert not result['generator_invoked'] and not result['ifc_publication']
    assert not list(tmp_path.rglob('*.ifc'))
    assert result['evidence_kind']=='offline_replay'
    assert 'source-facts.json' not in calls[0]['messages'][0]['content']


@pytest.mark.parametrize('kind',['truncated','malformed'])
def test_bad_response_keeps_evidence_and_no_generator(tmp_path,kind):
    cfg,client,calls=fake_client(kind)
    with pytest.raises(Exception):run_public_brief('只描述一个楼层。',tmp_path/kind,cfg,client,evidence_kind='offline_failure_injection')
    assert len(calls)==1
    assert (tmp_path/kind/'terminal.json').exists()
    assert list((tmp_path/kind).rglob('response.raw.json'))
    assert not list(tmp_path.rglob('*.ifc'))


def test_existing_attempt_blocks_transport(tmp_path):
    cfg,client,calls=fake_client()
    (tmp_path/'started.json').write_text('{}',encoding='utf-8')
    with pytest.raises(FileExistsError):run_public_brief('unchanged',tmp_path,cfg,client,evidence_kind='offline')
    assert not calls


def test_real_material_list_is_not_representable_in_active_schema():
    from jsonschema import Draft202012Validator
    schema=json.loads(Path('schemas/bim-json/2.3/schema.json').read_text(encoding='utf-8'))
    validator=Draft202012Validator({'$defs':schema['$defs'],'$ref':'#/$defs/materialAssignment'})
    assert validator.is_valid({'kind':'single_material','name':'Wood'})
    assert not validator.is_valid({'kind':'material_list','names':['Wood','Paint']})
    assert schema['$defs']['entity']['properties']['materials']['maxItems']==1
