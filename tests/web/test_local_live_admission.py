"""Local demo activation contracts; all configuration is placeholder-only and keyless."""
import pytest
from text2ifc_web.store import Store
from text2ifc_web.contracts import WebError
from text2ifc_web.live_runtime import load_local_provider_environment


def test_live_task_limit_is_atomic_persistent_and_deduplicated(tmp_path):
    store=Store(tmp_path)
    first,fresh=store.claim_start('prepared-one','one',task_limit=('reviewed-local',1))
    assert fresh
    again,fresh=store.claim_start('prepared-one','other-key',task_limit=('reviewed-local',1))
    assert not fresh and again['task_id']==first['task_id']
    with pytest.raises(WebError,match='LIVE_TASK_LIMIT'):
        Store(tmp_path).claim_start('prepared-two','two',task_limit=('reviewed-local',1))
    with store.connect() as db:assert db.execute('select count(*) from tasks').fetchone()[0]==1


def test_local_config_uses_only_selected_provider_fields_and_no_parent_search(tmp_path,monkeypatch):
    import dotenv
    monkeypatch.setattr('pathlib.Path.is_file',lambda self:True)
    observed=[]
    def fixture(path):
        observed.append(path)
        return {'DEEPSEEK_API_KEY':'[REDACTED_SECRET]','OPENAI_BASE_URL':'https://api.deepseek.com','UNRELATED_PASSWORD':'[REDACTED_SECRET]'}
    monkeypatch.setattr(dotenv,'dotenv_values',fixture)
    env=load_local_provider_environment(tmp_path,{})
    assert env['TEXT2IFC_PROVIDER']=='deepseek' and env['TEXT2IFC_DEEPSEEK_MODEL']=='deepseek-flash'
    assert 'UNRELATED_PASSWORD' not in env
    assert observed==[tmp_path/'.env']


def test_private_endpoint_does_not_get_an_invented_model(tmp_path,monkeypatch):
    monkeypatch.setattr('pathlib.Path.is_file',lambda self:False)
    env=load_local_provider_environment(tmp_path,{'OPENAI_BASE_URL':'https://example.invalid/v1'})
    assert 'TEXT2IFC_DEEPSEEK_MODEL' not in env
