"""Orchestration/public export boundaries; opaque fixtures are never native evidence."""
from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path
import shutil
import stat
import subprocess
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.dataset_batch.validation import sha256
from scripts.ifc_repair.repair_comparison.batch_cases import load_pair_candidates


def api():
    return importlib.import_module('scripts.ifc_repair.dataset_operator')


@pytest.fixture
def opaque_checked_dataset(tmp_path, monkeypatch):
    """Mock only upstream admission, then exercise real CSV/copy/path boundaries."""
    root = tmp_path / 'dataset'
    cases = []
    for i, (count, level, kind) in enumerate([(1, 'S1', 'geometry'), (2, 'S2', 'mixed'), (4, 'S3', 'geometry')], 1):
        folder = root / 'sources/source-a/cases' / f'case-{i:03d}-a01'
        public = folder / 'public'
        public.mkdir(parents=True)
        (public / 'model.ifc').write_bytes(f'OPAQUE IFC {i}'.encode())
        (public / 'request.txt').write_bytes(f'请恢复构件 {i}。\r\n'.encode('utf-8'))
        (public / 'request-world.txt').write_text('额外变体，不作为新题', encoding='utf-8')
        (folder / 'private').mkdir()
        (folder / 'private/reference.ifc').write_bytes(b'PRIVATE-GOLD-SENTINEL')
        (folder / 'private/answer-card.json').write_text('PRIVATE-ANSWER-SENTINEL', encoding='utf-8')
        cases.append({'case_id': f'source-a-{folder.name}', 'dataset_path': folder.relative_to(root).as_posix(),
                      'model_path': str(public / 'model.ifc'), 'request_path': str(public / 'request.txt'),
                      'level': level, 'primary_target_count': count, 'category': kind,
                      'source_id': 'source-a', 'input_digests': {'model.ifc': sha256(public / 'model.ifc'),
                                                               'request.txt': sha256(public / 'request.txt')}})
    summary = {'status': 'complete', 'source_models': 1, 'target_cases': 3,
               'machine_validated_cases': 3, 'human_reviewed_cases': 0, 'provider_calls': 0}
    (root / 'summary.json').write_text(json.dumps(summary), encoding='utf-8')
    monkeypatch.setattr(api(), 'check_dataset', lambda *args, **kwargs: (summary, cases))
    return root, cases


def test_public_export_only_contains_exact_pairs_and_six_columns(opaque_checked_dataset, tmp_path):
    source, candidates = opaque_checked_dataset
    public, evaluation = tmp_path / 'public', tmp_path / 'evaluation'
    result = api().export_public(source, public, evaluation)
    assert result['status'] == 'complete' and result['cases'] == 3
    rows = list(csv.DictReader((public / 'inputs.csv').open(encoding='utf-8', newline='')))
    assert set(rows[0]) == {'case_id', 'ifc_path', 'request_path', 'level', 'primary_target_count', 'task_kind'}
    assert {p.relative_to(public).as_posix() for p in public.rglob('*') if p.is_file()} == {
        'inputs.csv', *[r[k] for r in rows for k in ('ifc_path', 'request_path')]}
    for row, candidate in zip(rows, candidates, strict=True):
        assert (public / row['ifc_path']).read_bytes() == Path(candidate['model_path']).read_bytes()
        assert (public / row['request_path']).read_bytes() == Path(candidate['request_path']).read_bytes()
        assert row['primary_target_count'] == str(candidate['primary_target_count'])
    pairs = load_pair_candidates(public)
    assert [p['level'] for p in pairs] == ['S1', 'S2', 'S3']
    assert all(p['upstream_admission']['live_stage_admission'] is False for p in pairs)
    assert (evaluation / 'export.json').is_file()
    assert not any('private' in p.as_posix() or 'reference' in p.name for p in public.rglob('*'))
    assert api().check_export(public, evaluation)['cases'] == 3
    (public / rows[0]['request_path']).write_text('改写请求', encoding='utf-8')
    with pytest.raises(ValueError, match='EXPORT.*BINDING'):
        api().check_export(public, evaluation)


@pytest.mark.parametrize('destination', ['source_child', 'source_parent', 'evaluation_in_public', 'same_destination', 'existing'])
def test_export_rejects_overlap_or_existing_destination(opaque_checked_dataset, tmp_path, destination):
    source, _ = opaque_checked_dataset
    public, evaluation = tmp_path / 'public', tmp_path / 'evaluation'
    if destination == 'source_child': public = source / 'exported'
    if destination == 'source_parent': public = tmp_path
    if destination == 'evaluation_in_public': evaluation = public / 'private'
    if destination == 'same_destination': evaluation = public
    if destination == 'existing': public.mkdir()
    with pytest.raises((ValueError, FileExistsError)):
        api().export_public(source, public, evaluation)
    assert not evaluation.exists()


@pytest.mark.parametrize('change', ['duplicate_id', 'long_id', 'reserved_id', 'private_id', 'wrong_level', 'empty_request', 'changed_model'])
def test_export_rejects_invalid_or_drifted_public_inputs_before_writing(opaque_checked_dataset, tmp_path, change):
    source, cases = opaque_checked_dataset
    if change == 'duplicate_id': cases[1]['case_id'] = cases[0]['case_id'].upper()
    if change == 'long_id': cases[0]['case_id'] = 'a' * 102
    if change == 'reserved_id': cases[0]['case_id'] = 'CON'
    if change == 'private_id': cases[0]['case_id'] = 'private-reference'
    if change == 'wrong_level': cases[0]['level'] = 'S3'
    if change == 'empty_request': Path(cases[0]['request_path']).write_text(' ', encoding='utf-8')
    if change == 'changed_model': Path(cases[0]['model_path']).write_bytes(b'changed')
    public, evaluation = tmp_path / 'public', tmp_path / 'evaluation'
    with pytest.raises(ValueError):
        api().export_public(source, public, evaluation)
    assert not public.exists() and not evaluation.exists()


def test_export_rejects_hardlink_metadata(opaque_checked_dataset, tmp_path, monkeypatch):
    source, cases = opaque_checked_dataset
    model = Path(cases[0]['model_path'])
    # This Windows sandbox denies creating real hardlinks. Simulate only the
    # link count; keep the production path guard and all copying logic real.
    original_stat = Path.stat
    def linked_stat(path, *args, **kwargs):
        value = original_stat(path, *args, **kwargs)
        if path == model:
            # Preserve Windows-only file attributes as well as ordinary stat fields.
            fields = {name: getattr(value, name) for name in dir(value) if name.startswith('st_')}
            fields['st_nlink'] = 2
            return SimpleNamespace(**fields)
        return value
    monkeypatch.setattr(Path, 'stat', linked_stat)
    with pytest.raises(ValueError, match='LINK'):
        api().export_public(source, tmp_path / 'public', tmp_path / 'evaluation')


@pytest.mark.parametrize('node', ['file', 'ancestor'])
def test_export_rejects_windows_reparse_metadata(opaque_checked_dataset, tmp_path, monkeypatch, node):
    source, cases = opaque_checked_dataset
    model = Path(cases[0]['model_path'])
    blocked = model if node == 'file' else model.parent
    original_lstat = Path.lstat
    def reparse_stat(path, *args, **kwargs):
        value = original_lstat(path, *args, **kwargs)
        if path == blocked:
            return SimpleNamespace(st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)
        return value
    monkeypatch.setattr(Path, 'lstat', reparse_stat)
    with pytest.raises(ValueError, match='LINK_PATH_NOT_ALLOWED'):
        api().export_public(source, tmp_path / 'public', tmp_path / 'evaluation')
    assert not (tmp_path / 'public').exists()


def test_check_export_rejects_extra_file(opaque_checked_dataset, tmp_path):
    source, _ = opaque_checked_dataset
    public, evaluation = tmp_path / 'public', tmp_path / 'evaluation'
    api().export_public(source, public, evaluation)
    (public / 'notes.txt').write_text('unlisted input', encoding='utf-8')
    with pytest.raises(ValueError, match='EXPORT_FILE_SET'):
        api().check_export(public, evaluation)


def test_export_rechecks_earlier_source_inputs_after_copying_other_cases(opaque_checked_dataset, tmp_path, monkeypatch):
    source, candidates = opaque_checked_dataset
    public, evaluation = tmp_path / 'public', tmp_path / 'evaluation'
    original_copy = shutil.copyfile
    def drift_on_later_copy(src, dst, *args, **kwargs):
        result = original_copy(src, dst, *args, **kwargs)
        if Path(src) == Path(candidates[1]['model_path']):
            Path(candidates[0]['request_path']).write_text('changed after its copy', encoding='utf-8')
        return result
    monkeypatch.setattr(api().shutil, 'copyfile', drift_on_later_copy)
    with pytest.raises(ValueError, match='DATASET_CHANGED_DURING_EXPORT'):
        api().export_public(source, public, evaluation)
    assert public.exists() and (evaluation / 'export-failed.json').is_file()
    assert not (evaluation / 'export.json').exists()


def test_check_export_whitelist_is_derived_from_csv_not_receipt(opaque_checked_dataset, tmp_path):
    source, _ = opaque_checked_dataset
    public, evaluation = tmp_path / 'public', tmp_path / 'evaluation'
    api().export_public(source, public, evaluation)
    extra = public / 'private/answer-card.json'
    extra.parent.mkdir()
    extra.write_text('PRIVATE-ANSWER-SENTINEL', encoding='utf-8')
    receipt_path = evaluation / 'export.json'
    receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
    receipt['public_file_sha256']['private/answer-card.json'] = sha256(extra)
    receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
    with pytest.raises(ValueError, match='EXPORT_FILE_SET'):
        api().check_export(public, evaluation)


def test_real_two_case_pilot_exports_with_unchanged_native_receipts(scene_factory, tmp_path):
    from scripts.ifc_repair.dataset_batch.pilot import process_source, write_report
    from scripts.ifc_repair.dataset_batch.validation import program_hash
    model = scene_factory(tmp_path / 'source.ifc')
    origin = tmp_path / 'origin'
    origin.mkdir()
    spec = {'source_id': 'real-fixture', 'input_path': str(model),
            'request_profile': 'text2ifc/dataset-request/1.3', 'pilot_families': ['window', 'beam_column']}
    source = process_source(spec, tmp_path, origin, 2, 20261010)
    assert source['status'] == 'complete'
    write_report(origin, [source], [], 2)
    (origin / 'build.json').write_text(json.dumps({'schema_version': 'text2ifc/dataset-pilot-build/1.0',
        'configuration': {'program_sha256': program_hash(), 'cases_per_ifc': 2}}), encoding='utf-8')
    before = {p.relative_to(origin).as_posix(): sha256(p) for p in origin.rglob('*') if p.is_file()}
    public, evaluation = tmp_path / 'public', tmp_path / 'evaluation'
    result = api().export_public(origin, public, evaluation, repository_root=tmp_path)
    assert result['cases'] == 2
    assert {p.relative_to(origin).as_posix(): sha256(p) for p in origin.rglob('*') if p.is_file()} == before
    candidates = load_pair_candidates(public)
    assert {c['primary_target_count'] for c in candidates} == {1, 2}
    assert {c['level'] for c in candidates} == {'S1', 'S2'}


def test_generate_wrapper_uses_existing_cap_and_prints_one_summary(tmp_path, monkeypatch, capsys):
    destination = tmp_path / 'generated'
    observed = []
    def child(command, **kwargs):
        observed.append(command)
        assert '--cases-per-ifc' in command and command[command.index('--cases-per-ifc') + 1] == '2'
        assert command[command.index('--request-profile') + 1] == '1.3'
        destination.mkdir()
        (destination / 'summary.json').write_text(json.dumps({'status': 'complete', 'source_models': 1,
            'target_cases': 2, 'machine_validated_cases': 2, 'provider_calls': 0}), encoding='utf-8')
        kwargs['stdout'].write('child detailed progress\n')
        return subprocess.CompletedProcess(command, 0)
    monkeypatch.setattr(api().subprocess, 'run', child)
    assert api().main(['generate', '--input', str(tmp_path / 'input.ifc'), '--output', str(destination)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1 and json.loads(lines[0])['event'] == 'summary'
    assert observed and (destination / 'private/operator.log').read_text(encoding='utf-8').strip() == 'child detailed progress'


def test_status_does_not_generate_check_or_export(opaque_checked_dataset, monkeypatch, capsys):
    root, _ = opaque_checked_dataset
    monkeypatch.setattr(api(), 'check_dataset', lambda *args, **kwargs: pytest.fail('status must not revalidate'))
    assert api().main(['status', '--dataset', str(root)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary['event'] == 'summary' and summary['machine_validated_cases'] == 3


@pytest.mark.parametrize('with_summary', [True, False])
def test_failed_child_preserves_available_counts_in_single_summary(tmp_path, monkeypatch, capsys, with_summary):
    destination = tmp_path / 'incomplete'
    def child(command, **kwargs):
        destination.mkdir()
        if with_summary:
            (destination / 'summary.json').write_text(json.dumps({
                'status': 'incomplete', 'source_models': 2, 'target_cases': 8,
                'machine_validated_cases': 3, 'attempted_cases': 5, 'failed_attempts': 2,
                'worker_errors': [{'source_id': 'third', 'error': 'source rejected'}],
                'human_reviewed_cases': 0, 'provider_calls': 0}), encoding='utf-8')
        kwargs['stdout'].write('failure details retained\n')
        return subprocess.CompletedProcess(command, 2)
    monkeypatch.setattr(api().subprocess, 'run', child)
    assert api().main(['generate', '--input', str(tmp_path / 'input.ifc'),
                       '--output', str(destination), '--cases-per-ifc', '4']) == 2
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    summary = json.loads(lines[0])
    assert summary['event'] == 'summary' and summary['status'] == 'failed'
    assert summary['exit_code'] == 2
    assert Path(summary['log']).read_text(encoding='utf-8').strip() == 'failure details retained'
    if with_summary:
        assert summary['dataset_status'] == 'incomplete'
        assert summary['target_cases'] == 8 and summary['machine_validated_cases'] == 3
        assert summary['missing_cases'] == 5
        assert summary['attempted_cases'] == 5 and summary['failed_attempts'] == 2
        assert summary['worker_error_count'] == 1
        assert summary['report'] == str(destination / 'REPORT.md')
    else:
        assert 'target_cases' not in summary and 'missing_cases' not in summary
