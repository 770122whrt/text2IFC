# External Dataset Layout

External files are grouped by source and are never treated as project-native
truth without provenance and validation records.

```text
dataset/external/
  buildingsmart-official/
    ifc4/
    ifc4x3/
```

Rules:

1. Every file must appear in `dataset/manifests/raw-files.jsonl`.
2. Every source must appear in `dataset/sources/CATALOG.md`.
3. Licenses are stored in `dataset/sources/LICENSES/`.
4. IFC files remain tracked through Git LFS.
5. Schema-mismatched files must not enter an IFC2X3 benchmark split.
6. Derived text/JSON pairs must retain the raw-file source ID.
