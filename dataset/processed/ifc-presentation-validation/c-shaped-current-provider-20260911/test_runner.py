"""Offline latest-ledger wrapper check; no network and no live claims."""
from pathlib import Path
import pytest
from tests.agent.test_c_plan_run import fixture,Provider,module
from tests.agent.test_phase6_5_staged_generation import SequenceProvider

@pytest.mark.parametrize('mode',['complete','invalid_json'])
def test_latest_ledger_public_runner(tmp_path,mode):
    runner=module('c_latest_runner',Path(__file__).with_name('run_case.py'))
    brief,candidate=fixture()
    provider=Provider(brief,candidate) if mode=='complete' else SequenceProvider(['{'])
    before=runner.PRIOR_BUDGET.read_bytes()
    result=runner.execute(output=tmp_path/'run',provider_factory=lambda:provider,evidence_class='fake')
    assert result['budget_before']['calls_used']==17
    assert result['budget_before']['tokens_used_or_reserved']==1377030
    assert runner.PRIOR_BUDGET.read_bytes()==before
    if mode=='complete':
        assert result['status']=='compiled',result
        checker=module('c_latest_checker',runner.SOURCE/'check_ifc.py')
        checked=checker.check_ifc(Path(result['result']['ifc_path']))
        assert checked['status']=='passed',checked
    else:
        assert result['status']!='compiled' and len(provider.calls)==1
        assert not list((tmp_path/'run').rglob('*.ifc'))
