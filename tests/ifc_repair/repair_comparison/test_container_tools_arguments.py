"""Malformed model argv is a tool error before any container is created."""
import json

import pytest

from scripts.ifc_repair.repair_comparison import container_tools
from scripts.ifc_repair.repair_comparison.container_tools import ContainerTools
from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner
from scripts.ifc_repair.repair_comparison.isolated_direct import ChatExecutor


INVALID_ARGV = [None, 'python -c pass', [], [1], ['python', None], ['python', 'a\0b']]


@pytest.mark.parametrize('argv', INVALID_ARGV)
def test_invalid_argv_rejected_before_docker_or_activity_state(tmp_path, monkeypatch, argv):
    calls = []

    def unexpected_docker(*args, **kwargs):
        calls.append(args)
        pytest.fail('Malformed argv reached Docker')

    monkeypatch.setattr(container_tools, 'docker', unexpected_docker)
    tools = ContainerTools(tmp_path, tool_seconds=5)
    with pytest.raises(ValueError, match='INVALID_ARGV'):
        tools.execute(argv)
    assert not calls
    assert tools.quiescent is True
    assert not tools.records


def fake_docker(monkeypatch, *, start_error=None):
    calls = []

    def invoke(*args, **kwargs):
        calls.append((args, kwargs))
        if args[0] == 'start':
            if start_error:
                raise RuntimeError(start_error)
            return json.dumps({'exit_code': 0, 'stdout': 'ok', 'stderr': '', 'timed_out': False})
        if args[0] == 'inspect':
            return json.dumps([{'State': {'Running': False, 'Pid': 0}, 'Mounts': [],
                                'HostConfig': {'NetworkMode': 'none'}, 'Image': 'fake-image'}])
        return 'fake-container' if args[0] == 'create' else ''

    monkeypatch.setattr(container_tools, 'docker', invoke)
    return calls


@pytest.mark.parametrize('argv', [
    ['python', '-c', 'print("ok")'],
    ['sh', '-c', 'printf "%s" "$HOME"; true', ''],
])
def test_valid_argv_is_forwarded_exactly_with_existing_timeout_and_isolation(tmp_path, monkeypatch, argv):
    calls = fake_docker(monkeypatch)
    tools = ContainerTools(tmp_path, tool_seconds=5)
    result = tools.execute(argv, timeout_s=90)

    start = next(kwargs for args, kwargs in calls if args[0] == 'start')
    assert json.loads(start['input']) == {'argv': argv, 'timeout_s': 5}
    assert [args[0] for args, _ in calls] == ['create', 'start', 'stop', 'inspect', 'rm']
    create = calls[0][0]
    assert create[create.index('--network') + 1] == 'none'
    assert '--read-only' in create
    assert result['quiescent'] is True and result['exit_code'] == 0
    assert tools.quiescent is True


@pytest.mark.parametrize('timeout', [False, 0, float('nan'), '1'])
def test_invalid_timeout_still_fails_before_docker(tmp_path, monkeypatch, timeout):
    monkeypatch.setattr(container_tools, 'docker', lambda *a, **kw: pytest.fail('Invalid timeout reached Docker'))
    tools = ContainerTools(tmp_path, tool_seconds=5)
    with pytest.raises(ValueError, match='INVALID_TOOL_TIMEOUT'):
        tools.execute(['python', '-c', 'pass'], timeout_s=timeout)
    assert tools.quiescent is True


def engine_with_tools(tmp_path, argv, *, trailing_list=True):
    public = tmp_path / 'public'
    public.mkdir()
    (public / 'model.ifc').write_text('synthetic source fixture', encoding='utf-8')
    (public / 'request.txt').write_text('Synthetic executor argument test.', encoding='utf-8')
    raw = DirectRunner.create(
        public, tmp_path / 'runs', case_id='argv-case', arm='G',
        budget={'tokens': 1000, 'calls': 10, 'active_seconds': 100, 'tool_seconds': 5, 'extensions': []},
        runtime_metadata={'stage': 'repair-comparison-scalable-live'},
    )
    engine = ChatExecutor(raw.root, raw.run_id, gateway_url='https://offline.invalid/v1',
                          model='fake-model', evidence_class='deterministic_fake', isolated=True)
    engine.ledger.start(engine.run_id)
    calls = [{'id': 'bad-argv', 'type': 'function', 'function': {
        'name': 'execute', 'arguments': json.dumps({'argv': argv}),
    }}]
    if trailing_list:
        calls.append({'id': 'next-tool', 'type': 'function', 'function': {
            'name': 'list_files', 'arguments': '{}',
        }})
    engine.ledger.record(engine.run_id, 'chat_assistant', {'message': {
        'role': 'assistant', 'content': None, 'tool_calls': calls,
    }})
    return engine


@pytest.mark.parametrize('argv', ['python -c pass', ['python', None]])
def test_invalid_argv_is_persisted_tool_feedback_and_next_tool_can_run(tmp_path, monkeypatch, argv):
    calls = fake_docker(monkeypatch, start_error='DOCKER_START_FAILED: ValueError INVALID_ARGV')
    engine = engine_with_tools(tmp_path, argv)

    state = engine.pending()

    assert not calls
    assert state['status'] == 'running' and not state['activities']
    assert state['artifact'] is None
    assert engine.tools.quiescent is True
    tool_messages = [message for message in engine.messages() if message['role'] == 'tool']
    assert [message['tool_call_id'] for message in tool_messages] == ['bad-argv', 'next-tool']
    assert json.loads(tool_messages[0]['content']) == {'error': 'ValueError', 'detail': 'INVALID_ARGV'}
    assert 'files' in json.loads(tool_messages[1]['content'])
    assert len([event for event in engine.ledger.events(engine.run_id) if event['kind'] == 'chat_tool_result']) == 2
    engine.pending()
    assert len([event for event in engine.ledger.events(engine.run_id) if event['kind'] == 'chat_tool_result']) == 2


def test_actual_docker_fault_is_not_downgraded_to_model_argument_feedback(tmp_path, monkeypatch):
    calls = fake_docker(monkeypatch, start_error='DOCKER_START_FAILED: daemon unavailable')
    engine = engine_with_tools(tmp_path, ['python', '-c', 'pass'], trailing_list=False)

    with pytest.raises(RuntimeError, match='DOCKER_START_FAILED: daemon unavailable'):
        engine.pending()

    assert any(args[0] == 'start' for args, _ in calls)
    assert engine.tools.quiescent is True
    assert not engine.ledger.snapshot(engine.run_id)['activities']
    assert not [event for event in engine.ledger.events(engine.run_id) if event['kind'] == 'chat_tool_result']
