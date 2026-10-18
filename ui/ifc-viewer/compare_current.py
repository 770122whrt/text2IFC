"""Compare current, actual browser measurements; keep the earlier coarse-box report intact."""
from pathlib import Path
import json
import numpy as np

p=Path(__file__).parent/'.artifacts/sample-174'
native=json.loads((p/'native-report.json').read_text(encoding='utf8'))
reports={k:json.loads((p/(k+'-precise-report.json')).read_text(encoding='utf8')) for k in ('native','webifc')}
source={r['id']:r for r in native['products']}
result={'scope':'source identity, mesh presence, exact vertex extents; not complete surface equivalence or IFC validation','source_unchanged':native['source']['unchanged_byte_for_byte'],'engines':{}}
for engine,report in reports.items():
 actual={r['id']:r for r in report['sourceProducts'] if r.get('parsedBoundsMetres')}
 rows=[]
 for id in source.keys() & actual.keys():
  bounds=np.array(source[id]['bounds']);expected=np.array([[bounds[0,0],bounds[0,2],-bounds[1,1]],[bounds[1,0],bounds[1,2],-bounds[0,1]]])
  rows.append({'id':id,'class':source[id]['type'],'same_guid':source[id]['guid']==actual[id]['guid'],'max_bounds_difference_mm':float(np.abs(expected-np.array(actual[id]['parsedBoundsMetres'])).max()*1000)})
 errors=np.array([r['max_bounds_difference_mm'] for r in rows])
 result['engines'][engine]={'products':len(actual),'missing':sorted(source.keys()-actual.keys()),'extra':sorted(actual.keys()-source.keys()),'same_guids':all(r['same_guid'] for r in rows),'triangles':report['geometry']['triangles'],'maximum_bounds_difference_mm':float(errors.max()),'p95_bounds_difference_mm':float(np.percentile(errors,95)),'within_0_1mm':int((errors<=.1).sum()),'largest_differences':sorted(rows,key=lambda r:r['max_bounds_difference_mm'],reverse=True)[:12],'native_cache':report.get('native'),'direct_parser_diagnostics':len(report.get('diagnostics',[]))}
(p/'current-fidelity-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
