# text2IFC Proof

先选择工作流：[Generation](generation/README.md) · [Repair](repair/README.md)。案例根目录直接提供请求、IFC 和中文结论，过程材料集中在 evidence。

| 集合 | 状态 | 案例 |
|---|---|---:|
| [generation/phase6.6/generation-examples](generation/phase6.6/generation-examples/REPORT.md) | accepted | 6 |
| [generation/phase6.6/three-storey-clarification-ab-20260910](generation/phase6.6/three-storey-clarification-ab-20260910/REPORT.md) | accepted；人工已验收，B保留已知问题 | 2 |
| [repair/phase11/live-uat](repair/phase11/live-uat/REPORT.md) | historical | 1 |
| [repair/phase11/reference-cases](repair/phase11/reference-cases/REPORT.md) | accepted | 16 |
| [repair/phase12/plan07-v2](repair/phase12/plan07-v2/REPORT.md) | accepted | 10 |
| [repair/phase12/presentation-cases](repair/phase12/presentation-cases/REPORT.md) | pending_human_review | 3 |
| [repair/phase12.1/r1](repair/phase12.1/r1/REPORT.md) | accepted | 12 |

共 50 个直接展示案例。历史 live UAT 另引用 reference-cases 的两个成功案，不重复收纳。Plan07 已经用户人工审查通过；材质外观集合等待人工审查；整理不关闭 Phase、不提升模型能力结论。

另有[双层社区阅读活动楼的人工验收记录](generation/phase6.6/two-storey-community-20260909/REPORT.md)：用户于 2026-09-09 验收模型与展示，工程门禁仍为 blocked，未完成终端发布。该独立 review 集合不计入上述 50 案或 accepted machine 索引。

## 如何读案例

- repair：request.txt、02-damaged.ifc、03-repaired.ifc；正确无输出案使用 NO-REPAIR.md。
- original 仅沿用已声明的物理对照/私有评估角色；R1 没有 original，IFCCompare 为 N/A。
- generation：request.txt、model.json、generated.ifc，不使用修复三元组。
- 每个案例 evidence/README.md 提供机器材料入口。人读和机器材料描述同一案例，不是 original/repaired 的区别。

## 证据迁移与验证

用户批准将旧根目录权威集中到工作流集合。新 manifest 使用 text2ifc/workflow-proof-package/0.1：legacy_bundles 逐文件记录旧路径、现位置、SHA-256 和大小；原 FILES、合同、报告字节保持不变，重复 IFC 复用案例根文件。旧报告内的历史路径以该映射解释。

验证入口：scripts/proof/validate_human_views.py --root <collection>。冻结完整验证可用 scripts/proof/materialize_frozen_bundle.py 在临时目录还原旧布局后调用原 validator；不改写旧 schema。迁移验收与现行代码重验结果见 [整理记录](../../../docs/architecture/repository-organization-refactor.md)。

参考集合中的五个旧 Window 案仍有原有证据局限。撤回前 24 案的校验快照保留于 [历史记录](repair/phase11/reference-cases/evidence/history/IFC-REPAIR-COLLECTION-VALIDATION-20260903.json)，不能作为当前 16 案的验收结果。

[机器索引](PROOF-INVENTORY.json) · [展示规范](../../../docs/validation/ifc-repair-proof-format.md)
