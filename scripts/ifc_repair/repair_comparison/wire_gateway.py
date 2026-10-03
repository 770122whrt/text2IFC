"""Task-bound HTTP forwarding/accounting, without model-loop substitutions."""
from __future__ import annotations

from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
import uuid

import httpx

from .contracts import write_json


def wire_usage(raw: bytes, content_type: str, protocol: str):
    """Retain actual presence; native zero defaults do not create usage."""
    usage, complete, payload, _ = _wire_usage(raw, content_type, protocol)
    return usage, complete, payload


def _wire_usage(raw: bytes, content_type: str, protocol: str):
    if 'text/event-stream' not in content_type:
        try:
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            return None, False, None, False
        complete = isinstance(payload, dict)
        return payload.get('usage') if complete else None, complete, payload, complete
    usage, complete, final_output_seen = {}, False, False
    for line in raw.decode('utf8', errors='replace').splitlines():
        if not line.startswith('data:'):
            continue
        data = line[5:].strip()
        if data == '[DONE]':
            if protocol == 'chat':
                complete = True
            continue
        try:
            value = json.loads(data)
        except ValueError:
            continue
        if not isinstance(value,dict):continue
        if protocol == 'messages' and value.get('type') == 'message_stop':
            complete = True
        if value.get('type') == 'message_start':
            source = value.get('message', {}).get('usage')
        else:
            source = value.get('usage')
        if isinstance(source, dict):
            usage.update(source)
            if value.get('type') == 'message_delta' and 'output_tokens' in source:
                final_output_seen = True
    usage_complete = complete and (protocol != 'messages' or final_output_seen)
    return usage or None, complete, None, usage_complete


@dataclass(repr=False)
class Route:
    run_id: str
    token: str
    model: str
    api_key: str
    endpoints: dict
    evidence_class: str
    max_output_tokens: int
    question_events: dict = field(default_factory=dict)
    quiescent: object = None


class WireGateway:
    def __init__(self, ledger, root: Path, *, transport=None, port=0, timeout_seconds=1800, control_token=None):
        self.ledger, self.root = ledger, Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.routes = {}
        self.transport, self.timeout_seconds = transport, timeout_seconds
        self.control_token = control_token
        owner = self
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'
            def do_POST(self):
                owner.handle(self)
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        self.server.daemon_threads = True
        self.url = f'http://127.0.0.1:{self.server.server_address[1]}'
        self.thread = None

    def __enter__(self):
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        if self.thread:
            self.thread.join(timeout=5)

    def register(self, run_id, *, model, api_key, endpoints, evidence_class, max_output_tokens=65536, token=None, quiescent=None):
        token = token or uuid.uuid4().hex
        if token in self.routes:
            raise ValueError('ROUTE_ALREADY_REGISTERED')
        self.routes[token] = Route(run_id, token, model, api_key, endpoints, evidence_class, max_output_tokens, quiescent=quiescent)
        return token

    @staticmethod
    def reply(handler, status, body):
        raw = json.dumps(body, ensure_ascii=False).encode('utf8')
        handler.send_response(status)
        handler.send_header('Content-Type', 'application/json')
        handler.send_header('Content-Length', str(len(raw)))
        handler.end_headers()
        handler.wfile.write(raw)

    def handle(self, handler):
        # This endpoint is never offered by the container relay. It accepts a
        # separately held controller token, not the model task route token.
        if self.control_token and handler.path == '/control/'+self.control_token+'/answer':
            try:
                value=json.loads(handler.rfile.read(int(handler.headers['Content-Length'])))
                self.answer(value['token'],value['question_id'],answers=value['answers'],
                            text=value['text'],event_id=value['event_id'])
                return self.reply(handler,200,{'ok':True})
            except (ValueError,KeyError,TypeError) as error:
                return self.reply(handler,409,{'error':str(error)})
        parts = handler.path.strip('/').split('/', 1)
        route = self.routes.get(parts[0]) if len(parts) == 2 else None
        if route is None:
            return self.reply(handler, 404, {'error':'unoffered route'})
        path = parts[1]
        protocol = {'v1/chat/completions':'chat', 'v1/messages':'messages'}.get(path)
        if path != 'questions' and protocol not in route.endpoints:
            return self.reply(handler, 404, {'error':'unoffered endpoint'})
        try:
            length = int(handler.headers.get('Content-Length', '0'))
            if not 0 < length <= 64 * 1024 * 1024:
                raise ValueError('INVALID_REQUEST_SIZE')
            raw_request = handler.rfile.read(length)
            body = json.loads(raw_request)
            if not isinstance(body, dict):
                raise ValueError('OBJECT_REQUIRED')
            if path == 'questions':
                return self.question(handler, route, body)
            if body.get('model') != route.model:
                raise ValueError('MODEL_NOT_OFFERED')
            cap = body.get('max_tokens', body.get('max_completion_tokens'))
            if type(cap) is not int or not 0 < cap <= route.max_output_tokens:
                raise ValueError('OUTPUT_LIMIT_NOT_OFFERED')
            if self.ledger.snapshot(route.run_id)['status'] != 'running':
                raise ValueError('TASK_NOT_ACTIVE')
            request_id = 'wire-' + uuid.uuid4().hex
            # Bytes are a conservative development reservation, not usage.
            self.ledger.reserve(route.run_id, request_id, len(raw_request) + cap, metadata={
                'evidence_class': route.evidence_class, 'wire_protocol': protocol,
                'model_requested': route.model,
                'native_session_id': handler.headers.get('x-deepseek-harness-session-id'),
                'stage': 'compaction' if handler.headers.get('x-deepseek-harness-compact') == '1' else 'model'})
        except (ValueError, KeyError, UnicodeError) as error:
            return self.reply(handler, 403, {'error': str(error)})
        wire_dir = self.root / route.run_id
        wire_dir.mkdir(parents=True, exist_ok=True)
        allowed_headers = {'content-type', 'anthropic-version', 'anthropic-beta',
            'x-deepseek-harness-session-id', 'x-deepseek-harness-compact'}
        headers = {k:v for k,v in handler.headers.items() if k.lower() in allowed_headers}
        headers['Accept-Encoding'] = 'identity'
        if protocol == 'messages':
            headers['x-api-key'] = route.api_key
        else:
            headers['Authorization'] = 'Bearer ' + route.api_key
        raw = bytearray()
        status, content_type, error_type = 0, '', None
        began = time.time()
        try:
            with httpx.Client(transport=self.transport, timeout=self.timeout_seconds, follow_redirects=False) as client:
                with client.stream('POST', route.endpoints[protocol], content=raw_request, headers=headers) as response:
                    status = response.status_code
                    content_type = response.headers.get('content-type', 'application/json')
                    handler.send_response(status)
                    handler.send_header('Content-Type', content_type)
                    handler.send_header('Connection', 'close')
                    handler.end_headers()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw) > 128 * 1024 * 1024:
                            raise ValueError('RESPONSE_TOO_LARGE')
                        handler.wfile.write(chunk)
                        handler.wfile.flush()
        except Exception as error:
            error_type = type(error).__name__
        finally:
            usage, stream_complete, payload, usage_complete = _wire_usage(bytes(raw), content_type, protocol)
            response_record = {'http_status': status, 'content_type': content_type,
                'body': payload, 'stream_complete': stream_complete, 'usage_complete': usage_complete, 'error_type': error_type,
                'raw_file': str(wire_dir / (request_id + '.response.txt'))}
            failed = bool(error_type or status != 200 or not stream_complete)
            write_json(wire_dir / (request_id + '.json'), {'request_id':request_id,
                'request': body, 'response': response_record, 'usage': usage,
                'evidence_class': route.evidence_class, 'duration_s': time.time()-began,
                'auth_headers': 'omitted', 'native_session_id': handler.headers.get('x-deepseek-harness-session-id')})
            (wire_dir / (request_id + '.response.txt')).write_bytes(bytes(raw).replace(route.api_key.encode(), b'[REDACTED]'))
            self.ledger.settle(route.run_id, request_id, usage=usage, response=response_record, failed=failed)
            if not status:self.reply(handler,502,{'error':error_type})
            handler.close_connection = True

    def question(self, handler, route, body):
        request_id = body.get('requestId')
        if not isinstance(request_id, str) or not body.get('questions'):
            return self.reply(handler, 400, {'error':'invalid question packet'})
        if request_id in route.question_events:
            return self.reply(handler, 409, {'error':'question already pending'})
        pending = {'packet':body, 'event':threading.Event(), 'answer':None, 'paused':False}
        route.question_events[request_id] = pending
        self.ledger.record(route.run_id, 'native_question_received', body)
        # SDK continues waiting in this same task/process. Active background
        # work prevents pausing time; there is no automatic answer or G lookup.
        while not pending['event'].wait(.2):
            state = self.ledger.snapshot(route.run_id)
            if state['status'] not in {'running','awaiting_user'}:
                return self.reply(handler, 409, {'error':'task ended'})
            if not pending['paused'] and state['status']=='running' and not any(c['state']=='inflight' for c in self.ledger.calls(route.run_id)) and not state['activities'] and (route.quiescent is None or route.quiescent(body)):
                self.ledger.ask(route.run_id, question_id=request_id, text=json.dumps(body['questions'],ensure_ascii=False), binding={'native_packet':body})
                pending['paused'] = True
        return self.reply(handler, 200, pending['answer'])

    def answer(self, token, request_id, *, answers, text, event_id):
        route = self.routes[token]
        pending = route.question_events[request_id]
        if not pending['paused']:
            raise ValueError('ACTIVE_NATIVE_WORK_PREVENTS_ANSWER')
        questions=pending['packet']['questions']
        if not isinstance(answers,list) or len(answers)!=len(questions):
            raise ValueError('NATIVE_ANSWER_COUNT_MISMATCH')
        seen=set()
        for answer in answers:
            question=next((q for q in questions if q['id']==answer.get('id')),None)
            labels={o['label'] for o in (question or {}).get('options',[])}
            selected=answer.get('selected')
            if not question or answer['id'] in seen or not isinstance(selected,list) or not all(isinstance(s,str) for s in selected) or len(set(selected))!=len(selected) or not set(selected).issubset(labels) or (not question.get('multiSelect',False) and len(selected)>1) or ('custom' in answer and not isinstance(answer['custom'],str)) or (not selected and not answer.get('custom','').strip()):
                raise ValueError('NATIVE_ANSWER_NOT_OFFERED')
            seen.add(answer['id'])
        packet = {'requestId':request_id, 'status':'answered', 'answers':answers}
        self.ledger.answer(route.run_id, question_id=request_id, text=text, event_id=event_id, native_answer=packet)
        pending['answer'] = packet
        pending['event'].set()
