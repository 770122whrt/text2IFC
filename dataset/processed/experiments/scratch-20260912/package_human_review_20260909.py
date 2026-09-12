"""Install the user's human-reviewed model without promoting machine acceptance."""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.proof.package import SCHEMA, capture_bundle, digest, validate_package

SOURCE = ROOT / 'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260909'
COLLECTION = ROOT / 'dataset/processed/proof/generation/phase6.6/two-storey-community-20260909'
CASE = 'community-reading-building'
RUN = 'geometry-continuation/runs/5cd2006f0891913f'
assert not COLLECTION.exists(), 'Never replace an existing reviewed package'
verification = json.loads((SOURCE/'completion-recheck/verification.json').read_text(encoding='utf-8'))
assert verification['gate_overall_status'] == 'failed'
assert verification['ifc_sha256'] == digest(SOURCE/RUN/'output.ifc')
assert verification['request_sha256'] == digest(SOURCE/'request.txt')
mapping = {p.relative_to(SOURCE).as_posix(): f'{CASE}/evidence/frozen/{p.relative_to(SOURCE).as_posix()}'
           for p in SOURCE.rglob('*') if p.is_file()}
mapping.update({'request.txt':f'{CASE}/request.txt', f'{RUN}/candidate.json':f'{CASE}/model.json',
                f'{RUN}/output.ifc':f'{CASE}/generated.ifc'})
for name in ['overall.png','cutaway.png','window-double.png','door.png']:
    mapping[f'geometry-continuation/views/{name}'] = f'{CASE}/views/{name}'
bundle = capture_bundle(SOURCE, COLLECTION, 'frozen', mapping)
root = COLLECTION/CASE

artifacts = {name:{'sha256':digest(root/name),'size_bytes':(root/name).stat().st_size,
                    'source':f'{CASE}/{name}'} for name in ['request.txt','model.json','generated.ifc']}
review = {
    'decision':'accepted', 'reviewer':'user', 'date':'2026-09-09',
    'source':'current conversation: explicit user acceptance following completion-recheck report',
    'statement':'我验收过了没什么问题 你先将文件夹中有效的内容整理到proof中，并确认无误后将这次的report和图片等进行验收转移 状态修改为人类已经验收',
    'scope':'human inspection of this two-storey Generation model and presentation',
    'case_ids':[CASE], 'ifc_sha256':artifacts['generated.ifc']['sha256'],
    'request_sha256':artifacts['request.txt']['sha256'],
    'does_not_override_machine_gates':True,
}
doc = {'schema_version':SCHEMA,'collection_id':COLLECTION.name,'workflow':'generation',
       'status':'human_accepted','registration_status':'human_review_recorded',
       'accepted_proof_installed':False,'machine_acceptance_status':'blocked',
       'terminal_publication_status':'not_completed','human_review':review,
       'phase_assignment':'organization only; no phase or scientific capability promotion',
       'cases':[{'case_id':CASE,'path':CASE,'status':'human_accepted',
                 'outcome':'generated_candidate','evidence_mode':'live',
                 'provider_calls':6,'unresolved_reserved_call_count':1,
                 'run_id':'5cd2006f0891913f','machine_acceptance_status':'blocked',
                 'authority':f'{CASE}/evidence/frozen/{RUN}/gate-summary.json',
                 'artifacts':artifacts,'ifccompare':'N/A: Generation request readback, no repair ground truth'}],
       'legacy_bundles':[bundle]}

def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f: f.write(text)

def write_json(path, value): write(path,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

write_json(COLLECTION/'review-manifest.json',doc)
write_json(root/'human-review.json',review)
write_json(root/'FILES.json',{'schema_version':'text2ifc/package-artifacts/0.1','artifacts':artifacts})

summary = '''# 双层社区阅读活动楼 · 人工已验收

用户于 2026-09-09 明确表示“我验收过了没什么问题”，并要求收纳模型、报告和图片。本集合记录 **human_accepted（人工验收已通过）**；正式机器门禁仍为 **blocked**，终端发布未完成。

| 人工验收 | 独立模型复验 | 正式工程验收 |
|---|---|---|
| 用户通过 | 167 项通过 | geometry 3 项阻断，Audit 要求修订 |

''' + f'''从[案例报告]({CASE}/REPORT.md)进入，直接查看[中文输入]({CASE}/request.txt)、[完整 IFC]({CASE}/generated.ifc)和[整体图片]({CASE}/views/overall.png)。[用户验收记录]({CASE}/human-review.json)绑定实际 IFC 与输入哈希。

本集合使用既有 package 格式；review-manifest.json 保存人工结论和逐文件迁移映射。没有把 blocked 改为机器 accepted，没有创建主 manifest.json 或安装 accepted machine Proof。generated.ifc 是用户检查的完整候选，文件名沿用人读格式，不代表系统已经发布成功。

源运行按字节复制保留，未删除原目录、失败响应、未知用量预留或历史报告。完整证据见[说明]({CASE}/evidence/README.md)。该示例不能证明系统稳定成功率或科学贡献。
'''
write(COLLECTION/'README.md', summary)
write(COLLECTION/'REPORT.md', summary)
request=(root/'request.txt').read_text(encoding='utf-8')
case_report='''# 社区阅读活动楼：人工验收记录

**人工验收已通过；工程验收仍阻断。** 用户已检查本模型并明确认可。此状态依据真实人工反馈记录，不覆盖正式门禁失败，不将中断的运行补写为成功。

## 文件入口

- [实际中文输入](request.txt)，完整原文也在本页末尾。
- [完整模型 IFC](generated.ifc) · [生成模型 JSON](model.json)
- [人工验收记录](human-review.json) · [文件哈希](FILES.json)
- [完整过程证据](evidence/README.md)

## 模型和检查结果

| 内容 | 实际结果 |
|---|---|
| 建筑 | 两层社区阅读与活动楼，西侧大厅、东侧直跑楼梯 |
| 结构与空间 | 2 层、4 空间、10 墙、3 板、1 跑楼梯及真实层间洞口 |
| 门窗 | 10 窗、3 门，基础窗框／玻璃／门框／门扇、单面板与双竖面板窗 |
| 风格 | 暖色墙面、深色框、浅色玻璃，门窗立面有序 |
| 语义 | 墙体砖、楼板及屋面混凝土；没有自动补写未请求的性能属性 |
| IFC | IFC2X3，毫米；独立检查器重新打开同一 IFC，167 项通过、0 失败 |
| 视图 | 27 个实体构件网格化成功；图片与 IFC 的来源哈希一致 |
| 人工检查 | 用户于 2026-09-09 验收通过 |

## 保留的工程问题

正式 geometry gate 报告楼梯洞口身份未绑定及两处隔墙预期不足；Audit 返回 blocking=true / revise。两次后续 ChangeSet 返回因草案地址不合法被拒，第 3 次只有预留记录；运行没有完成终端发布。这些是下一步通用工程修复的对象，人工认可模型外观不意味着它们已经消失。

同任务累计 6 次已完成真实响应（Brief 1、Generator 2、Audit 1、ChangeSet 2），331,538 reported token；另有 1 次 ChangeSet 预留 172,003 token，结果和实际用量未知。原始尝试全部保留；没有在本次收纳中重新调用 Provider。

工程修复和下一例设计方向供用户另行审核，见[当前计划](../../../../../../../docs/architecture/semantic-appearance-plan.md)。修复后必须建立新验收记录，不能覆盖本次真实历史。

## 实际模型图片

![整体](views/overall.png)

![楼层与楼梯](views/cutaway.png)

剖看图仅隐藏屋面与南／东墙方便观察楼梯，悬空门窗是显示效果；完整 IFC 保留墙体。

![双竖面板窗](views/window-double.png)

![门框与门扇](views/door.png)

本例依实际请求不含栏杆、家具、机电和复杂五金。图片是实际 IFC 网格视图，没有生成式补画建筑内容。

## 实际发送的中文请求

''' + request
write(root/'REPORT.md',case_report)
write(root/'evidence/README.md',f'''# 证据来源与历史

人读入口是[案例报告](../REPORT.md)。人工验收记录位于[human-review.json](../human-review.json)；机器判断与人工判断分别保存。

- [正式门禁](frozen/{RUN}/gate-summary.json)：overall_status=failed。
- [真实 Audit](frozen/{RUN}/audit/parsed-output.json)：blocking=true。
- [独立 IFC 复验](frozen/geometry-continuation/completion-recheck-independent.json)：167 项通过。
- [调用预算](frozen/{RUN}/generation-budget.json)：真实消耗和未知预留保持原样。
- [冻结的完成情况报告](frozen/completion-recheck/REPORT.md)：人工验收前的历史判断，未重写其字节。
- [原始 Generator](frozen/{RUN}/generator/response.raw.json)、[首次失败 Generator](frozen/runtime/runs/148bdf3872e74ccd/generator/response.raw.json)。
- [本次使用的阶段准入](frozen/admission/roof-admission.json)。

collection 的 review-manifest.json/legacy_bundles 将源目录每个原路径映射到当前位置，并保存 SHA-256 与大小。旧报告内的相对链接属于旧布局；请通过映射定位，不以旧报告状态覆盖当前人工记录。源目录仍保留，未做删除或就地修改。
''')

# Preserve the exact local checker/render scripts and its previously frozen input basis.
support={}
for relative in ['.tmp/check_two_storey_review.py','.tmp/export_two_storey_mesh.py','.tmp/export_two_storey_png.py',
                 'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/request.txt',
                 'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908/frozen-expectations.json']:
    p=ROOT/relative
    dest=root/'evidence/reproduction'/p.name
    shutil.copyfile(p,dest) if dest.parent.exists() else (dest.parent.mkdir(parents=True),shutil.copyfile(p,dest))
    support[dest.relative_to(COLLECTION).as_posix()]={'source':relative,'sha256':digest(p)}
write_json(root/'evidence/reproduction/FILES.json',support)

result=validate_package(COLLECTION,doc,reopen=True)
assert result['status']=='passed', result
links=[]
for p in [COLLECTION/'README.md',COLLECTION/'REPORT.md',root/'REPORT.md',root/'evidence/README.md']:
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        assert (p.parent/link).resolve().exists(),(p,link)
        links.append(link)
for e in bundle['entries']:
    assert digest(SOURCE/e['legacy_path'])==e['sha256']
result.update(local_links_checked=len(links),frozen_files=len(bundle['entries']),source_unchanged=True,
              human_review_status='accepted',machine_acceptance_status='blocked',
              main_manifest_created=False,accepted_machine_install=False)
write_json(COLLECTION/'human-view-validation.json',result)
print(json.dumps(result,ensure_ascii=False))
