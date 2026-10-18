"""Keyless, deterministic Messages fixture; never a production/model proxy.

Run in its own internally networked container. Do not mount this test answerer
or its records in the model container. Every response and usage value is fake.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time

ROOT = Path('/evidence')
LOCK = threading.Lock()
COUNTS = {}
QUESTION_DONE = set()


def record(kind, **value):
    with LOCK:
        with (ROOT / 'wire.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'kind': kind, 'at': time.time(), **value}) + '\n')


def chunks(text=None, tool=None, usage=True):
    message = {'id': 'offline-fixture', 'model': 'offline-fixture'}
    if usage:
        message['usage'] = {'input_tokens': 11, 'output_tokens': 0}
    else:
        message['usage'] = {}  # Missing counts, not a malformed missing object.
    events = [{'type': 'message_start', 'message': message}]
    events.extend([
        {'type': 'content_block_start', 'index': 0,
         'content_block': {'type': 'thinking', 'thinking': ''}},
        {'type': 'content_block_delta', 'index': 0,
         'delta': {'type': 'thinking_delta', 'thinking': 'OFFLINE_REASONING_FIXTURE'}},
        {'type': 'content_block_stop', 'index': 0},
    ])
    if tool:
        name, args, call_id = tool
        block = {'type': 'tool_use', 'id': call_id, 'name': name, 'input': {}}
        delta = {'type': 'input_json_delta', 'partial_json': json.dumps(args)}
    else:
        block = {'type': 'text', 'text': ''}
        delta = {'type': 'text_delta', 'text': text}
    events.extend([
        {'type': 'content_block_start', 'index': 1, 'content_block': block},
        {'type': 'content_block_delta', 'index': 1, 'delta': delta},
        {'type': 'content_block_stop', 'index': 1},
        {'type': 'message_delta', 'delta': {'stop_reason': 'tool_use' if tool else 'end_turn'},
         **({'usage': {'output_tokens': 7}} if usage else {})},
        {'type': 'message_stop'},
    ])
    return events


def completion(session, step, body):
    if session == 'native-hang':
        # Keep a real child writing until the external container controller stops it.
        return chunks(tool=('bash', {
            'command': "python -u -c \"import time; from pathlib import Path; p=Path('/workspace/heartbeat'); exec('while True:\\n p.write_text(str(time.time()))\\n time.sleep(.2)')\"",
            'description': 'Offline process-stop fixture',
            'timeoutMs': 500,
        }, 'hanging-shell')) if step == 0 else chunks(text='BACKGROUND_JOB_RUNNING')
    if session == 'native-missing-usage':
        return chunks(text='MISSING_USAGE_OK', usage=False)
    if session == 'native-retry' and step == 0:
        return None  # One real HTTP failure; the native retry policy owns retrying.
    if session == 'native-retry':
        return chunks(text='NATIVE_RETRY_OK')
    if session == 'native-truncated':
        events = chunks(text='TRUNCATED_RECOVERED')
        return events[:3] if step == 0 else events
    if session == 'native-compaction':
        events = chunks(text='NATIVE_COMPACTION_TURN_OK')
        if step == 0:
            events[0]['message']['usage']['input_tokens'] = 100000
        return events
    if session == 'native-subagent':
        if step == 0:
            return chunks(tool=('subagent', {'description': 'Offline child trace fixture',
                'prompt': 'OFFLINE_CHILD_TASK: return the fixture response.',
                'run_in_background': False}, 'native-child'))
        assert 'OFFLINE_CHILD_OK' in json.dumps(body['messages'])
        return chunks(text='NATIVE_SUBAGENT_OK')
    if 'OFFLINE_CHILD_TASK' in json.dumps(body.get('messages', [])):
        return chunks(text='OFFLINE_CHILD_OK')
    assert session == 'native-core', session
    calls = [
        ('read', {'file_path': '/workspace/input.txt'}, 'read-input'),
        ('edit', {'file_path': '/workspace/input.txt', 'old_string': 'original', 'new_string': 'changed'}, 'edit-input'),
        ('bash', {'command': "python -c \"import ifcopenshell; from pathlib import Path; assert Path('/workspace/input.txt').read_text() == 'changed'; print('CORE_SHELL_OK', ifcopenshell.version)\"",
                  'description': 'Offline real shell and IfcOpenShell check'}, 'verify-shell'),
        ('ask_user_question', {'questions': [{'id': 'location', 'question': 'Which opening should I use?'}]}, 'ask-location'),
    ]
    previous = json.dumps(body['messages'])
    if step == 1:
        assert 'original' in previous and 'read-input' in previous
    elif step == 3:
        assert 'CORE_SHELL_OK' in previous
    elif step == 4:
        assert session in QUESTION_DONE
        assert 'The western opening.' in previous and 'ask-location' in previous
    if step < len(calls):
        names = {tool.get('name') for tool in body.get('tools', [])}
        assert calls[step][0] in names, names
        return chunks(tool=calls[step])
    if step == 4:
        return chunks(text='DSH_NATIVE_CORE_OK')
    assert 'The western opening.' in previous and 'DSH_NATIVE_CORE_OK' in previous
    return chunks(text='DSH_SAME_SESSION_CONTINUED')


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        try:
            if self.path == '/questions':
                session = body['sessionId']
                assert session == 'native-core'
                record('question', body=body)
                count = COUNTS[session]
                time.sleep(2)  # Deliberate fake-human wait, never a real approval.
                assert COUNTS[session] == count, 'model called again while waiting'
                answer = {'requestId': body['requestId'], 'answers': [
                    {'id': 'location', 'selected': [], 'custom': 'The western opening.'}]}
                QUESTION_DONE.add(session)
                record('fake_human_answer', body=answer)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(answer).encode())
                return
            assert self.path == '/v1/messages', self.path
            session = self.headers.get('x-deepseek-harness-session-id')
            with LOCK:
                step = COUNTS.get(session, 0)
                COUNTS[session] = step + 1
            record('request', session=session, step=step, body=body,
                   compact=self.headers.get('x-deepseek-harness-compact'))
            events = (chunks(text='Offline fixture context was summarized; continue the fixture.')
                      if self.headers.get('x-deepseek-harness-compact') == '1'
                      else completion(session, step, body))
            if events is None:
                record('http_failure', session=session, step=step, status=503)
                self.send_response(503)
                self.end_headers()
                self.wfile.write(b'{"error":{"type":"overloaded_error","message":"offline retry fixture"}}')
                return
            record('response', session=session, step=step, events=events,
                   usage_status=('unavailable' if session == 'native-missing-usage' else
                                 'partial_fake' if events[-1]['type'] != 'message_stop' else 'reported_fake'))
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            for event in events:
                self.wfile.write(f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode())
            self.wfile.flush()
        except Exception as error:
            record('fixture_error', message=repr(error))
            self.send_error(400, str(error))

    def log_message(self, *_args):
        pass


if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    ThreadingHTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
