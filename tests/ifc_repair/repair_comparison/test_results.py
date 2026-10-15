"""Compact export keeps selected outcomes and returned reasoning, not runtime logs."""
import gzip
import json
import zipfile
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import results
from scripts.ifc_repair.repair_comparison.contracts import write_json
from scripts.ifc_repair.repair_comparison.ledger import Ledger


def _run(tmp_path, *, submitted=True):
    root = tmp_path/'work'
    ledger = Ledger(root/'control.sqlite')
    ledger.create('sample-B', case_id='sample', arm='B', mode='live_formal',
                  budget={'tokens': 100, 'calls': 2, 'active_seconds': 60,
                          'tool_seconds': 10, 'extensions': []})
    ledger.start('sample-B')
    ledger.reserve('sample-B', 'request-1', 20, {'stage': 'changeset'})
    ledger.settle('sample-B', 'request-1', usage={'prompt_tokens': 3,
        'completion_tokens': 2, 'total_tokens': 5}, response={'body': {'model': 'deepseek-returned',
        'choices': [{'message': {'role': 'assistant', 'content': 'model output',
                                'reasoning_content': '原样返回的推理。'}}]}}, failed=False)
    artifact = root/'output.ifc'
    if submitted:
        artifact.write_bytes(b'ISO-10303-21;\npublic result\n')
    ledger.finish('sample-B', 'submitted' if submitted else 'no_output',
                  artifact={'path': str(artifact)} if submitted else None,
                  detail={'reason': 'test terminal'})
    write_json(root/'experiment.json', {'order': ['sample-B']})
    return {'run_id': 'sample-B', 'case_id': 'sample', 'arm': 'B',
            'status': 'submitted' if submitted else 'no_output',
            'artifact': str(artifact) if submitted else None, 'ledger_root': str(root),
            'strict_success': None, 'metric_status': 'deferred'}, ledger


def test_export_retains_bytes_usage_questions_and_real_returned_reasoning(tmp_path):
    row, ledger = _run(tmp_path)
    # Final evidence can contain recorded dialogue without requiring runtime logs.
    ledger.record(row['run_id'], 'answer', {'text': 'User-approved fact'})
    out = tmp_path/'compact'
    value = results.export_runs([row], out)
    selected = value['rows'][0]
    assert (out/selected['artifact']).read_bytes() == b'ISO-10303-21;\npublic result\n'
    assert selected['strict_success'] is None and selected['metric_status'] == 'deferred'
    assert selected['calls'][0]['usage']['total_tokens'] == 5
    assert selected['dialogue'][0]['payload']['text'] == 'User-approved fact'
    with gzip.open(out/'reasoning.jsonl.gz', 'rt', encoding='utf8') as f:
        reasoning = [json.loads(line) for line in f]
    assert reasoning[0]['messages'][0]['reasoning_content'] == '原样返回的推理。'
    assert reasoning[0]['model_returned'] == 'deepseek-returned'
    assert not any(p.name in {'wire', 'runtime', 'control.sqlite'} for p in out.rglob('*'))


def test_no_output_is_explicit_and_cannot_export_an_intermediate_ifc(tmp_path):
    row, _ = _run(tmp_path, submitted=False)
    value = results.export_runs([row], tmp_path/'out')
    assert value['rows'][0]['artifact'] is None
    assert value['rows'][0]['terminal_detail'] == {'reason': 'test terminal'}
    assert not list((tmp_path/'out').rglob('*.ifc'))
    row['artifact'] = str(tmp_path/'unsubmitted.ifc')
    with pytest.raises(ValueError, match='TERMINAL_ARTIFACT'):
        results.export_runs([row], tmp_path/'bad')


def test_terminal_only_and_unique_selection_are_required(tmp_path):
    row, _ = _run(tmp_path)
    with pytest.raises(ValueError, match='DUPLICATE_SELECTION'):
        results.export_runs([row, row], tmp_path/'dup')
    row['status'] = 'awaiting_user'
    with pytest.raises(ValueError, match='TERMINAL_REQUIRED'):
        results.export_runs([row], tmp_path/'active')


def test_messages_thinking_blocks_are_preserved_without_search_logs():
    call = {'response': json.dumps({'body': {'model': 'native-returned', 'content': [
        {'type': 'thinking', 'thinking': 'returned thinking', 'signature': 'returned signature'},
        {'type': 'text', 'text': 'answer'},
        {'type': 'web_search_tool_result', 'content': [{'type': 'web_search_result'}]}]}})}
    value = results.returned_messages(call)
    assert value['messages'] == [
        {'type': 'thinking', 'thinking': 'returned thinking', 'signature': 'returned signature'},
        {'type': 'text', 'text': 'answer'}]


def test_retiring_logs_does_not_reset_the_experiment_budget(tmp_path):
    from scripts.ifc_repair.repair_comparison.batch_operator import accounted_usage
    from scripts.ifc_repair.repair_comparison.demo_workflow import status
    row, _ = _run(tmp_path)
    root = tmp_path/'work'
    (root/'operator').mkdir()
    write_json(root/'operator/additional-attempts.json', {'roots': [],
        'archived_usage': {'known_tokens': 100, 'reserved_tokens': 17, 'unknown_calls': 1}})
    assert accounted_usage(root, status(root)) == {
        'known_tokens': 105, 'reserved_tokens': 17, 'unknown_calls': 1}
    write_json(root/'operator/additional-attempts.json', {'roots': [],
        'archived_usage': {'known_tokens': -100, 'reserved_tokens': 0, 'unknown_calls': 0}})
    with pytest.raises(ValueError, match='INVALID_ARCHIVED_USAGE'):
        accounted_usage(root, status(root))


def test_batch_owner_exports_compact_results_only_when_all_tasks_are_terminal(tmp_path, monkeypatch):
    from scripts.ifc_repair.repair_comparison import batch_operator
    _, _ = _run(tmp_path)
    monkeypatch.setattr(batch_operator.formal, 'experiment_plan', lambda root: {
        'authorization': {'total_api_token_limit': 1000}})
    out = tmp_path/'finished'
    assert batch_operator.run(tmp_path/'work', results_path=out) == 0
    value = json.loads((out/'latest-records.json').read_text(encoding='utf8'))
    assert len(value['rows']) == 1 and value['rows'][0]['artifact'] == 'outputs/sample/B.ifc'
    assert value['rows'][0]['strict_success'] is None


def test_historical_archive_marks_missing_dialogue_without_fabricating_it(tmp_path):
    row, ledger = _run(tmp_path, submitted=False)
    archive = tmp_path/'historical.zip'
    with zipfile.ZipFile(archive, 'w') as stream:
        stream.writestr('ledger/state.original.json', json.dumps(ledger.snapshot(row['run_id'])))
        stream.writestr('ledger/calls.sqlite-rows.original.json', json.dumps(ledger.calls(row['run_id'])))
    row['history_record'] = str(archive)
    value = results.export_runs([row], tmp_path/'out')
    assert value['rows'][0]['dialogue'] == []
    assert value['rows'][0]['dialogue_capture'] == 'not_retained_in_source'


def test_text_alone_is_not_a_returned_thinking_chain():
    assert not results.has_returned_thinking([{'type': 'text', 'text': 'Answer only'}])
    assert results.has_returned_thinking([{'reasoning_content': 'returned thought'}])
    assert results.has_returned_thinking([{'type': 'thinking', 'thinking': 'returned thought'}])


def test_retired_accounting_keeps_stream_completion_and_unknown_reservations(tmp_path):
    from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
    row, ledger = _run(tmp_path, submitted=False)
    root = Path(row['ledger_root'])
    # Use a separate messages task containing both a complete and incomplete response.
    ledger.create('native-D', case_id='native', arm='D', mode='live_formal',
        budget={'tokens':100,'calls':2,'active_seconds':60,'tool_seconds':10,'extensions':[]})
    ledger.start('native-D')
    for request, complete in [('complete', True), ('unknown', False)]:
        ledger.reserve('native-D', request, 20, {'wire_protocol':'messages'})
        ledger.settle('native-D', request, usage={'input_tokens':3,'output_tokens':2},
            response={'usage_complete':complete,'body':{'content':[{'type':'text','text':'returned'}]}},
            failed=not complete)
    ledger.finish('native-D', 'no_output')
    write_json(root/'experiment.json', {'order':['sample-B','native-D']})
    before = [s['usage'] for s in carrier.status(root)]
    results.retire_accounting(root)
    assert [s['usage'] for s in carrier.status(root)] == before
    assert ledger.calls('native-D')[0]['response'] == {'usage_complete':True}
    assert ledger.calls('native-D')[1]['response'] == {'usage_complete':False}
    with pytest.raises(ValueError, match='FINANCIAL_CHECKPOINT_IS_NOT_RESULT_AUTHORITY'):
        results.export_experiment(root, tmp_path/'incorrect')
    from scripts.ifc_repair.repair_comparison import batch_operator
    with pytest.raises(ValueError, match='FINANCIAL_CHECKPOINT_NOT_RUNNABLE'):
        batch_operator.run(root)
