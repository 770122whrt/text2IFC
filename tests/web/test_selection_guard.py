"""The web pick guard must stop wrong-object application, not silently retarget it."""
from pathlib import Path
import pytest
from text2ifc_web.selection_guard import check_selection
from text2ifc_ifc_repair.api import RepairAPI


def context(target='wall-A',reference='window-A'):
    return {'source_ifc_path':None,'resolution':{'operations':[{'operation_id':'op1','operation_type':'add_window_with_opening_to_wall','target_global_id':target}]},
            'installation_references':{'op1':{'target_global_id':target,'reference_global_id':reference}},'derivations':[]}

def refs(primary='wall-A',auxiliary='window-A'):
    return {'primary':{'global_id':primary,'ifc_class':'IfcWallStandardCase'},'auxiliary':{'global_id':auxiliary,'ifc_class':'IfcWindow'}}


def test_no_selection_does_not_invent_a_constraint():
    assert check_selection({'primary':None,'auxiliary':None},context())['valid']


def test_wall_and_reference_must_both_match_not_merely_share_a_type():
    assert check_selection(refs(),context())['valid']
    assert not check_selection(refs(),context(target='wall-B'))['valid']
    assert not check_selection(refs(),context(reference='window-B'))['valid']


def test_column_location_role_is_not_confused_with_the_storey_execution_target():
    c=context(target='storey-A');c['resolution']['operations'][0]['operation_type']='add_column'
    c['installation_references']={};c['derivations']=[{'operation_id':'op1','reference_occurrence_id':'column-A'}]
    assert check_selection({'primary':{'global_id':'column-A','ifc_class':'IfcColumn'},'auxiliary':None},c)['valid']
    c['derivations']=[]
    assert not check_selection({'primary':{'global_id':'column-A','ifc_class':'IfcColumn'},'auxiliary':None},c)['valid']


def test_guard_hook_is_an_explicit_native_api_extension(tmp_path):
    api=RepairAPI(tmp_path,provider=object())
    api.configure_integration(before_apply=lambda c:{'valid':False,'issues':[]},observer=None)
    assert callable(api._before_apply)
    with pytest.raises(TypeError):api.configure_integration(before_apply='untrusted')
