# dental-clinic-two-door-two-window-geometry-targeted Door 三方审计报告

## 1. 最终发布结论

- L0：`True`
- L1：`True`
- L2（生产 Semantic Manifest）：`True`
- 可发布：`True`
- 阻塞项：`0`
- 私有 Ground Truth 忠实度警告：`4`

生产修复只使用 damaged IFC、用户请求、Bound ChangeSet 与仍存活的 IFC 事实。original IFC 和被删除对象 GUID 仅在修复完成后进入本私有 comparator。

## 2. Mutation audit：original → damaged（私有）

- Door 数量变化：`-2`
- Window 数量变化：`-2`
- Opening 数量变化：`-4`
- Root 删除/新增：`65` / `0`
- Manifest 中的 Door 均被删除：`True`

这部分只证明 benchmark 损伤范围，不参与 Target、Type、ChangeSet 或 Applicator 决策。

## 3. Production repair audit：damaged → repaired

- operation 数：`4`
- L1 全部通过：`True`
- L2 全部通过：`True`
- Door/Window/Opening 数量变化：`2` / `2` / `4`
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
- 成功映射对象数：`4`
- 非阻塞 fidelity warning：`4`

私有 comparator 只解释修复质量；它无权改变 production release facts，也不会把缺失原值回灌到修复链路。

## 5. 逐对象语义映射

| 类别 | Operation | Original GUID | Repaired GUID | 方法 | 置信度 |
|---|---|---|---|---|---:|
| IfcDoor | operation-door-001 | `1byTDaqS91rBnWJlv$n$m2` | `2JkcPYBqzH_wagVz4peTxS` | mutation_manifest+application_role | 1.0 |
| IfcDoor | operation-door-002 | `35QeWibpT4DfyH3NIf2nTY` | `3C1zg2qEnVqf$lmDvZRwrA` | mutation_manifest+application_role | 1.0 |
| IfcWindow | operation-window-001 | `0otfaO0qPDAhynjJ6DmgEk` | `3NrnJom1nRYOY5P7b5EHsv` | mutation_manifest+application_role | 1.0 |
| IfcWindow | operation-window-002 | `2g$QZpOGbBUxSNx_ZgxJoj` | `2qZ1kjNJjNM9pUqadcFmBi` | mutation_manifest+application_role | 1.0 |

## 6. 几何与 placement 证据

| 类别 | Operation | Opening 覆盖率 | 名义中心偏差 mm | 轴偏差 ° | 原始世界几何≤1mm |
|---|---|---:|---:|---:|---|
| IfcDoor | operation-door-001 | 1.000 | 0.000 | 0.000 | 失败 |
| IfcDoor | operation-door-002 | 1.000 | 0.000 | 0.000 | 失败 |
| IfcWindow | operation-window-001 | 不适用 | 不适用 | 不适用 | 通过 |
| IfcWindow | operation-window-002 | 不适用 | 不适用 | 不适用 | 通过 |

Door 的覆盖率、名义中心和轴向来自 repaired IFC 的 Opening 局部坐标测量；“原始世界几何≤1mm”只来自修复后的私有 comparator。

## 7. Host / Opening / Fill / Storey / Type

| 类别 | Operation | Host | Storey | Type |
|---|---|---|---|---|
| IfcDoor | operation-door-001 | 通过 | 通过 | 失败 |
| IfcDoor | operation-door-002 | 通过 | 通过 | 失败 |
| IfcWindow | operation-window-001 | 通过 | 通过 | 失败 |
| IfcWindow | operation-window-002 | 通过 | 通过 | 失败 |

Door production operation 还逐项验证恰好一条 fill、Opening 恰好 void 一个 Wall、唯一 Storey containment 与唯一 Type 关系；完整机器证据见 `three-way-audit.json`。

## 8. Pset / Qto / Material provenance

| 类别 | Operation | occurrence Pset facts | Qto facts | effective material | provenance | 私有差异数 |
|---|---|---:|---:|---|---|---:|
| IfcDoor | operation-door-001 | 62→0 | 0→0 | 通过 | 通过 | 65 |
| IfcDoor | operation-door-002 | 62→0 | 0→0 | 通过 | 通过 | 65 |
| IfcWindow | operation-window-001 | 61→1 | 0→3 | 通过 | 通过 | 63 |
| IfcWindow | operation-window-002 | 61→1 | 0→3 | 通过 | 通过 | 63 |

原模型中未被用户请求或 Semantic Manifest 授权的 occurrence Pset/Qto 差异保留为私有 fidelity warning；它们不会被伪装成 exact restoration，也不会把 private Ground Truth 泄漏回生产修复。

## 9. 非目标保全

- damaged→repaired 新增 Root：`32`
- 声明新增 Root：`32`
- damaged→repaired 删除 Root：`0`
- 未声明新增 Root：`0`
- 共享 Type 不可变性与其他 Root/关系保全由 production full-model comparator 和 operation scope gate 负责。

## 10. 阻塞项与警告

### 阻塞项

- 无。

### 警告

- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-door-001`：Non-required original occurrence authoring facts remain different; production Manifest still passes.
- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-door-002`：Non-required original occurrence authoring facts remain different; production Manifest still passes.
- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-window-001`：Non-required original occurrence authoring facts remain different; production Manifest still passes.
- `PRIVATE_GROUND_TRUTH_FIDELITY_GAP` / `operation-window-002`：Non-required original occurrence authoring facts remain different; production Manifest still passes.

## 11. 指纹与产物路径

### 运行指纹

- `original_ifc_sha256`：`sha256:b90fe57b8aa9329d762a564770e697d4f7357677484e3a78ede4ab6d2163c0c0`
- `damaged_ifc_sha256`：`sha256:c51b4dc754f7e4f462806c8f2579f791a064022976231e72077e6768c4eef878`
- `repaired_ifc_sha256`：`sha256:7c5db7ccaaa57d1f44aa7ba664b3fe2487ace816ab5b36f4290f197f81c8be29`
- `request_sha256`：`sha256:8371932fd1c49a08424379bacbfeed92367d3dca28d46b7493c061400b2a6549`
- `changeset_sha256`：`sha256:bdfc1e66ef9a2e269cdb221466f42eac6286a10258bbea62084790cbaa363b79`
- `application_sha256`：`sha256:e36390b692aaff47e566c7a612585428d63d5e4a025362c87cdc8ce805d86972`
- `production_evaluation_sha256`：`sha256:42f6502cf0e914945e8010f245c306796ceabc03dbe0afd0c46cd93d575ecbf3`

### 输入产物

- `original`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/original.ifc`
- `damaged`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/damaged.ifc`
- `repaired`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/repaired.ifc`
- `request`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/request.txt`
- `changeset`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/changeset.json`
- `application`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/application.json`
- `evaluation`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/evaluation.json`
- `manifest`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/manifest.json`
- `production_boundary`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-proof-reaudit-fix-20260731-r2/dental-clinic-two-door-two-window-geometry-targeted/production-boundary.json`
