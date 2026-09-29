"""Lifetime control for trusted offline scripts, NOT a filesystem/network sandbox.

Windows descendants join a Job before the requested command is started.
https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import uuid


class WindowsJob:
    def __init__(self):
        self.api = ctypes.WinDLL('kernel32', use_last_error=True)
        self.api.CreateJobObjectW.argtypes = [ctypes.c_void_p, w.LPCWSTR]
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.api.SetInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD]
        self.api.QueryInformationJobObject.argtypes = [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p]
        self.api.TerminateJobObject.argtypes = [w.HANDLE, w.UINT]
        self.api.CloseHandle.argtypes = [w.HANDLE]
        class Basic(ctypes.Structure):
            _fields_ = [('process_time', ctypes.c_int64), ('job_time', ctypes.c_int64), ('flags', w.DWORD),
                        ('min_ws', ctypes.c_size_t), ('max_ws', ctypes.c_size_t), ('active_limit', w.DWORD),
                        ('affinity', ctypes.c_size_t), ('priority', w.DWORD), ('scheduling', w.DWORD)]
        class Extended(ctypes.Structure):
            _fields_ = [('basic', Basic), ('io', ctypes.c_uint64 * 6), ('memory', ctypes.c_size_t * 4)]
        self.name = 'text2ifc-offline-' + uuid.uuid4().hex
        self.handle = self.api.CreateJobObjectW(None, self.name)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise ctypes.WinError(ctypes.get_last_error())

    def stop(self):
        if not self.api.TerminateJobObject(self.handle, 1):
            raise ctypes.WinError(ctypes.get_last_error())
        class Accounting(ctypes.Structure):
            _fields_ = [('times', ctypes.c_int64 * 4), ('faults', w.DWORD), ('total', w.DWORD), ('active', w.DWORD), ('terminated', w.DWORD)]
        deadline = time.monotonic() + 3
        while True:
            info = Accounting()
            if not self.api.QueryInformationJobObject(self.handle, 1, ctypes.byref(info), ctypes.sizeof(info), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if info.active == 0:
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(.02)

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def run_offline(argv, cwd: Path, timeout_s: float, *, output_limit=65536):
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or '\0' in arg for arg in argv):
        raise ValueError('INVALID_COMMAND_ARGUMENTS')
    # Explicit allowlist: no credentials or inherited provider configuration.
    env = {key: value for key, value in os.environ.items() if key.upper() in {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATH', 'PATHEXT', 'TEMP', 'TMP'}}
    env.update({'PYTHONIOENCODING': 'utf-8', 'PYTHONUTF8': '1'})
    started, timed_out, quiescent = time.monotonic(), False, False
    job = WindowsJob() if os.name == 'nt' else None
    try:
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            if job:
                command = [sys.executable, '-I', str(Path(__file__).with_name('_command_worker.py')), job.name]
            else:
                command = argv
            proc = subprocess.Popen(command, cwd=cwd, env=env, stdin=subprocess.PIPE if job else subprocess.DEVNULL,
                                    stdout=stdout, stderr=stderr, start_new_session=not bool(job),
                                    creationflags=subprocess.CREATE_NO_WINDOW if job else 0)
            try:
                proc.communicate(json.dumps(argv).encode('utf-8') if job else None, timeout=timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                if job:
                    quiescent = job.stop()
                    if proc.poll() is None:  # Worker may have timed out before joining the job.
                        proc.kill()
                    proc.wait(timeout=3)
                else:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait(timeout=3)
                    quiescent = True  # Trusted offline process group, not adversarial containment.
            streams = []
            truncated = []
            for stream in (stdout, stderr):
                stream.seek(0)
                value = stream.read(output_limit + 1)
                streams.append(value[:output_limit].decode('utf-8', errors='replace'))
                truncated.append(len(value) > output_limit)
            return {'exit_code': proc.returncode, 'stdout': streams[0], 'stderr': streams[1],
                    'stdout_truncated': truncated[0], 'stderr_truncated': truncated[1],
                    'elapsed_s': time.monotonic() - started, 'timed_out': timed_out, 'quiescent': quiescent,
                    'scope': 'trusted offline command; host filesystem/network isolation NOT established'}
    finally:
        if job:
            job.close()
