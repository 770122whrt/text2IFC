"""Read-only availability check for the six approved Git LFS archives.

Uses the configured Git credential helper in memory, never logging credentials,
download URLs or response headers. Reads one byte per object; this is not a new
full-download integrity check. Only sanitized outcomes are saved.
"""
from pathlib import Path
from datetime import datetime, timezone
import base64
import json
import os
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
INDEX = ROOT / 'dataset/processed/experiments/zcode-history-20260913/recovery-index.json'
REPOSITORY = 'https://github.com/770122whrt/text2IFC.git'


def main():
    output = REPORT / 'remote-availability.json'
    if output.exists():
        raise ValueError('Keep prior availability evidence; use a separate attempt')
    record = {'checked_at': datetime.now(timezone.utc).isoformat(), 'repository': REPOSITORY,
              'scope': 'LFS download batch plus a one-byte read per object; not full remote hashing',
              'results': [], 'status': 'failed'}
    try:
        data = json.loads(INDEX.read_text(encoding='utf-8'))
        entries = [r for r in data['entries'] if 'lfs_oid' in r]
        if len(entries) != 6 or data['remote'] != REPOSITORY:
            raise ValueError('Unexpected requested archive set')
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
        completed = subprocess.run(['git', 'credential', 'fill'], input=f'url={REPOSITORY}\n\n',
                                   text=True, capture_output=True, cwd=ROOT, env=env, timeout=30)
        if completed.returncode:
            raise RuntimeError('Git credential helper failed')
        values = dict(line.split('=', 1) for line in completed.stdout.splitlines() if '=' in line)
        basic = base64.b64encode(f"{values['username']}:{values['password']}".encode()).decode()
        payload = {'operation': 'download', 'transfers': ['basic'],
                   'objects': [{'oid': r['lfs_oid'], 'size': r['bytes']} for r in entries]}
        request = Request(REPOSITORY + '/info/lfs/objects/batch',
                          data=json.dumps(payload).encode(), method='POST',
                          headers={'Authorization': 'Basic ' + basic,
                                   'Accept': 'application/vnd.git-lfs+json',
                                   'Content-Type': 'application/vnd.git-lfs+json'})
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        returned = batch['objects']
        if {r['oid'] for r in returned} != {r['lfs_oid'] for r in entries} or len(returned) != len(entries):
            raise ValueError('Unexpected batch object set')
        objects = {r['oid']: r for r in returned}
        for expected in entries:
            result = {'path': expected['source'], 'oid': expected['lfs_oid'], 'size': expected['bytes']}
            try:
                obj = objects[expected['lfs_oid']]
                if 'error' in obj or obj['size'] != expected['bytes']:
                    raise ValueError('Remote object unavailable or wrong size')
                action = obj['actions']['download']
                parts = urlsplit(action['href'])
                host = parts.hostname or ''
                if parts.scheme != 'https' or not (host == 'github.com' or host.endswith(('.githubusercontent.com', '.amazonaws.com', '.github.com'))):
                    raise ValueError('Unexpected download host')
                headers = dict(action.get('header', {}))
                headers['Range'] = 'bytes=0-0'
                # Do not forward the Git credential to the object host.
                with urlopen(Request(action['href'], headers=headers), timeout=30) as response:
                    status = response.status
                    extent = response.headers.get('Content-Range', '')
                    length = response.headers.get('Content-Length', '')
                    first = response.read(1)
                expected_size = expected['bytes']
                if len(first) != 1 or not ((status == 206 and extent == f'bytes 0-0/{expected_size}') or
                                         (status == 200 and length == str(expected_size))):
                    raise ValueError('Range or object size mismatch')
                result.update(status='available', http_status=status, bytes_read=1,
                              remote_size_matches=True, host=host)
            except Exception as error:
                result.update(status='failed', error_type=type(error).__name__)
                if isinstance(error, HTTPError):
                    result['http_status'] = error.code
            record['results'].append(result)
        if all(r['status'] == 'available' for r in record['results']):
            record['status'] = 'passed'
    except Exception as error:
        record['error_type'] = type(error).__name__
        if isinstance(error, HTTPError):
            record['http_status'] = error.code
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if record['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
