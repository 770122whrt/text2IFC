# IFC2X3 Repair 契约与证据入口

当前 Harness 链路、修复范围和已知限制见[B Harness 当前说明](../repair-comparison/b-common-repair.md)；当前成绩只在[实验表](../../../dataset/processed/experiments/repair-comparison/current/README.md)维护。

## 设计与现行约束

| 文档 | 用途 |
|---|---|
| [design.md](design.md) | 局部 ChangeSet、坐标、发布与评估设计；早期阶段内容按文内日期理解 |
| [target-retrieval-design.md](target-retrieval-design.md) | 目标索引、查询与公开候选证据合同 |
| [implementation-findings.md](implementation-findings.md) | 实施发现及原始决策依据 |
| [Phase 11 SPEC](../../../.planning/phases/11-wall-opening-and-door-operations/11-SPEC.md) | 门、洞口、填充关系与操作边界 |
| [Phase 11 VALIDATION](../../../.planning/phases/11-wall-opening-and-door-operations/11-VALIDATION.md) | 对应验证合同 |
| [Door Storey 勘误](phase11-door-storey-policy-erratum.md) | 贯通墙、洞口标高与楼层归属规则 |
| [结构恢复勘误](phase12-plan07-structural-restoration-erratum-2026-09-03.md) | 区分请求符合性与真实损伤恢复，禁止用不支持的圆柱案例代替 |
| [Structural Type Visual Fidelity 计划](phase12-structural-type-visual-fidelity-plan-2026-09-03.md) | 尚需使用的结构 Type、几何映射、材质与样式修复依据 |

源 IFC 不原地修改；私有 G、损伤配方和删除身份只进入评估侧。真实调用与能力声明遵守[Agent 验证协议](../agent-capability-evaluation.md)，Proof 遵守[人读证据规范](../ifc-repair-proof-format.md)。

## 保留的阶段验证与 Proof

这些是阶段证据，不替代当前代码的准入或最新成绩。

- [Phase 10.3 五窗验证](phase10.3-five-window-batch-validation-report.md)
- [Phase 11 Door / Opening 验证](phase11-door-validation-report.md)；审计前的假阳性保留于[历史 known-failure fixture](https://github.com/770122whrt/text2IFC/blob/d8ee81607c3c1239256c40c4b6dfff1761f40db3/tests/fixtures/ifc_repair/phase11-door-known-failure/README.md)，不属于成功证据
- [Phase 12 / 12.1 梁柱与属性验证](phase12-beam-column-validation-report.md)
- [R1 最终验收入口](../repair-milestone-r1/README.md)
- [工作流 Proof](../../../dataset/processed/proof/README.md)

## 已退役材料

超过两周、已完成且无现行执行依赖的 Repair 计划和旧报告已从本地删除；原文保存在[固定 Git 修订](https://github.com/770122whrt/text2IFC/tree/11f29030f3f3b5967535d16c4c4b31085e21ff64/docs/validation/ifc2x3-changeset)。恢复方式和旧实验目录见[统一 Git 恢复入口](../../../dataset/processed/experiments/README.md#repair-旧材料按需从-git-恢复2026-10-10)。仍被冻结合同直接读取的报告与计划输入保留原位，不修改历史失败或 Proof。
