"""Join the parent-owned Windows Job before starting any requested command."""
import ctypes
from ctypes import wintypes as w
import json
import subprocess
import sys


def main():
    api = ctypes.WinDLL('kernel32', use_last_error=True)
    api.OpenJobObjectW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
    api.OpenJobObjectW.restype = w.HANDLE
    api.GetCurrentProcess.restype = w.HANDLE
    api.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
    api.CloseHandle.argtypes = [w.HANDLE]
    job = api.OpenJobObjectW(1, False, sys.argv[1])
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not api.AssignProcessToJobObject(job, api.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        api.CloseHandle(job)
    argv = json.loads(sys.stdin.buffer.read().decode('utf-8'))
    return subprocess.call(argv, stdin=subprocess.DEVNULL)


if __name__ == '__main__':
    raise SystemExit(main())
