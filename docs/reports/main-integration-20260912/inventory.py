"""Read-only repository classification and conservative duplicate discovery."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

def git(*args):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', *args], cwd=ROOT).decode('utf-8')

def dump(name, value):
    with (OUT/name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

def category(path):
    if path.startswith(('src/', 'schemas/', 'prompts/')): return 'production_or_registered_contract'
    if path.startswith('tests/'): return 'regression_or_fixture_preserve_pending_coverage_review'
    if path.startswith('dataset/processed/proof/'): return 'frozen_proof_preserve'
    if path.startswith('dataset/processed/experiments/'): return 'archived_experiment_preserve'
    if path.startswith('dataset/processed/'): return 'run_or_dataset_requires_provenance_review'
    if path.startswith(('dataset/external/', 'dataset/sources/')): return 'source_data_or_license_preserve'
    if path.startswith(('docs/', '.planning/')): return 'guidance_or_historical_report'
    if path.startswith('scripts/'): return 'tool_requires_reference_review'
    return 'configuration_or_other_preserve'

files=[]
for line in git('ls-tree','-rz','HEAD').split('\0'):
    if not line: continue
    metadata,path=line.split('\t',1)
    mode,kind,oid=metadata.split()
    files.append(dict(path=path,kind=kind,git_oid=oid,classification=category(path)))
counts=Counter(row['classification'] for row in files)
groups=defaultdict(list)
for row in files:
    if row['path'].startswith('tests/') and row['path'].endswith('.py'):
        groups[row['git_oid']].append(row['path'])
duplicates=[paths for paths in groups.values() if len(paths)>1]
refs={ref:git('rev-parse',ref).strip() for ref in ['HEAD','origin/main','origin/Zcode']}
dump('tracked-inventory.json',dict(refs=refs,counts=dict(counts),files=files,
    exact_test_file_duplicate_groups=duplicates,
    note='Identical bytes are only candidates, not authorization to remove distinct discovery/package paths.'))

# Inspect only original roots declared by canonical Proof manifests.
from scripts.proof.package import digest, contained
bundles=[]
for p in (ROOT/'dataset/processed/proof').glob('*/*/*/manifest.json'):
    try:
        m=json.loads(p.read_text(encoding='utf-8'))
        for b in m.get('legacy_bundles',[]):
            old=Path(b['old_root'])
            old=old if old.is_absolute() else ROOT/old
            if not old.resolve().is_relative_to(ROOT):
                bundles.append(dict(manifest=str(p.relative_to(ROOT)),old_root=str(old),state='outside_checkout_preserve'));continue
            if not old.exists(): continue
            mismatch=[];matched=0;missing=0
            for e in b['entries']:
                source=contained(old,e['legacy_path']);target=contained(p.parent,e['path'])
                if not source.exists(): missing+=1;continue
                if source.stat().st_size==e['size_bytes'] and digest(source)==e['sha256'] and digest(target)==e['sha256']:matched+=1
                else:mismatch.append(e['legacy_path'])
            bundles.append(dict(manifest=str(p.relative_to(ROOT)),old_root=str(old),matched=matched,missing=missing,mismatches=mismatch,
                state='partial_source_requires_file_set_and_reference_review'))
    except (OSError,ValueError,KeyError) as exc:
        bundles.append(dict(manifest=str(p.relative_to(ROOT)),state='unreadable_preserve',error=str(exc)))
dump('proof-source-candidates.json',bundles)
dump('baseline.json',dict(refs=refs,tracked_files=len(files),test_python_files=sum(p['path'].startswith('tests/') and p['path'].endswith('.py') for p in files),
    test_duplicate_groups=duplicates,category_counts=dict(counts),proof_sources_requiring_review=len(bundles),
    full_offline_preflight_authorized=True,real_provider_authorized_for_this_task=False,delete_authorized_paths=[]))
print(json.dumps(dict(tracked_files=len(files),categories=dict(counts),test_duplicate_groups=duplicates,proof_sources=len(bundles)),ensure_ascii=False))
