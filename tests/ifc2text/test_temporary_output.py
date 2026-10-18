"""Temporary pytest products must stay outside retained experiment evidence."""
from pathlib import Path
import pytest


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


@pytest.mark.parametrize('exit_code', [0, 1])
def test_runner_cleans_success_and_failure_but_preserves_logs(tmp_path, exit_code):
    from scripts.ifc2text.temporary_output import new_pytest_basetemp, run_pytest_with_cleanup
    scratch = new_pytest_basetemp(tmp_path)
    other = new_pytest_basetemp(tmp_path)
    other.mkdir()
    (other / 'active.txt').write_text('another run')
    report = tmp_path / 'tests.xml'

    def run(command, **options):
        assert options == {'plugins': ['recorder']}
        scratch.mkdir()
        (scratch / 'generated.ifc').write_text('fixture')
        report.write_text('<testsuite/>')
        return exit_code

    assert run_pytest_with_cleanup(tmp_path, ['--basetemp=' + str(scratch)], run,
                                   plugins=['recorder']) == exit_code
    assert not scratch.exists()
    assert report.read_text() == '<testsuite/>'
    assert (other / 'active.txt').read_text() == 'another run'


def test_runner_cleans_on_exception(tmp_path):
    from scripts.ifc2text.temporary_output import new_pytest_basetemp, run_pytest_with_cleanup
    scratch = new_pytest_basetemp(tmp_path)
    def run(command):
        scratch.mkdir()
        (scratch / 'partial.json').write_text('{}')
        raise TimeoutError('child timed out')
    with pytest.raises(TimeoutError, match='child timed out'):
        run_pytest_with_cleanup(tmp_path, ['--basetemp=' + str(scratch)], run)
    assert not scratch.exists()


def test_runner_refuses_existing_evidence_directory(tmp_path):
    from scripts.ifc2text.temporary_output import run_pytest_with_cleanup
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    (evidence / 'output.ifc').write_text('accepted')
    with pytest.raises(ValueError, match='SCRATCH'):
        run_pytest_with_cleanup(tmp_path, ['--basetemp=' + str(evidence)],
                                lambda command: pytest.fail('Must not run'))
    assert (evidence / 'output.ifc').read_text() == 'accepted'


def test_runner_rejects_report_inside_disposable_directory(tmp_path):
    from scripts.ifc2text.temporary_output import new_pytest_basetemp, run_pytest_with_cleanup
    scratch = new_pytest_basetemp(tmp_path)
    with pytest.raises(ValueError, match='REPORT_INSIDE'):
        run_pytest_with_cleanup(tmp_path, ['--basetemp=' + str(scratch),
                               '--junitxml=' + str(scratch / 'tests.xml')],
                               lambda command: pytest.fail('Must not run'))


@pytest.mark.parametrize('passes', [True, False])
def test_real_pytest_child_removes_fixtures_keeps_junit(tmp_path, passes):
    import subprocess
    import sys
    import xml.etree.ElementTree as ET
    from scripts.ifc2text.temporary_output import new_pytest_basetemp, run_pytest_with_cleanup
    test_file = tmp_path / 'test_child.py'
    test_file.write_text('def test_fixture(tmp_path):\n'
                         '    (tmp_path / "object.ifc").write_text("fixture")\n'
                         f'    assert {passes}\n', encoding='utf-8')
    scratch = new_pytest_basetemp(tmp_path)
    report = tmp_path / 'result.xml'
    command = [sys.executable, '-m', 'pytest', str(test_file), '-q', '-o', 'addopts=',
               '-p', 'no:cacheprovider', '--basetemp=' + str(scratch),
               '--junitxml=' + str(report)]
    result = run_pytest_with_cleanup(tmp_path, command, subprocess.run, cwd=tmp_path,
                                    capture_output=True, timeout=60)
    assert result.returncode == (0 if passes else 1), result.stdout
    assert not scratch.exists()
    suite = ET.parse(report).find('testsuite')
    assert int(suite.attrib['tests']) == 1
    assert int(suite.attrib['failures']) == (0 if passes else 1)
