# Phase 12 Plan 07 结构恢复证据勘误与重新准入要求

日期：2026-09-03
状态：**Plan 07 的 Beam/Column damage-restoration 结论暂停使用，等待更换 fixture 后重新验证**

## 1. 结论

本次复核确认，Plan 07 的结构构件案例把两种不同目标混在了一起：

1. 测试系统能否按请求新增 Beam/Column；
2. 测试系统能否恢复 `damaged.ifc` 中被删除的 Beam/Column。

现有执行和 L0/L1/L2 主要证明了第一项，即生成结果符合请求；它们没有证明第二项。
离线 runner 和 live UAT 使用了与真实删除构件无关的远端占位坐标。系统随后忠实
执行这些请求，validator 又只检查 request conformance，因此位于建筑主体之外的
构件仍被判为 PASS。

这不是 Provider 随机漂移。直接错误位于 fixture/request；系统缺陷位于 Proof
缺少 damage-to-repair 绑定门。重复运行同一请求只会重复相同结果，不能形成新的
有效恢复证据。

本文件是追加勘误，不删除、不重写、不重新标注已有 genuine attempts 或 accepted
artifact。凡既有报告与本勘误的结构恢复结论冲突，以本勘误为准。

## 2. 已核对的证据链

### 2.1 真实损伤目标

`d7n.ifc` 的私有 mutation manifest 记录：

- 删除的 Beam `1RnWak0Kr6GxkeYF4Sd_bw` 位于 `Level 3`；可测 Storey-local
  axis 约为 `(-1339.985, 7503.972, 0)` 至
  `(-1339.985, 3283.972, 0)` mm。
- 删除的 Column `3dldEzenf9LvnDJYNNzLsH` 位于 `Level 1`；展开
  `IfcMappedItem` 后，其实体截面是 `IfcCircleProfileDef`，挤出深度约
  `2409.2 mm`。因此它被明确判定为圆柱，不属于当前 `add_column` 的直线矩形柱
  输入合同。

`vvo.ifc` 的私有 mutation manifest 记录：

- 删除的 Beam `17tPjyQtf2L9JnbXXmcTUF` 可测 Storey-local axis 约为
  `(-3316.630, -3863.523, 0)` 至 `(-3316.630, -8803.523, 0)` mm。
- 删除的 Column `1rsYNObuDC4euALdw6WUK4` 是矩形 `500 x 500`，但 Body 也是
  `IfcMappedItem`，当前诊断器无法得到满足恢复合同的显式 axis。

进一步扫描确认，VVO 的目标 Column 是 `500 x 500 mm` 矩形柱；Sixty5 结构模型中
也有可测的矩形柱，例如 `1DcFG7Zuf8FxTHX6fz74x3` 为 `500 x 800 mm`、挤出深度
`3700 mm`。但这些真实模型的柱普遍使用 `IfcMappedItem`，没有单独的显式 Axis
Polyline。当前资格检查把“必须存在显式 Axis 表示”当作前提，因而会把本可从
对象放置、映射变换、solid position、挤出方向和深度通用推导轴线的矩形柱也拒绝。

所以要区分两类问题：D7N 圆柱是 operation schema 不兼容，必须更换 IFC/目标；
VVO、Sixty5 的矩形柱是当前 extractor/eligibility 的通用映射变换能力缺口。在该能力
通过聚焦离线测试前，不得先制造新的柱损伤，更不能用手工坐标代替恢复事实。

### 2.2 请求和 operation 使用的坐标

`scripts/ifc_repair/run_phase12_offline.py` 当前固定使用：

| Case | 实际 operation 坐标 | 与删除目标的关系 |
|---|---|---|
| `phase12-d7n-beam-loadbearing` | `(100000, 100000, ...)` | 与 Level 3 被删 Beam 无关 |
| `phase12-d7n-column-loadbearing` | `(110000, 110000, ...)` | 与被删 Column 无关，且原目标几何不可重建 |
| `phase12-d7n-beam-column-atomic` | Beam 约 `(120000,120000)`；Column 约 `(123000,124000)` | 与两个被删目标均无关；Beam 还从 Level 3 改到了 Level 1 |
| `phase12-vvo-beam-material-present` | `(200000, 200000, ...)` | 与被删 Beam 无关 |
| `phase12-vvo-column-material-absent` | `(210000, 210000, ...)` | 与被删 Column 无关，且 axis 不可重建 |

`scripts/ifc_repair/run_phase12_live_uat.py` 的两条结构成功路径复用了同样的远端区域：

- `complete`：Beam 从 `(120000,120000,3000)` 到
  `(126000,120000,3000)`；Column 位于 `(123000,124000)`；
- `clarification-resume`：Column 位于 `(120000,120000)`。

intent、resolution、ChangeSet 和 repaired IFC 中的测量结果均沿用了 request 数值。
所以 applicator 没有擅自移动构件；错误坐标在进入 applicator 前已经被冻结。

### 2.3 为什么旧 Proof 会通过

现有 Beam/Column operation validator 验证的是：

- repaired 中的 axis/section 是否等于 operation frame；
- 构件是否被包含在指定 Storey；
- 是否建立指定 Type；
- 是否满足当前关系和 property 合同。

它没有验证：

- operation 是否对应 mutation manifest 中被删除的 role；
- Storey、axis、section、orientation、type/material/property 是否恢复原目标；
- 新构件是否处于建筑的合理空间范围；
- 声称“supported by”的 Beam 与 Column 是否实际相接；
- restoration case 是否真正关闭了 original → damaged → repaired 的差异。

因此旧 PASS 的准确含义是“按请求成功新增”，不是“成功恢复被删除构件”。

代码级复核还确认：现有 damage provenance audit 只证明“目标在 original 中存在、
在 damaged 中消失，且损伤可重放”；它没有把新建构件与该删除目标做恢复等价比较。
独立 private triplet audit 目前只在 Door operation 存在时进入，纯 Beam/Column 案例的
`independent_triplet_audit_publishable` 保持为空。这正是错误结果能够通过现有 Proof
的直接验证缺口。

## 3. Plan 07 逐案复核

### 3.1 Final-code 四案

| Case | 现有结果还能证明什么 | 不能再声称什么 | 处置 |
|---|---|---|---|
| `complete` | genuine Stage 1/1.5/2、atomic add、Type/property request conformance | Beam+Column damage restoration；物理位置合理；结构连接恢复 | **结构恢复证据无效**；更换 fixture/request 后重跑 |
| `clarification-resume` | offered property identity、clarification/resume、Column add request conformance | 被删 Column 恢复 | **结构恢复证据无效**；改用可支持的新 IFC/目标 |
| `window-semantic-canary` | 指定现有 Window 的 occurrence-only property authoring | Beam/Column 恢复；property private triplet restoration | 保留为 semantic/property UAT，不计结构恢复 |
| `program-guard` | unsupported atomic request 零 mutation、零 publish | 成功 repair | 保留为 no-output safety Proof；没有 `repaired.ifc` 是正确结果 |

四案因此不能再汇总成“三个结构修复成功 + 一个 guard”。更准确的分类是：两个结构
add/request-conformance UAT、一个 Window property canary、一个 no-output guard。

### 3.2 既有离线结构集合

以下五案均使用远端占位坐标，不能作为 damage-restoration Proof：

- `phase12-d7n-beam-loadbearing`
- `phase12-d7n-column-loadbearing`
- `phase12-d7n-beam-column-atomic`
- `phase12-vvo-beam-material-present`
- `phase12-vvo-column-material-absent`

`phase12-vvo-door-window-beam-column-atomic` 需要拆开解释：private mutation truth 只列出
两扇 Door、两扇 Window 及其 Window Opening，没有删除 Beam 或 Column。Door/Window
部分可以继续按其专用 comparator 审核；Beam/Column 只能算同一事务中的新增操作，
不能算结构构件恢复。

历史 `phase12-live-deepseek-complete` 和
`phase12-live-deepseek-clarification-resume` 使用相同 D7N damaged source 和相同远端
请求，因此受到同一勘误影响。append-only 证据保留，但不再作为结构恢复成功依据。

### 3.3 不受本问题直接否定的证据

- 60-case Stage 1.5 semantic evaluation 不执行 IFC placement，本次几何错误不直接
  否定它的 property selection 结果。
- `window-semantic-canary` 仍可作为 property authoring viability，但不是 private
  damage-restoration benchmark。
- `program-guard` 的零输出仍是正确安全结果。
- R1 12 案本来就声明合法 private triplet 为 0；它们可以继续证明冻结 request 的
  property/add/atomic execution 与 preservation，但不能填补 Plan 07 缺失的
  Beam/Column damage-restoration Proof。

## 4. IFC 更换规则

不得通过放宽 validator、猜测不可解析几何、使用远端占位坐标或增加样例特判来修补
现有案例。重新准入时，先扫描候选 IFC，再决定是否制造损伤。

一个 Beam/Column 只有同时满足下列条件，才能成为 restoration fixture：

1. IFC2X3 可稳定 reopen，source 保持不可变；
2. 目标属于当前生产能力：水平直线矩形 Beam 或竖直直线矩形 Column；
3. 在损伤前即可确定 Storey-local axis endpoints、section、orientation；
4. Type、material 和恢复所需 property 可以完整冻结；
5. 映射表示必须能经过完整 transformation 解引用；不能只看到内部
   `IfcExtrudedAreaSolid` 就假定 placement 已知；
6. 目标位于可解释的建筑范围内，且多构件案例的预期接触/支撑关系可以测量；
7. request 在运行前冻结，并精确描述要恢复的事实；private original/mutation truth
   只在 repaired 生成后由 evaluator 打开；
8. damage 后必须用 public damaged-only 路径确认目标确实缺失，且未破坏无关模型事实。

出现以下任一情况时，直接淘汰当前目标并更换 IFC 文件或更换同文件中的目标：

- 圆形、异形、斜向、曲线或变截面构件；
- axis、section、orientation 或 Storey placement 无法可靠恢复；
- `IfcMappedItem` 的完整变换无法由当前 extractor 解析；
- 原始构件语义超出当前 operation schema；
- 只能靠猜测或手工发明坐标才能构造 request。

具体到本次问题：

- D7N 圆柱永久退出当前矩形柱 restoration fixture；不得再次删除后用矩形占位柱
  替代。
- Sixty5 结构 IFC 作为优先替换候选，因为它包含大量矩形柱并具有清晰的结构模型
  语境；VVO 的 `500 x 500 mm` 矩形柱可以作为较小的备选。
- 替换不是立刻删除候选柱。必须先用通用的 mapped-transform 推导通过 Storey、世界/
  Storey-local axis、矩形 section、orientation 和 reopen preflight；该检查不得依赖
  某个 GlobalId、固定尺寸或文件名。
- 若通用 preflight 仍无法完整重建目标，本阶段应诚实记录 Column restoration
  `not_evaluated`，继续更换 IFC，而不是制造 PASS。

本次复核没有对 Sixty5 或 VVO 生成新 damaged IFC，也没有启动 repair：这是有意的
fail-closed 决定，用来避免在目标尚未可证明重建时再次制造错误基准。

## 5. 新 Proof 必须增加的阻断门

重新运行前，至少新增以下通用检查：

1. `RESTORATION_TARGET_RECONSTRUCTABLE`：损伤前目标的全部必需事实可提取；
2. `REQUEST_BOUND_TO_DAMAGE_ROLE`：private evaluator 确认请求/expected operation 与
   mutation role 一一对应；
3. `REPAIRED_CLOSES_DAMAGE_DELTA`：repaired 恢复相应 role 的几何、Storey、语义和
   必需关系，而不只是匹配 request；
4. `PLACEMENT_WITHIN_MODEL_CONTEXT`：新构件没有落在与建筑主体脱离的占位区域；
5. `STRUCTURAL_RELATION_MEASURED`：请求声称支撑/接触时，必须测量关系；
6. add-only、property-only、restoration 和 no-output 四类结果分别报告，不能互相
   代替；
7. 任何门失败时不得安装 accepted Proof，也不得据此关闭 Beam/Column restoration。

这些检查只针对本次已经发生且可合理再次发生的风险，不要求无差别重跑全部 curator。

## 6. 后续执行顺序

1. 保留所有旧 run 和 Proof，不删除、不重标；
2. 将旧结构案例视为 request-conformance 历史证据，不再视为 restoration authority；
3. 离线扫描候选 IFC，淘汰不支持的圆柱/映射表示/不可解析 placement；
4. 选定新的矩形 Beam 和 Column fixture，冻结原始几何与语义；
5. 先写会让现有远端占位案例失败的聚焦测试，再实现通用 restoration gates；
6. 生成新的、版本化 damaged fixture 和 request，不覆盖旧版本；
7. 通过 focused offline、reopen、damage-delta、preservation 和 private triplet
   comparator 后，才允许一次新的 genuine Provider run；
8. 重新撰写 Plan 07 Proof Matrix，并据真实结果决定 Phase 12/12.1 的结构恢复结论。

在上述工作完成前，Plan 07 的 Beam/Column **新增能力**可以按现有证据讨论，但
Beam/Column **损伤恢复闭环**不得标为 CLOSED。
