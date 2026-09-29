"""Temporary pytest products must stay outside retained experiment evidence."""
from pathlib import Path


def test_pytest_scratch_is_unique_and_does_not_modify_existing_run(tmp_path):
    from scripts.ifc2text.temporary_output import new_pytest_basetemp

    first = new_pytest_basetemp(tmp_path)
    first.mkdir()
    sentinel = first / 'keep.txt'
    sentinel.write_text('previous failure', encoding='utf-8')
    second = new_pytest_basetemp(tmp_path)
    assert first.parent == second.parent == tmp_path / '.tmp' / 'ifc2text-pytest'
    assert first != second and not second.exists()
    assert sentinel.read_text(encoding='utf-8') == 'previous failure'
    assert not (tmp_path / 'dataset').exists()


def test_pytest_scratch_resolves_relative_workspace(tmp_path, monkeypatch):
    from scripts.ifc2text.temporary_output import new_pytest_basetemp

    monkeypatch.chdir(tmp_path)
    path = new_pytest_basetemp(Path('.'))
    assert path.is_absolute()
    assert path.parent == tmp_path / '.tmp' / 'ifc2text-pytest'
