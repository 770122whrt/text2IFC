# IFC Target Retrieval and Context Design

> Status: implemented and verified for v1.1 Phase 7 on 2026-07-19  
> Goal: existing/damaged IFC + natural-language request -> explainable target
> candidates -> semantic ChangeSet -> deterministic IFC.

## 1. Target description decision

GUID, Name and spatial/directional descriptions are all valid target evidence;
none is the universal user-facing key.

| Selector | Strength | Limitation | Intended use |
|---|---|---|---|
| IFC GlobalId | Exact inside one model revision | Engineers rarely know it; identity may change across exports | Highest-confidence exact selector when supplied |
| Name/LongName/Tag/ObjectType/type name | Human/model vocabulary; searchable | May be duplicated, empty or export-specific | Alias evidence, never the sole global key |
| Storey/grid/space | Engineering-friendly spatial anchor | IFC may omit grids or boundaries | Hard/strong spatial constraints when available |
| Direction/facade/relative position | Natural for engineers | Requires a declared north/basis and tolerance | Spatial evidence with provenance |
| Geometry/dimensions/endpoints | Deterministic disambiguation | Not convenient as primary user language | Candidate filtering and tie breaking |
| Host/containment/adjacency | Strong topology | Relationship quality varies by authoring pattern | Operation-specific evidence |

If exact GUID conflicts with the requested class/storey/name/location, the
system reports a selector conflict; it must not silently trust one field.

## 2. Deterministic IFC index

The IFC is parsed locally. The LLM does not scan raw IFC or a full IFC-to-JSON
conversion.

Phase 7 initially exposes `IfcWall` (including registered subtypes), `IfcDoor`
and `IfcWindow` as editable target classes. `IfcSpace` is indexed as room,
containment, boundary and adjacency context, not yet as a mutation target. A
user may explicitly provide a different semantic interpretation of a space;
the query preserves that wording for a registered adapter instead of silently
forcing every spatial object into the default room meaning. Later element
families extend the same contracts through registered adapters.

The indexer emits a versioned `ElementRecord` with a common skeleton and typed
facets:

```json
{
  "record_id": "ifc:<GlobalId>",
  "ifc_global_id": "<bare GlobalId>",
  "ifc_class": "IfcWallStandardCase",
  "predefined_type": null,
  "identity": {
    "name": "Basic Wall:Outside wall:346660",
    "long_name": null,
    "tag": "346660",
    "object_type": "Basic Wall:Outside wall",
    "type_name": "Outside wall",
    "type_global_id": "<type GlobalId>",
    "aliases": ["outside wall", "外墙"]
  },
  "spatial": {
    "site": null,
    "building": "Building",
    "storey": "Level 1",
    "spaces": [],
    "grids": [],
    "world_bbox_mm": {},
    "centroid_mm": [],
    "orientation": {},
    "elevation_mm": 0
  },
  "topology": {
    "host_ids": [],
    "container_ids": [],
    "opening_ids": [],
    "filling_ids": [],
    "adjacent_space_ids": []
  },
  "properties": {
    "property_sets": [],
    "quantities": []
  },
  "geometry_summary": {
    "dimensions_mm": {},
    "axis_start_mm": [],
    "axis_end_mm": [],
    "supported_capabilities": []
  },
  "provenance": {
    "source_ifc_sha256": "sha256:...",
    "field_sources": {}
  }
}
```

`aliases` may include deterministic normalization and controlled bilingual
vocabulary, but never model-invented facts without provenance.

Wall-, Door-, Window-, Space-, Opening- and structural-specific fields belong
under registered facets or projections, not the common envelope. Invalid,
missing or duplicate GlobalIds receive structured diagnostics. An internal
diagnostic ID may keep such a record inspectable, but cannot silently authorize
an IFC mutation. The same validation applies to user-supplied IFC and IFC
produced by this system.

### 2.1 Property retention and projection

The local index retains as many parseable IFC property sets and quantities as
practical, with original names, IFC value types, units, owning entity/type and
field provenance. This retained property payload is not automatically copied
into the Provider prompt.

The request-understanding Agent extracts property-related intent into
structured JSON. Deterministic context projection selects only matching
existing properties and definitions for the chosen operation and candidates.
A later compiler may apply an attribute change only after checking its schema,
IFC value type, unit, applicability, target scope and operation contract. The
model expresses semantic intent; it does not author unchecked low-level IFC
property entities.

### 2.2 Index storage and lifecycle

Phase 7 uses an embedded SQLite database as the primary index store. It must
not require a separately managed database service. Storage remains behind a
repository/backend interface so later implementations can add another SQL or
vector backend without changing `ElementRecord`, `TargetQuery` or candidate
contracts.

Every database is bound to the source IFC SHA-256, IFC schema, index-schema
version and extractor version. Source or version drift triggers a deterministic
full rebuild in Phase 7. Incremental ChangeSet-driven maintenance is deferred
until large-model measurements justify the added complexity.

## 3. Request understanding

The first Agent stage converts user text into a `TargetQuery`; it does not emit
the repair ChangeSet yet:

```json
{
  "ifc_classes": ["IfcWall"],
  "global_ids": [],
  "identity_terms": ["Outside wall", "Basic Wall:Outside wall:346660"],
  "storey": "Level 1",
  "grid_constraints": [],
  "space_constraints": [],
  "direction_constraints": [],
  "relative_position": {
    "reference": "wall_axis_start",
    "offset_mm": 3042.5
  },
  "geometry_constraints": {},
  "attribute_intent": [],
  "requested_operation_type": "add_window_with_opening_to_wall"
}
```

The query preserves what the user actually said and marks inferred normalized
terms separately. A missing selector is not silently synthesized.

## 4. Retrieval and ranking

Retrieval is deterministic after `TargetQuery` generation:

1. exact GUID lookup when present;
2. allowed IFC class/subclass filter;
3. storey/building/site hard filters;
4. exact project label, Tag, type and normalized alias matching;
5. grid/space/host/adjacency constraints;
6. declared directional and relative-position constraints;
7. geometry compatibility and operation capability filtering;
8. fuzzy semantic alias score only after structural constraints.

The retriever contract permits structured, lexical and future vector candidate
sources to return the same evidence-bearing candidate shape. Phase 7 ships with
vector retrieval disabled and has no embedding or vector-database dependency.
If later enabled, embeddings are created from compact `ElementSearchDocument`
records rather than raw IFC JSON. Vector evidence may improve recall or soft
ranking only after hard class, storey, identity and relationship constraints;
it cannot override conflicts.

Each candidate returns score components and evidence, for example:

```json
{
  "ifc_global_id": "1F6umJ5H50aeL3A1As_wTm",
  "score": 0.98,
  "evidence": [
    {"field": "storey", "query": "Level 1", "actual": "Level 1", "match": "exact"},
    {"field": "identity.name", "query": "Basic Wall:Outside wall:346660", "actual": "Basic Wall:Outside wall:346660", "match": "exact"}
  ]
}
```

No fixed threshold is allowed to conceal ambiguity. A target is resolved only
when all hard constraints pass, one candidate is uniquely best under a frozen
margin policy, and no selector conflict exists. Otherwise the system asks for
clarification or stops.

## 5. LLM context packaging

The ChangeSet Agent receives:

- normalized repair intent and `TargetQuery`;
- the uniquely resolved candidate, or bounded top-K candidates when the Agent
  is explicitly responsible for a final semantic choice;
- only operation-relevant fields;
- only request-relevant property definitions and current values selected from
  the more complete local database;
- field provenance and coordinate basis;
- model/operation constraints and context budget;
- no whole IFC JSON, STEP text or private ground truth.

For a resolved target, `Name` is retained as human evidence while the bare
`ifc_global_id` is the binding written into `scope.target_ids` and operation
target fields. The compiler revalidates that binding against the same IFC
fingerprint before mutation.

## 6. Final product flow

```text
program --ifc model.ifc --request "..."
  -> local IFC index
  -> Agent TargetQuery / clarification
  -> deterministic candidate retrieval
  -> bounded public context
  -> Agent semantic ChangeSet
  -> Schema + binding + L1/L2 Audit
  -> transactional IFC Applicator
  -> output IFC + ChangeSet + evidence bundle
```

L1 and L2 are required. L3 authoring/identity exactness is recorded as a future
problem and is not a v1.1 compatibility claim.

## 7. Phase 7 verified implementation

The implemented contract uses these versioned boundaries:

- index: `text2ifc/ifc-index/0.1`;
- query: `text2ifc/ifc-target-query/0.1`;
- deterministic score: `text2ifc/target-score/0.1`;
- resolution: `text2ifc/ifc-target-resolution/0.1`;
- bounded context: `text2ifc/ifc-target-context/0.1`.

The CLI is now available as:

```text
python scripts/ifc_repair/index.py build SOURCE --database INDEX.sqlite
python scripts/ifc_repair/index.py query INDEX.sqlite --query query.json
```

This CLI stops after deterministic resolution and context projection. It does
not call a Provider, generate a ChangeSet, or mutate the source IFC. Normal
context is capped at five candidates; diagnostic context is capped at ten.
Only explicitly requested property evidence is projected from the broader
typed local property index.

LargeBuilding acceptance and exact measurements are recorded in
`phase7-validation-report.md`. These results validate functional behavior for
the selected fixture; they are not a large-scale performance claim.
