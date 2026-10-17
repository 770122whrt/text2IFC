"""Revalidate new code without overwriting the prior source-bound gate."""
import json
from types import SimpleNamespace

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as api
from scripts.ifc_repair.repair_comparison.contracts import read_json


def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(api, 'plan', lambda _: {'configuration': {'order': ['one-B']}})
    monkeypatch.setattr(api.carrier, 'bindings', lambda _: {'files': {'code.py': 'current'}})
    def execute(command, **kwargs):
        junit = next(item.split('=', 1)[1] for item in command if item.startswith('--junitxml='))
        from pathlib import Path
        Path(junit).write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>', encoding='utf8')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(api.subprocess, 'run', execute)
    monkeypatch.setattr(api, '_gate_report', lambda path: read_json(path))
    return tmp_path


def test_revision_keeps_previous_gate_bytes(tmp_path, monkeypatch):
    root = fixture(tmp_path, monkeypatch)
    tests = ['tests/ifc_repair/repair_comparison/test_gate_revisions.py']
    old = api.gate(root, tests)
    from pathlib import Path
    before = Path(old['receipt']).read_bytes()
    new = api.gate(root, tests, revision='candidate-02')
    assert Path(old['receipt']).read_bytes() == before
    assert new['receipt'] != old['receipt']
    assert read_json(Path(new['receipt']))['junit']['path'].endswith('scoped-candidate-02.xml')
    with pytest.raises(ValueError, match='SCOPED_GATE_ALREADY_RECORDED'):
        api.gate(root, tests, revision='candidate-02')


@pytest.mark.parametrize('revision', ['../escape', '/absolute', 'a/b', '', 'bad value'])
def test_revision_cannot_escape_gate_directory(tmp_path, monkeypatch, revision):
    root = fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match='INVALID_GATE_REVISION'):
        api.gate(root, ['tests/ifc_repair/repair_comparison/test_gate_revisions.py'], revision=revision)


def test_named_admission_keeps_original_frozen_records_and_only_updates_runtime_pointer(tmp_path, monkeypatch):
    from scripts.ifc_repair.repair_comparison.contracts import write_json
    from scripts.ifc_repair.repair_comparison.ledger import Ledger
    root = tmp_path
    config = {'stage': api.SCALABLE_STAGE, 'order': ['one-B'], 'b': None}
    bindings = {'files': {'scripts/ifc_repair/repair_comparison/batch_workflow.py': 'current'}}
    old_bindings = {'files': {'scripts/ifc_repair/repair_comparison/batch_workflow.py': 'previous'}}
    monkeypatch.setattr(api, 'plan', lambda _: {'configuration': config})
    monkeypatch.setattr(api.carrier, 'bindings', lambda _: bindings)
    monkeypatch.setattr(api, '_gate_report', lambda _: {'configuration': config})
    monkeypatch.setattr(api, '_verify_native', lambda *a, **kw: {'timeout_stop': {'quiescent': True}})
    Ledger(root/'control.sqlite')
    (root/'admission').mkdir()
    native = root/'native.json'
    write_json(native, {'fixture': 'offline source receipt'})
    frozen_path = root/'admission/harness-freeze.json'
    write_json(frozen_path, {'frozen': 'keep exact bytes'})
    original = root/'admission/live.json'
    write_json(original, {'configuration': config, 'bindings': old_bindings})
    runtime = {'configuration': config, 'admission': str(original), 'mode': 'live', 'routes': {'one-B': {}}}
    write_json(root/'experiment.json', runtime)
    before = original.read_bytes(), frozen_path.read_bytes()
    result = api.admit(root, native, scoped_receipt=native, revision='controller-01')
    assert result['admission'].endswith('live-controller-01.json')
    assert (original.read_bytes(), frozen_path.read_bytes()) == before
    after = read_json(root/'experiment.json')
    assert {k: v for k, v in after.items() if k != 'admission'} == {
        k: v for k, v in runtime.items() if k != 'admission'}
    assert after['admission'] == result['admission']
    with pytest.raises(ValueError, match='LIVE_ADMISSION_ALREADY_RECORDED'):
        api.admit(root, native, scoped_receipt=native, revision='controller-01')


def test_cli_passes_explicit_gate_and_receipt(tmp_path, monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(api, 'gate', lambda root, tests, **kw: calls.append(kw) or {'ok': True})
    monkeypatch.setattr(api, 'admit', lambda root, native, **kw: calls.append(kw) or {'ok': True})
    assert api.main(['gate', '--root', str(tmp_path), '--revision', 'fixed', '--tests', 'tests/example.py']) == 0
    assert calls[-1] == {'revision': 'fixed'}
    assert api.main(['admit', '--root', str(tmp_path), '--scoped-receipt', str(tmp_path/'admission/scoped-fixed.json')]) == 0
    assert calls[-1]['scoped_receipt'] == tmp_path/'admission/scoped-fixed.json'


def test_check_admission_reopens_the_bound_named_gate(tmp_path, monkeypatch):
    from pathlib import Path
    receipt = tmp_path/'admission/scoped-fixed.json'
    value = {'scoped_receipt': {'checked': True},
             'scoped_receipt_reference': {'path': str(receipt), 'sha256': 'receipt-digest'},
             'native_receipts': [{'path': str(tmp_path/'native.json'), 'sha256': 'receipt-digest'}]}
    monkeypatch.setattr(api.carrier, 'verify_admission', lambda *a: value)
    monkeypatch.setattr(api, 'sha256', lambda path: 'receipt-digest')
    seen = []
    monkeypatch.setattr(api, '_gate_report', lambda path: seen.append(Path(path)) or {'checked': True})
    monkeypatch.setattr(api, '_verify_native', lambda *a, **kw: {})
    api._check_admission(tmp_path, {'order': ['one-B']})
    assert seen == [receipt]


def test_refresh_only_unstarted_plan_and_preserve_old_bytes(tmp_path, monkeypatch):
    from scripts.ifc_repair.repair_comparison.contracts import write_json
    value = {'schema_version': api.PLAN_SCHEMA, 'budget_policy': api.TASK_BUDGET_ONLY,
             'configuration': {'scene_grounding_version': 'previous', 'budgets': {'one': 42},
                               'order': ['one-B']}}
    value['sha256'] = api._digest(value)
    write_json(tmp_path/'batch.json', value)
    old = (tmp_path/'batch.json').read_bytes()
    (tmp_path/'pause-between-tasks').touch()
    guarded = []
    monkeypatch.setattr(api, '_source_guard', lambda *a: guarded.append(True))
    result = api.refresh_unstarted(tmp_path)
    assert guarded == [True]
    assert api.plan(tmp_path)['configuration'] == {
        **value['configuration'], 'scene_grounding_version': api.carrier.SCENE_GROUNDING_VERSION}
    from pathlib import Path
    assert Path(result['previous_plan']).read_bytes() == old
    assert (tmp_path/'pause-between-tasks').exists()
    assert not (tmp_path/'admission/live.json').exists()
    assert api.refresh_unstarted(tmp_path)['state'] == 'unchanged'


@pytest.mark.parametrize('marker', ['experiment.json', 'control.sqlite'])
def test_started_plan_cannot_be_refreshed(tmp_path, monkeypatch, marker):
    (tmp_path/marker).touch()
    monkeypatch.setattr(api, 'plan', lambda _: pytest.fail('must reject before reading plan'))
    with pytest.raises(ValueError, match='STARTED_BATCH_IMMUTABLE'):
        api.refresh_unstarted(tmp_path)


def convention_plan(root):
    from scripts.ifc_repair.repair_comparison.contracts import sha256, write_json
    value = {'schema_version': api.PLAN_SCHEMA, 'budget_policy': api.TASK_BUDGET_ONLY,
             'configuration': {'scene_grounding_version': api.carrier.SCENE_GROUNDING_VERSION,
                               'budgets': {'one': 42, 'two': 42}, 'order': ['one-B', 'two-E']},
             'input_bindings': {}}
    for case in ('one', 'two'):
        public = root/'cases'/case/'public'
        public.mkdir(parents=True)
        (public/'model.ifc').write_bytes(b'unchanged IFC')
        request = public/'request.txt'
        request.write_text('公开请求：修改已有属性。\n', encoding='utf8')
        source = root/(case+'-source.txt')
        source.write_bytes(request.read_bytes())
        value['input_bindings'][case] = {'source_inputs_unchanged': True,
            'input_digests': {n: sha256(public/n) for n in ('model.ifc', 'request.txt')},
            'metadata_bindings': {str(source): sha256(source)}}
    value['sha256'] = api._digest(value)
    write_json(root/'batch.json', value)
    return value


def test_refresh_request_convention_preserves_sources_and_previous_plan(tmp_path):
    from scripts.ifc_repair.repair_comparison.batch_cases import request_convention_parts
    from scripts.ifc_repair.repair_comparison.contracts import sha256
    old = convention_plan(tmp_path)
    before = (tmp_path/'batch.json').read_bytes()
    convention = 'existing-ifc-property-units/1.0'
    metadata, appendix = request_convention_parts(convention)
    result = api.refresh_unstarted(tmp_path, request_convention=convention)
    current = api.plan(tmp_path)
    assert current['sha256'] != old['sha256']
    assert current['configuration'] == old['configuration']
    assert current['request_convention'] == convention
    from pathlib import Path
    assert Path(result['previous_plan']).read_bytes() == before
    for case, binding in current['input_bindings'].items():
        public = tmp_path/'cases'/case/'public'
        assert (public/'request.txt').read_bytes() == (tmp_path/(case+'-source.txt')).read_bytes()+appendix
        assert set(p.name for p in public.iterdir()) == {'model.ifc', 'request.txt'}
        assert binding['source_input_digests'] == old['input_bindings'][case]['input_digests']
        assert binding['request_convention'] == metadata
        assert binding['input_digests']['request.txt'] == sha256(public/'request.txt')
        assert binding['input_digests']['model.ifc'] == old['input_bindings'][case]['input_digests']['model.ifc']
    assert api.refresh_unstarted(tmp_path, request_convention=convention)['state'] == 'unchanged'
    assert not (tmp_path/'admission/request-refresh-pending.json').exists()


def test_convention_refresh_checks_all_inputs_before_any_write(tmp_path):
    convention_plan(tmp_path)
    first = tmp_path/'cases/one/public/request.txt'
    before = first.read_bytes()
    (tmp_path/'cases/two/public/request.txt').write_text('unexpected change', encoding='utf8')
    with pytest.raises(ValueError, match='PUBLIC_INPUT_CHANGED'):
        api.refresh_unstarted(tmp_path, request_convention='existing-ifc-property-units/1.0')
    assert first.read_bytes() == before
    assert not (tmp_path/'admission/request-refresh-pending.json').exists()


def test_interrupted_request_refresh_recovers_without_duplicate_appendix(tmp_path, monkeypatch):
    from pathlib import Path
    convention_plan(tmp_path)
    original = Path.replace
    def fail_second(path, destination):
        if Path(destination) == tmp_path/'cases/two/public/request.txt':
            raise KeyboardInterrupt('simulated interruption')
        return original(path, destination)
    with monkeypatch.context() as patch:
        patch.setattr(Path, 'replace', fail_second)
        with pytest.raises(KeyboardInterrupt):
            api.refresh_unstarted(tmp_path, request_convention='existing-ifc-property-units/1.0')
    assert (tmp_path/'admission/request-refresh-pending.json').is_file()
    api.refresh_unstarted(tmp_path, request_convention='existing-ifc-property-units/1.0')
    assert api.refresh_unstarted(tmp_path, request_convention='existing-ifc-property-units/1.0')['state'] == 'unchanged'
    for case in ('one', 'two'):
        text = (tmp_path/'cases'/case/'public/request.txt').read_text(encoding='utf8')
        assert text.count('属性更改中的数值沿用') == 1
        assert len(list((tmp_path/'cases'/case/'public').iterdir())) == 2
