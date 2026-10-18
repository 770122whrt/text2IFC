"""Compare matching IFC product identities and world AABBs between two actual parsers.
This is not a full surface-distance metric and does not prove pixel-identical rendering.
"""
from pathlib import Path
import json,re,html
from collections import Counter
import numpy as np
p=Path(__file__).parent/'.artifacts/sample-174'
native=json.loads((p/'native-report.json').read_text(encoding='utf8'))
dom=(p/'browser-front.html').read_text(encoding='utf8')
match=re.search(r'<pre[^>]*id="report"[^>]*>(.*?)</pre>',dom,re.S)
if not match:raise RuntimeError('Actual browser report missing')
browser=json.loads(html.unescape(match.group(1)))
(p/'browser-report.json').write_text(json.dumps(browser,ensure_ascii=False,indent=2),encoding='utf8')
nb={r['id']:r for r in native['products']};wb={r['id']:r for r in browser['sourceProducts'] if r.get('parsedBoundsMetres')}
errors=[]
for k in sorted(set(nb)&set(wb)):
    a=np.array(nb[k]['bounds']);target=np.array([[a[0,0],a[0,2],-a[1,1]],[a[1,0],a[1,2],-a[0,1]]])
    delta=np.abs(target-np.array(wb[k]['parsedBoundsMetres']));errors.append({'id':k,'guid':nb[k]['guid'],'type':nb[k]['type'],'bounds_max_abs_mm':float(delta.max()*1000),'same_guid':nb[k]['guid']==wb[k]['guid'],'native_triangles':nb[k]['triangles'],'browser_triangles':wb[k]['triangles']})
values=np.array([r['bounds_max_abs_mm'] for r in errors])
result={'native_expected':native['expected_body_products'],'native_meshes':len(nb),'browser_meshes':len(wb),'matched_ids':len(errors),'missing_in_browser':sorted(set(nb)-set(wb)),'extra_in_browser':sorted(set(wb)-set(nb)),'all_matching_guids':all(r['same_guid'] for r in errors),'frame_checked':'native (x,y,z) -> web-ifc (x,z,-y); no source geometry altered','bounds_mm':{'median':float(np.median(values)),'max':float(values.max()),'p95':float(np.percentile(values,95)),'within_0_1mm':int((values<=.1).sum())},'top_bounds_differences':sorted(errors,key=lambda r:r['bounds_max_abs_mm'],reverse=True)[:10],'native_triangles':native['triangles'],'browser_triangles':browser['geometry']['triangles'],'browser_parser':browser['parser'],'browser_diagnostic_count':len(browser['diagnostics']),'browser_diagnostic_messages':dict(Counter(d['message'][:400] for d in browser['diagnostics'])),'scope':'identity, whole-object presence, world-axis bounding extents only; not full topology, shape equality, IFC validator or repair acceptance'}
(p/'parser-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(p/'per-product-comparison.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
