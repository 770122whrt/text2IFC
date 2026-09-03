# Codex Implementation Prompt：Extensible IFC2X3 Local ChangeSet Evaluation

## 0. Authority and working rule

Implement the first extensible IFC2X3 local-modification evaluation workflow in
the current Text2IFC repository.

Before planning or editing code, read:

```text
docs/validation/ifc2x3-changeset/design.md
```

That design document is authoritative. This prompt defines implementation work
but must not silently change the design, visibility boundary, coordinate
contract, operation semantics, sample, or acceptance criteria.

If implementation evidence requires a design change:

1. stop that part of implementation;
2. record the conflict;
3. update the design decision log after review;
4. then update this prompt and tests.

Do not redesign the entire Text2IFC project. Reuse existing validation,
ChangeSet, evidence, revision, prompt registry, IFC compiler, extraction and
gate components where their contracts match.

## 1. Product boundary

Use the hybrid architecture:

```text
damaged.ifc as authoritative base model
    + compact public repair context JSON
    + repair_request.txt
    -> Provider semantic ChangeSet
    -> deterministic audit
    -> operation-specific incremental IFC applicator
    -> repaired.ifc
    -> semantic and geometric evaluation
```

Do not serialize the complete IFC into an LLM prompt. Do not rebuild the whole
existing IFC from BIM JSON. Do not let the model emit STEP text or low-level IFC
placement/representation entities.

The first implemented operation concerns a window, but the architecture is not
a window-only architecture.

## 2. Required implementation order

Use this order:

```text
repository inspection and reuse map
-> design/schema/prompt consistency check
-> selected sample freeze
-> deterministic mutation
-> private/public projection
-> compact context builder
-> common ChangeSet envelope and operation registry
-> common audit dispatcher
-> first Window operation handler
-> transactional IFC application
-> common and Window-specific comparison
-> deterministic fake-provider E2E
-> real-provider UAT
-> documentation and evidence update
```

Do not start with BIMNet, batch evaluation, curved walls, doors, beams or
columns. Leave tested extension points for them.

## 3. Repository inspection

Identify and document reusable components for:

1. BIM JSON 2.0 identity, placement and representation conventions;
2. current BIM JSON ChangeSet envelope, scope, validation and immutable apply;
3. Prompt Registry and provider traces;
4. issue normalization, evidence bundles and deterministic gates;
5. IFC2X3 entity, placement, geometry, relationship and identity creation;
6. IFC reopen and geometry verification;
7. atomic artifact writing;
8. test and dataset artifact conventions.

Reuse concepts and code only when their contracts fit. In particular, the
current BIM JSON ChangeSet applicator validates a complete Formal BIM JSON
candidate and cannot be reused unchanged as an imported-IFC applicator.

Produce a short reuse map before implementation.

## 4. Frozen first sample

Use:

```text
dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc
```

Expected frozen facts:

```text
schema: IFC2X3
size: 1,292,595 bytes
sha256: 102f8123f85eae5e237d7f6a9dcbc364bd5f1c0cfb94b40a7eeb2d7eac9bb725
source revision: 595fa90e3af7120d004fcb37a79d8657f1d1c9c2
license: MIT; evidence in the submodule LICENSE file
projects/sites/buildings: 1/1/1
storeys: 2
spaces: 8
walls: 18
openings: 60
windows: 42
doors: 18
IfcRelFillsElement: 60
IfcRelVoidsElement: 60
explicit curved walls: 0
valid Window-Opening-Wall chains: 42
```

Initial target:

```text
storey: Level 1
wall name: Basic Wall:Outside wall:346660
wall GlobalId: 1F6umJ5H50aeL3A1As_wTm
opening GlobalId: 2cXV28XOjE6f6irhW0CO4t
window GlobalId: 2cXV28XOjE6f6irgi0CO4t
window name: M_Fixed:0915 x 1830mm:354395
wall axis: [0,0,0] -> [8200,0,0] mm, straight two-point polyline
wall size: 8200 mm long, 200 mm thick, 3850 mm high
window size: 915 mm x 1830 mm
opening local origin: [3500, 100, 305] mm relative to the host wall;
  X is the Revit placement anchor, not the geometric centre; Z is the sill height
opening wall-local geometric X bounds: [2585, 3500] mm
opening geometric centre offset: 3042.5 mm
second opening placement X: 5315 mm; geometric X bounds: [4400, 5315] mm;
  geometric centre offset: 4857.5 mm
```

Before freezing the case artifact, additionally verify and record:

- the human-readable meaning of the wall local-X start in the repair request;
- the distinction between private authoring placement anchor and public
  wall-local geometric centre offset;
- target Opening representation details needed by the mutation manifest;
- an individual raw-file/experiment manifest authorizing evaluation use while
  preserving `training_eligible: false`.

Existing inspection evidence already shows that deleting the target Window and
Opening increases the host-wall volume by `0.33489 m3`, exactly
`0.915 * 1.83 * 0.2`, so the semantic opening removal closes the target void.
The target wall has no usable `IfcRelSpaceBoundary`; do not invent a room name.

Do not mutate the source file in place. Bind every case to the source SHA-256.

## 5. First mutation

Implement only:

```text
remove_window_and_opening
```

It must remove:

- the selected `IfcWindow`;
- its `IfcRelFillsElement`;
- its `IfcOpeningElement`;
- the corresponding `IfcRelVoidsElement`;
- direct dependent objects that cannot legally remain, recorded explicitly.

It must preserve:

- the host wall and its geometry, placement, identity, properties, materials
  and type assignments;
- all storeys and spaces;
- the door and door opening;
- the second window on the same host wall;
- all unrelated components and relationships.

The mutation must be deterministic, atomic and non-destructive. Generate:

```text
damaged.ifc
mutation_manifest.private.json
mutation_report.json
```

The damaged model must reopen as IFC2X3 and the target wall region must no
longer have the selected semantic/geometric opening.

## 6. Private/public separation

The private manifest may contain the exact deleted entities, STEP IDs,
GlobalIds, relationships, placement, geometry and comparison ground truth.

Create a deterministic allowlist projection that produces a public repair
specification. It may include:

- requested operation type;
- storey name;
- human-readable wall description;
- unambiguous wall-local reference and opening-centre offset;
- window/opening width, height and sill height;
- preservation requirements.

It must not expose:

- deleted Window or Opening GlobalId;
- STEP IDs;
- original relationship IDs;
- original entity payloads;
- private manifest paths or contents;
- gold ChangeSet.

Tests must prove that the Provider input is constructed only from public
artifacts.

## 7. Compact model context

Create a versioned public context contract, for example:

```text
text2ifc/ifc-repair-context/0.1
```

The Context Builder must be operation-aware and budgeted. For the first case it
should include only the relevant storey and a bounded list of compatible
straight-wall candidates with:

- stable public target ID and IFC GlobalId;
- name and IFC class;
- storey;
- wall-local coordinate basis;
- length, height and thickness;
- direction/exterior evidence when reliable;
- existing opening intervals;
- geometry capability classification.

Record context bytes, estimated tokens, selection rules and omitted candidate
counts. Never silently truncate the true target.

The common context schema must not contain Window-only root fields. Use a
typed target-detail payload supplied by an operation context adapter.

## 8. Common IFC repair ChangeSet

Create a versioned sibling of the current BIM JSON ChangeSet, for example:

```text
text2ifc/ifc-repair-changeset/0.1
```

Reuse the existing governance model:

- stable ChangeSet and operation IDs;
- base fingerprint binding;
- request/evidence binding;
- explicit scope and forbidden targets;
- deterministic validation;
- transactional application;
- preservation accounting;
- immutable artifacts and trace provenance.

Do not pretend the base is a Formal BIM JSON candidate. It is an IFC file.

The common envelope must support heterogeneous operations without changing the
dispatcher.

## 9. Operation registry

Implement a registry interface with at least:

```text
operation_type
target_ifc_classes
parameter_schema
context_adapter
precondition_checker
applicator
postcondition_checker
comparison_adapter
capability_constraints
```

Requirements:

1. Common orchestration must dispatch through the registry.
2. Common modules must not import Window implementation details.
3. An unknown operation must fail with a stable machine-readable error.
4. A test-only second operation fixture must be registrable without editing the
   common dispatcher. It does not need to mutate a real IFC.
5. Operation handlers must report created, modified and removed IFC objects.

Planned future operations include:

```text
add_opening_to_wall
add_door_with_opening_to_wall
add_beam
add_column
remove_component
update_component_placement
```

These are extension targets, not first-phase deliverables.

## 10. First operation

Implement:

```text
add_window_with_opening_to_wall
```

The Provider should output a semantic operation containing:

- target wall GlobalId;
- wall-local start reference and opening-centre offset;
- opening width and height;
- sill height;
- `fit_opening: true` for the window;
- evidence references.

The Provider must not output:

- raw STEP;
- `IfcLocalPlacement`, `IfcAxis2Placement3D`, `IfcCartesianPoint` or
  `IfcDirection` entities;
- OwnerHistory;
- representation topology;
- generated GlobalIds;
- unrelated IFC objects.

Deterministic code expands the semantic operation into:

- `IfcOpeningElement`;
- `IfcRelVoidsElement`;
- `IfcWindow`;
- `IfcRelFillsElement`;
- required placement and representation;
- required containment/type/property assignments when the selected source
  convention or acceptance contract requires them.

## 11. Audit

Implement common checks:

- JSON/schema validity;
- operation registration;
- IFC2X3 target schema;
- base model fingerprint;
- request/evidence binding;
- target existence and class;
- scope and forbidden targets;
- finite values and unit normalization;
- operation conflicts;
- precondition evidence availability.

Implement Window-operation checks:

- target wall is supported and straight;
- wall dimensions and local basis are resolvable;
- opening width, height and sill are positive;
- requested horizontal and vertical extents fit within the wall;
- requested interval does not overlap another opening;
- opening depth can safely void the wall;
- no duplicate target operation exists.

Return structured evidence. A Boolean-only audit is insufficient.

Curved, segmented or unknown wall geometry must produce:

```text
UNSUPPORTED_WALL_GEOMETRY
```

Do not approximate it as straight.

## 12. Transactional incremental application

Apply the audited ChangeSet to an in-memory copy of `damaged.ifc`.

Requirements:

1. Recheck the base fingerprint immediately before application.
2. Never overwrite original or damaged input files.
3. Dispatch each operation through the registry.
4. Evaluate postconditions before publishing output.
5. Write to a temporary path and reopen with IfcOpenShell.
6. Atomically publish `repaired.ifc` only after all checks pass.
7. On failure, return structured diagnostics and do not leave a success-looking
   repaired artifact.

Reuse or refactor existing compiler geometry, placement, relationship and
identity helpers where they can operate safely on an existing IFC file. Do not
create a second full IFC compiler.

## 13. Semantic and geometric comparison

Do not compare IFC bytes, STEP IDs or entity order.

The common comparator must report:

- IFC readability and schema preservation;
- operation postcondition status;
- non-target additions, removals and modifications;
- non-target GlobalId, placement, relationship and geometry drift;
- duplicate components;
- complete repair success.

The Window comparison adapter must report:

- correct host wall;
- correct Opening-Voids-Wall relation;
- correct Window-Fills-Opening relation;
- storey consistency;
- width, height, sill, opening-centre wall-local offset and orientation errors;
- restored geometric void;
- duplicate Window or Opening creation.

Use explicit millimetre and degree tolerances recorded in the report.

## 14. Artifact layout

Follow repository conventions. The intended responsibility split is:

```text
schemas/agent/                    public context and ChangeSet schemas
src/text2ifc_ifc_repair/          common runtime and registry
src/text2ifc_ifc_repair/operations/ operation handlers
scripts/ifc_repair/               inventory, mutation and case runner CLIs
tests/ifc_repair/                 unit and integration tests
dataset/processed/ifc-repair/     generated inventories and case artifacts
```

Exact names may be refined during implementation, but do not put production
logic only under `evaluation/` or hard-code the first case throughout common
modules.

## 15. Offline deterministic acceptance

Use a deterministic fake Provider that receives only:

- `repair_request.txt`;
- public repair specification;
- compact public context;
- public ChangeSet schema and supported operation definitions.

Automated tests must cover at least:

1. selected source Header, SHA-256 and counts;
2. no supported curved wall in the first target;
3. curved-wall rejection fixture;
4. deterministic mutation;
5. source immutability;
6. target Window/Opening/Fills/Voids removal;
7. unrelated door/window preservation;
8. private/public allowlist;
9. context budget and target retention;
10. common ChangeSet validation;
11. operation registry dispatch and unknown-operation rejection;
12. fake second-operation registration without dispatcher changes;
13. base fingerprint and scope failures;
14. Window preconditions and overlap checks;
15. transactional application;
16. repaired IFC reopen;
17. relationship and geometry restoration;
18. unexpected-change detection;
19. Provider input contains no private artifact;
20. complete fake-provider E2E.

## 16. Real Provider UAT

After offline tests pass, run one real Provider case using the same public
contract. Preserve:

```text
prompt id and hash
repair request
public context
raw provider response
parsed predicted changeset
audit evidence
repaired.ifc
evaluation_report.json
Chinese report.md
artifact manifest and private-input exclusion evidence
```

A deterministic or gold ChangeSet must not be presented as real Provider
output. If the Provider fails, record the failure honestly; do not bypass it
with private ground truth.

## 17. Documentation discipline

During implementation, keep these synchronized:

- canonical design document;
- public JSON Schemas;
- Prompt Registry asset;
- operation capability table;
- selected sample report;
- automated test acceptance list;
- implementation summary and exact commands;
- unresolved limitation list.

At every implementation wave, append evidence and decisions instead of
rewriting history. Mark proposed future operations as unsupported until their
own tests and UAT pass.

## 18. Required deliverables

Produce:

1. repository reuse map;
2. frozen sample and target report;
3. deterministic mutation and private manifest;
4. public projection and repair request;
5. compact public context contract and builder;
6. common IFC repair ChangeSet Schema;
7. extensible operation registry;
8. common structured Audit;
9. Window operation handler;
10. transactional incremental IFC applicator;
11. common and Window-specific comparator;
12. offline fake-provider E2E tests;
13. one real Provider UAT evidence bundle;
14. JSON and Chinese Markdown evaluation reports;
15. exact created/modified file list and commands;
16. reused-component list;
17. new-component justification;
18. known limitations and the BIMNet/curved-wall/door/beam/column next-step map.

## 19. Completion boundary

The first phase is complete only when:

- the selected BIM Whale source is hash-bound and unchanged;
- mutation removes Window and Opening while preserving unrelated content;
- the Provider sees only bounded public context;
- the predicted ChangeSet targets the correct wall and is audited;
- the applicator creates valid Opening, Window, Voids and Fills entities;
- the repaired IFC reopens and matches the requested geometry within tolerance;
- non-target drift is within the documented policy;
- offline tests pass;
- one real Provider UAT has traceable evidence;
- the registry proves the common system is not hard-coded to Window;
- BIMNet, curved walls, wall-only openings, doors, beams and columns remain
  explicit future work rather than unverified claims.

## 20. Implementation record — 2026-07-17

The offline deterministic path through the Window operation is implemented and
covered by automated tests. The committed evidence case is:

```text
dataset/processed/ifc-repair/cases/large-building-window-repair-001-offline-v1/
```

The real Provider UAT runner uses the same public contract. On 2026-07-18 the
repository `.env` was verified as a configured DeepSeek OpenAI-compatible path:
the API key is present, the endpoint host is `api.deepseek.com`, the selected
model is `deepseek-v4-flash`, and both configured input and output budgets are
`65536`. Secret values are never copied into reports.

Configuration readiness alone is not live acceptance. A real DeepSeek request
was executed on 2026-07-18 and passed the full ChangeSet, Audit, transactional
application and Comparator path. Its evidence is stored at
`dataset/processed/ifc-repair/cases/large-building-window-repair-001-deepseek-live-20260718-v2/`;
the offline fake result remains separately labelled.

Both DeepSeek budgets are fixed at `65536 tokens`: one client-side maximum
input guard and one Provider maximum output setting. The live-tested Prompt
includes the target schema, verified `spec:`/`context:` evidence namespaces, an
entire valid Window ChangeSet example, and untrusted-data instructions recorded
in the design decision log. A possible `128k` input setting remains a separate
near-limit context test and is not implied by this `6381`-prompt-token UAT.
