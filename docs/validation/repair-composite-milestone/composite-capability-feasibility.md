# Composite Capability Feasibility — Text2IFC Composite Repair Milestone

**Status:** health check of frozen production path at base revision
`8bfcfe075521ddb142f8608296dfbfea1fd385e4` (branch `Zcode`).

**Purpose:** specification Section 2 / Section 5. Zero-Provider inspection of
the six registered operations required by the Composite Scale Ladder, plus the
multi-operation atomic composition capability. No Provider call is involved in
anything recorded here.

**Verdict table**

| Operation | Registry | Intent schema | Stage 2 profile | Binder | Applicator | Comparison adapter | Focused tests | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `add_beam` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 6/6 pass | `HEALTHY_FOR_COMPOSITE_EVIDENCE` |
| `add_column` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5 pass | `HEALTHY_FOR_COMPOSITE_EVIDENCE` |
| `add_window_with_opening_to_wall` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 4/4 pass | `HEALTHY_FOR_COMPOSITE_EVIDENCE` |
| `add_door_with_opening_to_wall` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 4/4 pass | `HEALTHY_FOR_COMPOSITE_EVIDENCE` |
| `fill_existing_opening_with_door` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | (in same file) 4/4 pass | `HEALTHY_FOR_COMPOSITE_EVIDENCE` |
| `set_occurrence_properties` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 pass | `HEALTHY_FOR_COMPOSITE_EVIDENCE` |
| Multi-operation atomic ChangeSet (2–6 ops, mixed families) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 11/11 + 12/12 + 20/20 pass | `HEALTHY_FOR_COMPOSITE_EVIDENCE` |

## 1. `add_beam`

| Aspect | Evidence |
| --- | --- |
| Registry entry | `src/text2ifc_ifc_repair/operations/__init__.py:25` registers `beam_operation_definition()`; `OPERATION_TYPE = "add_beam"` at `src/text2ifc_ifc_repair/operations/beam.py:40`; full `OperationDefinition` at `beam.py:214-267` |
| Intent schema (Stage 1) | `_INTENT_PARAMETER_SCHEMA` at `beam.py:92-131` (axis start/end in mm, rectangle section w/h); `_INTENT_TARGET_SCHEMA` at `beam.py:132-149` (Storey by `global_id` or `names`) |
| Prompt profile | Stage 1 profile `beam.add.v0.3` bound at `beam.py:260`, registered in `prompts/agent/registry.json` → `prompts/agent/ifc-repair-profiles/beam.add.v0.3.json`; Stage 2 profile `beam.add.stage2.v0.1` at `beam.py:261` |
| Stage 2 contract | Stage 2 binding is family-generic: provider stage selects profiles via `select_prompt_profiles` (`src/text2ifc_ifc_repair/prompt_profiles.py`); changeset envelope `text2ifc/ifc-repair-changeset/0.4` validated in `src/text2ifc_ifc_repair/changesets.py:21-35` |
| Binder | deterministic binding + audit in `src/text2ifc_ifc_repair/audit.py`; resolved Storey target projection via `OperationRegistry.bind_resolved_target` (`src/text2ifc_ifc_repair/registry.py:267-301`) |
| Applicator | `_applicator` at `beam.py:413-490` — creates `IfcBeam` + generated/reused `IfcBeamType` + `IfcRelDefinesByType` + Storey containment |
| Postconditions | `beam.py:493-564`: `BEAM_GEOMETRY_MATCHES`, `BEAM_CONTAINED_IN_STOREY`, `BEAM_TYPE_BOUND`, `BEAM_ANALYSIS_RELATIONSHIPS_ABSENT` |
| Comparison/evaluation adapter | `_comparison_adapter` at `beam.py:567-582` → `structural_l1_comparison_report` (`src/text2ifc_ifc_repair/operations/structural_member.py:98-`); L2 policy `BEAM_EVALUATION_POLICY` at `beam.py:167-211` |
| Geometry constraints (freeze-relevant) | Beam axis must be horizontal (`STRUCTURAL_BEAM_NOT_HORIZONTAL`, `operations/structural_member.py:57-64`); section rectangle unrotated; grid/curved/analysis unsupported (`src/text2ifc_ifc_repair/structural_resolution.py:14-86`) |
| Focused test command | `python -m pytest tests/ifc_repair/test_beam_application.py tests/ifc_repair/test_beam_resolution.py -q -p no:cacheprovider --basetemp=<composite-evidence-*>` → **6 passed** (recorded 2026-08-31) |

## 2. `add_column`

| Aspect | Evidence |
| --- | --- |
| Registry entry | `operations/__init__.py:26`; `OPERATION_TYPE = "add_column"` at `src/text2ifc_ifc_repair/operations/column.py:40`; definition at `column.py:219-270` |
| Intent schema | `_INTENT_PARAMETER_SCHEMA` at `column.py:99-136` (axis base/top mm, rectangle section w/d + optional orientation); `_INTENT_TARGET_SCHEMA` at `column.py:137-` (Storey) |
| Prompt profile | `column.add.v0.3` at `column.py:266`; Stage 2 `column.add.stage2.v0.1` at `column.py:267` |
| Applicator | `_applicator` at `column.py:416-499` (IfcColumn + IfcColumnType + containment) |
| Postconditions | `column.py:501-590` (`COLUMN_GEOMETRY_MATCHES`, `COLUMN_CONTAINED_IN_STOREY`, `COLUMN_TYPE_BOUND`, …) |
| Comparison adapter | `column.py:592-` → `structural_l1_comparison_report` |
| Geometry constraints | Column must be vertical, upward (`STRUCTURAL_COLUMN_NOT_VERTICAL` / `STRUCTURAL_COLUMN_AXIS_DIRECTION_INVALID`, `operations/structural_member.py:65-79`) |
| Focused test command | `python -m pytest tests/ifc_repair/test_column_application.py tests/ifc_repair/test_column_resolution.py -q -p no:cacheprovider --basetemp=<composite-evidence-*>` → **5 passed** (recorded 2026-08-31) |

## 3. `add_window_with_opening_to_wall`

| Aspect | Evidence |
| --- | --- |
| Registry entry | `operations/__init__.py:20`; `OPERATION_TYPE` at `src/text2ifc_ifc_repair/operations/window.py:48`; definition at `window.py:354-398` |
| Intent schema | `PARAMETER_SCHEMA` at `window.py:60-93` (position wall_local_start + center_offset_mm; opening w/h/sill); wall target via public `target_query` (`geometry_constraints`: `storey_elevation_mm`, `wall_length_mm`, `wall_height_mm`, `wall_thickness_mm`; `direction`; `geometry_capabilities: ["straight_wall"]`) |
| Prompt profile | `window.add-with-opening` at `window.py:392`, registered in registry.json |
| Applicator | `window.py:689-` — creates IfcOpeningElement + IfcWindow + voids/fills relationships + generated IfcWindowStyle + Pset/quantity |
| Postconditions | window chain checks incl. `OPENING_WITHIN_WALL_HORIZONTAL/VERTICAL`, `OPENING_VOIDS_TARGET_WALL` (`window.py:577-599, 956`) |
| Comparison adapter | `window.py:997-` |
| Focused test command | `python -m pytest tests/ifc_repair/test_window_application.py -q -p no:cacheprovider --basetemp=<composite-evidence-*>` → **4 passed** (recorded 2026-08-31) |

## 4. `add_door_with_opening_to_wall`

| Aspect | Evidence |
| --- | --- |
| Registry entry | `operations/__init__.py:23`; `ADD_OPERATION_TYPE` at `src/text2ifc_ifc_repair/operations/door.py:53`; definition at `door.py:258-265` |
| Intent schema | `_ADD_INTENT_PARAMETER_SCHEMA` at `door.py:148-177` (position reference wall_local_start/midpoint/end; opening w/h + `dimension_meaning`; door style enum) |
| Prompt profile | `door.add-with-opening.v0.2` at `door.py:262` |
| Applicator / postconditions / comparison | `door.py:833-`, `door.py:978-` |
| Focused test command | `python -m pytest tests/ifc_repair/test_door_application.py -q -p no:cacheprovider --basetemp=<composite-evidence-*>` → **4 passed** (both door operations covered: add + fill) (recorded 2026-08-31) |

## 5. `fill_existing_opening_with_door`

| Aspect | Evidence |
| --- | --- |
| Registry entry | `operations/__init__.py:24`; `FILL_OPERATION_TYPE` at `door.py:54`; definition at `door.py:270-276` |
| Intent schema | `_FILL_INTENT_PARAMETER_SCHEMA` at `door.py:189-198` (`fit_existing_opening: true` + door style); opening located via public `target_query` on `IfcOpeningElement` with `geometry_capabilities: ["measured_hosted_opening"]` and constraints `opening_width_mm/height_mm/depth_mm/center_offset_mm/sill_height_mm` |
| Prompt profile | `door.fill-existing-opening.v0.2` at `door.py:274` |
| Applicator / postconditions | `door.py` (fill path reuses exact door type; `test_door_application.py:344` proves it) |
| Focused test command | same `test_door_application.py` run → **4 passed** (recorded 2026-08-31) |

## 6. `set_occurrence_properties`

| Aspect | Evidence |
| --- | --- |
| Registry entry | `operations/__init__.py:21`; `OPERATION_TYPE` at `src/text2ifc_ifc_repair/operations/occurrence_property.py:21`; definition at `occurrence_property.py:49-99`; editable classes IfcBeam/IfcColumn/IfcDoor/IfcWall(+StandardCase)/IfcWindow (`occurrence_property.py:23-30`) |
| Prompt profile | `occurrence.set-properties` at `occurrence_property.py:97` |
| Stage 1.5 | property resolution stage `src/text2ifc_ifc_repair/property_resolution_stage.py:43-51` (template `ifc-property-resolution.v0.2`) |
| Applicator / comparison adapter | `occurrence_property.py:262-`, `occurrence_property.py:351-` |
| Focused test command | `python -m pytest tests/ifc_repair/test_occurrence_property_operation.py -q -p no:cacheprovider --basetemp=<composite-evidence-*>` → **9 passed** (recorded 2026-08-31) |

## 7. Multi-operation atomic composition (required by the scale ladder)

The ChangeSet contract carries unique `operation_id` semantics: Stage 1 intent
enforces uniqueness (`src/text2ifc_ifc_repair/repair_intent.py:540-546`,
`DUPLICATE_OPERATION_ID`), the changeset layer rejects duplicate ids
(`src/text2ifc_ifc_repair/changesets.py:313-337`), and Stage 2 requires the
bound operation id set to equal the resolved set
(`src/text2ifc_ifc_repair/provider_stage.py:762-765`). Atomicity at apply time
is enforced by `_complete_transaction_valid`
(`src/text2ifc_ifc_repair/orchestrator.py:368-373`): all operations applied,
audited, published once; any failure suppresses the whole transaction
(`tests/ifc_repair/test_structural_atomicity.py:419`).

Focused commands (all recorded 2026-08-31, repo `.venv`, isolated basetemp):

| Command | Result |
| --- | --- |
| `python -m pytest tests/ifc_repair/test_structural_atomicity.py -q -p no:cacheprovider --basetemp=<composite-evidence-*>` | **11 passed** (incl. beam+column one strict transaction at `:335`; postcondition failure suppresses whole transaction at `:419`; 4-family changeset publishes once at `:520`) |
| `python -m pytest tests/ifc_repair/test_mixed_hosted_operation_atomicity.py -q ...` | **1 passed** (cross-family overlap rejected before publication) |
| `python -m pytest tests/ifc_repair/test_structural_stage2_contract.py -q ...` | **20 passed** (Stage 2 projection + unchanged-authority bind; binder rejects provider changes to resolved authority at `:564`) |
| `python -m pytest tests/ifc_repair/test_phase12_dataset_e2e.py -q ...` | **12 passed** (incl. `test_four_family_case_is_one_success_and_one_real_rollback` at `:494`: window ×2 + door-fill ×2 + beam + column = 6 ops in ONE accepted atomic case over `vvo.ifc`) |

The frozen proof case
`dataset/processed/proof/ifc-repair-success-cases/mixed/door-window-beam-column/phase12-vvo-door-window-beam-column-atomic/`
(recorded 2026-08-31, read-only) demonstrates the current frozen capability
ceiling: **6 operations across 4 families in one atomic ChangeSet**, applied
with 47 created entities and one publication. Its `repair-intent.json` shows
the public binding style that the composite cases below reuse (wall geometry
constraints, opening geometry constraints, Storey GlobalId for structural ops).

## 8. Feasibility of the requested scale-ladder compositions

| Requested composition | Feasible with current frozen path? | Evidence |
| --- | --- | --- |
| C1: Beam ×1 + Column ×1, atomic | **Yes** | `test_structural_atomicity.py:335` (beam+column one transaction); frozen proof `phase12-d7n-beam-column-atomic` |
| C2: Column ×2 + Door ×1 entity-level, atomic | **Yes** — door as `fill_existing_opening_with_door` (needs a real empty opening) or `add_door_with_opening_to_wall` (needs a wall) | four-family case has 2 door-fills + column + beam atomic (`test_phase12_dataset_e2e.py:494`); `test_phase12_dataset_e2e.py:79` mixed 2-window+2-door atomic |
| C3: Beam ×2 + Column ×2 + Window ×1, atomic | **Yes** — 5 ops; four-family case proves 6 ops incl. 2 windows | `test_phase12_dataset_e2e.py:494`; `run_phase12_offline.py:109,745` case matrix `phase12-vvo-door-window-beam-column-atomic` (window ×2 + door ×2 + beam + column) |
| C4: Column ×4 + Beam ×1 + Door ×1 + Window ×1 (7 ops) | **Yes in principle** — nothing in the changeset/atomicity contract caps operation count; the deterministic GlobalId derivation is per-operation (`operations/hosted_opening.py` `deterministic_global_id`), so N same-family ops need distinct operation_ids/parameters. Largest frozen atomic case has 6 ops; 7 is an extension within proven mechanics, executed as genuine evidence for the first time here. | `changesets.py:313-337` (no cardinality cap); `test_phase12_dataset_e2e.py:494` |
| C5 HERO: ~8–10 entity ops (Beam 2–3, Column 4–5, Door 1, Window 1) + ≤2 property intents | **Yes in principle** (same reasoning as C4). Largest historical atomic case = 6 ops; hero extends to ~9–10 within proven per-operation mechanics. Property intents ride on the operation (e.g. door FireRating, window IsExternal) via `property_intents` on the intent + Stage 1.5 (`property_resolution_stage.py`). | same as C4; `tests/ifc_repair/test_property_resolution_family_e2e.py:202` |
| C5-N: same + 1 unsupported `structural_analysis_node` → zero mutation | **Yes** — `structural_analysis_node` verified absent from the registry (`create_default_registry()` registers exactly 7 operation types, `operations/__init__.py:18-27`; `structural_analysis_node` not among them; intent capability checker returns `STRUCTURAL_ANALYSIS_UNSUPPORTED` for `structural_analysis_*` capability ids, `src/text2ifc_ifc_repair/request_stage.py:455-458`). R1 H4 froze the same guard shape (`repair-acceptance-freeze.json` case H4, reason `STRUCTURAL_ANALYSIS_UNSUPPORTED`, zero mutation). | `request_stage.py:430-505` |

**Door/Window entity-level authoring is healthy.** The four-family frozen
proof contains genuine entity-level door fills (2 IfcDoor + 2 IfcDoorStyle
created) and window+opening chains (2 IfcWindow + 2 IfcWindowStyle + 2
IfcOpeningElement created), so no substitution of property-only cases is
needed or used.

## 9. Known constraints the case design must respect (frozen behavior, not to be worked around)

1. **Beam axes are horizontal, columns vertical** (`operations/structural_member.py:57-79`). All frozen geometry obeys this.
2. **Structural placement is Storey-local mm with z relative to the Storey** (`beam.py:296` `coordinate_reference: storey_local_mm`); target Storey is bound by GlobalId at Stage 1.
3. **Structural Type authority**: exactly one `relationship:type` semantic assignment per structural op (`beam.py:316-325`); type policy is generated or exact-reuse, and Stage 2 must not change resolved authority (`test_structural_stage2_contract.py:564`).
4. **Same-axis overlap is rejected** (`STRUCTURAL_EXISTING_SAME_AXIS_OVERLAP`, `beam.py:355-365`) — repeated same-family ops must use spatially separated axes.
5. **Same-family conflicts are checked** via `conflict_domain` (`structural_member` for beam/column; `hosted_opening` for door/window) — `operations/hosted_opening.py` `hosted_opening_conflict_checker`.
6. **Deterministic GlobalId derivation is per operation_id** — two same-family operations with identical parameters and identical operation_id-derived inputs collide (`DETERMINISTIC_GLOBAL_ID_COLLISION`, `beam.py:371-383`). Distinct operation_ids + distinct geometry avoid this.
7. **Wall/opening targeting must be public**: wall by geometry constraints (length/height/thickness/storey elevation/direction) with `straight_wall` capability; opening by measured geometry with `measured_hosted_opening` capability. GlobalId/Name targeting is available but GlobalId-only requests make the case trivially resolvable; geometry-constraint requests match the frozen four-family precedent and exercise the real retriever.
8. **Property intents are resolved through Stage 1.5** (`property_resolution_stage.py`) when natural-language property claims are present; admissibility is enforced by `src/text2ifc_ifc_repair/property_admissibility.py`.

## 10. Blockers

None. All six operations and the atomic multi-family composition are
`HEALTHY_FOR_COMPOSITE_EVIDENCE`. No capability substitution is required.
