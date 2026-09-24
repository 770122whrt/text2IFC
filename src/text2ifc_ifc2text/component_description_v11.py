"""Disambiguate storey names and elevations without changing component facts."""
import json

from .compact import cell,mm1
from .component_description_v10 import component_description as previous
from .observation import CATEGORIES


def component_description(facts,narration=None):
    text=previous(facts,narration)
    floors=list(facts['storeys'])
    if any(facts.get('unassigned',{}).get(c) for c in CATEGORIES):
        floors.append({**facts['unassigned'],'label':'UNASSIGNED','name':'归属未确认','elevation_mm':None})
    for floor in floors:
        old='## 楼层 '+floor['label']+'｜'+cell(floor.get('name'))+'；标高 '+mm1(floor.get('elevation_mm'))
        new='## 楼层 '+floor['label']+'｜名称='+json.dumps(cell(floor.get('name')),ensure_ascii=False)+ \
            '；楼层标高='+mm1(floor.get('elevation_mm'))+' mm'
        text=text.replace(old+'\n',new+'\n',1)
    return text.replace('## 总体与读图约定\n',
        '## 总体与读图约定\n\n楼层名称仅为名称，名称中的数字不作为标高；楼层标高以各层标题中“楼层标高=”后的数值为准。标高未确认时不从名称推测。\n',1)
