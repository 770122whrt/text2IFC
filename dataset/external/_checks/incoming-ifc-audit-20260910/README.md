# 新增 IFC 数据检查与 IFC-bench 登记修订

当前目录：`dataset/external/_checks/incoming-ifc-audit-20260910/`。

[问题总结与处理建议](HANDOFF-SUMMARY.md) · [交给另一 Agent 的处理 Prompt](REPAIR-AGENT-PROMPT.md)。

本目录按用户要求从 `dataset/processed/review/` 迁入；88 份原文件迁移时逐字节一致，详见 `migration.json`。之后只增补人读说明及用户确认事项，原始 JSON 检查结果、失败和超时记录保持不变。历史记录内的旧目录引用由 `migration.json` 映射到此处，不代表旧目录仍存在。脚本仍在 `scripts/dataset/`，测试仍在 `tests/dataset/`；本目录不是独立模型来源，也不是正式准入清单。

日期：2026-09-10。项目：text2IFC。原 IFC、ZIP 和子模块内容均未修改；只新增检查代码、测试和报告，并修订一份旧兼容登记。

## 结论

两个 ZIP 共含 **80 个 IFC 文件：50 个 ResBIM 转换结果 + 29 个其他 RVT 转换结果 + 1 个原有 Circular 示例**。不是 80 个新转换建筑。全部重新用 IfcOpenShell 解析为 IFC2X3，IfcGrid 和 IfcGridAxis 均为零。包内、包间没有字节完全相同的重复；与当前 274 条 canonical 登记也没有字节级匹配。

**79 个转换文件都存在重复 GlobalId、IfcSIUnit 必填 Name 缺失、FILE_NAME.originating_system 缺失，不能按现状登记为合规通过。** 这些共同缺陷已通过第二次独立解析直接核对，不仅依赖校验器报错。旧 Circular 示例通过本轮基础技术检查，但完整标准认证、模型许可和正式准入均未完成。

| 项目 | ResBIM 50 | 新转换 29 | 附带 Circular |
|---|---:|---:|---:|
| 实际文件数 | 50 | 29 | 1 |
| IFC2X3 解析成功 | 50 | 29 | 1 |
| 小于 10 MiB 且有主体形状 | 50 | 20 | 1 |
| 有主体但超限 | 0 | 4 | 0 |
| 无主体形状 | 0 | 5 | 0 |
| Grid / GridAxis 均为零 | 50 | 29 | 1 |
| 完成属性/基数/逆关系/唯一性校验 | 50 | 25 | 1 |
| 上述校验发现错误的文件 | 50 | 25 | 0 |
| 完成几何抽检的文件 | 50 | 20 | 1 |
| 几何抽检构件数 / 失败数 | 1200 / 0 | 436 / 0 | 24 / 0 |
| 内存序列化后重开通过 | 50 | 25 | 1 |
| 本轮基础技术门槛通过 | 0 | 0 | 1 |

10 MiB = 10,485,760 字节；使用严格小于阈值。没有零字节 IFC。5 个“空输出”实际是可解析但无主体形状的骨架文件，不等于原 RVT 本身为空。

## 29 个新转换结果的分类

超限：RVT-004（37.9450 MiB）、RVT-005（37.8857 MiB）、RVT-011 和 RVT-012（均 67.9031 MiB）。四者基础解析、主体计数、Grid/Axis 和直接必填字段/GlobalId 检查已完成；完整属性校验、内存往返和几何抽检未完成。RVT-004 的一次深入校验超过 90 秒，保留了超时结果，其余超限文件不反复运行昂贵检查。

无主体：RVT-002、RVT-013、RVT-020、RVT-022、RVT-023。

其余 20 个是“小体积、有主体、待修复/待审”的候选，不是合规通过，也不能直接计为 20 个独立建筑。

## 重复、变体、依赖和许可

字节精确重复为零，不表示不存在建筑变体。共发现 12 对构件 GlobalId 高重合关系，详见 summary.json；属于变体线索，不自动合并身份。

- RVT-006 / RVT-007：较小集合的 117 个构件 GlobalId 全部重合。
- RVT-008 / RVT-010：443 个构件 GlobalId 重合。
- RVT-014 / RVT-015、RVT-016 / RVT-017：nowalls 与对应 house 版本的较小构件集合全部重合；两组之间也存在共享构件。
- RVT-004 / RVT-005 / RVT-011 / RVT-012：存在很高的构件重合；011 与 012 的 3271 个构件 GlobalId 完全相同，但文件字节及 DATA 区块并不完全相同。

包内依赖记录报告 RVT-025、RVT-026、RVT-028 缺少部分 DWG/RVT 输入依赖；RVT-008、RVT-022 的链接是否导出仍未确认。本轮读取并保存了这些来源证据，没有实际重跑 RVT 链接解析，因此不能将它们误称为已独立验证的 IFC 运行时依赖缺失。

全部文件的模型级许可终审均未完成。未扩大训练或再分发授权，verified-register.json 中 training_eligible 保持 false。建筑独立性计数保留 null，不以文件数代替。

## ResBIM 屋顶与拓扑

50 个 ResBIM IFC 均没有 IfcRoof，也没有 PredefinedType=ROOF 的 IfcSlab。这只能证明没有这些屋顶语义标记，不能单凭计数断言完全没有屋顶几何。若数据集要求屋顶语义明确，应单独检查源 RVT 与对应 IFC。

50 个 ResBIM IFC 的 Opening 均具有 Voids 关系，Door/Window 均有 Fills 关系。29 转换包中有 7 个文件存在部分门窗没有 Fills 链，已记作人工复核信号；不能把所有此类情况统一认定为非法。

## IFC-bench 修订及再验证

修订文件：dataset/manifests/external-corpora.json。

| 字段 | 原登记 | 当前本地核验 |
|---|---:|---:|
| 全部文件数 | 170 | 168 |
| 总字节数 | 2,074,769,344 | 1,510,012,238 |
| IFC 文件数 | 50 | 48 |
| IFC2X3 / 已登记可重开数量 | 27 | 25 |

用户于 2026-09-10 确认：projects/sixty5/arc.ifc、projects/sixty5/plumbing.ifc 是因文件体积过大而主动排除，不是意外丢失。本轮没有删除或恢复它们，后续不得擅自补回或重新下载。登记保留原计数、排除路径和用户确认来源；用户未提供当时的具体排除阈值，不把本次新 ZIP 的 10 MiB 目标反推为 IFC-bench 的历史筛选阈值。`reconciliation-before.json` 是确认原因前的历史核对快照，保留原文。

剩余 48 个 IFC 均与当前 canonical 路径登记一致。audit_dataset.py 修订后返回 valid=true；audit_ifc_source_dataset.py 再次验证 274 条正式记录，返回 valid=true。后者验证路径、身份和内容，不等于对现有 274 个 IFC 重新做了完整几何/Schema 校验。

## 执行与检查边界

新增检查器的初始 IFC2X3 兼容问题已修复，原失败报告保留；修复后聚焦测试为 **8 passed**。整个 tests/dataset 测试目录运行超过 120 秒，未完成，不能报告为全套通过。

本轮几何是按构件类别分层抽样，71 个有主体小文件合计抽检 1660 个构件，未发现失败。未运行全部 EXPRESS WHERE 规则、全部构件几何、碰撞、建筑设计规范、逐模型视觉验收或 RVT→IFC 完整性核验。dataset 总体审计还报告了 processed 中若干目录不可读；没有将这些目录计为已检查通过，也未扩大本轮两个 ZIP 的处理范围。

没有更新 ifc-files.jsonl、ifc-sources.json、训练划分或正式候选准入；没有 Git commit 或 push。原有 Proof 和其他并行任务修改保持不动。

## 文件入口

- [逐文件检查表](REPORT.md)
- [逐文件机器登记与来源、依赖、变体字段](verified-register.json)
- [统计和高重合关系](summary.json)
- [ZIP 成员清单与包内说明原文](inventory.json)
- [IFC-bench 修订前差异及来源证据](reconciliation-before.json)
- member-v2-*.json：单文件校验错误与几何抽检细节；member-000 至 member-004 为最初检查器失败记录，不能当作最终结果。

## 后续建议

先保留 70 个小体积、有主体的转换文件作为待修复候选；4 个超限和5个无主体文件保留诊断记录。不要直接导入主数据集。优先选一个 ResBIM 和一个其他来源小模型，定位共同的导出字段、GlobalId 和清理问题，在副本上修复并复验；小样验证成功后再讨论批量修复及变体、屋顶、许可准入。
