"""Summarize the actually executed bounded viewer run and compose its real screenshots."""
from pathlib import Path
import json,re
from collections import Counter
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
OUT=HERE/'.artifacts/dataset-ifc2x3/current'
r=json.loads((OUT/'results.json').read_text(encoding='utf8'))
rows=r['results'];details=[]
for row in rows:
    p=OUT/(row['id']+'-parser.json')
    if not p.exists():continue
    report=json.loads(p.read_text(encoding='utf8'))
    if row['diagnostic_count']:
        messages=Counter(re.sub(r'\d+','<id>',d['message']) for d in report['diagnostics'])
        details.append({'id':row['id'],'missing':row['missing_expected_ids'],'messages':dict(messages)})
summary={'tested':len(rows),'sources':len({r['source_collection'] for r in rows}),'loaded':sum(r.get('load_success',False) for r in rows),'no_whole_body_missing':sum(r.get('load_success',False) and not r.get('missing_expected_ids') for r in rows),'without_parser_diagnostics':sum(r.get('load_success',False) and r.get('diagnostic_count')==0 for r in rows),'all_basic_interactions':sum(all(r.get(k,False) for k in ['rotation_works','zoom_works','pick_hide_restore']) for r in rows),'sources_unchanged':all(r['source_unchanged'] for r in rows),'bytes_range':[min(r['bytes'] for r in rows),max(r['bytes'] for r in rows)],'load_seconds_range':[min(r['load_wall_seconds'] for r in rows),max(r['load_wall_seconds'] for r in rows)],'diagnostic_details':details,'scope':'Source-schema read, drawable mesh presence, source identities, real screenshots and selected basic interactions. Not full geometry equivalence, IFC validation or a claim over the entire dataset.'}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
sheet=Image.new('RGB',(1680,1125),'white');draw=ImageDraw.Draw(sheet)
for i,row in enumerate(rows):
    file=OUT/(row['id']+'.png')
    if not file.exists():continue
    im=Image.open(file).convert('RGB').crop((0,140,1108,836));im.thumbnail((414,261))
    x=(i%4)*420;y=(i//4)*375
    sheet.paste(im,(x+(414-im.width)//2,y+25))
    color='#934524' if row['missing_expected_ids'] else '#264a3f'
    draw.text((x+7,y+5),row['id'],fill=color)
    draw.text((x+7,y+297),f"meshes: {row['parsed_objects']} | diagnostics: {row['diagnostic_count']}",fill=color)
    draw.text((x+7,y+319),f"missing Body: {len(row['missing_expected_ids'])}",fill=color)
sheet.save(OUT/'contact-sheet.png')
print(json.dumps(summary,ensure_ascii=False,indent=2))
