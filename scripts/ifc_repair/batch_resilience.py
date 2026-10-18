"""Opt-in fault isolation and notifications for the frozen Repair batch.

This entry wraps the existing carrier without changing its Harness, inputs,
model identities, budgets, or Qwen entry. Operational admission is additional
to, and never a replacement for, the original source-bound runtime admission.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import closing
from dataclasses import asdict, dataclass
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path
import random
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
import xml.etree.ElementTree as ET

import httpx

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256, write_json
from scripts.ifc_repair.repair_comparison.controller_owner import task_owner
from scripts.ifc_repair.repair_comparison.ledger import Ledger, TERMINAL, encode
from scripts.ifc_repair.repair_comparison.wire_gateway import WireGateway, _wire_usage


FAMILIES = {'deepseek': ('A', 'B', 'D'), 'gpt': ('C', 'E'), 'qwen': ('F', 'G')}
TRANSIENT = {429, 500, 502, 503, 504}
MODULE = 'scripts/ifc_repair/batch_resilience.py'


@dataclass(frozen=True)
class Policy:
    backoff_seconds: tuple[float, ...] = (5, 15, 45)
    jitter_fraction: float = .2
    max_wait_seconds: float = 180
    deepseek_requests: int = 4
    gpt_requests: int = 2
    qwen_requests: int = 1
    desktop_notifications: bool = True

    def __post_init__(self):
        if (len(self.backoff_seconds) > 5 or any(s < 0 for s in self.backoff_seconds)
                or not 0 <= self.jitter_fraction <= 1 or self.max_wait_seconds <= 0
                or any(type(n) is not int or n < 1 for n in
                       (self.deepseek_requests, self.gpt_requests, self.qwen_requests))):
            raise ValueError('INVALID_RESILIENCE_POLICY')


def family(arm):
    return next(name for name, groups in FAMILIES.items() if arm in groups)


def retry_after(value, *, now=None):
    if not value:
        return 0
    try:
        return max(0, float(value))
    except (ValueError, TypeError):
        try:
            return max(0, parsedate_to_datetime(value).timestamp() - (time.time() if now is None else now))
        except (ValueError, TypeError, OverflowError):
            return 0


class Alerts:
    """Small persistent event outbox in the existing ledger, not per-task logs."""
    def __init__(self, root, *, desktop=None):
        self.root = Path(root)
        policy_path = self.root/'operations-policy.json'
        self.desktop = (read_json(policy_path).get('desktop_notifications', False)
                        if desktop is None and policy_path.is_file() else bool(desktop))
        self.ledger = Ledger(self.root/'control.sqlite')
        with self.ledger.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS batch_alerts('
                       'seq INTEGER PRIMARY KEY AUTOINCREMENT, signature TEXT UNIQUE, '
                       'payload TEXT NOT NULL, acknowledged INTEGER NOT NULL DEFAULT 0)')

    def emit(self, event, **fields):
        if event not in {'paused', 'attention', 'complete'}:
            return False
        allowed = {'reason', 'run_id', 'question_id', 'groups', 'completed', 'total'}
        payload = {'event': event, **{k: v for k, v in fields.items() if k in allowed}}
        payload = json.loads(encode(payload))
        signature = hashlib.sha256(encode(payload).encode()).hexdigest()
        with self.ledger.transaction() as db:
            inserted = db.execute('INSERT OR IGNORE INTO batch_alerts(signature,payload) VALUES(?,?)',
                                  (signature, encode({**payload, 'time': time.time()}))).rowcount
        if inserted and self.desktop:
            desktop_notification(payload)
        return bool(inserted)

    def pending(self, *, acknowledge=False):
        with self.ledger.transaction() as db:
            rows = db.execute('SELECT seq,payload FROM batch_alerts '
                              'WHERE acknowledged=0 ORDER BY seq').fetchall()
            if acknowledge and rows:
                db.executemany('UPDATE batch_alerts SET acknowledged=1 WHERE seq=?',
                               [(r[0],) for r in rows])
        return [{'seq': r[0], **json.loads(r[1])} for r in rows]


def desktop_notification(payload):
    """Best-effort Windows notification; delivery evidence remains in outbox."""
    if os.name != 'nt':
        return
    text = {'paused': 'Repair 实验已暂停', 'attention': 'Repair 实验需要处理',
            'complete': 'Repair 实验已完成'}[payload['event']]
    detail = str(payload.get('reason') or '')[:160]
    if payload.get('groups'):
        detail += '；相关组：'+'/'.join(payload['groups'])
    def literal(value):
        return "'"+value.replace("'", "''")+"'"
    command = ('Add-Type -AssemblyName System.Windows.Forms; '
               '$repairIcon=New-Object System.Windows.Forms.NotifyIcon; '
               '$repairIcon.Icon=[System.Drawing.SystemIcons]::Information; '
               '$repairIcon.Visible=$true; '
               f'$repairIcon.ShowBalloonTip(15000,{literal(text)},{literal(detail)},'
               '[System.Windows.Forms.ToolTipIcon]::Info); '
               'Start-Sleep -Seconds 20; $repairIcon.Dispose()')
    try:
        subprocess.Popen(['powershell.exe', '-NoProfile', '-NonInteractive', '-WindowStyle', 'Hidden',
                          '-EncodedCommand', base64.b64encode(command.encode('utf-16le')).decode()],
                         creationflags=subprocess.CREATE_NO_WINDOW,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass  # Notification permission/focus settings must not stop the batch.


class Holds:
    def __init__(self, root, *, alerts=None):
        self.root = Path(root)
        self.ledger = Ledger(self.root/'control.sqlite')
        self.alerts = alerts or Alerts(root)
        with self.ledger.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')

    @staticmethod
    def records(db):
        row = db.execute("SELECT value FROM batch_control WHERE key='provider-holds'").fetchone()
        return json.loads(row[0]) if row else {}

    def groups(self):
        with self.ledger.transaction() as db:
            records = self.records(db)
        return sorted({arm for row in records.values() for arm in row['groups']})

    def isolated_runs(self):
        with self.ledger.transaction() as db:
            row = db.execute("SELECT value FROM batch_control WHERE key='provider-isolated-runs'").fetchone()
        return json.loads(row[0]) if row else {}

    def hold(self, arm, *, reason, code=None, run_id=None, provider=True):
        name = family(arm) if provider else arm
        groups = list(FAMILIES[name]) if provider else [arm]
        with self.ledger.transaction() as db:
            records = self.records(db)
            new = name not in records
            records[name] = {'groups': groups, 'reason': reason, 'http_status': code,
                             'run_id': run_id, 'time': time.time()}
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                       ('provider-holds', encode(records)))
            if run_id:
                row = db.execute("SELECT value FROM batch_control WHERE key='provider-isolated-runs'").fetchone()
                isolated = json.loads(row[0]) if row else {}
                isolated[run_id] = {'groups': groups, 'reason': reason, 'http_status': code}
                db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                           ('provider-isolated-runs', encode(isolated)))
        if new:
            self.alerts.emit('attention', reason=reason, groups=groups, run_id=run_id)

    def release(self, groups, *, reason):
        if not reason or not groups or len(set(groups)) != len(groups) or not set(groups) <= set('ABCDEFG'):
            raise ValueError('GROUP_RELEASE_REASON_REQUIRED')
        with self.ledger.transaction() as db:
            parameters = ','.join('?' for _ in groups)
            busy = db.execute("SELECT 1 FROM runs WHERE json_extract(state,'$.arm') IN ("+parameters+") "
                              "AND json_extract(state,'$.status') IN ('running','awaiting_user') LIMIT 1", groups).fetchone()
            inflight = db.execute("SELECT 1 FROM calls JOIN runs USING(run_id) WHERE calls.state='inflight' "
                                  "AND json_extract(runs.state,'$.arm') IN ("+parameters+") LIMIT 1", groups).fetchone()
            if busy or inflight:
                raise ValueError('PROVIDER_RELEASE_REQUIRES_QUIESCENT_GROUPS')
            records = self.records(db)
            remaining = {name: {**row, 'groups': [g for g in row['groups'] if g not in groups]}
                         for name, row in records.items()}
            remaining = {name: row for name, row in remaining.items() if row['groups']}
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                       ('provider-holds', encode(remaining)))
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                       ('provider-release', encode({'groups': groups, 'reason': reason, 'time': time.time()})))


class _RetryLedger:
    """Map the carrier's final settlement to the last real retry attempt."""
    def __init__(self, ledger, local):
        self.original, self.local = ledger, local

    def __getattr__(self, name):
        return getattr(self.original, name)

    def reserve(self, run_id, request_id, upper_bound, metadata=None):
        metadata = {**(metadata or {}), 'operations_entry': MODULE}
        self.original.reserve(run_id, request_id, upper_bound, metadata)
        context = getattr(self.local, 'context', None)
        if context is not None:
            context.update(original=request_id, current=request_id, reservation=upper_bound,
                           metadata=metadata, failed=[], attempt=0)

    def settle(self, run_id, request_id, **kwargs):
        context = getattr(self.local, 'context', None)
        if context is None or request_id != context.get('original'):
            return self.original.settle(run_id, request_id, **kwargs)
        current = context['current']
        if current is None:
            return  # Retry budget was exhausted after the previous attempt settled.
        failure = context.get('final_failure')
        if failure:
            kwargs.update(failure, failed=True)
        self.original.settle(run_id, current, **kwargs)
        if not kwargs.get('failed') and context['failed']:
            self.original.record(run_id, 'provider_request_recovered', {
                'request_id': current, 'failed_request_ids': context['failed']})


class _RetryTransport(httpx.BaseTransport):
    def __init__(self, gateway, underlying):
        self.gateway, self.underlying = gateway, underlying

    def close(self):
        pass  # Per-client close must not tear down shared parallel connections.

    def handle_request(self, request):
        gateway, context = self.gateway, self.gateway.local.context
        route, ledger = context['route'], gateway.original_ledger
        state = ledger.snapshot(route.run_id)
        for attempt in range(len(gateway.policy.backoff_seconds)+1):
            context['attempt'] = attempt
            error, response, code, raw = None, None, 0, bytearray()
            try:
                response = self.underlying.handle_request(request)
                code = response.status_code
                # Do not expose partial model/tool output to a native client:
                # buffer one bounded response before forwarding it. Only an
                # unpublished response can be safely retried after HTTP 200.
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 128 * 1024 * 1024:
                        raise ValueError('RESPONSE_TOO_LARGE')
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
                    httpx.WriteTimeout, httpx.ReadError, httpx.WriteError,
                    httpx.RemoteProtocolError) as caught:
                error = caught
            finally:
                if response is not None:
                    response.close()
            raw = bytes(raw)
            content_type = response.headers.get('content-type', 'application/json') if response is not None else ''
            usage, complete, payload, usage_complete = _wire_usage(raw, content_type,
                context['metadata']['wire_protocol'])
            if code == 200 and not complete and error is None:
                error = httpx.RemoteProtocolError('INCOMPLETE_PROVIDER_RESPONSE')
            # iter_bytes already decodes content encodings. Prevent a second
            # decode; preserve SSE bytes/events and protocol completion markers.
            if response is not None:
                response = httpx.Response(code, content=raw, headers=[
                    (key, value) for key, value in response.headers.multi_items()
                    if key.lower() not in {'content-encoding', 'content-length', 'transfer-encoding'}])
            if code == 200 and error is None:
                return response
            if payload is None:
                try:
                    payload = json.loads(raw)
                except (ValueError, UnicodeError):
                    payload = {'error_excerpt': raw[:2048].decode('utf8', errors='replace')}
            if route.api_key:
                payload = json.loads(json.dumps(payload).replace(route.api_key, '[REDACTED]'))
            record = {'http_status': code, 'content_type': content_type, 'body': payload,
                      'stream_complete': complete, 'usage_complete': usage_complete,
                      'error_type': type(error).__name__ if error else None}
            quota = 'insufficient_quota' in str(payload) or 'billing_hard_limit' in str(payload)
            transient = (code in TRANSIENT or error is not None) and not quota
            retry = transient and attempt < len(gateway.policy.backoff_seconds)
            delay = (gateway.policy.backoff_seconds[attempt] *
                     (1+random.random()*gateway.policy.jitter_fraction) if retry else 0)
            delay = max(delay, retry_after(response.headers.get('retry-after')) if response is not None else 0)
            state = ledger.snapshot(route.run_id)
            room = state['limits']['active_seconds']-state['active_elapsed_s']
            if retry and (delay > gateway.policy.max_wait_seconds or delay >= room):
                retry = False
            if retry:
                # Reserve before resending. The first call's normal reservation
                # already exists; every additional actual request needs its own.
                current, next_id = context['current'], 'retry-'+uuid.uuid4().hex
                ledger.settle(route.run_id, current, usage=usage, response=record, failed=True)
                context['failed'].append(current)
                # Time spent waiting, including suspend, stays charged.
                # Every resend needs a fresh post-wait budget reservation.
                context['current'] = None
                ledger.record(route.run_id, 'provider_retry_wait', {
                    'request_id': current, 'delay_s': delay, 'http_status': code})
                gateway.sleeper(delay)
                try:
                    ledger.reserve(route.run_id, next_id, context['reservation'],
                                   {**context['metadata'], 'retry_of': context['original'], 'retry_attempt': attempt+1})
                except ValueError as budget:
                    # Already settled, so prevent a conflicting final settlement.
                    context['current'] = None
                    ledger.record(route.run_id, 'provider_retry_budget_stopped', {'reason': str(budget)})
                    return httpx.Response(403, json={'error': str(budget), 'origin': 'repair-controller'})
                context['current'] = next_id
                if response is not None:
                    response.close()
                continue
            if code >= 400 or error:
                gateway.holds.hold(state['arm'], reason='PROVIDER_QUOTA_EXHAUSTED' if quota
                    else 'PROVIDER_RETRY_EXHAUSTED' if transient else 'PROVIDER_HTTP_FAILURE',
                    code=code, run_id=route.run_id, provider=code != 400)
            if error:
                context['final_failure'] = {'usage': usage, 'response': record}
                raise error
            return response
        raise RuntimeError('UNREACHABLE_RETRY_STATE')


class ResilientGateway(WireGateway):
    def __init__(self, ledger, root, *, policy=None, sleeper=time.sleep, transport=None, **kwargs):
        self.original_ledger, self.local = ledger, threading.local()
        self.policy, self.sleeper = policy or Policy(), sleeper
        self.holds = Holds(Path(ledger.path).parent)
        self.slots = {name: threading.BoundedSemaphore(getattr(self.policy, name+'_requests'))
                      for name in FAMILIES}
        self.retry_transport = _RetryTransport(self, transport or httpx.HTTPTransport())
        super().__init__(_RetryLedger(ledger, self.local), root, transport=self.retry_transport, **kwargs)

    def handle(self, handler):
        token, _, suffix = handler.path.lstrip('/').partition('/')
        route = self.routes.get(token)
        if route is None or suffix in {'questions', 'control/answer'}:
            return super().handle(handler)
        arm = self.original_ledger.snapshot(route.run_id)['arm']
        if arm in self.holds.groups():
            return self.reply(handler, 503, {'error': 'PROVIDER_GROUP_HELD', 'origin': 'repair-controller'})
        slot = self.slots[family(arm)]
        while not slot.acquire(timeout=.5):
            state = self.original_ledger.snapshot(route.run_id)
            if state['status'] != 'running' or state['active_elapsed_s'] >= state['limits']['active_seconds']:
                return self.reply(handler, 403, {'error': 'TIME_BUDGET_EXHAUSTED', 'origin': 'repair-controller'})
        if arm in self.holds.groups():
            slot.release()
            return self.reply(handler, 503, {'error': 'PROVIDER_GROUP_HELD', 'origin': 'repair-controller'})
        self.local.context = {'route': route}
        try:
            return super().handle(handler)
        finally:
            self.local.context = None
            slot.release()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.retry_transport.underlying.close()


def interface_fault(root, run_id):
    """Persist a group hold; only safety/environment faults stop the whole batch."""
    ledger = Ledger(Path(root)/'control.sqlite')
    calls = ledger.calls(run_id)
    if not calls or not calls[-1]['failed']:
        return False
    recovered = {identifier for e in ledger.events(run_id) if e['kind'] == 'provider_request_recovered'
                 for identifier in e['payload']['failed_request_ids']}
    last = calls[-1]
    if last['request_id'] in recovered:
        return False
    if any(e['kind'] == 'provider_retry_budget_stopped' for e in ledger.events(run_id)):
        return False
    response = last.get('response') or {}
    code = response.get('http_status')
    if response.get('error_type') or code is not None and (code >= 400 or code == 0):
        arm = ledger.snapshot(run_id)['arm']
        Holds(root).hold(arm, reason='PROVIDER_INTERFACE_FAILURE', code=code,
                         run_id=run_id, provider=code != 400)
    return False


def load_policy(root):
    path = Path(root)/'operations-policy.json'
    value = read_json(path) if path.is_file() else asdict(Policy())
    value['backoff_seconds'] = tuple(value['backoff_seconds'])
    return Policy(**value)


def install(root, *, policy=None, monkeypatch=None):
    """Scoped process extension: main-thread/Qwen source files remain untouched."""
    root, policy = Path(root).resolve(), policy or load_policy(root)
    alerts, holds = Alerts(root, desktop=policy.desktop_notifications and monkeypatch is None), Holds(root)
    original_held, original_order = batch._held_groups, batch._dispatch_order
    original_emit, original_control = batch._emit, batch._control
    original_common = batch.common_failure
    def set_attribute(owner, name, value):
        if monkeypatch is not None:
            monkeypatch.setattr(owner, name, value)
        else:
            setattr(owner, name, value)
    def held(db):
        return sorted(set(original_held(db)) |
                      {arm for row in Holds.records(db).values() for arm in row['groups']})
    def order(value, config, states):
        groups = set(holds.groups())
        ordered = [run for run in original_order(value, config, states) if states[run]['arm'] not in groups]
        pending = [s for s in states.values() if s['status'] not in TERMINAL]
        if groups and pending and not any(s['status'] in {'running', 'awaiting_user'} for s in pending):
            with closing(batch._database(root)) as db:
                all_held = held(db)
            if all(s['arm'] in all_held for s in pending):
                batch.pause(root)
        return ordered
    def fields_for(event, fields):
        if event == 'paused' and holds.groups() and fields.get('reason') in {
                'requested_between_tasks', 'HELD_GROUPS_REMAINING'}:
            fields = {**fields, 'reason': 'PROVIDER_GROUPS_HELD', 'held_groups': holds.groups()}
        return fields
    def emit(event, **fields):
        fields = fields_for(event, fields)
        alerts.emit(event, **{**fields, 'groups': fields.get('held_groups', [])})
        return original_emit(event, **fields)
    def control(path, state, **fields):
        fields = fields_for(state, fields)
        if state == 'attention':
            alerts.emit(state, **fields)
        return original_control(path, state, **fields)
    def common_failure(states):
        # Provider faults already have a persistent, provider-scoped hold.
        # Runtime/isolation/recovery failures retain the original global gate.
        isolated = set(holds.groups())
        old_faults = holds.isolated_runs()
        remaining = []
        for state in states:
            native = state.get('native', {}).get('result', {})
            code = str(native.get('error_code') or state.get('detail') or '')
            if ((state['arm'] in isolated or state['run_id'] in old_faults)
                    and code.startswith(('PROVIDER_', 'GATEWAY_'))):
                continue
            remaining.append(state)
        return original_common(remaining)
    set_attribute(batch, '_held_groups', held)
    set_attribute(batch, '_dispatch_order', order)
    set_attribute(batch, '_interface_fault', interface_fault)
    set_attribute(batch, '_emit', emit)
    set_attribute(batch, '_control', control)
    set_attribute(batch, 'common_failure', common_failure)
    set_attribute(batch, 'CLI', [sys.executable, '-m', 'scripts.ifc_repair.batch_resilience', 'worker'])
    set_attribute(carrier, 'WireGateway', lambda *args, **kwargs: ResilientGateway(*args, policy=policy, **kwargs))


def verify_operations(root):
    """Fail closed on stale policy, wrapper, test receipt or base admission."""
    root = Path(root)
    with closing(batch._database(root)) as db:
        selected = db.execute("SELECT value FROM batch_control WHERE key='operations-admission'").fetchone()
    if not selected:
        raise ValueError('CURRENT_OPERATIONS_ADMISSION_REQUIRED')
    ref = json.loads(selected[0])
    if sha256(Path(ref['path'])) != ref['sha256']:
        raise ValueError('OPERATIONS_ADMISSION_CHANGED')
    receipt = read_json(Path(ref['path']))
    if receipt.get('passed') is not True or receipt.get('module_sha256') != sha256(carrier.REPO/MODULE):
        raise ValueError('CURRENT_OPERATIONS_ADMISSION_REQUIRED')
    if receipt['policy_sha256'] != sha256(root/'operations-policy.json'):
        raise ValueError('OPERATIONS_POLICY_CHANGED')
    for ref in receipt['evidence']:
        if sha256(Path(ref['path'])) != ref['sha256']:
            raise ValueError('OPERATIONS_EVIDENCE_CHANGED')
    for path, digest in receipt['tests'].items():
        if sha256(carrier.REPO/path) != digest:
            raise ValueError('OPERATIONS_TESTS_CHANGED')
    runtime = read_json(root/'experiment.json')
    if str(Path(runtime['admission']).resolve()) != receipt['base_admission']['path']:
        raise ValueError('OPERATIONS_BASE_ADMISSION_CHANGED')
    if sha256(Path(runtime['admission'])) != receipt['base_admission']['sha256']:
        raise ValueError('OPERATIONS_BASE_ADMISSION_CHANGED')
    carrier.verify_admission(Path(runtime['admission']), runtime['configuration'])
    return receipt


def configure(root, *, policy=None):
    root, policy = Path(root), policy or Policy()
    with task_owner(root, 'batch-owner'):
        if any(s['status'] in {'running', 'awaiting_user'} for s in batch._states(root)):
            raise ValueError('OPERATIONS_CONFIG_REQUIRES_QUIESCENT_BATCH')
        path = root/'operations-policy.json'
        document = json.loads(encode(asdict(policy)))
        if path.exists() and read_json(path) != document:
            raise ValueError('OPERATIONS_POLICY_FROZEN')
        if not path.exists():
            write_json(path, document)
    return {'event': 'operations_configured', 'policy': str(path)}


def admit_operations(root, *, junit, log, native_receipt, revision):
    """Accept actual focused/native receipts without rewriting the base freeze."""
    if not revision or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in revision):
        raise ValueError('INVALID_OPERATIONS_REVISION')
    root, junit, log, native_receipt = map(Path, (root, junit, log, native_receipt))
    runtime = read_json(root/'experiment.json')
    carrier.verify_admission(Path(runtime['admission']), runtime['configuration'])
    suites = ET.parse(junit).getroot()
    cases = list(suites.iter('testcase'))
    if not cases or any(list(c.iter('failure'))+list(c.iter('error'))+list(c.iter('skipped')) for c in cases):
        raise ValueError('OPERATIONS_TESTS_NOT_PASSED')
    required = {'test_429_retry_after_recovers_and_every_attempt_is_accounted',
                'test_native_d_stream_is_forwarded_unchanged_after_transient_error',
                'test_dynamic_provider_hold_does_not_stop_other_groups',
                'test_hold_release_keeps_manual_holds_and_old_terminal_failure',
                 'test_alerts_are_quiet_normally_deduplicated_and_persistent',
                 'test_200_body_disconnect_recovers_and_charges_each_attempt',
                 'test_repeated_200_disconnect_only_holds_provider_after_all_retries',
                 'test_resilient_actual_linux_public_cli_retries_and_preserves_native_tools'}
    if not required <= {c.get('name') for c in cases}:
        raise ValueError('OPERATIONS_REQUIRED_TESTS_MISSING')
    native = read_json(native_receipt)
    if (native.get('all_passed') is not True or native.get('real_models_called') is not False
            or native.get('real_credentials_used') is not False or native.get('first_429_recovered') is not True
            or native.get('post_200_disconnect_recovered') is not True
            or native.get('operations_module_sha256') != sha256(carrier.REPO/MODULE)
            or set(native.get('tested_arms', [])) != {'A', 'D', 'E'}
            or native['runtime_bindings_before'] != native['runtime_bindings_after']
            or not native['timeout_stop']['quiescent']):
        raise ValueError('OPERATIONS_NATIVE_NOT_PASSED')
    for row in native['runs']:
        if row['status'] != 'submitted' or sha256(Path(row['artifact']['path'])) != row['artifact']['sha256']:
            raise ValueError('OPERATIONS_NATIVE_ARTIFACT_CHANGED')
    def reference(path):
        return {'path': str(Path(path).resolve()), 'sha256': sha256(Path(path))}
    files = ('tests/ifc_repair/test_batch_resilience.py', 'tests/ifc_repair/test_batch_resilience_native.py')
    receipt = {'schema_version': 'repair-batch-operations-admission/1.0', 'passed': True,
               'scope': 'Bounded transport retries, provider isolation, persisted notifications; no capability claim.',
               'module_sha256': sha256(carrier.REPO/MODULE),
               'policy_sha256': sha256(root/'operations-policy.json'),
               'base_admission': reference(runtime['admission']),
               'tests': {path: sha256(carrier.REPO/path) for path in files},
               'evidence': [reference(path) for path in (junit, log, native_receipt)]+
                           [native['operations_driver'], native['service_log']],
               'effective_after_terminal_count': batch.brief_status(root)['completed'], 'time': time.time()}
    destination = root/'admission'/('operations-'+revision+'.json')
    with task_owner(root, 'batch-owner'):
        if destination.exists():
            raise ValueError('OPERATIONS_ADMISSION_ALREADY_RECORDED')
        if any(s['status'] in {'running', 'awaiting_user'} for s in batch._states(root)):
            raise ValueError('OPERATIONS_ADMISSION_REQUIRES_QUIESCENT_BATCH')
        write_json(destination, receipt)
        ledger = Ledger(root/'control.sqlite')
        with ledger.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                       ('operations-admission', encode(reference(destination))))
    return {'event': 'operations_admitted', 'receipt': str(destination)}


def process_alive(pid):
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x1000, False, int(pid))
        if not handle:
            return ctypes.get_last_error() == 5  # Unknown access is not proof of exit.
        try:
            status = ctypes.c_ulong()
            return bool(kernel.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(status))) and status.value == 259
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def watchdog(root):
    """Summary-only unexpected-owner check; never kill or redispatch tasks."""
    with closing(batch._database(root)) as db:
        row = db.execute("SELECT value FROM batch_control WHERE key='controller'").fetchone()
    controller = json.loads(row[0]) if row else {}
    if controller.get('state') in {'running', 'draining'} and not process_alive(controller.get('pid', 0)):
        Alerts(root).emit('attention', reason='CONTROLLER_NOT_RUNNING_CHECKPOINT_RETAINED')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or '--root' not in argv:
        raise ValueError('Usage: batch_resilience COMMAND --root PATH [batch options]')
    root = Path(argv[argv.index('--root')+1]).resolve()
    command = argv[0]
    if command == 'configure':
        print(json.dumps(configure(root), ensure_ascii=False))
        return 0
    if command == 'admit-operations':
        parser = argparse.ArgumentParser()
        parser.add_argument('command'); parser.add_argument('--root', type=Path, required=True)
        for option in ('junit', 'log', 'native-receipt'):
            parser.add_argument('--'+option, type=Path, required=True)
        parser.add_argument('--revision', required=True)
        args = parser.parse_args(argv)
        print(json.dumps(admit_operations(args.root, junit=args.junit, log=args.log,
              native_receipt=args.native_receipt, revision=args.revision), ensure_ascii=False))
        return 0
    if command == 'alerts':
        install(root)
        watchdog(root)
        alerts = Alerts(root).pending(acknowledge='--acknowledge' in argv)
        print(json.dumps({'alerts': alerts, 'summary': batch.brief_status(root) if alerts else None}, ensure_ascii=False))
        return 0
    if command == 'prepare':
        return batch.main(argv)  # Preparing public inputs needs no runtime hooks.
    if command == 'release-provider':
        parser = argparse.ArgumentParser()
        parser.add_argument('command'); parser.add_argument('--root', type=Path, required=True)
        parser.add_argument('--groups', nargs='+', choices=list('ABCDEFG'), required=True)
        parser.add_argument('--reason', required=True)
        args = parser.parse_args(argv)
        with task_owner(root, 'provider-hold-change'):
            Holds(root).release(args.groups, reason=args.reason)
        print(json.dumps({'event': 'provider_released', 'groups': args.groups}))
        return 0
    if command in {'run', 'resume', 'worker'}:
        value = (batch.plan(root) if (root/'batch.json').is_file()
                 else read_json(root/'experiment.json'))
        if value['mode'] == 'live':
            verify_operations(root)
    install(root)
    if command == 'worker':
        sys.argv = [sys.argv[0], *argv[1:]]
        carrier.main()
        return 0
    return batch.main(argv)


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf8')
        raise SystemExit(main())
    except (ValueError, KeyError, OSError) as error:
        if '--root' in sys.argv:
            try:
                Alerts(Path(sys.argv[sys.argv.index('--root')+1])).emit('attention',
                    reason=type(error).__name__+': '+str(error)[:240])
            except (ValueError, OSError):
                pass
        print(json.dumps({'event': 'attention', 'reason': type(error).__name__+': '+str(error)[:240]}, ensure_ascii=False))
        raise SystemExit(2)
