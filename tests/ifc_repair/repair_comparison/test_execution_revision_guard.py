"""Common B fix cannot authorize drift in another method or experiment contract."""
from copy import deepcopy

import pytest

from scripts.ifc_repair.repair_comparison.formal_admission import (
    execution_revision_changes, validate_process_native_row,
)


def binding():
    return {'images':{'B':'fixed-image'},'scene_grounding_version':'fixed',
            'files':{'src/text2ifc_ifc_repair/scene_context.py':'old',
                     'src/text2ifc_ifc_repair/api.py':'old-api',
                     'src/text2ifc_ifc_repair/evaluation.py':'old-evaluation',
                     'scripts/ifc_repair/repair_comparison/formal_admission.py':'old-guard',
                     'scripts/ifc_repair/repair_comparison/direct_runner.py':'AC-fixed'}}


def test_common_b_source_change_is_explicit():
    old=binding();new=deepcopy(old);new['files']['src/text2ifc_ifc_repair/scene_context.py']='candidate'
    assert execution_revision_changes(old,new)=={'src/text2ifc_ifc_repair/scene_context.py':{'before':'old','after':'candidate'}}


@pytest.mark.parametrize('drift',['other_lane','image','new_file','no_change'])
def test_unrelated_revision_is_rejected(drift):
    old=binding();new=deepcopy(old)
    if drift=='other_lane':new['files']['scripts/ifc_repair/repair_comparison/direct_runner.py']='edited'
    elif drift=='image':new['images']['B']='unapproved'
    elif drift=='new_file':new['files']['unapproved.py']='new'
    with pytest.raises(ValueError,match='EXECUTION_REVISION'):
        execution_revision_changes(old,new)


def test_parameter_fix_has_its_own_explicit_scope():
    old=binding();new=deepcopy(old);new['files']['src/text2ifc_ifc_repair/api.py']='fixed'
    assert set(execution_revision_changes(old,new,common_scope='parameter_clarification'))=={'src/text2ifc_ifc_repair/api.py'}
    with pytest.raises(ValueError,match='EXECUTION_REVISION_OUTSIDE_COMMON_SCOPE'):
        execution_revision_changes(old,new)
    new['files']['src/text2ifc_ifc_repair/scene_context.py']='unexpected'
    with pytest.raises(ValueError,match='EXECUTION_REVISION_OUTSIDE_COMMON_SCOPE'):
        execution_revision_changes(old,new,common_scope='parameter_clarification')


def test_unknown_common_scope_is_rejected():
    with pytest.raises(ValueError,match='EXECUTION_REVISION_SCOPE_UNKNOWN'):
        execution_revision_changes(binding(),binding(),common_scope='anything')


def test_validation_process_fix_has_its_own_explicit_scope():
    old=binding();new=deepcopy(old)
    new['files']['src/text2ifc_ifc_repair/evaluation.py']='spawn-isolated'
    assert set(execution_revision_changes(old,new,common_scope='validation_process'))=={
        'src/text2ifc_ifc_repair/evaluation.py'}
    with pytest.raises(ValueError,match='EXECUTION_REVISION_OUTSIDE_COMMON_SCOPE'):
        execution_revision_changes(old,new,common_scope='parameter_clarification')
    new['files']['src/text2ifc_ifc_repair/api.py']='unexpected'
    with pytest.raises(ValueError,match='EXECUTION_REVISION_OUTSIDE_COMMON_SCOPE'):
        execution_revision_changes(old,new,common_scope='validation_process')


@pytest.mark.parametrize('drift',[
    None, 'reused_models', 'sequential', 'larger_rss_limit', 'rss_over',
    'deadline_over', 'more_workers', 'validation_failed',
])
def test_process_native_revision_preserves_resource_and_mode_contract(drift):
    row={'validation_status':'passed','baseline_model_reused':False,
         'candidate_model_reused':False,'validation_metrics':{
             'mode':'accelerated','worker_count':2,'rss_limit_bytes':4*1024**3,
             'peak_rss_bytes':3*1024**3,'wall_seconds':6}}
    metrics=row['validation_metrics']
    if drift=='reused_models':row['candidate_model_reused']=True
    elif drift=='sequential':metrics['mode']='sequential'
    elif drift=='larger_rss_limit':metrics['rss_limit_bytes']=8*1024**3
    elif drift=='rss_over':metrics['peak_rss_bytes']=4*1024**3+1
    elif drift=='deadline_over':metrics['wall_seconds']=181
    elif drift=='more_workers':metrics['worker_count']=3
    elif drift=='validation_failed':row['validation_status']='failed'
    if drift is None:
        validate_process_native_row(row)
    else:
        with pytest.raises(ValueError,match='EXECUTION_NATIVE_VALIDATION_BOUNDS_REQUIRED'):
            validate_process_native_row(row)
