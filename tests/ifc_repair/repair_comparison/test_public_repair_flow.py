from pathlib import Path
import sys
import pytest
from scripts.ifc_repair.repair_comparison.direct_runner import DirectRunner, ReplayProvider
from scripts.ifc_repair.repair_comparison.scoring import score

REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize('arm', ['A', 'C'])
@pytest.mark.parametrize('case_id,kind', [('case-001', 'window'), ('case-002', 'door')])
def test_public_only_script_repairs_real_development_input(tmp_path, arm, case_id, kind):
    case = REPO / 'dataset/processed/ifc-repair/repair-comparison/development' / case_id
    runner = DirectRunner.create(case / 'public', tmp_path, case_id=case_id, arm=arm,
                                 budget={'tokens': 1000, 'calls': 10, 'active_seconds': 600, 'tool_seconds': 90, 'extensions': []})
    script = Path(__file__).with_name('public_repair_fixture.py').read_text(encoding='utf-8')
    calls = [('write_file', {'path': 'work/fixture.py', 'text': script}),
             ('execute', {'argv': [sys.executable, 'work/fixture.py', kind]}),
             ('submit', {'path': 'output/repaired.ifc'})]
    replay = [{'tool_calls': [{'name': name, 'arguments': args}], 'usage': {'input_tokens': 2, 'output_tokens': 3}} for name, args in calls]
    state = runner.run(ReplayProvider(replay), reservation=100)
    assert state['status'] == 'submitted', runner.ledger.events(runner.run_id)
    report = score(case, Path(state['artifact']['path']), terminal=state['status'])
    assert report['repair_success'] is True, report
    assert (case / 'public/model.ifc').read_bytes() == (tmp_path / 'inputs' / case_id / 'model.ifc').read_bytes()
