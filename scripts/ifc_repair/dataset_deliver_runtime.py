"""Prepare an immutable, actually executable delivery runtime from both frozen rounds."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from scripts.ifc_repair import dataset_pair_export as e
from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_supplement as s

SCHEMA = 'text2ifc/dataset-pinned-delivery-runtime/1.0'
HELPERS = ('dataset_deliver.py', 'dataset_pair_export_v2.py', 'dataset_request_v4.py', 'dataset_deliver_runtime.py')
BOOTSTRAP = '''"""Run delivery with registered project code loaded only from this runtime."""
import json
from pathlib import Path
import runpy
import sys

runtime = Path(__file__).resolve().parent
record = json.loads((runtime / 'runtime.json').read_text(encoding='utf-8'))
repository = Path(record['repository'])
excluded = {str(repository).casefold(), str(repository / 'src').casefold()}
sys.path[:] = [str(runtime), str(runtime / 'src'), str(repository / '.deps/python312'),
              *[p for p in sys.path if p and str(Path(p).resolve()).casefold() not in excluded]]
runpy.run_module('scripts.ifc_repair.dataset_deliver', run_name='__main__')
'''


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def check_runtime(runtime):
    runtime = e._pair_safe_path(Path(runtime))
    record = q.read(e._file(runtime, 'runtime.json'))
    e._require(record.get('schema_version') == SCHEMA and record.get('status') == 'prepared'
               and record.get('runtime_root') == str(runtime), 'RUNTIME_MANIFEST_INVALID')
    files = {e._pair_safe_path(p).relative_to(runtime).as_posix() for p in runtime.rglob('*') if p.is_file()}
    e._require(files == {'runtime.json', *record['program_sha256']}, 'RUNTIME_FILE_SET_CHANGED')
    for name, digest in record['program_sha256'].items():
        e._require(q.sha256(e._file(runtime, name)) == digest, 'RUNTIME_PROGRAM_BINDING_CHANGED:' + name)
    return record


def prepare_runtime(batch, *, repository=ROOT, runtime=None):
    batch, repository = e._pair_safe_path(Path(batch)), e._pair_safe_path(Path(repository))
    runtime = e._pair_safe_path(Path(runtime or batch / 'private/delivery-runtime'))
    e._require(runtime.is_relative_to(batch / 'private') and not runtime.is_relative_to(batch / 'private/production')
               and not runtime.is_relative_to(batch / 'private' / s.ROUND), 'PRIVATE_NEW_RUNTIME_ROOT_REQUIRED')
    first_root, extra_root = batch / 'private/production', batch / 'private' / s.ROUND
    first = q.read(e._file(first_root, 'build.json'))
    extra = q.read(e._file(extra_root, 'build.json'))
    original, frozen = first['code_sha256'], extra['code_sha256']
    e._require(first.get('schema_version') == q.SCHEMA and extra.get('schema_version') == s.SCHEMA
        and all(frozen.get(name) == digest for name, digest in original.items())
        and set(frozen) == {*original, 'scripts/ifc_repair/dataset_supplement.py',
                            'scripts/ifc_repair/dataset_geometry_guard_v2.py'}, 'FROZEN_RUNTIME_ROUND_BINDINGS_INVALID')
    payload, observed = {}, []
    for name, digest in frozen.items():
        source = e._file(extra_root / 'code-snapshot', name)
        data = source.read_bytes()
        e._require(_digest(data) == digest, 'FROZEN_SUPPLEMENT_SNAPSHOT_CHANGED:' + name)
        if name in original:
            e._require(q.sha256(e._file(first_root / 'private/code-snapshot', name)) == digest,
                       'FROZEN_FIRST_PASS_SNAPSHOT_CHANGED:' + name)
        payload[name] = data
        current = e._file(repository, name)
        actual = q.sha256(current)
        if actual != digest:
            observed.append({'path': name, 'frozen_sha256': digest, 'observed_main_sha256': actual,
                             'scope': 'Observed drift retained; main file untouched; runtime uses frozen bytes.'})
    for name in HELPERS:
        relative = 'scripts/ifc_repair/' + name
        payload[relative] = e._file(repository, relative).read_bytes()
    payload['bootstrap.py'] = BOOTSTRAP.encode('utf-8')
    hashes = {name: _digest(data) for name, data in payload.items()}
    record = {'schema_version': SCHEMA, 'status': 'prepared', 'runtime_root': str(runtime),
        'repository': str(repository), 'batch': str(batch), 'program_sha256': hashes,
        'round_build_sha256': {'first_pass': q.sha256(first_root / 'build.json'), s.ROUND: q.sha256(extra_root / 'build.json')},
        'observed_main_drift': observed, 'provider_calls': 0,
        'scope': 'Frozen first-pass/supplement programs plus new handoff helpers; actual loaded locations '
                 'must be checked by delivery. Main workspace is not claimed to match the frozen programs.'}
    if runtime.exists():
        saved = check_runtime(runtime)
        e._require(saved['program_sha256'] == hashes and saved['repository'] == str(repository)
            and saved['batch'] == str(batch) and saved['round_build_sha256'] == record['round_build_sha256'],
            'EXISTING_RUNTIME_BINDINGS_DIFFERENT')
        return saved
    runtime.mkdir()
    for name, data in payload.items():
        path = runtime / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    with (runtime / 'runtime.json').open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return check_runtime(runtime)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'check'))
    parser.add_argument('--batch', type=Path, default=q.DEFAULT_OUTPUT)
    parser.add_argument('--repository', type=Path, default=ROOT)
    parser.add_argument('--runtime', type=Path)
    args = parser.parse_args(argv)
    action = prepare_runtime(args.batch, repository=args.repository, runtime=args.runtime) if args.command == 'prepare' else check_runtime(args.runtime or args.batch / 'private/delivery-runtime')
    print(json.dumps({k: v for k, v in action.items() if k != 'program_sha256'}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
