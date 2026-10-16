"""Correlate the existing native parser log with its exact IFC source; never edit IFC."""
from pathlib import Path
from collections import Counter
import json
import re
import gzip
import base64
import os
import ifcopenshell

ROOT=Path(__file__).parent/'.artifacts/sample-174'
def main():
    source=ROOT/'source.ifc'
    before=source.read_bytes()
    model=ifcopenshell.open(str(source))
    records=[json.loads(line) for line in (ROOT/'native-geometry.log').read_text(encoding='utf-8').splitlines() if line.startswith('{')]
    errors=[r for r in records if r.get('level')=='Error']
    grouped=Counter((r.get('message'),r.get('instance')) for r in errors)
    groups=[]
    for (message,instance),count in grouped.items():
        found=re.match(r'#(\d+)=',instance or '')
        obj=model.by_id(int(found[1])) if found else None
        groups.append({'level':'Error','message':message,'instance':instance,'count':count,
                       'material_has_representation':bool(getattr(obj,'HasRepresentation',())) if obj and obj.is_a('IfcMaterial') else None})
    excluded=Counter();no_rep=[]
    for obj in model.by_type('IfcProduct'):
        if obj.is_a() in ('IfcOpeningElement','IfcSpace','IfcAnnotation'):
            excluded[obj.is_a()]+=1
        elif not getattr(obj,'Representation',None):
            no_rep.append({'id':obj.id(),'ifc_class':obj.is_a(),'name':obj.Name,'global_id':obj.GlobalId,
                           'decomposed_children':[{'id':child.id(),'ifc_class':child.is_a(),'has_representation':bool(getattr(child,'Representation',None))} for rel in getattr(obj,'IsDecomposedBy',()) for child in rel.RelatedObjects]})
    result={'source_name':source.name,'error_count':len(errors),'distinct_error_count':len(groups),'errors':groups,
            'excluded_classes':dict(excluded),'no_representation':no_rep,
            'no_representation_classes':dict(Counter(r['ifc_class'] for r in no_rep)),
            'source_unchanged':before==source.read_bytes(),
            'interpretation':'Correlated records, not a full visual-fidelity or IFC validity certificate.'}
    out=Path(__file__).parent/'.artifacts/api-wiring/round2'
    out.mkdir(parents=True,exist_ok=True)
    (out/'diagnostic-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    # Attach only explanatory metadata to the generated viewer cache after exact source verification.
    cache=ROOT/'native-meshes.json.gz'
    bundle=json.loads(gzip.decompress(cache.read_bytes()))
    assert base64.b64decode(bundle['source_base64'])==before, 'Cache/source mismatch'
    # Independent source-style inventory plus actual extracted face/material assignment.
    # Presence of at least one style is not a claim that every face is visually identical.
    style_rows=[];unassigned=0
    for product in bundle['products']:
        obj=model.by_id(product['id'])
        styled=set()
        for entity in model.traverse(obj.Representation) if getattr(obj,'Representation',None) else ():
            for item in getattr(entity,'StyledByItem',()):
                if getattr(item,'Styles',()):styled.add(item.id())
        invalid=sum(type(i) is not int or i<0 or i>=len(product['materials']) for i in product['material_ids'])
        unassigned+=invalid
        style_rows.append({'id':product['id'],'explicit_styled_item_ids':sorted(styled),
                           'mesh_material_names':[m['name'] for m in product['materials']],
                           'unassigned_triangles':invalid})
    result['style_audit']={'rendered_products':len(style_rows),
        'products_with_explicit_style':sum(bool(r['explicit_styled_item_ids']) for r in style_rows),
        'unassigned_triangles':unassigned,'products':style_rows,
        'scope':'Source StyledByItem presence and extracted material indices only; no pixel-equivalence claim.'}
    result['official_basis']={
        'schema':'IFC2X3 TC1',
        'product':'https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifckernel/lexical/ifcproduct.htm',
        'material':'https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcmaterialresource/lexical/ifcmaterial.htm',
        'roof':'https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcroof.htm',
        'stair':'https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcsharedbldgelements/lexical/ifcstair.htm'}
    (out/'diagnostic-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    bundle['diagnostic_audit']=result
    temporary=cache.with_suffix('.audit.tmp')
    temporary.write_bytes(gzip.compress(json.dumps(bundle,ensure_ascii=False,separators=(',',':')).encode('utf-8')))
    os.replace(temporary,cache)
    print(json.dumps({'error_count':result['error_count'],'distinct_error_count':result['distinct_error_count'],
        'excluded_classes':result['excluded_classes'],'no_representation_classes':result['no_representation_classes'],
        'style_audit':{k:v for k,v in result['style_audit'].items() if k!='products'},
        'source_unchanged':result['source_unchanged'],'report':str(out/'diagnostic-audit.json')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
