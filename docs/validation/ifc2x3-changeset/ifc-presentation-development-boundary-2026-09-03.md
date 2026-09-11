# IFC Presentation Development Boundary

> 接续计划：[Type、材质、属性和外观计划](../../architecture/semantic-appearance-plan.md)。已定稿范围：Type 按需在当前项目内组织，增加小型内置参数化模板与 Generation 基础门窗细节；Repair 保留原几何，模板不默认补写材料或性能属性，不实现跨 IFC 参照。下文保留第一阶段边界和已完成验证，后续离线实施与验证记录见该计划第 11 节，不覆盖本页历史边界或声称真实 Provider 能力提升。

状态：**FROZEN FOR IMPLEMENTATION**

日期：2026-09-03
适用范围：IFC2X3 Generation appearance 与 Repair visual fidelity 的第一阶段实现。

## 1. 目标

本轮只新增/修复 IFC presentation 能力，不重写 Generation 或 Repair 主链。

共享底层能力可以包含：

- `IfcSurfaceStyle` / `IfcSurfaceStyleShading` 创建；
- Material-owned style 绑定；
- representation item style 的只读检查与必要 override；
- appearance authority inspection；
- appearance fingerprint；
- deterministic appearance profile resolution。

Generation 与 Repair 只共享这些 IFC presentation primitives，不共享策略优先级。

## 2. Generation 冻结边界

Generation 目标是 **create appearance authority**。

冻结优先级：

```text
1. 用户明确指定颜色 / 风格
2. 用户明确指定 AppearanceProfile
3. LLM 从允许的 profile / palette 集合中选择
4. seeded deterministic variation
5. default profile
```

第一阶段实现约束：

- 不修改 Agent 主循环；
- 不修改现有 BIM JSON 2.0 schema；
- 不要求 LLM 输出原始 RGB；
- 不增加 token-dependent random RGB；
- 不改变现有 occurrence geometry contract；
- `text2ifc_compiler.relationships.add_v2_relationships()` 中 `assign_type(..., should_map_representations=False)` 保持不变；
- appearance 由 compiler/presentation policy 在已有 geometry/material 之后确定性附加；
- 同一次生成应使用一个协调的风格主题，但不同 material / component role 可以有不同颜色；
- seeded variation 只能在预先定义的 palette/profile 集合中选择，不允许任意 RGB 随机；
- 用户显式选择始终覆盖 profile/LLM/seeded variation。

第一阶段可以先覆盖现有 compiler 已有 Material 的构件；丰富 Window/Door 几何是后续独立 commit，不与基础颜色 authoring 混合。

## 3. Repair 冻结边界

Repair 目标是 **preserve / resolve existing appearance authority**，不是美化 source IFC。

冻结优先级：

```text
1. exact Type appearance authority
2. explicit user appearance
3. authorized existing/reference appearance
4. none
```

解释：

- 当用户明确要求 exact Type，且该 Type 存在可解析的 appearance authority 时，Type 优先；
- 用户同时给出冲突颜色时，不覆盖 Type appearance，并应在后续 appearance evidence 中记录冲突原因；
- exact Type 没有 appearance authority 时，才允许显式用户 appearance 生效；
- 没有 Type authority、用户 appearance 或授权 reference appearance 时，不猜颜色；
- Repair 禁止使用 Generation 的 demo/colorful profile 自动美化已有模型。

第一阶段实现约束：

- 不修改 Repair Prompt；
- 不覆盖任何已发布 Repair Intent / ChangeSet schema；
- 第一阶段先完成 existing Type/material/style fidelity；
- “用户明确指定颜色”的完整自然语言能力留给新的版本化 appearance intent / changeset contract；
- 不把颜色偷偷编码为现有 `material` 字段；
- 不修改 source IFC；
- 不降低 audit、transaction、reopen、L0/L1/L2、preservation 门禁；
- 不修改历史 accepted R1 Proof；只能新增 regression / validation evidence。

## 4. Representation authority 冻结规则

### 4.1 Window / Door

不能使用简单规则 `RepresentationMaps exists -> always map`。

IFC2X3 `IfcWindowStyle` / `IfcDoorStyle` 的 `ParameterTakesPrecedence` 决定精确几何 authority：

```text
ParameterTakesPrecedence = FALSE
    -> style RepresentationMaps 是 exact representation authority

ParameterTakesPrecedence = TRUE
    -> attached lining/panel parameters 是 parameter authority
```

因此 Window/Door 后续修复必须先分类 authority，再决定 mapped representation 或 parametric representation。

Generated/fallback Window/Door 后续应迁移到 IfcOpenShell 专用：

- `ifcopenshell.api.geometry.add_window_representation()`
- `ifcopenshell.api.geometry.add_door_representation()`

但该丰富几何改动与本轮 shared presentation primitives 分 commit 实施。

### 4.2 Beam / Column

Beam/Column 不允许为了 appearance 无条件 map Type 的完整 representation。

同一 Type 下 occurrence 长度可以不同，因此冻结规则：

```text
full representation proven occurrence-invariant
    -> mapped representation 可用

section/profile shared but occurrence length varies
    -> 保持 occurrence-specific parametric extrusion
    -> appearance/material 从 Type authority 复用
```

任何 appearance 修复不得改变请求的 axis、length、section、placement、Storey。

## 5. Style ownership 冻结规则

优先使用 IFC/IfcOpenShell 推荐的 Material-owned style：

```text
IfcMaterial
  -> IfcMaterialDefinitionRepresentation
  -> IfcStyledRepresentation
  -> IfcSurfaceStyle
```

直接挂在 representation item 上的 `IfcStyledItem` 视为更具体的 representation override；Repair 读取时必须能够识别，但 Generation 默认不以 item-style 作为第一选择。

第一版视觉表达采用 IFC2X3 兼容规则：普通不透明颜色优先使用 `IfcSurfaceStyleShading.SurfaceColour`；只有需要透明度时才使用其子类 `IfcSurfaceStyleRendering` 的 `Transparency`。不要把 IFC4 才新增到 `IfcSurfaceStyleShading` 的 `Transparency` 属性写进 IFC2X3。第一版不引入复杂 PBR/material rendering。

## 6. 不变量 / Regression Gates

任何实现必须保持：

### Generation

- BIM JSON 输入 validation 行为不变；
- geometry dimensions / placement 不变；
- material layer semantics 不变；
- type relationship 行为不变；
- compile -> temporary write -> reopen -> verify -> atomic publish 不变；
- 同输入 + 同 profile + 同 seed 结果必须 deterministic。

### Repair

- source hash 前后相同；
- ChangeSet audit 和 transaction atomicity 不变；
- existing Type GlobalId 不变；
- Type authority fingerprint 不被非法修改；
- geometry / placement / Storey 既有 postconditions 不回退；
- reopened IFC2X3 才能进入 evaluation；
- failed candidate 不得 promoted；
- existing accepted Proof append-only。

## 7. Test-first 顺序

冻结实施顺序：

```text
A. Shared presentation primitive tests (RED)
B. Repair exact-Type appearance preservation tests (RED)
C. Generation deterministic appearance profile tests (RED)
D. Implement minimal shared presentation layer
E. Connect Repair without changing geometry authority
F. Connect Generation compiler without changing Agent/schema
G. Focused tests
H. Existing Generation + Repair baseline regression
I. Offline public-path validation
J. Deterministic preflight
K. Live Provider validation only after all blocking gates PASS
```

Live Provider 不是 deterministic code debug 手段。任何 blocking offline/preflight failure 都禁止网络 transport。

## 8. Git / Commit Boundary

推荐最小提交边界：

```text
1. docs(presentation): freeze generation and repair appearance boundaries
2. test(presentation): add shared and repair/generation regressions
3. feat(presentation): add IFC2X3 presentation primitives
4. fix(repair): preserve exact-type appearance authority
5. feat(generation): add deterministic appearance profiles
6. test/validation: offline + live evidence
```

Window/Door rich geometry (`add_window_representation` / `add_door_representation`) 若本轮尚未需要，不与上述基础 presentation 提交混合。

## 9. 官方依据

- IfcOpenShell 0.8.5 `style.assign_material_style`: Material style 为推荐路径；representation direct style 优先于 material style。
- IfcOpenShell 0.8.5 `style.add_surface_style`: `IfcSurfaceStyleShading` 足以表达基础 colour/transparency。
- IfcOpenShell 0.8.5 `type.assign_type`: 默认会 map Type representations，但允许 `should_map_representations=False` 由应用自行管理。
- IfcOpenShell 0.8.5 `type.map_type_representations`: 用于确保 occurrence 与 Type representation 一致。
- IfcOpenShell 0.8.5 `geometry.add_window_representation` / `add_door_representation`: 提供专用参数化门窗 representation。
- buildingSMART IFC2X3 `IfcDoorStyle` / `IfcWindowStyle`: `ParameterTakesPrecedence` 决定参数或 style representation 哪一个是 exact geometry authority。

## 10. 2026-09-07 Git 接续状态

Repair 已有三个真实成功案例：exact Type 复用、显式颜色与 Material 恢复、Window/Door/Beam/Column 混合事务。中文与机器入口统一为 [presentation-cases](../../../dataset/processed/proof/repair/phase12/presentation-cases/REPORT.md)。此集合仍 pending_human_review；既有 live 成功不等于本次全部回归或系统能力通过。

本次提交共享 IFC2X3 style/material primitives、repair exact-Type appearance priority、Intent 0.9 / Prompt v0.12、Bound ChangeSet 0.6 / Draft 0.4 与回归。发现工作树曾原地改写已注册 ChangeSet Prompt v0.5：其原字节和哈希现已保留，appearance 指令新增到 v0.6，只有 appearance 路径选择新版本。冻结 live artifacts 里的旧模板 ID/hash 保持历史事实；本次没有用新 v0.6 发起真实调用，不能把旧 live 结果当作 v0.6 的真实验证。

Generation 已有 opt-in compiler appearance_profile / appearance_seed 参数、有限 palette 和确定性样式测试；它只证明编译器基础接入。自然语言请求到 Type/Material/appearance 策略的完整 generation 公共链路、丰富门窗和跨规模验收仍未完成；没有关闭 Generation 阶段。

本次离线验证：

- Prompt、appearance、共享 primitives、generation profiles、结构 Type 保真、Provider 与 evaluator/query 聚焦集：111 passed。
- 现有 presentation 离线脚本通过：15 个 styled products、11 种颜色，同输入/seed 重开后样式签名一致；repair Type 外观复用且几何通过。IFC 文件整体哈希受生成元数据影响，不宣称字节确定性。
- 首轮受影响 repair/compiler 回归暴露的兼容性问题已定位并修复：无 appearance 的 compact 请求继续使用原 Draft 0.2；精确映射 Type 的多色子构件保持原表示，不扁平覆盖；无外观请求不增加 `appearance: null`，保持既有独立重算结果。新增对应正负回归，未放宽 curator。
- 旧四类事务测试改为引用已整合 Proof 的现有字节。旧 Plan07 基础案例从 Git 恢复到 `tests/ifc_repair/fixtures/historical-plan07-base/`：21 文件、11,094,791 字节，逐文件与恢复清单核对。其 sidecar 明确 `withdrawn_historical_regression_fixture`；仅用于离线绑定、防篡改和 curator 接口回归，原报告中的 PASS 不重新成为有效恢复证据。原始文件未改写；测试临时副本在核对源哈希和大小后适配现行 BIMNet 路径。
- 最终受影响范围复测为 291 passed、1 failed；唯一失败是旧测试仍要求已撤销的 D7N restoration fixture 成功。依据已发布的 [结构恢复勘误](phase12-plan07-structural-restoration-erratum-2026-09-03.md)，将该项改为精确断言 `STRUCTURAL_MUTATION_TARGET_NOT_RECONSTRUCTABLE:beam` 且独立通过数为零，保留合法结构 Proof 的正向重算测试；不修改 validator 或阈值。 修正后正负两项复测均通过（2 passed、40 deselected，33.98 秒）。此前 291 项通过结果仍适用于未变动代码；没有再次运行整个 292 项集合。
- Python 改动静态解析通过。本次无 Provider、Full Preflight 或新的 Phase 验收。

下一步顺序：补 Generation 的请求到 Type/Material/profile 选择、编译/reopen、几何和样式不变量矩阵。来源扩展可独立继续，不作为已有数据上 Generation 开发的前置条件。

工作树整理：已存在的源码误暂存删除已解除；三个 presentation 成功包的重复暂存副本退出本次提交，保留现有 Proof。清理本次已结束的 10 个 `.tmp/two-lines-*` 测试目录，共 2,839 文件、682,032,211 字节（650.44 MiB）；可通过相应离线测试重新生成，测试日志保留。原始 genuine runs、来源进程工作区及 ifc-bench 子模块的两项本地删除保持未提交，不把它们误报为干净工作树。
