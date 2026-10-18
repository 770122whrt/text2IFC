"""Keep disposable pytest fixtures separate from retained experiment evidence."""
from pathlib import Path
import re
import shutil
from uuid import uuid4


def new_pytest_basetemp(workspace: Path) -> Path:
    """Return a fresh path: pytest clears its basetemp when a run starts."""
    parent = workspace.resolve() / '.tmp' / 'ifc2text-pytest'
    parent.mkdir(parents=True, exist_ok=True)
    return parent / uuid4().hex


def run_pytest_with_cleanup(workspace: Path, command, runner, **options):
    """Run in a single disposable workspace; logs and JUnit belong outside it."""
    root = workspace.resolve()
    parent = root / '.tmp' / 'ifc2text-pytest'
    values = [arg.split('=', 1)[1] for arg in command if arg.startswith('--basetemp=')]
    if len(values) != 1:
        raise ValueError('ONE_MANAGED_PYTEST_SCRATCH_REQUIRED')
    scratch = Path(values[0]).absolute()
    if (scratch.parent != parent or not re.fullmatch(r'[0-9a-f]{32}', scratch.name)
            or scratch.resolve() != scratch or not scratch.is_relative_to(root)):
        raise ValueError('UNMANAGED_PYTEST_SCRATCH')
    for arg in command:
        if arg.startswith(('--junitxml=', '--junit-xml=')):
            report = Path(arg.split('=', 1)[1]).resolve()
            if report.is_relative_to(scratch):
                raise ValueError('REPORT_INSIDE_PYTEST_SCRATCH')
    original_error = None
    try:
        return runner(command, **options)
    except BaseException as error:
        original_error = error
        raise
    finally:
        try:
            if scratch.is_symlink() or scratch.is_junction() or scratch.resolve() != scratch:
                raise OSError('PYTEST_SCRATCH_CHANGED_TO_LINK')
            if scratch.exists():
                shutil.rmtree(scratch)
        except OSError as error:
            if original_error is None:
                raise
            original_error.add_note(f'Pytest scratch cleanup failed: {error}')
