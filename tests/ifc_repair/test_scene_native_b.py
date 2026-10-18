"""New scene method across actual SDK/HTTP and isolated B task bindings."""
import json
import os
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

import pytest

from scripts.ifc_repair.repair_comparison.isolated_b import worker_execute
from text2ifc_ifc_repair.scene_grounding import SCENE_GROUNDING_VERSION
from tests.ifc_repair.repair_comparison.test_isolated_b import workspace
from tests.ifc_repair.test_scene_repair_api import SceneDemoProvider


@contextmanager
def scene_http(kind):
    provider = SceneDemoProvider(kind)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            packet = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(packet)
            prompt = packet['messages'][0]['content']
            result = provider.generate_candidate(prompt=prompt, schema=None,
                state={'stage': 'ifc_repair_scene_grounding' if '## Current public scene' in prompt else 'ifc_repair_changeset'})
            data = json.dumps({'id': 'offline-scene-'+str(len(requests)), 'model': packet['model'],
                'object': 'chat.completion', 'created': 0,
                'choices': [{'index': 0, 'finish_reason': 'stop', 'message': {'role': 'assistant',
                    'content': result.text, 'reasoning_content': 'Offline deterministic fixture.'}}],
                'usage': {'prompt_tokens': 11, 'completion_tokens': 7, 'total_tokens': 18}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *_):
            pass

    previous = os.environ.get('NO_PROXY')
    os.environ['NO_PROXY'] = '127.0.0.1,localhost'
    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/v1', requests
    finally:
        server.shutdown(); server.server_close(); thread.join(5)
        if previous is None:
            os.environ.pop('NO_PROXY',None)
        else:
            os.environ['NO_PROXY'] = previous


def test_scene_native_worker_uses_default_sdk_and_rejects_method_switch(tmp_path):
    work = workspace(tmp_path)
    with scene_http('door') as (url, calls):
        payload = {'action': 'start', 'run_id': 'scene-native-b', 'base_url': url,
                   'scene_grounding_version': SCENE_GROUNDING_VERSION}
        result = worker_execute(payload, workspace=work, state_root=tmp_path/'state')
        assert result['result']['successful_artifact_publishable'], result
        assert len(calls) == 4  # 2 public queries, grounded intent, bound ChangeSet
        assert all('reasoning_content' not in p['messages'][0]['content'] for p in calls)
        assert all(p['thinking']=={'type':'enabled'} for p in calls)
        binding = json.loads((tmp_path/'state/task.json').read_text())
        assert binding['scene_grounding_version']==SCENE_GROUNDING_VERSION
        with pytest.raises(ValueError, match='B_TASK_BINDING_MISMATCH'):
            worker_execute({**payload, 'action': 'read', 'scene_grounding_version': None},
                           workspace=work, state_root=tmp_path/'state')
        assert worker_execute({**payload, 'action':'read'}, workspace=work,
                              state_root=tmp_path/'state')['result']==result['result']
        assert len(calls)==4


def test_unknown_saved_scene_method_cannot_fall_back_to_text_only():
    from text2ifc_ifc_repair.api import _context_scene_mode
    from text2ifc_ifc_repair.run_models import RunStoreError
    with pytest.raises(RunStoreError,match='no implicit migration'):
        _context_scene_mode({'scene_grounding_version':'text2ifc/ifc-scene-grounding/future'})
    assert not _context_scene_mode({})
