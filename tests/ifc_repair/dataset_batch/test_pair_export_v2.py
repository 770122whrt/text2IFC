"""Opaque receipts exercise request transforms; they do not establish native IFC validity."""
from __future__ import annotations

import importlib

import pytest

from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair import dataset_request_v4 as profile
from .test_pair_export import opaque_sealed_pair_source


def api():
    return importlib.import_module('scripts.ifc_repair.dataset_pair_export_v2')


@pytest.fixture
def upgrade_source(opaque_sealed_pair_source):
    source, public, evaluation, folder, pairs = opaque_sealed_pair_source
    meta = q.read(folder / 'case.json')
    for pair in pairs:
        path = folder / pair['request_relative_path']
        original = path.read_bytes().decode('utf-8-sig')
        path.write_bytes((profile.HEADER + '\r\n' + original).encode('utf-8'))
        pair['request_sha256'] = q.sha256(path)
        meta['prompt_templates'][pair['locator_mode']]['sha256'] = pair['request_sha256']
    q.write_json(folder / 'case.json', meta)
    q.seal_case(folder)
    return source, public, evaluation, folder, pairs


def test_upgraded_requests_bind_source_body_prefix_and_final_bytes(upgrade_source):
    module = api()
    source, public, evaluation, folder, pairs = upgrade_source
    frozen = {p: q.sha256(p) for p in source.rglob('*') if p.is_file()}
    summary = module.export_pairs(source, public, evaluation, pairs, source_models=1)
    assert summary['pairs'] == 2 and summary['distinct_damages'] == 1
    assert summary['authoring_request_profile'] == profile.SOURCE_PROFILE
    assert summary['request_profile'] == profile.PROFILE and summary['public_files'] == 5
    receipt = q.read(evaluation / 'export.json')
    assert receipt['schema_version'] == 'text2ifc/dataset-pair-export/1.1'
    assert receipt['transform']['prefix_sha256'] == module.text_sha256(profile.PREFIX)
    assert len(receipt['transform']['program_sha256']) == 2
    for pair, provenance in zip(pairs, receipt['pair_provenance'], strict=True):
        body = (folder / pair['request_relative_path']).read_bytes().decode('utf-8-sig')
        rendered = (public / provenance['public_row']['request_path']).read_bytes()
        assert rendered == profile.upgrade_request(body).encode('utf-8')
        assert provenance['authoring_request_sha256'] == pair['request_sha256']
        assert provenance['source_body_sha256'] == module.text_sha256(body)
        assert provenance['public_request_sha256'] == q.sha256(public / provenance['public_row']['request_path'])
        assert provenance['public_request_sha256'] != provenance['authoring_request_sha256']
        assert (public / provenance['public_row']['ifc_path']).read_bytes() == (folder / 'public/model.ifc').read_bytes()
    assert all(q.sha256(p) == digest for p, digest in frozen.items())
    assert module.check_pair_export(public, evaluation) == summary


@pytest.mark.parametrize('change', ['native', 'unsupported_body', 'seal'])
def test_upgrade_does_not_bypass_original_authoring_gates(upgrade_source, change):
    module = api()
    source, public, evaluation, folder, pairs = upgrade_source
    if change == 'native':
        value = q.read(folder / 'private/validation.json')
        value['express_rules'] = False
        q.write_json(folder / 'private/validation.json', value)
        q.seal_case(folder)
    elif change == 'unsupported_body':
        path = folder / pairs[0]['request_relative_path']
        path.write_text('没有 1.3 标题的模拟请求', encoding='utf-8')
        meta = q.read(folder / 'case.json')
        pairs[0]['request_sha256'] = q.sha256(path)
        meta['prompt_templates']['world']['sha256'] = pairs[0]['request_sha256']
        q.write_json(folder / 'case.json', meta)
        q.seal_case(folder)
    else:
        (folder / 'public/model.ifc').write_bytes(b'changed')
    with pytest.raises(ValueError):
        module.export_pairs(source, public, evaluation, pairs, source_models=1)
    assert not public.exists() and not evaluation.exists()


@pytest.mark.parametrize('change', ['source_body', 'prefix', 'final_body', 'body_hash', 'program_hash'])
def test_readback_rejects_source_transform_and_public_text_drift(upgrade_source, change):
    module = api()
    source, public, evaluation, folder, pairs = upgrade_source
    module.export_pairs(source, public, evaluation, pairs, source_models=1)
    receipt = q.read(evaluation / 'export.json')
    provenance = receipt['pair_provenance'][0]
    if change == 'source_body':
        (folder / pairs[0]['request_relative_path']).write_text('changed source body', encoding='utf-8')
    elif change in {'prefix', 'final_body'}:
        path = public / provenance['public_row']['request_path']
        body = (folder / pairs[0]['request_relative_path']).read_bytes().decode('utf-8-sig')
        path.write_bytes((body if change == 'prefix' else profile.upgrade_request(body) + '\nprivate addition').encode('utf-8'))
        # Even a rehashed public receipt cannot excuse a body/prefix change.
        receipt['public_file_sha256'][provenance['public_row']['request_path']] = q.sha256(path)
        provenance['public_request_sha256'] = q.sha256(path)
    elif change == 'body_hash':
        provenance['source_body_sha256'] = '0' * 64
    else:
        receipt['transform']['program_sha256'][str(module.PROFILE_MODULE)] = '0' * 64
    q.write_json(evaluation / 'export.json', receipt)
    with pytest.raises(ValueError):
        module.check_pair_export(public, evaluation)


def test_upgraded_export_failure_retains_partial_output_and_error(upgrade_source, monkeypatch):
    module = api()
    source, public, evaluation, _, pairs = upgrade_source
    monkeypatch.setattr(module.shutil, 'copyfile', lambda *a, **kw: (_ for _ in ()).throw(OSError('simulated copy failure')))
    with pytest.raises(OSError, match='simulated copy failure'):
        module.export_pairs(source, public, evaluation, pairs, source_models=1)
    assert public.exists() and q.read(evaluation / 'export-failed.json')['error']
    with pytest.raises(FileExistsError, match='NEW_OUTPUT_REQUIRED'):
        module.export_pairs(source, public, evaluation, pairs, source_models=1)
