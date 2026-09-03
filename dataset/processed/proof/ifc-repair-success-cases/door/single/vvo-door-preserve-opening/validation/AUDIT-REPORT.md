# vvo-door-preserve-opening Door 三方审计报告

## 1. 最终发布结论

- L0：`True`
- L1：`True`
- L2（生产 Semantic Manifest）：`True`
- 可发布：`True`
- 阻塞项：`0`
- 私有 Ground Truth 忠实度警告：`1`

生产修复只使用 damaged IFC、用户请求、Bound ChangeSet 与仍存活的 IFC 事实。original IFC 和被删除对象 GUID 仅在修复完成后进入本私有 comparator。

## 2. Mutation audit：original → damaged（私有）

- Door 数量变化：`-1`
- Window 数量变化：`0`
- Opening 数量变化：`0`
- Root 删除/新增：`8` / `0`
- Manifest 中的 Door 均被删除：`True`

这部分只证明 benchmark 损伤范围，不参与 Target、Type、ChangeSet 或 Applicator 决策。

## 3. Production repair audit：damaged → repaired

- operation 数：`1`
- L1 全部通过：`True`
- L2 全部通过：`True`
- Door/Window/Opening 数量变化：`1` / `0` / `0`
- 未声明新增 Root：`0`
- Ground Truth 泄漏检查：`True`

### L0 检查

| 检查 | 状态 |
|---|---|
| L0_REOPEN_ORIGINAL | passed |
| L0_REOPEN_DAMAGED | passed |
| L0_REOPEN_REPAIRED | passed |
| L0_BASE_MODEL_FINGERPRINT | passed |
| L0_SOURCE_REQUEST_HASH | passed |
| L0_OPERATION_IDENTITY | passed |
| L0_RELATIONSHIP_INTEGRITY | passed |
| L0_PRODUCTION_INPUT_BOUNDARY | passed |
| L0_SOURCE_FILES_UNCHANGED | passed |

## 4. Private fidelity：original → repaired

- 完整 authoring exactness：`False`
- 成功映射对象数：`1`
- 非阻塞 fidelity warning：`1`

私有 comparator 只解释修复质量；它无权改变 production release facts，也不会把缺失原值回灌到修复链路。

## 5. 逐对象语义映射

| 类别 | Operation | Original GUID | Repaired GUID | 方法 | 置信度 |
|---|---|---|---|---|---:|
| IfcDoor | operation-vvo-door-preserve-opening | `2IUEnGd5v4Yfg1ZlPtd0qa` | `29wFPfqAzOUwBFe2s9SBmg` | mutation_manifest+application_role | 1.0 |

## 6. 几何与 placement 证据

| 类别 | Operation | Opening 覆盖率 | 名义中心偏差 mm | 轴偏差 ° | 原始世界几何≤1mm |
|---|---|---:|---:|---:|---|
| IfcDoor | operation-vvo-door-preserve-opening | 1.000 | 0.000 | 0.000 | 通过 |

Door 的覆盖率、名义中心和轴向来自 repaired IFC 的 Opening 局部坐标测量；“原始世界几何≤1mm”只来自修复后的私有 comparator。

## 7. Host / Opening / Fill / Storey / Type

| 类别 | Operation | Host | Storey | Type |
|---|---|---|---|---|
| IfcDoor | operation-vvo-door-preserve-opening | 通过 | 通过 | 通过 |

Door production operation 还逐项验证恰好一条 fill、Opening 恰好 void 一个 Wall、唯一 Storey containment 与唯一 Type 关系；完整机器证据见 `three-way-audit.json`。

## 8. Pset / Qto / Material provenance

| 类别 | Operation | occurrence Pset facts | Qto facts | effective material | provenance | 私有差异数 |
|---|---|---:|---:|---|---|---:|
| IfcDoor | operation-vvo-door-preserve-opening | 4→0 | 0→0 | 通过 | 变化 | 7 |

原模型中未被用户请求或 Semantic Manifest 授权的 occurrence Pset/Qto 差异保留为私有 fidelity warning；它们不会被伪装成 exact restoration，也不会把 private Ground Truth 泄漏回生产修复。

## 9. 非目标保全

- damaged→repaired 新增 Root：`3`
- 声明新增 Root：`3`
- damaged→repaired 删除 Root：`0`
- 未声明新增 Root：`0`
- 共享 Type 不可变性与其他 Root/关系保全由 production full-model comparator 和 operation scope gate 负责。

## 10. 阻塞项与警告

### 阻塞项

- 无。

### 警告

- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-vvo-door-preserve-opening`：Non-required original occurrence authoring facts remain different; production Manifest still passes.

## 11. 指纹与产物路径

### 运行指纹

- `original_ifc_sha256`：`sha256:b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc`
- `damaged_ifc_sha256`：`sha256:a8558c195d1dba8277e9bcd9b0ee047e145658d3d1068b9aea0f1affac0c68c6`
- `repaired_ifc_sha256`：`sha256:43ef5af0ad9de74b3c7a36b2e94f5a51323190c1033cf4c1375d4fd96e3a6d43`
- `request_sha256`：`sha256:a5b21baf6467ed9b9642b9611afbb945c5a816bc3124b4fb3f7bdeff187997d4`
- `changeset_sha256`：`sha256:2563f51c90863fa4d1e98b0adf8f0d64a10b4d020d743aef883e068a187b0e9a`
- `application_sha256`：`sha256:da04df9d8753ad030206b06e4a23fc51755f088f92b56d02aa40483393e8aa9b`
- `production_evaluation_sha256`：`sha256:446cebf55201fe942f4c18bd7e58b6885490e7b27f2ae8f340424161f932603c`

### 输入产物

- `original`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/original.ifc`
- `damaged`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/damaged.ifc`
- `repaired`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/repaired.ifc`
- `request`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/request.txt`
- `changeset`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/changeset.json`
- `application`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/application.json`
- `evaluation`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/evaluation.json`
- `manifest`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/manifest.json`
- `production_boundary`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-door-preserve-opening/production-boundary.json`
