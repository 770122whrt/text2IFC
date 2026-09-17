"""Prepare a read-only hierarchical IFC description preview; no Provider access."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from text2ifc_ifc2text.observation import extract_description_facts
from text2ifc_ifc2text.hierarchy import make_hierarchy_plan, batch_plan, assemble_hierarchy
from text2ifc_ifc2text.llm_pipeline import _write_json
from text2ifc_text.splits import atomic_write_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args()
    root = args.output_dir.resolve()
    root.relative_to(ROOT)
    root.mkdir(parents=True,exist_ok=True)
    if (root/'prepared.json').exists():
        raise ValueError('PREPARED_PREVIEW_ALREADY_EXISTS')
    before = args.source.read_bytes()
    facts = extract_description_facts(args.source)
    plan = make_hierarchy_plan(facts)
    batches = batch_plan(plan)
    results = [{'schema_version':'text2ifc/ifc2text-layout/0.3',
                'groups':[{'block_id':block['id'],'paragraphs':[[i['id']] for i in block['items']]}
                           for block in b['blocks']]} for b in batches]
    text = assemble_hierarchy(plan,results)
    import ifcopenshell
    model = ifcopenshell.open(str(args.source))
    direct = {k:len(model.by_type(c)) for k,c in {
        'walls':'IfcWall','doors':'IfcDoor','windows':'IfcWindow',
        'openings':'IfcOpeningElement','spaces':'IfcSpace','stairs':'IfcStair',
        'slabs':'IfcSlab','coverings':'IfcCovering'}.items()}
    if args.source.read_bytes()!=before or direct!=plan['component_counts']:
        raise ValueError('SOURCE_IMMUTABILITY_OR_COVERAGE_FAILED')
    _write_json(root/'source-facts.json',facts)
    _write_json(root/'writing-plan.json',plan)
    atomic_write_text(root/'design-description-deterministic.md',text)
    result = {'status':'prepared','mode':'deterministic_preview_not_LLM',
              'batch_count':len(batches),'fragment_count':plan['fact_fragment_count'],
              'direct_ifc_counts':direct,'unrepresented_classes':facts['unrepresented_classes'],
              'source_unchanged':True,'text_characters':len(text)}
    _write_json(root/'prepared.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
