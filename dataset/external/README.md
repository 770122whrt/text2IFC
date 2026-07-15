# External Dataset Layout

External files are grouped by source and are never treated as project-native
truth without provenance and validation records.

```text
dataset/external/
  buildingsmart-official/
    ifc4/
    ifc4x3/
  bim-whale-ifc-samples/  # pinned external corpus submodule
  ifc-bench/              # pinned external corpus submodule
```

Rules:

1. Files copied into this repository must appear in
   `dataset/manifests/raw-files.jsonl`.
2. A linked corpus snapshot must appear in
   `dataset/manifests/external-corpora.json` with a fixed source revision.
   Files inside a linked corpus are not training-admitted by that link alone.
3. Any linked file selected for a benchmark, derived pair, or training split
   must first receive its own `raw-files.jsonl` record and license decision.
4. Every source must appear in `dataset/sources/CATALOG.md`.
5. Licenses are stored in `dataset/sources/LICENSES/` or retained in a pinned
   linked corpus with an explicit license evidence path.
6. IFC files copied into the parent repository remain tracked through Git LFS.
7. Schema-mismatched files must not enter an IFC2X3 benchmark split.
8. Derived text/JSON pairs must retain the raw-file source ID.
