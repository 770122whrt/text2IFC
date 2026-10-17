"""Reused gates may excuse only the freshly revalidated aggregation module."""
from copy import deepcopy

import pytest

from scripts.ifc_repair.repair_comparison import formal_admission as admission


def test_revalidated_aggregation_cannot_excuse_a_runtime_change(tmp_path,monkeypatch):
    log=tmp_path/'gate.log';log.write_text('1 passed in 1s',encoding='utf8')
    command=['python','-m','pytest','tests/test_formal_admission.py']
    sources={admission.HERE+'formal_admission.py':'before','src/text2ifc_ifc_repair/api.py':'stable'}
    monkeypatch.setattr(admission,'capture_sources',lambda scope:sources)
    receipt=admission.make_suite_receipt(log,command=command,exit_code=0,scope='execution',
        source_bindings=deepcopy(sources),capture_source='synthetic gate guard only')
    sources[admission.HERE+'formal_admission.py']='after'
    with pytest.raises(ValueError,match='STALE'):
        admission.validate_suite_receipt(receipt)
    allowed={admission.HERE+'formal_admission.py'}
    assert admission.validate_suite_receipt(receipt,revalidated_sources=allowed)
    sources['src/text2ifc_ifc_repair/api.py']='new runtime'
    with pytest.raises(ValueError,match='STALE'):
        admission.validate_suite_receipt(receipt,revalidated_sources=allowed)
