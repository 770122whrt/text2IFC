# 已完成案例与开发工作区清理

2026-09-12；分支 `codex/workflow-dataset-links`。用户批准执行既有删除清单，并按相同方式处理其他已完成案例和开发目录。本轮没有调用 Provider、修改生产行为、运行 Full Preflight 或合并 main。

## 保留位置与删除范围

光庭首批清理已完成：75 个目录、24 个单独文件，共 49,563 文件、744,508,756 字节（710.02 MiB）。见 [独立执行记录](../courtyard-proof-closeout-20260912/deletion-result.json)。两版成品、人工状态、失败尝试和账本仍在 [光庭 Proof](../../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/REPORT.md)。

追加清理先备份后删除，复制时的索引状态不作为最终删除结果：

| 范围 | 保存和处理方式 | 精确清单 |
|---|---|---|
| 17 个旧展示／开发目录 | 3,555 份证据，173 份复用已有 Proof，其余原字节进入 experiments；36 个 Python 缓存不归档 | [旧路径与保留路径](../../../dataset/processed/experiments/development-retirement-20260912.json) |
| 328 个 `.tmp` 单独文件 | 116 份复用冻结结果，212 份一次性脚本或结果归档；两个巨大重复空白诊断日志无损 ZIP 保存 | [逐文件索引](../../../dataset/processed/experiments/scratch-retirement-20260912.json) |
| 313 个已结束的 pytest 目录 | 对应保留的 JUnit 测试族；检查路径、文件数、大小、锁及链接后删除可重建夹具 | [目录与来源](scratch-retirement-plan.json) |

两个日志从 383,419,299 字节压缩为 19,914,355 字节，解压成员与原文 SHA-256 相同。归档不把旧失败或待审结果升级为已验收，不改原始响应和历史判断；若原目录与现有 Proof 中同名文件的字节不同，两份都保留。

每次执行结果另存 `deletion-*.json`，完成后由本报告补充实际数量。清理脚本 [retire.ps1](retire.ps1) 只处理清单范围。权限错误、目录内容变化或缺失保留证据均停止该目标并记录，不重设 ACL、不操作活动工作树。

## 测试处理及验证

保留有独立覆盖价值的通用回归。四个 A/B 测试文件改用归档运行器；一次性实验脚本从工作区归档，不作为新增正式测试。光庭 12 个一次性测试脚本已随前一批 Proof 收纳。

路径复验最初为 **18 通过、2 失败**。原因是旧 continuation 测试将 Brief 升为 2.1，却没有提供此版本要求的 `known_facts.semantic_requirements`。归档前后运行器字节相同；此次仅为明确没有材料／属性语义的合成夹具补空列表，未改生产门禁或原断言。修正后 **20 通过**。保留 [初次结果](path-regression.xml)、[失败归因](fixture-diagnosis.json) 与 [修正结果](path-regression-fixed.xml)，不将路径复验描述为系统能力提升。

[归档检查](archive-verification.json) 验证 3,883 个保留绑定（3,767 个不同文件／ZIP 成员），扫描 3,589 个文本／数据库对象，未发现凭据。只检查本次迁移证据，没有大范围重算既有 Proof。新归档在删除前还需验证 Git 索引中的字节及远端备份。

## 保留边界

`agent-demo` 中仍被测试、验证器或数据构建使用的输入，`ifc-repair`／`ifc-repair-runs` 中独立真实尝试、来源材料、private Gold 及权限不明项继续保留；依据见 [旧目录用途清单](legacy-root-inventory.json)。这些内容尚不具备可用副本或可重建夹具的退役依据。保留活动 `.tmp/main-integration-20260912` 工作树、数据下载目录、会话恢复材料、外部 IFC 压缩包、ifc-bench 及归属不明的根目录 composite-evidence 文件夹。

冻结记录中的原绝对路径是历史来源，通过归档索引追溯；不改写冻结数据库或旧 admission。新真实运行须创建新工作区并遵循当前准入。
