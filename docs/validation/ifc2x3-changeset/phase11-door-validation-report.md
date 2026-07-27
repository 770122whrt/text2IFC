# Phase 11 Door / Opening 验证报告

> 日期：2026-07-28  
> 当前结论：离线实现与真实 IFC 验证通过；真实 DeepSeek UAT 尚未执行。  
> 外部阻塞：Codex 执行额度层拒绝网络命令，Provider 实际调用数为 0。

## 1. 阶段目标

Phase 11 将已经验证过的 Window 修复链路扩展到三类操作：

1. 只在直墙上创建 Opening；
2. 在直墙上同时创建 Opening 和 Door；
3. 向一个已存在、尚未填充的 Opening 中安装 Door。

三类有洞口的构件共用一个 wall-local hosted-opening 核心，同时保留各自的
参数、Type、语义与验证策略，没有复制一套 Window 管线。

## 2. 完整链路

```mermaid
flowchart LR
    A["IFC2X3 + 用户文本"] --> B["Stage 1<br/>RepairIntent 0.5"]
    B --> C["选择 Prompt Profile"]
    C --> D["SQLite 索引与确定性解析"]
    D --> E["Semantic Manifest 0.3"]
    E --> F["Stage 2<br/>Bound ChangeSet 0.4"]
    F --> G["审计与原子化 IFC 写入"]
    G --> H["IFC 重开"]
    H --> I["L1 几何/关系/保全"]
    H --> J["L2 语义"]
    H --> K["Occurrence Fidelity 0.2"]
    I --> L["统一发布判断"]
    J --> L
    K --> L
```

LLM 负责理解请求并生成受约束的意图或草稿。以下工作由程序完成：

- IFC GlobalId 与文件指纹绑定；
- Target、Opening、Wall、Storey 和 Type 的确定性解析；
- Door/Opening 的几何与 IFC 关系创建；
- 生成 Type 的模板摘要校验；
- ChangeSet 审计、IFC 重开、L1/L2 和全局 preservation；
- 不支持能力的拒绝与原子回滚。

## 3. Prompt 路由

RepairIntent 0.5 的每个 operation 包含 `component_family`、`action` 和
`operation_profile`。

| Profile | 用途 |
|---|---|
| `window.add-with-opening` | Window 与新 Opening |
| `opening.add-to-wall` | 只创建墙洞 |
| `door.add-with-opening` | Door 与新 Opening |
| `door.fill-existing-opening` | Door 填入已有 Opening |
| `occurrence.set-properties` | 修改既有 occurrence 标量属性 |

Stage 1 只看到紧凑 Profile 目录；Stage 2 只加载本次 operation 选中的
contract 和 few-shot，避免把所有构件操作与例子一次性放入 Prompt。

## 4. Door 输入边界

当前阻塞参数是：

- 目标 Wall 或已有 Opening；
- Door 总宽与总高；
- Opening 宽、高与 sill；
- wall-local 中心位置；
- 支持的开启语义；
- 明确复用的 DoorStyle，或允许系统使用受控模板生成 Type。

材料、五金、上亮、门框细节和自定义 Pset 不是默认必需事实：

- 用户没有要求时，系统不生成；
- 用户明确要求且系统支持时，进入 semantic assignment；
- 用户要求但系统不支持时，由确定性能力检查拒绝；
- 不把不支持的细节交给 LLM 临时编造。

## 5. IFC 写入

### 5.1 Opening-only

`add_opening_to_wall` 创建一个 `IfcOpeningElement` 和一个
`IfcRelVoidsElement`。

它不会创建 Door、Window、`IfcRelFillsElement`、Door/Window Type 或
`IfcRelSpaceBoundary`。

### 5.2 Door + 新 Opening

`add_door_with_opening_to_wall` 创建或更新：

- Opening 与 void 关系；
- Door 与 fill 关系；
- Door 的 wall/opening-relative placement；
- Door 的 Storey containment；
- DoorStyle 绑定；
- 用户明确授权的 occurrence Pset/Quantity。

### 5.3 Door 填入已有 Opening

`fill_existing_opening_with_door` 要求：

- Opening 存在；
- Opening 只有一个宿主；
- Opening 尚未被填充；
- 请求或解析得到的 Wall 与实际宿主一致。

该操作保留原 Opening 与 void GlobalId，不创建第二个 Opening。

## 6. DoorStyle 策略

### 精确复用

用户明确指定且唯一解析到既有 DoorStyle 时：

- 新 Door 绑定该 Type；
- 复用 Type 的 RepresentationMap；
- 不修改 Type 的 formal attributes；
- 不复制其他 Door occurrence 的直接 Pset/Quantity；
- 不把源 occurrence 的错误 Storey 关系一并复制。

### 受控生成

没有复用 Type 时，当前只支持 `SINGLE_SWING_LEFT`、
`SINGLE_SWING_RIGHT` 和明确的 `NOTDEFINED`。

生成内容使用 `text2ifc-door-single-swing-template/0.1`。模板包含独立摘要；
若 formal operation、模板正文或摘要被篡改，应用阶段失败且不发布 IFC。

生成几何是可重复的简化 type-owned mapped panel，不代表门框、五金或材料事实。

## 7. 语义 scope

| Scope | 目标 occurrence |
|---|---|
| `window_occurrence` | `IfcWindow` |
| `door_occurrence` | `IfcDoor` |
| `opening_occurrence` | `IfcOpeningElement` |

公共写入器不再固定假设 Window。未知 scope、重复 scope 映射或缺少目标 role
会失败关闭。

真实 LargeBuilding 输出验证了：

- `Custom_Asset.AssetCode = D-001` 只写入 Door；
- `BaseQuantities.Width = 915 mm` 只写入 Opening；
- Type 复用没有复制源 Door 的 occurrence 属性包。

## 8. 验证门禁

### L1

Door L1 检查：

- Door 恰好填充一个 Opening；
- Opening 恰好 void 一个 Wall；
- Door 宽高与授权参数一致；
- Door 进入宿主墙的 Storey；
- Door 绑定 DoorStyle；
- 实际 IFC Root 变化均在授权角色内；
- IFC 可重开且不新增 validation diagnostics；
- damaged IFC 指纹保持不变。

### L2

Door L2 必需事实是 Type、host Wall、Storey、OverallWidth 和 OverallHeight。

显式 Pset、Quantity、Material 和 Classification 只有在用户文本或确定性策略
建立事实时才成为检查项。未请求事实报告 `not_required`。

### Occurrence Fidelity

新增 `text2ifc/ifc-occurrence-comparison/0.2`，记录 IFC class、scope、
application role、related Opening、attributes、effective scalar Psets、
quantities 与单位。Window 旧版 0.1 comparator 保持兼容。

## 9. 真实 IFC 离线结果

固定命令：

```powershell
.venv\Scripts\python.exe scripts\ifc_repair\run_phase11_offline.py
```

结果目录：

```text
dataset/processed/ifc-repair/phase11-door-offline/
```

### LargeBuilding

| 项目 | 值 |
|---|---|
| 原门 | `M_Single-Flush:Inside Door:353172` |
| Door GlobalId | `2cXV28XOjE6f6irgi0COhu` |
| Opening GlobalId | `2cXV28XOjE6f6irhW0COhu` |
| Type GlobalId | `2cXV28XOjE6f6irhu0COgZ` |
| OperationType | `SINGLE_SWING_RIGHT` |
| Damage | 删除 Door/fill，保留 Opening/void |
| 结果 | IFC2X3 重开、L1、L2、preservation 通过 |

### vvo

| 项目 | 值 |
|---|---|
| 原门 | `单扇 - 与墙齐:800x2480:255008` |
| Door GlobalId | `2IUEnGd5v4Yfg1ZlPtd0qa` |
| Opening GlobalId | `2IUEnGd5v4Yfg1ZkLtd0qa` |
| Type GlobalId | `2Bp10QP5H0qx3NLxP020qy` |
| OperationType | `SINGLE_SWING_LEFT` |
| Damage | 删除 Door/fill，保留 Opening/void |
| 结果 | IFC2X3 重开、L1、L2、preservation 通过 |

vvo 原 Door occurrence 与宿主墙落在不同 Storey。修复器按宿主墙 Storey 写入，
没有为了追求 authoring identity 而复刻这个错误关系。Type 仍精确复用。

每个案例包含 original、damaged、repaired IFC、request、ChangeSet、
application、evaluation、comparison、manifest 和人工阅读 README。

## 10. 测试结果

- Plan 11-01：60 个聚焦测试通过；
- Plan 11-02：81 个聚焦测试通过；
- Plan 11-03：29 个聚焦测试通过；
- Plan 11-04：218 个语义/评估回归通过；
- Plan 11-04 最终矩阵：86 个测试通过；
- Plan 11-05 mutation/dataset/live contract：9 个测试通过；
- 首次完整 IFC repair suite：632 passed、1 skipped、6 failed。

6 个失败来自新增 operation 后的历史 fixture 假设：

- 把目录第一个 operation 当成 Window；
- 旧 RepairIntent fixture 缺少 0.5 routing/semantic 空字段；
- 旧 occurrence property assignment 没有显式 scope。

这些兼容问题修复后，最终完整 IFC repair suite 为：

```text
638 passed, 1 skipped in 429.04s
```

## 11. 真实 DeepSeek UAT

配置检查已通过：

| 项目 | 值 |
|---|---|
| Provider | `deepseek-openai-compatible` |
| Model | `deepseek-v4-flash` |
| 最大输入 | 65,536 tokens |
| 最大输出 | 65,536 tokens |
| Secret | 仅报告 redacted 状态 |

计划用例是完整 Door 输入、不完整输入加一次合并澄清，以及复杂双扇门在
Stage 2 前被能力层拒绝。

```powershell
.venv\Scripts\python.exe scripts\ifc_repair\run_phase11_live_uat.py --live
```

本次命令在进入 Provider 前被 Codex 执行额度层拒绝，提示最早可在
2026-08-03 10:34 后重新尝试。因此本轮证据是：

```text
Stage 1 calls = 0
Stage 2 calls = 0
DeepSeek success = not executed
synthetic fallback = false
```

这不是 Provider、Prompt 或 schema 失败；没有真实网络请求发生。Phase 11
不会在该证据补齐前标记 complete。

## 12. 剩余验收

1. 额度恢复后运行三组真实 DeepSeek UAT；
2. 对 live 产物执行独立重开、L1/L2、occurrence 与 proof 校验；
3. 只把真实成功案例纳入 `ifc-repair-success-cases/door`；
4. 更新 OPS-01/OPS-02、ROADMAP 和 STATE 为 complete；
5. 创建 Phase 11 最终 Git checkpoint。

## 13. 可复现命令

```powershell
.venv\Scripts\python.exe -m pytest tests/ifc_repair/test_door_mutation.py -q
.venv\Scripts\python.exe scripts/ifc_repair/run_phase11_offline.py
.venv\Scripts\python.exe scripts/ifc_repair/run_phase11_live_uat.py --check-config
.venv\Scripts\python.exe scripts/ifc_repair/run_phase11_live_uat.py --live
```

## 14. 结论

Opening-only、Door+Opening、Door 填入已有 Opening 的合同、解析、IFC 写入、
Type 策略、语义 scope、L1/L2 与通用 occurrence comparator 已实现。

LargeBuilding 和 vvo 的 source-bound 离线链路已生成可重开的修复 IFC，并通过
生产验证。真实 DeepSeek UAT 是当前唯一已知的外部阻塞证据；在实际调用完成前，
本报告保持“实现通过、Phase 11 尚未最终关闭”的结论。
