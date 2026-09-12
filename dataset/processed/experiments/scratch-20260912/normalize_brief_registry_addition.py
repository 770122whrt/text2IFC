import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];path=root/'prompts/agent/registry.json'
current=json.loads(path.read_text(encoding='utf-8'))
base=subprocess.check_output(['git','show','HEAD:prompts/agent/registry.json'],cwd=root).decode('utf-8')
old=json.loads(base)
assert current['templates'][:-1]==old['templates']
row=current['templates'][-1];assert row['template_id']=='design-brief.v2.9'
row['sha256']='sha256:'+row['sha256'].removeprefix('sha256:')
index=base.rindex('\n  ]')
addition=',\n'+'\n'.join('    '+line for line in json.dumps(row,ensure_ascii=False,indent=2).splitlines())
result=base[:index]+addition+base[index:]
assert json.loads(result)['templates']==old['templates']+[row]
with path.open('w',encoding='utf-8',newline='\n') as file:file.write(result)
