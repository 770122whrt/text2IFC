# vvo-two-door-two-window-mixed Door 三方审计报告

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
- Opening 数量变化：`-2`
- Root 删除/新增：`34` / `0`
- Manifest 中的 Door 均被删除：`True`

这部分只证明 benchmark 损伤范围，不参与 Target、Type、ChangeSet 或 Applicator 决策。

## 3. Production repair audit：damaged → repaired

- operation 数：`4`
- L1 全部通过：`True`
- L2 全部通过：`True`
- Door/Window/Opening 数量变化：`2` / `2` / `2`
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
| IfcDoor | operation-door-001 | `2IUEnGd5v4Yfg1ZlPtd0qa` | `29Zxmk5fjGJAUZtu9obmYS` | mutation_manifest+application_role | 1.0 |
| IfcDoor | operation-door-002 | `1B$rgWypT66viEf2CI1iIv` | `3jV9sCX2DN$vtwzfSJ5Ieo` | mutation_manifest+application_role | 1.0 |
| IfcWindow | operation-window-001 | `2dYMXn0_5AKRbD_0yUIAqJ` | `0MJBBoskLR9vG16v9KBfFE` | mutation_manifest+application_role | 1.0 |
| IfcWindow | operation-window-002 | `08xWVL$9z6JRwr3oWJHoAz` | `2pjOTgXJ5My8gZy7V3OjFb` | mutation_manifest+application_role | 1.0 |

## 6. 几何与 placement 证据

| 类别 | Operation | Opening 覆盖率 | 名义中心偏差 mm | 轴偏差 ° | 原始世界几何≤1mm |
|---|---|---:|---:|---:|---|
| IfcDoor | operation-door-001 | 1.000 | 0.000 | 0.000 | 通过 |
| IfcDoor | operation-door-002 | 1.000 | 0.000 | 0.000 | 通过 |
| IfcWindow | operation-window-001 | 不适用 | 不适用 | 不适用 | 通过 |
| IfcWindow | operation-window-002 | 不适用 | 不适用 | 不适用 | 通过 |

Door 的覆盖率、名义中心和轴向来自 repaired IFC 的 Opening 局部坐标测量；“原始世界几何≤1mm”只来自修复后的私有 comparator。

## 7. Host / Opening / Fill / Storey / Type

| 类别 | Operation | Host | Storey | Type |
|---|---|---|---|---|
| IfcDoor | operation-door-001 | 通过 | 通过 | 通过 |
| IfcDoor | operation-door-002 | 通过 | 通过 | 通过 |
| IfcWindow | operation-window-001 | 通过 | 通过 | 通过 |
| IfcWindow | operation-window-002 | 通过 | 通过 | 通过 |

Door production operation 还逐项验证恰好一条 fill、Opening 恰好 void 一个 Wall、唯一 Storey containment 与唯一 Type 关系；完整机器证据见 `three-way-audit.json`。

## 8. Pset / Qto / Material provenance

| 类别 | Operation | occurrence Pset facts | Qto facts | effective material | provenance | 私有差异数 |
|---|---|---:|---:|---|---|---:|
| IfcDoor | operation-door-001 | 4→0 | 0→0 | 通过 | 变化 | 7 |
| IfcDoor | operation-door-002 | 4→0 | 0→0 | 通过 | 变化 | 7 |
| IfcWindow | operation-window-001 | 4→1 | 0→3 | 通过 | 变化 | 6 |
| IfcWindow | operation-window-002 | 4→1 | 0→3 | 通过 | 变化 | 6 |

原模型中未被用户请求或 Semantic Manifest 授权的 occurrence Pset/Qto 差异保留为私有 fidelity warning；它们不会被伪装成 exact restoration，也不会把 private Ground Truth 泄漏回生产修复。

## 9. 非目标保全

- damaged→repaired 新增 Root：`22`
- 声明新增 Root：`22`
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

- `original_ifc_sha256`：`sha256:b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc`
- `damaged_ifc_sha256`：`sha256:6824086b4171cce034acaa23ad51c3020d87ed44c0aead62979a4b4ad17c4db3`
- `repaired_ifc_sha256`：`sha256:de8ebc1aa849b4968ffa54f19fb3dcfce44a83968b2548104beb63b1c18336cf`
- `request_sha256`：`sha256:07917df5c971a9a7e41f07a02f549514ddb31c1caed559f82d329eb3eb4287c2`
- `changeset_sha256`：`sha256:e402daa51d7cb77fc853927d72a49e8e9297874006558519b3fa2c4d12270801`
- `application_sha256`：`sha256:d79a62184393f14cd5abba0233f7bf5cea781dd0b1bacbd3468fda8a38d5ca45`
- `production_evaluation_sha256`：`sha256:12953ce01c16afb01d572a97876002ef3940f30831d71e786a96bdacf468287c`

### 输入产物

- `original`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/original.ifc`
- `damaged`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/damaged.ifc`
- `repaired`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/repaired.ifc`
- `request`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/request.txt`
- `changeset`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/changeset.json`
- `application`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/application.json`
- `evaluation`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/evaluation.json`
- `manifest`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/manifest.json`
- `production_boundary`：`E:/code for project/bimnet/dataset/processed/ifc-repair/phase11-door-audit-fix-final-2/vvo-two-door-two-window-mixed/production-boundary.json`
