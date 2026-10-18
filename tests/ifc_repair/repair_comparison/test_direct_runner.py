"""Same A/C replay through actual tools, persisted question and one submission."""
import importlib
import json
import os
from pathlib import Path
import sys
import time

import pytest

from scripts.ifc_repair.repair_comparison.ledger import Ledger


def runtime():
    name = 'scripts.ifc_repair.repair_comparison.direct_runner'
    assert (Path(__file__).resolve().parents[3] / name.replace('.', '/')).with_suffix('.py').exists(), 'Direct executor is not implemented'
    return importlib.import_module(name)


def test_direct_executor_entrypoint():
    assert runtime().DirectRunner


def make(tmp_path, arm='A'):
    public = tmp_path / 'public'
    public.mkdir(exist_ok=True)
    (public / 'model.ifc').write_text('ISO-10303-21;\n/* damaged */\nEND-ISO-10303-21;', encoding='utf-8')
    (public / 'request.txt').write_text('请修复二层的门。', encoding='utf-8')
    api = runtime()
    budget = {'tokens': 1000, 'calls': 20, 'active_seconds': 60, 'tool_seconds': 5, 'extensions': []}
    runner = api.DirectRunner.create(public, tmp_path / 'experiment', case_id='case-001', arm=arm, budget=budget)
    return runner, public


def response(*calls, content='', usage=None):
    return {'content': content, 'tool_calls': list(calls), 'usage': usage or {'input_tokens': 2, 'output_tokens': 3}, 'reasoning_status': 'not_returned'}


def tool(name, **arguments):
    return {'name': name, 'arguments': arguments}


@pytest.mark.parametrize('arm', ['A', 'C'])
def test_direct_edit_question_restart_and_unique_explicit_submission(tmp_path, arm):
    runner, public = make(tmp_path, arm)
    api = runtime()
    replies = [response(tool('ask_user', question='哪一侧？')),
               response(tool('replace_text', path='model.ifc', old='damaged', new='edited')),
               response(tool('submit', path='model.ifc'))]
    first = runner.run(api.ReplayProvider(replies), reservation=20)
    assert first['status'] == 'awaiting_user'
    assert first['usage']['known_total_tokens'] == 5
    question = first['question']['question_id']
    runner.ledger.answer(runner.run_id, question_id=question, text='靠走廊这一侧。', event_id='human-1')
    restarted = api.DirectRunner(runner.root, runner.run_id)
    result = restarted.run(api.ReplayProvider(replies), reservation=20)
    assert result['status'] == 'submitted'
    assert result['usage']['known_total_tokens'] == 15
    assert 'edited' in Path(result['artifact']['path']).read_text(encoding='utf-8')
    assert 'damaged' in (public / 'model.ifc').read_text(encoding='utf-8')
    assert not (restarted.workspace / 'private').exists()
    assert len([e for e in restarted.ledger.events(restarted.run_id) if e['kind'] == 'terminal']) == 1
    with pytest.raises(ValueError, match='TERMINAL'):
        restarted.submit('model.ifc')


def test_silent_stop_does_not_publish_unchanged_working_copy(tmp_path):
    runner, _ = make(tmp_path)
    result = runner.run(runtime().ReplayProvider([response(content='done')]), reservation=20)
    assert result['status'] == 'no_output' and result['artifact'] is None


def test_real_script_tool_and_paging_are_neutral(tmp_path):
    runner, _ = make(tmp_path)
    script = "from pathlib import Path\np=Path('model.ifc')\np.write_text(p.read_text().replace('damaged','script-edit'))\nprint('script complete')\n"
    replies = [response(tool('write_file', path='work/edit.py', text=script)),
               response(tool('execute', argv=[sys.executable, 'work/edit.py'])),
               response(tool('read_file', path='model.ifc', offset=0, limit=5)),
               response(tool('submit', path='model.ifc'))]
    result = runner.run(runtime().ReplayProvider(replies), reservation=20)
    assert result['status'] == 'submitted'
    assert 'script-edit' in Path(result['artifact']['path']).read_text(encoding='utf-8')
    results = [e['payload']['result'] for e in runner.ledger.events(runner.run_id) if e['kind'] == 'tool_result']
    assert results[1]['exit_code'] == 0 and results[1]['quiescent'] is True
    assert results[2]['truncated'] is True


@pytest.mark.parametrize('path', ['../control.sqlite', 'C:/Windows/win.ini', '../public/model.ifc', 'work/../../secret', 'model.ifc:secret'])
def test_file_tools_reject_escape_and_alternate_streams(tmp_path, path):
    runner, _ = make(tmp_path)
    with pytest.raises(ValueError):
        runner.tools.read_file(path)


def test_partial_tool_batch_pauses_without_dropping_remaining_calls(tmp_path):
    runner, _ = make(tmp_path)
    replies = [response(tool('ask_user', question='哪侧？'), tool('write_file', path='work/after.txt', text='continued')), response(tool('submit', path='model.ifc'))]
    first = runner.run(runtime().ReplayProvider(replies), reservation=20)
    assert not (runner.workspace / 'work/after.txt').exists()
    runner.ledger.answer(runner.run_id, question_id=first['question']['question_id'], text='左侧', event_id='answer')
    result = runtime().DirectRunner(runner.root, runner.run_id).run(runtime().ReplayProvider(replies), reservation=20)
    assert result['status'] == 'submitted'
    assert (runner.workspace / 'work/after.txt').read_text(encoding='utf-8') == 'continued'


def test_unresolved_request_cannot_be_redispatched_after_crash(tmp_path):
    runner, _ = make(tmp_path)
    runner.ledger.start(runner.run_id)
    runner.ledger.reserve(runner.run_id, 'request-0', 20)
    with pytest.raises(ValueError, match='RECOVERY_REQUIRED'):
        runner.run(runtime().ReplayProvider([response()]), reservation=20)
    assert len(runner.ledger.calls(runner.run_id)) == 1


def test_malformed_reply_and_budget_exhaustion_keep_all_attempts(tmp_path):
    runner, _ = make(tmp_path)
    replies = [{'tool_calls': 'truncated', 'usage': None}, response(tool('submit', path='model.ifc'))]
    result = runner.run(runtime().ReplayProvider(replies), reservation=600)
    assert result['status'] == 'budget_exhausted'
    assert result['usage']['coverage'] == 'unavailable'
    assert result['artifact'] is None


@pytest.mark.skipif(os.name != 'nt', reason='Windows job cleanup for this development host')
def test_execute_timeout_stops_child_before_human_wait(tmp_path):
    runner, _ = make(tmp_path)
    child = "import time; from pathlib import Path; time.sleep(2); Path('leaked.txt').write_text('bad')"
    parent = f"import subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c',{child!r}])\ntime.sleep(10)"
    runner.tools.write_file('work/parent.py', parent)
    result = runner.tools.execute([sys.executable, 'work/parent.py'], timeout_s=.4)
    assert result['timed_out'] is True and result['quiescent'] is True
    time.sleep(2.2)
    assert not (runner.workspace / 'leaked.txt').exists()


def test_only_replay_provider_is_allowed_in_offline_entry(tmp_path):
    runner, _ = make(tmp_path)
    with pytest.raises(ValueError, match='OFFLINE_REPLAY_ONLY'):
        runner.run(object(), reservation=20)


def test_time_limit_stops_pending_file_edits(tmp_path):
    runner, _ = make(tmp_path)
    now = [0.0]
    runner.ledger.clock = lambda: now[0]
    class SlowReply(runtime().ReplayProvider):
        def complete(self, *args, **kwargs):
            now[0] = 61.0
            return super().complete(*args, **kwargs)
    result = runner.run(SlowReply([response(tool('write_file', path='work/late.txt', text='late'))]), reservation=20)
    assert result['status'] == 'budget_exhausted'
    assert not (runner.workspace / 'work/late.txt').exists()


def test_question_survives_crash_before_tool_result(tmp_path, monkeypatch):
    runner, _ = make(tmp_path)
    original = runner.ledger.record
    def crash(run_id, kind, payload, **kwargs):
        if kind == 'tool_result':
            raise RuntimeError('crash before result event')
        return original(run_id, kind, payload, **kwargs)
    monkeypatch.setattr(runner.ledger, 'record', crash)
    replies = [response(tool('ask_user', question='哪层？')), response(tool('submit', path='model.ifc'))]
    with pytest.raises(RuntimeError, match='crash'):
        runner.run(runtime().ReplayProvider(replies), reservation=20)
    restarted = runtime().DirectRunner(runner.root, runner.run_id)
    state = restarted.ledger.snapshot(runner.run_id)
    assert state['status'] == 'awaiting_user'
    restarted.ledger.answer(runner.run_id, question_id=state['question']['question_id'], text='二层', event_id='answer')
    assert restarted.run(runtime().ReplayProvider(replies), reservation=20)['status'] == 'submitted'


def test_two_resumers_cannot_execute_one_settled_tool_twice(tmp_path, monkeypatch):
    runner, _ = make(tmp_path)
    runner.ledger.start(runner.run_id)
    runner.ledger.reserve(runner.run_id, 'request-0', 20)
    runner.ledger.settle(runner.run_id, 'request-0', usage={'input_tokens': 2, 'output_tokens': 3},
                        response=response(tool('write_file', path='work/once.txt', text='once')))
    other = runtime().DirectRunner(runner.root, runner.run_id)
    stale = other.ledger.events(other.run_id)
    monkeypatch.setattr(other.ledger, 'events', lambda _: stale)
    runner._apply_pending()
    calls = []
    monkeypatch.setattr(other.tools, 'write_file', lambda **kwargs: calls.append(kwargs))
    with pytest.raises(ValueError, match='RECOVERY_REQUIRED'):
        other._apply_pending()
    assert calls == []
