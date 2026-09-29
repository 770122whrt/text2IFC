# IFC Repair 四组实验文档

> 更新：2026-09-29｜专题版本：v0.2。
> 当前：已按第一轮人审意见重写两道简单开发题；公开请求无GUID、构件名或方法提示，撤销门开向必答项，损坏IFC须通过格式校验。只维护本目录这一套正文，不另存版本副本。

20 个源 IFC、每模型一个任务、四组共 80 个任务单元；其中 2–4 个任务需要澄清，先按 3 个准备。A 是 DeepSeek API 通用执行器，B 是 DeepSeek＋我们的 Harness，C 是 GPT API＋与 A 相同的执行器，D 按 DeepSeek 官方 Harness 调研接入。日常 Codex 是开发工具，不是 C 组被测产品。

## 阅读与执行入口

| 文档 | 职责 |
|---|---|
| [实验计划](plan.md) | 四组、方法中立输入、人工审查、工作副本、动态预算与开发阶段 |
| [指标规范](metrics.md) | 数量、完整构件、关系比例、任务、IFC 校验、保全、澄清与用量 |
| [DSH 接入与隔离](deepseek-harness-integration.md) | 先调研再隔离，原生问答继续、推理记录与预算停止 |
| [Codex 启动提示词](development-start-prompt.md) | 直接读取仓库正文，只读核对并提出开发建议，不重复导入更新包 |
| [代码核对与首批开发建议](development-readiness.md) | 实际复用入口、环境状态、DSH 固定版本证据及 M1.1–M1.4 文件与验收 |

计划管范围与安排，指标文档管计分，DSH 文档管接入细节；提示词引用这些正文，不成为另一个实验规范。`development-readiness.md` 记录本次实际核对和开发建议，不替代三份正文，也不是 Stage Admission 或正式成绩。

[研究登记](../../reports/repair-demo/claims-and-experiments.md)继续负责 Claim、批准状态和真实运行索引，不另起第四份研究主稿。既有 Proof 与历史成绩不因更新而改变。

## v0.2 已合并的调整

A/C 只接收中性请求和 IFC，可自行选择脚本或直接编辑，不默认附送 API 教程。实验端冻结 D、被测侧操作副本。20 个任务全部人工审查；评分程序基本自检单列，不代替人审。

保留 DeepSeek 实际返回推理；DSH 先渐进调研，以 Docker 为优先隔离候选；预算按任务分配且同题四组采用相同调整规则；2–4 个澄清题在 20 题内，等待和继续保留同一任务及累计用量。

上版默认“统一 128k／900 秒”“无澄清”“A/C 默认附教程与仅 Python 路径”已由 v0.2 相应条款取代。具体阈值、平台、SDK/API 版本由实际核对确定，不重复向用户发研究选项问卷。

## 当前执行状态

2026-09-29 阶段 1 的可审阅交付已生成：

- [开发题包总入口](../../../dataset/processed/ifc-repair/repair-comparison/development/README.md)：固定目录内的待审材料，输入与配方纳入Git，后续原位更新。
- [case-001：补中间固定窗](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/REVIEW.md)：LargeBuilding，MIT，信息充分题。
- [case-002：保留洞口补门](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/REVIEW.md)：Duplex Apartment，CC BY 4.0，二层唯一空室内门洞；左右开启均允许，信息充分题。
- [窗题格式校验](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/IFC-VALIDATION.md)／[门题格式校验](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/IFC-VALIDATION.md)：schema＋EXPRESS零诊断，两份D均为PASS。
- [门题同步网格查看器](../../../dataset/processed/ifc-repair/repair-comparison/development/case-002/VIEW.html)／[窗题查看器](../../../dataset/processed/ifc-repair/repair-comparison/development/case-001/VIEW.html)：本地生成的HTML，重建命令见下方实现说明。删除门为150378，150478保持原位置及网格。
- [实际实现、检查与命令](development-readiness.md#6-阶段-1-实际交付两道开发题与最小工具)：37项聚焦测试通过；查看器浏览器视觉验收受限，尚未完成；不代表修复模型成绩或运行时隔离已验收。

整体按用户要求保持约 20 个不同源 IFC 的规模，优先许可明确的独立场景族；导出版本、损坏副本和修复副本不增加样本数。开发题与正式未见样本分开，数量口径见[计划 §6.1](plan.md#61-源模型选择)。

用户已审阅第一轮并要求上述修订；新版材料保持待复核，未代写accepted。损伤规模分S1单目标、S2双目标（同类／混合）、S3三个及以上目标，当前实际两题为S1，混合损坏尚未生成。后续澄清题只选位置、楼层或不可推导的必要尺寸等真实缺项。预算账本、执行器、独立评分器和DSH接入尚未实施；未安装软件、启动服务、调用模型或修改生产代码。后续遵守[现有准入协议](../agent-capability-evaluation.md)。
