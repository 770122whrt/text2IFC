"""Pair exports; opaque fixtures prove boundaries, never native IFC validity."""
from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path
import shutil

import ifcopenshell
import pytest

from scripts.ifc_repair.dataset_batch.engine import seal_case
from scripts.ifc_repair.dataset_batch.validation import sha256
from scripts.ifc_repair.repair_comparison.batch_cases import load_pair_candidates


def api():
    return importlib.import_module('scripts.ifc_repair.dataset_pair_export')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False) + '\n', encoding='utf-8')


def record(source_root, case, mode, *, damage_id='formal-021-d001', case_id=None):
    return {'case_id': case_id or f'{damage_id}-{mode}', 'source_id': 'formal-021',
            'damage_id': damage_id, 'locator_mode': mode,
            'case_path': case.relative_to(source_root).as_posix(),
            'request_relative_path': f'public/request-{mode}.txt',
            'model_sha256': sha256(case / 'public/model.ifc'),
            'request_sha256': sha256(case / f'public/request-{mode}.txt'),
            'primary_target_count': 1, 'task_kind': 'geometry'}


@pytest.fixture
def opaque_sealed_pair_source(tmp_path):
    """Explicitly synthetic sealed receipts, with no claimed native execution."""
    batch = tmp_path / 'batch'
    source = batch / 'private/production'
    folder = source / 'sources/formal-021'
    case = folder / 'cases/damage-001'
    (case / 'public').mkdir(parents=True)
    (folder / 'private').mkdir(parents=True)
    (folder / 'private/reference.ifc').write_bytes(b'OPAQUE PRIVATE REFERENCE; NO NATIVE EVIDENCE')
    reference_hash = sha256(folder / 'private/reference.ifc')
    write(folder / 'private/source.json', {'source_id': 'formal-021', 'source_sha256': reference_hash,
          'fixture_kind': 'opaque simulated receipts, not native evidence'})
    write(folder / 'private/source-validation.json', {'passed': True, 'finding_count': 0,
          'express_rules': True, 'schema': 'IFC2X3', 'ifcopenshell_version': ifcopenshell.version,
          'input_sha256': reference_hash, 'fixture_kind': 'simulated source-native receipt'})
    (case / 'public/model.ifc').write_bytes(b'OPAQUE DAMAGED IFC\r\n')
    for mode, text in [('world', '请恢复世界坐标指定的窗。\r\n'),
                       ('host_wall', '\ufeff请恢复主墙上指定的窗。\n')]:
        (case / f'public/request-{mode}.txt').write_bytes(text.encode('utf-8'))
    templates = {mode: {'applicable': True, 'sha256': sha256(case / f'public/request-{mode}.txt')}
                 for mode in ('world', 'host_wall')}
    meta = {'schema_version': 'text2ifc/ifc-repair-dataset-case/1.1', 'status': 'passed',
            'machine_validated': True, 'human_reviewed': False, 'source_unchanged': True,
            'private_identity_leakage': False, 'information_sufficient': True,
            'wall_check_passed': True, 'wall_check_applicable': True,
            'independent_mesh_check_passed': True, 'source_sha256': reference_hash,
            'damaged_sha256': sha256(case / 'public/model.ifc'),
            'deleted_counts': {'door': 0, 'window': 1, 'beam': 0, 'column': 0},
            'property_changes': 0, 'prompt_templates': templates,
            'additional_evidence': ['private/prompt-check.json', 'private/wall-check.json',
                                    'private/mesh-check.json']}
    write(case / 'case.json', meta)
    write(case / 'private/mutation.json', {'schema_version': 'text2ifc/ifc-repair-dataset-mutation/1.3',
          'prompt_profile': 'text2ifc/dataset-request/1.3', 'source_sha256': reference_hash,
          'damaged_sha256': meta['damaged_sha256'],
          'deletions': [{'guid': 'private-hidden-window', 'ifc_class': 'IfcWindow'}], 'property_changes': []})
    write(case / 'private/recipe.json', {'fixture_kind': 'opaque, no mutation execution'})
    write(case / 'private/validation.json', {'passed': True, 'finding_count': 0,
          'express_rules': True, 'schema': 'IFC2X3', 'ifcopenshell_version': ifcopenshell.version,
          'fixture_kind': 'simulated native receipt'})
    write(case / 'private/preservation.json', {'passed': True, 'fixture_kind': 'simulated receipt'})
    write(case / 'private/prompt-check.json', {mode: {'passed': True, 'errors': []} for mode in templates})
    write(case / 'private/wall-check.json', {'passed': True, 'applicable': True, 'errors': []})
    write(case / 'private/mesh-check.json', {'passed': True, 'errors': []})
    seal_case(case)
    pairs = [record(source, case, mode) for mode in ('world', 'host_wall')]
    return source, batch / 'public', batch / 'private/evaluation', case, pairs


def test_two_locator_pairs_are_separate_rows_with_identical_ifc_bytes(opaque_sealed_pair_source):
    source, public, evaluation, case, pairs = opaque_sealed_pair_source
    before = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob('*') if p.is_file()}
    result = api().export_pairs(source, public, evaluation, pairs, source_models=1)
    assert result['status'] == 'complete'
    assert result['pairs'] == 2 and result['distinct_damages'] == 1 and result['source_models'] == 1
    assert result['public_files'] == 5 and result['live_stage_admission'] is False
    rows = list(csv.DictReader((public / 'inputs.csv').open(encoding='utf-8', newline='')))
    assert list(rows[0]) == ['case_id', 'ifc_path', 'request_path', 'level', 'primary_target_count', 'task_kind']
    assert {p.relative_to(public).as_posix() for p in public.rglob('*') if p.is_file()} == {
        'inputs.csv', *[r[k] for r in rows for k in ('ifc_path', 'request_path')]}
    for row, pair in zip(rows, pairs, strict=True):
        assert (public / row['ifc_path']).read_bytes() == (case / 'public/model.ifc').read_bytes()
        assert (public / row['request_path']).read_bytes() == (case / pair['request_relative_path']).read_bytes()
        assert (row['level'], row['task_kind'], row['primary_target_count']) == ('S1', 'geometry', '1')
    assert len(load_pair_candidates(public)) == 2
    receipt = json.loads((evaluation / 'export.json').read_text(encoding='utf-8'))
    assert receipt['schema_version'] == 'text2ifc/dataset-pair-export/1.0'
    assert len(receipt['pair_provenance']) == 2 and receipt['bound_hashes']
    assert {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob('*') if p.is_file()} == before
    assert api().check_pair_export(public, evaluation)['pairs'] == 2


@pytest.mark.parametrize('change', ['case_id', 'damage_mode'])
def test_rejects_duplicate_pair_identity_before_output(opaque_sealed_pair_source, change):
    source, public, evaluation, _, pairs = opaque_sealed_pair_source
    if change == 'case_id':
        pairs[1]['case_id'] = pairs[0]['case_id'].upper()
    else:
        pairs.append({**pairs[0], 'case_id': 'another-case'})
    with pytest.raises(ValueError, match='DUPLICATE'):
        api().export_pairs(source, public, evaluation, pairs, source_models=1)
    assert not public.exists() and not evaluation.exists()


@pytest.mark.parametrize('change', ['case_escape', 'request_private', 'mode', 'wrong_count', 'wrong_kind',
                                  'wrong_model_hash', 'source_count', 'private_case_id'])
def test_rejects_invalid_pair_records_before_output(opaque_sealed_pair_source, change):
    source, public, evaluation, _, pairs = opaque_sealed_pair_source
    source_count = 1
    if change == 'case_escape': pairs[0]['case_path'] = '../outside'
    if change == 'request_private': pairs[0]['request_relative_path'] = 'private/reference.ifc'
    if change == 'mode': pairs[0]['locator_mode'] = 'storey_local'
    if change == 'wrong_count': pairs[0]['primary_target_count'] = 2
    if change == 'wrong_kind': pairs[0]['task_kind'] = 'property'
    if change == 'wrong_model_hash': pairs[0]['model_sha256'] = '0' * 64
    if change == 'source_count': source_count = 2
    if change == 'private_case_id': pairs[0]['case_id'] = 'private-gold-answer'
    with pytest.raises(ValueError):
        api().export_pairs(source, public, evaluation, pairs, source_models=source_count)
    assert not public.exists() and not evaluation.exists()


@pytest.mark.parametrize('receipt_name', ['case.json', 'private/validation.json', 'private/preservation.json',
                                       'private/prompt-check.json', 'private/wall-check.json', 'private/mesh-check.json'])
def test_rejects_failed_receipts_even_after_resealing(opaque_sealed_pair_source, receipt_name):
    source, public, evaluation, case, pairs = opaque_sealed_pair_source
    path = case / receipt_name
    value = json.loads(path.read_text(encoding='utf-8'))
    if receipt_name == 'case.json': value['machine_validated'] = False
    elif receipt_name == 'private/prompt-check.json': value['host_wall']['passed'] = False
    else: value['passed'] = False
    write(path, value)
    seal_case(case)
    with pytest.raises(ValueError):
        api().export_pairs(source, public, evaluation, pairs, source_models=1)
    assert not public.exists() and not evaluation.exists()


def test_rejects_same_damage_id_pointing_to_a_different_case(opaque_sealed_pair_source):
    source, public, evaluation, case, pairs = opaque_sealed_pair_source
    other = case.parent / 'damage-002'
    shutil.copytree(case, other)
    pairs[1] = record(source, other, 'host_wall')
    with pytest.raises(ValueError, match='DAMAGE.*BINDING'):
        api().export_pairs(source, public, evaluation, pairs, source_models=1)
    assert not public.exists() and not evaluation.exists()


def test_rejects_changed_seal_and_reference_bytes(opaque_sealed_pair_source):
    source, public, evaluation, case, pairs = opaque_sealed_pair_source
    (case / 'private/prompt-check.json').write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError, match='SEAL'):
        api().export_pairs(source, public, evaluation, pairs, source_models=1)
    seal_case(case)
    (case.parent.parent / 'private/reference.ifc').write_bytes(b'CHANGED REFERENCE')
    with pytest.raises(ValueError):
        api().export_pairs(source, public, evaluation, pairs, source_models=1)


def test_all_source_bindings_are_rechecked_after_the_last_copy(opaque_sealed_pair_source, monkeypatch):
    source, public, evaluation, case, pairs = opaque_sealed_pair_source
    original = api().shutil.copyfile
    def copy(source_file, destination):
        result = original(source_file, destination)
        if Path(source_file).name == 'request-host_wall.txt':
            (case / 'public/request-world.txt').write_bytes(b'CHANGED AFTER FIRST PAIR COPY')
        return result
    monkeypatch.setattr(api().shutil, 'copyfile', copy)
    with pytest.raises(ValueError, match='SOURCE.*CHANGED'):
        api().export_pairs(source, public, evaluation, pairs, source_models=1)
    assert not (evaluation / 'export.json').exists()
    assert (evaluation / 'export-failed.json').is_file()


def test_check_whitelist_does_not_trust_extra_receipt_entries(opaque_sealed_pair_source):
    source, public, evaluation, _, pairs = opaque_sealed_pair_source
    api().export_pairs(source, public, evaluation, pairs, source_models=1)
    extra = public / 'private/answer-card.json'
    write(extra, {'hidden': 'PRIVATE ANSWER SENTINEL'})
    path = evaluation / 'export.json'
    receipt = json.loads(path.read_text(encoding='utf-8'))
    receipt['public_file_sha256']['private/answer-card.json'] = sha256(extra)
    write(path, receipt)
    with pytest.raises(ValueError, match='FILE_SET'):
        api().check_pair_export(public, evaluation)


def test_roots_must_not_contain_each_other(opaque_sealed_pair_source):
    source, public, _, _, pairs = opaque_sealed_pair_source
    with pytest.raises(ValueError):
        api().export_pairs(source, public, public / 'evaluation', pairs, source_models=1)
    assert not public.exists()


@pytest.mark.parametrize('change', ['source_native_missing', 'source_native_failed', 'property_class',
                                  'model_size_limit', 'request_digest_missing', 'case_digest_missing'])
def test_rejects_missing_admission_and_scope_boundaries(opaque_sealed_pair_source, change):
    source, public, evaluation, case, pairs = opaque_sealed_pair_source
    native = case.parent.parent / 'private/source-validation.json'
    if change == 'source_native_missing':
        native.rename(native.with_suffix('.saved'))  # Retain the negative fixture evidence.
    elif change == 'source_native_failed':
        receipt = json.loads(native.read_text(encoding='utf-8'))
        receipt['passed'] = False
        write(native, receipt)
    else:
        meta = json.loads((case / 'case.json').read_text(encoding='utf-8'))
        mutation = json.loads((case / 'private/mutation.json').read_text(encoding='utf-8'))
        if change == 'property_class':
            mutation['property_changes'] = [{'guid': 'private-surviving-wall', 'ifc_class': 'IfcWall'}]
            meta['property_changes'] = 1
            for pair in pairs:
                pair.update(primary_target_count=2, task_kind='mixed')
        if change == 'model_size_limit':
            with (case / 'public/model.ifc').open('wb') as stream:
                stream.truncate(20_000_000)
            digest = sha256(case / 'public/model.ifc')
            meta['damaged_sha256'] = mutation['damaged_sha256'] = digest
            for pair in pairs:
                pair['model_sha256'] = digest
        if change == 'request_digest_missing':
            meta['prompt_templates']['world'].pop('sha256')
        if change == 'case_digest_missing':
            meta.pop('source_sha256')
            meta.pop('damaged_sha256')
        write(case / 'case.json', meta)
        write(case / 'private/mutation.json', mutation)
        seal_case(case)
    with pytest.raises(ValueError):
        api().export_pairs(source, public, evaluation, pairs, source_models=1)
    assert not public.exists() and not evaluation.exists()


@pytest.mark.parametrize('kind,deleted,property_guids,count,level', [
    ('property', 0, ['private-survivor', 'private-survivor'], 1, 'S1'),
    ('mixed', 1, ['private-survivor', 'private-survivor'], 2, 'S2'),
    ('geometry', 3, [], 3, 'S3'),
])
def test_count_and_budget_use_distinct_primary_products(opaque_sealed_pair_source, kind, deleted,
                                                      property_guids, count, level):
    source, public, evaluation, case, pairs = opaque_sealed_pair_source
    meta = json.loads((case / 'case.json').read_text(encoding='utf-8'))
    mutation = json.loads((case / 'private/mutation.json').read_text(encoding='utf-8'))
    mutation['deletions'] = [{'guid': f'private-hidden-window-{index}', 'ifc_class': 'IfcWindow'}
                             for index in range(deleted)]
    mutation['property_changes'] = [{'guid': guid, 'ifc_class': 'IfcDoor'} for guid in property_guids]
    meta.update(deleted_counts={'door': 0, 'window': deleted, 'beam': 0, 'column': 0},
                property_changes=len(property_guids))
    for pair in pairs:
        pair.update(primary_target_count=count, task_kind=kind)
    write(case / 'case.json', meta)
    write(case / 'private/mutation.json', mutation)
    seal_case(case)
    summary = api().export_pairs(source, public, evaluation, pairs, source_models=1)
    assert summary['budget_levels'] == {level: 2}
    rows = list(csv.DictReader((public / 'inputs.csv').open(encoding='utf-8', newline='')))
    assert all(row['primary_target_count'] == str(count) and row['task_kind'] == kind for row in rows)


def test_real_sealed_scene_supports_both_locator_pairs(scene_factory, tmp_path):
    module = api()  # A missing exporter must fail before creating a native fixture.
    from scripts.ifc_repair.dataset_batch.pilot import process_source
    source_file = scene_factory(tmp_path / 'mother.ifc')
    batch = tmp_path / 'real-batch'
    source = batch / 'private/production'
    source.mkdir(parents=True)
    spec = {'source_id': 'formal-021', 'input_path': str(source_file), 'source_sha256': sha256(source_file),
            'request_profile': 'text2ifc/dataset-request/1.3', 'pilot_families': ['window']}
    result = process_source(spec, tmp_path, source, 1, 20261010)
    assert result['status'] == 'complete'
    case = source / result['cases'][0]['path']
    pairs = [record(source, case, mode) for mode in ('world', 'host_wall')]
    before = {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob('*') if p.is_file()}
    summary = module.export_pairs(source, batch / 'public', batch / 'private/evaluation', pairs, source_models=1)
    assert summary['pairs'] == 2 and summary['distinct_damages'] == 1
    assert {p.relative_to(source).as_posix(): sha256(p) for p in source.rglob('*') if p.is_file()} == before
