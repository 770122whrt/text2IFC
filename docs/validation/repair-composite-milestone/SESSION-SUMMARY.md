# 损伤-恢复里程碑会话总结（Session Summary）

**日期：** 2026-09-01
**范围：** Composite Repair Milestone 语义重构（增量改造 → 损伤-恢复）、
C1–C5 非 vvo 模型组、真实 DeepSeek 执行、用户驱动的严格 IFCcompare 审计与
三轮缺陷修复、proof 策展与验收。
**基础 revision：** `8bfcfe07`（branch `Zcode`）

---

## 一、工作与代码修改

### 1.1 语义重构（用户决策）

用户指出早期复合组（C1–C5 增量改造语义）的根本缺陷：检验的 beam/column
在 original 与 damaged 中都不存在。语义整体重构为：

> original（构件原生存在）→ 确定性损伤（删除请求对应构件）→
> 修复（恢复到被移除构件的原位几何）→ repaired 与 original IFCcompare

### 1.2 R1–R3（vvo 首组损伤-恢复）

- 模型 vvo（原生 6 梁+5 柱+26 门+23 窗），损伤深度递增
  （1 梁 → 1 梁+1 柱 → 2 梁+1 柱）
- 离线确定性回放 3/3 绿；真实 DeepSeek 3/3 成功
  （类计数恢复、原位对齐、comparator passed）

### 1.3 C1–C5（非 vvo 组，三模型）

模型选择：**sixty5/str**（354 梁纯结构大模型）、**1px**（四族齐全）、
**d7n**（全四族）。损伤面 2 → 8 构件（梁+门+窗复合）。

执行经历 v1→v4 四轮（真实失败全部保留在 `ifc-repair-runs/` 下）：

| 轮次 | 结果 | 暴露的问题 |
|---|---|---|
| v1 | 3/5 | 门契约不可达（NOTDEFINED 路径未教）、请求措辞诱导 |
| v2 | 4/5 | C1 楼层错（见缺陷 7）、属性全丢（P2 范围） |
| v3 | 1/5 | 属性句措辞诱导模型引用被删构件原名 → 目标解析 fail-closed |
| **v4** | **5/5** | 全部成功：类计数恢复 + comparator passed + 84 条属性恢复 |

### 1.4 产品代码修改（全部机制级，零案例引用）

| 文件 | 修改 | 缺陷 |
|---|---|---|
| `operations/window.py` + `semantic_authoring.py` | window 语义清单升 v0.3（与兄弟族对齐） | 1 |
| `operations/door.py` | door L1 授权覆盖 `semantic_door_*` 全角色空间 | 2 |
| `composite_proof.py` | Proof 谓词按冻结几何/目标/属性解析（Provider 自选 ID） | 3 |
| `changesets.py` | draft authority scope/evidence 集合语义比较 | 4 |
| `operations/door.py`+`window.py`（profile v0.3/v0.2） | 发布可达契约（formal_enum_explicit 教学等） | 5 |
| `request_stage.py` | **`canonicalize_semantic_bundle_claims`**：bundle 属性声明解析后立即内联进 intent，使 evidence/coordinator/全下游可见 | 6 |
| `request_stage.py`（早前） | 澄清空槽位等（见 DEFECT-RECORD 3-5） | 3-5 |

辅助层（非产品代码）：live runner / curator / report 生成器 /
audit 脚本（`scripts/ifc_repair/composite_evidence/`、
`composite-evidence-audit/`）。

每项修复均有独立冻结的失败族（与用例解耦）：
`test_mixed_manifest_binding`(14)、`test_door_property_authorization`(7)、
`test_draft_authority_set_semantics`(10)、`test_published_contract_reachability`(25)、
`test_semantic_bundle_claim_propagation`(5)。

### 1.5 用户驱动的严格审计（本会话关键转折）

用户对 proof 逐一验收后要求"每个项目都进行 IFCcompare 的严格验证"。
独立审计脚本逐案验证七维：实体级 comparator diff、楼层归属、世界几何、
门洞回填、宿主墙、截面旋向、属性丢失。审计发现并推动修复：

- **C1 楼层错（缺陷 7，冻结缺陷）**：梁在 storey 12，冻结记 03，
  恢复件低 28.32m——之前所有验证（含我最初的"原位对齐"检查）都只比
  楼层局部 x/y，未比楼层身份。教训直接催生审计的楼层/世界坐标维度。
- **属性全丢（P2）**：恢复件不带任何 pset → 全案恢复（84 条）。
- **审计脚本自身两次假阳性**（RESTORE_MISSING 因 OCC 空形状、门/窗
  PROPERTY_LOSS 因占位符未填）——均已修正，最终审计结构问题**归零**。

### 1.6 门禁

复合证据全套件 65/65 绿；`compileall` OK；基线指纹经 authorized-fix
记录后 verify CLEAN（508 文件）；全部真实失败过程保留。

---

## 二、Proof 文件地图与未来注意事项

### 2.1 位置与结构

```
dataset/processed/proof/repair-damage-restoration/
├── README.md                     ← 组织说明 + v4 验收终态（入口）
├── R1/ R2/ R3/                    ← vvo 组（损伤-恢复首组）
├── C1/ … C5/                      ← 非 vvo 组（三模型难度阶梯）
│   ├── 01-original.ifc            ← 原始公开模型（构件原生）
│   ├── 02-damaged.ifc             ← 确定性损伤
│   ├── 03-repaired.ifc            ← 真实 DeepSeek 恢复产物
│   ├── input/request.txt          ← 冻结请求（含属性句）
│   ├── agent/{repair-intent,live-attempts}.json
│   ├── changeset/bound-changeset.json
│   ├── validation/original-comparison.json
│   └── FILES.json / manifest.json / REPORT.md（验收版）
```

REPORT.md 为**验收版**：逐构件损伤清单（名称/GUID/楼层/坐标/截面/
损伤方式）+ 恢复映射表（原↔新 GID）+ 类计数三列对照 + 五步手工验收。

历史与过程证据：`dataset/processed/ifc-repair-runs/repair-damage-restoration*`
（v2/v3 真实失败保留）、`composite-evidence-audit/audit-*.json`（终态审计）。

### 2.2 验收结论（v4）

- 五案全 `succeeded`；类计数恢复（六类逐一相等）；comparator 全 `passed`
- 原位对齐：placement/截面/门洞回填/宿主墙/世界位置全对齐
- 属性恢复 84 条（梁/门/窗 pset 按原值）

**已知边界（验收时不应视为缺陷）：**

1. **恢复=几何级重建非字节还原**：新 GUID/新类型/新关系是 `add_*` 契约
   的固有语义；comparator 的 added 集即恢复产物。
2. **挤出深度毫米差**：原建模有实体偏移/端部裁切（如 7447.5 vs 7560），
   轴线/截面/楼层/世界中心一致——原建模变体，非错误。
3. **未恢复项**：`BaseQuantities` 工程量（无作者头，P3 已声明搁置）、
   `Span`（几何派生）、空壳 pset（值为 None）、C1 的 Reference/Slope
   （请求范围选择）。
4. **审计口径**：验收以 `composite-evidence-audit/audit_all_cases.py`
   重放为准；它包含楼层/世界几何维度——这是 C1 楼层缺陷的教训。

### 2.3 未来注意事项

1. **Plan 07（phase12.1）未收尾且不属本线**：四案例 E2E 矩阵历史无
   同轮全过、proof 未策展、状态未关闭——需单独会话执行，勿与
   damage-restoration 组混淆。
2. **运行环境**：bimnet 与 bimnet-zcode 同 commit 双工作树已分叉
   （另一会话在 bimnet 有改动）；`.venv` 物理在 bimnet 但经 rootdir
   `pythonpath`/runner 显式 sys.path 指向 zcode 代码——改 venv 前先确认。
3. **大模型时限**：sixty5（117k 实体）评估需 900s 时限注入
   （公共 orchestrator seam，门禁不减）。
4. **torch DLL**：Windows 上属性运行时要求
   `_prepare_windows_torch_runtime()` 在 `import ifcopenshell` 之前。
5. **Live Provider 行为方差**：模型可能用 semantic_bundle（已修复传播）、
   幻觉 profile id、附加多余字段——修正预算（2）耗尽即终态失败，
   同案例重试是可靠性证据而非盲测证据。
6. **请求措辞敏感**：给属性句时**不要**引用被删构件原名称（模型会
   发 set_occurrence_properties 指向不存在的实体）；用
   "Give the restored N these exact property values: ..." 句式。
7. **git 策展**：全部变更留在工作区，提交由用户决定。

---

## 三、系统是否具备 Repair 能力（分层结论）

按 `docs/validation/agent-capability-evaluation.md` 的三级声明框架：

### 3.1 已证明（Bug fixed / 类鲁棒性）

六个确定性缺陷修复，每个带独立失败族与全量回归——修复本身是可靠的。

### 3.2 已证明（可行性与安全门有效性，live 证据）

**是——在损伤-恢复语义下，系统具备真实可用的 repair 功能。** 证据：

- **真实修复链路**：真实 DeepSeek 意图 → 属性解析（BGE-M3/Qdrant+Stage1.5）→
  绑定 → apply → 原子发布 → 严格重开 L0/L1/L2 → repaired vs original
  comparator，**五案×多轮共 40+ 次真实调用走通全链**。
- **修复质量**：恢复件回到原位几何（含楼层、世界坐标）、原截面、
  原属性值；类计数精确恢复；comparator 判定只有恢复产物在变更集内。
- **安全性**：负孪生（含不支持操作）对真实 Provider 正确 fail-closed
  零突变；模型幻觉/越权输出（错误 profile、多余字段、引用已删实体）
  均被确定性门拒收——这正是 repair 系统需要的失败安全边界。
- **泛化迹象**：跨 4 个模型（vvo/sixty5/1px/d7n）、跨 4 个构件族
  （梁/柱/门/窗）、损伤面 1→8 构件递增全部走通。

### 3.3 未证明（系统能力统计声明）

**不声称** "系统 repair 成功率 X%" 这类统计结论。那需要：
冻结 Baseline/Candidate 配对评测、未知样本分布、失败进分母、切片
非回退、置信区间——本轮 live 是**可行性证据**（同案例重试=可靠性证据），
不是能力度量。C1-C5 是我设计的损伤面，非独立评测集。

### 3.4 能力边界（诚实清单）

- 恢复是**几何/属性级**而非原件字节级（GUID/类型必然新建）
- BaseQuantities、原建模裁切细节不在恢复范围
- live 行为有方差：同案例可能一轮成功一轮失败（正确 fail-closed 后
  重试即过），单次失败不等于能力缺失，但连续失败需要走 debug 回流
  （本会话 v1→v4 正是该回流的完整示范）

**一句话结论：** 系统在损伤-恢复语义下的 repair 功能是真实、可验证、
失败安全的；其确定性骨架（门禁/绑定/审计）足以承载真实 Provider 的
行为方差并把它约束在安全边界内；统计意义上的能力量化留待正式评测。

---

## 附：本会话产出索引

| 类别 | 位置 |
|---|---|
| Proof 包 | `dataset/processed/proof/repair-damage-restoration/` |
| 冻结契约 | `docs/validation/repair-composite-milestone/damage-restoration*.json` |
| 缺陷记录 | 同目录 `DEFECT-RECORD.md`（缺陷 1-7） |
| 工作总结 | 同目录 `WORK-SUMMARY.md`（一至十节） |
| 证据矩阵 | 同目录 `composite-evidence-matrix.md` |
| 严格审计 | `composite-evidence-audit/audit-*.json` |
| 运行工件 | `dataset/processed/ifc-repair-runs/repair-damage-restoration*` |
| 失败族测试 | `tests/ifc_repair/`（5 个新家族文件） |
