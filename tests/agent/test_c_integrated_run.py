"""Public C continuation controls; all Providers in this file are fake."""
import importlib.util
import json
from pathlib import Path

import pytest


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ROOT = Path('dataset/processed/ifc-presentation-validation')
SOURCE = ROOT/'c-shaped-teaching-building-20260910'


@pytest.mark.parametrize('status', ['compiled', 'needs_clarification'])
def test_exact_runner_reuses_budget_and_only_generates_when_ready(tmp_path, status):
    from tests.agent.test_phase6_5_staged_generation import SequenceProvider
    m = module('c_integrated', ROOT/'c-shaped-integrated-20260911/run_case.py')
    fixture = module('c_offline', SOURCE/'offline_case.py')
    brief, candidate = fixture.build()
    if status == 'needs_clarification':
        brief = json.loads((ROOT/'c-shaped-brief-budget-experiment-20260910/live/64k/design-brief/design-brief.json').read_text(encoding='utf-8'))
    audit = {'schema_version':'text2ifc/audit/2.0','recommendation':'accept','blocking':False,
             'deterministic_gate_status':'passed','findings':[],
             'evidence_paths':['generator/candidate.json','repair/route.json']}
    provider = SequenceProvider([brief, candidate, audit])
    previous = Path(m.PRIOR_BUDGET).read_bytes()
    result = m.execute(output=tmp_path/'run', provider_factory=lambda:provider, evidence_class='fake')
    assert result['status'] == status
    assert result['budget_before']['calls_used'] == 4
    assert result['budget_before']['tokens_used_or_reserved'] == 300540
    assert result['budget_after']['calls_used'] == (7 if status == 'compiled' else 5)
    assert Path(m.PRIOR_BUDGET).read_bytes() == previous
    if status == 'compiled':
        checker = module('c_checker', SOURCE/'check_ifc.py')
        assert checker.check_ifc(Path(result['result']['ifc_path']))['status'] == 'passed'
    else:
        assert not list((tmp_path/'run').rglob('output.ifc'))


def test_existing_output_stops_before_provider(tmp_path):
    m = module('c_integrated', ROOT/'c-shaped-integrated-20260911/run_case.py')
    def forbidden():
        raise AssertionError('No transport permitted')
    with pytest.raises(FileExistsError):
        m.execute(output=tmp_path, provider_factory=forbidden, evidence_class='fake')
