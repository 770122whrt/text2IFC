import json,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
base=root/'dataset/processed/ifc-presentation-validation/two-storey-human-review-20260908'
evidence=base/'scoped-offline-evidence';evidence.mkdir(exist_ok=True)
for name in ['two-storey-natural-input-01.xml','two-storey-contracts-02.xml','diagnose_two_storey.py','diagnose_two_storey_enum.py','correct_two_storey.py','run_two_storey_review.py','check_two_storey_review.py']:
    p=root/'.tmp'/name
    if p.is_file() and not (evidence/name).exists():shutil.copyfile(p,evidence/name)
calls={}
for p in base.rglob('metrics.json'):
    v=json.loads(p.read_text(encoding='utf-8'))
    if v.get('response_id') and v.get('model'):
        calls.setdefault(v['response_id'],{'model':v['model'],'stage':v.get('stage','design-brief'),
            'path':p.relative_to(base).as_posix(),'status':v.get('contract_status',v.get('design_status',v.get('status'))),
            'usage':v.get('usage',{})})
rows='\n'.join(f"| {i} | {c['stage']} | {c['status']} | [{rid}]({c['path']}) |" for i,(rid,c) in enumerate(calls.items(),1))
last=json.loads((base/'corrective-04/execution.json').read_text(encoding='utf-8'))
report=f'''# 双层 Generation 开发记录

**当前状态：{last['status']}。未登记 Proof，也未替换已有单层案例。**

本次目标是两层社区阅读／活动小楼：西侧活动厅、东侧直跑楼梯、二层实际楼梯洞口，10 扇有框与玻璃面板的窗、3 扇有框和门扇的门，暖色协调主题。输入由 Codex 根据用户“更好的双层案例”要求编写，是公开合成演示，不是未见能力评测。

[冻结原始请求](request.txt) · [运行前冻结预期](frozen-expectations.json)

## 实际运行

| 次数 | 阶段 | 返回合同状态 | 真实响应及记录 |
|---|---|---|---|
{rows}

第一次 Brief 返回后因末尾换行回显差异被控制器拒绝；原响应保留。只修正运行包装器读取文本的末尾换行处理，未放宽产品合同。第二次公共 CLI 的 Brief 合法，Generator 被现有校验挡住：IFC2X3 楼梯属性名错误、门向 Style 冲突及局部坐标轴不一致。公共 CLI 未发布 IFC。

离线逐字重放复现全部 10 项问题，未改动候选；见 [诊断](offline-contract-diagnosis.json)。通过现有 feedback 接口的一次纠正调用返回空正文，已保留为真实失败；随后对相同载荷做一次有限重试。本记录不将空正文、失败或开发纠正称为公共 CLI 首次成功。

最后一次重试返回完整 JSON，原先三类合同错误不再报出，但 10 个 IfcWindowStyle 将 ConstructionType 写成了 `WINDOW`；该值不属于 IFC2X3 IfcWindowStyleConstructionEnum。未改动真实候选的离线校验复现全部 10 项错误，见 [枚举诊断](offline-enum-diagnosis.json)。**本轮真实调用已停止，没有可交付 IFC，没有进行 Audit、最终验收或双层视觉检查。** 下一步应先冻结合法／非法枚举、无 Type 请求时最小附件、门窗类别和公共纠错路径的案例族，再考虑版本化上下文或纠错改动；不能手改本案 JSON 后称为真实生成成功。

## 检查与交付边界

- 相关楼梯、公共语义路径和 Repair 定位检查：54 passed。
- 门窗局部旋转、门向冲突、模板及 invalid Formal 恢复：59 passed。两组均为离线聚焦回归，不是 Full Preflight 或能力得分。
- [测试与运行脚本](scoped-offline-evidence/) 保留到当前运行目录；复现脚本原始路径仍为仓库 `.tmp/`，不可在复制位置直接执行。
- 复用已验证的同阶段准入；没有修改已注册 Prompt、Schema、profile 或生产代码，没有运行 Full Preflight。
- 只有实际候选通过合同、语义、编译、重读、几何与独立请求核对后才进入 Audit 和最终验收。最终 IFC 通过后，按既有格式整理 request、model、IFC、中文逐项报告与静态图片，等待人工确认；不再新建网页。
- 当前没有 accepted 登记。失败 attempts、模型原始响应和源请求全部保留，不以手写或离线修补的候选冒充真实输出。

## 原始请求（UTF-8）

{(base/'request.txt').read_text(encoding='utf-8')}
'''
(base/'REPORT.md').write_text(report,encoding='utf-8')
print(json.dumps({'status':last['status'],'distinct_provider_responses':len(calls),'total_reported_tokens':sum(c['usage'].get('total_tokens',0) for c in calls.values())},ensure_ascii=False))
