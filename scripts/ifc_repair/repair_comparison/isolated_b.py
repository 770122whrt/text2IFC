"""Isolated B carrier for the unchanged public RepairAPI and default OpenAI SDK.

The host owns credentials, gateway accounting and experiment admission. This
carrier accepts only an internal gateway and a dummy credential. Each command
starts a disposable worker; Linux state is retained in one task-specific volume.
No ledger, experiment scorer, private IFC or mutation data is packaged.
"""
from __future__ import annotations

import ast
import contextlib
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import uuid
from urllib.parse import urlsplit


DUMMY_KEY = 'isolated-b-no-external-credential'
MODEL = 'deepseek-v4-flash'
SOURCE_ENTRIES = ('text2ifc_ifc_repair.api', 'text2ifc_agent.openai_compat',
                  'text2ifc_ifc_repair.validation_worker')
SOURCE_PACKAGES = frozenset(('text2ifc_agent', 'text2ifc_contract', 'text2ifc_extractor',
                             'text2ifc_ifc_repair', 'text2ifc_knowledge',
                             'text2ifc_presentation', 'text2ifc_text'))
RESULT_PREFIX = 'ISOLATED_B_RESULT='


def _checked_file(root: Path, path: Path) -> Path:
    root, path = root.absolute(), path.absolute()
    if not path.is_relative_to(root):
        raise ValueError('BUNDLE_PATH_ESCAPE')
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, 'is_junction') and item.is_junction()):
            raise ValueError('BUNDLE_SYMLINK_FORBIDDEN')
        if item == root:
            break
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('BUNDLE_FILE_MISSING_OR_ESCAPE')
    return path


def _source_closure(repo: Path) -> set[Path]:
    """Resolve only local static imports from two production entry points.

    text2ifc_text.gold is production Python imported by the unchanged package
    initializer, not Gold data. No dataset paths are traversed or copied.
    """
    root = repo / 'src'
    pending, seen = list(SOURCE_ENTRIES), set()
    while pending:
        name = pending.pop()
        if name.split('.')[0] not in SOURCE_PACKAGES:
            if name.startswith('text2ifc'):
                raise ValueError('UNREVIEWED_PRODUCTION_PACKAGE: ' + name)
            continue
        path = root.joinpath(*name.split('.')).with_suffix('.py')
        if not path.is_file():
            path = root.joinpath(*name.split('.'), '__init__.py')
        if not path.is_file() or path in seen:
            continue  # from module import symbol is not necessarily a module
        _checked_file(repo, path)
        seen.add(path)
        package = list(path.relative_to(root).parts[:-1])
        pending.extend('.'.join(package[:i]) for i in range(1, len(package) + 1))
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            if isinstance(node, ast.Import):
                pending.extend(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = package[:len(package) - node.level + 1] if node.level else []
                base = '.'.join(base + (node.module or '').split('.')).strip('.')
                pending.extend([base, *(base + '.' + item.name for item in node.names)])
    return seen


def build_runtime_bundle(repo: Path, destination: Path) -> list[str]:
    """Create a clean, explicit file bundle; never mount the repository itself."""
    repo, destination = Path(repo).resolve(), Path(destination).absolute()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('BUNDLE_DESTINATION_NOT_EMPTY')
    files = _source_closure(repo)
    # Registry validation reads every registered template, including other roles.
    registry = repo / 'prompts/agent/registry.json'
    files.add(registry)
    for row in json.loads(registry.read_text(encoding='utf-8'))['templates']:
        asset = repo / row['path']
        if not asset.is_relative_to(repo / 'prompts/agent'):
            raise ValueError('UNREVIEWED_PROMPT_PATH')
        files.add(asset)
    for directory in ('prompts/agent/ifc-repair-profiles', 'prompts/agent/ifc-repair-few-shots',
                      'schemas/agent', 'schemas/bim-json', 'schemas/ifc'):
        files.update((repo / directory).rglob('*.json'))
    # The frozen generated IFC registry verifies the EXPRESS source identity.
    files.add(repo / 'schemas/ifc/IFC2X3_TC1.exp')
    inventory = []
    for source in sorted(files):
        _checked_file(repo, source)
        relative = source.relative_to(repo)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        inventory.append(relative.as_posix())
    shutil.copyfile(Path(__file__), destination / 'isolated_b.py')
    inventory = sorted([*inventory, 'isolated_b.py'])
    (destination / 'bundle.json').write_text(json.dumps({'files': inventory}, indent=2), encoding='utf-8')
    return inventory


def verify_runtime_bundle(bundle: Path) -> list[str]:
    bundle = Path(bundle).absolute()
    manifest = _checked_file(bundle, bundle / 'bundle.json')
    inventory = json.loads(manifest.read_text(encoding='utf-8'))['files']
    actual = sorted(p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file())
    if actual != sorted([*inventory, 'bundle.json']):
        raise ValueError('BUNDLE_INVENTORY_MISMATCH')
    for relative in inventory:
        _checked_file(bundle, bundle / relative)
        if relative != 'isolated_b.py' and not relative.startswith(('src/', 'schemas/', 'prompts/agent/')):
            raise ValueError('BUNDLE_INVENTORY_FORBIDDEN_PATH')
    return inventory


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,100}', value):
        raise ValueError('INVALID_B_IDENTIFIER')
    return value


def _gateway(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme != 'http' or parsed.hostname not in {'repair-gateway', 'host.docker.internal', '127.0.0.1', 'localhost'}
            or parsed.username or parsed.password or not parsed.port
            or not re.fullmatch(r'/(?:[0-9a-f]{32}/)?v1/?', parsed.path)
            or parsed.query or parsed.fragment):
        raise ValueError('INTERNAL_GATEWAY_REQUIRED')
    return url.rstrip('/')


@dataclass(frozen=True)
class IsolatedBConfig:
    bundle: Path
    workspace: Path
    state_volume: str
    network: str
    base_url: str
    image: str = 'text2ifc/repair-tools:py312-ifc085-v2'
    container_name: str = 'repair-isolated-b'
    model: str = MODEL
    timeout_seconds: float = 1800.0
    evidence_class: str = 'deterministic_fake_http'

    def __post_init__(self):
        for value in (self.state_volume, self.network, self.container_name):
            _identifier(value)
        if self.network in {'host', 'bridge', 'none'}:
            raise ValueError('DEDICATED_INTERNAL_NETWORK_REQUIRED')
        _gateway(self.base_url)
        if self.model != MODEL:
            raise ValueError('FROZEN_B_MODEL_REQUIRED')
        if self.timeout_seconds <= 0:
            raise ValueError('POSITIVE_TIMEOUT_REQUIRED')
        if self.evidence_class not in {'deterministic_fake_http', 'live'}:
            raise ValueError('INVALID_EVIDENCE_CLASS')


class IsolatedB:
    def __init__(self, config: IsolatedBConfig):
        self.config = config

    def prepare_state_volume(self) -> None:
        """Initialize ownership only; never remove or replace retained state."""
        c = self.config
        subprocess.run(['docker', 'volume', 'create', c.state_volume], check=True, capture_output=True, text=True)
        subprocess.run(['docker', 'run', '--rm', '--pull=never', '--network=none', '--read-only', '--cap-drop=ALL',
                        '--security-opt=no-new-privileges', '--memory=256m', '--cpus=1', '--pids-limit=32',
                        '--cap-add=CHOWN', '--user=0:0', '--mount', f'type=volume,source={c.state_volume},target=/state,volume-nocopy',
                        c.image, 'python', '-c', 'import os; os.chown("/state",65532,65532)'],
                       check=True, capture_output=True, text=True)

    def docker_argv(self) -> list[str]:
        c = self.config
        bundle, work = Path(c.bundle).absolute(), Path(c.workspace).absolute()
        verify_runtime_bundle(bundle)
        _checked_file(work, work / 'model.ifc')
        _checked_file(work, work / 'task.txt')
        output = work / 'output'
        output.mkdir(exist_ok=True)
        if output.is_symlink() or (hasattr(output, 'is_junction') and output.is_junction()):
            raise ValueError('OUTPUT_SYMLINK_FORBIDDEN')
        for path in (bundle, work, output):
            if ',' in str(path):
                raise ValueError('DOCKER_MOUNT_PATH_CONTAINS_COMMA')
        return ['docker', 'run', '--rm', '--pull=never', '-i', '--name', c.container_name,
                '--network', c.network, '--add-host=host.docker.internal:host-gateway',
                '--user=65532:65532', '--read-only', '--cap-drop=ALL',
                '--security-opt=no-new-privileges', '--memory=8g', '--cpus=4', '--pids-limit=256',
                '--tmpfs=/tmp:rw,noexec,nosuid,size=512m', '--workdir=/workspace',
                '--env=PYTHONPATH=/runtime/src', '--env=PYTHONDONTWRITEBYTECODE=1', '--env=HOME=/tmp',
                '--mount', f'type=bind,source={bundle},target=/runtime,readonly',
                '--mount', f'type=bind,source={work / "model.ifc"},target=/workspace/model.ifc,readonly',
                '--mount', f'type=bind,source={work / "task.txt"},target=/workspace/task.txt,readonly',
                '--mount', f'type=bind,source={output},target=/workspace/output',
                '--mount', f'type=volume,source={c.state_volume},target=/state,volume-nocopy',
                c.image, 'python', '/runtime/isolated_b.py', 'worker']

    def execute(self, action: str, run_id: str, **answer_binding) -> dict:
        """One native command. A timeout kills this worker, never restarts a run."""
        c = self.config
        info = subprocess.run(['docker', 'network', 'inspect', c.network, '--format', '{{.Internal}}'],
                              capture_output=True, text=True, check=True)
        if info.stdout.strip() != 'true':
            raise ValueError('DOCKER_NETWORK_NOT_INTERNAL')
        payload = {'action': action, 'run_id': _identifier(run_id), 'base_url': c.base_url,
                   'model': c.model, 'timeout_seconds': c.timeout_seconds,
                   'evidence_class': c.evidence_class, **answer_binding}
        try:
            result = subprocess.run(self.docker_argv(), input=json.dumps(payload, ensure_ascii=False),
                                    text=True, encoding='utf-8', capture_output=True, timeout=c.timeout_seconds)
        except subprocess.TimeoutExpired:
            stopped = self.stop()
            return {'ok': False, 'error': 'WORKER_TIMEOUT', 'container_stopped': stopped,
                    'artifact_relative': None, 'evidence_class': c.evidence_class}
        records = [line[len(RESULT_PREFIX):] for line in result.stdout.splitlines() if line.startswith(RESULT_PREFIX)]
        if len(records) != 1:
            return {'ok': False, 'error': 'WORKER_RESULT_MISSING', 'exit_code': result.returncode,
                    'stderr': result.stderr[-8000:], 'artifact_relative': None, 'evidence_class': c.evidence_class}
        value = json.loads(records[0])
        value['exit_code'] = result.returncode
        value['stderr'] = result.stderr[-8000:]
        if result.returncode != 0:
            value.update(ok=False, artifact_relative=None)
        return value

    def start(self, run_id: str) -> dict:
        return self.execute('start', run_id)

    def answer(self, run_id: str, *, answer: dict, clarification_id: str, expected_state_version: int) -> dict:
        return self.execute('answer', run_id, answer=answer, clarification_id=clarification_id,
                            expected_state_version=expected_state_version)

    def read(self, run_id: str) -> dict:
        return self.execute('read', run_id)

    def export_state(self, destination: Path) -> Path:
        """Copy native evidence off its Linux volume without giving it to a model."""
        target = Path(destination).absolute()
        if target.exists() and any(target.iterdir()):
            raise ValueError('STATE_EXPORT_DESTINATION_NOT_EMPTY')
        target.mkdir(parents=True, exist_ok=True)
        c = self.config
        result = subprocess.run(['docker', 'run', '--rm', '--pull=never', '--network=none', '--read-only',
                                 '--user=65532:65532', '--cap-drop=ALL', '--memory=512m', '--cpus=1',
                                 '--mount', f'type=volume,source={c.state_volume},target=/state,readonly,volume-nocopy',
                                 c.image, 'python', '-c',
                                 'import sys,tarfile; t=tarfile.open(fileobj=sys.stdout.buffer,mode="w|"); '
                                 't.add("/state",arcname="state"); t.close()'],
                                capture_output=True, check=True, timeout=120)
        with tarfile.open(fileobj=io.BytesIO(result.stdout), mode='r:') as archive:
            archive.extractall(target, filter='data')
        return target / 'state'

    def stop(self) -> bool:
        name = self.config.container_name
        subprocess.run(['docker', 'kill', name], capture_output=True, text=True, timeout=30)
        state = subprocess.run(['docker', 'ps', '--filter', f'name=^/{name}$', '--format', '{{.Names}}'],
                               capture_output=True, text=True, timeout=30)
        return state.returncode == 0 and not state.stdout.strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def worker_execute(payload: dict, *, workspace=Path('/workspace'), state_root=Path('/state')) -> dict:
    """Worker entry, also exercised locally with a deterministic fake HTTP peer.

    The default production OpenAI client and RepairAPI are never substituted.
    Reads do not initiate inference; interrupted in-flight work is not redispatched.
    """
    from text2ifc_agent.openai_compat import OpenAICompatRuntimeConfig, OpenAICompatibleLiveProvider
    from text2ifc_ifc_repair.api import RepairAPI
    import jsonschema

    action = payload['action']
    if action not in {'start', 'answer', 'read'}:
        raise ValueError('INVALID_WORKER_ACTION')
    run_id = _identifier(payload['run_id'])
    native_id = 'repair-' + uuid.uuid5(uuid.NAMESPACE_URL, run_id).hex
    gateway = _gateway(payload['base_url'])
    if payload.get('model', MODEL) != MODEL:
        raise ValueError('FROZEN_B_MODEL_REQUIRED')
    evidence_class = payload.get('evidence_class', 'deterministic_fake_http')
    if evidence_class not in {'deterministic_fake_http', 'live'}:
        raise ValueError('INVALID_EVIDENCE_CLASS')
    workspace, state_root = Path(workspace).resolve(), Path(state_root).resolve()
    source = _checked_file(workspace, workspace / 'model.ifc')
    request = _checked_file(workspace, workspace / 'task.txt')
    source_hash = _sha(source)
    binding = {'run_id': run_id, 'source_sha256': source_hash, 'request_sha256': _sha(request),
               'model': MODEL, 'evidence_class': evidence_class}
    state_root.mkdir(parents=True, exist_ok=True)
    binding_path = state_root / 'task.json'
    if action == 'start':
        # Exclusive claim precedes every native effect. Uncertain failures require
        # read/diagnosis, never an automatic new run with reset accounting.
        with binding_path.open('x', encoding='utf-8') as handle:
            json.dump(binding, handle)
    elif json.loads(binding_path.read_text(encoding='utf-8')) != binding:
        raise ValueError('B_TASK_BINDING_MISMATCH')
    config = OpenAICompatRuntimeConfig(provider='deepseek', provider_label='DeepSeek',
        api_key=DUMMY_KEY, api_key_env='ISOLATED_DUMMY', base_url=gateway, base_url_env='ISOLATED_GATEWAY',
        model=MODEL, model_env='ISOLATED_MODEL', max_completion_tokens=65536, max_input_tokens=65536,
        timeout_seconds=float(payload.get('timeout_seconds', 1800)))
    provider = OpenAICompatibleLiveProvider(config=config)
    native_root = state_root / 'native'
    api = RepairAPI(native_root, provider=provider)
    try:
        if action == 'start':
            result = api.start(source, request.read_text(encoding='utf-8'), run_id=native_id)
        elif action == 'answer':
            prior = api.read_result(native_id)
            question = prior.to_dict().get('clarification')
            if not question or question['clarification_id'] != payload['clarification_id'] or prior.state_version != payload['expected_state_version']:
                raise ValueError('CLARIFICATION_BINDING_STALE')
            jsonschema.Draft202012Validator(question['answer_schema']).validate(payload['answer'])
            result = api.continue_with_answer(native_id, payload['answer'], clarification_id=payload['clarification_id'],
                                             expected_state_version=payload['expected_state_version'])
        else:
            result = api.read_result(native_id)
        if _sha(source) != source_hash:
            raise ValueError('SOURCE_IFC_CHANGED')
        artifact = None
        if result.successful_artifact_publishable:
            result = api.read_result(native_id)  # validates native publication, never scans IFC candidates
            if not result.successful_artifact_publishable:
                raise ValueError('NATIVE_PUBLICATION_CHANGED')
            published = _checked_file(native_root, native_root / result.run_directory / result.artifacts['successful_ifc'])
            target = workspace / 'output/native-result.ifc'
            target.parent.mkdir(exist_ok=True)
            if target.exists():
                _checked_file(workspace, target)
                if _sha(target) != _sha(published):
                    raise ValueError('EXPORTED_ARTIFACT_CONFLICT')
            else:
                with target.open('xb') as stream:
                    stream.write(published.read_bytes())
            artifact = 'output/native-result.ifc'
        return {'ok': True, 'task_run_id': run_id, 'result': result.to_dict(), 'artifact_relative': artifact,
                'source_unchanged': True, 'native_root': '/state/native', 'evidence_class': evidence_class}
    finally:
        provider.client.close()


def main() -> int:
    if sys.argv[1:] != ['worker']:
        raise SystemExit('usage: isolated_b.py worker < request.json')
    try:
        payload = json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            result = worker_execute(payload)
    except Exception as error:
        result = {'ok': False, 'error': f'{type(error).__name__}: {error}', 'artifact_relative': None}
    print(RESULT_PREFIX + json.dumps(result, ensure_ascii=False))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
