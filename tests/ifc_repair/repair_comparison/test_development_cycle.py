"""Selection and pass decisions must not depend on hand-inspected model output."""
from pathlib import Path
import json

import pytest

from scripts.ifc_repair.repair_comparison import development_cycle as api


def test_fresh_selection_is_reproducible_and_excludes_whole_source_groups():
    rows = [{'case_id': str(i), 'level': 'S1', 'task_kind': 'geometry' if i % 2 else 'property'}
            for i in range(12)]
    sources = {str(i): str(i//2) for i in range(12)}
    chosen = api.choose_fresh(rows, sources, excluded=['0'], seed=17)
    assert chosen == api.choose_fresh(rows, sources, excluded=['0'], seed=17)
    assert len(chosen) == len({sources[c] for c in chosen}) == 2
    assert not {'0', '1'} & set(chosen)
    assert {rows[int(c)]['task_kind'] for c in chosen} == {'geometry', 'property'}


def test_fresh_selection_does_not_reuse_exhausted_pool():
    rows = [{'case_id': 'one', 'level': 'S1', 'task_kind': 'geometry'}]
    with pytest.raises(ValueError, match='FRESH_TWO_CASES_UNAVAILABLE'):
        api.choose_fresh(rows, {'one': 'source'}, excluded=['one'], seed=1)


@pytest.mark.parametrize('checks,kind,allowed', [
    (['passed','passed'], 'fresh', True), (['passed','failed'], 'fresh', False),
    (['passed','review_required'], 'fresh', False), (['passed'], 'fresh', False),
    (['passed','passed'], 'regression', False),
])
def test_only_two_strict_fresh_passes_allow_batch(checks, kind, allowed):
    rows = [{'case_id': str(i), 'terminal': 'submitted', 'format': True,
             'independent': status} for i, status in enumerate(checks)]
    assert api.decision(rows, kind=kind)['batch_eligible'] is allowed


def test_submitted_without_format_or_independent_evidence_is_not_success():
    rows = [{'case_id': 'one', 'terminal': 'submitted', 'format': False, 'independent': 'passed'},
            {'case_id': 'two', 'terminal': 'no_output', 'format': None, 'independent': 'not_evaluated'}]
    verdict = api.decision(rows, kind='fresh')
    assert verdict['passed'] == 0 and not verdict['batch_eligible']


def test_check_reads_structured_exports_and_binds_formal_artifact(tmp_path, monkeypatch):
    import json
    from scripts.ifc_repair.repair_comparison import host_evaluator
    from scripts.ifc_repair.repair_comparison.contracts import write_json
    from scripts.ifc_repair.repair_comparison.ledger import Ledger
    from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
    selection = {'kind': 'fresh', 'arm': 'B', 'case_ids': ['one', 'two']}
    write_json(tmp_path/'round.json', {'selection': selection, 'selection_sha256': api.batch._digest(selection)})
    folder = tmp_path/'batch'
    folder.mkdir()
    ledger = Ledger(folder/'control.sqlite')
    for case in selection['case_ids']:
        ledger.create(case+'-B', case_id=case, arm='B', budget=fixed_budget_profile('S1'))
        ledger.start(case+'-B')
        ledger.finish(case+'-B', 'submitted', artifact={'path':'formal-fixture', 'sha256':'frozen'})
    with ledger.transaction() as db:
        db.execute('CREATE TABLE batch_exports(run_id TEXT PRIMARY KEY,summary TEXT NOT NULL)')
        for case in selection['case_ids']:
            db.execute('INSERT INTO batch_exports VALUES(?,?)', (case+'-B', json.dumps({
                'status':'submitted','artifact_sha256':'frozen','common_format_validation':{'passed':True}})))
    monkeypatch.setattr(api.batch, 'plan', lambda root: {'configuration': {
        'case_ids':['one','two'], 'case_groups':{'one':['B'],'two':['B']}}})
    seen = []
    def evaluate(state, case, result):
        seen.append((case, result))
        return {'status':'passed','codes':[], 'result_sha256':'changed'}
    monkeypatch.setattr(host_evaluator, 'evaluate_result', evaluate)
    with pytest.raises(ValueError, match='EXPORTED_ARTIFACT_CHANGED'):
        api.check(tmp_path)
    assert seen[0][1] == folder/'results/one/B/repaired.ifc'


def test_prepare_freezes_selection_before_failed_control_and_never_starts_model(tmp_path, monkeypatch):
    from scripts.ifc_repair.repair_comparison import host_evaluator
    dataset = tmp_path/'dataset'
    (dataset/'public').mkdir(parents=True)
    (dataset/'private/evaluation').mkdir(parents=True)
    (dataset/'public/inputs.csv').write_text('case_id,level,task_kind\none,S1,geometry\ntwo,S1,property\n', encoding='utf-8-sig')
    (dataset/'private/evaluation/export.json').write_text(json.dumps({'pair_provenance':[
        {'case_id':'one','source_id':'s1'},{'case_id':'two','source_id':'s2'}]}), encoding='utf8')
    root = tmp_path/'round'
    def controls(*args, **kwargs):
        assert (root/'round.json').is_file()
        return {'evaluator_admitted':False}
    monkeypatch.setattr(host_evaluator, 'prepare_evaluator', controls)
    monkeypatch.setattr(api.batch, 'prepare', lambda *a, **k: pytest.fail('failed control cannot prepare live task'))
    with pytest.raises(ValueError, match='ROUND_EVALUATOR_NOT_ADMITTED'):
        api.prepare(root,dataset,kind='regression',arm='B',case_ids=['one','two'])
    assert api._record(root)['selection']['case_ids'] == ['one','two']


def test_prepare_passes_and_freezes_public_request_convention(tmp_path, monkeypatch):
    from scripts.ifc_repair.repair_comparison import host_evaluator
    dataset = tmp_path/'dataset'
    (dataset/'public').mkdir(parents=True)
    (dataset/'private/evaluation').mkdir(parents=True)
    (dataset/'public/inputs.csv').write_text('case_id,level,task_kind\none,S1,geometry\ntwo,S1,property\n', encoding='utf-8-sig')
    (dataset/'private/evaluation/export.json').write_text(json.dumps({'pair_provenance':[
        {'case_id':'one','source_id':'s1'},{'case_id':'two','source_id':'s2'}]}), encoding='utf8')
    monkeypatch.setattr(host_evaluator, 'prepare_evaluator', lambda *a, **k: {'evaluator_admitted':True})
    seen = []
    monkeypatch.setattr(api.batch, 'prepare', lambda *a, **k: seen.append(k))
    convention = 'existing-ifc-property-units/1.0'
    api.prepare(tmp_path/'round', dataset, kind='regression', arm='E', case_ids=['one','two'],
                request_convention=convention)
    assert seen[0]['request_convention'] == convention
    assert api._record(tmp_path/'round')['selection']['request_convention'] == convention


def test_partial_round_exposes_failure_and_actual_question_without_raw_response(tmp_path, monkeypatch):
    import sqlite3
    from scripts.ifc_repair.repair_comparison.contracts import write_json
    selection = {'kind': 'regression', 'arm': 'B', 'case_ids': ['one', 'two']}
    write_json(tmp_path/'round.json', {'selection': selection, 'selection_sha256': api.batch._digest(selection)})
    folder = tmp_path/'batch'
    folder.mkdir()
    with sqlite3.connect(folder/'control.sqlite') as db:
        db.execute('CREATE TABLE runs(run_id TEXT,state TEXT)')
        for case, state, reason in [('one','awaiting_user','DOOR_OPERATION_REQUIRED'),
                                    ('two','no_output','SCENE_GROUNDING_EXHAUSTED')]:
            db.execute('INSERT INTO runs VALUES(?,?)', (case+'-B', json.dumps({
                'status': state, 'native': {'result': {'reason_code': reason},
                    'scene_diagnostics': {'rounds': [{'issue_codes': ['SCHEMA_INVALID']}]}},
                'question': {'binding': {'native_question': {'question': '请补充开向。'}}},
                'raw_response': 'DO-NOT-EXPORT'})))
    monkeypatch.setattr(api.batch, 'plan', lambda _: {'configuration': {
        'case_ids': ['one','two'], 'case_groups': {'one':['B'], 'two':['B']}}})
    monkeypatch.setattr(api.batch, 'brief_status', lambda _: {
        'state':'attention', 'completed':1, 'total':2, 'known_tokens':42, 'unknown_calls':0})
    summary = api.check(tmp_path)
    assert [r['terminal'] for r in summary['cases']] == ['awaiting_user','no_output']
    assert summary['cases'][0]['clarification'] == '请补充开向。'
    assert summary['cases'][1]['reason'] == 'SCENE_GROUNDING_EXHAUSTED'
    assert not summary['batch_eligible']
    assert 'DO-NOT-EXPORT' not in json.dumps(summary)
    record = api._record(tmp_path)
    assert 'outcome' not in record and record['checkpoint'] == summary
