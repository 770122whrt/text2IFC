"""Short-context projections preserve public authority and tool protocol."""
from copy import deepcopy
import json

import pytest

from scripts.ifc_repair.qwen_context import ContextLimitError, ContextPolicy, compact_request


def body(messages):
    return {'model': 'qwen', 'messages': messages, 'tools': [], 'max_tokens': 512}


def pair(i, text):
    return [
        {'role': 'assistant', 'content': None, 'tool_calls': [
            {'id': f'c{i}', 'type': 'function', 'function': {'name': 'read_file', 'arguments': '{"path":"model.ifc"}'}}]},
        {'role': 'tool', 'tool_call_id': f'c{i}', 'content': json.dumps({'ok': True, 'text': text})}]


def test_small_input_is_unchanged():
    original = body([{'role': 'system', 'content': 'protocol'}, {'role': 'user', 'content': '修复窗。'}])
    before = deepcopy(original)
    projected, stats = compact_request(original, arm='G', policy=ContextPolicy())
    assert projected == original == before
    assert stats['mode'] == 'unchanged' and stats['estimator'] == 'lexical_estimate_25pct_margin'


def test_g_archives_large_results_and_reuses_refs_on_resume(tmp_path):
    messages = [{'role': 'system', 'content': 'protocol'}, {'role': 'user', 'content': 'Window at x=2000 mm.'}]
    for i in range(8):
        messages += pair(i, 'public IFC line\n' * 3000)
    messages += [{'role': 'user', 'content': 'Human confirmed: keep 864 mm.'}]
    original = body(messages)
    before = deepcopy(original)
    policy = ContextPolicy(context_tokens=12000, output_tokens=512, overhead_tokens=256, recent_pairs=2)
    projected, stats = compact_request(original, arm='G', policy=policy, workspace=tmp_path)
    assert original == before
    assert stats['after_estimate'] + 512 + 256 <= 12000
    assert [m for m in projected['messages'] if m['role'] in {'system', 'user'}] == [m for m in messages if m['role'] in {'system', 'user'}]
    refs = list((tmp_path/'.qwen-context').glob('*.txt'))
    assert refs and any('public IFC line' in p.read_text(encoding='utf8') for p in refs)
    second, _ = compact_request(original, arm='G', policy=policy, workspace=tmp_path)
    assert second == projected and set(refs) == set((tmp_path/'.qwen-context').glob('*.txt'))
    expected = set()
    for m in projected['messages']:
        if m['role'] == 'assistant':
            expected = {c['id'] for c in m.get('tool_calls', [])}
        if m['role'] == 'tool':
            assert m['tool_call_id'] in expected
            expected.remove(m['tool_call_id'])
    assert not expected


def test_pending_calls_and_recent_geometry_survive(tmp_path):
    messages = [{'role': 'system', 'content': 'protocol'}, {'role': 'user', 'content': 'request'}]
    for i in range(9):
        messages += pair(i, 'old data\n' * 2000 if i < 8 else 'size=0.864 m; x=12227.5 mm; failed: host mismatch')
    pending = pair(99, '')[0]
    messages.append(pending)
    projected, _ = compact_request(body(messages), arm='G', policy=ContextPolicy(context_tokens=10000, output_tokens=512), workspace=tmp_path)
    assert projected['messages'][-1] == pending
    assert 'size=0.864 m; x=12227.5 mm; failed: host mismatch' in json.dumps(projected)


def scene_prompt(scene, previous):
    return ('header\n## Public request\n修复 x=3000 mm 的窗，保留其余。\n'
            '## Read-only query results so far\n'+json.dumps(scene, indent=2)+'\n'
            '## Validation feedback\n'+json.dumps({'error': 'wrong host', 'record_id': 'r0'})+'\n'
            '## Previous failed proposal (bounded data)\n'+json.dumps(previous)+'\n'
            '## Response schema\n'+json.dumps({'required': ['action', 'query_id']})+'\n')


def test_f_keeps_cited_and_latest_query_cohorts_and_full_denominator():
    scene = {'source_role': 'current_public_ifc', 'records': [], 'types': {'t1': {'unit': 'm'}}, 'queries': []}
    for i in range(8):
        scene['records'].append({'id': f'r{i}', 'type_id': 't1', 'description': 'a'*3500})
        scene['queries'].append({'query_id': f'q{i}', 'query_ids': [f'q{i}'], 'record_ids': [f'r{i}'], 'total_matches': 1, 'complete': True})
    original = body([{'role': 'user', 'content': scene_prompt(scene, {'query_id': 'q0', 'reference_id': 'r0'})}])
    policy = ContextPolicy(context_tokens=12000, output_tokens=512, overhead_tokens=256, recent_scene_queries=2)
    projected, stats = compact_request(original, arm='F', policy=policy)
    text = projected['messages'][0]['content']
    scene_out = json.loads(text.split('## Read-only query results so far\n')[1].split('\n## ')[0])
    assert {q['query_id'] for q in scene_out['queries']} == {'q0', 'q6', 'q7'}
    assert {r['id'] for r in scene_out['records']} == {'r0', 'r6', 'r7'}
    assert all(q['record_ids'] and q['total_matches'] == 1 and q['complete'] for q in scene_out['queries'])
    assert '修复 x=3000 mm 的窗，保留其余。' in text
    assert 'wrong host' in text and 'm' in scene_out['types']['t1']['unit']
    assert stats['mode'] == 'scene_projection'


def test_protected_input_only_fails_after_compaction_attempt():
    with pytest.raises(ContextLimitError, match='PROTECTED_CONTEXT_EXCEEDS_WINDOW'):
        compact_request(body([{'role': 'system', 'content': 'x'*30000}]), arm='G',
                        policy=ContextPolicy(context_tokens=8000, output_tokens=512))


def test_unsupported_arm_never_transforms():
    with pytest.raises(ValueError, match='QWEN_ARMS_ONLY'):
        compact_request(body([]), arm='B', policy=ContextPolicy())
