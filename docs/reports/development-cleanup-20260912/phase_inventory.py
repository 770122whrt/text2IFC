"""Read-only, permission-aware inventory of the approved earlier-phase scope."""
from pathlib import Path
import argparse
import json
import os

ROOT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--context', choices=['default', 'elevated'], required=True)
    args = p.parse_args()
    scope = json.loads((REPORT/'phase-scope.json').read_text('utf8'))
    bundles = []
    for selected in scope['selected']:
        root = ROOT/selected['path']
        files, visited, errors, links = [], [], [], []
        if root.is_symlink() or root.is_junction():
            raise ValueError(f'Linked root: {root}')
        def error(exc):
            errors.append(dict(path=Path(exc.filename).relative_to(root).as_posix(), error=str(exc)))
        for base, dirs, names in os.walk(root, onerror=error):
            visited.append(Path(base).relative_to(root).as_posix())
            for name in dirs + names:
                item = Path(base)/name
                if item.is_symlink() or item.is_junction():
                    links.append(dict(legacy_path=item.relative_to(root).as_posix(), target=os.readlink(item), directory=item.is_dir()))
                    if name in dirs:
                        dirs.remove(name)
                    continue
            for name in names:
                item = Path(base)/name
                if item.is_symlink() or item.is_junction():
                    continue
                try:
                    stat = item.stat()
                    files.append(dict(legacy_path=item.relative_to(root).as_posix(), size_bytes=stat.st_size))
                except OSError as exc:
                    error(exc)
        bundles.append(dict(old_root=selected['path'], files=files, visited=visited, errors=errors, links=links))
    result = dict(context=args.context, bundles=bundles)
    (REPORT/f'phase-inventory-{args.context}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(json.dumps(dict(context=args.context, roots=len(bundles), files=sum(len(b['files']) for b in bundles),
        errors=sum(len(b['errors']) for b in bundles))))


if __name__ == '__main__':
    main()
