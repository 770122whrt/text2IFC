# IFC2X3 Local ChangeSet 验证索引

最新验收：[Phase 10.1 显式 IFC 属性写入与验证报告](phase10.1-validation-report.md)。
它覆盖标准属性、自定义属性确认、Type 精确复用/系统模板 fallback、
LargeBuilding 离线验收与真实 DeepSeek 双案例 UAT，并冻结 Phase 10.2 的
检索输出边界。

Phase 8 验证报告：[Evaluation 0.2、Benchmark Gold 隔离与 LargeBuilding 零 Provider 基线](phase8-validation-report.md)（2026-07-19 通过）。

本目录只维护同一项验证工作的权威设计、实施约束与可追溯证据，避免 Window
首个案例和后续墙洞、门、梁、柱能力分散到不同文档后发生语义漂移。

| 文档 | 职责 | 当前状态 |
|---|---|---|
| [phase10-single-pipeline-input-output.md](phase10-single-pipeline-input-output.md) | 单个真实案例的全链路 Input/Output、各 Part 作用、产物位置和最终 IFC 效果 | 2026-07-22；面向工程理解与复现 |
| [phase10-validation-report.md](phase10-validation-report.md) | Window 语义 manifest/Bound ChangeSet、原子写回、LargeBuilding 离线与四路径 DeepSeek L1/L2 | 2026-07-22 通过；后续细分为 10.1 精确属性写入和 10.2 检索/RAG |
| [phase9.1-validation-report.md](phase9.1-validation-report.md) | Type/Occurrence 证据修正、无 GUID Prototype 解析、LargeBuilding 与四路径 DeepSeek UAT | 2026-07-21 通过；真实 L2 缺口交接 Phase 10 |
| [phase9-stage1-contract-repair-report.md](phase9-stage1-contract-repair-report.md) | Stage 1 partial intent、系统指纹封装、缺参 feedback 与双路径 DeepSeek UAT | 2026-07-20 两组 Stage 1 合同通过；整体因既有 L2 evidence conflict 未发布 |
| [phase9-validation-report.md](phase9-validation-report.md) | 单一 IFC + 文本 RepairAPI、薄 CLI、离线/LargeBuilding 与真实 DeepSeek UAT | 2026-07-20 确定性验收通过；Stage 1 修复后 live 双路径已进入 Stage 2 |
| [design.md](design.md) | 设计权威、坐标语义、能力边界、验收标准与决策日志 | 离线闭环与一次 DeepSeek live UAT 均已通过 |
| [implementation-prompt.md](implementation-prompt.md) | 按设计实施的顺序、交付物和测试清单 | 与设计同步 |
| [reuse-map.md](reuse-map.md) | 现有模块复用与新增模块理由 | 已完成首轮 |
| [implementation-findings.md](implementation-findings.md) | 实施证据、冲突、处理结果和外部阻塞 | 持续追加 |
| [ground-truth-comparison.md](ground-truth-comparison.md) | 完整 Pipeline、Agent 输入输出、编译产物与 original-vs-repaired 直比 | L1 通过；L2/L3 未通过或未定义 |
| [target-retrieval-design.md](target-retrieval-design.md) | GUID/Name/方位/空间/几何混合索引、TargetQuery 与候选证据合同 | v1.1 Phase 7 已实现并验证 |
| [phase7-validation-report.md](phase7-validation-report.md) | Phase 7 精确命令、LargeBuilding 计数、实测数据、拒绝证据与边界 | 2026-07-19 通过 |

## 已实现入口

- 构建并查询本地 IFC 目标索引：
  `.venv\Scripts\python scripts\ifc_repair\index.py build <source.ifc> --database <index.sqlite>`
  `.venv\Scripts\python scripts\ifc_repair\index.py query <index.sqlite> --query <query.json>`
- 运行离线确定性案例：
  `.venv\Scripts\python scripts\ifc_repair\run_case.py <output> --mode fake`
- 检查真实 Provider 配置：
  `.venv\Scripts\python scripts\ifc_repair\run_case.py --check-config`
- 运行真实 Provider UAT：
  `.venv\Scripts\python scripts\ifc_repair\run_case.py <output> --mode live`
  - 默认读取仓库根目录 `.env`。
  - 当前活动路径为 `deepseek-openai-compatible`。
  - live 请求、响应、事件和脱敏 metadata 会进入证据包。
- 已冻结离线证据：
  `dataset/processed/ifc-repair/cases/large-building-window-repair-001-offline-v1/`
- 已通过的真实 DeepSeek UAT 证据：
  `dataset/processed/ifc-repair/cases/large-building-window-repair-001-deepseek-live-20260718-v2/`

## 能力边界

当前生产 handler 只支持 `add_window_with_opening_to_wall` 与 IFC2X3 直线墙。
公共 ChangeSet envelope、Operation Registry、Audit、事务应用与 Comparator 已为
异构 operation 留出并测试接口。以下仍是后续能力，不得宣称已实现：

- 仅挖墙洞；
- 门及其洞口；
- 梁与柱；
- 删除构件和更新 placement；
- BIMNet 大样本适配；
- 曲面、曲线或分段墙。
