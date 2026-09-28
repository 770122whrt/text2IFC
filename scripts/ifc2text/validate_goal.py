"""Record scoped, network-blocked IFC2Text admission on committed code."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

from scripts.ifc2text.run_goal import SCOPE, git, load
from text2ifc_ifc2text.llm_pipeline import _write_json

TARGETS = [
    'tests/ifc2text',
    'tests/agent/test_prompt_registry.py',
    'tests/agent/test_interactive_cli_generation.py::test_ready_phase6_2_session_generates_ifc_report_and_db_artifacts',
    'tests/agent/test_phase6_2_openai_compat.py',
    'tests/agent/test_public_brief_failure_evidence.py',
]


class OfflineRecorder:
    def __init__(self):
        self.network_attempts = 0
        self.counts = {'passed': 0, 'failed': 0, 'skipped': 0}
        self.nodeids = []
        self.setup_errors = 0

    def deny(self, *args, **kwargs):
        self.network_attempts += 1
        raise RuntimeError('NETWORK_FORBIDDEN_DURING_OFFLINE_ADMISSION')

    @contextlib.contextmanager
    def network_guard(self):
        # CPython's Windows socketpair uses a loopback connection for an asyncio
        # wakeup pair. Allow only that standard-library construction, not clients.
        from contextvars import ContextVar
        import pytest
        inside_pair = ContextVar('ifc2text_local_socketpair', default=False)
        original_connect = socket.socket.connect
        original_pair = socket.socketpair

        def connect(sock, address):
            if inside_pair.get() and isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
                return original_connect(sock, address)
            return self.deny(address)

        def pair(*args, **kwargs):
            token = inside_pair.set(True)
            try:
                return original_pair(*args, **kwargs)
            finally:
                inside_pair.reset(token)

        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(socket.socket, 'connect', connect)
            patch.setattr(socket.socket, 'connect_ex', self.deny)
            patch.setattr(socket, 'create_connection', self.deny)
            patch.setattr(socket, 'socketpair', pair)
            yield

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            self.counts[report.outcome] += 1
            self.nodeids.append({'nodeid': report.nodeid, 'outcome': report.outcome})
        elif report.failed:
            self.setup_errors += 1
        elif report.skipped:
            self.counts['skipped'] += 1


def main():
    import compileall
    import pytest
    import ifcopenshell
    import shapely
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='scripts/ifc2text/hxp-goal-v0.3.json')
    args = parser.parse_args()
    cfg = load(ROOT / args.config)
    commit = git('rev-parse', 'HEAD')
    if git('status', '--porcelain', '--untracked-files=all', '--', *SCOPE):
        raise RuntimeError('COMMIT_EXECUTION_SCOPE_BEFORE_ADMISSION')
    base = ROOT / cfg['output'] / 'validation'
    base.mkdir(parents=True, exist_ok=True)
    if (base / 'admission.json').exists():
        previous = load(base / 'admission.json')
        archived = base / ('admission-' + previous['code_commit'][:12] + '.json')
        if not archived.exists():
            _write_json(archived, previous)
    root = base / ('check-' + commit[:12])
    root.mkdir(exist_ok=False)
    _write_json(base.parent / 'config.json', cfg)
    temp = root / 'pytest-temp'
    command = [*TARGETS, '-q', '--basetemp=' + str(temp), '-p', 'no:cacheprovider']
    observer = OfflineRecorder()
    stream = io.StringIO()
    start = datetime.now(timezone.utc).isoformat()
    with observer.network_guard():
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            exit_code = int(pytest.main(command, plugins=[observer]))
    log = stream.getvalue()
    (root / 'pytest.log').write_text(log, encoding='utf-8')
    compiled = all(compileall.compile_dir(str(ROOT / path), quiet=1) for path in
                   ['src/text2ifc_ifc2text', 'tests/ifc2text', 'scripts/ifc2text'])
    clean = not git('status', '--porcelain', '--untracked-files=all', '--', *SCOPE)
    valid = (exit_code == 0 and observer.counts['passed'] > 0 and not observer.counts['failed']
             and not observer.counts['skipped'] and not observer.setup_errors
             and observer.network_attempts == 0 and compiled and clean)
    record = {
        'schema_version': 'text2ifc/ifc2text-goal-admission/0.3',
        'status': 'admitted' if valid else 'blocked',
        'code_commit': commit, 'branch': git('branch', '--show-current'),
        'started_at': start, 'finished_at': datetime.now(timezone.utc).isoformat(),
        'python': platform.python_version(), 'platform': platform.platform(),
        'ifcopenshell': ifcopenshell.version, 'shapely': shapely.__version__,
        'command': ['python', '-m', 'pytest', *command], 'exit_code': exit_code,
        'tests': observer.counts, 'setup_errors': observer.setup_errors,
        'nodeids': observer.nodeids, 'log_path': (root.relative_to(base) / 'pytest.log').as_posix(),
        'log_sha256': hashlib.sha256(log.encode('utf-8')).hexdigest(),
        'compileall': compiled, 'execution_scope_clean': clean,
        'network_transport_attempted': bool(observer.network_attempts),
        'scope_paths': SCOPE, 'full_preflight': False,
        'evidence_kind': 'synthetic_and_frozen_provider_regression_not_model_capability',
        'public_path': 'IFC extraction -> hierarchical writing -> text-only public Generation -> IFC -> diagnostic Compare',
        'live_reconstruction_mode': 'single attempt; questions or unsupported facts stop; no automatic answers',
        'not_applicable': ['repair source mutation transactions', 'private damaged/pristine benchmark'],
        'limitations': ['offline semantic model responses are frozen fixtures',
                        'fine mesh equality and room semantics are not certified',
                        'real-world reconstruction may ask for clarification or reject unsupported facts'],
    }
    _write_json(root / 'admission.json', record)
    _write_json(base / 'admission.json', record)
    print(json.dumps({k: record[k] for k in ['status', 'code_commit', 'tests', 'network_transport_attempted', 'compileall']}, indent=2))
    print(log[-1800:])
    return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
