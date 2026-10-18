"""Live hold changes affect scheduling, without resetting tasks or workspaces."""
from contextlib import closing

import pytest

from scripts.ifc_repair import batch_resilience as resilience
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from tests.ifc_repair.repair_comparison.test_parallel_batch import _parallel_batch, _jobs


@pytest.mark.parametrize('release', [True, False])
def test_provider_release_during_other_job_refreshes_dispatch(tmp_path, monkeypatch, release):
    root, ledger, order, _ = _parallel_batch(
        tmp_path, monkeypatch, capacity=1, groups=('B', 'E', 'C'))
    original_plan = (root/'batch.json').read_bytes()
    original_config = (root/'experiment.json').read_bytes()
    resilience.install(root, monkeypatch=monkeypatch)
    monkeypatch.setattr(batch, 'CLI', ['python', '-m', 'carrier'])
    holds = resilience.Holds(root)
    holds.hold('E', reason='Temporary GPT interface failure', code=429, run_id=order[1])
    before = {run: ledger.snapshot(run) for run in order[1:]}
    started, _, _ = _jobs(monkeypatch, root, ledger, order)
    original_process = batch._Process

    class ReleaseAfterOtherJob(original_process):
        def poll(self):
            outcome = super().poll()
            if release and self.role == 'run' and self.run == order[0] and outcome == 0:
                holds.release(['C', 'E'], reason='Operator requested resuming GPT')
            return outcome

    monkeypatch.setattr(batch, '_Process', ReleaseAfterOtherJob)
    assert batch.run(root) == 0
    assert started == (order if release else order[:1])
    assert (root/'batch.json').read_bytes() == original_plan
    assert (root/'experiment.json').read_bytes() == original_config
    for run in order[1:]:
        state = ledger.snapshot(run)
        assert state['budget'] == before[run]['budget']
        assert state['metadata'] == before[run]['metadata']
        assert state['status'] == ('no_output' if release else 'ready')
    with closing(batch._database(root)) as db:
        assert db.execute('SELECT count(*) FROM runs').fetchone()[0] == 3
    assert holds.groups() == ([] if release else ['C', 'E'])
