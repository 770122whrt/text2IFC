from __future__ import annotations

import json
import zipfile

from scripts.ifc_repair.dataset_batch.engine import verify_seal
from scripts.ifc_repair.dataset_batch.pilot import process_source, write_report
from scripts.ifc_repair.dataset_batch.validation import sha256
from scripts.ifc_repair.update_damage_pilot import update_dataset


def test_in_place_update_archives_old_bytes_and_reuses_only_identical_ifc(scene_factory, tmp_path):
    source = scene_factory(tmp_path / 'source.ifc', millimetres=True)
    dataset = tmp_path / 'old-pilot'
    dataset.mkdir()
    result = process_source({'source_id': 'fixture', 'input_path': str(source),
                             'pilot_families': ['window', 'door_window', 'beam_column', 'attribute']},
                            str(tmp_path), str(dataset), 4, 20261010)
    assert result['status'] == 'complete'
    write_report(dataset, [result], [], 4)
    (dataset / 'build.json').write_text('{}', encoding='utf-8')
    old_hashes = {c['path']: sha256(dataset / c['path'] / 'public/model.ifc') for c in result['cases']}
    old_request = (dataset / result['cases'][0]['path'] / 'public/request.txt').read_bytes()
    updated = update_dataset(dataset, tmp_path / 'new-stage', workers=1, expected_cases=4, install=True)
    assert updated['installed'] and updated['same_ifc_cases'] == 4 and updated['rebuilt_cases'] == 0
    for path, digest in old_hashes.items():
        assert sha256(dataset / path / 'public/model.ifc') == digest
        assert verify_seal(dataset / path)
        checks = json.loads((dataset / path / 'private/prompt-check.json').read_text(encoding='utf-8'))
        assert checks['world']['passed']
    archive = dataset / 'private/history/request-1.2-before-1.3.zip'
    with zipfile.ZipFile(archive) as history:
        assert history.read(result['cases'][0]['path'] + '/public/request.txt') == old_request
    assert json.loads((dataset / 'summary.json').read_text(encoding='utf-8'))['request_profile'].endswith('/1.3')
