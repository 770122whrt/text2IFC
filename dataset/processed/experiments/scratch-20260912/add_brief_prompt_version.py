import copy,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=root/'prompts/agent/design-brief-v2.7.md'
raw=source.read_bytes()
old=b'text2ifc/design-brief/2.0 Schema'
assert raw.count(old)==1
new=raw.replace(old,b'text2ifc/design-brief/2.3 Schema')
target=root/'prompts/agent/design-brief-v2.9.md'
with target.open('xb') as file:file.write(new)
registry=root/'prompts/agent/registry.json'
data=json.loads(registry.read_text(encoding='utf-8'))
row=copy.deepcopy(next(r for r in data['templates'] if r['template_id']=='design-brief.v2.7'))
row.update(template_id='design-brief.v2.9',path=target.relative_to(root).as_posix(),sha256=hashlib.sha256(new).hexdigest())
data['templates'].append(row)
with registry.open('w',encoding='utf-8',newline='\n') as file:json.dump(data,file,ensure_ascii=False,indent=2);file.write('\n')
assert source.read_bytes()==raw
