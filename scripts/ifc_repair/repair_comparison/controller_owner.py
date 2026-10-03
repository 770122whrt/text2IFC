"""Nonblocking OS lock: one controller may execute a task at a time."""
from contextlib import contextmanager
from pathlib import Path
import os
import hashlib
from .ledger import identifier


@contextmanager
def task_owner(root,run_id):
    folder=Path(root)/'controller-locks';folder.mkdir(exist_ok=True)
    key=hashlib.sha256(identifier(run_id).encode()).hexdigest()
    with (folder/(key+'.lock')).open('a+b') as stream:
        stream.seek(0,2)
        if not stream.tell():stream.write(b'0');stream.flush()
        stream.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as error:
            raise ValueError('RUN_CONTROLLER_ALREADY_ACTIVE') from error
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream,fcntl.LOCK_UN)
