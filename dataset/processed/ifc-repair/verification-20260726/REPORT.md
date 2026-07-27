# Window Repair 多 IFC 回归报告（2026-07-26）

## 总结

本轮完成了一次新的真实 DeepSeek 单窗端到端实验，并对 vvo、AdvancedProject 和 px4 执行了五窗批量损伤与原子修复。四条正式链路均有可发布 IFC；所有成功链路的 Production L1/L2 通过，批量链路的私有 Ground Truth L1/L2 也通过。

| IFC | 规模 | Provider 模式 | 操作 | 结果 |
|---|---:|---|---:|---|
| LargeBuilding | 20,735 entities | 真实 DeepSeek | 1 Window | 成功 |
| vvo | 48,935 entities | 离线确定性 Provider | 5 Windows | 成功 |
| AdvancedProject | 770,172 entities | 离线确定性 Provider | 5 Windows | 成功 |
| px4_1 | 501,401 entities | 离线确定性 Provider | 5 Windows | 成功 |
| BasicHouse | 52.7 MB 文件 | mutation preflight | 5 Windows | 安全拒绝 |
| 7y3_1 | 9 MB 文件 | 离线确定性 Provider | 5 Windows | Ground Truth 空间关系冲突 |

“离线确定性 Provider”用于验证索引、解析后的结构化意图、统一 ChangeSet、编译器、原子发布和 L1/L2，不代表真实 LLM 调用。真实 Provider 证据只来自 LargeBuilding r22。

## 成功链路

### 1. LargeBuilding：真实 DeepSeek 重复实验

- 运行：`../phase10.5-window-fidelity-live-20260726-r22/`
- 人工案例：`../../proof/ifc-repair-success-cases/window/single/largebuilding-r22-repeat/REPORT.md`
- Stage 1：1 次调用成功
- Stage 2：1 次调用成功
- synthetic fallback：false
- Production：L1/L2 passed
- Private Ground Truth：L1/L2 passed
- 被删除 Window：`M_Fixed:0915 x 1830mm:354395`

### 2. vvo：五窗原子修复

- 运行：`vvo-five-window/`
- 状态：`succeeded`
- Production 和 Private Ground Truth：5/5 L1/L2 passed
- 被删除 Window：
  - `固定:500x1180:279940`
  - `固定:870x2370:255906`
  - `四开落地窗:4500x2950:253321`
  - `固定:1600x600:287667`
  - `固定:1600x600:287848`

### 3. AdvancedProject：770,172 实体

- 运行：`advancedproject-five-window-r4/`
- 状态：`succeeded`
- Production 和 Private Ground Truth：5/5 L1/L2 passed
- 大模型全量 preservation/diff 成功完成
- 被删除 Window：
  - `BALANS Fixed Single Window:BALANS 10M FLOOR (SH = 0):916922`
  - `BALANS Fixed Single Window:BALANS 10M FLOOR (SH = 0):919838`
  - `BALANS Fixed Single Window:BALANS 10M BATHROOM:960189`
  - `BALANS Fixed Single Window:BALANS 20M FLOOR (SH = 0):773593`
  - `BALANS Fixed Single Window:BALANS 30M FLOOR (SH = 0):781498`

该运行的正向链路和 Private GT 已成功。旧 wrapper 只在成功后的负例断言中停止；负例逻辑已修复，并由最终 584 项回归和 px4 r7 的原子回滚覆盖。

### 4. px4：501,401 实体与同墙上下叠窗

- 运行：`px4-five-window-r7/`
- 状态：`succeeded`
- Production 和 Private Ground Truth：5/5 L1/L2 passed
- 负例：人为制造同位置 Opening 后，整批拒绝且不发布部分 IFC
- 被删除 Window：
  - `固定:840x1775:237502`
  - `固定:370x370:249432`
  - `固定:370x370:249553`
  - `塑钢窗-三扇中固定:DSC2415:266052`
  - `固定:1100x1875:289339`

本案例推动两个必要修复：

1. Opening overlap 从一维水平区间改为墙面二维矩形相交；
2. duplicate-chain 判断加入窗台高度，允许同一水平位置的上下叠窗。

## 未通过但必须保留的边界

### BasicHouse：损伤阶段拒绝

`remove_windows_and_openings_batch` 检测到 `MUTATION_TARGET_REGION_NOT_CLOSED`。这表示删除 Opening 后宿主墙的几何体积没有按预期闭合，损伤夹具无法证明自己生成了可信 damaged IFC，因此流程在 Provider 前停止。没有发布伪造的修复结果。

### 7y3_1：原始 Ground Truth 自身楼层冲突

修复结果的几何、墙关系、Pset 和 Quantity 可通过，但四个原 Window 的直接空间 containment 与宿主墙不一致：

| operation | 宿主墙楼层 | 原 Window 楼层 |
|---|---|---|
| 001 | 标高 3 | 标高 6 |
| 002 | 标高 3 | 标高 6 |
| 003 | 标高 3 | 标高 3 |
| 004 | 标高 3 | 标高 6 |
| 005 | 标高 3 | 标高 2 |

系统选择把新窗放回宿主墙所在楼层，因此 Production L1 正确，但 Private GT 的 `window.storey` 不一致。复制源文件的错误 containment 会破坏 L1，不应为了 Ground Truth exactness 放宽规则。

### px4 原 A70 选择：源 occurrence 自身越出洞口

早期选择的三扇 `嘉寓A70系列铝合金内开窗` 在原 IFC 中，其 mapped geometry 已向洞口下方伸出约 289 mm。修复器忠实复用该 Type 后也被 L1 `window.geometry-fit` 拒绝。正式 r7 改选了原始几何有效、删除后仍有 surviving Type 的五条链路。

## 代码与测试

本轮新增或修正：

- occurrence-direct 标量 Pset 与 Window/Opening Quantity 的完整投影和 authoring；
- 多 operation 自定义属性一次确认、统一授权；
- 数值单位物理等价比较；
- Window 与 Opening 同名 Quantity 的 scope 隔离；
- mapped Window 允许框体在墙厚方向合理突出，但 X/Z 必须物理匹配；
- 同墙 Opening 的二维相交审计；
- 上下叠窗的 duplicate-chain 正确识别。

最终回归：

```text
584 passed, 1 skipped in 326.29s
```

## Door 准入判断

Window 主链路已具备：

- 真实 Provider 的单窗端到端成功证据；
- 3 个不同 IFC 的五窗批量原子化成功；
- 50 万和 77 万实体级模型验证；
- Pset/Quantity、Type 复用、二维冲突和原子回滚；
- 对无效 damaged fixture、错误 Ground Truth 和异常 Type 几何的 fail-closed 边界。

因此可以进入 Door 的 operation adapter 设计与最小实现，但应继续把 BasicHouse mutation closure 和源 IFC 数据质量诊断作为 Window 的已知边界，而不是宣称任意 IFC 都已支持。
