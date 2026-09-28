"""Preserve usage across call allocation and explicit human token extensions."""
import hashlib
import json
from pathlib import Path

from text2ifc_ifc2text.goal_budget import GoalBudget,GoalStopped


def _digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def allocate(previous,root,*,additional_call_slots,additional_tokens=0,authorization=None):
    if type(additional_call_slots) is not int or additional_call_slots<=0:
        raise ValueError('POSITIVE_CALL_SLOTS_REQUIRED')
    if (type(additional_tokens) is not int or additional_tokens<0
            or (additional_tokens and (not isinstance(authorization,str) or not authorization.strip()))):
        raise ValueError('TOKEN_EXTENSION_REQUIRES_EXPLICIT_AUTHORIZATION')
    snapshot=previous.snapshot()
    if snapshot['halted'] or any(a['status']=='reserved' for a in snapshot['attempts']):
        raise GoalStopped('PREDECESSOR_HALTED_OR_UNSETTLED')
    path=Path(root);path.mkdir(parents=True,exist_ok=False)
    record={'schema_version':'text2ifc/component-budget-allocation/1.0',
        'predecessor_path':str(previous.path.resolve()),'predecessor_sha256':_digest(previous.path),
        'predecessor_snapshot':snapshot,'additional_call_slots':additional_call_slots,
        'token_ceiling':snapshot['limits']['tokens'],
        'reason':'Call slots for the authorized component development and remaining loops; no new token allowance. All previous usage and failures remain charged.'}
    if additional_tokens:
        record.update(schema_version='text2ifc/component-budget-allocation/1.1',
            additional_tokens=additional_tokens,authorization=authorization,
            token_ceiling=snapshot['limits']['tokens']+additional_tokens,
            reason='Explicit human token extension; predecessor usage, failures and call counts remain charged.')
    manifest=path/'allocation.json'
    manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest


class ComponentBudget(GoalBudget):
    def __init__(self,manifest):
        self.manifest=Path(manifest)
        self.authority=json.loads(self.manifest.read_text(encoding='utf-8'))
        a=self.authority;p=a['predecessor_snapshot']
        extra=a.get('additional_tokens',0)
        if (a['schema_version'] not in {'text2ifc/component-budget-allocation/1.0','text2ifc/component-budget-allocation/1.1'}
                or type(extra) is not int or extra<0
                or (a['schema_version'].endswith('/1.0') and extra!=0)
                or (a['schema_version'].endswith('/1.1') and (extra<=0 or not isinstance(a.get('authorization'),str) or not a['authorization'].strip()))
                or a['token_ceiling']!=p['limits']['tokens']+extra):
            raise GoalStopped('INVALID_COMPONENT_BUDGET_ALLOCATION')
        if p['halted'] or any(x['status']=='reserved' for x in p['attempts']):
            raise GoalStopped('PREDECESSOR_HALTED_OR_UNSETTLED')
        self._check_predecessor()
        self.inherited_reconstruction=p['calls']['reconstruction']
        super().__init__(self.manifest.parent/'budget',writing_calls=p['limits']['writing'],
            reconstruction_calls=self.inherited_reconstruction+a['additional_call_slots'],
            tokens=a['token_ceiling'],historical_writing_calls=p['calls']['writing'],
            historical_tokens=p['tokens_used_or_reserved'])

    def _check_predecessor(self):
        if _digest(self.authority['predecessor_path'])!=self.authority['predecessor_sha256']:
            raise GoalStopped('PREDECESSOR_CHANGED')

    def snapshot(self):
        self._check_predecessor()
        result=super().snapshot()
        result['calls']['reconstruction']+=self.inherited_reconstruction
        return result


def open_allocation(manifest):return ComponentBudget(manifest)


def resume_settled_truncation(budget, response_path, *, rationale):
    """Explicit diagnostic recovery, never an automatic transport retry.

    One settled truncation may be resumed in this ledger. Unknown usage, other
    failures, unsettled calls and exhausted limits remain blocking. The receipt
    freezes the prior state; all failed attempts and limits remain unchanged.
    """
    if not isinstance(rationale, str) or not rationale.strip():
        raise GoalStopped('TRUNCATION_RECOVERY_REASON_REQUIRED')
    response_path = Path(response_path)
    response = json.loads(response_path.read_text(encoding='utf-8'))
    with budget._lock():
        before = budget.snapshot(); data = budget._read()
        failures = [a for a in data['attempts'] if a['status'] == 'failed']
        if (not data['halted'] or data['halt_reason'] != 'UNUSABLE_RESPONSE_length'
                or len(failures) != 1 or failures[0] != data['attempts'][-1]
                or any(a['status'] == 'reserved' for a in data['attempts'])
                or not failures[0].get('usage_known')):
            raise GoalStopped('TRUNCATION_RECOVERY_NOT_APPLICABLE')
        attempt = failures[0]; usage = response.get('usage', {})
        values = [usage.get('prompt_tokens'), usage.get('completion_tokens')]
        if (attempt.get('failure') != 'UNUSABLE_RESPONSE_length'
                or response.get('id') != attempt.get('response_id')
                or len(response.get('choices', [])) != 1
                or response['choices'][0].get('finish_reason') != 'length'
                or any(type(v) is not int or v < 0 for v in values)
                or sum(values) != attempt['charged_tokens']):
            raise GoalStopped('TRUNCATION_RESPONSE_MISMATCH')
        if (before['tokens_used_or_reserved'] >= before['limits']['tokens']
                or before['calls'][attempt['stage']] >= before['limits'][attempt['stage']]):
            raise GoalStopped('CUMULATIVE_GOAL_BUDGET_EXCEEDED')
        record = {'schema_version': 'text2ifc/settled-truncation-recovery/1.0',
            'action': 'resume_settled_truncation', 'before_snapshot': before,
            'before_ledger_sha256': _digest(budget.path),
            'response_path': str(response_path.resolve()), 'response_sha256': _digest(response_path),
            'rationale': rationale, 'limits_and_attempts_unchanged': True}
        receipt = budget.root / 'settled-truncation-recovery.json'
        if receipt.exists():
            # A crash after writing the receipt but before the ledger update may
            # finish the same transition; a different prior state cannot reuse it.
            if json.loads(receipt.read_text(encoding='utf-8')) != record:
                raise GoalStopped('TRUNCATION_RECOVERY_RECEIPT_CONFLICT')
        else:
            with receipt.open('x', encoding='utf-8') as stream:
                json.dump(record, stream, ensure_ascii=False, indent=2)
        data.update(halted=False, halt_reason=None)
        budget._write(data)
    return receipt
