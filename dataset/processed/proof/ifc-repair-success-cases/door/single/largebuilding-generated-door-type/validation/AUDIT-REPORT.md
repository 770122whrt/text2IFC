# largebuilding-generated-door-type Door 三方审计报告

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
- Opening 数量变化：`-1`
- Root 删除/新增：`31` / `0`
- Manifest 中的 Door 均被删除：`True`

这部分只证明 benchmark 损伤范围，不参与 Target、Type、ChangeSet 或 Applicator 决策。

## 3. Production repair audit：damaged → repaired

- operation 数：`1`
- L1 全部通过：`True`
- L2 全部通过：`True`
- Door/Window/Opening 数量变化：`1` / `0` / `1`
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
| IfcDoor | operation-generated-door-001 | `2cXV28XOjE6f6irgi0COhu` | `3WGF1dkUzHkung2ItzKtYu` | mutation_manifest+application_role | 1.0 |

## 6. 几何与 placement 证据

| 类别 | Operation | Opening 覆盖率 | 名义中心偏差 mm | 轴偏差 ° | 原始世界几何≤1mm |
|---|---|---:|---:|---:|---|
| IfcDoor | operation-generated-door-001 | 1.000 | 0.000 | 0.000 | 失败 |

Door 的覆盖率、名义中心和轴向来自 repaired IFC 的 Opening 局部坐标测量；“原始世界几何≤1mm”只来自修复后的私有 comparator。

## 7. Host / Opening / Fill / Storey / Type

| 类别 | Operation | Host | Storey | Type |
|---|---|---|---|---|
| IfcDoor | operation-generated-door-001 | 通过 | 通过 | 失败 |

Door production operation 还逐项验证恰好一条 fill、Opening 恰好 void 一个 Wall、唯一 Storey containment 与唯一 Type 关系；完整机器证据见 `three-way-audit.json`。

## 8. Pset / Qto / Material provenance

| 类别 | Operation | occurrence Pset facts | Qto facts | effective material | provenance | 私有差异数 |
|---|---|---:|---:|---|---|---:|
| IfcDoor | operation-generated-door-001 | 31→0 | 3→0 | 失败 | 变化 | 68 |

原模型中未被用户请求或 Semantic Manifest 授权的 occurrence Pset/Qto 差异保留为私有 fidelity warning；它们不会被伪装成 exact restoration，也不会把 private Ground Truth 泄漏回生产修复。

## 9. 非目标保全

- damaged→repaired 新增 Root：`6`
- 声明新增 Root：`6`
- damaged→repaired 删除 Root：`0`
- 未声明新增 Root：`0`
- 共享 Type 不可变性与其他 Root/关系保全由 production full-model comparator 和 operation scope gate 负责。

## 10. 阻塞项与警告

### 阻塞项

- 无。

### 警告

- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-generated-door-001`：Non-required original occurrence authoring facts remain different; production Manifest still passes.

## 11. 指纹与产物路径

### 运行指纹

- `original_ifc_sha256`：`sha256:102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725`
- `damaged_ifc_sha256`：`sha256:fed14afd7b68fa79afee817b4f73e3fe391415e2e515b7a329744ba78aeeb10f`
- `repaired_ifc_sha256`：`sha256:2af345dc8edd0b986b22b669ced51a8fd6812e1756f79dd76bb3e78ca0ba3858`
- `request_sha256`：`sha256:b9ca64a69dd23e23e41753a10fa657105e3d995027b55fb27fef8e27267c5004`
- `changeset_sha256`：`sha256:4ce1b1219898c4e3d90f8fd1728a0b91f66bb8a9f90f5d1cd3cdb05bf50b83bd`
- `application_sha256`：`sha256:3fa704c54d3c8c1d269a9895f11a33b947c963fe9825edfac87f66a9df6219f4`
- `production_evaluation_sha256`：`sha256:b49ef8669137d1b7c0543d891b0b1fb3ae9f1d7c0f7784e4460da1694d99fca5`

### 输入产物

- `original`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/original.ifc`
- `damaged`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/damaged.ifc`
- `repaired`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/repaired.ifc`
- `request`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/request.txt`
- `changeset`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/changeset.json`
- `application`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/application.json`
- `evaluation`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/evaluation.json`
- `manifest`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/manifest.json`
- `production_boundary`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/largebuilding-generated-door-type/production-boundary.json`
