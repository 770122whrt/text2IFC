# Dataset Manifests

## 当前 IFC 文件资产入口（2026-09-26）

按用户要求，统一管理清单位于 external：[当前资产登记](../external/ifc-asset-register.jsonl)、[139 个核心场景](../external/ifc-core-register.jsonl)及[使用说明](../external/IFC_DATASET.md)。2026-09-26 当前登记387条来源、386份唯一首选内容。核心为 132 IFC2X3＋7 IFC4，全部小于 10 MB。该文件资产视图保留逐项质量与许可边界；不改写既有训练、benchmark 和 Proof authority。

## 清理阶段基线登记（2026-09-13）

[整理登记报告](dataset-registration-20260913/README.md) 汇总当时所有可读取 dataset 目录，并单列 13 个权限隔离目录。[active-ifc-register.jsonl](dataset-registration-20260913/active-ifc-register.jsonl)／[CSV](dataset-registration-20260913/active-ifc-register.csv) 汇总原 canonical 274 份与选定 ResBIM 50 份，基线共 324 个唯一 IFC、277 个 IFC2X3。

新表是汇总库存，原 `ifc-files.jsonl` 仍管理原 274 份；ResBIM 的 50 份选择、来源与技术报告通过新登记表引用，没有手工改写现有生成器输出或 benchmark/split 合同。源许可支持与训练 eligible 分开。当前 RVT 工作暂停，删除详情以 [deletion-journal.jsonl](dataset-registration-20260913/deletion-journal.jsonl) 解释历史获取/运行记录中的已退役文件。

## 当前权威与兼容层

- `ifc-sources.json`：来源级记录；`ifc-files.jsonl`：canonical 文件记录。
- `ifc-source-summary.json`：派生统计；`ifc-validation.jsonl`、`ifc2x3-certified.jsonl`：既有验证与技术筛选投影，不能从其命名推断完整 schema/EXPRESS 合规。
- `ifc-repair-benchmarks.jsonl` 与 `ifc-repair-cases/`：benchmark 子集及 public/private case 合同，不是全量 source inventory。
- `bimnet-ifc2x3.jsonl` 仍由 source generator 输出兼容投影；`raw-files.jsonl`、`external-corpora.json` 仍有旧消费者。当前不删除这三项。
- 当前 BIMNet 物理位置是 `dataset/external/bimnet/`；下文 train/test 表述是来源历史。
- `acquisitions/` 和 acquisition 文件保存逐来源获取记录。

生成入口：`scripts/dataset/build_ifc_source_manifests.py`；审查入口：`scripts/dataset/audit_ifc_source_dataset.py`。本次导航整理未重新运行全量数据探测。

2026-09-10 补充：[两个新增 IFC ZIP 检查与 IFC-bench 登记修订](../external/_checks/incoming-ifc-audit-20260910/README.md)。`external-corpora.json` 的 IFC-bench 计数对应用户筛选后的本地子集（168 个文件、48 个 IFC）；用户已确认两份上游 IFC 因体积过大主动排除，不需要补回。原历史计数和排除路径保留，具体排除阈值未提供，不作推定。新增 80 个 ZIP 成员只登记在检查目录，未进入 canonical IFC 清单。

2026-09-13 用户确认：上述两个历史 IFC ZIP 已因不合格主动删除，80 个历史条目不计入当前磁盘库存。新的 RVT 转换与来源审查在 [external/RVT](../external/RVT/README.md) 独立管理，尚未改写本目录正式 IFC authority。

## 历史格式及仍被使用的专项合同

## `raw-files.jsonl`

One JSON object per externally acquired raw file.

Required fields:

```json
{
  "id": "source-specific-stable-id",
  "source_repository": "owner/repository",
  "source_revision": "commit SHA",
  "source_path": "path/in/source/repository.ifc",
  "retrieved_at": "YYYY-MM-DD",
  "license": "SPDX-like identifier",
  "local_path": "dataset/external/source/file.ifc",
  "sha256": "lowercase hexadecimal digest",
  "declared_schema": "IFC4",
  "validation": "pending",
  "approved_uses": ["parser-test"],
  "training_eligible": false
}
```

## Future Manifests

`text-json-pairs.jsonl` will link every generated text instruction and BIM JSON
document to one or more `raw-files.jsonl` IDs, generation settings, review
status, and dataset split.

## `bimnet-ifc2x3.jsonl`

One record per authorized local BIMNet IFC2X3 file. The manifest records the
local and source-relative path, SHA-256, IFC schema, Matterport scene family,
approved local uses, and the user's authorization confirmation date.

`source_revision` and `retrieved_at` remain `null` because those facts were
not recorded when the local files were obtained. The manifest does not infer
them. Raw or derived redistribution rights are also not inferred.

The existing `dataset/ifc/train` and `dataset/ifc/test` folders are historical
source paths, not text2IFC model split assignments. Phase 3 must split by
`scene_family` before generating text or augmented variants. The canonical
family map is `dataset/processed/derived/bim-json-2.0/scene-families.json`, whose
`split_assignment` remains `null` until that work begins.

## `ifc-repair-benchmarks.jsonl`

Phase 10.3 repair benchmarks. Each record binds one admitted IFC to its current
SHA-256, IFC schema, byte/entity/Window/valid-chain/wall capability metrics,
project split when applicable, execution role and a human-readable suitability
reason.

The manifest does not redefine the historical `dataset/ifc/train` and
`dataset/ifc/test` folders. For example, `vvo.ifc` remains physically under the
historical `train` source path while its project split is `test`, as determined
by `dataset/splits/bimnet-scene-splits.json`.

Regenerate candidate records with:

```powershell
.venv\Scripts\python scripts\dataset\build_ifc_repair_benchmarks.py
```

The command prints canonical JSONL for review; it does not overwrite the
checked-in manifest.

## `ifc-repair-cases/*.private.json`

Evaluator-only target mappings for reproducible mutation cases. These records
contain original Window and Opening identifiers and therefore must never enter
Provider prompts or public run bundles.

## `ifc-repair-cases/phase10.5-window-fidelity-cases.json`

Phase 10.5 public acceptance matrix for complete explicit occurrence facts,
exact-occurrence reuse, authorized same-Type cohort reuse, deliberate cohort
conflict, and an atomic five-Window bundle. Every admitted source, damaged and
reference repaired IFC is SHA-256-bound, and each case lists the exact public
facts that may be projected to the Agent. Private mutation mappings and Ground
Truth comparator Gold remain outside this manifest and outside Provider input.

## Read-only dataset audit

Run:

```powershell
.venv\Scripts\python scripts\dataset\audit_dataset.py
```

The audit validates file paths, hashes, IFC schema declarations, duplicate
identities and linked-corpus counts, then inventories `dataset/processed`
roots as `retain`, `regenerable` or `review_before_delete`. It never moves,
deletes or rewrites dataset content. Classification is review evidence only.

## IFC repair success proof

`dataset/processed/proof/ifc-repair-success-cases/manifest.json` indexes
human-reviewable repair successes. Each admitted case contains:

- original, damaged and published repaired IFC copies;
- the exact user request;
- structured Agent output and a bound ChangeSet;
- Production L1/L2 and optional private Ground Truth evidence;
- a human-readable report and per-file SHA-256 manifest.

The proof manifest is an accepted-results index, not a training split and not
a replacement for `ifc-repair-benchmarks.jsonl`. Private mutation manifests
remain evaluator-only and must never be projected into Provider context.

## Processed 存储归并

[processed-layout-20260913.json](processed-layout-20260913.json) 记录派生数据和旧 JSON 修复材料的旧路径、新路径与原字节 SHA-256；不替代源 IFC 的 provenance、数据划分或 Proof manifest。
