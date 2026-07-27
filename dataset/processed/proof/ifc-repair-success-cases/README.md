# IFC Repair 成功案例集

本目录集中保存已经通过机器验证并成功发布 IFC 的修复案例。它回答的是：

> 给定一份原始 IFC、一份人为构造的 damaged IFC 和一段用户文本，系统是否
> 能通过真实 Agent 输出受约束 ChangeSet，并生成可重新打开、通过 L1/L2 的
> 修复 IFC？

当前版本只收录 `add_window_with_opening_to_wall`。Door、只挖 Opening、
Beam、Column 等 operation 后续按照同一目录合同追加，不会混入现有 Window
报告。

## 案例索引

| 案例 | 模型规模 | 操作数 | 主要证明 | 结果 |
|---|---:|---:|---|---|
| [LargeBuilding 单窗完整语义复刻](window/single/largebuilding-full-replication/REPORT.md) | 20,735 entities | 1 | Type 复用、16 项文本属性、有效语义完整性 | Production 与 Private L1/L2 passed |
| [LargeBuilding r22 真实 DeepSeek 重复实验](window/single/largebuilding-r22-repeat/REPORT.md) | 20,735 entities | 1 | Stage 1/2 各一次真实调用、无 fallback、可重复发布 | Production 与 Private L1/L2 passed |
| [vvo 五窗批量修复](window/batch/vvo-five-window/REPORT.md) | 48,935 entities | 5 | 一个文本、一个统一 ChangeSet、同墙多窗、原子发布 | 5 项 L1/L2 passed |
| [AdvancedProject 五窗大型模型修复](window/batch/advancedproject-five-window/REPORT.md) | 770,172 entities | 5 | 大型 IFC、全模型 preservation、映射 Type | 5 项 L1/L2 passed |
| [px4 五窗与上下叠窗修复](window/batch/px4-five-window/REPORT.md) | 501,401 entities | 5 | 二维 Opening 冲突、上下叠窗、原子回滚 | 5 项 L1/L2 passed |

三个案例的横向解读见
[WINDOW-CASES-SUMMARY.md](WINDOW-CASES-SUMMARY.md)，机器可读总索引见
[manifest.json](manifest.json)，本次集合验收见
[VALIDATION.md](VALIDATION.md)。

## 每个案例包含什么

```text
01-original.ifc
02-damaged.ifc
03-repaired.ifc

input/          用户实际输入
agent/          RepairIntent、Provider draft 与 Provider 元数据
changeset/      经过确定性绑定和审计的统一 ChangeSet
validation/     damage、application、L1/L2、Comparator 或 Ground Truth 证据

REPORT.md       面向人阅读的案例报告
FILES.json      文件角色、来源、大小和 SHA-256
```

三份 IFC 的含义固定：

- `01-original.ifc`：构造损伤前的 Ground Truth，只供 damage 和 evaluator
  使用；
- `02-damaged.ifc`：交给修复系统的 IFC 输入；
- `03-repaired.ifc`：通过 Production gate 后发布的 IFC 输出。

Private mutation manifest 记录被移除对象的真实身份，因此标记为
`evaluator_only`。它不能进入 Stage 1 或 Stage 2 Prompt。

## 准入规则

一个运行只有同时满足以下条件才进入本目录：

1. 使用真实 Provider；或者明确保存真实 Provider 输出，并在修复后的代码上
   确定性重放；
2. ChangeSet 已绑定 damaged IFC 指纹；
3. IFC application 成功，输出可以用 IfcOpenShell 重新打开；
4. 全局 preservation/scope gate 通过；
5. 每个 operation 的 L1 和 L2 均为 `passed`；
6. `complete_repair_success = true`；
7. `successful_artifact_publishable = true`；
8. 原始、damaged、repaired、输入、ChangeSet 和验证证据均可追溯。

仅写出一个 `.ifc`、仅离线 fake Provider 通过、历史失败或只有 diagnostic
candidate 的运行都不属于成功案例。

## 副本与来源

Proof 目录保存经过校验的副本，不移动或删除原始运行产物。每个
`FILES.json` 都记录副本的 SHA-256 和原来源路径。原始 Prompt、完整响应日志、
SQLite 索引和临时 staging 文件继续保留在原运行目录，不重复复制。

文件大小和 STEP 文本是否相同不是成功标准。当前发布合同是：

```text
geometry_relationship_success
AND semantic_fidelity_success
AND global_preservation_success
```

L3 authoring exactness（原 GlobalId、Name、Tag、STEP 顺序和字节级相同）仍为
观察项，不作为当前 Window 修复的发布门槛。

## 一键校验

新增或更新任何成功案例后执行：

```powershell
.venv\Scripts\python scripts\ifc_repair\validate_success_cases.py
```

机器可读输出：

```powershell
.venv\Scripts\python scripts\ifc_repair\validate_success_cases.py --json
```

相同规则已由 `tests/ifc_repair/test_success_case_collection.py` 接入 pytest。校验会检查
FILES 哈希与完整覆盖、三份 IFC 重开、IFC2X3 schema、ChangeSet damaged 指纹、
RepairIntent/ChangeSet/evaluation operation 数，以及 Production 发布状态与 L1/L2。

## 后续构件如何接入

后续按 operation family 新建目录，例如：

```text
door/single/<case-id>/
door/batch/<case-id>/
opening/single/<case-id>/
beam/single/<case-id>/
column/single/<case-id>/
```

新增案例必须继续使用相同的三份 IFC、输入、Agent、ChangeSet、验证报告和
`FILES.json` 合同。Door 等构件拥有自己的 L1/L2 policy，不得通过重命名
Window 字段伪装成新能力。
