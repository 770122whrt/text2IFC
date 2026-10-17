"""Orchestrate bounded dataset preparation and export public experiment inputs."""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'src'), str(ROOT / '.deps/python312')]

from scripts.ifc_repair.collect_damage_pilot import bound_origin_program, inspect_source
from scripts.ifc_repair.dataset_batch.validation import program_hash, sha256
from scripts.ifc_repair.repair_comparison.batch_cases import (
    _pair_safe_path, load_candidates, load_pair_candidates,
)
from scripts.ifc_repair.repair_comparison.budget import budget_level_for_primary_targets

FIELDS = ('case_id', 'ifc_path', 'request_path', 'level', 'primary_target_count', 'task_kind')
PRIVATE_WORDS = re.compile(r'original|gold|reference|mutation|private|pristine|ground[_-]?truth', re.I)


def read(path):
    return json.loads(_pair_safe_path(Path(path)).read_text(encoding='utf-8-sig'))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _disjoint(*paths):
    for i, first in enumerate(paths):
        for second in paths[i + 1:]:
            require(not first.is_relative_to(second) and not second.is_relative_to(first),
                    'OUTPUTS_MUST_BE_DISJOINT_FROM_DATASET_AND_EACH_OTHER')


def _new(path):
    path = _pair_safe_path(Path(path))
    if path.exists():
        raise FileExistsError('NEW_OUTPUT_REQUIRED:' + str(path))
    return path


def check_dataset(dataset, *, repository_root=ROOT):
    """Verify the current pilot's sealed receipts, then use the experiment adapter.

    Dataset-authoring code may read private evidence; none of it is serialized
    into the public directory. Native/geometry checks are not rerun here.
    """
    root = _pair_safe_path(Path(dataset))
    summary = read(root / 'summary.json')
    require(summary.get('schema_version') == 'text2ifc/dataset-pilot-report/1.0',
            'PILOT_DATASET_REQUIRED_USE_LEGACY_TOOL_FOR_OTHER_FORMATS')
    candidates = load_candidates(root)
    bound_origin_program(root, program_hash())
    profile = summary.get('request_profile')
    require(profile in {'text2ifc/dataset-request/1.2', 'text2ifc/dataset-request/1.3'}, 'UNSUPPORTED_REQUEST_PROFILE')
    source_hashes, damaged_hashes = [], []
    for source in summary['sources']:
        result, hashes, _ = inspect_source(root, source['source_id'], Path(repository_root),
                                          len(source['cases']), profile=profile)
        source_hashes.append(result['source_sha256'])
        damaged_hashes.extend(hashes)
        require(0 < (root / 'sources' / source['source_id'] / 'private/reference.ifc').stat().st_size < 20_000_000,
                'SOURCE_SIZE_LIMIT')
    require(len(set(source_hashes)) == summary['source_models'], 'DUPLICATE_SOURCE_BYTES')
    require(len(set(damaged_hashes)) == len(candidates) == summary['target_cases'], 'DUPLICATE_OR_MISSING_CASE_BYTES')
    for case in candidates:
        require(Path(case['model_path']).stat().st_size < 20_000_000, 'DAMAGED_SIZE_LIMIT')
    return summary, candidates


def _public_rows(candidates):
    rows, identifiers = [], set()
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *{f'COM{i}' for i in range(1, 10)}, *{f'LPT{i}' for i in range(1, 10)}}
    require(bool(candidates), 'NO_PUBLIC_CASES')
    for case in candidates:
        key = case['case_id']
        require(isinstance(key, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,100}', key)
                and not key.endswith('.') and key.split('.')[0].upper() not in reserved
                and not PRIVATE_WORDS.search(key), 'PUBLIC_CASE_ID_INVALID')
        require(key.casefold() not in identifiers, 'DUPLICATE_CASE_ID')
        identifiers.add(key.casefold())
        count = case['primary_target_count']
        require(type(count) is int and count > 0 and budget_level_for_primary_targets(count) == case['level'],
                'PUBLIC_BUDGET_LEVEL_MISMATCH')
        require(case['category'] in {'geometry', 'property', 'mixed'}, 'INVALID_TASK_KIND')
        for field, suffix, digest_name in [('model_path', '.ifc', 'model.ifc'), ('request_path', '.txt', 'request.txt')]:
            path = _pair_safe_path(Path(case[field]))
            require(path.is_file() and path.suffix.lower() == suffix and path.stat().st_size > 0,
                    'INVALID_PUBLIC_INPUT')
            require(sha256(path) == case['input_digests'][digest_name], 'PUBLIC_INPUT_BINDING_CHANGED')
        require(Path(case['request_path']).read_text(encoding='utf-8-sig').strip(), 'EMPTY_PUBLIC_REQUEST')
        rows.append({'case_id': key, 'ifc_path': f'cases/{key}/model.ifc',
                     'request_path': f'cases/{key}/request.txt', 'level': case['level'],
                     'primary_target_count': count, 'task_kind': case['category']})
    return rows


def _export_file_set(public):
    files = set()
    for entry in public.rglob('*'):
        entry = _pair_safe_path(entry)
        if entry.is_file():
            files.add(entry.relative_to(public).as_posix())
    return files


def check_export(public, evaluation):
    public, evaluation = _pair_safe_path(Path(public)), _pair_safe_path(Path(evaluation))
    _disjoint(public, evaluation)
    receipt = read(evaluation / 'export.json')
    require(receipt.get('status') == 'complete' and receipt.get('public_root') == str(public), 'EXPORT_RECEIPT_BINDING_FAILED')
    cases = load_pair_candidates(public)
    allowed = {'inputs.csv', *[Path(case[field]).relative_to(public).as_posix()
                              for case in cases for field in ('model_path', 'request_path')]}
    require(_export_file_set(public) == set(receipt['public_file_sha256']) == allowed, 'EXPORT_FILE_SET_CHANGED')
    for relative, expected in receipt['public_file_sha256'].items():
        require(sha256(public / relative) == expected, 'EXPORT_INPUT_BINDING_CHANGED:' + relative)
    require(len(cases) == receipt['cases'], 'EXPORT_CASE_COUNT_CHANGED')
    return {'status': 'complete', 'cases': len(cases), 'public_root': str(public),
            'evaluation_root': str(evaluation), 'budget_levels': dict(Counter(c['level'] for c in cases)),
            'task_kinds': dict(Counter(c['category'] for c in cases)),
            'public_files': len(receipt['public_file_sha256']), 'live_stage_admission': False,
            'validation_scope': 'saved export receipt, public file whitelist/hash and CSV checks; no upstream/native/mesh revalidation'}


def export_public(dataset, output, evaluation, *, repository_root=ROOT):
    """Create a strict public whitelist and a separate evaluator-only receipt."""
    dataset = _pair_safe_path(Path(dataset))
    public, evaluation = _pair_safe_path(Path(output)), _pair_safe_path(Path(evaluation))
    _disjoint(dataset, public, evaluation)
    public, evaluation = _new(public), _new(evaluation)
    summary, candidates = check_dataset(dataset, repository_root=repository_root)
    rows = _public_rows(candidates)  # Reject bad IDs/paths/budgets before creating either destination.
    bindings = {path: value for case in candidates
                for path, value in case.get('upstream_admission', {}).get('metadata_bindings', {}).items()}
    bindings.update({case[field]: case['input_digests'][name] for case in candidates
                     for field, name in [('model_path', 'model.ifc'), ('request_path', 'request.txt')]})
    evaluation.mkdir(parents=True)
    public.mkdir(parents=True)
    try:
        hashes = {}
        for case, row in zip(candidates, rows, strict=True):
            for source_name, output_name, digest_name in [('model_path', 'ifc_path', 'model.ifc'),
                                                        ('request_path', 'request_path', 'request.txt')]:
                source, target = _pair_safe_path(Path(case[source_name])), public / row[output_name]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                expected = case['input_digests'][digest_name]
                require(sha256(target) == sha256(source) == expected, 'PUBLIC_INPUT_CHANGED_DURING_COPY')
                hashes[row[output_name]] = expected
        require(all(sha256(_pair_safe_path(Path(path))) == expected for path, expected in bindings.items()),
                'DATASET_CHANGED_DURING_EXPORT')
        with (public / 'inputs.csv').open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        hashes['inputs.csv'] = sha256(public / 'inputs.csv')
        # This is the same parser used by experiment prepare; it does not grant native/live admission.
        require(len(load_pair_candidates(public)) == len(rows), 'EXPORT_PAIR_ADAPTER_MISMATCH')
        receipt = {'status': 'complete', 'source_dataset': str(dataset), 'public_root': str(public),
                   'cases': len(rows), 'source_models': summary['source_models'],
                   'machine_validated_cases': len(rows), 'human_reviewed_cases': summary.get('human_reviewed_cases', 0),
                   'provider_calls': 0, 'live_stage_admission': False,
                   'dataset_summary_sha256': sha256(dataset / 'summary.json'),
                   'public_file_sha256': hashes, 'source_metadata_bindings': bindings,
                   'case_provenance': [{'row': row, 'source_id': case['source_id'],
                                        'dataset_path': case['dataset_path']} for row, case in zip(rows, candidates, strict=True)],
                   'operator_sha256': sha256(Path(__file__)),
                   'scope': 'Exact public IFC/request copies; prior sealed native/prompt/wall/mesh checks; no native rerun, system repair or human acceptance.'}
        (evaluation / 'export.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        return check_export(public, evaluation)
    except Exception as exc:
        (evaluation / 'export-failed.json').write_text(json.dumps({'status': 'failed', 'error': f'{type(exc).__name__}: {exc}',
            'scope': 'Partial outputs retained; use new destinations for a retry.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        raise


def _brief(root):
    summary = read(Path(root) / 'summary.json')
    result = {k: summary[k] for k in ('status', 'source_models', 'target_cases', 'machine_validated_cases',
                                    'human_reviewed_cases', 'attempted_cases', 'failed_attempts', 'provider_calls') if k in summary}
    result['report'] = str(Path(root).resolve() / 'REPORT.md')
    if type(summary.get('target_cases')) is int and type(summary.get('machine_validated_cases')) is int:
        result['missing_cases'] = max(0, summary['target_cases'] - summary['machine_validated_cases'])
    if isinstance(summary.get('worker_errors'), list):
        result['worker_error_count'] = len(summary['worker_errors'])
    return result


class ChildFailure(RuntimeError):
    def __init__(self, returncode, log, details):
        super().__init__(f'CHILD_FAILED: exit={returncode}; log={log}')
        self.details = {'exit_code': returncode, 'log': str(log), **details}


def _child(command, output):
    output = _new(output)
    log = ROOT / '.tmp/dataset-operator-logs' / (uuid.uuid4().hex + '.log')
    log.parent.mkdir(parents=True, exist_ok=True)
    environment = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    with log.open('w', encoding='utf-8') as stream:
        result = subprocess.run([sys.executable, '-B', *command], cwd=ROOT, env=environment,
                                stdout=stream, stderr=subprocess.STDOUT, check=False)
    if output.is_dir():
        (output / 'private').mkdir(exist_ok=True)
        shutil.copyfile(log, output / 'private/operator.log')
        log = output / 'private/operator.log'
    if result.returncode != 0:
        details = {}
        if (output / 'summary.json').is_file():
            try:
                details = _brief(output)
                details['dataset_status'] = details.pop('status', 'unknown')
            except Exception as exc:
                details = {'summary_error': f'{type(exc).__name__}: {exc}'[:400]}
        raise ChildFailure(result.returncode, log, details)
    return {**_brief(output), 'log': str(output / 'private/operator.log')}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    generate = sub.add_parser('generate', help='bounded pilot; reuses generate_damage_pilot.py')
    inputs = generate.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--input', type=Path)
    inputs.add_argument('--sources', type=Path)
    generate.add_argument('--output', type=Path, required=True)
    generate.add_argument('--cases-per-ifc', type=int, choices=range(1, 9), default=2)
    generate.add_argument('--workers', type=int, choices=(1, 2), default=2)
    generate.add_argument('--seed', type=int, default=20261010)
    generate.add_argument('--request-profile', choices=('1.2', '1.3'), default='1.3')
    collect = sub.add_parser('collect', help='copy complete sources and reuse sealed receipts')
    collect.add_argument('--origin', type=Path, action='append', required=True)
    collect.add_argument('--source-id', action='append', required=True)
    collect.add_argument('--output', type=Path, required=True)
    collect.add_argument('--cases-per-ifc', type=int, choices=range(1, 9), default=2)
    export = sub.add_parser('export', help='public IFC/TXT/inputs.csv only; separate evaluator receipt')
    export.add_argument('--dataset', type=Path, required=True)
    export.add_argument('--output', type=Path, required=True)
    export.add_argument('--evaluation-output', type=Path, required=True)
    for name in ('check', 'status'):
        command = sub.add_parser(name)
        command.add_argument('--dataset', type=Path, required=True)
        if name == 'check':
            command.add_argument('--evaluation-output', type=Path, help='check an exported public bundle against its separate receipt')
    args = parser.parse_args(argv)
    try:
        if args.command == 'generate':
            source_flag = '--input' if args.input else '--sources'
            result = _child([str(ROOT / 'scripts/ifc_repair/generate_damage_pilot.py'), source_flag,
                str((args.input or args.sources).resolve()), '--output', str(args.output.resolve()),
                '--cases-per-ifc', str(args.cases_per_ifc), '--workers', str(args.workers),
                '--seed', str(args.seed), '--request-profile', args.request_profile], args.output)
        elif args.command == 'collect':
            command = [str(ROOT / 'scripts/ifc_repair/collect_damage_pilot.py'), '--output', str(args.output.resolve()),
                       '--cases-per-ifc', str(args.cases_per_ifc)]
            for origin in args.origin: command.extend(['--origin', str(origin.resolve())])
            for source in args.source_id: command.extend(['--source-id', source])
            result = _child(command, args.output)
        elif args.command == 'export':
            result = export_public(args.dataset, args.output, args.evaluation_output)
        elif args.command == 'check':
            if args.evaluation_output:
                result = check_export(args.dataset, args.evaluation_output)
            else:
                _, candidates = check_dataset(args.dataset)
                result = {**_brief(args.dataset), 'checked_cases': len(candidates),
                          'validation_scope': 'sealed receipt/hash/index checks; no new native or mesh execution'}
        else:
            result = _brief(args.dataset)
        print(json.dumps({'event': 'summary', 'command': args.command, **result}, ensure_ascii=False))
        return 0
    except Exception as exc:
        details = exc.details if isinstance(exc, ChildFailure) else {}
        print(json.dumps({**details, 'event': 'summary', 'command': args.command, 'status': 'failed',
                          'error': f'{type(exc).__name__}: {exc}'[:1200], 'provider_calls': 0}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
