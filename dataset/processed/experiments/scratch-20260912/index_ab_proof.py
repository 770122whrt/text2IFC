import difflib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
proof=ROOT/'dataset/processed/proof'
collection='generation/phase6.6/three-storey-clarification-ab-20260910'
def change_root(text):
    text=text.replace('| 集合 | 状态 | 案例 |','| 集合 | 状态 | 案例 |',1)
    anchor='| [generation/phase6.6/generation-examples](generation/phase6.6/generation-examples/REPORT.md) | accepted | 6 |'
    assert anchor in text
    text=text.replace(anchor,anchor+f'\n| [{collection}]({collection}/REPORT.md) | accepted；人工已验收，B保留已知问题 | 2 |',1)
    assert '共 48 个直接展示案例。' in text
    return text.replace('共 48 个直接展示案例。','共 50 个直接展示案例。',1)
def change_generation(text):
    anchor='| [generation-examples](phase6.6/generation-examples/REPORT.md) | accepted | 6 |'
    assert anchor in text
    return text.replace(anchor,anchor+'\n| [三层建筑A/B](phase6.6/three-storey-clarification-ab-20260910/REPORT.md) | accepted；人工已验收，B保留已知问题 | 2 |',1)
patch=[]
for relative,transform in [('dataset/processed/proof/README.md',change_root),('dataset/processed/proof/generation/README.md',change_generation)]:
    path=ROOT/relative
    current=path.read_text(encoding='utf-8')
    head=subprocess.check_output(['git','show','HEAD:'+relative],cwd=ROOT).decode('utf-8')
    path.write_text(transform(current),encoding='utf-8',newline='\n')
    patch.extend(difflib.unified_diff(head.splitlines(True),transform(head).splitlines(True),fromfile='a/'+relative,tofile='b/'+relative))
(ROOT/'.tmp/ab-proof-navigation.patch').write_text(''.join(patch),encoding='utf-8',newline='\n')
inventory=proof/'PROOF-INVENTORY.json'
doc=json.loads(inventory.read_text(encoding='utf-8'))
assert not any(r['path']==collection for r in doc['collections'])
doc['collections'].append(dict(collection_id='three-storey-clarification-ab-20260910',path=collection,status='accepted',case_count=2,
    manifest=collection+'/manifest.json',report=collection+'/REPORT.md',human_review_date='2026-09-10',
    scope='Faithful generation and human presentation acceptance; B retains known clearance defect, no code compliance claim.'))
doc['generated_at']='2026-09-10'
inventory.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
source=ROOT/'dataset/processed/ifc-presentation-validation/three-storey-clarification-branches-20260910/failure-recovery-rerun-20260910'
(source/'PROOF-LOCATION.md').write_text('''# 当前人工验收入口

用户于2026-09-10将两份人读IFC改名为generated-A.ifc / generated-B.ifc，并确认内容无误。
现已计入[三层建筑A/B Proof](../../proof/generation/phase6.6/three-storey-clarification-ab-20260910/REPORT.md)。

本目录的FILES及报告保留验收前字节和文件名；当前Proof manifest逐项映射原始路径并保存相同哈希。当前人工状态以Proof内human-review.json为准，B已知净空问题仍然存在。
''',encoding='utf-8',newline='\n')
print('Proof indexed; navigation patch excludes existing unrelated additions.')
