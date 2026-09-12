"""One-time compressed preservation of approved, closed phase workspaces."""
from pathlib import Path
import argparse
import hashlib
import json
import sqlite3
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
OUT = ROOT/'dataset/processed/experiments/phase-history-20260912'
sys.path[:0] = [str(ROOT/'src'), str(ROOT)]
from text2ifc_agent.artifact_scan import SECRET_PATTERNS, ALLOWED_ENV_NAMES


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', 'utf8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--context', choices=['default', 'elevated'], required=True)
    args = parser.parse_args()
    plan = json.loads((REPORT/'phase-inventory-combined.json').read_text('utf8'))
    OUT.mkdir(exist_ok=True)
    index_path = OUT/'manifest.json'
    state = json.loads(index_path.read_text('utf8')) if index_path.exists() else dict(
        status='archiving', proof_status_changed=False, provider_calls=0, bundles=[], archives=[], findings=[])
    roots = {b['old_root']: b for b in state['bundles']}
    saved = {}
    for b in state['bundles']:
        for e in b['entries']:
            saved[(e['sha256'], e['size_bytes'])] = {k:e[k] for k in ('retained_path', 'archive_member') if k in e}
    for manifest in (ROOT/'dataset/processed/proof').glob('*/*/*/manifest.json'):
        try:
            proof = json.loads(manifest.read_text('utf8'))
        except (ValueError, OSError):
            continue
        for b in proof.get('legacy_bundles', []):
            for e in b['entries']:
                saved.setdefault((e['sha256'], e['size_bytes']), dict(retained_path=(manifest.parent/e['path']).relative_to(ROOT).as_posix()))
    checked_prior = set()
    for source in plan['bundles']:
        if source['unresolved_errors']:
            continue
        b = roots.get(source['old_root'])
        if b is None:
            b = dict(old_root=source['old_root'], entries=[], excluded_caches=[], links=source['links'])
            roots[b['old_root']] = b
            state['bundles'].append(b)
        done = {e['legacy_path'] for e in b['entries'] + b['excluded_caches']}
        zip_path = OUT/(Path(b['old_root']).parent.name+'--'+Path(b['old_root']).name+'.zip')
        z = None
        failures = []
        try:
            for item in source['files']:
                rel = item['legacy_path']
                if rel in done or args.context not in item['contexts']:
                    continue
                p = ROOT/b['old_root']/rel
                try:
                    data = p.read_bytes()
                except OSError as exc:
                    failures.append(dict(path=str(p), error=str(exc)))
                    continue
                if len(data) != item['size_bytes']:
                    raise ValueError(f'Source size changed: {p}')
                sha = hashlib.sha256(data).hexdigest()
                e = dict(legacy_path=rel, size_bytes=len(data), sha256=sha, source_context=args.context)
                if p.suffix == '.pyc' or '__pycache__' in p.parts or '.pytest_cache' in p.parts:
                    b['excluded_caches'].append(e)
                    continue
                prior = saved.get((sha, len(data)))
                if prior and 'archive_member' not in prior:
                    target = ROOT/prior['retained_path']
                    try:
                        if str(target) not in checked_prior:
                            if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
                                raise ValueError(f'Prior Proof hash mismatch: {target}')
                            checked_prior.add(str(target))
                    except OSError:
                        prior = None
                if not prior:
                    if p.name.startswith('.env'):
                        raise ValueError(f'Environment file requires separate handling: {p}')
                    if p.suffix.lower() in {'.json', '.jsonl', '.txt', '.log', '.md', '.py', '.ps1', '.xml', '.html', '.yaml', '.yml', '.sqlite', '.db'}:
                        if p.suffix.lower() in {'.sqlite', '.db'}:
                            with sqlite3.connect(p.as_uri()+'?mode=ro', uri=True) as con:
                                lines = list(con.iterdump())
                        else:
                            lines = data.decode('utf8', errors='replace').splitlines()
                        for number, line in enumerate(lines, 1):
                            for env in ALLOWED_ENV_NAMES:
                                line = line.replace(env, '')
                            for code, pat in SECRET_PATTERNS:
                                if pat.search(line):
                                    state['findings'].append(dict(path=p.relative_to(ROOT).as_posix(), line=number, code=code))
                                    raise ValueError(f'Potential credential in {p}; stopped before archiving this file.')
                    if z is None:
                        z = zipfile.ZipFile(zip_path, 'a', compression=zipfile.ZIP_DEFLATED, compresslevel=6)
                    if rel in z.namelist():
                        raise ValueError(f'Duplicate archive member: {rel}')
                    z.writestr(rel, data)
                    prior = dict(retained_path=zip_path.relative_to(ROOT).as_posix(), archive_member=rel)
                    saved[(sha, len(data))] = prior
                b['entries'].append({**e, **prior})
        finally:
            if z:
                z.close()
            write(index_path, state)
        print(Path(b['old_root']).name, len(b['entries']), 'evidence', len(b['excluded_caches']), 'caches', len(failures), 'read errors', flush=True)
        if failures:
            write(REPORT/('phase-read-errors-'+args.context+'-'+Path(b['old_root']).name+'.json'), failures)
    state['archives'] = [dict(path=p.relative_to(ROOT).as_posix(), size_bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.glob('*.zip'))]
    expected = sum(len(b['files']) for b in plan['bundles'] if not b['unresolved_errors'])
    actual = sum(len(b['entries'])+len(b['excluded_caches']) for b in state['bundles'])
    state['status'] = 'archived_not_deleted' if actual == expected else 'partial'
    write(index_path, state)
    print(json.dumps(dict(status=state['status'], expected=expected, captured=actual,
        archive_bytes=sum(x['size_bytes'] for x in state['archives']))))


if __name__ == '__main__':
    main()
