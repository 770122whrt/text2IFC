"""Administrative call-slot allocation under the unchanged human token ceiling."""
import hashlib
import json
from pathlib import Path

from text2ifc_ifc2text.goal_budget import GoalBudget,GoalStopped


def _digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def allocate(previous,root,*,additional_call_slots):
    if type(additional_call_slots) is not int or additional_call_slots<=0:
        raise ValueError('POSITIVE_CALL_SLOTS_REQUIRED')
    snapshot=previous.snapshot()
    if snapshot['halted'] or any(a['status']=='reserved' for a in snapshot['attempts']):
        raise GoalStopped('PREDECESSOR_HALTED_OR_UNSETTLED')
    path=Path(root);path.mkdir(parents=True,exist_ok=False)
    record={'schema_version':'text2ifc/component-budget-allocation/1.0',
        'predecessor_path':str(previous.path.resolve()),'predecessor_sha256':_digest(previous.path),
        'predecessor_snapshot':snapshot,'additional_call_slots':additional_call_slots,
        'token_ceiling':snapshot['limits']['tokens'],
        'reason':'Call slots for the authorized component development and remaining loops; no new token allowance. All previous usage and failures remain charged.'}
    manifest=path/'allocation.json'
    manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest


class ComponentBudget(GoalBudget):
    def __init__(self,manifest):
        self.manifest=Path(manifest)
        self.authority=json.loads(self.manifest.read_text(encoding='utf-8'))
        a=self.authority;p=a['predecessor_snapshot']
        if a['schema_version']!='text2ifc/component-budget-allocation/1.0' or a['token_ceiling']!=p['limits']['tokens']:
            raise GoalStopped('INVALID_COMPONENT_BUDGET_ALLOCATION')
        if p['halted'] or any(x['status']=='reserved' for x in p['attempts']):
            raise GoalStopped('PREDECESSOR_HALTED_OR_UNSETTLED')
        self._check_predecessor()
        self.inherited_reconstruction=p['calls']['reconstruction']
        super().__init__(self.manifest.parent/'budget',writing_calls=p['limits']['writing'],
            reconstruction_calls=self.inherited_reconstruction+a['additional_call_slots'],
            tokens=p['limits']['tokens'],historical_writing_calls=p['calls']['writing'],
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
