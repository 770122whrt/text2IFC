"""Read-only checks for prepared compact text; qualitative review remains explicit."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from text2ifc_ifc2text.compact import compact_description, narrative_context, validate_narration, mm1
from text2ifc_ifc2text.compact_pipeline import CLASSES
from text2ifc_ifc2text.observation import all_items
from text2ifc_ifc2text.llm_pipeline import _write_json


def review(output: Path):
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.unit
    load = lambda p: json.loads(p.read_text(encoding='utf-8'))
    facts = load(output/'source-facts.json')
    prepared = load(output/'prepared.json')
    source = Path(prepared['source_path'])
    before = source.read_bytes()
    model = ifcopenshell.open(str(source))
    text = (output/'design-description.md').read_text(encoding='utf-8')
    narration = load(output/'writing/narration/parsed-response.json')
    validate_narration(narration, narrative_context(facts))
    settings = ifcopenshell.geom.settings(); settings.set(settings.USE_WORLD_COORDS, True)
    scale = ifcopenshell.util.unit.calculate_unit_scale(model)*1000
    counts = Counter(c for c,_ in all_items(facts))
    errors = []; unassessed = []; checks = []; max_rounding = 0.0
    if text != compact_description(facts, narration): errors.append('ASSEMBLY_CHANGED')
    for category, cls in CLASSES.items():
        if counts[category] != len(model.by_type(cls)): errors.append('COUNT_'+category)
    for category, item in all_items(facts):
        label = item['label']; entity = model.by_guid(item['source_global_id'])
        box = item.get('bounds_mm'); max_delta = None
        if box:
            try:
                shape = ifcopenshell.geom.create_shape(settings, entity)
                verts = shape.geometry.verts
                max_delta = 0.0
                for n,axis in enumerate(('x','y','z')):
                    values = [float(v)*1000 for v in verts[n::3]]
                    max_delta = max(max_delta, *[abs(a-b) for a,b in zip([min(values),max(values)],box[axis])])
                    max_rounding = max(max_rounding,*[abs(float(mm1(v))-v) for v in box[axis]])
                if max_delta > .002: errors.append('BOUNDS_'+label)
            except Exception as error:
                unassessed.append({'label':label,'field':'independent_direct_mesh','reason':type(error).__name__})
        else: unassessed.append({'label':label,'field':'bounds'})
        for field,key in [('OverallWidth','overall_width_mm'),('OverallHeight','overall_height_mm')]:
            if item.get(key) is not None:
                value = getattr(entity,field,None)
                if value is None or abs(float(value)*scale-item[key])>.002: errors.append(field+'_'+label)
        # Entity presence checks do not mistake material references for geometry rows.
        if category in ('walls','doors','windows','openings'):
            if sum(line.startswith('|'+label+'|') for line in text.splitlines()) != 1: errors.append('TEXT_COUNT_'+label)
        elif label not in text: errors.append('TEXT_ABSENCE_'+label)
        checks.append({'label':label,'category':category,'bounds_delta_mm':max_delta})
    if max_rounding > .050001: errors.append('COORDINATE_ROUNDING')
    if source.read_bytes()!=before: errors.append('SOURCE_CHANGED')
    report = {'schema_version':'text2ifc/compact-content-check/0.5',
        'status':'checks_passed_pending_agent_prose_review' if not errors else 'blocked',
        'errors':errors,'unassessed':unassessed,'checks':checks,
        'counts':dict(counts),'characters':len(text),'han_characters':len(re.findall(r'[\u4e00-\u9fff]',text)),
        'max_coordinate_rounding_error_mm':max_rounding,'source_unchanged':source.read_bytes()==before,
        'not_proven':['exact_shape_fidelity','room_semantics','qualitative_narration_correctness'],
        'narration_for_agent_review':narration}
    _write_json(output/'content-check.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--config',default='scripts/ifc2text/compact-campaign-v0.5.json')
    args=parser.parse_args(); cfg=json.loads((ROOT/args.config).read_text(encoding='utf-8'))
    reports={c['id']:review(ROOT/cfg['output']/c['id']) for c in cfg['cases']}
    print(json.dumps({k:{f:v[f] for f in ['status','errors','unassessed','counts','characters','han_characters','max_coordinate_rounding_error_mm','narration_for_agent_review']} for k,v in reports.items()},ensure_ascii=False,indent=2))
    return int(any(r['errors'] for r in reports.values()))

if __name__=='__main__': raise SystemExit(main())
