"""Context expansion preserves completed evidence, task budgets and ownership."""
from copy import deepcopy
import json
import sqlite3

import httpx
import pytest

from scripts.ifc_repair import qwen_batch as qwen
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from scripts.ifc_repair.repair_comparison.group_config import default_providers, scalable_configuration
from tests.ifc_repair.test_qwen_batch import make_ledger, success
from tests.ifc_repair.repair_comparison.test_parallel_batch import _parallel_batch


def root_fixture(tmp_path, monkeypatch):
    root, ledger, order, _ = _parallel_batch(tmp_path, monkeypatch, capacity=4, groups=('F', 'G'))
    value = read_json(root/'batch.json')
    providers = qwen.limited_providers(default_providers(), qwen.QwenPolicy())
    value['configuration']['providers'] = providers
    value['configuration']['budgets'] = {ledger.snapshot(run)['case_id']:ledger.snapshot(run)['budget'] for run in order}
    value.pop('sha256')
    value['sha256'] = batch._digest(value)
    write_json(root/'batch.json', value)
    runtime = read_json(root/'experiment.json')
    runtime['configuration'] = deepcopy(value['configuration'])
    runtime.update({k: deepcopy(v) for k, v in value['configuration'].items()})
    write_json(root/'experiment.json', runtime)
    write_json(root/'qwen-policy.json', qwen.policy_document(qwen.QwenPolicy()))
    with ledger.transaction() as db:
        db.execute('CREATE TABLE IF NOT EXISTS batch_control(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        for name in ['property_authorization', 'clarification_policy']:
            db.execute('INSERT OR REPLACE INTO batch_control VALUES(?,?)',
                (name, json.dumps({'batch_sha256':value['sha256'], 'unchanged_fact':'public-only'})))
    write_json(root/'service.json', {'state':'stopped'})
    return root, ledger, order


def table_bytes(root):
    with sqlite3.connect(root/'control.sqlite') as db:
        return {table:db.execute('SELECT * FROM '+table+' ORDER BY rowid').fetchall()
                for table in ['runs', 'calls', 'events']}


def test_expansion_keeps_terminal_calls_budgets_and_four_slots(tmp_path, monkeypatch):
    root, ledger, order = root_fixture(tmp_path, monkeypatch)
    ledger.start(order[0]); ledger.reserve(order[0], 'old', 1)
    ledger.settle(order[0], 'old', usage=None, response={'usage_complete':False}, failed=True)
    ledger.finish(order[0], 'no_output', detail='original failure')
    before = table_bytes(root)
    original = read_json(root/'batch.json')
    result = qwen.configure_context(root, context_tokens=256000, revision='test256')
    assert result['state'] == 'context_applied_requires_admission'
    assert table_bytes(root) == before
    updated = batch.plan(root)
    assert updated['scheduler'] == {'max_running':4}
    assert updated['configuration']['budgets'] == original['configuration']['budgets']
    assert updated['configuration']['providers']['qwen']['max_input_tokens'] == 256000
    assert updated['configuration']['configuration_version'].endswith('/0.2')
    assert qwen.load_policy(root).context_tokens == 256000
    assert read_json(root/'experiment.json')['configuration'] == updated['configuration']
    with sqlite3.connect(root/'control.sqlite') as db:
        for name in ['property_authorization','clarification_policy']:
            p=json.loads(db.execute('SELECT value FROM batch_control WHERE key=?',(name,)).fetchone()[0])
            assert p == {'batch_sha256':updated['sha256'], 'unchanged_fact':'public-only'}
    assert qwen.configure_context(root, context_tokens=256000, revision='test256')['state'] == 'unchanged'
    assert table_bytes(root) == before


def test_active_task_blocks_context_change(tmp_path, monkeypatch):
    root, ledger, order = root_fixture(tmp_path, monkeypatch)
    ledger.start(order[0])
    before = {p.name:p.read_bytes() for p in [root/'batch.json',root/'experiment.json',root/'qwen-policy.json']}
    with pytest.raises(ValueError, match='QUIESCENT'):
        qwen.configure_context(root, context_tokens=256000, revision='blocked')
    assert {p.name:p.read_bytes() for p in [root/'batch.json',root/'experiment.json',root/'qwen-policy.json']} == before


def test_configuration_version_does_not_relabel_legacy_profile(tmp_path):
    providers = qwen.limited_providers(default_providers(), qwen.QwenPolicy(context_tokens=256000))
    from scripts.ifc_repair.repair_comparison.budget import fixed_budget_profile
    common=dict(cases_root=tmp_path,case_ids=['case'],budgets={'case':fixed_budget_profile('S1')},
                case_groups={'case':['F','G']})
    assert scalable_configuration(providers=default_providers(),**common)['configuration_version'].endswith('/0.1')
    assert scalable_configuration(providers=providers,**common)['configuration_version'].endswith('/0.2')


def test_partial_publish_recovers_without_resetting_evidence(tmp_path, monkeypatch):
    root, ledger, order = root_fixture(tmp_path, monkeypatch)
    before = table_bytes(root)
    original = batch._replace_bytes
    def interrupted(path, data):
        if path.name == 'qwen-policy.json':
            raise OSError('simulated restart')
        original(path,data)
    monkeypatch.setattr(batch, '_replace_bytes', interrupted)
    with pytest.raises(OSError, match='simulated restart'):
        qwen.configure_context(root, context_tokens=256000, revision='recovery')
    assert (root/'qwen-context-revision.pending').exists()
    with pytest.raises(ValueError, match='RECOVERY_REQUIRED'):
        qwen.main(['status','--root',str(root)])
    monkeypatch.setattr(batch, '_replace_bytes', original)
    qwen.configure_context(root, context_tokens=256000, revision='recovery')
    assert table_bytes(root) == before
    assert not (root/'qwen-context-revision.pending').exists()


def test_admission_rejects_budget_or_evidence_changes(tmp_path, monkeypatch):
    root, ledger, order = root_fixture(tmp_path, monkeypatch)
    previous = {'configuration':deepcopy(batch.plan(root)['configuration'])}
    qwen.configure_context(root, context_tokens=256000, revision='sealed')
    value = batch.plan(root)
    binding = {'files':{}, 'budget':'unchanged'}
    assert qwen.verify_context_revision(root,previous,value,binding,binding)
    changed = deepcopy(value)
    changed['configuration']['budgets'] = {}
    with pytest.raises(ValueError, match='CONFIGURATION_CHANGED'):
        qwen.verify_context_revision(root,previous,changed,binding,binding)
    ledger.start(order[0])
    with pytest.raises(ValueError, match='EVIDENCE_CHANGED'):
        qwen.verify_context_revision(root,previous,value,binding,binding)


@pytest.mark.parametrize('arm', ['F','G'])
def test_256k_gateway_reserves_tokens_not_serialized_bytes(tmp_path, arm):
    ledger = make_ledger(tmp_path, arm=arm)
    policy=qwen.QwenPolicy(context_tokens=256000,tokenizer_path=qwen.default_policy().tokenizer_path)
    received=[]
    def transport(request):
        received.append(len(request.content))
        return success()
    with qwen.QwenGateway(ledger,tmp_path/'wire',policy=policy,transport=httpx.MockTransport(transport)) as gateway:
        token=gateway.register('case-'+arm,model='qwen',api_key=None,
            endpoints={'chat':'https://fake.test/chat'},evidence_class='fake',max_output_tokens=8192)
        response=httpx.post(gateway.url+'/'+token+'/v1/chat/completions',trust_env=False,timeout=20,
            json={'model':'qwen','messages':[{'role':'user','content':' hello'*150000}],'max_tokens':8192})
    assert response.status_code == 200
    assert received[0] > 750000
    calls=ledger.calls('case-'+arm)
    assert 150000 <= calls[0]['reservation'] < 256000
    assert len(calls) == 1
