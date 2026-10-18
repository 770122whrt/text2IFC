"""Runs the installed official DSH SDK; contains no fake model or answer card."""
from dataclasses import asdict
import importlib.metadata
import json
import os
from pathlib import Path
import sys

from deepseek_harness import DeepSeekHarness


def main():
    case = sys.argv[1]
    state = Path('/state')
    assert os.getuid() != 0
    assert not Path('/var/run/docker.sock').exists()
    assert not Path('/host-canary').exists()
    assert not Path('/other-arm').exists()
    assert not os.access('/opt/venv', os.W_OK)
    Path('/workspace/input.txt').write_text('original')
    patch = state / 'offline.patch.json'
    patches = [
        {'id': 'session-persistence-jsonl', 'config': {'root': '/state/sessions', 'compression': 'none'}},
        {'id': 'session-telemetry-otel', 'disabled': True},
        {'insert': [
            {'id': 'repair-official-ask-user', 'name': '@deepseek-ai/dsh-tool-ask-user'},
            {'id': 'repair-question-bridge', 'name': 'file:///opt/probe/question-bridge.mjs',
             'config': {'endpoint': 'http://dsh-fixture:8000/questions'}},
        ]},
    ]
    if case == 'compaction':
        # Force pressure cheaply for this component test; formal runs retain
        # their separately frozen policy. All native tools remain enabled.
        patches.append({'id': 'compaction-basic', 'config': {
            'thresholdRatio': 0.01, 'headroomTokens': 0,
            'retainTokens': 64, 'maxTokens': 512}})
    patch.write_text(json.dumps(patches))
    versions = {name: importlib.metadata.version(name) for name in (
        'deepseek-harness-sdk', 'deepseek-harness-runtime-bin', 'ifcopenshell')}
    (state / 'versions.json').write_text(json.dumps({'python': sys.version, **versions}, indent=2))
    harness = DeepSeekHarness(
        provider='deepseek-official', model='offline-fixture', profile='sdk',
        cwd='/workspace', dsh_home='/state/home', patches=(str(patch),),
        env={'DSH_PERMISSION_MODE': 'danger-full-access', 'DSH_TELEMETRY_DISABLED': '1'},
        api_key='offline-not-a-secret', base_url='http://dsh-fixture:8000',
        request_timeout_seconds=90,
    )
    def notification(value):
        with (state / 'notifications.jsonl').open('a') as stream:
            stream.write(json.dumps(asdict(value)) + '\n')
    try:
        with harness:
            prompt = 'Run the offline runtime fixture.'
            if case == 'compaction':
                prompt += ' fixture-context' * 10000
            result = harness.run(prompt, session_id=f'native-{case}', on_notification=notification)
            (state / 'result.json').write_text(json.dumps(asdict(result), indent=2))
            if case == 'core':
                assert result.final_response == 'DSH_NATIVE_CORE_OK', result.final_response
                assert Path('/workspace/input.txt').read_text() == 'changed'
                continued = harness.run('Continue this same session.', session_id=result.session_id, on_notification=notification)
                assert continued.final_response == 'DSH_SAME_SESSION_CONTINUED'
                (state / 'continued.json').write_text(json.dumps(asdict(continued), indent=2))
            elif case == 'retry':
                assert result.final_response == 'NATIVE_RETRY_OK'
            elif case == 'missing-usage':
                assert result.final_response == 'MISSING_USAGE_OK'
            elif case == 'subagent':
                assert result.final_response == 'NATIVE_SUBAGENT_OK'
                assert any(event.payload.get('sessionId') != result.session_id
                           for event in result.notifications if event.method == 'session.event')
            elif case == 'truncated':
                # Native policy terminates after a partially exposed stream.
                # Do not require another model call or turn that into a success.
                assert result.finish_reason == 'error' and not result.final_response
                assert any(event['type'] == 'assistant/attempt' for event in result.events)
                terminal = next(event for event in reversed(result.events) if event['type'] == 'turn/end')
                assert terminal['data']['reason']['error']['code'] == 'STREAM_CLOSED'
            elif case == 'compaction':
                continued = harness.run('Continue the offline fixture.', session_id=result.session_id,
                                        on_notification=notification)
                (state / 'continued.json').write_text(json.dumps(asdict(continued), indent=2))
                assert any(event['type'] == 'compaction/summary' for event in result.events + continued.events)
            elif case == 'hang':
                # Keep the runtime (including its native background jobs) alive.
                import time
                time.sleep(90)
        (state / 'passed.json').write_text(json.dumps({'case': case, 'evidence': 'real_runtime_fake_model'}))
    except BaseException:
        (state / 'runtime-diagnostics.txt').write_text(harness.client._runtime_diagnostics())
        raise


if __name__ == '__main__':
    main()
