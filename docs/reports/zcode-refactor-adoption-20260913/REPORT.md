# Zcode 有效重构接入

基线：`a25ec1d4`，分支 `codex/workflow-dataset-links`。用户要求将旧镜像中有价值的重构落实到当前代码。使用当前函数体与合同，不覆盖为旧版本；归档退役另见 [archive 报告](../archive-retirement-20260913/REPORT.md)。

## 1. 生产评估与私有基准比较：已接入

- `production_evaluation.py` 承接生产输入、生产评估和公共／基准复用的内部计算；`benchmark_evaluation.py` 保留私有输入、比较、投影及“不得提升失败生产结果”的检查。内部计算仍可由基准比较器传入私有模型，公开生产入口始终使用受限输入并禁止该来源。
- 12 个生产消费者改用生产模块，包括当前 orchestrator、离线／UAT 和 C1–C5 执行器；旧导入重导出同一对象。兼容 workflow 仍保留独立的基准比较入口。
- 16 个迁移函数／类的 AST 与当前基线一致，只改 policy 常量名称，值仍为 `phase8.1`。加速调度测试的 monkeypatch 指向新归属模块，原断言保留。
- 修改前现有回归 29 passed；新增导入边界检查 2 failed，分别命中公共 orchestrator 加载私有基准模块、新生产模块缺失。修改后同组加调度回归 44 passed；评估合同、L1、策略、公共应用、终态、安全与澄清回归 167 passed。共 211 项聚焦离线检查通过。

这验证职责迁移及已覆盖路径的兼容，不代表发现了既有 Gold 泄漏，也不代表系统修复成功率提高。

## 2. Proof 校验独立成包：已接入

`text2ifc_proof` 承接当前集合校验、Door 三方审计和 live transcript 审计。校验器不再导入 curator／runner，10 个脚本消费者直接使用新包；两处旧脚本保留 CLI 与 Python 模块别名。当前后续新增的结构恢复与冻结路径处理保留；集合投影仍使用仓库既有 `scripts/proof/package.py`，本次没有把整个项目改造成独立可分发的 Proof 产品。

103 个 validator 定义、33 个 Door auditor 定义在去除 import 调整后与基线 AST 一致；39 个共享 live 审计定义的 AST 完全一致。新增导入／CLI 检查初始 5 failed，提取后通过。入口／UAT 回归 117 passed、1 failed；R1／结构 Proof 回归 51 passed、15 failed。

16 个失败均在固定提交 `2d1a18bb` 的原始四个脚本上复现：4 个仍读已退役 Proof 路径，11 个旧模拟 transcript 在 profile 路由门被拒绝，1 个缺少旧 v2 准入文件。基线在子进程内加载 Git 原代码，普通导入和按文件加载均绑定原代码，工作树不回滚；未改测试断言。原始失败与基线分别保留在 [本次结果](proof-authority-tests.xml)、[原代码复核](proof-original-baseline.xml)，提取核对见 [JSON](proof-extraction-checks.json)。首次定位还运行过 R1 `-x`（16 passed、1 failed）及结构 Proof `-x`（25 passed、1 failed），均属同一失败，不能重复计入通过总数。

因此这一步是结构接入与已覆盖行为保持，不是全套 Proof 检查通过。后续修复测试数据绑定时必须恢复其原来的关键断言覆盖，不允许更新冻结 Prompt 或恢复撤回的验收资格来凑通过。缺失的 live 准入继续阻止真实调用。

## 3. 运行脚本分类：待接入

按 UAT、offline、curators、audits 整理实际实现，保留旧入口。不更换冻结准入的路径／哈希含义；没有有效新准入时真实调用继续失败关闭。

## 验证边界

本轮无 Provider 调用、Full Preflight、完整 curator 或新人工验收。现有 Proof 字节与状态不变，不删除测试以取得通过。保留其他任务的 RVT、Proof 未跟踪文件和 ifc-bench 修改。
