"""One persistent budget across IFC2Text writing and public text2IFC transport.

Reservations survive crashes. SDK retries must be disabled at client construction;
all HTTP attempts pass through BudgetClient. A halt cannot be reset by a new run dir.
"""
from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any


class GoalStopped(RuntimeError):
    pass


class GoalBudget:
    def __init__(self, root, *, writing_calls=None, reconstruction_calls=None, tokens=None,
                 historical_writing_calls=None, historical_tokens=None):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root/'goal-budget.json'
        supplied = {'writing': writing_calls, 'reconstruction': reconstruction_calls, 'tokens': tokens}
        with self._lock():
            if self.path.exists():
                data = self._read()
                for k, value in supplied.items():
                    if value is not None and data['limits'][k] != value:
                        raise GoalStopped('FROZEN_BUDGET_CANNOT_CHANGE')
                for k, value in [('writing', historical_writing_calls), ('tokens', historical_tokens)]:
                    if value is not None and data['historical'][k] != value:
                        raise GoalStopped('HISTORICAL_CONSUMPTION_CANNOT_CHANGE')
            else:
                limits = {'writing': 26 if writing_calls is None else writing_calls,
                          'reconstruction': 12 if reconstruction_calls is None else reconstruction_calls,
                          'tokens': 1_000_000 if tokens is None else tokens}
                if any(type(v) is not int or v <= 0 for v in limits.values()):
                    raise ValueError('BUDGET_LIMIT_MUST_BE_POSITIVE_INTEGER')
                history = {'writing': historical_writing_calls or 0, 'tokens': historical_tokens or 0}
                if any(type(v) is not int or v < 0 for v in history.values()):
                    raise ValueError('INVALID_HISTORICAL_CONSUMPTION')
                self._write({'schema_version': 'text2ifc/ifc2text-goal-budget/0.3',
                             'limits': limits, 'historical': history,
                             'halted': False, 'halt_reason': None, 'attempts': []})

    @contextmanager
    def _lock(self):
        path = self.root/'goal-budget.lock'
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise GoalStopped('CONCURRENT_OR_INTERRUPTED_BUDGET_WRITER') from None
        try:
            yield
        finally:
            os.close(fd)
            path.unlink()

    def _read(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            assert data['schema_version'] == 'text2ifc/ifc2text-goal-budget/0.3'
            assert isinstance(data['attempts'], list) and type(data['halted']) is bool
            for a in data['attempts']:
                assert a['stage'] in ('writing','reconstruction')
                assert type(a['charged_tokens']) is int and a['charged_tokens'] >= 0
                assert a['status'] in ('reserved','completed','failed')
            return data
        except (AssertionError, ValueError, KeyError, TypeError):
            raise GoalStopped('INVALID_BUDGET_LEDGER') from None

    def _write(self, data):
        tmp = self.root/'goal-budget.pending.json'
        with tmp.open('w',encoding='utf-8', newline='\n') as f:
            json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp,self.path)

    def snapshot(self):
        data = self._read()
        return {**data,
                'tokens_used_or_reserved': data['historical']['tokens'] + sum(a['charged_tokens'] for a in data['attempts']),
                'calls': {'writing': data['historical']['writing'] + sum(a['stage']=='writing' for a in data['attempts']),
                          'reconstruction': sum(a['stage']=='reconstruction' for a in data['attempts'])}}

    def check_capacity(self, stage: str, *, calls: int = 1, tokens: int = 0):
        if stage not in ('writing','reconstruction') or type(calls) is not int or calls < 0:
            raise ValueError('INVALID_BUDGET_STAGE_OR_CALL_COUNT')
        data = self.snapshot()
        if data['halted'] or any(a['status']=='reserved' for a in data['attempts']):
            raise GoalStopped('HALTED_OR_UNSETTLED_GOAL_BUDGET')
        if data['calls'][stage]+calls > data['limits'][stage] or data['tokens_used_or_reserved']+tokens > data['limits']['tokens']:
            raise GoalStopped('CUMULATIVE_GOAL_BUDGET_EXCEEDED')

    def reserve(self, stage: str, tokens: int) -> int:
        if type(tokens) is not int or tokens <= 0:
            raise ValueError('INVALID_RESERVATION')
        with self._lock():
            self.check_capacity(stage, tokens=tokens)
            data = self._read()
            n = len(data['attempts'])+1
            data['attempts'].append({'attempt':n,'stage':stage,'status':'reserved',
                                     'charged_tokens':tokens,'reserved_tokens':tokens})
            self._write(data)
            return n

    def settle(self, token: int, *, usage: dict | None = None, failure: str | None = None,
               response_id=None, model=None, elapsed_seconds=0.0):
        with self._lock():
            data = self._read()
            attempt = data['attempts'][token-1]
            if attempt['status'] != 'reserved':
                raise GoalStopped('ATTEMPT_ALREADY_SETTLED')
            usage = usage or {}
            input_tokens = usage.get('prompt_tokens',usage.get('input_tokens'))
            output_tokens = usage.get('completion_tokens',usage.get('output_tokens'))
            known = all(type(v) is int and v >= 0 for v in (input_tokens,output_tokens))
            if known:
                attempt['charged_tokens'] = input_tokens+output_tokens
            else:
                failure = failure or 'USAGE_UNAVAILABLE'
            attempt.update(status='failed' if failure else 'completed', failure=failure,
                           usage_known=known, response_id=response_id, model=model,
                           elapsed_seconds=round(elapsed_seconds,6))
            total = data['historical']['tokens'] + sum(a['charged_tokens'] for a in data['attempts'])
            if failure or total > data['limits']['tokens']:
                data.update(halted=True, halt_reason=failure or 'ACTUAL_TOKEN_LIMIT_EXCEEDED')
            self._write(data)

    def halt(self, reason: str):
        with self._lock():
            data = self._read()
            data.update(halted=True,halt_reason=reason)
            self._write(data)


class BudgetClient:
    """Narrow SDK-compatible transport wrapper; never logs secrets or exception text."""
    def __init__(self, client: Any, budget: GoalBudget, stage: str):
        self.client, self.budget, self.stage = client, budget, stage
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, **request):
        cap = request.get('max_tokens', request.get('max_completion_tokens'))
        if type(cap) is not int or cap <= 0:
            raise GoalStopped('EXPLICIT_OUTPUT_LIMIT_REQUIRED')
        # A UTF-8 byte allowance is conservative for the input token reservation.
        reserve = len(json.dumps(request.get('messages',[]),ensure_ascii=False).encode('utf-8')) + cap
        token = self.budget.reserve(self.stage, reserve)
        started = time.monotonic()
        try:
            response = self.client.chat.completions.create(**request)
        except Exception as error:
            self.budget.settle(token, failure=type(error).__name__, elapsed_seconds=time.monotonic()-started)
            raise
        payload = response if isinstance(response,dict) else response.model_dump()
        choices = payload.get('choices') or []
        finish = choices[0].get('finish_reason') if choices else None
        content = (choices[0].get('message') or {}).get('content') if choices else None
        failure = None if finish == 'stop' and isinstance(content,str) and content.strip() else f'UNUSABLE_RESPONSE_{finish}'
        self.budget.settle(token, usage=payload.get('usage'), failure=failure,
                           response_id=payload.get('id'), model=payload.get('model'),
                           elapsed_seconds=time.monotonic()-started)
        return response
