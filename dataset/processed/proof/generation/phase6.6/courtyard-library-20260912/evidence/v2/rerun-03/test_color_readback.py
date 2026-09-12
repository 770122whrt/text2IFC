import importlib.util
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('hex_review',Path(__file__).with_name('color_readback_v2.py'))
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)

@pytest.mark.parametrize('hex_color',['#000000','#FFFFFF','#123456','#7F80FE','#E6E0D3','#D2C7B3','#304B4D'])
def test_three_decimal_channels_retain_hex_but_adjacent_byte_is_rejected(hex_color):
    ints=[int(hex_color[i:i+2],16) for i in (1,3,5)]
    channels=[round(v/255,3) for v in ints]
    row=dict(zip(('red','green','blue'),channels))
    assert review.matches_hex8([row],hex_color)
    other=ints[:];other[0]+=1 if ints[0]<255 else -1
    assert not review.matches_hex8([row],'#'+''.join(f'{v:02X}' for v in other))

@pytest.mark.parametrize('signatures',[[],[{},{}],[{}],[{'red':float('nan'),'green':0,'blue':0}],[{'red':-0.01,'green':0,'blue':0}],[{'red':False,'green':0,'blue':0}]])
def test_missing_ambiguous_or_invalid_style_is_rejected(signatures):
    assert not review.matches_hex8(signatures,'#000000')

@pytest.mark.parametrize('attack',['none','wrong_color','wrong_transparency','missing_part','ambiguous'])
def test_parts_keep_requested_transparency_and_exact_hex(attack):
    a={'frame':[[dict(red=.071,green=.204,blue=.337)]],
       'glazing':[[dict(red=.5,green=.7,blue=.8,transparency=.65)]]}
    requested={'frame':{'color':[18/255,52/255,86/255]},'glazing':{'transparency':.65}}
    if attack=='wrong_color':a['frame'][0][0]['red']=19/255
    if attack=='wrong_transparency':a['glazing'][0][0]['transparency']=.64
    if attack=='missing_part':a.pop('frame')
    if attack=='ambiguous':a['frame'][0].append(a['frame'][0][0].copy())
    assert review.matches_part_styles(a,requested)==(attack=='none')
