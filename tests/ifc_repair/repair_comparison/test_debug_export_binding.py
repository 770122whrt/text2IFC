"""Native task hashes bind executed bytes; public request bytes stay frozen."""
import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch
from scripts.ifc_repair.repair_comparison.contracts import read_json, sha256
from tests.ifc_repair.repair_comparison.test_scalable_workflow import debug_export_batch


@pytest.mark.parametrize('debug_export_batch', [
    b'Repair this public object.\n',
    b'Repair this public object.\r\n',
    b'First line.\r\nSecond line.\nThird line.\r\n',
    b'  First line.\nSecond line.  ',
    '修复公开属性。\r\n保持现有单位。\n'.encode('utf8'),
], indirect=True, ids=['lf', 'crlf', 'mixed-lines', 'outer-whitespace', 'unicode'])
def test_debug_export_binds_actual_native_task_without_changing_public_input(debug_export_batch):
    root, ledger, calls = debug_export_batch
    source = root/'cases/one/public/request.txt'
    native = root/'workspaces/one-E/task.txt'
    before = source.read_bytes(), native.read_bytes(), ledger.snapshot('one-E')
    assert batch.debug_export(root)['exported'] == 1
    receipt = read_json(root/'debug/one-E/receipt.json')
    assert receipt['identity']['binding']['request_sha256'] == sha256(native)
    assert receipt['identity']['batch_sha256'] == batch.plan(root)['sha256']
    assert source.read_bytes() == before[0] and native.read_bytes() == before[1]
    assert ledger.snapshot('one-E') == before[2]
    assert batch.debug_export(root)['reused'] == 1 and len(calls) == 1


def test_debug_export_rejects_semantically_changed_native_request_before_copy(debug_export_batch):
    root, ledger, calls = debug_export_batch
    (root/'workspaces/one-E/task.txt').write_text('Different task.\n', encoding='utf8')
    with pytest.raises(ValueError, match='DEBUG_EXPORT_REQUEST_BINDING_MISMATCH'):
        batch.debug_export(root)
    assert calls == [] and not (root/'debug').exists()


def test_debug_export_still_rejects_snapshot_request_hash_mismatch(debug_export_batch):
    root, ledger, calls = debug_export_batch
    # Same decoded request, distinct bytes: this current workspace no longer
    # matches the frozen Linux task's byte-level hash captured by the fixture.
    native = root/'workspaces/one-E/task.txt'
    text = native.read_text(encoding='utf8')
    raw = native.read_bytes()
    replacement = text.replace('\n', '\r\n').encode('utf8')
    if replacement == raw:
        replacement = text.encode('utf8')
    native.write_bytes(replacement)
    with pytest.raises(ValueError, match='DEBUG_EXPORT_BINDING_MISMATCH'):
        batch.debug_export(root)
    assert len(calls) == 1
    assert not (root/'debug/one-E/receipt.json').exists()
