"""Persistent admission budget shared by a Generation session's model stages."""
from __future__ import annotations

import json
import hashlib
import math
import os
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path

from .openai_compat import OpenAICompatError


class GenerationBudgetExceeded(OpenAICompatError):
    def __init__(self, reason):
        super().__init__(reason, evidence={'failure_class':'generation_task_budget',
                                          'transport_attempted':False})


@dataclass(frozen=True)
class BudgetLimits:
    max_calls: int = 32
    max_tokens: int = 2_000_000
    max_active_seconds: float = 3600

    def __post_init__(self):
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0
               for v in asdict(self).values()):
            raise ValueError('Generation budget limits must be positive finite values')
        if not isinstance(self.max_calls, int) or not isinstance(self.max_tokens, int):
            raise ValueError('Call and token limits must be integers')


class GenerationBudget:
    def __init__(self, root, limits=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root/'generation-budget.json'
        with self._locked():
            if self.path.exists():
                data = self._read()
                if limits is not None and data['limits'] != asdict(limits):
                    raise GenerationBudgetExceeded('Resuming cannot change the frozen task budget')
            else:
                frozen = limits or BudgetLimits()
                self._write({'schema_version':'text2ifc/generation-budget/1.0',
                             'limits':asdict(frozen), 'attempts':self._historical_attempts(frozen)})

    def _historical_attempts(self, limits):
        # Import recorded consumption once. Duplicate archive copies count
        # conservatively; do not infer that similar responses were one call.
        responses = list(self.root.rglob('response.raw.json'))
        sources = responses + [p for p in self.root.rglob('request.redacted.json')
                               if not (p.parent/'response.raw.json').exists()]
        attempts = []
        for path in sorted(sources):
            raw = path.read_bytes()
            try:
                payload = json.loads(raw)
                usage = payload.get('usage', {}) if path.name == 'response.raw.json' else {}
            except (ValueError, AttributeError):
                raise GenerationBudgetExceeded('Unreadable historical Provider evidence') from None
            tokens = _usage_tokens(usage)
            attempts.append({'attempt':len(attempts)+1, 'stage':'historical',
                'status':'imported', 'source':path.relative_to(self.root).as_posix(),
                'source_sha256':hashlib.sha256(raw).hexdigest(),
                'reserved_tokens':limits.max_tokens, 'tokens_charged':tokens if tokens is not None else limits.max_tokens,
                'elapsed_seconds':0, 'active_time_unknown':True})
        return attempts

    @contextmanager
    def _locked(self):
        lock = self.root/'generation-budget.lock'
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise GenerationBudgetExceeded('Concurrent or interrupted budget writer requires inspection') from None
        try:
            yield
        finally:
            os.close(fd)
            lock.unlink()

    def _read(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            if data['schema_version'] != 'text2ifc/generation-budget/1.0':
                raise ValueError('version')
            BudgetLimits(**data['limits'])
            if not isinstance(data['attempts'], list):
                raise ValueError('attempts')
            for attempt in data['attempts']:
                if (not isinstance(attempt['tokens_charged'], int) or isinstance(attempt['tokens_charged'], bool)
                    or attempt['tokens_charged'] < 0 or not isinstance(attempt['elapsed_seconds'], (int, float))
                    or not math.isfinite(attempt['elapsed_seconds']) or attempt['elapsed_seconds'] < 0
                    or attempt['status'] not in {'reserved','completed','failed','imported'}):
                    raise ValueError('invalid usage')
            return data
        except (ValueError, TypeError, KeyError):
            raise GenerationBudgetExceeded('Invalid persisted generation budget') from None

    def _write(self, data):
        temporary = self.root/'generation-budget.pending.json'
        with temporary.open('w', encoding='utf-8', newline='\n') as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, self.path)

    def snapshot(self):
        data = self._read()
        return {**data, 'calls_used':len(data['attempts']),
                'tokens_used_or_reserved':sum(a['tokens_charged'] for a in data['attempts']),
                'active_seconds':sum(a['elapsed_seconds'] for a in data['attempts'])}

    def reserve(self, *, stage, reserved_tokens):
        if not isinstance(reserved_tokens, int) or reserved_tokens <= 0:
            raise ValueError('A positive token reservation is required')
        with self._locked():
            data = self.snapshot()
            limits = data['limits']
            if (data['calls_used'] >= limits['max_calls']
                or data['tokens_used_or_reserved'] + reserved_tokens > limits['max_tokens']
                or data['active_seconds'] >= limits['max_active_seconds']):
                raise GenerationBudgetExceeded('Generation task call/token/active-time budget exhausted')
            token = len(data['attempts']) + 1
            data['attempts'].append({'attempt':token, 'stage':stage, 'status':'reserved',
                'tokens_charged':reserved_tokens, 'reserved_tokens':reserved_tokens,
                'elapsed_seconds':0})
            self._write({k:data[k] for k in ('schema_version','limits','attempts')})
            return token

    def assert_publishable(self):
        data = self.snapshot()
        if (data['tokens_used_or_reserved'] > data['limits']['max_tokens']
            or data['active_seconds'] > data['limits']['max_active_seconds']
            or any(a['status'] == 'reserved' for a in data['attempts'])):
            raise GenerationBudgetExceeded('Unsettled or exceeded task budget blocks publication')

    def settle(self, token, *, usage=None, elapsed_seconds=0, failed=False):
        with self._locked():
            data = self._read()
            attempt = data['attempts'][token-1]
            if attempt['status'] != 'reserved':
                raise GenerationBudgetExceeded('Budget attempt has already been settled')
            usage = usage or {}
            tokens = _usage_tokens(usage)
            if tokens is not None:
                attempt['tokens_charged'] = tokens
            attempt.update(status='failed' if failed else 'completed',
                           elapsed_seconds=max(0, elapsed_seconds))
            self._write(data)


class BudgetedProvider:
    def __init__(self, provider, budget, max_output_tokens=None):
        self.provider, self.budget = provider, budget
        config = getattr(provider, 'config', None)
        self.max_output_tokens = max_output_tokens or getattr(config, 'max_completion_tokens', 131072)

    def __getattr__(self, name):
        return getattr(self.provider, name)

    def generate_live(self, **kwargs):
        # UTF-8 bytes are a conservative input allowance; keep the Provider's
        # output cap unchanged, never spend beyond admission by lowering it.
        reserved = len(kwargs['prompt'].encode('utf-8')) + self.max_output_tokens
        token = self.budget.reserve(stage=kwargs.get('state', {}).get('stage', 'model'),
                                    reserved_tokens=reserved)
        started = time.monotonic()
        try:
            result = self.provider.generate_live(**kwargs)
        except Exception:
            self.budget.settle(token, elapsed_seconds=time.monotonic()-started, failed=True)
            raise
        self.budget.settle(token, usage=result.response.get('usage', {}),
                           elapsed_seconds=time.monotonic()-started)
        return result


def _usage_tokens(usage):
    if not isinstance(usage, dict):
        return None
    values = (usage.get('input_tokens', usage.get('prompt_tokens')),
              usage.get('output_tokens', usage.get('completion_tokens')))
    if all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in values):
        return sum(values)
    return None
