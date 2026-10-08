# IFC Repair 四组实验文档

> 更新：2026-10-08｜专题版本：v0.2。
> 当前：20个不同且许可明确的IFC题包已获委托完成技术审题并冻结。四组原批次63/80项终态，17项未开始。本轮未开启Goal，B共性修复与001～010的两批开发复验已完成：001～004、006、008～010真实严格通过；005原响应离线重放补全，007跨层高度被拒绝并按用户意见保留。两批服务均停止，原请求、预算、评分及旧尝试保持。修复与结果见[B共性修复报告](b-common-repair.md)。只维护本目录这一套正文，不另存版本副本。

阶段3的[独立安装范围](deepseek-harness-integration.md#13-阶段3安装与隔离方案已批准的具体范围)已获准；固定完整DSH 0.2.0rc1原生工具、问答、子Agent、摘要和停止证据见[§6.9](development-readiness.md#69-阶段3dsh安装与首批原生离线验收)。本轮统一账本、容器公共CLI、准入及真实运行见[§6.11](development-readiness.md#611-goal-本轮首批五题与两个-demo-的四组接线2026-10-04)。用户已批准开发调用约20M token目标，超出不重复审批。

20 个源 IFC、每模型一个任务、四组共 80 个任务单元；其中 2–4 个任务需要澄清，先按 3 个准备。A 是 DeepSeek API 通用执行器，B 是 DeepSeek＋我们的 Harness，C 是 GPT API＋与 A 相同的执行器，D 按 DeepSeek 官方 Harness 调研接入。日常 Codex 是开发工具，不是 C 组被测产品。

## 阅读与执行入口

| 文档 | 职责 |
|---|---|
| [实验计划](plan.md) | 四组、方法中立输入、人工审查、工作副本、动态预算与开发阶段 |
| [指标规范](metrics.md) | 数量、完整构件、关系比例、任务、IFC 校验、保全、澄清与用量 |
| [DSH 接入与隔离](deepseek-harness-integration.md) | 先调研再隔离，原生问答继续、推理记录与预算停止 |
| [Codex 启动提示词](development-start-prompt.md) | 直接读取仓库正文，只读核对并提出开发建议，不重复导入更新包 |
| [代码核对与首批开发建议](development-readiness.md) | 实际复用入口、环境状态、DSH 固定版本证据及 M1.1–M1.4 文件与验收 |
| [两道 demo 的真实联调](demo-results.md) | 八任务的实际状态、提交、格式检查、人工等待及失败用量 |
| [B 共性问题与001～010复验](b-common-repair.md) | 当前缺陷归因、最小修复、离线证据和原题开发复验 |

计划管范围与安排，指标文档管计分，DSH 文档管接入细节；提示词引用这些正文，不成为另一个实验规范。`development-readiness.md` 记录本次实际核对和开发建议，不替代三份正文，也不是 Stage Admission 或正式成绩。

[研究登记](../../reports/repair-demo/claims-and-experiments.md)继续负责 Claim、批准状态和真实运行索引，不另起第四份研究主稿。既有 Proof 与历史成绩不因更新而改变。

## v0.2 已合并的调整

A/C 只接收中性请求和 IFC，可自行选择脚本或直接编辑，不默认附送 API 教程。实验端冻结 D、被测侧操作副本。20 个任务全部人工审查；评分程序基本自检单列，不代替人审。

保留 DeepSeek 实际返回推理；DSH 先渐进调研，以 Docker 为优先隔离候选；预算按任务分配且同题四组采用相同调整规则；2–4 个澄清题在 20 题内，等待和继续保留同一任务及累计用量。

上版默认“统一 128k／900 秒”“无澄清”“A/C 默认附教程与仅 Python 路径”已由 v0.2 相应条款取代。具体阈值、平台、SDK/API 版本由实际核对确定，不重复向用户发研究选项问卷。

## 历史开发检查点（2026-09-29～10-04）

2026-09-29 阶段 1 的可审阅交付已生成：

- [开发题包总入口](../../../dataset/processed/ifc-repair/repair-comparison/development/README.md)：固定目录内的待审材料，输入与配方纳入Git，后续原位更新。
- [首批五题人审入口](../../../dataset/processed/ifc-repair/repair-comparison/formal/README.md)：S1/S2、三份CC BY 4.0及两份GPL；五题均有格式报告与G/D查看器，尚待逐题人审，未向模型发送。
- [case-001：补中间固定窗](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/REVIEW.md)：LargeBuilding，MIT，信息充分题。
- [case-002：保留洞口补门](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/REVIEW.md)：Duplex Apartment，CC BY 4.0，二层唯一空室内门洞；左右开启均允许，信息充分题。
- [窗题格式校验](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/IFC-VALIDATION.md)／[门题格式校验](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/IFC-VALIDATION.md)：schema＋EXPRESS零诊断，两份D均为PASS。
- [门题同步网格查看器](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/VIEW.html)／[窗题查看器](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/VIEW.html)：本地生成的HTML，重建命令见下方实现说明。删除门为150378，150478保持原位置及网格。
- [实际实现、检查与命令](development-readiness.md#6-阶段-1-实际交付两道开发题与最小工具)：37项聚焦测试通过；查看器浏览器视觉验收受限，尚未完成；不代表修复模型成绩或运行时隔离已验收。

整体按用户要求保持约 20 个不同源 IFC 的规模，优先许可明确的独立场景族；导出版本、损坏副本和修复副本不增加样本数。开发题与正式未见样本分开，数量口径见[计划 §6.1](plan.md#61-源模型选择)。

用户已认可形式并要求继续，未代写正式题accepted。损伤按S1单目标、S2双目标（同类／混合）、S3三个及以上分级；首批五题已包含S2两窗和窗门混合。后续必要澄清题仍选位置、楼层或不可推导的尺寸缺项。两demo真实联调只验证可运行链路，失败、无输出和人工等待均保留；正式20题人审、指标和80任务冻结仍未完成。生产改动仍仅有此前获准的尺寸单位修复。遵守[现有准入协议](../agent-capability-evaluation.md)。
