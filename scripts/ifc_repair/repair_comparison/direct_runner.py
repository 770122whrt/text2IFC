"""A/C common offline execution loop. Only deterministic replay is enabled."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil

from .contracts import PUBLIC_FILES, safe_path, sha256
from .ledger import Ledger, TERMINAL, identifier
from .neutral_tools import NeutralTools, TOOLS


class ReplayProvider:
    def __init__(self, responses):
        self.responses = copy.deepcopy(responses)

    def complete(self, index, *, messages, tools):
        if index >= len(self.responses):
            raise ValueError('REPLAY_EXHAUSTED')
        return copy.deepcopy(self.responses[index])


class DirectRunner:
    def __init__(self, root: Path, run_id):
        self.root = safe_path(Path(root))
        self.run_id = identifier(run_id)
        self.ledger = Ledger(self.root / 'control.sqlite')
        state = self.ledger.snapshot(run_id)
        self.workspace = safe_path(Path(state['metadata']['workspace']))
        self.tools = NeutralTools(self.workspace, tool_seconds=state['limits']['tool_seconds'])

    @classmethod
    def create(cls, public: Path, root: Path, *, case_id, arm, budget, mode='offline_development', runtime_metadata=None):
        if arm not in {'A', 'C', 'B', 'D'}:
            raise ValueError('ARM_NOT_IMPLEMENTED')
        identifier(case_id)
        public, root = safe_path(Path(public)), safe_path(Path(root))
        if set(p.name for p in public.iterdir()) != PUBLIC_FILES:
            raise ValueError('PUBLIC_FILE_ALLOWLIST_MISMATCH')
        for name in PUBLIC_FILES:
            safe_path(public / name)
        run_id = f'{case_id}-{arm}'
        workspace = safe_path(root / 'workspaces' / run_id)
        if workspace.exists():
            raise ValueError('WORKSPACE_ALREADY_EXISTS_USE_RESUME')
        inputs = root / 'inputs' / case_id
        if inputs.exists():
            if any((inputs / name).read_bytes() != (public / name).read_bytes() for name in PUBLIC_FILES):
                raise ValueError('UNEQUAL_PUBLIC_INPUTS')
        else:
            inputs.mkdir(parents=True)
            for name in PUBLIC_FILES:
                shutil.copyfile(public / name, inputs / name)
        ledger = Ledger(root / 'control.sqlite')
        ledger.create(run_id, case_id=case_id, arm=arm, budget=budget, mode=mode,
                      metadata={'workspace': str(workspace), 'input_dir': str(inputs), 'input_sha256': sha256(inputs / 'model.ifc'),
                                'runtime_isolation_verified': False, 'network_transport_attempted': False, 'runtime': runtime_metadata or {}})
        workspace.mkdir(parents=True)
        for folder in ('work', 'output'):
            (workspace / folder).mkdir()
        shutil.copyfile(inputs / 'model.ifc', workspace / 'model.ifc')
        request = (inputs / 'request.txt').read_text(encoding='utf-8').strip()
        (workspace / 'task.txt').write_text(request + '\n', encoding='utf-8')
        ledger.record(run_id, 'initial_message', {'role': 'user', 'content': f'请按以下要求操作这个 IFC 文件：\n\n{request}\n\nIFC 文件：model.ifc'})
        return cls(root, run_id)

    def submit(self, relative):
        state = self.ledger.snapshot(self.run_id)
        if state['status'] in TERMINAL:
            raise ValueError('TERMINAL_IMMUTABLE')
        if state['status'] != 'running':
            raise ValueError('RUN_NOT_ACTIVE')
        if state['active_elapsed_s'] >= state['limits']['active_seconds'] or state['usage']['token_overrun']:
            return self.ledger.finish(self.run_id, 'budget_exhausted')
        source = self.tools.path(relative)
        if source.suffix.lower() != '.ifc' or not source.is_file():
            raise ValueError('EXPLICIT_IFC_FILE_REQUIRED')
        metadata = state['metadata']
        if sha256(Path(metadata['input_dir']) / 'model.ifc') != metadata['input_sha256']:
            raise ValueError('FROZEN_INPUT_CHANGED')
        target = safe_path(self.root / 'artifacts' / self.run_id / 'result.ifc')
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation: an interrupted/previous publication is never overwritten.
        if target.exists():
            if sha256(target) != sha256(source):
                raise ValueError('ARTIFACT_ALREADY_FROZEN')
        else:
            with target.open('xb') as handle:
                handle.write(source.read_bytes())
        artifact = {'path': str(target), 'sha256': sha256(target), 'submitted_path': relative}
        return self.ledger.finish(self.run_id, 'submitted', artifact=artifact)

    def messages(self):
        messages = []
        calls = {row['request_id']: row for row in self.ledger.calls(self.run_id)}
        for event in self.ledger.events(self.run_id):
            kind, payload = event['kind'], event['payload']
            if kind == 'initial_message':
                messages.append(payload)
            elif kind == 'request_settled':
                response = calls[payload['request_id']]['response']
                if isinstance(response, dict):
                    messages.append({'role': 'assistant', **{k: response[k] for k in ('content', 'tool_calls', 'reasoning', 'reasoning_content') if k in response}})
            elif kind == 'tool_result':
                messages.append({'role': 'tool', 'tool_call_id': payload['call_id'], 'content': json.dumps(payload['result'], ensure_ascii=False)})
            elif kind == 'answer':
                messages.append({'role': 'user', 'content': payload['text']})
        return messages

    def _apply_pending(self):
        events = self.ledger.events(self.run_id)
        done = {e['payload']['call_id'] for e in events if e['kind'] == 'tool_result'}
        started = {e['payload']['call_id'] for e in events if e['kind'] == 'tool_started'}
        questions = {e['payload']['question_id'] for e in events if e['kind'] == 'question'}
        for call in self.ledger.calls(self.run_id):
            response = call['response']
            if not isinstance(response, dict) or not isinstance(response.get('tool_calls', []), list):
                continue
            for index, tool in enumerate(response.get('tool_calls', [])):
                call_id = f"{call['request_id']}-tool-{index}"
                if call_id in done:
                    continue
                if call_id in questions:
                    # Asking and recording the visible tool result may straddle a crash.
                    # The durable question is authoritative and must never be asked twice.
                    self.ledger.record(self.run_id, 'tool_result', {'call_id': call_id, 'result': {'status': 'awaiting_user'}}, event_id='result:' + call_id)
                    continue
                if call_id in started:
                    raise ValueError('TOOL_RECOVERY_REQUIRED_NO_AUTOMATIC_REEXECUTION')
                state = self.ledger.snapshot(self.run_id)
                remaining = state['limits']['active_seconds'] - state['active_elapsed_s']
                if remaining <= 0 or state['usage']['token_overrun']:
                    self.ledger.finish(self.run_id, 'budget_exhausted')
                    return
                self.tools.tool_seconds = min(state['limits']['tool_seconds'], remaining)
                claimed = self.ledger.record(self.run_id, 'tool_started', {'call_id': call_id, 'tool': tool}, event_id='start:' + call_id)
                if not claimed:
                    raise ValueError('TOOL_RECOVERY_REQUIRED_ALREADY_CLAIMED')
                try:
                    name, arguments = tool['name'], tool['arguments']
                    if name == 'ask_user':
                        self.ledger.ask(self.run_id, question_id=call_id, text=arguments['question'])
                        self.ledger.record(self.run_id, 'tool_result', {'call_id': call_id, 'result': {'status': 'awaiting_user'}}, event_id='result:' + call_id)
                        return
                    if name == 'submit':
                        result = self.submit(arguments['path'])
                        self.ledger.record(self.run_id, 'tool_result', {'call_id': call_id, 'result': {'status': result['status']}}, event_id='result:' + call_id)
                        return
                    if name not in {'read_file', 'write_file', 'replace_text', 'list_files', 'execute'}:
                        raise ValueError('UNKNOWN_TOOL')
                    self.ledger.activity(self.run_id, call_id, begin=True)
                    result = getattr(self.tools, name)(**arguments)
                    if name == 'execute' and not result['quiescent']:
                        raise RuntimeError('PROCESS_STOP_NOT_CONFIRMED')
                    self.ledger.activity(self.run_id, call_id, begin=False)
                except (KeyError, TypeError, ValueError, OSError) as error:
                    state = self.ledger.snapshot(self.run_id)
                    if call_id in state['activities']:
                        self.ledger.activity(self.run_id, call_id, begin=False)
                    result = {'error': type(error).__name__, 'detail': str(error)}
                self.ledger.record(self.run_id, 'tool_result', {'call_id': call_id, 'result': result}, event_id='result:' + call_id)

    def run(self, provider: ReplayProvider, *, reservation):
        if not isinstance(provider, ReplayProvider):
            raise ValueError('OFFLINE_REPLAY_ONLY')
        state = self.ledger.snapshot(self.run_id)
        if state['arm'] not in {'A', 'C'}:
            raise ValueError('DIRECT_RUNNER_REQUIRES_A_OR_C')
        if state['status'] == 'ready':
            self.ledger.start(self.run_id)
        while True:
            state = self.ledger.snapshot(self.run_id)
            if state['status'] != 'running':
                return state
            if state['activities'] or any(c['state'] == 'inflight' for c in self.ledger.calls(self.run_id)):
                raise ValueError('RECOVERY_REQUIRED_NO_AUTOMATIC_REDISPATCH')
            self._apply_pending()
            state = self.ledger.snapshot(self.run_id)
            if state['status'] != 'running':
                return state
            calls = self.ledger.calls(self.run_id)
            if calls:
                previous = calls[-1]['response']
                if isinstance(previous, dict) and isinstance(previous.get('tool_calls', []), list) and not previous.get('tool_calls') and not calls[-1]['failed']:
                    return self.ledger.finish(self.run_id, 'no_output')
            request_id = f'request-{len(calls)}'
            try:
                self.ledger.reserve(self.run_id, request_id, reservation, metadata={'stage': 'root', 'evidence_class': 'deterministic_replay', 'reasoning_status': 'only_returned_fields'})
            except ValueError as error:
                if 'BUDGET' not in str(error):
                    raise
                return self.ledger.finish(self.run_id, 'budget_exhausted', detail=str(error))
            try:
                result = provider.complete(len(calls), messages=self.messages(), tools=TOOLS)
                malformed = not isinstance(result, dict) or not isinstance(result.get('tool_calls', []), list)
                self.ledger.settle(self.run_id, request_id, usage=result.get('usage') if isinstance(result, dict) else None,
                                   response=result, failed=malformed)
            except Exception as error:
                self.ledger.settle(self.run_id, request_id, usage=None, response={'error': type(error).__name__, 'detail': str(error)}, failed=True)
                return self.ledger.finish(self.run_id, 'runtime_error', detail=str(error))
