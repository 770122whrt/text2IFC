# IFC2Text Phase 1 实施记录（2026-09-16）

本文记录 `codex/bim2text-research` 分支上 IFC2Text 第一阶段的实际实现、验证、样本结果和下一步边界。研究方向与长期架构仍以 [`../architecture/bim2text-bidirectional-bridge-research.md`](../architecture/bim2text-bidirectional-bridge-research.md) 为准；本文只记录已经发生的工程事实，不另立一套竞争方案。

## 1. 本轮目标

第一阶段先建立一个能够解释误差来源的往返基线：

```text
源 IFC
  → 确定性建筑事实
  → 可重建的设计说明
  → 现有 text2IFC
  → 重建 IFC
  → GUID 无关 Compare
```

本轮没有修改现有 text2IFC Generation 行为。重建端的边界固定为只接收设计说明，不接收源 IFC、source facts、源 GlobalId 或其他解析结果。

自进化、微调和跨建筑策略学习没有在本轮实现；只保留后续可以接入的事实、section 和 Compare 反馈结构。

## 2. 接手时核实结果

开始实现前重新读取了：

- 根目录 `AGENTS.md`；
- `docs/how-to/agent-takeover.md`；
- `docs/README.md`；
- `.planning/STATE.md`、`.planning/ROADMAP.md`、`.planning/PROJECT.md`；
- IFC2Text 架构方案；
- Agent/Provider 准入协议 `docs/validation/agent-capability-evaluation.md`。

现场 Git 分支为 `codex/bim2text-research`。工作树原本已经存在大量 Dataset、manifest 和文档修改，本轮没有 reset、clean、restore 或覆盖这些并行工作。

已有能力中可直接复用的主要部分是：

1. `src/text2ifc_extractor/`：IFC2X3 单位、placement、void/fill 等确定性读取；
2. `src/text2ifc_ifc_repair/geometry.py` 与 `index_adapters.py`：墙体、开口、门窗宿主坐标及 IfcSpace 几何读取；
3. `src/text2ifc_agent/interactive_cli_flow.py`：现有 text2IFC Design Brief → Generation 公共调用路径；
4. IfcOpenShell 0.8.5 与 Shapely 2.1.2：当前环境可用。

旧 `scripts/ifc_pipeline/` 中的 IFC→文本代码保留为历史参考，但没有作为新基线直接复用。它主要输出统计摘要，会截断构件明细，并存在依赖名称猜类别等信息损失，不满足可重建说明要求。

## 3. 新增实现

### 3.1 面向描述的建筑事实

新增 `src/text2ifc_ifc2text/facts.py`，产生 `text2ifc/ifc2text-facts/0.1`。

当前事实范围包括：

- IFC Schema、单位与统一世界坐标约定；
- BuildingStorey 名称与标高；
- 墙体中心轴、长度、厚度、高度、世界几何范围；
- Door / Window 名义宽高、世界位置、Opening 与宿主墙关系；
- Opening 尺寸、沿宿主墙位置和底部标高；
- IfcSpace 名称、几何范围和可用的 IfcRelSpaceBoundary；
- IfcStair 及其可测量分解构件的几何高度范围；
- 每个提取失败、空间推导失败或暂不支持项。

所有数值来自 IFC 直接字段或 IfcOpenShell 几何计算。语言模型没有补事实的接口。

墙体测量有两条路径：

1. 优先复用已有显式两点 Axis + 几何厚度/高度测量；
2. 对没有显式 Axis 但具有可处理实体几何的长直墙，从世界坐标 mesh 的平面主轴计算中心轴，并明确记录 `measurement_method=world_mesh_principal_axis`。

第二条路径是在真实离线测试中发现的必要补充：现有编译器生成的合法墙体并不保证带 repair 模块所要求的显式 Axis。如果只接受显式 Axis，则“同一设计独立重新编译”也无法作为 Compare 基准。

### 3.2 无 IfcSpace 的保守空间推导

当前第一版不是通用 room recognition，而是一个清楚受限的几何 baseline：

- 只使用可测量的直墙中心轴；
- 用墙厚的一半加小范围 snap tolerance 延伸普通墙角端点；
- polygonize 得到封闭区域；
- 设置最小面积过滤；
- 得到的结果只称为 `derived_enclosed_region`；
- `semantic_use` 固定为 `unknown`，不根据形状猜卧室、走廊等用途；
- 无法闭合时返回推导 issue，继续输出墙体、门窗和开口，不强行造房间。

这里端点延伸只为处理常见“墙中心轴止于相交墙表面而非另一墙中心线”的建模方式，不允许用长距离补线修复真实开放区域。

### 3.3 固定设计说明 baseline

新增 `src/text2ifc_ifc2text/description.py`。当前 deterministic baseline 使用：

```text
整体概况
→ 楼层
  → IfcSpace / 几何推导区域
  → 墙体
  → 门窗与开口
  → 楼梯与跨层构件
→ 读取限制
```

说明不输出源 GlobalId。没有真实北向时只使用 IFC 世界坐标、X/Y 和墙局部轴线，不把坐标轴擅自翻译为东南西北。

### 3.4 重建 Truth Boundary

新增 `src/text2ifc_ifc2text/text2ifc_public.py`。

桥接函数只有设计说明文本作为建筑输入，然后进入现有：

```text
SessionStore
→ run_design_brief_clarification_loop
→ run_ready_session_to_ifc
```

函数签名没有 source IFC / source facts 参数。roundtrip manifest 同时明确：

```text
reconstruction_receives:
  - design-description.md

reconstruction_must_not_receive:
  - source IFC
  - source-facts.json
  - source GlobalIds
```

本轮已经验证该边界的离线调用 seam，但没有执行新的真实 Provider 调用。

### 3.5 GUID 无关 Compare

新增 `src/text2ifc_ifc2text/compare.py`。

与 repair comparator 不同，本比较器不假设源模型和重建模型保留相同 GlobalId。当前流程为：

1. 两个 IFC 分别重开、分别抽取描述级事实；
2. 可选一次整栋全局 translation 对齐；
3. 按楼层标高匹配楼层；
4. 在同楼层内按几何位置、墙方向和尺寸一对一匹配墙、门、窗、Opening；
5. 在墙几何建立跨模型对应后，再核验 Door / Window / Opening 的 host-wall 关系；
6. 分开报告 missing、extra、position / dimension deviation 和 relationship difference。

当前不允许为每个构件单独平移以提高分数。

比较状态明确分开：

- `files_readable`；
- `geometry_processable`；
- `reconstruction_consistent`。

### 3.6 Roundtrip 产物

新增 `src/text2ifc_ifc2text/roundtrip.py` 和 `scripts/ifc2text/run_baseline.py`。

每个样本当前至少可保留：

```text
source-facts.json
design-description.md
roundtrip.json
compare.json        # 有 reconstructed IFC 后生成
```

当前真实样本准备结果位于：

`dataset/processed/experiments/ifc2text-phase1-20260916/`

它们是 development / experiment artifacts，不是 accepted Proof。

## 4. 首轮真实样本

本轮没有只挑最容易模型，而是同时保留可成功和失败的空间推导样本。

### 4.1 `hxp.ifc`：有 IfcSpace 的常规三层建筑

路径：`dataset/external/bimnet/hxp.ifc`

当前抽取：

- 3 层；
- 5 个明确 IfcSpace；
- 34 面墙；
- 7 扇门；
- 3 扇窗；
- 15 个 Opening。

事实与说明均已生成。部分没有 IfcSpace 的楼层继续尝试几何推导；墙体不足时明确返回 issue。

### 4.2 `i5n.ifc`：多层、门窗和楼梯

路径：`dataset/external/bimnet/i5n.ifc`

当前抽取：

- 3 层；
- 1 个明确 IfcSpace；
- 22 面墙；
- 6 扇门；
- 8 扇窗；
- 15 个 Opening；
- 1 个 IfcStair。

发现 IfcStair 自身 `Representation` 可为空，但其 `IfcStairFlight`、Landing 和 Member 分解构件具有几何。因此 baseline 已扩展为优先读取 Stair 自身，失败后组合实际分解构件 bounds，再记录几何覆盖的楼层范围。这个范围不能自动解释成语义上的“可通行连接”。

### 4.3 `1px.ifc`：无 IfcSpace 的空间推导正例

路径：`dataset/external/bimnet/1px.ifc`

源模型没有 IfcSpace。当前第一层从墙体几何得到 6 个封闭区域，均保留为用途未知的几何推导区域；第二层墙体证据不足，没有强行补造区域。

这证明第一版推导可以处理一部分常见封闭布局，同时保持 fail-closed。

### 4.4 `Type 5.ifc`：无 IfcSpace 的困难反例

路径：`dataset/external/european-lca-typical-buildings/20260916/Type 5.ifc`

当前：

- 2 层；
- 0 IfcSpace；
- 9 面墙；
- 6 扇门；
- 8 扇窗；
- 14 个 Opening。

墙中心轴当前无法构成可信闭环，因此没有生成房间，只输出构件布置。这一失败结果保留，不把空间推导失败伪装成正确。

该模型完整抽取约 90 秒，明显慢于 `hxp` / `i5n` 的几秒级结果。文件大小和墙数量不足以预测 tessellation 成本。下一步底层性能优化应优先考虑形状缓存和一次 tessellation 多处复用，而不是简单扩大 timeout。

## 5. Compare 的独立故障注入验证

测试使用项目自身 BIM JSON 编译器生成相互独立的 IFC 文件，没有修改源 IFC。

已经验证：

1. 同一个 BIM JSON 独立编译两次：Compare 可判为一致；
2. 删除 Door 及其 Fill 关系：Door 被报告为 missing；
3. Window 整体移动：报告位置 deviation；
4. Window 宽度与几何同时修改：报告尺寸 deviation，而不是被误归类为 missing + extra。

构件 matching 和 acceptance 被刻意分开：一个位置相同但宽度变化较大的窗仍应先匹配为“同一个几何角色候选”，随后报告尺寸错误。

## 6. 下一步描述端：版本化提纲—分段—合并

真实调用前先固定第一版 Prompt contract。

### 6.1 为什么采用总—分—总

当前采用：

```text
总：建筑整体、坐标/单位/层数/阅读基准
分：逐楼层 → 空间/区域 → 墙 → 门窗/开口 → 跨层构件
总：跨层组织、覆盖情况、明确限制
```

它适合当前任务，但不能让最后一步重新生成全文，否则最后一次模型调用可能再次改尺寸、改坐标或遗漏构件。

因此实现拆成：

```text
Outline Agent
  → 为每个 section 分配 allowed_fact_refs / required_fact_refs / primary ownership

Section Writer
  → 每次只看到当前 section 允许的事实
  → 输出 text + used / omitted / unresolved fact refs

Merge Agent
  → 只给 section_order、短过渡、closing_summary、limitations

Deterministic Assembler
  → 原样拼接已经完成的 section text
  → required fact 被遗漏时 fail closed
```

新增 `src/text2ifc_ifc2text/writing.py`：

- `build_fact_index()`：把 source facts 投影为 prompt-safe 本地 fact refs，去掉 source GlobalId / source path；
- `assemble_sectioned_description()`：按 merge order 原样拼 section，不接受“重写主体”的字段；required fact 静默遗漏时直接阻断。

### 6.2 Prompt 版本

第一版模板登记到现有 `prompts/agent/registry.json`：

| Template ID | 文件 | 作用 |
|---|---|---|
| `ifc2text-outline.v0.1` | `prompts/agent/ifc2text/ifc2text-outline-v0.1.md` | 提纲与事实 ownership |
| `ifc2text-section-writer.v0.1` | `prompts/agent/ifc2text/ifc2text-section-writer-v0.1.md` | 有界分段写作 |
| `ifc2text-merge.v0.1` | `prompts/agent/ifc2text/ifc2text-merge-v0.1.md` | 顺序、过渡与结尾总结，不改写主体 |

对应机器合同：

- `schemas/ifc2text/outline-0.1.schema.json`；
- `schemas/ifc2text/section-0.1.schema.json`；
- `schemas/ifc2text/merge-0.1.schema.json`。

版本规则沿用仓库合同：已经登记并参与运行的版本不原地改写。Prompt 行为需要改变时新增 `v0.2` 等版本，并同步更新 registry hash 与针对性测试。

IFC2Text 版本号独立于 Generation `design-brief.v2.x`、`bim-json-generator.v*`，避免把不同角色混成一条版本序列。

## 7. 当前验证

最新聚焦命令：

```powershell
.\.venv\Scripts\python.exe -m pytest \
  tests/ifc2text/test_baseline.py \
  tests/ifc2text/test_prompt_pipeline.py \
  tests/agent/test_prompt_registry.py \
  -q --basetemp=.ifc2text-pytest-phase1e -p no:cacheprovider
```

结果：**20 passed**。

覆盖内容包括：

- IFC2Text facts / description；
- 无 IfcSpace 的正常墙角小间隙闭合；
- Truth Boundary；
- GUID 无关 Compare 的相同、缺门、窗位移、窗尺寸变化；
- 三个 IFC2Text Prompt 的 registry hash 与渲染；
- Outline / Section / Merge JSON Schema；
- fact index 不暴露 source GlobalId；
- deterministic merge 不接受主体重写；
- required fact 遗漏时 fail closed；
- 现有 Prompt registry 历史 hash 回归。

没有运行 Full Preflight。

## 8. 当前没有做的事情

### 8.1 新的真实 Provider 往返尚未执行

仓库 `STATE.md` 已明确说明旧 Generation admission 只是历史快照，新调用必须重新判断准入。IFC2Text 新增了新的 outline / section / merge Agent stage，因此不能直接把旧历史运行当成当前 Stage Admission。

本轮没有因为 `.env` 或 API key 存在就绕过这一门禁，也没有调用真实 Provider、消耗新的 Generation 预算或声称已经得到真实重建 IFC。

因此当前真正成立的是：

```text
真实源 IFC
→ 确定性 facts
→ deterministic baseline design description
→ text2IFC 公共路径接口已接通（离线 seam）
→ GUID-independent Compare 已独立验证
```

还不能写成：

```text
真实源 IFC
→ LLM 分层说明
→ genuine text2IFC Provider reconstruction
→ reconstructed IFC
→ real roundtrip comparison PASS
```

后者要在新的当前 Stage Admission 和本次预算授权满足后执行。

### 8.2 空间推导仍是 baseline

当前只证明简单直墙闭合策略有正例，并有真实失败反例。还没有证明：

- 多高度切片优于墙中心轴；
- 门洞辅助分区在真实样本上的准确率；
- 复杂开放空间、错层和通高空间；
- derived region 对应人工房间 truth 的准确率。

不能用当前推导结果自身证明房间正确。

## 9. 下一步建议顺序

在不改变既定研究方向的前提下，建议下一步按以下顺序继续：

1. 为新的 IFC2Text outline / section / merge stage 建立适用的 zero-network Stage Admission，复用现有 Provider seam 和 public Generation path，但不触发 Full Preflight；
2. 用 deterministic fake / frozen replay 验证完整“facts → outline → sections → deterministic merge → Design Brief → Generation”链路的正常、遗漏事实、schema-invalid、截断和失败路径；
3. 明确本轮真实 Provider 调用预算后，先对一个有 IfcSpace 的小模型做 genuine 往返；
4. Compare 定位误差属于 parsing、space inference、description 还是 reconstruction；
5. 再跑多层建筑与无 IfcSpace 正/反例；
6. 根据真实误差决定优先优化空间推导还是描述表达，不提前实施自进化。

如果真实调用前需要修改既有 text2IFC Generation contract、Provider transport、预算规则或出现新的目标冲突，应在该点停下讨论；普通 IFC2Text 实现细节继续按代码和测试证据处理。

## 10. 提交前复核与声明收紧（2026-09-16）

最终 Merge 修改后重新运行 `tests/ifc2text` 与 `tests/agent/test_prompt_registry.py`，使用独立临时目录 `.pytest-tmp-ifc2text-20260916-f`；结果 20 passed，30.36 秒，无跳过。本次仅为聚焦回归，不是 Stage Admission 或真实模型调用。

本快照按开发基线提交，不按已完成能力提交。上文的“接通”仅指接口存在且 mock seam 测试通过；尚未有 facts→LLM提纲→正文→Generation 的完整运行器。`used_fact_refs` 等自报字段不能独立证明正文数值或语义正确。空间推导结果是轴线围合候选，不是已验证净房间；1px 的六个候选没有独立房间参照。Type 5 的失败来自端点延伸改动之前，不能当作最终算法的已复测反例。Stair 分解代码更新后，i5n 的旧产物也未重新生成。

比较器仍为诊断原型：当前全局平移估计、贪心匹配、未知尺寸及未分配楼层构件的计数需要补负例；其 `reconstruction_consistent` 不得直接当作整栋建筑保真验收。相同 BIM JSON 独立编译不自动证明 GUID 不同，后续需显式改 GUID 的测试。以上限制不会通过更改源模型、删去失败样本或放松容差消除。

Merge 合同最终以实际 Schema 为准：结尾总结是独立 section，Merge 不另造 `closing_summary` 正文；上文早期字段说明是历史设计过程。

已获得本轮 LLM 调用授权；执行前仍完成适用离线链路、记录模型/版本/预算上限并先提交代码。授权不等于已执行。Dataset、其他任务文档、临时目录、凭据和旧实验不纳入本任务提交。
