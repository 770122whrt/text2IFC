# Phase 7 Pattern Map

## Domain Contracts and Canonical JSON

- Closest analog: `src/text2ifc_ifc_repair/context.py`.
- Reuse its schema-version constants, SHA-256 binding, sorted JSON with
  `allow_nan=False`, and byte/token stabilization behavior.
- New query/resolution contracts must live beside repair contracts without
  changing the existing `ifc-repair-context/0.1` payload silently.

## Registry Extension

- Closest analog: `src/text2ifc_ifc_repair/registry.py`.
- Use immutable definitions and stable machine-readable errors.
- Retrieval adapters are a separate registry/protocol because index extraction
  and candidate sources are not repair operations.

## IFC Extraction

- Closest analogs: `sample.py`, `geometry.py`, and `context.py`.
- Reuse `straight_wall_axis`, wall/opening geometry facts, schema checks, and
  containment traversal patterns.
- Extend spatial lookup for `IfcSpace.Decomposes` and filling/void host chains.

## Transactional Publication

- Closest analogs: `apply.py` and `workflow.py`.
- Build SQLite in a temporary sibling path and atomically publish only after
  schema creation, extraction, diagnostics, and transaction commit succeed.

## CLI

- Closest analogs: `scripts/ifc_repair/inventory.py` and `run_case.py`.
- Use `argparse`, `Path`, deterministic sorted JSON output, integer exit codes,
  and no secret/environment output.

## Tests

- Closest analogs: `tests/ifc_repair/test_context.py` and `test_sample.py`.
- Use the frozen LargeBuilding path for real integration behavior, copies for
  mutations, `tmp_path` for databases, and exact machine-readable error/status
  assertions.

## Files to Create or Extend

| Role | Planned file | Closest analog |
|---|---|---|
| Domain models | `src/text2ifc_ifc_repair/index_models.py` | `changesets.py` |
| SQLite repository | `src/text2ifc_ifc_repair/index_store.py` | transactional publication in `apply.py` |
| IFC indexer | `src/text2ifc_ifc_repair/indexer.py` | `sample.py`, `context.py` |
| Retrieval | `src/text2ifc_ifc_repair/target_query.py` | selection logic in `context.py` |
| Candidate protocols | `src/text2ifc_ifc_repair/retrievers.py` | capability dispatch in `registry.py` |
| Context projection | `src/text2ifc_ifc_repair/target_context.py` | `context.py` |
| CLI | `scripts/ifc_repair/index.py` | `inventory.py` |

