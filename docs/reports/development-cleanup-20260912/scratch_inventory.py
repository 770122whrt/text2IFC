"""Read-only classification of closed pytest outputs and one-off scratch files."""
from pathlib import Path
import json
import os
import re
import xml.etree.ElementTree as ET
import argparse

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='scratch-inventory.json', choices=['scratch-inventory.json', 'scratch-inventory-elevated.json'])
    args = parser.parse_args()
    names = {}
    roots = [ROOT/'.tmp', ROOT/'dataset/processed/experiments', ROOT/'docs/reports/courtyard-proof-closeout-20260912',
        ROOT/'dataset/processed/proof/generation/phase6.6/courtyard-library-20260912']
    xmls = list(roots[0].glob('*.xml'))
    for root in roots[1:]:
        xmls.extend(root.rglob('*.xml'))
    for p in xmls:
        try:
            for t in ET.parse(p).iter('testcase'):
                name = t.get('name', '')
                names.setdefault(re.sub(r'\W', '_', name)[:30], dict(test=name, xml=p.relative_to(ROOT).as_posix()))
        except (OSError, ET.ParseError):
            continue
    selected, preserved = [], []
    for p in sorted((ROOT/'.tmp').iterdir()):
        if not p.is_dir():
            continue
        if p.name in {'main-integration-20260912', 'dataset-acquisition', 'cleanup-recovery-20260912'}:
            preserved.append(dict(path=p.relative_to(ROOT).as_posix(), reason='Active worktree, dataset source, or recovery material'))
            continue
        try:
            if p.is_symlink() or p.is_junction():
                raise ValueError('linked root')
            bindings = []
            for x in p.iterdir():
                if not x.is_dir() or not x.name.startswith('test_'):
                    raise ValueError('not exclusively closed pytest test directories')
                stem = re.sub(r'\d+$', '', x.name)
                match = next((v for k, v in names.items() if k.startswith(stem)), None)
                if not match:
                    raise ValueError('test family has no retained JUnit record')
                bindings.append(dict(child=x.name, **match))
            if not bindings:
                raise ValueError('empty/unattributed')
            files = []
            def inaccessible(error):
                raise error
            for base, dirs, leaves in os.walk(p, onerror=inaccessible):
                for n in dirs + leaves:
                    item = Path(base)/n
                    if item.is_symlink() or item.is_junction():
                        raise ValueError('linked descendant')
                files.extend(Path(base)/n for n in leaves)
            selected.append(dict(path=p.as_posix(), file_count=len(files),
                size_bytes=sum(f.stat().st_size for f in files), origin=bindings))
            print(p.name, len(files), flush=True)
        except (OSError, ValueError) as error:
            preserved.append(dict(path=p.relative_to(ROOT).as_posix(), reason=str(error)))
    (OUT/args.output).write_text(json.dumps(dict(directories=selected, preserved=preserved),
        ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps({'directories':len(selected), 'files':sum(x['file_count'] for x in selected),
        'bytes':sum(x['size_bytes'] for x in selected), 'preserved':len(preserved)}))


if __name__ == '__main__':
    main()
