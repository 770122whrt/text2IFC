# processed 与根目录整理

2026-09-13，当前分支 `codex/workflow-dataset-links`。先快进同步上一轮已经推送的 main 合并提交 b4eb7ccf，再执行本轮归并。原 ifc-bench 本地改动保留。

## 已完成

- processed 顶层由 **17 个目录及 2 份散落数据文件，收敛为 7 个用途目录**：[Proof](../../../dataset/processed/proof/README.md)、[实验](../../../dataset/processed/experiments/README.md)、[派生数据](../../../dataset/processed/derived/README.md)、text2json、agent-demo、ifc-repair、ifc-repair-runs。
- 8 类数据目录及两份解析 JSON 归入 derived；历史内容和数据划分不变。旧 jsonfix 的 14 份完整材料进入 experiments/legacy-jsonfix；原展示目录的导航移至 agent-demo/presentation。
- 共移位 80 个文件／8,445,473 原字节，其中 79 份保持原字节、1 份为更新链接的工作区 README。[路径映射](../../../dataset/manifests/processed-layout-20260913.json)保留旧路径、目标和校验。移动不计为磁盘节省。
- 10 份代码／脚本更新当前读取或输出路径，4 份既有测试仅调整路径和相应路径预期；没有删除回归测试或重写发布的 Prompt／Schema。
- 65 份派生数据的原 Git 对象和本地字节均保持不变；旧 CRLF 检出约定单独保留，避免搬迁产生无关换行改写。[Git 字节核对](git-byte-preservation.json)保留首次暂存属性未刷新的检查记录。
- 按用户明确批准的 [15 项清单](DELETE-LIST.md)，删除 97 个可重建／重复文件，4,274,221 字节（约 4.08 MiB）。[删除回执](deletion-result.json)逐目标记录结果。

## composite 是什么

根目录的 9 个 `composite-evidence-setsem-*` 是 Repair 的集合语义回归输出，共 54 份文件。它们由 fixture Provider 写出：同一目标／证据集合换序应绑定成功，额外、缺失、重复身份应被拒绝。目录内虽有 rendered-prompt、raw-response 等名称，但不是实际 Provider 运行，更不是 accepted Proof。

相关测试 `tests/ifc_repair/test_draft_authority_set_semantics.py` 已在先前 main 整合中改为 pytest tmp_path。本轮将该已有修复同步到当前分支，清理旧输出，并执行 12 项回归确认根目录未再产生这些目录。不重复声称本轮新增了模型能力。

## 验证

| 检查 | 结果 |
|---|---|
| 迁移前既有路径回归 | 1 failed：新 derived 路径尚未存在；[原始失败](path-before.xml) |
| 首次迁移后检查 | 28 passed、22 setup errors：本轮命令未创建 basetemp 父目录；[记录](path-after.xml) |
| 补建父目录后，相同范围重跑 | **50 passed，59.38 秒**；[日志](focused-tests-verified.txt)、[JUnit](path-after-verified.xml) |
| 迁移文件、根目录回归与 Proof 保全 | 80 个绑定核对通过；composite 根目录残留为 0；Proof diff 为空；[核对](verification.json) |
| 新 JSON 修复归档文本扫描 | 14 个文本，0 个发现；不是独立安全审计 |
| Python 与导航 | 10 份改动代码语法检查通过；最终链接检查见 navigation-check.json |

测试覆盖真实数据的旧合同迁移、来源不变、Gold／split 约束、Phase 6 清单、提取统计读取及集合身份拒绝边界。没有运行 Full Preflight、完整 curator、真实 Provider 或全仓哈希扫描；没有重新生成已验收 IFC。

本轮自行产生的 pytest 临时目录也已回收，JUnit 和日志保留；这部分不混入用户批准的旧文件统计，见[临时目录回执](own-test-temp-retirement.json)。

## 保留边界

agent-demo 与两个 Repair 目录仍有实际代码、few-shot、测试和 Plan07 来源消费者；本轮不为缩短目录列表而改造公共运行链路。text2json 保留训练／评估与私有 Gold 的现有边界。

正常用户上下文下仍无法完整读取的 Repair 旧夹具／权限隔离路径保留，详见[保留清单](retained-boundaries.json)。不能根据访问失败判定目录为空。依赖环境、模型缓存、凭据、活动 main 工作树及 ifc-bench 改动保持原样。冻结 Proof 和已归档实验不反复搬迁。

新测试只写 pytest 临时目录；单次诊断写 .tmp；成品、归档与派生数据分别使用 Proof、experiments、derived。根目录和 processed 的说明已经同步。

本轮提交与普通推送目标为当前分支；没有再合并 main、创建 PR、强推或删除分支。最终提交号与远端核对结果在交付消息中报告。
