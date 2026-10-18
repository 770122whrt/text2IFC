"""Optional G-only client parser for Qwen services without auto tool parsing.

Retains the existing generic tools, executor, isolation and Qwen budget gateway.
Raw provider responses remain the ledger authority. No Harness changes.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import threading
from copy import deepcopy
from pathlib import Path
import sys

import jsonschema
from . import qwen_batch as qwen

VERSION = 'qwen-client-tools/0.1'
MODULE = 'scripts/ifc_repair/qwen_tools.py'
BASE_INSTALL = qwen.install


def decode_tools(content, tools):
    """Decode native XML-ish or JSON tool blocks against offered schemas only."""
    if not isinstance(content, str):
        raise ValueError('QWEN_TOOL_CONTENT_NOT_TEXT')
    if '<tool_call>' not in content:
        return []
    blocks = list(re.finditer(r'<tool_call>(.*?)</tool_call>', content, re.S))
    if len(blocks) != content.count('<tool_call>') or len(blocks) != content.count('</tool_call>'):
        raise ValueError('QWEN_TOOL_BLOCK_INCOMPLETE')
    offered = {t['function']['name']: t['function']['parameters'] for t in tools}
    calls = []
    for index, block in enumerate(blocks):
        value = block.group(1).strip()
        if value.startswith('{'):
            obj = json.loads(value)
            name, args = obj['name'], obj['arguments']
        else:
            function = re.fullmatch(r'<function=([A-Za-z_][\w]*)>\s*(.*?)\s*</function>', value, re.S)
            if not function:
                raise ValueError('QWEN_TOOL_FUNCTION_INVALID')
            name, body = function.groups()
            if name not in offered:
                raise ValueError('QWEN_TOOL_NOT_OFFERED')
            args, end = {}, 0
            for parameter in re.finditer(r'<parameter=([A-Za-z_][\w]*)>(.*?)</parameter>', body, re.S):
                if body[end:parameter.start()].strip():
                    raise ValueError('QWEN_TOOL_PARAMETER_INVALID')
                key, raw = parameter.groups()
                if key in args or key not in offered[name].get('properties', {}):
                    raise ValueError('QWEN_TOOL_PARAMETER_NOT_OFFERED_OR_DUPLICATED')
                # Qwen's template puts one newline around literal strings.
                raw = raw.removeprefix('\n').removesuffix('\n')
                kind = offered[name]['properties'][key].get('type')
                args[key] = raw if kind == 'string' else json.loads(raw.strip())
                end = parameter.end()
            if body[end:].strip():
                raise ValueError('QWEN_TOOL_PARAMETER_INVALID')
        if name not in offered:
            raise ValueError('QWEN_TOOL_NOT_OFFERED')
        try:
            jsonschema.Draft202012Validator(offered[name]).validate(args)
        except jsonschema.ValidationError as error:
            raise ValueError('QWEN_TOOL_ARGUMENT_SCHEMA_INVALID') from error
        identity = hashlib.sha256((str(index)+block.group()).encode()).hexdigest()[:24]
        calls.append({'id': 'call_qwen_'+identity, 'type': 'function',
                      'function': {'name': name, 'arguments': json.dumps(args, ensure_ascii=False)}})
    return calls


class _Request:
    def __init__(self, handler, body):
        self.original = handler
        raw = qwen.encoded(body)
        self.rfile = io.BytesIO(raw)
        self.headers = dict(handler.headers)
        self.headers['Content-Length'] = str(len(raw))

    def __getattr__(self, name):
        return getattr(self.original, name)


class ToolGateway(qwen.QwenGateway):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local = threading.local()

    def handle(self, handler):
        self.local.tools = None
        parts = handler.path.strip('/').split('/', 1)
        route = self.routes.get(parts[0]) if len(parts) == 2 else None
        if route and parts[1] == 'v1/chat/completions' and self.ledger.snapshot(route.run_id)['arm'] == 'G':
            length = int(handler.headers.get('Content-Length', '0'))
            if 0 < length <= 64*1024*1024:
                raw = handler.rfile.read(length)
                try:
                    body = json.loads(raw)
                except ValueError:
                    return self.reply(handler, 403, {'error':'INVALID_REQUEST_JSON','origin':'repair-controller'})
                if isinstance(body, dict) and body.get('tools'):
                    body['tool_choice'] = None
                    self.local.tools, self.local.run_id = deepcopy(body['tools']), route.run_id
                    self.ledger.record(route.run_id, 'qwen_tool_transport', {'version': VERSION,
                        'tool_choice': None, 'offered_names': [t['function']['name'] for t in body['tools']]})
                handler = _Request(handler, body)
        return super().handle(handler)

    def _raw_reply(self, handler, status, content_type, raw):
        if status == 200 and self.local.tools:
            try:
                payload = json.loads(raw)
                choice = payload['choices'][0]
                message = choice['message']
                if not message.get('tool_calls') and choice['finish_reason'] == 'stop':
                    calls = decode_tools(message.get('content') or '', self.local.tools)
                    if calls:
                        message['tool_calls'], message['content'] = calls, None
                        choice['finish_reason'] = 'tool_calls'
                        self.ledger.record(self.local.run_id, 'qwen_tool_decoded', {'version':VERSION,
                            'names':[c['function']['name'] for c in calls], 'raw_provider_response_retained':True})
                        raw = qwen.encoded(payload)
            except (ValueError, KeyError, TypeError) as error:
                self.ledger.record(self.local.run_id, 'qwen_tool_decode_failed', {'version':VERSION,'reason':str(error)[:160]})
                return self.reply(handler, 502, {'error':'QWEN_TOOL_DECODE_INVALID','origin':'repair-controller'})
        return super()._raw_reply(handler, status, content_type, raw)


def install(root, policy=None):
    BASE_INSTALL(root, policy)
    if getattr(qwen.carrier, '_qwen_tools_installed', False):
        return
    original = qwen.carrier.bindings
    def bindings(configuration=None):
        value = original(configuration)
        if not configuration or any(r.endswith('-G') for r in configuration['order']):
            value['files'][MODULE] = qwen.sha256(qwen.carrier.REPO/MODULE)
        return value
    qwen.carrier.bindings = bindings
    policy = policy or qwen.load_policy(Path(root))
    qwen.carrier.WireGateway = lambda *args, **kwargs: ToolGateway(*args, policy=policy, **kwargs)
    qwen.batch.CLI = [sys.executable, '-m', 'scripts.ifc_repair.qwen_tools', 'worker']
    qwen.carrier._qwen_tools_installed = True


def main():
    root = qwen._option(sys.argv[1:], '--root')
    if not root:
        raise ValueError('ROOT_REQUIRED')
    install(Path(root), qwen.load_policy(Path(root)))
    return qwen.main()


if __name__ == '__main__':
    raise SystemExit(main())
