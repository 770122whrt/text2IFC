"""One-off, offline archive retirement inventory. Does not delete or edit Proof.

Retains the historical refactor delta and small recovery metadata. The six
original ZIPs stay recoverable from the fixed Git/LFS revision in the index.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'archive/zcode-local-20260905'
DEST = ROOT / 'dataset/processed/experiments/zcode-history-20260913'
REPORT = Path(__file__).resolve().parent
REVISION = 'd1639232f74e4108f3242c46162bcd91bf0909fe'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def add(z, name, data):
    info = ZipInfo(name, (2026, 9, 13, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    z.writestr(info, data, compresslevel=9)


def main():
    if DEST.exists():
        raise ValueError('Destination already exists; preserve the previous attempt')
    for p in [SOURCE, *SOURCE.rglob('*')]:
        if p.is_symlink() or getattr(p, 'is_junction', lambda: False)():
            raise ValueError('Unexpected link in archive')
    files = sorted(p for p in SOURCE.rglob('*') if p.is_file())
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', 'archive'], cwd=ROOT).decode().split('\0')
    if {p.relative_to(ROOT).as_posix() for p in files} != set(filter(None, tracked)):
        raise ValueError('Archive contains untracked, missing, or changed path set')
    entries = []
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        blob = subprocess.check_output(['git', 'show', f'{REVISION}:{rel}'], cwd=ROOT)
        oid = subprocess.check_output(['git', 'rev-parse', f'{REVISION}:{rel}'], cwd=ROOT).decode().strip()
        row = {'source': rel, 'bytes': p.stat().st_size, 'sha256': digest(p), 'git_blob': oid}
        if p.suffix == '.zip':
            lines = blob.decode('ascii').splitlines()
            if lines[0] != 'version https://git-lfs.github.com/spec/v1':
                raise ValueError('Expected LFS pointer')
            row['lfs_oid'] = lines[1].split('sha256:', 1)[1]
            if row['sha256'] != row['lfs_oid'] or row['bytes'] != int(lines[2].split()[1]):
                raise ValueError(f'ZIP differs from frozen Git pointer: {rel}')
            row['retained_as'] = {'kind': 'git_lfs_history', 'revision': REVISION, 'path': rel}
        else:
            # Historical ordinary text used CRLF checkouts; preserve both identities.
            row['git_blob_sha256'] = hashlib.sha256(blob).hexdigest()
            data = p.read_bytes()
            if data != blob and data.replace(b'\r\n', b'\n') != blob:
                raise ValueError(f'Text differs from frozen Git blob: {rel}')
        entries.append(row)

    DEST.mkdir(parents=True)
    with ZipFile(DEST / 'recovery-metadata.zip', 'x') as z:
        for row in entries:
            p = ROOT / row['source']
            rel = p.relative_to(SOURCE).as_posix()
            if p.suffix == '.zip':
                continue
            if rel.startswith('published-contracts/'):
                target = DEST / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(p.read_bytes())
                row['retained_as'] = {'kind': 'file', 'path': target.relative_to(ROOT).as_posix()}
            else:
                add(z, rel, p.read_bytes())
                row['retained_as'] = {'kind': 'zip_member', 'path': (DEST / 'recovery-metadata.zip').relative_to(ROOT).as_posix(), 'member': rel}

    mirror = 'refactor_workspace/text2ifc-refactored/'
    snapshot = 'refactor_workspace/tmp/source-snapshot/'
    delta = []
    documents = []
    unchanged = 0
    with ZipFile(SOURCE / 'refactor-workspace.zip') as old, ZipFile(DEST / 'refactor-reference.zip', 'x') as new:
        names = set(old.namelist())
        for name in sorted(names):
            if not name.startswith(mirror) or not name.endswith('.py'):
                continue
            rel = name[len(mirror):]
            if rel.split('/')[0] not in {'src', 'scripts', 'tests'}:
                continue
            data = old.read(name)
            base = snapshot + rel
            if base in names and data == old.read(base):
                unchanged += 1
                continue
            add(new, 'mirror/' + rel, data)
            local = ROOT / rel
            delta.append({'path': rel, 'member': 'mirror/' + rel, 'original_member': name,
                          'kind': 'changed' if base in names else 'new_or_relocated',
                          'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                          'current_state': 'same' if local.is_file() and local.read_bytes() == data else 'different' if local.is_file() else 'absent'})
        for name in sorted(names):
            is_audit = name.startswith('refactor_workspace/audit/') and name.endswith('.md')
            is_handoff = name in {'refactor_workspace/REFACTOR-HANDOFF.md', 'refactor_workspace/WORK-STATUS.md'}
            is_design = name.startswith(mirror + 'docs/') and name.endswith('.md') and ('/development/' in name or name.startswith(mirror + 'docs/architecture/'))
            if not (is_audit or is_handoff or is_design):
                continue
            data = old.read(name)
            add(new, name, data)
            documents.append({'member': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        removed = sorted(name[len(snapshot):] for name in names if name.startswith(snapshot)
                         and name.endswith('.py') and name[len(snapshot):].split('/')[0] in {'src', 'scripts', 'tests'}
                         and mirror + name[len(snapshot):] not in names)

    for row in entries:
        retained = row['retained_as']
        if retained['kind'] == 'file':
            actual = digest(ROOT / retained['path'])
        elif retained['kind'] == 'zip_member':
            with ZipFile(ROOT / retained['path']) as z:
                actual = hashlib.sha256(z.read(retained['member'])).hexdigest()
        else:
            continue
        if actual != row['sha256']:
            raise ValueError('Retained bytes mismatch')
    with ZipFile(DEST / 'refactor-reference.zip') as z:
        for row in delta + documents:
            if hashlib.sha256(z.read(row['member'])).hexdigest() != row['sha256']:
                raise ValueError('Refactor member mismatch')

    record = {'schema_version': 'text2ifc/archive-retirement/1.0', 'created_at': datetime.now(timezone.utc).isoformat(),
              'status': 'prepared_not_deleted', 'source_revision': REVISION,
              'remote': 'https://github.com/770122whrt/text2IFC.git',
              'source_root': SOURCE.relative_to(ROOT).as_posix(), 'entries': entries,
              'source_files': len(entries), 'source_bytes': sum(x['bytes'] for x in entries),
              'historical_recovery_check': 'docs/reports/zcode-integration-20260905/remote-recovery-verification.json',
              'historical_recovery_scope': 'Fresh independent LFS download in 2026-09-05; not repeated here',
              'refactor': {'base_revision': '8bfcfe075521ddb142f8608296dfbfea1fd385e4', 'unchanged_python_files': unchanged,
                           'delta': delta, 'removed_or_relocated': removed, 'documents': documents},
              'new_archive_checks': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(DEST.glob('*.zip'))]}
    write_json(DEST / 'recovery-index.json', record)
    proposal = {'status': 'prepared_not_deleted', 'authorization': 'User approved archive retirement direction on 2026-09-13, preserving important Proof',
                'root': str(ROOT / 'archive'), 'entries': entries,
                'empty_directories_after_files': [str(SOURCE / 'published-contracts'), str(SOURCE), str(ROOT / 'archive')]}
    write_json(REPORT / 'delete-list.json', proposal)
    print(json.dumps({'source_files': len(entries), 'source_bytes': record['source_bytes'], 'code_delta_files': len(delta),
                      'historical_docs': len(documents), 'new_zips': record['new_archive_checks']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
