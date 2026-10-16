"""Local API metadata; native RunStore remains the sole Repair outcome authority."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import sqlite3
import uuid

from .contracts import WebError


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(prefix):
    return prefix+'-'+uuid.uuid4().hex


def json_text(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.tmp')
    try:
        temporary.write_text(json_text(value), encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class Store:
    def __init__(self, root):
        root = Path(root)
        if root.is_symlink():
            raise WebError('STORE_LINK_FORBIDDEN')
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ('inputs', 'requests', 'native'):
            (self.root/name).mkdir(exist_ok=True)
        self.database = self.root/'web.sqlite'
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY, run_id TEXT UNIQUE NOT NULL,
                prepared_id TEXT UNIQUE NOT NULL, client_key TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL, busy INTEGER NOT NULL DEFAULT 0,
                result TEXT, error_code TEXT, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS answers (
                task_id TEXT NOT NULL, client_key TEXT NOT NULL, payload TEXT NOT NULL,
                PRIMARY KEY(task_id,client_key));
            CREATE TABLE IF NOT EXISTS live_task_slots (
                approval_id TEXT NOT NULL, task_id TEXT UNIQUE NOT NULL,
                PRIMARY KEY(approval_id,task_id));
            CREATE TABLE IF NOT EXISTS activity (
                seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                payload TEXT NOT NULL, created_at TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def file(self, directory, ident, suffix):
        prefix = {'inputs':'input','requests':'request'}[directory]
        if not re.fullmatch(prefix+r'-[a-f0-9]{32}', ident):
            raise WebError('RESOURCE_NOT_FOUND', 404)
        path = self.root/directory/(ident if directory=='inputs' else ident+'.json')
        if directory == 'inputs':
            path = path/suffix
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != self.root.parent):
            raise WebError('RESOURCE_LINK_FORBIDDEN', 409)
        if not path.is_file():
            raise WebError('RESOURCE_NOT_FOUND', 404)
        return path

    def input(self, ident):
        return json.loads(self.file('inputs',ident,'metadata.json').read_text(encoding='utf-8'))

    def source(self, ident):
        return self.file('inputs',ident,'source.ifc')

    def prepared(self, ident):
        return json.loads(self.file('requests',ident,'').read_text(encoding='utf-8'))

    def task(self, task_id):
        if not re.fullmatch(r'task-[a-f0-9]{32}', task_id):
            raise WebError('TASK_NOT_FOUND', 404)
        with self.connect() as db:
            row = db.execute('SELECT * FROM tasks WHERE task_id=?',(task_id,)).fetchone()
        if row is None:
            raise WebError('TASK_NOT_FOUND',404)
        return dict(row)

    def claim_start(self, prepared_id, client_key, *, task_limit=None):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            # Check the key binding first; an OR query could choose the other row
            # when two existing tasks match different halves of the condition.
            row = db.execute('SELECT * FROM tasks WHERE client_key=?',(client_key,)).fetchone()
            if row is not None and row['prepared_id'] != prepared_id:
                raise WebError('IDEMPOTENCY_CONFLICT',409)
            if row is None:
                row = db.execute('SELECT * FROM tasks WHERE prepared_id=?',(prepared_id,)).fetchone()
            if row:
                return dict(row), False
            if task_limit is not None:
                approval_id,maximum=task_limit
                used=db.execute('SELECT count(*) FROM live_task_slots WHERE approval_id=?',(approval_id,)).fetchone()[0]
                if used>=maximum:raise WebError('LIVE_TASK_LIMIT',429)
            task_id,run_id = identity('task'),identity('repair')
            db.execute('INSERT INTO tasks VALUES (?,?,?,?,?,1,NULL,NULL,?)',(task_id,run_id,prepared_id,client_key,'queued',now()))
            if task_limit is not None:
                db.execute('INSERT INTO live_task_slots VALUES (?,?)',(approval_id,task_id))
        return self.task(task_id), True

    def claim_answer(self, task_id, client_key, payload):
        encoded = json_text(payload)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT payload FROM answers WHERE task_id=? AND client_key=?',(task_id,client_key)).fetchone()
            if row:
                if row['payload'] != encoded:
                    raise WebError('IDEMPOTENCY_CONFLICT',409)
                return False
            task = db.execute('SELECT busy,status FROM tasks WHERE task_id=?',(task_id,)).fetchone()
            if task is None:
                raise WebError('TASK_NOT_FOUND',404)
            if task['busy'] or task['status'] != 'clarification_required':
                raise WebError('TASK_NOT_WAITING',409)
            db.execute('INSERT INTO answers VALUES (?,?,?)',(task_id,client_key,encoded))
            db.execute("UPDATE tasks SET busy=1,status='queued',error_code=NULL WHERE task_id=?",(task_id,))
        return True

    def prior_answer(self, task_id, client_key, payload):
        with self.connect() as db:
            row = db.execute('SELECT payload FROM answers WHERE task_id=? AND client_key=?',(task_id,client_key)).fetchone()
        if row is None:
            return False
        if row['payload'] != json_text(payload):
            raise WebError('IDEMPOTENCY_CONFLICT',409)
        return True

    def finish(self, task_id, *, result=None, error_code=None):
        status = result['status'] if result is not None else 'interrupted'
        with self.connect() as db:
            db.execute('UPDATE tasks SET status=?,busy=0,result=?,error_code=? WHERE task_id=?',
                       (status, json_text(result) if result is not None else None,error_code,task_id))

    def record_activity(self, task_id, payload):
        with self.connect() as db:
            db.execute('INSERT INTO activity(task_id,payload,created_at) VALUES (?,?,?)',(task_id,json_text(payload),now()))

    def activities(self, task_id, after=-1):
        with self.connect() as db:
            rows=db.execute('SELECT * FROM activity WHERE task_id=? AND seq>? ORDER BY seq LIMIT 500',(task_id,after)).fetchall()
        return [{'activity_seq':r['seq'],'occurred_at':r['created_at'],**json.loads(r['payload'])} for r in rows]

    def mark_interrupted(self):
        # On single-service startup only. Native terminal outcomes are recovered on read.
        with self.connect() as db:
            db.execute("UPDATE tasks SET busy=0,status='interrupted',error_code='WORKER_INTERRUPTED' WHERE busy=1")
