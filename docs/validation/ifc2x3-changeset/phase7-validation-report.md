# Phase 7 Validation Report

Date: 2026-07-19  
Scope: IFC retrieval index, structured target resolution, bounded context, and
local CLI. This report does not claim ChangeSet generation or IFC mutation.

## Result

Phase 7 passed its automated acceptance contract. A supplied IFC2X3 file can be
indexed locally, queried through a versioned `TargetQuery`, resolved or safely
rejected with field evidence, and projected into a bounded Provider-facing
context.

LargeBuilding produced 86 initial-scope records:

| Entity family | Count | Current role |
|---|---:|---|
| Wall, including `IfcWallStandardCase` | 18 | editable target |
| Door | 18 | editable target |
| Window | 42 | editable target |
| Space | 8 | contextual spatial entity |

The frozen Wall query combined Name `Basic Wall:Outside wall:346660`, storey
`Level 1`, and direction `east`. It resolved uniquely to
`ifc:1F6umJ5H50aeL3A1As_wTm`. A Level 1 IfcSpace query also resolved uniquely.
A controlled duplicate-name fixture returned `ambiguous` with no resolved ID.

## Exact verification commands

```text
.venv\Scripts\python -m pytest tests\ifc_repair -q
.venv\Scripts\python -m compileall -q src\text2ifc_ifc_repair scripts\ifc_repair
.venv\Scripts\python scripts\ifc_repair\index.py build dataset\external\bim-whale-ifc-samples\LargeBuilding\IFC\LargeBuilding.ifc --database phase7-large-building.tmp.sqlite
.venv\Scripts\python scripts\ifc_repair\index.py query phase7-large-building.tmp.sqlite --query phase7-wall-query.tmp.json
git diff --check
```

Observed results:

- full IFC repair regression: `64 passed in 147.51s`;
- compileall: passed;
- schema validation: passed through focused query/resolution/context tests;
- CLI build/query smoke: exit code 0, resolution `resolved`;
- `git diff --check`: passed;
- source IFC SHA-256:
  `102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725`;
- source size: 1,292,595 bytes;
- SQLite index size: 1,634,304 bytes;
- observed local build time: 2,237.29 ms;
- resolved normal context: 2,267 UTF-8 bytes, estimated 567 tokens.

Build time and size are single-machine observations only. Phase 13 remains the
place for scale, latency, and incremental-index claims.

## Integrity and abstention evidence

- SQL values are parameter-bound, including quote/SQL-shaped alias fixtures.
- Failed builds do not replace a published database.
- Source hash and index-schema mismatches fail explicitly.
- Duplicate or malformed IFC GlobalIds remain diagnostic-only identities.
- GUID conflicts with class, storey, or name return `conflict`.
- zero matches return `not_found`; ties and near ties return `ambiguous`;
  unsupported requested geometry returns `unsupported`.
- normal top-K is 5 and diagnostic top-K is at most 10.
- context projection omits unrelated properties and non-allowlisted facets.

## Explicit boundaries

- Provider calls during Phase 7 validation: **0**.
- Vector retrieval: **disabled**; only a dependency-free extension interface
  exists.
- Full IFC JSON or STEP input in Provider context: **0**.
- Private ground truth or damage manifest input: **0**.
- LargeBuilding's 18 indexed Walls expose the supported straight-wall path.
  Curved, segmented, or otherwise unsupported Wall editing remains deferred and
  is represented by `unsupported_or_approximate` plus diagnostics when seen.
- Natural-language-to-TargetQuery interpretation remains a later Agent phase.
