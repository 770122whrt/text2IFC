import json
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'docs/reports/run-cleanup-review-20260910'
data=json.loads((out/'inventory.json').read_text(encoding='utf-8'))
for row in data['targets']:
    for file in row['file_inventory']:file['proof_copies']=file['proof_copies'][:1]
(out/'inventory.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
targets=[]
ab=data['targets'][0]
for branch in ['A-revise','B-retain']:
    prefix=branch+'/runtime/'
    files=[{**f,'path':f['path'][len(prefix):]} for f in ab['file_inventory'] if f['path'].startswith(prefix)]
    assert files and all(f['proof_copies'] for f in files)
    targets.append(dict(target=ab['target']+'/'+prefix.rstrip('/'),files=files,
        reason='已验收A/B Proof内有相同字节副本；只退役runtime，保留原脚本、输入、报告和PROOF-LOCATION。',
        condition='本次实验结束；更新活动依赖引用后再执行，旧冻结记录不回写。'))
two=data['targets'][1];assert not two['uncovered_files']
targets.append(dict(target=two['target'],files=two['file_inventory'],reason='533份文件均有人工验收Proof副本；保持机器blocked原状态。',
    condition='先补存此前未跟踪的Proof包并推送、核实远端后再删源目录。'))
for row in data['targets'][2:]:
    assert not row['errors'] and not row['reparse_points']
    targets.append(dict(target=row['target'],files=row['file_inventory'],reason='本对话明确创建的pytest/离线夹具目录；非真实Provider产物。相关红绿XML、日志和代码已保留。',
        condition='只删清单内目录，不删除同名.log/.xml、脚本或其他.tmp目录。'))
manifest=dict(status='pending_explicit_user_deletion_approval',deletion_performed=False,
    execute_after='experiment_completed_and_hashes_rechecked',targets=targets)
(out/'deletion-proposal.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 本对话运行目录清理提案','',
    '状态：只读盘点与证据保全；尚未删除。只有用户批准本清单后才执行。路径均相对于 `E:/code for project/bimnet`。','',
    '| 拟删除目录 | 文件数 | MiB | 保全依据 |','|---|---:|---:|---|']
for row in targets:
    size=sum(f['bytes'] for f in row['files'])
    lines.append(f"| `{row['target']}` | {len(row['files'])} | {size/1048576:.2f} | {row['reason']} |")
total=sum(f['bytes'] for row in targets for f in row['files'])
lines+=['',f'合计{len(targets)}个精确目录，约{total/1048576:.2f} MiB。完整文件、大小、SHA-256和Proof副本位置见 [删除清单](deletion-proposal.json)。',
    '', '保留：A/B运行根目录及测试仍使用的run_branches.py；A/B此前失败尝试；C型失败和成功Brief、最新累计账本、冻结评价器；当前96K实验；所有已验收Proof。',
    '', 'A/B旧runtime删除后，历史报告和admission中的原路径只是冻结的历史记录。实际机器权威位于Proof的evidence/frozen；后续活动脚本与准入必须读取该规范副本，不能通过删除后绕过哈希检查。',
    '', '双层包此前存在于本地但没有Git跟踪；已重新核对533份源文件副本与人读结构/IFC重开。必须先将该人工review包保全到Git并推送，不能仅因文件夹名叫proof就删源。人工通过不提升机器blocked状态。',
    '', 'pytest目录来自本次对话明确执行的测试命令，可从已提交测试重新生成；红绿日志/XML已收入C型诊断与验证包。未将可重建夹具冒充真实Provider证据。',
    '', '删除前重新核对绝对路径在仓库内、无junction/symlink、文件集合和哈希未变、没有活动进程使用；若内容变化，停止该项并报告。不会修改Codex会话、账号或数据库。']
(out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'targets':len(targets),'mib':round(total/1048576,2),'files':sum(len(t['files']) for t in targets)}))
