"""Offline terminal export never turns staging files or missing thoughts into evidence."""
import json
import sqlite3
from contextlib import closing

import pytest

from scripts.ifc_repair.repair_comparison import results
from scripts.ifc_repair.repair_comparison.contracts import sha256
from scripts.ifc_repair.repair_comparison.ledger import Ledger


BUDGET = {'tokens': 100, 'calls': 3, 'active_seconds': 60,
          'tool_seconds': 10, 'extensions': []}


def _task(tmp_path, *, arm='B', status='submitted', native=None, thoughts='真实返回的推理。',
          run_id=None, unknown=False, detail=None, native_envelope=False):
    root = tmp_path/'experiment'
    clock = [100.0]
    ledger = Ledger(root/'control.sqlite', clock=lambda: clock[0])
    run_id = run_id or 'case-001-'+arm
    # These fixtures test the consumer of the seven-arm ledger, independently
    # of which arm-creation implementation is installed by the scheduler.
    ledger.create(run_id, case_id='case-001', arm=arm if arm in 'ABCD' else 'A',
                  budget=BUDGET, mode='offline_development')
    ledger.start(run_id)
    ledger.reserve(run_id, 'call-1', 20, {'stage': 'changeset'})
    message = {'content': 'The answer is not a returned thought chain.'}
    if thoughts is not None:
        message['reasoning_content'] = thoughts
    ledger.settle(run_id, 'call-1', usage={'prompt_tokens': 3, 'completion_tokens': 2},
                  response={'body': {'choices': [{'message': message}]}}, failed=False)
    if unknown:
        ledger.reserve(run_id, 'call-2', 20, {'wire_protocol': 'messages'})
        ledger.settle(run_id, 'call-2', usage={'input_tokens': 4, 'output_tokens': 7},
                      response={'usage_complete': False, 'body': {'content': [
                          {'type': 'thinking', 'thinking': '另一次实际返回。'}]}}, failed=True)
    if native is not None:
        ledger.set_native(run_id, native if native_envelope else {'result': native})
    intermediate = root/'workspaces'/run_id/'output'/'intermediate.ifc'
    intermediate.parent.mkdir(parents=True)
    intermediate.write_bytes(b'not formally submitted')
    artifact = root/'artifacts'/run_id/'result.ifc'
    if status == 'submitted':
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b'ISO-10303-21;\nfinal fixture bytes\nEND-ISO-10303-21;\n')
    clock[0] = 112.0
    ledger.finish(run_id, status, artifact={'path': str(artifact), 'sha256': sha256(artifact)}
                  if status == 'submitted' else None, detail=detail)
    _edit_state(root, run_id, {'arm': arm})
    return root, run_id, artifact


def _edit_state(root, run_id, changes, *, terminal=False):
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        state = json.loads(db.execute('SELECT state FROM runs WHERE run_id=?', (run_id,)).fetchone()[0])
        state.update(changes)
        db.execute('UPDATE runs SET state=? WHERE run_id=?', (json.dumps(state), run_id))
        if terminal:
            row = db.execute("SELECT seq,payload FROM events WHERE run_id=? AND kind='terminal'",
                             (run_id,)).fetchone()
            payload = json.loads(row[1])
            payload.update({key: value for key, value in changes.items() if key in {'status', 'artifact', 'detail'}})
            db.execute('UPDATE events SET payload=? WHERE seq=?', (json.dumps(payload), row[0]))
        db.commit()


def test_submitted_bytes_usage_time_and_validation_are_distinct(tmp_path):
    root, run_id, artifact = _task(tmp_path, unknown=True, native={
        'status': 'validation_failed', 'stage': 'production_validation',
        'reason_code': 'NATIVE_CHECK_FAILED', 'validation': {'passed': False}},
        detail='explicitly submitted, not scored')
    before = (root/'control.sqlite').read_bytes()
    received = []

    def common_check(path):
        received.append(path)
        return {'passed': True, 'status': 'passed', 'validator': 'offline fixture'}

    output = tmp_path/'compact'
    summary = results.export_task(root, output, run_id, format_check=common_check)
    leaf = output/'case-001'/'B'
    report = (leaf/'report.md').read_text(encoding='utf8')
    assert {p.name for p in leaf.iterdir()} == {'report.md', 'repaired.ifc'}
    assert (leaf/'repaired.ifc').read_bytes() == artifact.read_bytes()
    assert received == [artifact.resolve()]
    assert summary['status'] == 'submitted'
    assert summary['usage']['total_tokens'] is None
    assert summary['usage']['known_total_tokens'] == 5
    assert summary['usage']['unknown_calls'] == 1
    assert summary['usage']['reserved_tokens'] == 20
    assert summary['time']['active_elapsed_s'] == 12
    assert summary['time']['wall_elapsed_s'] == 12
    assert summary['native_validation']['passed'] is False
    assert summary['common_format_validation']['passed'] is True
    assert 'NATIVE_CHECK_FAILED' in report and 'production_validation' in report
    assert 'Repair score: pending' in report
    assert '真实返回的推理。' in report and '另一次实际返回。' in report
    assert (root/'control.sqlite').read_bytes() == before


@pytest.mark.parametrize('arm', list('ABCDEFG'))
@pytest.mark.parametrize('thoughts', ['the returned reasoning', None])
def test_all_arms_capture_only_returned_reasoning_and_never_intermediate_ifc(tmp_path, arm, thoughts):
    root, run_id, _ = _task(tmp_path, arm=arm, status='no_output', thoughts=thoughts)
    output = tmp_path/'compact'
    summary = results.export_task(root, output, run_id)
    leaf = output/'case-001'/arm
    report = (leaf/'report.md').read_text(encoding='utf8')
    assert [p.name for p in leaf.iterdir()] == ['report.md']
    assert summary['artifact'] is None
    assert summary['reasoning_status'] == ('returned' if thoughts else 'not_returned')
    assert 'The answer is not a returned thought chain.' not in report
    if thoughts:
        assert thoughts in report
    else:
        assert 'not_returned' in report and 'missing' in report.lower()
    assert summary['common_format_validation']['status'] == 'not_applicable'


def test_utf8_budgets_keep_omission_labels_for_oversized_native_detail_and_thoughts(tmp_path):
    root, run_id, _ = _task(tmp_path, thoughts='思考🙂'*20000,
                          native={'status': 'failed', 'error': '原生错误'*20000,
                                  'validation': {'passed': False, 'diagnostics': ['诊断'*30000]}},
                          detail='失败原因'*40000)
    output = tmp_path/'compact'
    summary = results.export_task(root, output, run_id,
                                  format_check={'passed': False, 'diagnostics': ['错误'*40000]})
    encoded = (output/'case-001'/'B'/'report.md').read_bytes()
    report = encoded.decode('utf8')
    assert len(encoded) <= 64*1024
    assert summary['reasoning_bytes'] <= 8*1024
    assert summary['reasoning_truncated'] is True
    assert 'omitted' in report.lower()
    excerpt = report.split('<!-- returned-reasoning:start -->\n')[1].split('\n<!-- returned-reasoning:end -->')[0]
    assert len(excerpt.encode('utf8')) <= 8*1024
    assert 'Terminal status: submitted' in report


@pytest.mark.parametrize('status', ['no_output', 'budget_exhausted', 'cancelled', 'runtime_error', 'unsupported'])
def test_non_submitted_terminals_do_not_invoke_ifc_check(tmp_path, status):
    root, run_id, _ = _task(tmp_path, status=status, thoughts=None, detail='actual failure')

    def forbidden_check(path):
        pytest.fail('There is no submitted IFC to validate.')

    summary = results.export_task(root, tmp_path/'compact', run_id, format_check=forbidden_check)
    assert summary['status'] == status
    assert summary['artifact'] is None
    assert summary['native_validation']['status'] == 'not_retained'


@pytest.mark.parametrize('changes, code', [
    ({'status': 'running'}, 'TERMINAL_REQUIRED'),
    ({'activities': ['native-worker']}, 'TERMINAL_STATE_MISMATCH'),
    ({'status': 'no_output'}, 'TERMINAL_ARTIFACT_MISMATCH'),
    ({'run_id': 'another-run'}, 'TERMINAL_STATE_MISMATCH'),
    ({'case_id': 'unsafe:case'}, 'INVALID_RESULT_PATH'),
    ({'arm': 'H'}, 'INVALID_RESULT_PATH'),
])
def test_state_guards_fail_before_writing(tmp_path, changes, code):
    root, run_id, _ = _task(tmp_path)
    _edit_state(root, run_id, changes)
    output = tmp_path/'compact'
    with pytest.raises(ValueError, match=code):
        results.export_task(root, output, run_id)
    assert not output.exists()


def test_inflight_call_or_terminal_event_disagreement_blocks_export(tmp_path):
    root, run_id, _ = _task(tmp_path)
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        db.execute("UPDATE calls SET state='inflight' WHERE run_id=?", (run_id,))
        db.commit()
    with pytest.raises(ValueError, match='TERMINAL_STATE_MISMATCH'):
        results.export_task(root, tmp_path/'inflight', run_id)
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        db.execute("UPDATE calls SET state='completed' WHERE run_id=?", (run_id,))
        db.execute("UPDATE events SET payload=? WHERE run_id=? AND kind='terminal'",
                   (json.dumps({'status': 'no_output', 'artifact': None}), run_id))
        db.commit()
    with pytest.raises(ValueError, match='TERMINAL_STATE_MISMATCH'):
        results.export_task(root, tmp_path/'different-event', run_id)


@pytest.mark.parametrize('kind', ['intermediate', 'outside', 'missing', 'wrong_hash', 'non_ifc'])
def test_only_the_hash_bound_formal_ifc_can_be_exported(tmp_path, kind):
    root, run_id, artifact = _task(tmp_path)
    if kind == 'wrong_hash':
        reference = {'path': str(artifact), 'sha256': '0'*64}
        code = 'FORMAL_ARTIFACT_HASH_MISMATCH'
    elif kind == 'missing':
        artifact.unlink()
        reference = {'path': str(artifact), 'sha256': '0'*64}
        code = 'FORMAL_ARTIFACT_MISSING'
    else:
        path = (root/'workspaces'/run_id/'output'/'intermediate.ifc' if kind == 'intermediate'
                else tmp_path/'outside.ifc' if kind == 'outside' else root/'artifacts'/run_id/'result.txt')
        if not path.exists():
            path.write_bytes(b'not the formal output')
        reference = {'path': str(path), 'sha256': sha256(path)}
        code = 'FORMAL_ARTIFACT_PATH_MISMATCH'
    _edit_state(root, run_id, {'artifact': reference}, terminal=True)
    output = tmp_path/'compact'
    with pytest.raises(ValueError, match=code):
        results.export_task(root, output, run_id)
    assert not output.exists()


def test_no_output_guard_and_unique_case_arm_directory(tmp_path):
    root, run_id, _ = _task(tmp_path/'no-output', status='no_output')
    output = tmp_path/'compact'
    leaf = output/'case-001'/'B'
    leaf.mkdir(parents=True)
    (leaf/'repaired.ifc').write_bytes(b'previous submitted result must not be removed')
    with pytest.raises(ValueError, match='NO_OUTPUT_ARTIFACT_EXISTS'):
        results.export_task(root, output, run_id)
    assert not (leaf/'report.md').exists()
    assert (leaf/'repaired.ifc').read_bytes() == b'previous submitted result must not be removed'
    first_root, first_run, _ = _task(tmp_path/'first')
    output = tmp_path/'unique'
    first = results.export_task(first_root, output, first_run)
    assert results.export_task(first_root, output, first_run) == first
    other_root, other_run, _ = _task(tmp_path/'other', run_id='another-attempt-B')
    with pytest.raises(ValueError, match='RESULT_TASK_EXISTS'):
        results.export_task(other_root, output, other_run)
    # Identical run IDs in distinct ledgers are still distinct attempts.
    repeated_root, repeated_run, _ = _task(tmp_path/'repeated')
    with pytest.raises(ValueError, match='RESULT_TASK_EXISTS'):
        results.export_task(repeated_root, output, repeated_run)


def test_missing_ledger_and_common_check_failure_are_explicit(tmp_path):
    with pytest.raises(ValueError, match='RESULT_LEDGER_MISSING'):
        results.export_task(tmp_path/'absent', tmp_path/'out', 'case-001-B')
    assert not (tmp_path/'absent').exists()
    root, run_id, _ = _task(tmp_path, thoughts=None)

    def failed_check(path):
        raise RuntimeError('offline validator failure')

    summary = results.export_task(root, tmp_path/'compact', run_id, format_check=failed_check)
    assert summary['common_format_validation']['status'] == 'error'
    assert summary['common_format_validation']['passed'] is None
    report = (tmp_path/'compact'/'case-001'/'B'/'report.md').read_text(encoding='utf8')
    assert 'offline validator failure' in report
    assert summary['status'] == 'submitted'


def test_missing_native_stage_pending_check_and_redacted_thoughts_are_explicit(tmp_path):
    root, run_id, _ = _task(tmp_path, thoughts=None)
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        db.execute('UPDATE calls SET response=? WHERE run_id=?', (json.dumps({'body': {'content': [
            {'type': 'redacted_thinking', 'data': 'redacted opaque data'},
            {'type': 'text', 'text': 'ordinary final answer'}]}}), run_id))
        db.commit()
    summary = results.export_task(root, tmp_path/'compact', run_id)
    report = (tmp_path/'compact'/'case-001'/'B'/'report.md').read_text(encoding='utf8')
    assert summary['common_format_validation']['status'] == 'pending'
    assert summary['reasoning_status'] == 'not_returned'
    assert '"stage": "not_retained"' in report
    assert '"reason_code": "not_retained"' in report
    assert 'ordinary final answer' not in report
    assert 'redacted opaque data' not in report


def test_common_check_cannot_replace_bound_ifc_and_leaf_cannot_gain_extra_files(tmp_path):
    root, run_id, artifact = _task(tmp_path)
    output = tmp_path/'compact'
    leaf = output/'case-001'/'B'
    leaf.mkdir(parents=True)
    (leaf/'runtime.log').write_text('Unrelated existing file.', encoding='utf8')
    with pytest.raises(ValueError, match='RESULT_DIRECTORY_NOT_COMPACT'):
        results.export_task(root, output, run_id)
    assert not (leaf/'report.md').exists()
    output = tmp_path/'mutation-guard'

    def mutating_check(path):
        path.write_bytes(b'different fixture IFC')
        return {'passed': True}

    with pytest.raises(ValueError, match='FORMAL_ARTIFACT_HASH_MISMATCH'):
        results.export_task(root, output, run_id, format_check=mutating_check)
    assert not output.exists()
    assert artifact.read_bytes() == b'different fixture IFC'
