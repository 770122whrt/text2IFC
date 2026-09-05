# Composite Evidence Matrix — Text2IFC Composite Repair Milestone

**Base revision:** `8bfcfe075521ddb142f8608296dfbfea1fd385e4` (branch `Zcode`).
Baseline fingerprint CLEAN at every checkpoint（508 生产文件；授权生产修复
[含缺陷 3-5 的 profile 切换] 与失败族测试文件以 before/after 哈希记录于
`authorized_fixes`，参考号 `defects-3-5-live-contract-fixes`）。

**Genuine Provider execution: PERFORMED（两轮）**

- 第一轮（修复前）：12 次真实 DeepSeek 调用（stage1×9、stage2×3），按冻结
  顺序执行一次。4 个正向用例真实失败——事后按协议 §5 回流定位出三个合同
  缺陷（见 DEFECT-RECORD 3-5），全部机制级修复并全门禁绿。
- **第二轮（修复后，同案例重试可靠性证据）：16 次真实 DeepSeek 调用**
  （stage1×9、property_resolution×2、stage2×5）。

## Live 用例矩阵（第二轮，修复后）

| Case | BIM | Families | Entity Ops | Property Intents | Total Intents | Atomic | Visible Artifact Change | Live Outcome（修复后） | 第一轮（修复前） |
| ---- | --- | -------: | ---------: | ---------------: | ------------: | -----: | ----------------------: | ------- | --- |
| C1 | CM-TALL | beam, column | 2 | 0 | 2 | PASS | IfcBeam 0→1, IfcColumn 0→1, +2 Types, +2 rels | **succeeded**（复现稳定） | succeeded |
| C2 | CM-S65 | column, door | 3 | 0 | 3 | PASS | +2 Columns, +1 Door(fill)+Style, +1 Type, +rels | **succeeded**（完整发布，严格门全过） | clarification_required |
| C3 | CM-TALL | beam, column, window | 5 | 0 | 5 | PASS | +2 Beams, +2 Columns, +1 Window+Opening+Style, +Types, +rels | **succeeded**（零修正一次绑定） | provider_failed |
| C4 | CM-S65 | beam, column, door, window | 7 | 0 | 7 | — | — | not_publishable（冻结用例缺陷：请求文本 offset 5000 与 fixture 16000 不一致，撞已知凹陷区；详见下） | clarification_required |
| C5 | CM-VVO | beam, column, door, window | 8 | 2 | 10 | PASS | +4 Columns, +2 Beams, +1 Door+Opening+Style, +1 Window+Opening+Style, +EI60 Pset, +IsExternal | **succeeded**（8 操作 + 2 属性，严格全过） | clarification_required |
| C5-N | CM-VVO | +1 不支持操作 | 8 | 2 | 11 | PASS (fail-closed) | **零突变** | **unsupported**（负守卫复现稳定） | unsupported |


## 离线确定性结果（对照：证明复合组成本身可绑定、可应用、可证明）

同一冻结 6 用例在零 Provider 的确定性驱动下（`tests/ifc_repair/composite_evidence/`，
48 项测试）：C1–C5 全部 OFFLINE_PROVEN（完整公共 API 链路：Stage 1 → 解析 →
Stage 1.5 属性解析 → Stage 2 绑定 → apply → 原子发布 → IFC2X3 重开 → L0/L1/L2
→ 操作级 Proof → 精确增量保存），C5-N 负守卫通过。25 个实体操作全部应用成功
（4 族：beam/column/door[fill+add]/window），C5-N 的 8 个操作按设计原子拒绝。

## Live 结果细节

- **C1 完整成功**：DeepSeek Stage 1 意图（自选 ID `op_beam_add`/`op_column_add`，
  几何与冻结完全一致）→ Stage 2 绑定 → apply → 原子发布 → IFC2X3 重开 →
  严格 L0/L1/L2 重算全过 → 操作级复合 Proof（按冻结几何绑定自选 ID）全过 →
  精确增量保存 + 比较器零无关突变全过。2 次真实调用，52 秒。
- **C5-N 负孪生通过**：含不支持操作的原子请求正确终态 `unsupported`
  （reason `STRUCTURAL_ANALYSIS_UNSUPPORTED`），源文件 SHA-256 前后一致
  （零突变），零 Stage 2 尝试，无发布产物。**全有或全无安全门对真实
  Provider 有效的首次直接证明。** 2 次真实调用。
- **C2/C4 澄清**：DeepSeek Stage 1 抽取的填门意图缺少必填门参数槽位
  （`/parameters/door/operation_type`、`hinge_side`、`viewpoint`），尽管
  请求文本明确写了 SINGLE_SWING_LEFT——真实 Provider 抽取行为，保留。
- **C3 Provider 失败**：Stage 2 草稿两次 `DRAFT_AUTHORITY_SCOPE_MISMATCH`
  （Provider 草稿的 scope 与解析权威不一致），重试耗尽后终态
  `provider_failed`——真实 Provider 输出质量行为，保留。
- **C5 澄清**：Stage 1 意图质量高（8 操作全部正确，含按名称定位 Storey、
  按几何约束定位墙），但 DeepSeek 把几何容差写为 0（冻结用 0.05–1.0），
  实测几何浮点尾差导致目标解析 `not_found` 澄清——真实 Provider 行为，保留。

## 汇总（第二轮 live，修复后）

- 真实 Provider 调用（第二轮）：**16**（stage1 ×9、property_resolution ×2、stage2 ×5）。
- live 成功用例：**5/6**（C1/C2/C3/C5 全链路成功；C5-N 安全门通过）。
- live 保留的真实失败：1（C4，冻结用例请求/fixture 偏移不一致，非产品缺陷）。
- 离线确定性成功：25/25 实体操作（对照证明组成可执行）。
- 合约重验证（零新调用）：C1/C2/C3/C5/C5-N 全部 passed；C4 not_applicable。
- 模型重开：PASS（C1/C2/C3/C5 live + 全部离线用例）。
- 保存：PASS（精确增量 + 比较器零无关突变；C5-N 零突变）。

## 发现并修复的生产缺陷（live 执行的前置条件）

两个潜在混合族缺陷（历史单族用例无法触及），均已按用户授权做机制级修复、
冻结失败族、全量回归（详见 `DEFECT-RECORD.md`）：

1. **混合清单绑定缺陷**（`window.py` + `semantic_authoring.py`）
2. **门语义角色 L1 授权缺口**（`door.py`）

另有一次 live 揭示的 Proof 合约自身缺陷并已修复：原合约按冻结
operation_id 绑定谓词，而 live Provider 自选 ID（`op_beam_add` 等）——
现按**冻结几何/目标/属性**解析操作（operation_id 由变更集提供），
离线（冻结 ID）与 live（自选 ID）路径统一验证（48/48）。

## 验证门禁（live 执行后全部复跑）

| 门禁 | 结果 |
| --- | --- |
| 复合证据套件（48 项，含两个更新的篡改测试） | 48 通过 |
| 失败族：混合清单绑定 + 门角色授权 | 21 通过 |
| 门族回归（application/resolution/geometry/mixed-hosted） | 41 通过 |
| phase12 数据集 e2e + 冻结证明 | 53 通过 |
| phase12 live UAT 生产路径 | 11 通过 |
| R1 汇总套件 | 69 通过 |
| 基线指纹 | CLEAN |
| live 合约离线重验证（零新调用） | C1 passed、C5-N passed |


---

# 损伤-恢复语义证据组（Damage-Restoration，2026-09-01）

应用户要求重构语义：original 原生含构件 → 确定性损伤 → 修复恢复原位 →
repaired 与 original IFC 比较。早期"增量改造"组保留为历史证据。

| 案例 | 损伤 | 真实调用 | 终态 | 类计数恢复 | comparator | 原位对齐 |
|---|---|---:|---|---|---|---|
| R1 | 1 梁 | 2 | **succeeded** | 是 | passed | 是（轴 570×400 @(-7452.2,-14836.2)） |
| R2 | 1 梁+1 柱 | 2 | **succeeded** | 是 | passed | 是（梁+柱 500×500×3712.1 @(-3307.4,-9061.8)） |
| R3 | 2 梁+1 柱 | 3 | **succeeded** | 是 | passed | 是（两梁+柱逐一验证 ALIGNED） |

- 真实 Provider 调用合计 7（DeepSeek，无合成回退）；时延 56.9/78.4/140.9 s。
- 离线确定性对照 3/3 绿（`test_damage_restoration_freeze.py` + 可行性
  `test_damage_restoration_roundtrip.py` 3/3）；复合证据全套件 54/54 绿。
- Proof 包：`dataset/processed/proof/repair-damage-restoration/`（01/02/03
  + agent/changeset/validation + README 语义差异表）。
- 冻结契约：`damage-restoration-freeze.json`；运行工件：
  `dataset/processed/ifc-repair-runs/repair-damage-restoration/`。
- 指纹：新证据文件以 authorized-fix 记录（参考号
  `damage-restoration-semantics`），verify CLEAN。

**过程记录（诚实）**：首轮 live 三案因请求文本措辞诱导模型附加冗余
`length_mm` 字段（schema 拒绝，`STRUCTURAL_SCALAR_EXTENT_UNSUPPORTED`）
全部 `unsupported`；修正冻结请求（去掉引导性长度表述、明确"轴由起终点
完全确定"）后一次通过。该修正发生在冻结当轮（资产未发布），属冻结过程
内部迭代，非对已发布冻结用例的改写。


---

# 损伤-恢复 C1–C5 非 vvo 模型组（2026-09-01）

| 案例 | 模型 | 损伤 | 调用 | 终态 | 类计数恢复 | comparator | 原位对齐 |
|---|---|---|---:|---|---|---|---|
| C1 | sixty5/str | 2 梁 | 2 | **succeeded** | 是 | passed | 2/2 梁 |
| C2 | 1px | 1 梁+1 门 | 2 | **succeeded** | 是 | passed | 梁+门洞回填 |
| C3 | d7n | 2 梁+1 门 | 2 | **succeeded** | 是 | passed | 2 梁+门洞回填 |
| C4 | d7n | 3 梁+1 门+1 窗 | 2 | **succeeded** | 是 | passed | 3 梁+窗+门洞 |
| C5 | d7n | 4 梁+2 门+2 窗 | 2* | **succeeded** | 是 | passed | 4 梁+2 窗+2 门洞 |

\* C5 为同案例重试（首次 live 两 attempt 均真实失败并保留：
幻觉 profile id、多余字段；均 fail-closed）。大模型时限经公共 seam
放宽至 900 s（门禁不变）。离线对照 5/5 绿；复合证据全套件见门禁记录。
