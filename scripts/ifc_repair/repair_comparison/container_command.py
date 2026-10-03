"""One generic command in a container; no domain helpers or provider access."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time


def main():
    request = json.load(sys.stdin)
    argv, timeout = request['argv'], request['timeout_s']
    if not isinstance(argv,list) or not argv or any(not isinstance(v,str) or '\0' in v for v in argv):
        raise ValueError('INVALID_ARGV')
    began=time.monotonic()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:process=subprocess.Popen(argv,cwd='/workspace',stdout=out,stderr=err,start_new_session=True)
        except OSError as error:
            print(json.dumps({'exit_code':127,'stdout':'','stderr':str(error),'output_truncated':False,
                'timed_out':False,'duration_s':time.monotonic()-began}))
            return
        timed_out=False
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out=True
        finally:
            try: os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait(timeout=5)
        streams=[]
        for handle in (out,err):
            handle.seek(0)
            raw=handle.read(1024*1024+1)
            streams.append((raw[:1024*1024].decode('utf8',errors='replace'),len(raw)>1024*1024))
    print(json.dumps({'exit_code':process.returncode,'stdout':streams[0][0],'stderr':streams[1][0],
        'output_truncated':streams[0][1] or streams[1][1], 'timed_out':timed_out,
        'duration_s':time.monotonic()-began},ensure_ascii=False))


if __name__=='__main__':
    main()
