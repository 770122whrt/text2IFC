"""OS ownership locks; short shared service transitions may wait for a slot."""
from contextlib import contextmanager
from pathlib import Path
import os
import hashlib
import time
from .ledger import identifier


@contextmanager
def task_owner(root,run_id, *, wait_seconds=0):
    if wait_seconds < 0:
        raise ValueError('INVALID_OWNER_WAIT')
    folder=Path(root)/'controller-locks';folder.mkdir(exist_ok=True)
    key=hashlib.sha256(identifier(run_id).encode()).hexdigest()
    with (folder/(key+'.lock')).open('a+b') as stream:
        stream.seek(0,2)
        if not stream.tell():stream.write(b'0');stream.flush()
        stream.seek(0)
        deadline = time.monotonic() + wait_seconds
        while True:
            try:
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except OSError as error:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ValueError('RUN_CONTROLLER_ALREADY_ACTIVE') from error
                time.sleep(min(.05, remaining))
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream,fcntl.LOCK_UN)
