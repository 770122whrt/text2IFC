import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'dataset/processed/ifc-presentation-validation/c-shaped-brief-budget-experiment-20260910'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
e=read(P/'live/execution.json'); assert e['status']=='completed'
requests={a:read(P/f'live/{a}/design-brief/request.redacted.json')['request'] for a in ['96k','64k']}
diff=[k for k in requests['96k'].keys() | requests['64k'].keys() if requests['96k'].get(k)!=requests['64k'].get(k)]
assert diff==['max_tokens'],diff
rows=[]
for arm in e['arms']:
    label=arm['label']; d=P/f'live/{label}/design-brief'
    meta=read(d/'response-metadata.json');u=meta['usage'];b=read(d/'design-brief.json');f=b['known_facts']
    sem=f['semantic_requirements']; by={key:sum(key in s for s in sem) for key in ['material','template','type','properties','appearance']}
    row=dict(label=label,cap=arm['output_cap'],status=arm['status'],valid=arm['valid'],finish_reason=meta['stop_reason'],
        response_id=meta['response_id'],model=meta['model'],input_tokens=u['prompt_tokens'],completion_tokens=u['completion_tokens'],
        reasoning_tokens=u['completion_tokens_details']['reasoning_tokens'],visible_tokens=u['completion_tokens']-u['completion_tokens_details']['reasoning_tokens'],
        total_tokens=u['total_tokens'],cache_hit_tokens=u['prompt_cache_hit_tokens'],active_seconds=arm['budget_after']['active_seconds']-arm['budget_before']['active_seconds'],
        brief_observations=dict(storeys=len(f['storeys']),spaces=sum(len(s['spaces']) for s in f['storeys']),walls=sum(sum(len(group) for group in s['walls'].values()) if isinstance(s['walls'],dict) else len(s['walls']) for s in f['storeys']),
            doors=sum(len(s['doors']) for s in f['storeys']),windows=sum(len(s['windows']) for s in f['storeys']),stairs=len(f['stairs']),
            semantic_fields=by,materials=sorted({s['material']['name'] for s in sem if 'material' in s}),appearance=f['appearance'],
            roof=f['roof_slab'],clarifications=b['clarification_questions'],blocking_ambiguities=[x['id'] for x in b['ambiguities'] if x.get('blocking')]),
        output_characters=len((d/'model-text.txt').read_text(encoding='utf-8')))
    rows.append(row)
comparison=dict(status='completed',scope='two real single-response Brief calls, one per cap; no Generation/Audit/IFC',request_diff_keys=diff,
    prompt_identical=True,arms=rows,budget_before=e['budget_before'],budget_after=e['budget_after'],
    added_tokens=e['budget_after']['tokens_used_or_reserved']-e['budget_before']['tokens_used_or_reserved'],
    limitations=['N=1 per cap; decoding randomness, order and cache confounded; no reliability rate or causal effect estimate',
      'Brief validation and selected field inventory do not independently prove all request values or final IFC semantics',
      'Both responses require clarification; neither is generation-ready',
      'Clarification is model interpretation of the existing Prompt rule; its assertion of deterministic checking is not an independently executed check'])
write(P/'comparison.json',comparison)
lines=['# Design Brief 单次输出额度实验（2026-09-10）','',
'结论：96K 可为较长响应提供余量，但本次 64K 也完整返回；提高上限还不能视为稳定性修复，更不是节省 token 的方案。两组均为 `needs_clarification`，不是 ready，也未产出新 IFC。','',
'实验只改变单次 `max_tokens`，预先确定先96K后64K，各执行一次真实响应。请求、对话、Schema 2.3、Prompt v2.9、模型请求 deepseek-v4-flash 和 thinking 设置一致；实际响应标识为 deepseek-flash。红acted请求逐字段比较只有 max_tokens 不同。原始请求见 [C型输入](../c-shaped-teaching-building-20260910/request.txt)，冻结设置见 [protocol.json](protocol.json)。','',
'| 单次上限 | 输入 | 输出（含推理） | 推理 | 可见输出 | 总 token | 活动秒 | 结果 |','|---|---:|---:|---:|---:|---:|---:|---|']
for r in rows:lines.append(f"| {r['cap']:,} | {r['input_tokens']:,} | {r['completion_tokens']:,} | {r['reasoning_tokens']:,} | {r['visible_tokens']:,} | {r['total_tokens']:,} | {r['active_seconds']:.3f} | stop；校验通过；待澄清 |")
lines += ['', '96K 这次输出68,621 token，超过旧65,536上限3,085；它确实使用了额外空间。64K这次仅输出47,369 token，也成功完成。输出中的推理分别约79.4%和77.9%；继续压缩可见JSON的空白不是主要解法。两次缓存命中也不同，分别14,208/18,304输入token，不能把时间差归因于输出上限。','',
'两组都提出：二、三层楼梯洞口与声明的交通/楼梯空间平面重叠，要求确认空间是否包含楼梯井。96K另记了非阻塞的踏步口径问题。现有Prompt第100行明确要求对这类重叠提出澄清；这是模型执行提示规则的结果，并非本实验运行了独立几何审查器。输出中“确定性检查显示”的文字不能当作检查证据；重叠本身也不等于不合理建筑。是否已有足够用户信息、是否产生多余澄清，需另做通用规则适用性复核，不能在本次额度实验中代答或放行。','',
'选定字段只读盘点：两组均保留三层、九空间、七门、二十一窗、两段楼梯，以及warm-residential主题。详细材料/模板字段数量、屋面记录和澄清原文见 [comparison.json](comparison.json)。这不是最终IFC逐项独立验收。','',
'建议按小步实施（本轮仅建议，未改生产默认配置、Prompt或Schema）：','',
'1. 将96K保留为Brief有界诊断/重试选项，继续使用任务共用账本与退出机制。不要全阶段提高额度，也不把重试当作新预算。',
'2. 优先做输入去重：原始请求同时出现在USER_REQUEST和CONVERSATION，可在新Prompt版本中只呈现一次并保留来源绑定；精简重复规则及不相关示例/能力片段，保持所需Schema、材料/Type授权和冲突约束。先比较质量与实际用量，再决定采用。',
'3. 若仍经常出现长推理，再比较受支持的阶段专用推理设置；之后才考虑分段Brief（先全局尺寸/层级，再构件与语义），由确定性代码按稳定ID合并、冲突暂停、仅重试失败段，并共用预算。重复楼层的压缩表达不意味着共享IFC Type。','',
'[token-opportunities.json](token-opportunities.json) 是前次v2.7成功响应的离线估算，不是本次真实节省量。前次可见JSON原文与去空白后均31,047字符，去空白收益为零；输入请求重复项约1,436估算token，能力目录/示例/Schema分别约4,190/2,578/1,898估算token。估算器不是Provider分词器；这些数不能直接承诺实际节省或费用下降。','',
'验证与证据：实验runner及直接受影响路径38项离线测试通过，承接同阶段既有准入；初次命令引用不存在的测试文件而未执行测试，其日志一并保留。当前真实调用新增2次、152,910 token；C任务含原失败与前次诊断累计4次、300,540 token、886.717秒，原32次/200万token/3600秒上限不变。最新账本是 [live/generation-budget.json](live/generation-budget.json)。旧预算字节不变，不能继续把旧2次账本作为最新状态。','',
'所有真实请求/响应、失败记录和准入均保留。这只是单次配对可行性观察；没有Baseline/Candidate盲测、系统能力提升结论、Generation/Audit/新IFC、Full Preflight或Proof登记。准入是调用当时的冻结快照；其部分旧运行路径在随后获准清理中退役，今后调用必须重新绑定规范Proof，不能直接重用本快照。']
(P/'REPORT.md').write_text('\n'.join(lines).replace('红acted','脱敏')+'\n',encoding='utf-8')
print(json.dumps({r['label']:{k:r[k] for k in ['completion_tokens','reasoning_tokens','status','brief_observations']} for r in rows},ensure_ascii=False)[:2600])
