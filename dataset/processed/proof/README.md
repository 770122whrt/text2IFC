# text2IFC Proof

先选择工作流：[Generation](generation/README.md) · [Repair](repair/README.md)。每个案例直接提供请求、IFC 和中文结论；完整过程从案例 evidence/README.md 进入。

| 人读集合 | 状态 | 本集合直接展示案例 |
|---|---|---:|
| [generation/phase6.6/generation-examples](generation/phase6.6/generation-examples/REPORT.md) | accepted | 6 |
| [repair/phase11/reference-cases](repair/phase11/reference-cases/REPORT.md) | accepted | 16 |
| [repair/phase11/live-uat](repair/phase11/live-uat/REPORT.md) | historical | 1 |
| [repair/phase12/plan07-v2](repair/phase12/plan07-v2/REPORT.md) | pending_human_review | 10 |
| [repair/phase12.1/r1](repair/phase12.1/r1/REPORT.md) | accepted | 12 |

共 45 个直接展示案例。Phase 11 历史 UAT 原有三案，其中两个成功案引用 reference-cases，未重复计算。Plan 07 仍为 pending_human_review、r1_included=false；R1 为独立 accepted 集合。目录整理不改变 Phase 状态或产生新的能力结论。

## 如何读结果

- repair 成功案：request.txt、02-damaged.ifc、03-repaired.ifc、REPORT.md。
- 正确无输出案：request.txt、02-damaged.ifc、NO-REPAIR.md；不得出现 repaired IFC。
- original 只沿用预先合法声明的角色；R1 没有 original，IFCCompare 为 N/A。
- generation：request.txt、model.json、generated.ifc、REPORT.md；不套用 repair 三元组。
- 旧证据中的 accepted、live、replay、offline 与历史局限分别保留。人读验证只检查展示、来源一致性和 reopen，不代替原独立 Proof。

## 保持原位的机器权威

以下目录是冻结或已提交的权威／来源位置，保留原路径以保护已有绑定。日常阅读使用上表。

- [repair 参考权威](ifc-repair-success-cases/manifest.json)：当前主 manifest 16 案。
- [Plan 07 v2 authority](ifc-repair-success-cases-v2-plan07-staging/README.md)：与待审人读集合分离。
- [R1 Proof 0.3](repair-milestone-r1/r1-20260902T152701658266Z-curated/manifest.json)：12 案，11 输出、H4 无输出，40 次 genuine 调用。
- [Phase 11 历史 UAT](phase11-live-uat/uat-20260731T224900289758Z/README.md)。
- [generation 原收纳记录](text2ifc-success-cases/manifest.json)。

[2026-09-03 校验快照](IFC-REPAIR-COLLECTION-VALIDATION-20260903.json)中的 24 案属于撤回前历史记录。commit a1c3d679 已从主集合撤回 8 个旧结构案例；当前数量为 16，不用该快照宣称当前全集通过。负向回归仍在 tests/fixtures/ifc_repair/phase12-plan07-offsite-known-failure/。

## 验证入口

```powershell
.venv/Scripts/python scripts/proof/validate_human_views.py --root dataset/processed/proof/repair/phase12.1/r1
.venv/Scripts/python scripts/ifc_repair/install_plan07_human_proof.py --validate-only
```

其他集合将 --root 换成上表路径。规范见 [IFC repair Proof 展示规范](../../../docs/validation/ifc-repair-proof-format.md)。机器索引见 [PROOF-INVENTORY.json](PROOF-INVENTORY.json)。
