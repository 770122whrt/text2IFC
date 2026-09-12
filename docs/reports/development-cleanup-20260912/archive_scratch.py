"""Collect one-off scratch code/results; exclude session, account and active data."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'dataset/processed/experiments'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    index = {}
    d = json.loads((OUT/'development-retirement-20260912.json').read_text(encoding='utf8'))
    for b in d['bundles']:
        for e in b['entries']:
            index.setdefault((e['size_bytes'], e['sha256']), ROOT/e['retained_path'])
    sources = [OUT/'c-token-archive-20260911.json']
    for m in sources:
        for b in json.loads(m.read_text(encoding='utf8'))['bundles']:
            for e in b['entries']:
                index.setdefault((e['size_bytes'], e['sha256']), OUT/e['path'])
    entries, preserved = [], []
    for p in sorted((ROOT/'.tmp').iterdir()):
        if not p.is_file():
            continue
        if p.is_symlink() or p.suffix.lower() not in {'.py','.xml','.json','.txt','.log','.patch','.nul','.bin'}:
            preserved.append(dict(path=p.relative_to(ROOT).as_posix(), reason='Outside one-off code/result scope'))
            continue
        text = p.read_bytes().decode('utf8', errors='replace')
        if any(x in (p.name+'\n'+text).lower() for x in ['codex-conversation', 'thread_history', 'codex_home', '.codex/sessions', '.codex\\sessions', 'accounts.json']):
            preserved.append(dict(path=p.relative_to(ROOT).as_posix(), reason='Possible session/account material'))
            continue
        h = sha(p)
        key = (p.stat().st_size, h)
        retained = index.get(key)
        if retained and (not retained.is_file() or sha(retained) != h):
            retained = None
        if retained:
            action = 'reuse_frozen_result'
        else:
            retained = OUT/'scratch-20260912'/p.name
            retained.parent.mkdir(exist_ok=True)
            with p.open('rb') as src, retained.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            action = 'archive_one_off_script_or_result'
            index[key] = retained
        entries.append(dict(path=p.as_posix(), size_bytes=key[0], sha256=h,
            retained_path=retained.relative_to(ROOT).as_posix(), action=action))
    (OUT/'scratch-retirement-20260912.json').write_text(json.dumps(dict(entries=entries,preserved=preserved),
        ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'files':len(entries), 'bytes':sum(e['size_bytes'] for e in entries),
        'reused':sum(e['action']=='reuse_frozen_result' for e in entries), 'preserved':len(preserved)}))


if __name__ == '__main__':
    main()
