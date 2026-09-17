# IFC2Text Validation

本目录保存 IFC2Text 从确定性建筑事实到版本化设计说明、再接入现有 text2IFC Generation 公共路径的阶段准入与后续评测材料。

当前入口：

- **最新受控基线 v0.3：** [阶段验证机器记录](../../../dataset/processed/experiments/ifc2text-phase1-20260917/hxp-goal-v03-01/validation/admission.json)（代码 `c9443963`，106 passed）；[简短决策与结果](../../reports/ifc2text-phase1-decisions-2026-09-17.md)。完整说明已生成，真实重建在 Design Brief 截断，累计调用账本暂停，不代表已准许再次付费重试。
- **历史 v0.2：** [Phase 1 写作与公共桥 Stage Admission v0.2（2026-09-17）](phase1-writing-admission-v02-2026-09-17.md) · [机器记录](phase1-writing-admission-v02-2026-09-17.json)
- **历史准入：** [Phase 1 初版 Admission（a333f68b）](phase1-writing-admission-2026-09-17.md) · [机器记录](phase1-writing-admission-2026-09-17.json)。该版本在第一次真实写作揭示高基数 section 后按 invalidation contract 停止用于当前执行。

当前 Admission 只证明对应固定代码版本在 zero-network 条件下通过写作 stage、Provider seam 和公共 Generation bridge 的适用离线门禁。它不是 IFC2Text 能力提升证据，也不等于真实 Provider 往返已经成功。
