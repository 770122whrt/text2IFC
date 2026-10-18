"""F/G-only short-context entry over the existing repair batch carrier.

Examples: python -m scripts.ifc_repair.qwen_batch prepare --root <new-root>
--dataset <pairs> --mode offline; then run/status --brief/pause/resume. Live
execution retains the existing scoped/native admission and publication gates.
"""
from __future__ import annotations

from copy import deepcopy
from contextlib import closing
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
import os
import re
from pathlib import Path
import sys
import sqlite3
import time
import uuid

import httpx

from scripts.ifc_repair.qwen_context import ContextLimitError, ContextPolicy, compact_request, encoded
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.group_config import default_providers, normalize_providers
from scripts.ifc_repair.repair_comparison.ledger import Ledger, encode
from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway, _wire_usage

POLICY_VERSION = 'qwen-short-context/0.1'
TRANSIENT = {429, 500, 502, 503, 504}
MODULE_FILES = ('scripts/ifc_repair/qwen_batch.py', 'scripts/ifc_repair/qwen_context.py')
TOKENIZER_ASSET = carrier.REPO/'.cache/models/Qwen3.5-35B-A3B-tokenizer/tokenizer.json'


@dataclass(frozen=True)
class QwenPolicy(ContextPolicy):
    backoff_seconds: tuple[float, ...] = (2, 8)
    cooldown_seconds: float = 60
    request_timeout_seconds: float = 180

    def __post_init__(self):
        # Base validates just its fields, not this subclass's retry settings.
        ContextPolicy(**{k: getattr(self, k) for k in ContextPolicy.__dataclass_fields__})
        if (len(self.backoff_seconds) > 3 or any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 30 for v in self.backoff_seconds)
                or type(self.cooldown_seconds) not in (int, float) or not math.isfinite(self.cooldown_seconds)
                or not 0 < self.cooldown_seconds <= 600 or type(self.request_timeout_seconds) not in (int, float)
                or not math.isfinite(self.request_timeout_seconds) or not 0 < self.request_timeout_seconds <= 1800):
            raise ValueError('INVALID_RETRY_POLICY')


def policy_document(policy):
    return {'schema_version': POLICY_VERSION, **asdict(policy)}


def default_policy():
    return QwenPolicy(tokenizer_path=str(TOKENIZER_ASSET.resolve()) if TOKENIZER_ASSET.is_file() else None)


def load_policy(root):
    return load_policy_file(Path(root)/'qwen-policy.json')


def load_policy_file(path):
    value = read_json(Path(path))
    if value.pop('schema_version', None) != POLICY_VERSION:
        raise ValueError('QWEN_POLICY_VERSION_REQUIRED')
    if 'backoff_seconds' in value:
        value['backoff_seconds'] = tuple(value['backoff_seconds'])
    return QwenPolicy(**value)


def limited_providers(providers, policy):
    value = deepcopy(providers)
    qwen = value['qwen']
    # Keep the legacy pre-gateway allowance; larger offered windows must not
    # remain capped by the earlier 128K client guard.
    qwen['max_input_tokens'] = max(128000, policy.context_tokens)
    qwen['max_output_tokens'] = policy.output_tokens
    qwen['request_options'].setdefault('temperature', .6)
    qwen['request_options'].setdefault('top_p', .95)
    qwen['request_options']['chat_template_kwargs'] = {'enable_thinking': False}
    return normalize_providers(value)


def interface_fault(root, run_id):
    """A recovered retry remains failed evidence, but is no longer a blocker."""
    ledger = Ledger(Path(root)/'control.sqlite')
    recovered = {request_id for event in ledger.events(run_id)
                 if event['kind'] == 'qwen_request_recovered'
                 for request_id in event['payload']['failed_request_ids']}
    for call in ledger.calls(run_id):
        if call['failed'] and call['request_id'] not in recovered:
            response = call.get('response') or {}
            code = response.get('http_status')
            if code == 400 and context_error(response.get('body')):
                continue  # An individual irreducible context is a task failure.
            if response.get('error_type') or code is not None and (code >= 400 or code == 0):
                return True
    return any(e['kind'] == 'qwen_circuit_blocked' for e in ledger.events(run_id))


def _evidence_seal(db):
    result = {}
    for table, order in [('runs', 'run_id'), ('calls', 'run_id,request_id'), ('events', 'seq')]:
        digest = hashlib.sha256()
        for row in db.execute(f'SELECT * FROM {table} ORDER BY {order}'):
            digest.update((encode(list(row))+'\n').encode('utf8'))
        result[table] = digest.hexdigest()
    return result


def _context_target(before, change, reference):
    raw = deepcopy(before['policy'])
    raw.pop('schema_version')
    raw['backoff_seconds'] = tuple(raw['backoff_seconds'])
    policy = replace(QwenPolicy(**raw), context_tokens=change['context_tokens'])
    value = deepcopy(before['plan'])
    value['configuration']['providers'] = limited_providers(value['configuration']['providers'], policy)
    value['configuration']['configuration_version'] = 'repair-comparison-scalable-configuration/0.2'
    value['qwen_context_revision'] = reference
    value.pop('sha256')
    value['sha256'] = batch._digest(value)
    runtime = deepcopy(before['runtime'])
    runtime['configuration'] = deepcopy(value['configuration'])
    for key in ['providers', 'configuration_version']:
        runtime[key] = deepcopy(value['configuration'][key])
    return value, runtime, policy_document(policy)


def configure_context(root, *, context_tokens, revision):
    """Revise an idle existing F/G batch, preserving all task evidence and budgets."""
    from scripts.ifc_repair.repair_comparison.controller_owner import task_owner
    from scripts.ifc_repair.batch_resilience import process_alive
    root = Path(root).resolve()
    if context_tokens != 256000 or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', revision):
        raise ValueError('INVALID_QWEN_CONTEXT_REVISION')
    if not all((root/name).is_file() for name in ['control.sqlite', 'batch.json', 'experiment.json', 'qwen-policy.json']):
        raise ValueError('QWEN_BATCH_NOT_PREPARED')
    receipt = root/'admission'/f'context-{revision}.json'
    receipt.parent.mkdir(exist_ok=True)
    pending = root/'qwen-context-revision.pending'
    ledger = Ledger(root/'control.sqlite')
    with task_owner(root, 'batch-owner'), task_owner(root, 'service-transition'):
        with ledger.transaction() as db:
            if db.execute("SELECT 1 FROM runs WHERE json_extract(state,'$.status') IN ('running','awaiting_user') LIMIT 1").fetchone() or db.execute("SELECT 1 FROM calls WHERE state='inflight' LIMIT 1").fetchone():
                raise ValueError('QWEN_CONTEXT_REQUIRES_QUIESCENT_BATCH')
            for name in ['controller.json', 'service.json']:
                if (root/name).is_file():
                    state = read_json(root/name)
                    if state.get('pid') and process_alive(state['pid']):
                        raise ValueError('QWEN_CONTEXT_REQUIRES_QUIESCENT_PROCESSES')
            if receipt.is_file() and not pending.exists():
                if load_policy(root).context_tokens != context_tokens or batch.plan(root).get('qwen_context_revision') != {'path':str(receipt), 'sha256':sha256(receipt)}:
                    raise ValueError('QWEN_CONTEXT_REVISION_CHANGED')
                return {'state':'unchanged', 'context_tokens':context_tokens}
            if pending.is_file():
                change = read_json(pending)
                if change['revision'] != revision or change['context_tokens'] != context_tokens:
                    raise ValueError('QWEN_CONTEXT_REVISION_RECOVERY_REQUIRED')
                before_path = Path(change['before']['path'])
                if sha256(before_path) != change['before']['sha256']:
                    raise ValueError('QWEN_CONTEXT_HISTORY_CHANGED')
                before = read_json(before_path)
            else:
                before = {'plan':batch.plan(root), 'runtime':read_json(root/'experiment.json'), 'policy':read_json(root/'qwen-policy.json')}
                if {r.rsplit('-',1)[1] for r in before['plan']['configuration']['order']} != {'F','G'}:
                    raise ValueError('QWEN_ARMS_ONLY')
                before_path = receipt.with_name(f'context-{revision}-before.json')
                if before_path.exists() and read_json(before_path) != before:
                    raise ValueError('QWEN_CONTEXT_HISTORY_CHANGED')
                write_json(before_path, before)
                change = {'schema_version':'qwen-context-revision/1.0', 'revision':revision,
                    'context_tokens':context_tokens, 'previous_context_tokens':before['policy']['context_tokens'],
                    'before':{'path':str(before_path),'sha256':sha256(before_path)},
                    'evidence_seal':_evidence_seal(db), 'authorization':'User approved 256K and four slots; retain results and budgets.'}
                write_json(pending, change)
            reference = {'path':str(receipt), 'sha256':hashlib.sha256((encode(change)+'\n').encode('utf8')).hexdigest()}
            value, runtime, policy = _context_target(before, change, reference)
            if _evidence_seal(db) != change['evidence_seal']:
                raise ValueError('QWEN_CONTEXT_EVIDENCE_CHANGED')
            for name in ['property_authorization', 'clarification_policy']:
                row = db.execute('SELECT value FROM batch_control WHERE key=?',(name,)).fetchone()
                if not row:
                    continue
                authority = json.loads(row[0])
                if authority.get('batch_sha256') not in {before['plan']['sha256'],value['sha256']}:
                    raise ValueError('QWEN_CONTEXT_AUTHORIZATION_CHANGED')
                if authority['batch_sha256'] == before['plan']['sha256']:
                    db.execute('INSERT OR IGNORE INTO batch_control VALUES(?,?)',(name+'@'+before['plan']['sha256'],row[0]))
                authority['batch_sha256'] = value['sha256']
                db.execute('UPDATE batch_control SET value=? WHERE key=?',(encode(authority),name))
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',('qwen-context-revision',encode(reference)))
        for path, document in [(root/'batch.json',value),(root/'experiment.json',runtime),(root/'qwen-policy.json',policy),(receipt,change)]:
            batch._replace_bytes(path,(encode(document)+'\n').encode('utf8'))
        pending.unlink()
    return {'state':'context_applied_requires_admission','context_tokens':context_tokens,'receipt':str(receipt),'reinitialized':False}


def verify_context_revision(root, previous, value, old, current):
    reference = value.get('qwen_context_revision', {})
    path = Path(reference.get('path','')).resolve()
    batch._need(path.parent == root/'admission' and sha256(path) == reference.get('sha256'), 'QWEN_CONTEXT_RECEIPT_CHANGED')
    change = read_json(path)
    before_path = Path(change['before']['path'])
    batch._need(sha256(before_path) == change['before']['sha256'], 'QWEN_CONTEXT_HISTORY_CHANGED')
    before = read_json(before_path)
    target, runtime, policy = _context_target(before, change, reference)
    batch._need(value == target and previous['configuration'] == before['plan']['configuration']
        and read_json(root/'qwen-policy.json') == json.loads(encode(policy))
        and read_json(root/'experiment.json')['configuration'] == runtime['configuration'], 'QWEN_CONTEXT_CONFIGURATION_CHANGED')
    batch._need({k:v for k,v in old.items() if k!='files'} == {k:v for k,v in current.items() if k!='files'}, 'QWEN_CONTEXT_BINDINGS_CHANGED')
    with closing(sqlite3.connect(root/'control.sqlite')) as db:
        recorded = db.execute("SELECT value FROM batch_control WHERE key='qwen-context-revision'").fetchone()
        batch._need(recorded and json.loads(recorded[0]) == reference and _evidence_seal(db) == change['evidence_seal'], 'QWEN_CONTEXT_EVIDENCE_CHANGED')
    return reference


def context_error(payload):
    text = json.dumps(payload, ensure_ascii=False).lower()
    return any(marker in text for marker in ('maximum context length', 'context_length_exceeded',
        'context window', 'max total tokens', 'too many tokens'))


def smaller_window(policy, cap, payload):
    text = json.dumps(payload, ensure_ascii=False).lower()
    limits = re.findall(r'(?:maximum context length|max total tokens|context window)[^\d]{0,30}([\d,]+)', text)
    observed = min((int(v.replace(',', '')) for v in limits), default=policy.context_tokens)
    size = min(int(policy.context_tokens*.75), int(observed*.9))
    return replace(policy, context_tokens=size, output_tokens=cap)


class QwenGateway(WireGateway):
    def __init__(self, *args, policy, sleeper=time.sleep, **kwargs):
        super().__init__(*args, **kwargs)
        self.policy, self.sleeper = policy, sleeper

    def _circuit(self, route, *, open_until=None):
        key = 'qwen-circuit:'+hashlib.sha256(encoded([route.endpoints['chat'], route.model])).hexdigest()
        with self.ledger.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            if open_until is not None:
                db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)', (key, encode({'until': open_until})))
            row = db.execute('SELECT value FROM batch_control WHERE key=?', (key,)).fetchone()
        return json.loads(row['value'])['until'] if row else 0

    def handle(self, handler):
        parts = handler.path.strip('/').split('/', 1)
        route = self.routes.get(parts[0]) if len(parts) == 2 else None
        # Questions/control keep their native quiescence and same-session rules.
        if route is None or parts[1] != 'v1/chat/completions':
            return super().handle(handler)
        try:
            state = self.ledger.snapshot(route.run_id)
            if state['arm'] not in {'F', 'G'}:
                raise ValueError('QWEN_ARMS_ONLY')
            if state['status'] != 'running':
                raise ValueError('TASK_NOT_ACTIVE')
            length = int(handler.headers.get('Content-Length', '0'))
            if not 0 < length <= 64*1024*1024:
                raise ValueError('INVALID_REQUEST_SIZE')
            body = json.loads(handler.rfile.read(length))
            if not isinstance(body, dict) or body.get('model') != route.model:
                raise ValueError('MODEL_NOT_OFFERED')
            if body.get('stream') is True:
                raise ValueError('QWEN_NONSTREAM_REQUIRED_FOR_RETRY')
            body.update(route.request_options)
            source_body = deepcopy(body)
            cap = body.get('max_tokens', body.get('max_completion_tokens'))
            if type(cap) is not int or not 0 < cap <= min(route.max_output_tokens, self.policy.output_tokens):
                raise ValueError('OUTPUT_LIMIT_NOT_OFFERED')
            body, context = compact_request(body, arm=state['arm'], policy=self.policy,
                workspace=state['metadata'].get('workspace'))
            raw_request = encoded(body)
            self.ledger.record(route.run_id, 'qwen_context_projection', context)
            if self._circuit(route) > time.time():
                self.ledger.record(route.run_id, 'qwen_circuit_blocked', {'reason': 'QWEN_ENDPOINT_COOLDOWN'})
                return self.reply(handler, 503, {'error': 'QWEN_ENDPOINT_COOLDOWN', 'origin': 'repair-controller'})
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            rejection = {'error': str(error), 'origin': 'repair-controller', 'wire_protocol': 'chat'}
            self.ledger.record(route.run_id, 'controller_request_rejected', rejection)
            return self.reply(handler, 403, rejection)
        failed_ids = []
        context_retried = False
        headers = {'Content-Type': 'application/json', 'Accept-Encoding': 'identity'}
        if route.api_key:
            headers['Authorization'] = 'Bearer '+route.api_key
        for attempt in range(1+len(self.policy.backoff_seconds)):
            state = self.ledger.snapshot(route.run_id)
            remaining = state['limits']['active_seconds']-state['active_elapsed_s']
            request_id = 'qwen-'+uuid.uuid4().hex
            try:
                reservation = context['after_estimate'] + cap + self.policy.overhead_tokens
                self.ledger.reserve(route.run_id, request_id, reservation, metadata={
                    'evidence_class': route.evidence_class, 'wire_protocol': 'chat', 'model_requested': route.model,
                    'stage': 'model', 'qwen_policy': POLICY_VERSION, 'attempt': attempt+1, 'context': context})
            except ValueError as error:
                return self.reply(handler, 403, {'error': str(error), 'origin': 'repair-controller', 'wire_protocol': 'chat'})
            status, content_type, raw, error_type, retry_after = 0, 'application/json', b'', None, 0
            began = time.time()
            try:
                with httpx.Client(transport=self.transport, trust_env=self.transport is None,
                        follow_redirects=False, timeout=max(.01, min(self.policy.request_timeout_seconds, remaining))) as client:
                    response = client.post(route.endpoints['chat'], content=raw_request, headers=headers)
                    status, content_type, raw = response.status_code, response.headers.get('content-type', 'application/json'), response.content
                    if len(raw) > 128*1024*1024:
                        raise ValueError('RESPONSE_TOO_LARGE')
                    try:
                        retry_after = min(30, max(0, float(response.headers.get('retry-after', '0'))))
                    except ValueError:
                        pass
            except Exception as error:
                error_type = type(error).__name__
                transient = isinstance(error, (httpx.TimeoutException, httpx.NetworkError))
            else:
                transient = status in TRANSIENT
            usage, complete, payload, usage_complete = _wire_usage(raw, content_type, 'chat')
            failed = bool(error_type or status != 200 or not complete)
            record = {'http_status': status, 'content_type': content_type, 'body': payload,
                      'stream_complete': complete, 'usage_complete': usage_complete, 'error_type': error_type}
            # Actual projected input and raw response are in the existing ledger;
            # no extra per-call files are exported or needed for recovery.
            self.ledger.record(route.run_id, 'qwen_wire_request', {'request_id': request_id,
                'request': body, 'duration_s': time.time()-began, 'auth_headers': 'omitted'})
            self.ledger.settle(route.run_id, request_id, usage=usage, response=record, failed=failed)
            if not failed:
                if failed_ids:
                    self.ledger.record(route.run_id, 'qwen_request_recovered', {'request_id': request_id, 'failed_request_ids': failed_ids})
                self._circuit(route, open_until=0)
                return self._raw_reply(handler, status, content_type, raw)
            failed_ids.append(request_id)
            if status == 400 and context_error(payload) and not context_retried and attempt < len(self.policy.backoff_seconds):
                context_retried = True
                try:
                    tighter = smaller_window(self.policy, cap, payload)
                    body, context = compact_request(source_body, arm=state['arm'], policy=tighter,
                        workspace=state['metadata'].get('workspace'))
                except (ContextLimitError, ValueError) as error:
                    self.ledger.record(route.run_id, 'qwen_context_irreducible', {'reason': str(error)})
                    return self.reply(handler, 403, {'error': 'PROTECTED_CONTEXT_EXCEEDS_WINDOW_AFTER_COMPACTION',
                        'origin': 'repair-controller', 'wire_protocol': 'chat'})
                raw_request = encoded(body)
                self.ledger.record(route.run_id, 'qwen_context_projection', {**context, 'trigger': 'upstream_context_error'})
                continue
            if transient and attempt < len(self.policy.backoff_seconds):
                delay = max(self.policy.backoff_seconds[attempt], retry_after)
                # Retry waits count as active task time. Budget/call reservations
                # are checked afresh, never reset when the same request retries.
                self.ledger.record(route.run_id, 'qwen_retry_wait', {'request_id': request_id, 'delay_s': delay})
                self.sleeper(delay)
                continue
            if transient:
                self._circuit(route, open_until=time.time()+self.policy.cooldown_seconds)
            if not status or error_type:
                return self.reply(handler, 502, {'error': error_type or 'INVALID_UPSTREAM_RESPONSE'})
            return self._raw_reply(handler, status, content_type, raw)

    @staticmethod
    def _raw_reply(handler, status, content_type, raw):
        handler.send_response(status)
        handler.send_header('Content-Type', content_type)
        handler.send_header('Content-Length', str(len(raw)))
        handler.end_headers()
        handler.wfile.write(raw)


def install(root, policy=None):
    """Install only in this independent CLI process; base modules stay on disk."""
    root = Path(root).resolve()
    policy = policy or load_policy(root)
    if getattr(carrier, '_qwen_entry_installed', False):
        if carrier._qwen_entry_root != root:
            raise ValueError('QWEN_PROCESS_ROOT_ALREADY_BOUND')
        return
    original_bindings = carrier.bindings
    def bindings(configuration=None):
        value = original_bindings(configuration)
        value['files'].update({p: sha256(carrier.REPO/p) for p in MODULE_FILES})
        value['files']['qwen-policy.json'] = hashlib.sha256(encoded(policy_document(policy))).hexdigest()
        if policy.tokenizer_path:
            value['files']['qwen-tokenizer.json'] = sha256(Path(policy.tokenizer_path))
        return value
    carrier.bindings = bindings
    carrier.WireGateway = lambda *args, **kwargs: QwenGateway(*args, policy=policy, **kwargs)
    carrier._qwen_entry_installed, carrier._qwen_entry_root = True, root
    batch.CLI = [sys.executable, '-m', 'scripts.ifc_repair.qwen_batch', 'worker']
    batch._interface_fault = interface_fault


def _option(argv, name):
    if name not in argv:
        return None
    return argv[argv.index(name)+1]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.stdout.reconfigure(encoding='utf8')
    sys.stderr.reconfigure(encoding='utf8')
    if not argv or '--root' not in argv:
        print('Usage: qwen_batch prepare|gate|admit|run|pause|resume|status --root PATH [batch options]')
        return 2
    root = Path(_option(argv, '--root')).resolve()
    if argv[0] == 'configure-context':
        print(json.dumps(configure_context(root, context_tokens=int(_option(argv,'--context-tokens')), revision=_option(argv,'--revision')),ensure_ascii=False))
        return 0
    if (root/'qwen-context-revision.pending').exists():
        raise ValueError('QWEN_CONTEXT_REVISION_RECOVERY_REQUIRED')
    # New roots only. Existing formal A-E admission and terminal evidence cannot
    # be relabeled as short-context F/G runs.
    if argv[0] == 'prepare':
        if root.exists():
            raise ValueError('NEW_QWEN_ROOT_REQUIRED')
        policy_path = _option(argv, '--policy')
        policy = load_policy_file(policy_path) if policy_path else default_policy()
        if policy_path:
            argv[argv.index('--policy'):argv.index('--policy')+2] = []
        if '--groups' in argv or _option(argv, '--scope') == 'two-rounds':
            raise ValueError('QWEN_PREPARE_FREEZES_FG_FULL_SCOPE')
        providers_path = _option(argv, '--providers')
        providers = read_json(Path(providers_path)) if providers_path else default_providers()
        if providers_path:
            argv[argv.index('--providers'):argv.index('--providers')+2] = []
        install(root, policy)
        original_prepare = batch.prepare
        def prepare(*args, **kwargs):
            kwargs['providers'] = limited_providers(providers, policy)
            result = original_prepare(*args, **kwargs)
            write_json(root/'qwen-policy.json', policy_document(policy))
            return result
        batch.prepare = prepare
        argv += ['--groups', 'F', 'G']
        if '--scope' not in argv:
            argv += ['--scope', 'full']
        if '--concurrency' not in argv:
            argv += ['--concurrency', '2']
    else:
        policy = load_policy(root)
        configuration = (batch.plan(root)['configuration'] if (root/'batch.json').is_file()
                         else read_json(root/'experiment.json')['configuration'] if argv[0] == 'worker'
                         else batch.plan(root)['configuration'])
        if {r.rsplit('-', 1)[1] for r in configuration['order']} - {'F', 'G'}:
            raise ValueError('QWEN_ARMS_ONLY')
        if configuration['providers'] != limited_providers(configuration['providers'], policy):
            raise ValueError('QWEN_PROVIDER_POLICY_CHANGED')
        install(root, policy)
    if argv[0] == 'worker':
        sys.argv = [sys.argv[0], *argv[1:]]
        carrier.main()
        return 0
    return batch.main(argv)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as error:
        print(json.dumps({'event': 'attention', 'reason': type(error).__name__+': '+str(error)[:240]}, ensure_ascii=False))
        raise SystemExit(2)
