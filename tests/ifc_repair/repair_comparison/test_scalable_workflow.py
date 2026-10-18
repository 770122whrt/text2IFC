import json
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
from scripts.ifc_repair.repair_comparison.ledger import Ledger


@pytest.mark.parametrize('retain_debug', [False, True])
def test_prepare_freezes_an_explicit_small_subset_without_other_inputs(tmp_path, monkeypatch, retain_debug, capsys):
    inputs = tmp_path/'inputs'
    inputs.mkdir()
    for case in ('one', 'two', 'three'):
        (inputs/(case+'.ifc')).write_bytes(b'unit-test opaque public IFC')
        (inputs/(case+'.txt')).write_text('Restore the public object.', encoding='utf8')
    monkeypatch.setattr(batch, 'check_ifc', lambda path: {'passed': True, 'status': 'passed'})
    result = batch.prepare(tmp_path/'out', inputs, scope='full', input_format='pairs',
                           default_level='S1', mode='offline', groups=['E'],
                           case_ids=['three', 'one'], retain_debug=retain_debug)
    configuration = batch.plan(tmp_path/'out')['configuration']
    assert result['tasks'] == 2
    assert configuration['case_ids'] == ['one', 'three']
    assert configuration['order'] == ['one-E', 'three-E']
    assert not (tmp_path/'out/cases/two').exists()
    assert configuration['b_validation_corrections'] == 2
    assert batch.plan(tmp_path/'out')['retain_debug'] is retain_debug
    opposite = '--no-retain-debug' if retain_debug else '--retain-debug'
    assert batch.main(['resume', '--root', str(tmp_path/'out'), opposite]) == 2
    assert 'RETENTION_POLICY_FROZEN' in capsys.readouterr().out


@pytest.mark.parametrize('ids,reason', [([], 'CASE_SELECTION_REQUIRED'),
    (['one', 'one'], 'DUPLICATE_CASE_SELECTION'), (['missing'], 'UNKNOWN_CASE_SELECTION')])
def test_prepare_rejects_invalid_subset_before_materializing(tmp_path, monkeypatch, ids, reason):
    inputs = tmp_path/'inputs'
    inputs.mkdir()
    (inputs/'one.ifc').write_bytes(b'unit-test opaque public IFC')
    (inputs/'one.txt').write_text('Restore the object.', encoding='utf8')
    with pytest.raises(ValueError, match=reason):
        batch.prepare(tmp_path/'out', inputs, scope='full', default_level='S1',
                      mode='offline', groups=['E'], case_ids=ids)
    assert not (tmp_path/'out').exists()


def test_brief_status_never_reads_reports_or_response_bodies(tmp_path, monkeypatch):
    ledger = Ledger(tmp_path / 'control.sqlite')
    ledger.create('one-F', case_id='one', arm='F', budget=fixed_budget_profile('S1'))
    ledger.start('one-F')
    ledger.reserve('one-F', 'call', 100, metadata={'stage': 'model'})
    ledger.settle('one-F', 'call', usage={'prompt_tokens': 10, 'completion_tokens': 2},
                  response={'body': 'large body must not be selected'})
    def forbidden(*args, **kwargs):
        raise AssertionError('Brief progress must not load task reports/calls')
    monkeypatch.setattr(Ledger, 'calls', forbidden)
    monkeypatch.setattr(batch, 'export_task', forbidden)
    status = batch.brief_status(tmp_path)
    assert status['active'] == 'one-F'
    assert status['completed'] == 0 and status['total'] == 1
    assert status['known_tokens'] == 12
    assert len(json.dumps(status)) < 2048


def test_case_budget_only_no_aggregate_cap(tmp_path):
    ledger = Ledger(tmp_path / 'control.sqlite')
    ledger.create('one-F', case_id='one', arm='F', budget=fixed_budget_profile('S1'))
    state = ledger.snapshot('one-F')
    assert batch.may_start(state)
    assert batch.TASK_BUDGET_ONLY == 'per-task-only/no-batch-total'


def test_repeated_harness_system_failures_require_distinct_cases():
    def state(case, arm='F'):
        return {'case_id': case, 'arm': arm, 'status': 'runtime_error',
                'detail': 'NATIVE_PROCESS_STOP_NOT_CONFIRMED', 'native': {}}
    assert batch.common_failure([state('one'), state('one','E')]) is None
    assert batch.common_failure([state('one'), state('two')]) is not None
    assert batch.common_failure([state('one','G'), state('two','G')]) is None


def test_pause_and_resume_marker_never_reset_ledger(tmp_path):
    ledger = Ledger(tmp_path / 'control.sqlite', clock=lambda: 1)
    ledger.create('one-F', case_id='one', arm='F', budget=fixed_budget_profile('S1'))
    ledger.start('one-F')
    ledger.reserve('one-F', 'first', 100)
    ledger.settle('one-F', 'first', usage={'prompt_tokens': 10, 'completion_tokens': 2}, response={})
    before = ledger.snapshot('one-F')
    batch.pause(tmp_path)
    assert (tmp_path / 'pause-between-tasks').exists()
    batch.clear_pause(tmp_path)
    after = ledger.snapshot('one-F')
    assert before == after
    assert after['usage']['known_total_tokens'] == 12


def test_artifact_validator_rejects_invalid_ifc_without_output_mutation(tmp_path):
    path = tmp_path / 'bad.ifc'; path.write_bytes(b'not an IFC')
    before = path.read_bytes()
    checked = batch.check_ifc(path)
    assert checked['passed'] is False
    assert checked['status'] in {'failed', 'error'}
    assert path.read_bytes() == before


def test_artifact_validator_accepts_a_real_ifc_and_keeps_bytes(tmp_path):
    import ifcopenshell
    model = ifcopenshell.file(schema='IFC4')
    placement = model.create_entity('IfcAxis2Placement3D', Location=model.create_entity('IfcCartesianPoint', Coordinates=(0.,0.,0.)))
    context = model.create_entity('IfcGeometricRepresentationContext', ContextType='Model',
        CoordinateSpaceDimension=3, WorldCoordinateSystem=placement)
    units = model.create_entity('IfcUnitAssignment', Units=[model.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE')])
    model.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), Name='Validator fixture',
        RepresentationContexts=[context], UnitsInContext=units)
    path = tmp_path/'valid.ifc'
    model.write(str(path))
    before = path.read_bytes()
    result = batch.check_ifc(path)
    assert result['passed'] is True, result
    assert result['express_rules'] is True and path.read_bytes() == before


@pytest.mark.parametrize('known', [True, False])
@pytest.mark.parametrize('retain_debug', [False, True])
def test_terminal_cleanup_retains_charges_flags_and_export_only(tmp_path, monkeypatch, known, retain_debug):
    ledger = Ledger(tmp_path/'control.sqlite', clock=lambda:1)
    ledger.create('one-F', case_id='one', arm='F', budget=fixed_budget_profile('S1'))
    ledger.start('one-F')
    ledger.reserve('one-F', 'call', 100, metadata={'wire_protocol':'messages'})
    ledger.settle('one-F', 'call', usage={'input_tokens':10,'output_tokens':2} if known else None,
        response={'body': {'content':[{'type':'thinking','thinking':'Actual offline fixture text.'}]},
                  'usage_complete':True,'stream_complete':True,'http_status':200})
    state = ledger.finish('one-F','no_output', detail='No submit in the offline fixture.')
    batch.export_task(tmp_path,tmp_path/'results','one-F')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE batch_exports(run_id TEXT PRIMARY KEY,summary TEXT NOT NULL)')
        db.execute('INSERT INTO batch_exports VALUES(?,?)',('one-F','{}'))
    for folder in ('wire/one-F','workspaces/one-F','runtime/one-F'):
        directory=tmp_path/folder
        directory.mkdir(parents=True)
        (directory/'scratch.txt').write_text('Disposable fixture', encoding='utf8')
    source = tmp_path/'cases/one/public/model.ifc'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'Source preservation fixture')
    before = ledger.snapshot('one-F')['usage']
    commands = []
    def docker(*args, **kwargs):
        commands.append(args)
        return 'fake-owned-volume' if args[:2] == ('volume', 'ls') else ''
    monkeypatch.setattr(batch, 'docker', docker)
    config = {'routes': {'one-F': {'container': 'fake-owned', 'volume': 'fake-owned-volume'}}}
    raw_response = ledger.calls('one-F')[0]['response']
    batch._retire_task(tmp_path, state, config, retain_debug)
    assert ledger.snapshot('one-F')['usage'] == before
    assert ledger.calls('one-F')[0]['response']['usage_complete'] is True
    if retain_debug:
        assert ledger.calls('one-F')[0]['response'] == raw_response
    else:
        assert 'body' not in ledger.calls('one-F')[0]['response']
    assert (('volume', 'rm', 'fake-owned-volume') in commands) is (not retain_debug)
    assert commands[0][0] == 'ps'
    assert source.read_bytes() == b'Source preservation fixture'
    assert [p.name for p in (tmp_path/'results/one/F').iterdir()] == ['report.md']
    for folder in ('wire/one-F', 'workspaces/one-F', 'runtime/one-F'):
        assert (tmp_path/folder/'scratch.txt').exists() is retain_debug
    assert ledger.events('one-F')[-1]['payload']['detail'] == 'No submit in the offline fixture.'


def test_queued_answer_rejects_a_changed_question_without_reset(tmp_path, monkeypatch):
    ledger = Ledger(tmp_path/'control.sqlite', clock=lambda:1)
    ledger.create('one-F',case_id='one',arm='F',budget=fixed_budget_profile('S1'))
    ledger.start('one-F')
    ledger.ask('one-F',question_id='current',text='Which location?')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        db.execute('INSERT INTO batch_control VALUES(?,?)',('answer',json.dumps(
            {'run_id':'one-F','answer':{'question_id':'previous','source':'user_confirmed','text':'Here'}})))
    monkeypatch.setattr(batch.carrier,'answer',lambda *a:pytest.fail('Stale answer must not be injected'))
    with pytest.raises(ValueError,match='QUEUED_ANSWER_QUESTION_CHANGED'):
        batch._queued_answer(tmp_path)
    assert ledger.snapshot('one-F')['status'] == 'awaiting_user'


@pytest.mark.parametrize('guard', ['active', 'inflight', 'process'])
def test_debug_retention_still_requires_quiescence(tmp_path, monkeypatch, guard):
    ledger = Ledger(tmp_path/'control.sqlite', clock=lambda: 1)
    ledger.create('one-F', case_id='one', arm='F', budget=fixed_budget_profile('S1'))
    ledger.start('one-F')
    if guard == 'inflight':
        ledger.reserve('one-F', 'call', 100)
    state = ledger.snapshot('one-F')
    if guard != 'active':
        state['status'] = 'no_output'
    monkeypatch.setattr(batch, 'docker', lambda *args: 'fake-owned')
    reason = {'active': 'ACTIVE_TASK_CANNOT_RETIRE', 'inflight': 'INFLIGHT_TASK_CANNOT_RETIRE',
              'process': 'NATIVE_PROCESS_STOP_NOT_CONFIRMED'}[guard]
    with pytest.raises(ValueError, match=reason):
        batch._retire_task(tmp_path, state,
            {'routes': {'one-F': {'container': 'fake-owned', 'volume': 'fake-owned-volume'}}}, True)


@pytest.fixture
def debug_export_batch(tmp_path, monkeypatch, request):
    from scripts.ifc_repair.repair_comparison.contracts import write_json
    from scripts.ifc_repair.repair_comparison.group_config import harness_profile
    inputs = tmp_path/'inputs'
    inputs.mkdir()
    (inputs/'one.ifc').write_bytes(b'public source fixture')
    (inputs/'one.txt').write_bytes(getattr(request, 'param', b'Repair this public object.'))
    monkeypatch.setattr(batch, 'check_ifc', lambda path: {'passed': True})
    root = tmp_path/'batch'
    batch.prepare(root, inputs, scope='full', default_level='S1', mode='offline',
                  groups=['E'], retain_debug=True)
    value = batch.plan(root)
    config = {'configuration': value['configuration'], 'mode': 'offline',
              'network': 'repair-debug-network',
              'routes': {'one-E': {'volume': 'debug-volume', 'container': 'debug-container', 'token': '0'*32}}}
    write_json(root/'experiment.json', config)
    ledger = Ledger(root/'control.sqlite', clock=lambda: 1)
    ledger.create('one-E', case_id='one', arm='E', budget=fixed_budget_profile('S1'))
    ledger.start('one-E')
    ledger.finish('one-E', 'no_output')
    with ledger.transaction() as db:
        db.execute('CREATE TABLE batch_exports(run_id TEXT PRIMARY KEY,summary TEXT NOT NULL)')
        db.execute("INSERT INTO batch_exports VALUES('one-E','{}')")
    monkeypatch.setattr(batch, 'docker', lambda *args: '')
    work = root/'workspaces/one-E'
    work.mkdir(parents=True)
    # Match the public DirectRunner's native request materialization boundary.
    text = (root/'cases/one/public/request.txt').read_text(encoding='utf8').strip()
    (work/'task.txt').write_text(text+'\n', encoding='utf8')
    from scripts.ifc_repair.repair_comparison.contracts import sha256
    native_request_hash = sha256(work/'task.txt')
    calls = []
    profile = harness_profile(value['configuration'], 'E')
    def export(worker, destination):
        calls.append(worker.config)
        assert worker.config.model_profile == profile
        state = destination/'state'
        (state/'native').mkdir(parents=True)
        (state/'native/evidence.json').write_text('{}', encoding='utf8')
        binding = value['input_bindings']['one']['input_digests']
        write_json(state/'task.json', {'run_id': 'one-E', 'model': profile['model'],
            'model_profile': profile, 'source_sha256': binding['model.ifc'],
            'request_sha256': native_request_hash})
        return state
    from scripts.ifc_repair.repair_comparison.isolated_b import IsolatedB
    monkeypatch.setattr(IsolatedB, 'export_state', export)
    return root, ledger, calls


def test_debug_export_forwards_e_profile_and_reuses_complete_snapshot(debug_export_batch):
    root, ledger, calls = debug_export_batch
    first = batch.debug_export(root)
    second = batch.debug_export(root)
    assert first['exported'] == 1 and second['reused'] == 1
    assert len(calls) == 1
    assert (root/'debug/one-E/receipt.json').is_file()


@pytest.mark.parametrize('failure', ['active', 'retention', 'incomplete', 'tampered', 'lock'])
def test_debug_export_rejects_unsafe_or_incomplete_snapshot(debug_export_batch, failure):
    from scripts.ifc_repair.repair_comparison.contracts import write_json
    root, ledger, calls = debug_export_batch
    expected = {'active': 'ACTIVE_TASK_CANNOT_RETIRE', 'retention': 'DEBUG_RETENTION_REQUIRED',
                'incomplete': 'DEBUG_EXPORT_INCOMPLETE', 'tampered': 'DEBUG_EXPORT_CHANGED',
                'lock': 'RUN_CONTROLLER_ALREADY_ACTIVE'}[failure]
    if failure == 'active':
        with ledger.transaction() as db:
            state = ledger._load(db, 'one-E')
            state['status'] = 'running'
            ledger._save(db, state)
    elif failure == 'retention':
        value = batch.plan(root)
        value['retain_debug'] = False
        value.pop('sha256')
        value['sha256'] = batch._digest(value)
        write_json(root/'batch.json', value)
    elif failure == 'incomplete':
        (root/'debug/one-E/state').mkdir(parents=True)
    elif failure == 'tampered':
        batch.debug_export(root)
        (root/'debug/one-E/state/native/evidence.json').write_text('changed', encoding='utf8')
    if failure == 'lock':
        with batch.task_owner(root, 'batch-owner'):
            with pytest.raises(ValueError, match=expected):
                batch.debug_export(root)
    else:
        with pytest.raises(ValueError, match=expected):
            batch.debug_export(root)
    assert len(calls) == (1 if failure == 'tampered' else 0)
