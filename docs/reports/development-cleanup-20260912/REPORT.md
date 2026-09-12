# 已完成案例与开发工作区清理

2026-09-12；分支 `codex/workflow-dataset-links`。用户批准执行既有删除清单，并按相同方式处理其他已完成案例和开发目录。本轮没有调用 Provider、修改生产行为、运行 Full Preflight 或合并 main。

**已完成：** 464 个清单目录、352 个单独文件及 4 个测试链接均已退役，共删除 253,690 个旧文件、10,482,178,079 字节（约 9.76 GiB）。这是删除的源文件字节数，未扣减新增归档，不是磁盘净节省值。[汇总与核对](cleanup-summary.json) 保留准确数量；所有真实证据在 Proof／experiments，26 个当前依赖目录保留。本次清单没有待管理员处理的删除项。

## 保留位置与删除范围

光庭首批清理已完成：75 个目录、24 个单独文件，共 49,563 文件、744,508,756 字节（710.02 MiB）。见 [独立执行记录](../courtyard-proof-closeout-20260912/deletion-result.json)。两版成品、人工状态、失败尝试和账本仍在 [光庭 Proof](../../../dataset/processed/proof/generation/phase6.6/courtyard-library-20260912/REPORT.md)。

追加清理先备份后删除，复制时的索引状态不作为最终删除结果：

| 范围 | 保存和处理方式 | 精确清单 |
|---|---|---|
| 17 个旧展示／开发目录 | 3,555 份证据，173 份复用已有 Proof，其余原字节进入 experiments；36 个 Python 缓存不归档 | [旧路径与保留路径](../../../dataset/processed/experiments/development-retirement-20260912.json) |
| 328 个 `.tmp` 单独文件 | 116 份复用冻结结果，212 份一次性脚本或结果归档；两个巨大重复空白诊断日志无损 ZIP 保存 | [逐文件索引](../../../dataset/processed/experiments/scratch-retirement-20260912.json) |
| 315 个已结束的 pytest 目录 | 原清单 313 个，加本轮失败／通过验证的 2 个；对应保留的 JUnit，检查路径、文件数、大小、锁及链接后删除可重建夹具 | [目录与来源](scratch-retirement-plan.json) |

两个日志从 383,419,299 字节压缩为 19,914,355 字节，解压成员与原文 SHA-256 相同。归档不把旧失败或待审结果升级为已验收，不改原始响应和历史判断；若原目录与现有 Proof 中同名文件的字节不同，两份都保留。

追加批次已完成：17 个旧案例目录、315 个 pytest 目录、328 个单独文件，实际删除 193,368 文件、3,138,312,816 字节。加光庭首批共 242,931 文件、3,882,821,572 字节；此处不含下述更早 Phase 批次。精确执行结果另存 `deletion-*.json`。清理脚本 [retire.ps1](retire.ps1) 只处理清单范围。权限错误、目录内容变化或缺失保留证据均停止该目标并记录，不重设 ACL、不操作活动工作树。

**权限复核补存：** 三个目录的删除前检查发现不同 Windows 上下文的文件可见性不一致；首次归档遍历遗漏了权限隐藏的子目录。删除门禁保留了这三个目录。补存另外 883 文件、19,390,141 字节（包括原有离线矩阵、修复破坏材料及 5 个历史 pytest-cache 文件），原始复制索引不改，使用 [追加映射](../../../dataset/processed/experiments/development-retirement-permission-supplement-20260912.json)。补充材料全部逐字节验证，凭据扫描无发现；见 [补存验证](permission-supplement-verification.json)。不得仅凭原归档“绑定通过”推断原目录完整性。

## 测试处理及验证

保留有独立覆盖价值的通用回归。四个 A/B 测试文件改用归档运行器；一次性实验脚本从工作区归档，不作为新增正式测试。光庭 12 个一次性测试脚本已随前一批 Proof 收纳。

路径复验最初为 **18 通过、2 失败**。原因是旧 continuation 测试将 Brief 升为 2.1，却没有提供此版本要求的 `known_facts.semantic_requirements`。归档前后运行器字节相同；此次仅为明确没有材料／属性语义的合成夹具补空列表，未改生产门禁或原断言。修正后 **20 通过**。保留 [初次结果](path-regression.xml)、[失败归因](fixture-diagnosis.json) 与 [修正结果](path-regression-fixed.xml)，不将路径复验描述为系统能力提升。

[归档检查](archive-verification.json) 验证 3,883 个保留绑定（3,767 个不同文件／ZIP 成员），扫描 3,589 个文本／数据库对象，未发现凭据。只检查本次迁移证据，没有大范围重算既有 Proof。新归档在删除前还需验证 Git 索引中的字节及远端备份。

原批次 [索引验证](index-verification.json) 核对 3,767 个保留文件、98 个 LFS 指针；[补存索引验证](permission-supplement-index-verification.json) 核对 883 文件、7 个 LFS 指针。初次 `diff --check` 报告失败 JUnit 原始回溯中的两处尾随空白；未修改失败输出，手写源码和文档的定向检查通过。

## 保留边界

`agent-demo` 中仍被测试、验证器或数据构建使用的输入，以及 `ifc-repair`／`ifc-repair-runs` 中当前 curator 和 Plan07 使用的案例与源基线继续保留；依据见 [旧目录用途清单](legacy-root-inventory.json) 和 [Phase 范围及依赖](phase-scope.json)。独立真实尝试和 private Gold 可归档但不能销毁或混入 Provider 输入。保留活动 `.tmp/main-integration-20260912` 工作树、数据下载目录、会话恢复材料、外部 IFC 压缩包、ifc-bench 及归属不明的根目录 composite-evidence 文件夹。

冻结记录中的原绝对路径是历史来源，通过归档索引追溯；不改写冻结数据库或旧 admission。新真实运行须创建新工作区并遵循当前准入。

## 用户追加：更早的 Phase

用户明确要求范围不止 A/B。追加处理 Phase 6、9–12 共 57 个历史目录，26 个仍有依赖或需要单独判断的目录保留，未删除早期 SPEC、Prompt、Schema 或通用回归测试。

两种 Windows 上下文合并盘点后，10,759 个文件的集合完整，无未解释的访问缺口。归档约 6.15 GiB 源字节，新增 54 个 ZIP／276,467,242 字节；复用 Proof 的 305 个文件，并合并完全相同的字节。每个原路径独立映射，历史角色不会因去重而合并。见 [归档入口](../../../dataset/processed/experiments/phase-history-20260912/README.md) 和 [完整绑定验证](phase-archive-verification.json)。

初次普通用户盘点遇到旧测试故意构造的链接并停止，未跟随目标。最终记录 4 个链接及其目标；删除时只移除链接条目，逐个删除已备份且仍匹配的源文件，再删除清单内的空目录，不递归触及链接目标。删除前须推送此批完整备份。旧机器结论保持，未运行新 Provider 或完整 curator。

57 个 Phase 目录已全部删除：默认上下文删除 10,628 文件，沙盒外上下文删除其余 131 文件，并仅移除 4 个测试链接。两个执行记录为 [默认](deletion-phases-default.json)、[沙盒外](deletion-phases-elevated.json)；每个根目录都有实际删除回执，目录残留为 0。

删除后补充两项现有拒绝守卫检查，**2 通过**：旧 offsite 结构恢复案例和已知不连通 Generation 仍被拒绝，见 [JUnit](phase-retirement-guards.xml)。四个 A/B 模块删除旧目录后仍收集到 20 个测试；这是加载检查，不能重复记为 20 项执行。当前 few-shot、公共离线夹具和 Plan07 来源见 [保留输入检查](kept-inputs-check.json)。活动导航没有指向本批已退役目录的链接。

## Git 与收尾

| 提交 | 内容 |
|---|---|
| `eaa67b29` | 首批光庭源目录与临时工作区退役 |
| `8b51e6e2` | 其他案例、一次性开发记录的备份和测试路径迁移 |
| `81097dee` | Windows 权限隐藏材料补存 |
| `6eff9388` | 更早 Phase 的压缩备份及已完成的展示源目录清理 |

上述备份均先推送再删除；最终删除记录、目录导航和状态更新一起提交并普通推送到同一分支。本轮不创建 PR、不合并 main、不删除其他分支、不压缩 Git/LFS 历史。ifc-bench、活动 main 工作树、未归属材料和既有未登记 Proof 保留原状态。四个本轮生成的暂存路径清单属于执行脚手架，完成暂存后另行回收，不计入上述旧文件统计。
