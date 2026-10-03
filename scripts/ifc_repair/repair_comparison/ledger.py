"""Transactional experiment-side task ledger. No Provider/network transport."""
from __future__ import annotations

from contextlib import closing, contextmanager
import json
from pathlib import Path
import re
import sqlite3
import time

from .budget import normalize_usage, positive, usage_summary, validate_budget
from .contracts import safe_path

TERMINAL = {'submitted', 'no_output', 'budget_exhausted', 'cancelled', 'runtime_error', 'unsupported'}


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}', value):
        raise ValueError('INVALID_IDENTIFIER')
    return value


class Ledger:
    def __init__(self, path: Path, *, clock=time.time):
        self.path, self.clock = safe_path(Path(path)), clock
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, state TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, event_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, at REAL NOT NULL, UNIQUE(run_id,event_id));
                CREATE TABLE IF NOT EXISTS calls(run_id TEXT NOT NULL, request_id TEXT NOT NULL, reservation INTEGER NOT NULL, metadata TEXT NOT NULL, state TEXT NOT NULL, usage TEXT, response TEXT, failed INTEGER NOT NULL DEFAULT 0, UNIQUE(run_id,request_id));
            ''')

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        return db

    @contextmanager
    def transaction(self):
        db = self._connect()
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _load(db, run_id):
        row = db.execute('SELECT state FROM runs WHERE run_id=?', (run_id,)).fetchone()
        if not row:
            raise ValueError('RUN_NOT_FOUND')
        return json.loads(row['state'])

    @staticmethod
    def _save(db, state):
        db.execute('UPDATE runs SET state=? WHERE run_id=?', (encode(state), state['run_id']))

    def _tick(self, state):
        now = float(self.clock())
        if state['checkpoint'] is not None:
            delta = now - state['checkpoint']
            if delta < 0:
                raise ValueError('CLOCK_WENT_BACKWARDS')
            if state['status'] == 'running':
                state['active_elapsed_s'] += delta
            elif state['status'] == 'awaiting_user':
                state['human_wait_s'] += delta
        state['checkpoint'] = now
        return now

    def _event(self, db, run_id, kind, payload, event_id=None):
        if event_id is None:
            import uuid
            event_id = uuid.uuid4().hex
        old = db.execute('SELECT kind,payload FROM events WHERE run_id=? AND event_id=?', (run_id, event_id)).fetchone()
        if old:
            if old['kind'] != kind or old['payload'] != encode(payload):
                raise ValueError('EVENT_CONFLICT')
            return False
        db.execute('INSERT INTO events(run_id,event_id,kind,payload,at) VALUES(?,?,?,?,?)', (run_id, event_id, kind, encode(payload), self.clock()))
        return True

    @staticmethod
    def _running(state):
        if state['status'] in TERMINAL:
            raise ValueError('TERMINAL_IMMUTABLE')
        if state['status'] != 'running':
            raise ValueError('RUN_NOT_ACTIVE')

    @staticmethod
    def _other_active(db, run_id):
        if any(json.loads(row['state'])['status'] == 'running' for row in db.execute('SELECT state FROM runs WHERE run_id<>?', (run_id,))):
            raise ValueError('OTHER_ACTIVE_TASK')

    @staticmethod
    def _quiescent(db, state):
        inflight = db.execute("SELECT COUNT(*) FROM calls WHERE run_id=? AND state='inflight'", (state['run_id'],)).fetchone()[0]
        if inflight or state['activities']:
            raise ValueError('INFLIGHT_WORK_PREVENTS_PAUSE_OR_TERMINATION')

    def create(self, run_id, *, case_id, arm, budget, metadata=None, mode='offline_development'):
        identifier(run_id)
        identifier(case_id)
        if arm not in {'A', 'B', 'C', 'D'}:
            raise ValueError('INVALID_ARM')
        if mode not in {'offline_development','real_runtime_fake_model','live_development'}:
            raise ValueError('INVALID_EVIDENCE_MODE')
        validate_budget(budget)
        with self.transaction() as db:
            for row in db.execute('SELECT state FROM runs'):
                other = json.loads(row['state'])
                if other['case_id'] == case_id:
                    if other['budget'] != budget:
                        raise ValueError('UNEQUAL_CASE_BUDGET')
                    if other['arm'] == arm:
                        raise ValueError('CASE_ARM_ALREADY_REGISTERED')
            state = {'run_id': run_id, 'case_id': case_id, 'arm': arm, 'mode': mode,
                     'status': 'ready', 'budget': budget, 'extensions_used': [], 'question': None,
                     'activities': [], 'metadata': metadata or {}, 'artifact': None, 'native': {},
                     'started': None, 'ended': None, 'checkpoint': None,
                     'active_elapsed_s': 0.0, 'human_wait_s': 0.0}
            db.execute('INSERT INTO runs VALUES(?,?)', (run_id, encode(state)))
            self._event(db, run_id, 'created', {'case_id': case_id, 'arm': arm, 'evidence_class': mode})
        return self.snapshot(run_id)

    def start(self, run_id):
        with self.transaction() as db:
            state = self._load(db, run_id)
            if state['status'] != 'ready':
                raise ValueError('RUN_ALREADY_STARTED')
            self._other_active(db, run_id)
            state['started'] = self._tick(state)
            state['status'] = 'running'
            self._save(db, state)
            self._event(db, run_id, 'started', {})
        return self.snapshot(run_id)

    @staticmethod
    def limits(state):
        profile = state['budget']
        rules = [r for r in profile['extensions'] if r['id'] in state['extensions_used']]
        return {'tokens': profile['tokens'] + sum(r['tokens'] for r in rules), 'calls': profile['calls'],
                'active_seconds': profile['active_seconds'] + sum(r['active_seconds'] for r in rules), 'tool_seconds': profile['tool_seconds']}

    @staticmethod
    def _normalized_usage(usage, metadata, response):
        protocol = (metadata or {}).get('wire_protocol', 'chat')
        complete = True
        if protocol == 'messages':
            record = response if isinstance(response, dict) else {}
            complete = record.get('usage_complete', record.get('stream_complete')) is True
        return normalize_usage(usage, protocol=protocol, complete=complete)

    @staticmethod
    def _calls(db, run_id):
        result = []
        for row in db.execute('SELECT * FROM calls WHERE run_id=? ORDER BY rowid', (run_id,)):
            call = dict(row)
            for key in ('metadata', 'usage', 'response'):
                call[key] = json.loads(call[key]) if call[key] is not None else None
            call['normalized_usage'] = Ledger._normalized_usage(call['usage'], call['metadata'], call['response']) if call['state'] != 'inflight' else None
            result.append(call)
        return result

    def calls(self, run_id):
        with closing(self._connect()) as db:
            return self._calls(db, run_id)

    def snapshot(self, run_id):
        with closing(self._connect()) as db:
            state = self._load(db, run_id)
            self._tick(state)
            state['limits'] = self.limits(state)
            state['usage'] = usage_summary(self._calls(db, run_id), state['limits']['tokens'])
            end = state['ended'] if state['ended'] is not None else self.clock()
            state['wall_elapsed_s'] = 0.0 if state['started'] is None else end - state['started']
            state['time_accounting'] = 'wall clock; interrupted running intervals remain charged'
            return state

    def reserve(self, run_id, request_id, upper_bound, metadata=None):
        identifier(request_id)
        if not positive(upper_bound, integer=True):
            raise ValueError('INVALID_RESERVATION')
        with self.transaction() as db:
            state = self._load(db, run_id)
            self._running(state)
            self._tick(state)
            limits = self.limits(state)
            calls = self._calls(db, run_id)
            if any(c['request_id'] == request_id for c in calls):
                raise ValueError('REQUEST_ALREADY_RESERVED_DO_NOT_REDISPATCH')
            if state['active_elapsed_s'] >= limits['active_seconds']:
                raise ValueError('TIME_BUDGET_EXHAUSTED')
            usage = usage_summary(calls, limits['tokens'])
            if usage['known_total_tokens'] + usage['reserved_tokens'] + upper_bound > limits['tokens']:
                raise ValueError('TOKEN_BUDGET_EXHAUSTED')
            if len(calls) >= limits['calls']:
                raise ValueError('CALL_BUDGET_EXHAUSTED')
            db.execute('INSERT INTO calls(run_id,request_id,reservation,metadata,state) VALUES(?,?,?,?,?)', (run_id, request_id, upper_bound, encode(metadata or {}), 'inflight'))
            self._save(db, state)
            self._event(db, run_id, 'request_reserved', {'request_id': request_id, 'upper_bound': upper_bound})

    def settle(self, run_id, request_id, *, usage, response, failed=False):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM calls WHERE run_id=? AND request_id=?', (run_id, request_id)).fetchone()
            if not row:
                raise ValueError('REQUEST_NOT_RESERVED')
            if row['state'] != 'inflight':
                if row['usage'] == encode(usage) and row['response'] == encode(response) and bool(row['failed']) == failed:
                    return
                raise ValueError('SETTLEMENT_CONFLICT')
            state = self._load(db, run_id)
            self._running(state)
            self._tick(state)
            db.execute('UPDATE calls SET state=?,usage=?,response=?,failed=? WHERE run_id=? AND request_id=?', ('failed' if failed else 'completed', encode(usage), encode(response), int(failed), run_id, request_id))
            self._save(db, state)
            known = self._normalized_usage(usage, json.loads(row['metadata']), response) is not None
            self._event(db, run_id, 'request_settled', {'request_id': request_id, 'failed': failed, 'usage_known': known})

    def activity(self, run_id, activity_id, *, begin):
        identifier(activity_id)
        with self.transaction() as db:
            state = self._load(db, run_id)
            self._running(state)
            self._tick(state)
            if begin:
                if activity_id in state['activities']:
                    raise ValueError('ACTIVITY_ALREADY_ACTIVE')
                state['activities'].append(activity_id)
            else:
                state['activities'].remove(activity_id)
            self._save(db, state)
            self._event(db, run_id, 'activity_started' if begin else 'activity_stopped', {'activity_id': activity_id})

    def ask(self, run_id, *, question_id, text, binding=None):
        identifier(question_id)
        if not isinstance(text, str) or not text.strip():
            raise ValueError('EMPTY_QUESTION')
        with self.transaction() as db:
            state = self._load(db, run_id)
            self._running(state)
            self._quiescent(db, state)
            self._tick(state)
            state['question'] = {'question_id': question_id, 'text': text, 'binding': binding or {}}
            self._event(db, run_id, 'question', state['question'], 'question:' + question_id)
            state['status'] = 'awaiting_user'
            self._save(db, state)
        return self.snapshot(run_id)

    def answer(self, run_id, *, question_id, text, event_id, requested_fact_ids=(), answered_fact_ids=(), native_answer=None):
        payload = {'question_id': question_id, 'text': text, 'requested_fact_ids': list(requested_fact_ids), 'answered_fact_ids': list(answered_fact_ids), 'native_answer': native_answer}
        if not isinstance(text, str) or not text.strip():
            raise ValueError('EMPTY_ANSWER')
        if not set(answered_fact_ids).issubset(requested_fact_ids):
            raise ValueError('UNASKED_FACT_NOT_ALLOWED')
        with self.transaction() as db:
            existing = db.execute('SELECT payload FROM events WHERE run_id=? AND event_id=?', (run_id, event_id)).fetchone()
            if existing:
                if existing['payload'] != encode(payload):
                    raise ValueError('ANSWER_CONFLICT')
                return self._load(db, run_id)
            state = self._load(db, run_id)
            if state['status'] != 'awaiting_user' or state['question']['question_id'] != question_id:
                raise ValueError('QUESTION_BINDING_STALE')
            self._other_active(db, run_id)
            self._tick(state)
            self._event(db, run_id, 'answer', payload, event_id)
            state['status'], state['question'] = 'running', None
            self._save(db, state)
        return self.snapshot(run_id)

    def extend(self, run_id, rule_id):
        with self.transaction() as db:
            state = self._load(db, run_id)
            self._running(state)
            rule = next((r for r in state['budget']['extensions'] if r['id'] == rule_id), None)
            if rule is None or rule_id in state['extensions_used']:
                raise ValueError('EXTENSION_NOT_AVAILABLE')
            if len(self._calls(db, run_id)) < rule['min_calls']:
                raise ValueError('EXTENSION_TRIGGER_NOT_MET')
            state['extensions_used'].append(rule_id)
            self._save(db, state)
            self._event(db, run_id, 'budget_extended', rule)
        return self.snapshot(run_id)

    def finish(self, run_id, status, *, artifact=None, detail=None):
        if status not in TERMINAL or (status == 'submitted') != (artifact is not None):
            raise ValueError('INVALID_TERMINAL')
        with self.transaction() as db:
            state = self._load(db, run_id)
            if state['status'] in TERMINAL:
                if state['status'] == status and state['artifact'] == artifact:
                    return self.snapshot(run_id)
                raise ValueError('TERMINAL_IMMUTABLE')
            self._quiescent(db, state)
            state['ended'] = self._tick(state)
            state['status'], state['artifact'] = status, artifact
            self._save(db, state)
            self._event(db, run_id, 'terminal', {'status': status, 'artifact': artifact, 'detail': detail})
        return self.snapshot(run_id)

    def record(self, run_id, kind, payload, *, event_id=None):
        with self.transaction() as db:
            self._load(db, run_id)
            return self._event(db, run_id, kind, payload, event_id)

    def set_native(self, run_id, native):
        with self.transaction() as db:
            state = self._load(db, run_id)
            self._running(state)
            state['native'] = native
            self._save(db, state)

    def events(self, run_id):
        with closing(self._connect()) as db:
            return [{**dict(row), 'payload': json.loads(row['payload'])} for row in db.execute('SELECT * FROM events WHERE run_id=? ORDER BY seq', (run_id,))]
