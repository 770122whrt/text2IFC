"""Keep disposable pytest fixtures separate from retained experiment evidence."""
from pathlib import Path
from uuid import uuid4


def new_pytest_basetemp(workspace: Path) -> Path:
    """Return a fresh path: pytest clears its basetemp when a run starts."""
    parent = workspace.resolve() / '.tmp' / 'ifc2text-pytest'
    parent.mkdir(parents=True, exist_ok=True)
    return parent / uuid4().hex
