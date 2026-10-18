"""Pure metadata/control tests; no fresh IFC/native claims."""
import importlib
from pathlib import Path

import pytest

from scripts.ifc_repair import dataset_pairs as q
from scripts.ifc_repair.dataset_batch import engine


def api():
    return importlib.import_module('scripts.ifc_repair.dataset_property_tail')


def prop(name):
    return {'guid':'metadata-door','ifc_class':'IfcDoor','pset_name':'Fixture',
            'property_name':name,'value_type':'IfcLabel','before':name,'after':name+' [damage-00]'}


def test_only_property_recipes_skip_all_previously_tried_keys_and_duplicates():
    module=api()
    recipes=[{'family':'door','deletions':[{'guid':'deleted'}],'property_changes':[]},
             *[{'family':'attributes','deletions':[],'property_changes':[prop(n)]} for n in ('accepted','failed','new','new')]]
    skipped={q.recipe_key(r) for r in recipes[1:3]}
    actual=list(module.property_recipes({},skipped,original=lambda *a,**k:iter(recipes)))
    assert actual==[recipes[3]]


@pytest.mark.parametrize('baseline,expected',[(28,2),(30,0),(20,10)])
def test_tail_target_is_actual_deficit_with_a_separate_budget(baseline,expected):
    assert api().plan_target(baseline,max_attempts=30)=={'baseline_pairs':baseline,
        'target_added_pairs':expected,'per_mother_cap':30,'max_attempts':30}


def test_adapter_keeps_original_guarded_checks_and_restores_all_globals(monkeypatch,tmp_path):
    module=api()
    original=q._configuration,q.iter_raw_recipes,q.make_pair_records,engine.guard_geometry
    monkeypatch.setattr(module,'program_bindings',lambda:{'fixture':'explicit metadata binding'})
    binding={'round':module.ROUND,'source_id':'formal-041'}
    with module.tail_adapter(binding,set(),set()):
        config=q._configuration({'source_id':'formal-041','source_sha256':'a'*64},
            pairs_per_ifc=2,max_attempts=30,seed=20261010)
        assert config['property_tail']==binding and config['code_sha256']==module.program_bindings()
        assert engine.guard_geometry is module.guard_geometry
    assert (q._configuration,q.iter_raw_recipes,q.make_pair_records,engine.guard_geometry)==original


def test_adapter_rejects_damage_bytes_seen_in_any_prior_round(monkeypatch,tmp_path):
    module=api()
    monkeypatch.setattr(q,'_check_damage',lambda *a,**k:({'damaged_sha256':'old'},None,None,None))
    with module.tail_adapter({},set(),{'old'}):
        with pytest.raises(ValueError,match='DUPLICATE_DAMAGE_OF_PREVIOUS_ROUNDS'):
            q._check_damage(None,None,None,None,None,tmp_path)


def test_tail_summary_distinguishes_prior_pairs_from_new_attempts():
    module=api()
    build={'baseline_pairs':28,'target_added_pairs':2,'source':{'source_id':'formal-041'},'max_attempts':30}
    row={'pairs':[{},{}],'cases':[{}],'attempts':[{'status':'failed'},{'status':'passed'}],
         'stop_reason':'pair_quota_met','candidate_rejection_count':0,'status':'complete'}
    summary=module.summary_record(build,row)
    assert summary['status']=='finished' and summary['total_pairs']==30
    assert summary['added_pairs']==2 and summary['new_damages']==1
    assert summary['attempted_cases']==2 and summary['failed_attempts']==1
    assert summary['worker_errors']==[]


def test_new_collector_rejects_a_root_that_was_not_loaded(tmp_path):
    module=importlib.import_module('scripts.ifc_repair.dataset_deliver_v3')
    with pytest.raises(ValueError,match='CODE_ROOT_NOT_ACTUALLY_LOADED'):
        module._environment(q.ROOT,tmp_path)
