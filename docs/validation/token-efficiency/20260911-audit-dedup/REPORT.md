# T1：Audit 证据去重的第一步结果

日期：2026-09-11。产品：text2IFC。状态：**离线实施与同源对照完成；真实 token、模型质量及默认启用待验证**。唯一计划为 [semantic-appearance-plan.md 第19节](../../../architecture/semantic-appearance-plan.md#19-token-效率与质量保全渐进实施计划2026-09-11)。本报告不是 Proof，不改变 A/B 人工验收或 C 的未完成状态。

## 1. 做了什么，为什么这样做

修复后的 Audit 中，同一几何/语义/保全检查会被放入不同证据分支并重复发送。本步只处理 DETERMINISTIC_GATES 与 REVISION_EVIDENCE 中完全相同的大 JSON 对象或列表：一份正文保存在同一消息的 values 表中，其余位置以 audit_ref 引用。保留不同 revision、状态、数值、列表顺序和证据路径，发送前由代码完整还原比对。

这可以消除重复输入，又不需要模型概括或猜测。用户请求、对话、Design Brief、完整候选和用户设计审查决定继续完整发送；collect_revision_audit_evidence 和最终验证器不改。大对象阈值512 UTF-8字节是避免微小引用开销的工程取值，未作为调参结果或论文最优参数；最终仍比较包含说明文字的完整 Prompt，字节和现有 token 估计都必须更小才采用新格式，否则回退。已有 audit_ref 标记冲突也回退，坏引用/还原不一致阻止发送。

新增 audit.v4（普通）和 audit.v5（用户设计审查），输出合同分别仍为 audit/2.0 与 audit/3.0；70个旧 registry 条目及旧 Prompt 哈希保持。公共 Audit API 增加显式 audit_context_mode="deduplicated"，默认仍是 full。未增加 CLI/完整 loop 的配置传播；应在单阶段真实对照成立后单独接入并验证持久化/恢复，避免本步扩成完整编排重构。

## 2. 同源前后对比

输入来自已冻结的 A/B accepted Proof，仅作只读开发对照。每份 baseline 都由原参数和原 Prompt 版本重新渲染，与历史 request.messages[0].content **逐字相同**；源文件原始字节哈希保存在 [comparison.json](comparison.json)。输出对照没有运行，不能把旧 response 复制成新实验结果。

| 冻结请求 | 原输入字节 | 本步输入字节 | 字节变化 | 原→新字符启发式 token 估计 | 实际采用格式 |
| --- | ---: | ---: | ---: | ---: | --- |
| A 首次 Audit | 132,858 | 132,858 | 0 | 34,570→34,570 | 原格式 |
| B 首次 Audit | 128,098 | 128,098 | 0 | 33,502→33,502 | 原格式 |
| B 修复后 Audit | 255,470 | 195,088 | **−23.64%** | 65,503→50,263（−23.27%） | 去重，29份共享值 |

前三列统计完整消息文本，包括新引用语法、说明和表项，不包括 HTTP JSON 外壳。三份合计516,426→456,044字节，减少11.69%；这只是所选三条 Audit 请求的加权长度，不是整个 pipeline 的实测节省率。没有有效重复的两份若强制转换，各会增加931字节；回退避免了该开销。

更正此前讨论的一处计量前提：本地 prompt-render-input.json 有顶层 GATE_SUMMARY 等字段，但旧 audit.v2/v3 没有引用它们，实际没有发送。它们不进入本步新消息，也不计为被删除的重复输入。真正的节省来自两份实际发送的机器证据树。

| 历史原格式真实用量 | input | output（已含 reasoning） | 其中 reasoning | 新格式实际用量 |
| --- | ---: | ---: | ---: | --- |
| A 首次 Audit | 45,988 | 8,147 | 6,899 | 未测 |
| B 首次 Audit | 44,035 | 11,781 | 10,755 | 未测 |
| B 修复后 Audit | 91,765 | 5,464 | 5,044 | 未测 |

字符估算在这三条请求中均低于真实 input，因此只是实现中已有的启发式指标，**不是实际 tokenizer，也不是可靠的预算上界**。不能将23.64%字节下降直接乘到91,765上声称真实 token 节省；后续需独立校准计量和预算估算。本步未改其原有算法或放宽预算。

## 3. 质量与验证边界

- 三份真实消息的全部传输结构和值还原一致，完整候选、用户输入、Brief 和审查决定不变。相似但不同的失败/历史通过/标高/布尔/零/null/序列未合并。
- 公共 Audit 仍拒绝覆盖失败硬门、把 retain/revise 写成 resolved、围栏 JSON、坏引用和未知模式；重复失败/恢复分别保存实际发送文本、参数及记录，不能借用旧成功响应。
- 初始28项红测试因新模块/API尚不存在而失败，测试和计划提交为6217c3dc；不能称为发现28个旧生产 bug。实现后聚焦28 passed。相关注册版本、默认公开入口、两策略、CLI、Gate/revision Audit、设计审查及异常终态回归130 passed。
- 追加公共 Final Acceptance 实际 IFC 编译重读、用户决定与计量负对照后，本步36 passed；两例 IFC2X3/几何检查通过，原候选字节未改。36与130有重叠，不累计为案例成功率。fake Provider 的固定回答不证明 LLM 能无损理解引用。

这些检查证明确定性信息保全和公共边界兼容。引用会增加查找层级，也可能增加 reasoning 或漏检；因此尚不能宣称 LLM 质量非劣效、输出下降或系统稳定性提升。未运行真实 Provider、Stage/Full Preflight、独立未见场景能力评测或人工视觉验收。已验收 IFC 和原始真实 attempts 均未改写。

测试命令与各次记录哈希保存在 [validation.json](validation.json)。主要复验入口：

```powershell
.venv\Scripts\python.exe -m pytest tests/agent/test_audit_context.py -q -p no:cacheprovider --basetemp=.tmp/audit-context-review
```

输入长度对照工具：[compare_audit_context.py](../../../../scripts/agent/compare_audit_context.py)。对 comparison.json 中每个 audit_dir 传一个 --audit-dir，再指定一个**尚不存在**的 --output JSON 路径；工具拒绝旧 Prompt 无法重建/实际消息不匹配及覆盖旧报告，始终不创建 Provider。

实际阶段入口：

```python
from text2ifc_agent.live_pipeline import run_audit_report_stage

# 本报告未执行以下真实调用；provider 必须来自已批准且准入有效的实验。
run_audit_report_stage(
    provider=provider, case_dir=case_dir, case_id=case_id,
    audit_context_mode="deduplicated",
)
```

新增 audit-context.json 区分请求模式、最终采用模式、回退原因、前后长度和还原结果；prompt-wire-input.json 只含实际发送字段，原 prompt-render-input.json 保留本地完整参数。失败 attempt 中也复制这两份新记录。

## 4. 本步是否有效，接下来怎么推进

**在修复后存在重复证据的这份 Audit 上，输入文本减少有效；对首次 Audit 无收益，回退有效。真实 token 和模型质量尚不能判断。** 本步不改输出 Schema，也没有输出 token 下降的实测证据。

报告本步后，按计划逐项推进。T1 默认切换前须以同一模型/参数分别运行 full/去重单阶段对照，纳入真实失败、相近但不同的 revision 和用户保留已知问题等情况，记录实际输入、输出、reasoning、诊断一致性和错误放行；若引用增加推理或漏检，保留 full 并调整表示。该实验需要适用阶段准入及具体新载荷授权，不能挪用 C 的旧授权。

后续降低 output 的主要研究候选是参数化重复构件/楼层与确定性展开；降低 input 的候选是保留全局约束和必要依赖的分包上下文。两者需要单独版本合同、消融实验、未见请求族与相同独立 IFC 评价器。T1 是基础工程，尚不是已经证实的论文创新；也不承诺凭几条案例证明“质量绝对不下降”。
