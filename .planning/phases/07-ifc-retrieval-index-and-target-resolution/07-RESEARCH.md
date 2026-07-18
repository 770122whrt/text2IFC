---
phase: 07
status: complete
researched: 2026-07-19
requirements:
  - TGT-01
  - TGT-02
  - TGT-03
  - TGT-04
  - TGT-05
---

# Phase 7 Research: IFC Retrieval Index and Target Resolution

## Research Complete

Phase 7 can be implemented entirely with the current Python/IfcOpenShell stack
and the Python standard library. SQLite is built into Python 3.12; the installed
IfcOpenShell 0.8.5 provides `ifcopenshell.util.element.get_psets`, `get_type`,
placement utilities, geometry tessellation, and inverse IFC relationships
needed by the first index.

## Recommended Architecture

```text
IFC2X3 file
  -> IndexBuilder + registered ElementAdapters
  -> SQLiteIndexRepository
  -> versioned TargetQuery
  -> hard constraint filtering
  -> deterministic evidence scoring
  -> ResolutionResult (resolved / ambiguous / not_found / conflict / unsupported)
  -> bounded TargetContext projection
```

Keep the current operation registry unchanged. Add a retrieval-side adapter
registry whose public contracts are independent from Window operations. The
operation registry may supply allowed target classes and capability filters to
retrieval, but it must not own index storage.

## SQLite Design

Use normalized searchable columns plus canonical JSON for extensible payloads:

- `index_metadata`: source SHA-256, IFC schema, index schema version,
  extractor version, source size, build timestamp, status.
- `elements`: record ID, GlobalId, IFC class, name fields, type identity,
  storey identity, geometry capability, centroid/bounds/axis JSON, facet JSON.
- `aliases`: normalized alias, original alias, field, provenance.
- `relationships`: source GlobalId, relation kind, target GlobalId, provenance.
- `properties`: entity GlobalId, set kind/name, property name, canonical value
  JSON, IFC value type, unit, inherited flag, provenance.
- `diagnostics`: stable code, severity, entity/STEP reference, message/evidence.

Foreign keys and unique constraints enforce repository integrity. Do not place
all searchable facts inside one JSON column. Every query uses bound SQL
parameters; user text never becomes SQL syntax.

Build into a temporary database in the destination directory, commit the
transaction, then atomically replace the requested database path. A failed IFC
parse or extraction must not publish a half-built index.

## IFC Extraction Findings

The LargeBuilding sample contains 18 walls, 18 doors, 42 windows, and 8 spaces.
Its Wall/Door/Window types and property sets are available through
`ifcopenshell.util.element`; Window records expose approximately 15 inherited
and instance property/quantity groups. `IfcSpace` containment uses
`IfcRelAggregates.Decomposes` in this sample rather than
`ContainedInStructure`, so the indexer needs a generic spatial-parent resolver.

Initial record coverage:

- `IfcWall` including `IfcWallStandardCase`: aliases, type, storey, axis,
  dimensions, openings, geometry capability.
- `IfcDoor` and `IfcWindow`: aliases, type, storey, dimensions, filling/opening
  and host-wall chain where present.
- `IfcSpace`: contextual record with aliases, LongName, storey, boundaries and
  adjacency evidence when exported.

An absent space boundary is `unavailable` evidence, not a false negative.
Curved or unrecognized wall axes remain indexed with an unsupported capability
diagnostic; they are not dropped and not approximated as straight.

## Property Retention

Call `get_psets(element, should_inherit=True, verbose=True)` once per indexed
entity. Flatten the result into typed property rows while retaining the source
set and raw canonical value. Values that cannot be represented as JSON receive
a diagnostic and a deterministic string representation rather than crashing
the whole index.

The Provider projection never copies all property rows. `attribute_intent`
selects set/property names and relevant existing values. This preserves future
semantic fidelity without reintroducing whole-IFC prompt input.

## TargetQuery and Ranking

Use a versioned Python/JSON contract with these groups:

- explicit selectors: GUID, class, storey, host/containment, required
  grid/space/direction/geometry;
- identity terms: Name, LongName, Tag, ObjectType, type name, aliases;
- normalized selectors with provenance;
- operation/capability requirements;
- attribute intent.

Resolution is a status-bearing result, not a function that always returns one
entity. Exact GUID must still be checked against all other explicit selectors.
Hard constraints filter first. Versioned integer score components then rank
aliases, spatial/relationship facts, direction, and geometry. A unique winner
requires a tested score margin; otherwise return `ambiguous` with top evidence.

Candidate evidence records `matched`, `mismatched`, and `unavailable` facts.
Stable ordering is score descending, then GlobalId ascending. No database row
order or STEP ID may influence the winner.

## Vector Extension

Define a `CandidateRetriever` protocol and a disabled `VectorRetriever`
registration point. Future vector hits use a compact `ElementSearchDocument`
and enter only after hard filters. Phase 7 must have no embedding package,
network call, or vector database dependency.

## Context Projection

Normal Provider context retains top-5; diagnostics may retain top-10. Canonical
UTF-8 JSON is measured after every reduction and records actual bytes plus the
existing conservative `ceil(bytes/4)` token estimate. Projection includes only
operation- and intent-relevant facets/properties. It cannot remove the resolved
exact candidate to meet budget; if one candidate cannot fit, return an explicit
budget error.

## Compatibility Strategy

Do not silently mutate `ifc-repair-context/0.1`. Add separate Phase 7 query,
resolution, and target-context contracts. The existing Window repair pipeline
continues to pass while Phase 9 later adopts the new target-resolution path.
Where practical, reuse canonical JSON/fingerprint helpers and adapt the legacy
context builder only after the new resolver is independently green.

## Validation Architecture

Use pytest with real SQLite and real IFC files. Unit tests should build
temporary databases and query them through the public repository API. IFC
integration tests use a copied LargeBuilding model for duplicate/malformed
identity cases and the frozen source for stable counts and property evidence.

Required test layers:

1. contract and repository tests;
2. index extraction and invalid-model diagnostics;
3. deterministic resolution, conflicts, ambiguity, and stable ordering;
4. bounded context and attribute projection;
5. CLI build/query behavior;
6. LargeBuilding end-to-end retrieval plus existing IFC repair regressions.

Every behavior task follows RED/GREEN/REFACTOR and records the failing focused
test before production code is added.

## Risks and Mitigations

- Geometry tessellation can be expensive: compute only registered summaries,
  cache per entity during one build, and record unavailable geometry instead of
  aborting unrelated records.
- Real IFC files contain malformed identity: publish diagnostics and refuse
  automatic mutation binding for unreliable records.
- SQLite schema can leak into public contracts: keep repository rows private
  and reconstruct versioned domain records at the boundary.
- Fuzzy scoring can hide ambiguity: fixed score components, field evidence,
  stable tie order, and explicit margin gate.
- Property payload can overwhelm prompts: retain locally, project by structured
  attribute intent and byte budget.
- Existing Window UAT can regress: keep v0.1 context compatibility and run the
  complete `tests/ifc_repair` suite before phase verification.

## Planning Recommendation

Use four dependent TDD plans: contracts/storage; IFC indexing; deterministic
resolution/vector boundary; context/CLI/LargeBuilding closure. This sequencing
keeps each RED test focused and prevents context integration from defining the
domain model accidentally.

## RESEARCH COMPLETE

