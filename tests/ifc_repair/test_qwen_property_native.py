"""The same Qwen HTTP seam in the existing property-capable Linux image."""
import os
from pathlib import Path

import pytest

from scripts.ifc_repair.repair_comparison.contracts import read_json, write_json
from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison import demo_workflow as carrier
from scripts.ifc_repair.repair_comparison.formal_admission import file_ref
from scripts.ifc_repair.repair_comparison.contracts import sha256
from scripts.ifc_repair.repair_comparison.ledger import Ledger
from scripts.ifc_repair import qwen_batch as qwen
from tests.ifc_repair import test_qwen_batch_native as qwen_native
from tests.ifc_repair.repair_comparison import test_scalable_native as native


@pytest.mark.skipif(os.environ.get('REPAIR_QWEN_DOCKER') != '1', reason='explicit existing property Docker gate')
def test_f_property_image_uses_same_qwen_context_and_resume(tmp_path, request, monkeypatch):
    # G runs in the generic image, already covered by its own matrix. The
    # property image belongs to the Harness group F only.
    policy = qwen_native.acceptance_policy()
    root = tmp_path/'runtime'
    for module, name in ((carrier, 'bindings'), (carrier, 'WireGateway'), (batch, 'CLI'), (batch, '_interface_fault')):
        monkeypatch.setattr(module, name, getattr(module, name))
    monkeypatch.setattr(carrier, '_qwen_entry_installed', False, raising=False)
    qwen.install(root, policy)
    original = carrier.initialize
    def initialize(*args, **kwargs):
        kwargs['providers'] = qwen.limited_providers(kwargs['providers'], policy)
        config = original(*args, **kwargs)
        write_json(root/'qwen-policy.json', qwen.policy_document(policy))
        return config
    monkeypatch.setattr(carrier, 'initialize', initialize)
    monkeypatch.setattr(native, 'default_providers', lambda: qwen.limited_providers(qwen.default_providers(), policy))
    monkeypatch.setattr(native, 'CLI', qwen_native.CLI+['worker'])
    previous_path = Path(os.environ['REPAIR_QWEN_PRIOR_NATIVE'])
    previous = read_json(previous_path)
    stop = previous['timeout_stop']
    assert stop['quiescent'] and stop['container_stopped'] and stop['timed_out']
    assert sha256(Path(stop['evidence']['path'])) == stop['evidence']['sha256']
    def reuse_timeout(_):
        current = batch._runtime_bindings(carrier.bindings(read_json(root/'experiment.json')['configuration']))
        old = batch._runtime_bindings(previous['runtime_bindings_after'])
        qwen_native.unchanged_stop_sources(current, old)
        return {**stop, 'reused_from': file_ref(previous_path)}
    monkeypatch.setattr(native, '_native_timeout_check', reuse_timeout)
    native._native_grid(tmp_path, request, property_runtime=True,
        case_groups={'case-001': ['F'], 'case-002': ['F']})
    receipt = read_json(tmp_path/'native-stage.json')
    receipt['helper_test_file'] = file_ref(Path(qwen_native.__file__))
    receipt['test_file'] = file_ref(Path(__file__))
    write_json(tmp_path/'native-stage.json', receipt)
    ledger = Ledger(root/'control.sqlite')
    assert all(any(e['kind'] == 'qwen_context_projection' for e in ledger.events(run)) for run in receipt['configuration']['order'])
    batch._verify_native(tmp_path/'native-stage.json', receipt['configuration'], groups=['F'])
