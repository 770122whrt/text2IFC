# Dataset Reorganization / IFC Acquisition Boundary

> 日期：2026-09-04  
> 状态：**Approved — 2026-09-04 经用户明确批准执行；后续若改变本边界，必须重新获得人工确认。**  
> 目的：冻结下一阶段 IFC 数据整理、BIMNet 迁移、公开 IFC 获取、去重、Manifest 生成与数据集目录整理的边界，防止执行过程中范围漂移。

---

## 1. 本阶段目标

本阶段只建设 **Source IFC 数据基础设施**，为后续 Repair Benchmark 与 Post-training 提供不断扩大的、来源清楚的 IFC 源文件池。

Generation 与 Repair / Post-training 的数据路线继续保持分离：

```text
Generation Demo Paper
  -> 当前已有数据足够
  -> 不依赖本阶段新增 IFC 才能推进

Repair / Post-training
  -> 扩大独立 Source IFC
  -> 真实公开 IFC 优先
  -> 去重 / 解析 / reopen / provenance
  -> 后续再派生 Damage / Repair / Training 数据
```

本阶段 **不生成 Repair cases、不运行 Provider、不做 Post-training、不修改 Repair Pipeline**。

---

## 2. 本阶段唯一主要 Dataset Scope

数据整理以用户指定的四个目录为核心：

```text
dataset/ifc
dataset/manifests
dataset/external
dataset/splits
```

### 2.1 `dataset/external`

未来所有 canonical Source IFC 的统一物理存放位置。

包括：

- BIMNet（从 `dataset/ifc/train` / `test` 迁入）；
- 当前已有 BIM Whale；
- 当前已有 IFC-Bench；
- buildingSMART Community Sample Test Files；
- BIMData R&D Open Models Index 所发现并实际下载的上游 IFC；
- BIMcollab Example Project；
- KIT IFC Examples；
- STEP Tools IFC Sample Data；
- 后续经人工批准新增的公开 source。

IfcOpenShell `files` repository **本阶段明确 Deferred，不下载**。

### 2.2 `dataset/manifests`

只保存数据登记、来源、canonical file inventory、benchmark selection 与 private repair-case authority。

原则：

> Manifest 是数据登记和内容管理层，不应变成多个互相重叠、手工维护、难以判断 authority 的 JSON 文件集合。

### 2.3 `dataset/splits`

只保存实验 split authority。

物理目录不再表达 train / validation / test。

即：

```text
physical location != experiment split
```

### 2.4 `dataset/ifc`

当前只包含历史 BIMNet `train/` 与 `test/` 物理目录。

本阶段完成 BIMNet 原子迁移后，`dataset/ifc` 不再作为 canonical Source IFC 存储位置。

默认目标状态：在全部引用和验证通过后移除空的历史 `dataset/ifc` 目录，不保留第二套 BIMNet IFC 副本。

---

## 3. BIMNet 迁移边界

### 3.1 当前事实

当前物理结构：

```text
dataset/ifc/train/*.ifc
dataset/ifc/test/*.ifc
```

实际 BIMNet IFC 为 **25 个文件**：

- train：18
- test：7
- `bimnet-ifc2x3.jsonl`：25 条有效 JSONL record；文件结尾另有一个空行
- `bimnet-scene-splits.json`：25 files / 19 scene families

因此当前不存在 25/26 数据不一致；正式迁移仍必须由脚本重新枚举并验证。

### 3.2 目标物理结构

```text
dataset/external/bimnet/
  1px.ifc
  759.ifc
  7y3.ifc
  7y3_1.ifc
  ...
```

不再保留：

```text
bimnet/train/
bimnet/test/
```

因为 train/test 是实验 split，不是 source provenance。

### 3.3 Split 保留

现有：

```text
dataset/splits/bimnet-scene-splits.json
```

继续作为 BIMNet scene-family split authority。

迁移后：

- split assignment 不因文件移动而变化；
- stable BIMNet file IDs 尽可能保持不变；
- source manifest 引用更新到新的 unified IFC manifest；
- split 中所有 file IDs 必须能解析到 canonical IFC record；
- train / validation / test 必须继续按 scene family 隔离。

### 3.4 原子迁移要求

禁止采用：

```text
先搬部分文件
-> 再慢慢修引用
-> 新旧路径长期共存
```

必须采用：

```text
1. 建立 old_path -> new_path migration map
2. 计算并冻结原文件 SHA-256
3. 生成目标 manifest preview
4. 更新所有生产脚本 / focused tests / active manifests 的 canonical paths
5. 移动 25 个 IFC 到 dataset/external/bimnet
6. 重新计算 SHA-256，要求与迁移前一致
7. 跑 focused path / manifest / split / reopen validation
8. 全部通过后删除旧副本 / 空目录
```

任何一步失败：**停止，不删除旧 canonical source。**

### 3.5 已知路径影响

当前已有 scripts / tests 直接引用：

```text
dataset/ifc/train/vvo.ifc
dataset/ifc/train/px4_1.ifc
dataset/ifc/test/d7n.ifc
...
```

因此 BIMNet 迁移必须包含引用迁移和 focused regression，不能只改 manifest。

历史 validation/report 文档记录的是历史真实路径，不要求为了目录整理批量改写历史报告；只有仍被当作 active instruction / current path authority 的文档需要更新。

---

## 4. Manifest Authority：目标简化方案

目标不是继续增加大量互相重叠的 manifest，而是收敛 authority。

### 4.1 建议最终保留的核心层

```text
dataset/manifests/
  README.md
  ifc-sources.json
  ifc-files.jsonl
  ifc-repair-benchmarks.jsonl
  ifc-repair-cases/
```

其中：

### `ifc-sources.json`

**Source-level authority**。

一条 source 记录描述：

- source id / canonical name；
- upstream repository / URL；
- acquisition mode；
- source revision / retrieval evidence；
- license；
- attribution / citation requirement；
- research-use status；
- training-use status；
- redistribution status；
- source classification；
- notes。

### `ifc-files.jsonl`

**Canonical unique IFC file authority**。

一条 record 对应一份实际保留的 canonical IFC 文件。

至少包含：

- stable file id；
- source id；
- `discovered_via`；
- canonical local path；
- original source path；
- SHA-256；
- size；
- schema；
- IfcOpenShell parse；
- traversal；
- roundtrip write / reopen；
- source family / project family；
- scene / discipline / variant（可获得时）；
- entity / capability statistics；
- approved/restricted uses；
- training eligibility；
- redistribution status；
- notes / warnings。

### `ifc-repair-benchmarks.jsonl`

继续只表达：

> 从 canonical `ifc-files.jsonl` 中挑选出的 Repair benchmark subset。

它不是 source inventory。

### `ifc-repair-cases/`

继续保留 public/private repair case authority；private Ground Truth 不进入 source manifest 或 Provider input。

---

## 5. 旧 Manifest 的迁移原则

当前：

```text
bimnet-ifc2x3.jsonl
raw-files.jsonl
external-corpora.json
ifc-repair-benchmarks.jsonl
ifc-repair-cases/
```

计划：

### 合并进入统一 authority

- `bimnet-ifc2x3.jsonl` -> `ifc-files.jsonl` + `ifc-sources.json`
- `raw-files.jsonl` -> `ifc-files.jsonl` + `ifc-sources.json`
- `external-corpora.json` -> `ifc-sources.json` + 自动 inventory statistics

### 保留

- `ifc-repair-benchmarks.jsonl`
- `ifc-repair-cases/`
- `README.md`（重写为新的 manifest authority 说明）

### 删除旧 manifest 的条件

旧 manifest **不得先删**。

只有：

1. 新 generator 生成结果；
2. 新旧记录完成 coverage 对照；
3. hashes / paths / source metadata / authorization 没有丢失；
4. 所有 active consumers 已切换；
5. focused audit 通过；

之后才允许删除 superseded manifests。

---

## 6. Manifest 必须尽可能由代码生成

这是本阶段冻结规则。

禁止主要依赖人工逐行维护：

```text
ifc-files.jsonl
ifc-sources.json
repair benchmark file metadata
```

### 6.1 建议 generator

最终具体文件名可在实现前小范围调整，但 authority 必须保持：

```text
scripts/dataset/build_ifc_source_manifests.py
scripts/dataset/audit_ifc_source_dataset.py
```

Generator 负责自动计算：

- filesystem enumeration；
- canonical relative path；
- bytes；
- SHA-256；
- schema；
- IfcOpenShell parse / reopen；
- entity counts；
- major entity histogram；
- Window / Door hosted-opening chains；
- source-family / duplicate evidence；
- source-level file counts；
- manifest deterministic ordering。

### 6.2 人工内容

允许人工编写 / 审核：

- source notes；
- license interpretation note；
- citation / attribution note；
- research / training / redistribution caution；
- unusual model warning；
- human admission decision。

但这些人工字段进入 JSON 时，应由 generator 从一个明确的 source policy / metadata definition 读取并生成，而不是直接手改生成后的 manifest JSON。

### 6.3 Determinism

同一文件树 + 同一 source policy + 同一 generator version：

```text
生成 manifest 必须 byte-stable
```

至少要求：

- deterministic record ordering；
- deterministic key ordering；
- canonical JSON serialization；
- 无运行时间戳污染 canonical manifest（retrieval date 等真实 provenance 除外）；
- `--check` 模式检测 drift。

---

## 7. Source 分类与使用标注

统一 source classification：

```text
authorized_local
public_official
public_research
public_example
public_test_fixture
generated_internal       # 本阶段不生成，仅预留分类
```

每个 source / file 至少登记三类使用边界：

```text
research_use
training_use
redistribution
```

值应采用有限枚举，例如：

```text
allowed
allowed_with_attribution
authorized_local_only
review_required
not_inferred
prohibited
```

### BIMNet

必须明确：

```text
source_classification = authorized_local
research_use = authorized
training_use = authorized_local_only
redistribution = not_inferred
```

并保留用户已确认的 Matterport3D/BIMNet authorization evidence；不得因为移动到 `dataset/external/bimnet` 就把它误分类为普通公开数据。

---

## 8. 下载来源边界

用户批准执行后，本轮计划获取：

1. buildingSMART Community Sample Test Files；
2. BIMData R&D Open Models Index 指向的 IFC2X3 上游 source；
3. BIMcollab Example Project；
4. KIT IFC Examples；
5. STEP Tools IFC Sample Data。

明确不进入本轮：

- IfcOpenShell `files`；
- 未经登记的新来源；
- 私有 / 不明确来源 IFC；
- 绕过访问控制的数据；
- Repair case generation / Post-training。

---

## 9. IFC Admission 规则

### 9.1 当前 Repair Source Pool

当前 Repair / Post-training 扩充主目标：**IFC2X3**。

buildingSMART / BIMData upstream 等用于当前 Repair pool 的 IFC 必须：

```text
schema = IFC2X3
IfcOpenShell parse = PASS
basic traversal = PASS
temporary write = PASS
reopen written copy = PASS
```

大小不限。

### 9.2 KIT / STEP / BIMcollab 中的其他 Schema

可以下载并登记有价值的公开 sample，但：

- IFC2X3 -> 当前 Repair candidate；
- IFC4 / IFC4X3 -> source archive / future schema expansion；
- 不混入当前 IFC2X3 Repair benchmark 统计。

### 9.3 Strict Validation

`ifcopenshell.validate` warning / schema conformance 可以登记为额外 evidence，但不是本轮唯一硬 admission gate。

原因：部分公开 test repositories 本身包含用于测试边界的非完全 conformant 文件。

因此分开记录：

```text
parseable
roundtrip_stable
strict_validation_status
```

当前 canonical Repair source 至少要求前两项 PASS。

---

## 10. 去重边界

用户已确认：**完全重复 IFC 不保留第二份实体文件。**

### Level 1 — Exact byte duplicate

```text
SHA-256 equal
```

处理：

- 保留一份 canonical IFC；
- 不保留第二份相同 bytes；
- source manifest 仍记录多个 provenance / discovery alias；
- 不把 alias 计入 unique IFC count。

### Level 2 — Same model / serialization variant

SHA 不同但疑似同一模型时，使用：

- root GUID signature；
- project / building metadata；
- major entity histogram；
- source family；
- discipline / schema；

标记 `suspected_same_model`。

### Level 3 — Semantic comparison

必要时使用现有 normalized semantic fingerprint / IFCCompare / IfcDiff 辅助判断：

```text
semantic_duplicate
same_family_variant
independent_model
```

注意：

- 同建筑 ARC / STR / MEP 不是 duplicate；
- 同建筑 IFC2X3 / IFC4 不是 exact duplicate，应作为 variant；
- 同 family 的不同版本可以保留，但不能统计成独立 source family。

---

## 11. BIMData R&D 的特殊规则

BIMData R&D Open Models Index 是 discovery/index authority，不自动视为所有 IFC 的原始数据主人。

必须尽可能记录：

```text
discovered_via = bimdata-rd-index
canonical_source = actual upstream source
```

若 BIMData index 指向的文件已经存在于 IFC-Bench / BIMcollab / OpenIFC 等本地 source：

- 先 SHA 去重；
- 不下载/保留第二份完全相同 IFC；
- 只增加 discovery provenance；
- license 以实际 upstream evidence 为准。

---

## 12. 下载与整理执行顺序（批准后）

### Phase 0 — Stage Preflight / Baseline

只做本阶段首次 preflight，不做 repository-wide full preflight。

冻结：

- 当前四个目录 tree；
- existing file SHA index；
- existing canonical IDs；
- active path references；
- current manifest coverage；
- current split coverage。

### Phase 1 — Manifest Generator + Tests

先写 generator 和 focused tests，**先不移动 BIMNet、不下载新数据**。

验证 generator 能对当前 dataset 生成稳定 preview。

### Phase 2 — BIMNet Atomic Migration

执行 `dataset/ifc/{train,test}` -> `dataset/external/bimnet/`。

更新 active references / manifests / splits source pointer。

验证后移除旧副本。

### Phase 3 — Existing External Consolidation

先把当前已有：

- BIM Whale；
- buildingSMART official；
- IFC-Bench；

纳入 unified manifest / dedup / source classification。

### Phase 4 — buildingSMART Community

下载 -> IFC2X3 filter -> parse -> roundtrip -> dedup -> admission。

### Phase 5 — BIMData R&D Upstream

解析 index -> upstream acquisition -> IFC2X3 -> dedup against all current data -> admission。

### Phase 6 — BIMcollab

下载 Example Project -> schema classification -> parse/reopen -> dedup -> admission/status。

### Phase 7 — KIT + STEP Tools

下载并登记；IFC2X3 进入当前 candidate，其他 schema 单独分类。

### Phase 8 — Consolidated Audit / Report

输出最终统计：

- downloaded candidates；
- exact duplicates；
- same-family variants；
- rejected parse failures；
- rejected roundtrip failures；
- unique canonical IFC；
- IFC2X3 count；
- source-family count；
- source distribution；
- schema distribution；
- size distribution；
- Repair capability distribution；
- research/training/redistribution status distribution。

---

## 13. Manifest / Dataset 管理原则

必须保持以下规则，防止后续再次变乱：

1. **一个 canonical IFC 只有一个物理副本。**
2. **多个来源发现同一 IFC，记录 alias/provenance，不复制文件。**
3. **实验 split 不通过物理 train/test 目录表达。**
4. **Manifest generated-first，manual JSON edit 是例外而不是常态。**
5. **Source、File、Benchmark、Case 四层 authority 分开。**
6. **License / research / training / redistribution 分字段，不用一个模糊 `license_ok`。**
7. **BIMNet 即使移到 external，也继续保持 authorized-local 身份。**
8. **Historical processed/proof artifacts 不进入 Source IFC inventory。**
9. **Generated IFC 与 real-source IFC 永远分开 provenance。**
10. **任何删除必须发生在新 authority 和验证成功之后。**

---

## 14. 停止条件 / 需要重新向用户请求的情况

执行过程中遇到以下任一情况，立即停止相关 source / migration，不自行扩大处理：

- license / research / training / redistribution 条款无法合理判断；
- BIMNet migration 出现 SHA mismatch；
- split file ID 无法映射到 canonical record；
- active production / repair path 无法安全迁移；
- 发现两个不同 IFC 发生 canonical ID collision；
- 去重需要删除非 exact duplicate 且语义关系不清楚；
- 下载源需要账号、访问控制、非公开授权或特殊条款；
- 需要引入本文件未批准的新 source；
- 需要 full repository preflight；
- 需要修改 Repair Pipeline 行为或 benchmark truth contract。

可局部继续其他独立 source 的工作，但不得绕过问题 source 的 gate。

---

## 15. 本文批准后允许执行的动作

批准本文后，本阶段授权范围为：

```text
Manifest generator / audit code
Focused tests
BIMNet physical migration + active path migration
Current manifest consolidation
Public IFC acquisition from approved sources
IFC2X3/schema classification
IfcOpenShell parse / temporary write / reopen
Exact and bounded semantic dedup
Source/license/usage registration
Dataset folder cleanup within the four approved directories
Final inventory / audit / human-readable report
```

仍不授权：

```text
Repair case generation
Damage generation
Provider calls
Repair benchmark execution
Post-training
IfcOpenShell/files acquisition
New unapproved source families
Repair Pipeline feature changes
Full repository preflight
```

---

## 16. 批准 Gate

**本文当前只是 Boundary Draft。**

在用户明确批准之前：

- 不执行数据下载；
- 不移动 BIMNet；
- 不删除任何 IFC；
- 不删除旧 manifest；
- 不修改 splits；
- 不实现 generator。

用户批准后，按第 12 节 Phase 0 -> Phase 8 执行；若需要改变本边界，必须先回到本文更新并重新获得人工确认。
