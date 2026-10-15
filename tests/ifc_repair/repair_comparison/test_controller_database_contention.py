"""Controller waits for short writer contention without replaying task work."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import sqlite3
import threading
import time

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.ledger import Ledger


@pytest.fixture
def short_database_wait(monkeypatch):
    connect = Ledger._connect

    def short_connect(self):
        db = connect(self)
        db.execute('PRAGMA busy_timeout=10')
        return db

    monkeypatch.setattr(Ledger, '_connect', short_connect)
    if hasattr(batch, 'ControllerLedger'):
        monkeypatch.setattr(batch.ControllerLedger, 'LOCK_WAIT_SECONDS', .5)


@pytest.mark.parametrize('journal', ['delete', 'wal'])
def test_four_controller_writers_wait_then_commit_once(tmp_path, short_database_wait, journal):
    ledger = Ledger(tmp_path/'control.sqlite')
    batch._control(tmp_path, 'paused')
    with closing(sqlite3.connect(ledger.path, isolation_level=None)) as owner:
        owner.execute('PRAGMA journal_mode='+journal)
        owner.execute('BEGIN IMMEDIATE')
        started = threading.Barrier(5)

        def update(index):
            started.wait(timeout=5)
            return batch._control(tmp_path, 'running', active_count=index)

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(update, index) for index in range(4)]
            started.wait(timeout=5)
            time.sleep(.1)
            owner.commit()
            for future in futures:
                future.result(timeout=3)
    with closing(sqlite3.connect(ledger.path)) as db:
        assert db.execute("SELECT count(*) FROM batch_control WHERE key='controller'").fetchone()[0] == 1
        assert db.execute('SELECT count(*) FROM calls').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM events').fetchone()[0] == 0


def test_persistent_writer_still_fails_closed(tmp_path, short_database_wait):
    ledger = Ledger(tmp_path/'control.sqlite')
    batch._control(tmp_path, 'paused')
    with closing(sqlite3.connect(ledger.path, isolation_level=None)) as owner:
        owner.execute('BEGIN IMMEDIATE')
        started = time.monotonic()
        with pytest.raises(sqlite3.OperationalError, match='locked'):
            batch._control(tmp_path, 'running')
        assert time.monotonic()-started < 1.5
        owner.rollback()
    with closing(sqlite3.connect(ledger.path)) as db:
        assert 'paused' in db.execute("SELECT value FROM batch_control WHERE key='controller'").fetchone()[0]


def test_authorization_is_not_replayed_or_replaced_after_contention(tmp_path, short_database_wait):
    Ledger(tmp_path/'control.sqlite')
    batch._property_authorization(tmp_path, {'sha256': 'original'}, grant=True)
    with pytest.raises(ValueError, match='PROPERTY_AUTHORIZATION_BATCH_CHANGED'):
        batch._property_authorization(tmp_path, {'sha256': 'different'}, grant=True)
    assert batch._property_authorization(tmp_path, {'sha256': 'original'})['batch_sha256'] == 'original'
