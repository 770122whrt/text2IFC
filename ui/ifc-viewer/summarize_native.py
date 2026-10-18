"""Summarize retained native diagnostics and source material coverage, without hiding errors."""
import json,re
from collections import Counter
from pathlib import Path
p=Path(__file__).parent/'.artifacts/sample-174'
r=json.loads((p/'native-report.json').read_text())
lines=[json.loads(x) for x in (p/'native-geometry.log').read_text().splitlines() if x.strip()]
s={'levels':dict(Counter(x.get('level') for x in lines)),'diagnostics':[{'level':a,'message':b,'instance_type':c,'count':n} for (a,b,c),n in Counter((x.get('level'),x.get('message'),re.search(r'=(\w+)\(',x.get('instance','')).group(1) if re.search(r'=(\w+)\(',x.get('instance','')) else None) for x in lines).items()],'palette':list({str(m):m for e in r['products'] for m in e['materials']}.values())}
(p/'diagnostic-summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(s,ensure_ascii=False,indent=2))
