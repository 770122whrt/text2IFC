# vvo-five-door-authority-public-repair Door 三方审计报告

## 1. 最终发布结论

- L0：`True`
- L1：`True`
- L2（生产 Semantic Manifest）：`True`
- 可发布：`True`
- 阻塞项：`0`
- 私有 Ground Truth 忠实度警告：`5`

生产修复只使用 damaged IFC、用户请求、Bound ChangeSet 与仍存活的 IFC 事实。original IFC 和被删除对象 GUID 仅在修复完成后进入本私有 comparator。

## 2. Mutation audit：original → damaged（私有）

- Door 数量变化：`-5`
- Window 数量变化：`0`
- Opening 数量变化：`0`
- Root 删除/新增：`43` / `0`
- Manifest 中的 Door 均被删除：`True`

这部分只证明 benchmark 损伤范围，不参与 Target、Type、ChangeSet 或 Applicator 决策。

## 3. Production repair audit：damaged → repaired

- operation 数：`5`
- L1 全部通过：`True`
- L2 全部通过：`True`
- Door/Window/Opening 数量变化：`5` / `0` / `0`
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
- 成功映射对象数：`5`
- 非阻塞 fidelity warning：`5`

私有 comparator 只解释修复质量；它无权改变 production release facts，也不会把缺失原值回灌到修复链路。

## 5. 逐对象语义映射

| 类别 | Operation | Original GUID | Repaired GUID | 方法 | 置信度 |
|---|---|---|---|---|---:|
| IfcDoor | operation-door-001 | `2IUEnGd5v4Yfg1ZlPtd0qa` | `0iVBzpj9vOuPt7qg1ElgYI` | mutation_manifest+application_role | 1.0 |
| IfcDoor | operation-door-002 | `2IUEnGd5v4Yfg1ZlPtd0tI` | `0BUuoYFZ5NXuvIhlQWOe83` | mutation_manifest+application_role | 1.0 |
| IfcDoor | operation-door-003 | `08xWVL$9z6JRwr3oWJHoYK` | `0SED3i33rQV83AWvReyDz8` | mutation_manifest+application_role | 1.0 |
| IfcDoor | operation-door-004 | `08xWVL$9z6JRwr3oWJHoYg` | `1WIs4DRV9V$gmeuQFzcjcJ` | mutation_manifest+application_role | 1.0 |
| IfcDoor | operation-door-005 | `08xWVL$9z6JRwr3oWJHpOf` | `1odWwIghLL8woxa12SGbjk` | mutation_manifest+application_role | 1.0 |

## 6. 几何与 placement 证据

| 类别 | Operation | Opening 覆盖率 | 名义中心偏差 mm | 轴偏差 ° | 原始世界几何≤1mm |
|---|---|---:|---:|---:|---|
| IfcDoor | operation-door-001 | 1.000 | 0.000 | 0.000 | 失败 |
| IfcDoor | operation-door-002 | 1.000 | 0.000 | 0.000 | 失败 |
| IfcDoor | operation-door-003 | 1.000 | 0.000 | 0.000 | 失败 |
| IfcDoor | operation-door-004 | 1.000 | 0.000 | 0.000 | 失败 |
| IfcDoor | operation-door-005 | 1.000 | 0.000 | 0.000 | 失败 |

Door 的覆盖率、名义中心和轴向来自 repaired IFC 的 Opening 局部坐标测量；“原始世界几何≤1mm”只来自修复后的私有 comparator。

## 7. Host / Opening / Fill / Storey / Type

| 类别 | Operation | Host | Storey | Type |
|---|---|---|---|---|
| IfcDoor | operation-door-001 | 通过 | 通过 | 失败 |
| IfcDoor | operation-door-002 | 通过 | 通过 | 失败 |
| IfcDoor | operation-door-003 | 通过 | 通过 | 失败 |
| IfcDoor | operation-door-004 | 通过 | 通过 | 失败 |
| IfcDoor | operation-door-005 | 通过 | 通过 | 失败 |

Door production operation 还逐项验证恰好一条 fill、Opening 恰好 void 一个 Wall、唯一 Storey containment 与唯一 Type 关系；完整机器证据见 `three-way-audit.json`。

## 8. Pset / Qto / Material provenance

| 类别 | Operation | occurrence Pset facts | Qto facts | effective material | provenance | 私有差异数 |
|---|---|---:|---:|---|---|---:|
| IfcDoor | operation-door-001 | 4→0 | 0→0 | 失败 | 变化 | 7 |
| IfcDoor | operation-door-002 | 4→0 | 0→0 | 失败 | 变化 | 7 |
| IfcDoor | operation-door-003 | 4→0 | 0→0 | 失败 | 变化 | 7 |
| IfcDoor | operation-door-004 | 4→0 | 0→0 | 失败 | 变化 | 7 |
| IfcDoor | operation-door-005 | 4→0 | 0→0 | 失败 | 变化 | 7 |

原模型中未被用户请求或 Semantic Manifest 授权的 occurrence Pset/Qto 差异保留为私有 fidelity warning；它们不会被伪装成 exact restoration，也不会把 private Ground Truth 泄漏回生产修复。

## 9. 非目标保全

- damaged→repaired 新增 Root：`20`
- 声明新增 Root：`20`
- damaged→repaired 删除 Root：`0`
- 未声明新增 Root：`0`
- 共享 Type 不可变性与其他 Root/关系保全由 production full-model comparator 和 operation scope gate 负责。

## 10. 阻塞项与警告

### 阻塞项

- 无。

### 警告

- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-door-001`：Non-required original occurrence authoring facts remain different; production Manifest still passes.
- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-door-002`：Non-required original occurrence authoring facts remain different; production Manifest still passes.
- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-door-003`：Non-required original occurrence authoring facts remain different; production Manifest still passes.
- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-door-004`：Non-required original occurrence authoring facts remain different; production Manifest still passes.
- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-door-005`：Non-required original occurrence authoring facts remain different; production Manifest still passes.

## 11. 指纹与产物路径

### 运行指纹

- `original_ifc_sha256`：`sha256:b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc`
- `damaged_ifc_sha256`：`sha256:d91addae033f50c564cb3dfefaa7df496212ddd20da86d91bdd1ea256eb7373f`
- `repaired_ifc_sha256`：`sha256:a7e085242452f8b312173eb8aa11b08115971a4140f0a724e9850f5550270e03`
- `request_sha256`：`sha256:64e86f704b8f838fe7e16a9ae1de9c0db87bcd79f14a755553a4a1653c33abe0`
- `changeset_sha256`：`sha256:92dfc67819d52e3caf6f12f2cd391d90c2e3838765bcf215ed09027d7f188d86`
- `application_sha256`：`sha256:eaa24fefbbbcf203547e596ecfe976a46b5febfa7c4908d246b640298b085279`
- `production_evaluation_sha256`：`sha256:0e23263b94f6fb73ac9ce64b4b0d5a1ff1a6e598550440ab46c49846a6846df5`

### 输入产物

- `original`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/original.ifc`
- `damaged`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/damaged.ifc`
- `repaired`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/repaired.ifc`
- `request`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/request.txt`
- `changeset`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/changeset.json`
- `application`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/application.json`
- `evaluation`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/evaluation.json`
- `manifest`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/manifest.json`
- `production_boundary`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-authority-audit-final-2/vvo-five-door-authority-public-repair/production-boundary.json`
