"""Fold only byte-equivalent JSON records repeated at flat and storey paths.

The schema validator remains strict. No field merge, alias resolution, guessed
storey, or conflict winner is allowed; raw model output is retained in the trace.
"""
import copy
import hashlib
import json
from pathlib import Path


def _canonical(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')


def normalize_brief_duplicates(brief):
    result=copy.deepcopy(brief);changes=[]
    if not isinstance(result,dict) or result.get('schema_version')!='text2ifc/design-brief/2.9' or result.get('status')!='ready':
        return result,changes
    known=result.get('known_facts')
    if not isinstance(known,dict) or not isinstance(known.get('storeys'),list):return result,changes
    for collection,cls in [('doors','IfcDoor'),('windows','IfcWindow')]:
        flat=known.get(collection)
        if not isinstance(flat,list):continue
        nested={}
        for index,storey in enumerate(known['storeys']):
            if not isinstance(storey,dict) or not isinstance(storey.get('id'),str):continue
            rows=storey.get(collection,[])
            if not isinstance(rows,list):continue
            for ordinal,row in enumerate(rows):
                if isinstance(row,dict) and isinstance(row.get('id'),str):
                    nested.setdefault(row['id'],[]).append((row,storey['id'],f'/known_facts/storeys/{index}/{collection}/{ordinal}'))
        counts={}
        for row in flat:
            if isinstance(row,dict) and isinstance(row.get('id'),str):counts[row['id']]=counts.get(row['id'],0)+1
        kept=[]
        for index,row in enumerate(flat):
            candidates=nested.get(row.get('id'),[]) if isinstance(row,dict) and isinstance(row.get('id'),str) else []
            if len(candidates)==1 and counts.get(row['id'])==1:
                original,storey,path=candidates[0]
                # Explicit class and owning storey must agree, not just geometry.
                if row.get('ifc_class')==cls and row.get('storey')==storey and _canonical(row)==_canonical(original):
                    changes.append({'removed_path':f'/known_facts/{collection}/{index}','retained_path':path,
                        'entity_id':row['id'],'reason':'Identical complete record with the same explicit storey'})
                    continue
            kept.append(row)
        if len(kept)!=len(flat):
            if kept:known[collection]=kept
            else:known.pop(collection)
    return result,changes


def normalize_with_trace(brief,root):
    normalized,changes=normalize_brief_duplicates(brief)
    if changes:
        root=Path(root)
        record={'schema_version':'text2ifc/brief-duplicate-normalization/1.0','changes':changes,
                'raw_sha256':hashlib.sha256(_canonical(brief)).hexdigest(),
                'normalized_sha256':hashlib.sha256(_canonical(normalized)).hexdigest(),
                'parameters_changed':False,'extra_provider_calls':0}
        for name,value in [('raw-parsed-output.json',brief),('normalization.json',record)]:
            with (root/name).open('x',encoding='utf-8') as stream:
                stream.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    return normalized
