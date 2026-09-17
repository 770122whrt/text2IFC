"""Explicitly authorized budget amendment linked to a preserved predecessor ledger."""
from __future__ import annotations
import json
from pathlib import Path
from .goal_budget import GoalBudget, GoalStopped
from .llm_pipeline import _write_json


class CampaignBudget(GoalBudget):
    def __init__(self, root, *, predecessor, tokens=2_000_000, writing_calls=26, reconstruction_calls=12):
        self.predecessor=Path(predecessor)
        previous=json.loads(self.predecessor.read_text(encoding='utf-8'))
        if any(a['status']=='reserved' for a in previous['attempts']):
            raise GoalStopped('PREDECESSOR_UNSETTLED')
        writing=previous['historical']['writing']+sum(a['stage']=='writing' for a in previous['attempts'])
        consumed=previous['historical']['tokens']+sum(a['charged_tokens'] for a in previous['attempts'])
        self.historical_reconstruction=sum(a['stage']=='reconstruction' for a in previous['attempts'])
        authority={'schema_version':'text2ifc/budget-amendment/0.4',
            'reason':'2026-09-17 explicit authorization: three buildings, one Compare, total 2000000 tokens, Brief 64K or 128K',
            'predecessor':str(self.predecessor),'predecessor_ledger':previous,
            'imported_writing_calls':writing,'imported_reconstruction_calls':self.historical_reconstruction,
            'imported_tokens':consumed,'new_limits':{'tokens':tokens,'writing':writing_calls,'reconstruction':reconstruction_calls}}
        p=Path(root)/'budget-amendment.json'
        if p.exists():
            if json.loads(p.read_text(encoding='utf-8'))!=authority: raise GoalStopped('AMENDMENT_CHANGED')
        else: _write_json(p,authority)
        super().__init__(root,writing_calls=writing_calls,reconstruction_calls=reconstruction_calls,
                         tokens=tokens,historical_writing_calls=writing,historical_tokens=consumed)

    def snapshot(self):
        result=super().snapshot()
        result['calls']['reconstruction']+=self.historical_reconstruction
        result['historical_reconstruction_calls']=self.historical_reconstruction
        return result
