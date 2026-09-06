# Dataset Manifests

## 当前权威与兼容层

- `ifc-sources.json`：来源级记录；`ifc-files.jsonl`：canonical 文件记录。
- `ifc-source-summary.json`：派生统计；`ifc-validation.jsonl`、`ifc2x3-certified.jsonl`：对应验证与严格样本选择。
- `ifc-repair-benchmarks.jsonl` 与 `ifc-repair-cases/`：benchmark 子集及 public/private case 合同，不是全量 source inventory。
- `bimnet-ifc2x3.jsonl` 仍由 source generator 输出兼容投影；`raw-files.jsonl`、`external-corpora.json` 仍有旧消费者。当前不删除这三项。
- 当前 BIMNet 物理位置是 `dataset/external/bimnet/`；下文 train/test 表述是来源历史。
- `acquisitions/` 和 acquisition 文件保存逐来源获取记录。

生成入口：`scripts/dataset/build_ifc_source_manifests.py`；审查入口：`scripts/dataset/audit_ifc_source_dataset.py`。本次导航整理未重新运行全量数据探测。

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
family map is `dataset/processed/bim-json-2.0/scene-families.json`, whose
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
