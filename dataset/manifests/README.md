# Dataset Manifests

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
