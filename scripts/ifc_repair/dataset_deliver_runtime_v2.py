"""Pin frozen rounds and separately bound startup dependencies in a new runtime.

The failed 1.0 runtime is retained. Registered 87/89 authoring files come from
its verified snapshot. Ancillary imports are exact current-source copies with
separate provenance, never claimed to be covered by historic native receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from scripts.ifc_repair import dataset_deliver_runtime as old_runtime
from scripts.ifc_repair import dataset_pair_export as e
from scripts.ifc_repair import dataset_pairs as q

SCHEMA = 'text2ifc/dataset-pinned-delivery-runtime/1.1'
DEFAULT_ENTRY = 'scripts.ifc_repair.dataset_deliver'
PACKAGE_MARKERS = {
    'scripts/__init__.py': b'"""Pinned project package boundary for the dataset runtime."""\n',
    'scripts/ifc_repair/__init__.py': b'"""Pinned offline IFC dataset programs."""\n',
}
# Actual startup imports required by the frozen repair package and batch cases.
# These were absent from the historical registered 87/89 program catalogue.
ANCILLARY_FILES = (
    'scripts/ifc_repair/repair_comparison/__init__.py',
    *('src/text2ifc_knowledge/' + name + '.py' for name in (
        '__init__', 'express_registry', 'sources', 'psd_registry', 'registry', 'property_search', 'property_runtime')),
    *('src/text2ifc_text/' + name + '.py' for name in ('__init__', 'splits', 'projection', 'gold', 'pairs')),
    *('src/text2ifc_contract/' + name + '.py' for name in (
        '__init__', 'json_io', 'schema', 'validation', 'draft', 'capabilities', 'geometry_v2',
        'property_validation', 'placement', 'relationships_v2', 'validation_v2')),
)
BOOTSTRAP = '''"""Execute only bound project modules; retain installed Python/dependency paths."""
import importlib
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
from scripts.ifc_repair import dataset_deliver_runtime_v2 as pinned

def main():
    pinned.check_runtime(runtime)
    arguments = sys.argv[1:]
    module = 'scripts.ifc_repair.dataset_deliver'
    if arguments[:1] == ['--module']:
        if len(arguments) < 2:
            raise ValueError('RUNTIME_ENTRY_MODULE_REQUIRED')
        module, arguments = arguments[1], arguments[2:]
    if module not in record['entry_modules']:
        raise ValueError('RUNTIME_ENTRY_MODULE_NOT_BOUND')
    if arguments == ['--check-imports']:
        importlib.import_module(module)
        print(json.dumps(pinned.check_loaded_runtime(runtime), ensure_ascii=False, indent=2))
    else:
        pinned.check_loaded_runtime(runtime)
        sys.argv[:] = [module, *arguments]
        try:
            runpy.run_module(module, run_name='__main__')
        finally:
            pinned.check_loaded_runtime(runtime)

if __name__ == '__main__':
    main()
'''


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _module_path(module):
    e._require(isinstance(module, str) and module.startswith('scripts.ifc_repair.')
        and all(part.isidentifier() for part in module.split('.')), 'INVALID_RUNTIME_ENTRY_MODULE')
    return module.replace('.', '/') + '.py'


def check_runtime(runtime):
    """Hash/whitelist check; it does not imply the calling modules are pinned."""
    runtime = e._pair_safe_path(Path(runtime))
    record = q.read(e._file(runtime, 'runtime.json'))
    e._require(record.get('schema_version') == SCHEMA and record.get('status') == 'prepared'
        and record.get('runtime_root') == str(runtime), 'RUNTIME_MANIFEST_INVALID')
    files = {e._pair_safe_path(p).relative_to(runtime).as_posix() for p in runtime.rglob('*') if p.is_file()}
    e._require(files == {'runtime.json', *record['program_sha256']}, 'RUNTIME_FILE_SET_CHANGED')
    for name, digest in record['program_sha256'].items():
        e._require(q.sha256(e._file(runtime, name)) == digest, 'RUNTIME_PROGRAM_BINDING_CHANGED:' + name)
    base_manifest = e._pair_safe_path(Path(record['base_runtime_manifest']))
    e._require(q.sha256(base_manifest) == record['base_runtime_manifest_sha256'], 'BASE_RUNTIME_MANIFEST_CHANGED')
    for name, digest in record['registered_program_sha256'].items():
        e._require(record['program_sha256'].get(name) == digest, 'REGISTERED_RUNTIME_BINDING_CHANGED:' + name)
    for name, digest in record['ancillary_sha256'].items():
        e._require(record['program_sha256'].get(name) == digest, 'ANCILLARY_RUNTIME_BINDING_CHANGED:' + name)
    for module in record['entry_modules']:
        e._require(_module_path(module) in record['program_sha256'], 'RUNTIME_ENTRY_MODULE_NOT_BOUND')
    return record


def check_loaded_runtime(runtime):
    """Require every loaded project module, including ancillary files, to be pinned."""
    runtime = e._pair_safe_path(Path(runtime))
    record = check_runtime(runtime)
    loaded = {}
    for name, module in tuple(sys.modules.items()):
        if name != 'scripts' and not name.startswith(('scripts.', 'text2ifc_')):
            continue
        filename = getattr(module, '__file__', None)
        if filename is None:
            for folder in getattr(module, '__path__', ()):
                e._require(Path(folder).resolve().is_relative_to(runtime), 'PROJECT_NAMESPACE_OUTSIDE_RUNTIME:' + name)
            continue
        path = e._pair_safe_path(Path(filename))
        e._require(path.is_relative_to(runtime), 'PROJECT_MODULE_OUTSIDE_RUNTIME:' + name)
        relative = path.relative_to(runtime).as_posix()
        actual = q.sha256(path)
        e._require(record['program_sha256'].get(relative) == actual, 'LOADED_PROJECT_MODULE_NOT_BOUND:' + name)
        loaded[name] = {'path': str(path), 'sha256': actual,
            'registered_authoring_program': relative in record['registered_program_sha256']}
    e._require(q.ROOT.resolve() == runtime, 'CODE_ROOT_NOT_ACTUALLY_LOADED')
    return {'schema_version': SCHEMA, 'status': 'ready', 'runtime_root': str(runtime),
        'source_repository': record['repository'], 'manifest_sha256': q.sha256(runtime / 'runtime.json'),
        'loaded_project_modules': dict(sorted(loaded.items())), 'main_project_fallbacks': [],
        'provider_calls': 0, 'scope': 'Fresh loaded-location/hash check only; no IFC/native/Provider execution.'}


def prepare_runtime(batch, *, repository=ROOT, base_runtime=None, runtime=None, extra_modules=()):
    batch, repository = e._pair_safe_path(Path(batch)), e._pair_safe_path(Path(repository))
    base = e._pair_safe_path(Path(base_runtime or batch / 'private/delivery-runtime'))
    runtime = e._pair_safe_path(Path(runtime or batch / 'private/delivery-runtime-v3'))
    e._require(runtime.is_relative_to(batch / 'private') and not runtime.is_relative_to(base)
        and not runtime.is_relative_to(batch / 'private/production')
        and not runtime.is_relative_to(batch / 'private/supplement-r1')
        and not runtime.is_relative_to(batch / 'private/extension-r2'), 'PRIVATE_NEW_RUNTIME_ROOT_REQUIRED')
    previous = check_runtime(base) if q.read(e._file(base, 'runtime.json')).get('schema_version') == SCHEMA else old_runtime.check_runtime(base)
    e._require(previous['batch'] == str(batch) and previous['repository'] == str(repository), 'BASE_RUNTIME_CONTEXT_CHANGED')
    first = q.read(e._file(batch / 'private/production', 'build.json'))
    extra = q.read(e._file(batch / 'private/supplement-r1', 'build.json'))
    original, registered = first['code_sha256'], extra['code_sha256']
    e._require(all(registered.get(name) == digest for name, digest in original.items())
        and set(registered) == {*original, 'scripts/ifc_repair/dataset_supplement.py',
                               'scripts/ifc_repair/dataset_geometry_guard_v2.py'}
        and all(previous['program_sha256'].get(name) == digest for name, digest in registered.items()),
        'REGISTERED_FROZEN_PROGRAM_BINDINGS_INVALID')
    round_hashes = {'first_pass': q.sha256(batch / 'private/production/build.json'),
        'supplement-r1': q.sha256(batch / 'private/supplement-r1/build.json')}
    e._require(previous['round_build_sha256'] == round_hashes, 'FROZEN_ROUND_BUILD_CHANGED')
    payload = {name: e._file(base, name).read_bytes() for name in previous['program_sha256'] if name != 'bootstrap.py'}
    ancillary, ancillary_origins = {}, {}
    for name in ANCILLARY_FILES:
        e._require(name not in registered, 'ANCILLARY_COLLIDES_WITH_REGISTERED_PROGRAM')
        source = e._file(repository, name)
        if name in payload:
            e._require(previous.get('ancillary_sha256', {}).get(name) == _digest(payload[name]),
                       'ANCESTOR_ANCILLARY_BINDING_CHANGED')
        else:
            payload[name] = source.read_bytes()
        ancillary[name] = _digest(payload[name])
        ancillary_origins[str(source)] = ancillary[name]
    entries = [DEFAULT_ENTRY, *sorted((set(previous.get('entry_modules', ())) | set(extra_modules)) - {DEFAULT_ENTRY})]
    additions = ['scripts/ifc_repair/dataset_deliver_runtime_v2.py', *(_module_path(m) for m in extra_modules)]
    for name in additions:
        source = e._file(repository, name)
        data = source.read_bytes()
        if name in payload:
            e._require(payload[name] == data, 'NEW_ENTRY_CANNOT_REPLACE_FROZEN_FILE:' + name)
        else:
            payload[name] = data
    for name, data in PACKAGE_MARKERS.items():
        e._require(name not in payload or payload[name] == data, 'GENERATED_PACKAGE_MARKER_COLLISION')
        payload[name] = data
    payload['bootstrap.py'] = BOOTSTRAP.encode('utf-8')
    hashes = {name: _digest(data) for name, data in payload.items()}
    record = {'schema_version': SCHEMA, 'status': 'prepared', 'runtime_root': str(runtime),
        'repository': str(repository), 'batch': str(batch), 'program_sha256': hashes,
        'registered_program_sha256': registered, 'round_build_sha256': round_hashes,
        'ancillary_sha256': ancillary, 'ancillary_source_sha256': ancillary_origins,
        'ancillary_pin_origin': 'ancestor-runtime' if previous['schema_version'] == SCHEMA else 'current-repository',
        'generated_package_marker_sha256': {name: _digest(data) for name, data in PACKAGE_MARKERS.items()},
        'base_runtime_manifest': str(base / 'runtime.json'),
        'base_runtime_manifest_sha256': q.sha256(base / 'runtime.json'),
        'entry_modules': entries, 'observed_main_drift': previous['observed_main_drift'], 'provider_calls': 0,
        'scope': '87/89 registered authoring bytes retained; ancillary startup dependencies separately pinned '
                 'from observed source or retained ancestor runtime; generated package markers prevent composition with installed '
                 'win32 scripts namespaces. Installed interpreter and .deps reused. No main project fallback.'}
    if runtime.exists():
        saved = check_runtime(runtime)
        e._require(saved == record, 'EXISTING_RUNTIME_BINDINGS_DIFFERENT')
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
    parser.add_argument('--base-runtime', type=Path)
    parser.add_argument('--runtime', type=Path)
    parser.add_argument('--extra-module', action='append', default=[])
    args = parser.parse_args(argv)
    record = prepare_runtime(args.batch, repository=args.repository, base_runtime=args.base_runtime,
        runtime=args.runtime, extra_modules=args.extra_module) if args.command == 'prepare' else check_runtime(
            args.runtime or args.batch / 'private/delivery-runtime-v3')
    print(json.dumps({key: value for key, value in record.items() if key not in {
        'program_sha256', 'registered_program_sha256', 'ancillary_sha256', 'ancillary_source_sha256'}},
        ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
