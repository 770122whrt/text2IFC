"""Explicit closure is part of the public text, not postprocessing live outputs."""
import copy
import pytest
from text2ifc_ifc2text.wall_details_v08 import closed_ring, single_wall_description


@pytest.mark.parametrize('points',[
    [[0,0],[100,0],[80,20],[0,20]],
    [[0,0],[100,0],[80,20],[0,20],[0,0]],
    [[-10.04,5.02],[50.01,5.02],[40.05,30.04],[-10.04,5.02]],
])
def test_explicit_closure_appears_once_at_end_without_changing_points(points):
    original=copy.deepcopy(points)
    text=closed_ring(points); segments=text.split('→')
    assert segments[0]==segments[-1]
    assert segments[-2]!=segments[-1]
    assert points==original


def test_v08_single_wall_no_implicit_closure_or_source_identity():
    wall={'label':'wall-A','source_global_id':'PRIVATE_ID',
          'solid_detail':{'bottom_outline_xy_mm':[[0,0],[100,0],[80,20],[0,20],[0,0]],
                          'bottom_z_mm':0.,'height_mm':3000.}}
    text=single_wall_description(wall)
    assert '自动闭合' not in text
    assert '(0.0,0.0)→(100.0,0.0)→(80.0,20.0)→(0.0,20.0)→(0.0,0.0)' in text
    assert 'PRIVATE_ID' not in text


def test_rounding_cannot_silently_destroy_profile():
    with pytest.raises(ValueError,match='INVALID_RING'):
        closed_ring([[0.,0.],[.01,0.],[0.,.01]])
