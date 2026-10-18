"""The public request convention is an explicit newly prepared batch choice."""
import pytest

from scripts.ifc_repair.repair_comparison import batch_workflow as batch


POLICY = 'existing-ifc-property-units/1.0'


@pytest.mark.parametrize('convention', [None, POLICY])
def test_prepare_freezes_only_an_explicit_request_convention(tmp_path, monkeypatch, convention):
    inputs = tmp_path/'inputs'
    inputs.mkdir()
    (inputs/'one.ifc').write_bytes(b'opaque controller fixture')
    (inputs/'one.txt').write_text('Restore property.', encoding='utf8')
    original = batch.materialize_public
    received = []
    def materialize(cases, destination, **kwargs):
        received.append(kwargs)
        return original(cases, destination)
    monkeypatch.setattr(batch, 'materialize_public', materialize)
    monkeypatch.setattr(batch, 'check_ifc', lambda _: {'passed': True, 'status': 'passed'})
    root = tmp_path/'prepared'
    batch.prepare(root, inputs, scope='full', input_format='pairs', default_level='S1',
                  mode='offline', groups=['E'], request_convention=convention)
    value = batch.plan(root)
    if convention is None:
        assert 'request_convention' not in value and received == [{}]
    else:
        assert value['request_convention'] == POLICY
        assert received == [{'request_convention': POLICY}]


def test_request_convention_only_available_for_new_prepare(tmp_path, capsys):
    assert batch.main(['resume', '--root', str(tmp_path), '--request-convention', POLICY]) == 2
    assert 'REQUEST_CONVENTION_UNSTARTED_ONLY' in capsys.readouterr().out
