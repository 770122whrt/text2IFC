"""Pack already-extracted triangles and their exact source snapshot. Never infer geometry."""
import gzip,json,base64
from pathlib import Path
import numpy as np
p=Path(__file__).parent/'.artifacts/sample-174'
r=json.loads((p/'native-report.json').read_text(encoding='utf8'));a=np.load(p/'meshes.npz',allow_pickle=False)
source=(p/'source.ifc').read_bytes()
if len(source)!=r['source']['bytes']:raise ValueError('Source snapshot size changed')
parts=[]
for item in r['products']:
 k=str(item['id']);parts.append({'id':item['id'],'guid':item['guid'],'vertices':a[k+'_v'].tolist(),'faces':a[k+'_f'].tolist(),'material_ids':a[k+'_m'].tolist(),'materials':item['materials']})
log=[json.loads(line) for line in (p/'native-geometry.log').read_text().splitlines() if line.strip()]
bundle={'schema':'ifc-native-mesh-preview/1','source_bytes':len(source),'source_base64':base64.b64encode(source).decode('ascii'),'ifcopenshell':r['kernel']['ifcopenshell'],'settings':r['kernel']['settings'],'native_frame':'x,y,z (Z up)','products':parts,'diagnostics':{'errors':sum(x.get('level')=='Error' for x in log),'notices':sum(x.get('level')=='Notice' for x in log),'scope':'Retained native material conversion diagnostics; see native-geometry.log'}}
payload=json.dumps(bundle,separators=(',',':'),ensure_ascii=False).encode('utf8')
with gzip.open(p/'native-meshes.json.gz','wb') as f:f.write(payload)
print(json.dumps({'products':len(parts),'json_bytes':len(payload),'gzip_bytes':(p/'native-meshes.json.gz').stat().st_size,'exact_source_embedded':True,'source_ifc_changed':False}))
