from __future__ import annotations

import json
import shutil

import pytest

from scripts.ifc_repair.collect_damage_pilot import ROOT, bound_origin_program, collect
from scripts.ifc_repair.dataset_batch.engine import verify_seal
from scripts.ifc_repair.dataset_batch.pilot import process_source, write_report
from scripts.ifc_repair.dataset_batch.validation import program_hash, sha256


@pytest.fixture
def checked_origin(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source.ifc')
    origin = tmp_path / 'origin'
    origin.mkdir()
    spec = {'source_id': 'fixture', 'input_path': str(source), 'pilot_families': ['window']}
    result = process_source(spec, tmp_path, origin, 1, 20261010)
    assert result['status'] == 'complete'
    write_report(origin, [result], [], 1)
    (origin / 'build.json').write_text(json.dumps({'configuration': {'program_sha256': program_hash()}}), encoding='utf-8')
    return origin, result


def test_collection_reuses_exact_sealed_bytes_and_records_origin(checked_origin, tmp_path):
    origin, result = checked_origin
    output = tmp_path / 'collection'
    summary = collect([origin], output, ['fixture'], tmp_path, count_per_source=1)
    assert summary['status'] == 'complete'
    case = output / result['cases'][0]['path']
    assert verify_seal(case)
    assert sha256(case / 'public/model.ifc') == sha256(origin / result['cases'][0]['path'] / 'public/model.ifc')
    integrity = json.loads((output / 'integrity.json').read_text(encoding='utf-8'))
    assert integrity['passed'] and integrity['sealed_cases'] == 1
    assert integrity['native_zero_findings_cases'] == 1
    assert summary['history']['prior_failed_attempts'] == 0
    with pytest.raises(FileExistsError):
        collect([origin], output, ['fixture'], tmp_path, count_per_source=1)


def test_collection_rejects_tampered_prompt_before_creating_output(checked_origin, tmp_path):
    origin, result = checked_origin
    (origin / result['cases'][0]['path'] / 'public/request.txt').write_text('changed', encoding='utf-8')
    output = tmp_path / 'rejected'
    with pytest.raises(ValueError, match='SEAL'):
        collect([origin], output, ['fixture'], tmp_path, count_per_source=1)
    assert not output.exists()


def test_collection_accepts_request_v3_and_two_cases_per_ifc(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source-v3.ifc')
    origin = tmp_path / 'origin-v3'
    origin.mkdir()
    spec = {'source_id': 'new-model', 'input_path': str(source),
            'request_profile': 'text2ifc/dataset-request/1.3',
            'pilot_families': ['window', 'beam_column']}
    result = process_source(spec, tmp_path, origin, 2, 20261010)
    assert result['status'] == 'complete'
    write_report(origin, [result], [], 2)
    (origin / 'build.json').write_text(json.dumps({'configuration': {'program_sha256': program_hash()}}), encoding='utf-8')
    output = tmp_path / 'collection-v3'
    summary = collect([origin], output, ['new-model'], tmp_path, count_per_source=2)
    assert summary['status'] == 'complete'
    assert summary['machine_validated_cases'] == 2
    assert summary['request_profile'] == spec['request_profile']
    build = json.loads((output / 'build.json').read_text(encoding='utf-8'))
    assert build['configuration']['cases_per_ifc'] == 2
    assert build['configuration']['request_profile'] == spec['request_profile']
    for row in result['cases']:
        assert verify_seal(output / row['path'])
        assert sha256(output / row['path'] / 'public/model.ifc') == sha256(origin / row['path'] / 'public/model.ifc')


def test_collection_checks_manifest_profile_against_origin(checked_origin, tmp_path):
    origin, _ = checked_origin
    summary = json.loads((origin / 'summary.json').read_text(encoding='utf-8'))
    summary['request_profile'] = 'text2ifc/dataset-request/1.3'
    (origin / 'summary.json').write_text(json.dumps(summary), encoding='utf-8')
    output = tmp_path / 'profile-mismatch'
    with pytest.raises(ValueError, match='CASE_MANIFEST_MISMATCH'):
        collect([origin], output, ['fixture'], tmp_path, count_per_source=1)
    assert not output.exists()


def test_changed_generator_cannot_reuse_receipts_without_byte_bound_snapshot(tmp_path):
    origin = tmp_path / 'origin'
    origin.mkdir()
    previous = program_hash()
    (origin / 'build.json').write_text(json.dumps({'configuration': {'program_sha256': previous}}), encoding='utf-8')
    with pytest.raises(ValueError, match='WITHOUT_SNAPSHOT'):
        bound_origin_program(origin, 'new-program')
    snapshot = origin / 'private/source-snapshot'
    hashes = {}
    for path in (ROOT / 'scripts/ifc_repair/dataset_batch').glob('*.py'):
        relative = path.relative_to(ROOT)
        dest = snapshot / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        hashes[relative.as_posix()] = sha256(dest)
    (snapshot / 'sha256.json').write_text(json.dumps(hashes), encoding='utf-8')
    assert bound_origin_program(origin, 'new-program') == previous
    (snapshot / 'scripts/ifc_repair/dataset_batch/prompt_check.py').write_text('tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='SNAPSHOT_CHANGED'):
        bound_origin_program(origin, 'new-program')
