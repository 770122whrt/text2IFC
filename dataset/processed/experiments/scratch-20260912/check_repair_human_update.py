import json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote,urlsplit
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from scripts.proof.package import validate_package
collection=root/'dataset/processed/proof/repair/phase12.1/semantic-appearance-20260908'
case=collection/'vvo-instance-properties'
manifest=json.loads((collection/'review-manifest.json').read_text(encoding='utf-8'))
result=validate_package(collection,manifest,reopen=False)
assert result['status']=='passed',result
assert manifest['registration_status']=='unregistered' and not (collection/'manifest.json').exists()
text=(case/'REPORT.md').read_text(encoding='utf-8')
request=(case/'request.txt').read_text(encoding='utf-8').strip()
assert request in text
assert '\ufffd' not in text
links=re.findall(r'\]\(([^)]+)\)',text)
for link in links:
    parsed=urlsplit(link)
    if not parsed.scheme and parsed.path:assert (case/unquote(parsed.path)).resolve().is_file(),link
ET.parse(case/'evidence/views/location-plan.svg')
query=json.loads((case/'evidence/no-guid-location-boundary.json').read_text(encoding='utf-8'))
assert query['result']['status']=='ambiguous' and len(query['result']['candidates'])==2
result.update(scope='Changed human report links and UTF-8, SVG XML, unchanged request/IFC and frozen bundle hashes; no repeated IFC reopen or accepted curator.',human_report_links=len(links),no_guid_candidates=2,registration='unregistered')
path=case/'evidence/human-language-validation.json'
with path.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result,ensure_ascii=False))
