# IFC2X3 Local ChangeSet 验证索引

Phase 11 当前状态见
[Door / Opening 验证报告](phase11-door-validation-report.md)：合同、索引、
确定性解析、IFC 写入、L1/L2、occurrence comparator 以及 LargeBuilding/vvo
离线链路已经通过。2026-07-29 至 2026-07-30 的严格复审修复了“关系存在但
Door 几何未填入 Opening”的假阳性。最终权威复跑采用独立 damaged-only
生产进程，通过纯几何签名完成一组两窗两门和一组五门修复；original 与
mutation mapping 只在 repaired IFC 生成后的私有 comparator 中出现。
真实 DeepSeek 命令此前在进入 Provider 前被外部执行额度阻塞，实际
Stage 1/Stage 2 调用数均为 0，因此 Phase 11 尚未最终关闭。

下一阶段设计：
[Phase 11 Wall Opening 与 Door Operations SPEC](../../../.planning/phases/11-wall-opening-and-door-operations/11-SPEC.md)。
它冻结 Opening-only、Door+Opening、Door 填入既有 Opening、DoorStyle
复用/生成、开启方向澄清、RepairIntent 路由、按 operation 加载 few-shot，
以及单门/五门/混合构件/大型 IFC/真实 DeepSeek 的验收边界。五份执行计划、
实现研究和验证策略已经落地；当前可宣称离线确定性 Door 修复能力，但不得把
尚未执行的真实 Provider UAT 说成成功。

最新验收：[Phase 10.5 Window Occurrence Fidelity 与验证加速报告](phase10.5-window-fidelity-validation-report.md)。
  它记录 occurrence 属性/Quantity 输入与授权复用、Ground Truth Comparator、
  不可变 validation cache，以及 AdvancedProject 冷启动 62.687 秒、热缓存
  23.562 秒的完整验证。真实 DeepSeek r21 no-fallback UAT 已通过。

当前可直接人工检查的单窗/多窗成功产物集中在
[IFC Repair 成功案例集](../../../dataset/processed/proof/ifc-repair-success-cases/README.md)。
每个案例都包含 original、damaged、repaired IFC、用户输入、Agent 输出、
Bound ChangeSet、验证证据和独立报告。

审计前的 Door 假阳性没有留在成功案例中；原始失败二进制、哈希和缺陷说明保存在
[Phase 11 Door known-failure fixture](../../../tests/fixtures/ifc_repair/phase11-door-known-failure/README.md)。

人工属性核验：
[LargeBuilding 真实修复 Window 属性对比](phase10.1-largebuilding-window-property-comparison.md)。
它逐项区分 occurrence-direct、Type-inherited、用户新增和缺失属性，避免将
当前 L2 通过误解为完整 authoring metadata 复刻。

Phase 8 验证报告：[Evaluation 0.2、Benchmark Gold 隔离与 LargeBuilding 零 Provider 基线](phase8-validation-report.md)（2026-07-19 通过）。

本目录只维护同一项验证工作的权威设计、实施约束与可追溯证据，避免 Window
首个案例和后续墙洞、门、梁、柱能力分散到不同文档后发生语义漂移。

| 文档 | 职责 | 当前状态 |
|---|---|---|
| [Phase 11 SPEC](../../../.planning/phases/11-wall-opening-and-door-operations/11-SPEC.md) | Opening/Door operation、Type/swing/position/属性边界、Prompt Profile、L1/L2 和验收矩阵 | 已实现；2026-07-29 严格 Door 几何/Storey 审计通过 |
| [Phase 11 RESEARCH](../../../.planning/phases/11-wall-opening-and-door-operations/11-RESEARCH.md) | 当前 Window 专用耦合、IFC2X3 DoorStyle/Openings 事实、版本升级和推荐扩展缝 | 2026-07-28 规划研究完成 |
| [Phase 11 VALIDATION](../../../.planning/phases/11-wall-opening-and-door-operations/11-VALIDATION.md) | schema、索引、authoring、L1/L2、批量/混合、大型 IFC、真实 DeepSeek 和 Proof 验收 | 2026-07-28 验证矩阵完成 |
| [Phase 11 Door Storey Policy Erratum](phase11-door-storey-policy-erratum.md) | 多楼层贯通墙中 direct containment 与 Opening 高度上下文冲突时的正式 Storey 决策 | 2026-07-30 已冻结并有 fail-closed 回归 |
| [Phase 11 执行计划](../../../.planning/phases/11-wall-opening-and-door-operations/11-01-PLAN.md) | 五步顺序入口：契约/Prompt → 索引/解析 → IFC 写入 → 评估 → 数据集/live UAT | 离线实现与 Proof 完成；真实 Provider UAT 待执行 |
| [phase10.5-window-fidelity-validation-report.md](phase10.5-window-fidelity-validation-report.md) | occurrence 属性输入/授权复用、Ground Truth Comparator、validation cache、冷/热大型 IFC 性能与真实 DeepSeek UAT | 2026-07-26 全部通过；Production/private L1/L2 与 occurrence fidelity passed |
| [phase10.4-comparator-0.2-validation-report.md](phase10.4-comparator-0.2-validation-report.md) | 大型 IFC 全局保全门禁、fail-closed 指纹、三次性能/内存基准与完整 Production 重放 | 2026-07-25 Comparator 与 AdvancedProject 五窗 L1/L2/发布闭环通过 |
| [phase10.3-five-window-batch-validation-report.md](phase10.3-five-window-batch-validation-report.md) | dataset 审计、五窗 damage/repair、统一 ChangeSet、原子回滚、逐项 L1/L2、真实 DeepSeek 与大型 IFC 矩阵 | 2026-07-24 通过；五项 L1/L2 passed |
| [phase10.2-property-knowledge-validation-report.md](phase10.2-property-knowledge-validation-report.md) | 自然语言属性解析、token 边界、BGE-M3/Qdrant、通用 occurrence 写入和真实 DeepSeek UAT | 2026-07-24 通过；L1/L2 passed |
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

Phase 10.1 additional validation:
[Window effective-property full replication and IfcDiff report](phase10.1-full-window-replication-and-ifcdiff-report.md).
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

当前生产 Registry 支持 Window、Opening-only、Door+Opening 和 Door 填入既有
Opening 的 IFC2X3 直线墙操作。Door 必须通过实际洞口几何、fill/void 拓扑、
Opening 实际标高楼层、Type 与 L2 必需事实的联合门禁。
公共 ChangeSet envelope、Operation Registry、Audit、事务应用与 Comparator 已为
异构 operation 留出并测试接口。以下仍是后续能力，不得宣称已实现：

- 梁与柱；
- 删除构件和更新 placement；
- BIMNet 大样本适配；
- 曲面、曲线或分段墙。
