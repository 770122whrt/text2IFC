"""One-time inventory and reviewable deletion list; deletion is performed by PowerShell."""
from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import os
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / 'dataset'
RVT = DATA / 'external/RVT'
SELECTED = RVT / 'IFC/dataset-resbim50-20260913'


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def save(name, data):
    with (HERE / name).open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def rel(path):
    return path.relative_to(ROOT).as_posix()


def inventory(label):
    rows, errors, links = [], [], []
    def walk(folder):
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    try:
                        path = Path(entry.path)
                        status = entry.stat(follow_symlinks=False)
                        if getattr(status, 'st_file_attributes', 0) & 1024:
                            links.append(rel(path))
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            if entry.name not in {'.git', '__pycache__'} and path != HERE:
                                walk(path)
                        elif entry.is_file(follow_symlinks=False):
                            record = {'path': rel(path), 'size_bytes': status.st_size, 'suffix': path.suffix.lower(), 'mtime_ns': status.st_mtime_ns}
                            parts = path.relative_to(DATA).parts
                            record['group'] = '/'.join(parts[:2]) if len(parts) > 2 else parts[0]
                            if record['suffix'] in {'.ifc', '.rvt'}:
                                record['sha256'] = sha(path)
                            if record['suffix'] == '.ifc':
                                with path.open('rb') as h:
                                    match = re.search(rb"FILE_SCHEMA\s*\(\s*\(\s*['\"]([^'\"]+)", h.read(16384), re.I)
                                record['header_schema'] = match.group(1).decode('ascii', errors='replace').upper() if match else None
                            rows.append(record)
                    except OSError as error:
                        errors.append({'path': str(entry.path), 'error': str(error)})
        except OSError as error:
            errors.append({'path': str(folder), 'error': str(error)})
    walk(DATA)
    rows.sort(key=lambda x: x['path'])
    groups = defaultdict(lambda: {'files': 0, 'bytes': 0, 'extensions': Counter()})
    for row in rows:
        group = groups[row['group']]
        group['files'] += 1
        group['bytes'] += row['size_bytes']
        group['extensions'][row['suffix'] or '<none>'] += 1
    with (HERE / f'{label}-files.jsonl').open('x', encoding='utf-8') as h:
        for row in rows:
            h.write(json.dumps(row, ensure_ascii=False) + '\n')
    summary = {'scope': 'All dataset regular files; excludes this registration directory, .git directories and __pycache__; archive contents not counted as loose models.', 'file_count': len(rows), 'size_bytes': sum(x['size_bytes'] for x in rows), 'groups': dict(groups), 'errors': errors, 'reparse_points_not_traversed': links}
    save(f'{label}-summary.json', summary)
    print(json.dumps({k: summary[k] for k in ['file_count', 'size_bytes', 'errors', 'reparse_points_not_traversed']}, ensure_ascii=True), flush=True)
    if links or any(not str(e['path']).startswith(str(DATA / 'processed') + os.sep) for e in errors):
        raise SystemExit('Unresolved inventory within cleanup scope; no deletion admission')
    return rows


def plan():
    if (HERE / 'before-files.jsonl').exists():
        summary = json.loads((HERE / 'before-summary.json').read_text('utf-8'))
        assert not summary['reparse_points_not_traversed']
        assert all(str(e['path']).startswith(str(DATA / 'processed') + os.sep) for e in summary['errors'])
        rows = [json.loads(line) for line in (HERE / 'before-files.jsonl').read_text('utf-8').splitlines()]
    else:
        rows = inventory('before')
    manifest = json.loads((SELECTED / 'manifest.json').read_text('utf-8'))
    keep = [a for a in manifest['assets'] if a.get('ifc_path') and a['source_name'] == 'ResBIM']
    keep_rvt = {rel(RVT / a['rvt_path_from_RVT_directory']): a['rvt_sha256'] for a in keep}
    assert len(keep_rvt) == 50
    good, bad = defaultdict(list), defaultdict(list)
    for path in (RVT / 'runs').rglob('*.json'):
        try:
            report = json.loads(path.read_text('utf-8'))
        except (ValueError, UnicodeError):
            continue
        if isinstance(report, dict) and report.get('sha256') and 'technical_candidate' in report and 'validation_scope' in report:
            (good if report['technical_candidate'] else bad)[report['sha256']].append(rel(path))
    archives = {rel(RVT / name) for name in ['Text2IFC_RVT86_CrossSource_A.zip', 'Text2IFC_RVT86_CrossSource_B.zip', 'additional/ResBIM/datapoints_100.7z']}
    deletions = []
    for row in rows:
        path = row['path']
        reason = None
        if row['suffix'] == '.rvt':
            if path in keep_rvt:
                assert row['sha256'] == keep_rvt[path]
                continue
            assert path.startswith('dataset/external/RVT/') or path.startswith('dataset/external/bim-whale-ifc-samples/')
            reason = 'user_removed_other_rvt_or_conversion_input_copy'
        elif row['suffix'] == '.ifc' and path.startswith('dataset/external/RVT/'):
            if row['sha256'] in good:
                continue
            assert row['sha256'] in bad, f'Unclassified IFC: {path}'
            reason = 'failed_ifc_validation_report_with_matching_sha256'
        elif path in archives:
            reason = 'archive_of_rejected_or_unselected_rvt_models_selected_50_already_preserved'
        if reason:
            target = dict(row, absolute_path=str(ROOT / path), reason=reason)
            target['sha256'] = row.get('sha256') or sha(ROOT / path)
            if row['suffix'] == '.ifc':
                target['failure_reports'] = bad[row['sha256']]
            deletions.append(target)
    assert sum(d['suffix'] == '.rvt' for d in deletions) == 266
    assert sum(d['suffix'] == '.ifc' for d in deletions) == 209
    assert sum(d['path'] in archives for d in deletions) == 3
    for asset in keep:
        assert sha(SELECTED / asset['ifc_path']) == asset['ifc_sha256']
    save('deletion-plan.json', {'authorization': 'User requested retain 50 ResBIM, pause RVT statistics/conversion, delete other RVTs and unsuccessful IFC conversion results; user additionally explicitly included five BIM Whale RVTs.', 'allowed_roots': [str(RVT), str(DATA / 'external/bim-whale-ifc-samples')], 'keep_rvt_paths': keep_rvt, 'count': len(deletions), 'bytes': sum(d['size_bytes'] for d in deletions), 'files': deletions})
    save('retained-resbim50.json', keep)
    print(json.dumps({'delete_count': len(deletions), 'delete_bytes': sum(d['size_bytes'] for d in deletions), 'by_extension': dict(Counter(d['suffix'] for d in deletions)), 'keep_rvt': len(keep_rvt)}, indent=2), flush=True)


def after():
    rows = inventory('after')
    lookup = {r['path']: r for r in rows}
    before = [json.loads(line) for line in (HERE / 'before-files.jsonl').read_text('utf-8').splitlines()]
    plan = json.loads((HERE / 'deletion-plan.json').read_text('utf-8'))
    deleted = {x['path'] for x in plan['files']}
    assert not deleted.intersection(lookup)
    preserved_ifcs = [x for x in before if x['suffix'] == '.ifc' and x['path'] not in deleted]
    assert all(lookup[x['path']]['sha256'] == x['sha256'] for x in preserved_ifcs)
    proof_rows = [x for x in before if x['path'].startswith('dataset/processed/')]
    assert all(x['path'] in lookup and (x['size_bytes'], x['mtime_ns']) == (lookup[x['path']]['size_bytes'], lookup[x['path']]['mtime_ns']) for x in proof_rows)
    rvts = [x for x in rows if x['suffix'] == '.rvt']
    assert {x['path'] for x in rvts} == set(plan['keep_rvt_paths']) and len(rvts) == 50
    canonical = [json.loads(line) for line in (DATA / 'manifests/ifc-files.jsonl').read_text('utf-8').splitlines() if line.strip()]
    assert len(canonical) == 274
    for row in canonical:
        assert lookup[row['local_path']]['sha256'] == row['sha256']
    resbim = json.loads((HERE / 'retained-resbim50.json').read_text('utf-8'))
    active = []
    for row in canonical:
        active.append({'id': row['id'], 'source_id': row['source_id'], 'local_path': row['local_path'], 'sha256': row['sha256'], 'size_bytes': row['size_bytes'], 'declared_schema': row['header_schema'], 'role': 'existing_registered_source', 'training_eligible': row['training_eligible'], 'authority': 'dataset/manifests/ifc-files.jsonl', 'validation': row['validation']})
    for row in resbim:
        path = rel(SELECTED / row['ifc_path'])
        active.append({'id': 'resbim-' + row['inventory_id'].lower(), 'inventory_id': row['inventory_id'], 'source_id': 'resbim', 'local_path': path, 'sha256': row['ifc_sha256'], 'size_bytes': row['ifc_bytes'], 'declared_schema': 'IFC2X3', 'role': 'selected_synthetic_residential_unit', 'source_rvt_path': rel(RVT / row['rvt_path_from_RVT_directory']), 'source_rvt_sha256': row['rvt_sha256'], 'source_url': row['source_url'], 'license': 'MIT', 'source_training_rights_supported': True, 'training_eligible': False, 'training_admission': 'not_assigned_no_split_or_complete_building_qualification', 'authority': rel(HERE / 'retained-resbim50.json'), 'strict_validation_report': rel(RVT / row['validation_report_from_RVT_directory']), 'visual_sample_inspected': row['visual_sample_inspected'], 'rvt_fidelity': 'not_verified', 'independent_building': 'not_established'})
    assert len(active) == len({a['sha256'] for a in active}) == 324
    with (HERE / 'active-ifc-register.jsonl').open('x', encoding='utf-8') as handle:
        for row in active:
            handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    with (HERE / 'active-ifc-register.csv').open('x', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['id', 'source_id', 'local_path', 'sha256', 'size_bytes', 'declared_schema', 'role', 'training_eligible'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(active)
    all_ifcs = [x for x in rows if x['suffix'] == '.ifc']
    external_ifcs = [x for x in all_ifcs if x['path'].startswith('dataset/external/')]
    active_hashes = {x['sha256'] for x in active}
    reserve = [x for x in external_ifcs if x['sha256'] not in active_hashes]
    save('reserve-ifc-files.json', reserve)
    errors = json.loads((HERE / 'after-summary.json').read_text('utf-8'))['errors']
    summary = {'active_source_ifc_files': 324, 'active_source_ifc_unique_sha256': 324, 'active_source_ifc_bytes': sum(x['size_bytes'] for x in active), 'active_by_schema': dict(Counter(x['declared_schema'] for x in active)), 'active_by_source': dict(Counter(x['source_id'] for x in active)), 'training_eligible_existing': sum(x['training_eligible'] for x in active), 'selected_resbim': 50, 'rvt_work_status': 'paused_by_user', 'loose_rvt_files_in_readable_scope': len(rvts), 'external_physical_ifcs': len(external_ifcs), 'external_unique_ifc_hashes': len({x['sha256'] for x in external_ifcs}), 'reserve_unique_ifc_hashes': len({x['sha256'] for x in reserve}), 'dataset_physical_ifcs_in_readable_scope_including_proof_experiments_copies': len(all_ifcs), 'deleted_files': len(deleted), 'deleted_bytes': plan['bytes'], 'all_remaining_readable_ifc_hashes_unchanged': len(preserved_ifcs), 'processed_readable_files_size_mtime_unchanged': len(proof_rows), 'dataset_inventory_errors': errors, 'scope': 'No new IFC conversion or semantic validation; inventory, SHA256 reconciliation and user-authorized deletion only. Snapshot excludes registry itself, .git directories, __pycache__, archive interiors and explicitly listed inaccessible processed directories. Entire-dataset counts are lower bounds when errors are present; external cleanup inventory is complete.'}
    save('registration-summary.json', summary)
    print(json.dumps(summary, ensure_ascii=True, indent=2), flush=True)


if __name__ == '__main__':
    {'plan': plan, 'after': after}[sys.argv[1]]()
