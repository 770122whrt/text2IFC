"""Freeze B's correction allowance without changing a legacy task on restart."""
from dataclasses import replace
import json

import pytest

from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.isolated_b import IsolatedBConfig, worker_execute
from tests.ifc_repair.repair_comparison.test_batch_workflow import _formal_public_inputs


def test_batch_b_corrections_are_explicit_and_legacy_defaults_stay_absent(tmp_path):
    args = dict(cases_root=tmp_path, case_ids=['example'], budgets={
        'example': {'tokens': 1500000, 'calls': 48, 'active_seconds': 1800,
                    'tool_seconds': 120, 'extensions': []}}, stage=carrier.FORMAL_STAGE)
    assert 'b_validation_corrections' not in carrier.batch_configuration(**args)
    for value in (0, 1, 2):
        assert carrier.batch_configuration(**args, b_validation_corrections=value)[
            'b_validation_corrections'] == value
    for value in (True, -1, 3, '2'):
        with pytest.raises(ValueError, match='VALIDATION_CORRECTION'):
            carrier.batch_configuration(**args, b_validation_corrections=value)


def test_carrier_b_correction_limit_is_bounded(tmp_path):
    config = IsolatedBConfig(tmp_path/'bundle', tmp_path/'work', 'test-state',
                            'test-internal', 'http://repair-gateway:8000/v1')
    assert config.max_validation_corrections == 0
    for value in (-1, 3, True, '2'):
        with pytest.raises(ValueError, match='VALIDATION_CORRECTION'):
            replace(config, max_validation_corrections=value)


@pytest.mark.parametrize('limit', [None, 0, 1, 2])
def test_worker_binds_and_passes_limit_before_native_provider(tmp_path, monkeypatch, limit):
    from text2ifc_ifc_repair import api
    cases, _, _ = _formal_public_inputs(tmp_path/'authored')
    work = cases/'synthetic-001/public'
    (work/'task.txt').write_text('Public synthetic transport test.', encoding='utf8')
    expected = 0 if limit is None else limit
    observed = []

    class StopBeforeProvider(Exception):
        pass

    def inspect_api(*args, **kwargs):
        observed.append(kwargs['max_validation_corrections'])
        raise StopBeforeProvider

    monkeypatch.setattr(api, 'RepairAPI', inspect_api)
    payload = {'action': 'start', 'run_id': 'correction-config',
               'base_url': 'http://127.0.0.1:8000/v1'}
    if limit is not None:
        payload['max_validation_corrections'] = limit
    with pytest.raises(StopBeforeProvider):
        worker_execute(payload, workspace=work, state_root=tmp_path/'state')
    assert observed == [expected]
    binding = json.loads((tmp_path/'state/task.json').read_text(encoding='utf8'))
    assert binding.get('max_validation_corrections', 0) == expected
    with pytest.raises(ValueError, match='B_TASK_BINDING_MISMATCH'):
        worker_execute({**payload, 'action': 'read', 'max_validation_corrections':
                        1 if expected != 1 else 2}, workspace=work, state_root=tmp_path/'state')
    assert observed == [expected]
