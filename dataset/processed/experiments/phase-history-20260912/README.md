# 早期 Phase 运行与调试历史

保存 Generation Phase 6 和 Repair Phase 9–12 的 57 个已结束工作区，包含成功、失败、未放行输出、原始 Provider 响应、预算与评价材料。人工状态和机器结论均沿用原记录；这里不是新增 accepted Proof。

入口仍为 [Proof](../../proof/README.md)。本目录用 54 个 ZIP 保存独有原文件，复用现有 Proof 中的相同内容，并对重复字节只保存一份。[manifest.json](manifest.json) 逐项记录 `old_root`、`legacy_path`、大小、SHA-256、保留文件及可选的 `archive_member`。恢复历史路径时按这些绑定复制／解压；不能只解压某一个 ZIP 就假设已获得该工作区的全部材料。

10,759 份源文件共 6,599,356,507 字节，新增 ZIP 共 276,467,242 字节；7,692 个不同保留文件／成员中，305 个复用现有 Proof。4 个历史测试链接只保存原目标文字，不将目标目录收纳进来，也不在解压时自动创建链接。全部文件绑定已验证，未发现凭据。

按文件名前缀阅读：`agent-demo--` 为早期 Generation，`ifc-repair--` 为 Phase 9–12 Repair 开发，`ifc-repair-runs--` 为 Phase 12／R1 运行历史。原始日期、失败状态、private Gold 的评价角色和历史 Prompt 版本不改。冻结的路径和 admission 只是当时环境，新调用不得直接复用。

[执行报告](../../../../docs/reports/development-cleanup-20260912/REPORT.md) 记录实际删除结果、Git 备份及保留的当前输入。生产 few-shot、仍被测试和 curator 使用的源材料保留原处。
