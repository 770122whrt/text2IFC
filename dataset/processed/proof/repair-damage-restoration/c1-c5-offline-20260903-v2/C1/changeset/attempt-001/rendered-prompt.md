# IFC Repair ChangeSet Draft Generator 0.5

Return exactly one JSON draft conforming to `CHANGESET_SCHEMA`. Deterministic
code, not the Provider, binds and authors semantic assignments.

## Public request

On storey "12 twaalfde verdieping" of this building, restore the two missing support beams in one atomic ChangeSet. Each beam has a rectangular section 250 mm wide (horizontal) by 450 mm deep (vertical). Beam 1 occupies the centerline from (19290.0, 36452.5, -575.0) mm to (19290.0, 29005.0, -575.0) mm (storey-local); beam 2 occupies the centerline from (22590.0, 36452.5, -575.0) mm to (22590.0, 29005.0, -575.0) mm. Each axis is fully determined by its start and end points; do not state a scalar length. Reuse the existing beam type with GlobalId 0OvyTYAaD5pfeQsZGtwMGy for both beams; do not generate new types. Restore both beams with their common properties: load bearing = true, external = false, FireRating = "120" (a text label), slope = 0.0, reference = "balk vierkant_gen_250x710 (C25/30)".

## Immutable bindings

- source request: sha256:69b62e9c1778c1d8989bf21eb4b803bb185421448b410ce64c692f44a885a9a0
- model: sha256:df78acdeb823224384b87eecdabf3f42984c50ee02f8f3717053de5c9189e13e
- semantic manifest ref: changeset/semantic-manifests.json
- semantic manifest hash: sha256:160b0140d487a9c42ff3592a91d9a32bd8ecd382a49a7adf2506c1dae6eb6dcf

## Resolved operation projection

{"evidence_refs": ["resolved:/operations/restore-beam-1/context/candidate_targets/0", "resolved:/operations/restore-beam-2/context/candidate_targets/0"], "operations": [{"evidence_refs": ["resolved:/operations/restore-beam-1/context/candidate_targets/0"], "operation_id": "restore-beam-1", "operation_type": "add_beam", "parameters": {"axis": {"end": {"x_mm": 19290.0, "y_mm": 29005.0, "z_mm": -575.0}, "start": {"x_mm": 19290.0, "y_mm": 36452.5, "z_mm": -575.0}}, "section": {"height_mm": 450.0, "shape": "rectangle", "width_mm": 250.0}}, "target": {"storey_global_id": "02GkOQJZz4x9WAhoZkKFPX"}}, {"evidence_refs": ["resolved:/operations/restore-beam-2/context/candidate_targets/0"], "operation_id": "restore-beam-2", "operation_type": "add_beam", "parameters": {"axis": {"end": {"x_mm": 22590.0, "y_mm": 29005.0, "z_mm": -575.0}, "start": {"x_mm": 22590.0, "y_mm": 36452.5, "z_mm": -575.0}}, "section": {"height_mm": 450.0, "shape": "rectangle", "width_mm": 250.0}}, "target": {"storey_global_id": "02GkOQJZz4x9WAhoZkKFPX"}}], "scope": {"forbidden_ids": [], "target_ids": ["02GkOQJZz4x9WAhoZkKFPX"]}}

The entire `RESOLVED_OPERATIONS` object is the canonical envelope authority.
Copy its `scope`, `evidence_refs`, and every operation exactly. Preserve every
list order shown there; do not reconstruct or sort any union yourself.

## Semantic group counts

{"conditional": 16, "not_required": 0, "required": 4}

## Explicit user slot references

["pset:Pset_BeamCommon.FireRating", "pset:Pset_BeamCommon.IsExternal", "pset:Pset_BeamCommon.LoadBearing", "pset:Pset_BeamCommon.Reference", "pset:Pset_BeamCommon.Slope"]

## Selected operation contracts, profiles, and sentinel few-shots

{"few_shots": [{"case": "complete", "example_id": "beam.add.stage2.v0.1.complete", "expected": {"evidence_refs": ["resolved:/operations/beam-example-1/context/candidate_targets/0"], "operation_id": "beam-example-1", "operation_type": "add_beam", "parameters": {"axis": {"end": {"x_mm": 5000, "y_mm": 0, "z_mm": 3000}, "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000}}, "section": {"height_mm": 500, "shape": "rectangle", "width_mm": 300}}, "target": {"storey_global_id": "EXAMPLE-STOREY-BEAM"}}, "output_schema": "text2ifc/ifc-repair-stage2-operation/0.1", "profile_id": "beam.add.stage2.v0.1", "rule": "Copy the deterministic resolved operation exactly; Stage 2 does not emit intent, Type, property, status, clarification, or unsupported-result fields.", "schema_version": "text2ifc/ifc-repair-stage2-few-shot/0.1", "sentinel": "EXAMPLE_ONLY"}], "operation_contracts": [{"operation_type": "add_beam", "parameter_schema": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"end": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}, "start": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}}, "required": ["start", "end"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"height_mm": {"exclusiveMinimum": 0, "type": "number"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "height_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "postcondition_names": ["beam_geometry_matches", "beam_contained_in_storey", "beam_type_bound"], "precondition_names": ["target_exists", "structural_axis_available", "structural_type_authorized"], "target_ifc_classes": ["IfcBuildingStorey"], "target_schema": {"additionalProperties": false, "properties": {"storey_global_id": {"minLength": 1, "type": "string"}}, "required": ["storey_global_id"], "type": "object"}}], "selected_profiles": [{"action": "add", "component_family": "beam", "draft_responsibility": "Copy the deterministic resolved target, geometry parameters, and evidence references into the Draft operation exactly. Consumed upstream authority is not recreated or reinterpreted.", "few_shot_output_schema": "text2ifc/ifc-repair-stage2-operation/0.1", "few_shots": [{"example_id": "beam.add.stage2.v0.1.complete", "path": "prompts/agent/ifc-repair-few-shots/beam-add-stage2-v0.1-complete.json", "sha256": "sha256:0cfebe0759f75b33346f86c01e580f387f5bb12549e55d32692f9d6187433e39"}], "operation_type": "add_beam", "profile_hash": "sha256:6281a88273c828c8e52057652c6f91982e7d03975a93e79e2f2629e68675ad4b", "profile_id": "beam.add.stage2.v0.1", "profile_version": "0.1", "schema_version": "text2ifc/ifc-repair-prompt-profile/0.3", "stage": "stage2", "stage2_projection_fields": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "target_ifc_classes": ["IfcBuildingStorey"]}]}

## Draft schema

{"$defs": {"beam": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/strings"}, "operation_id": {"$ref": "#/$defs/id"}, "operation_type": {"const": "add_beam"}, "parameters": {"$ref": "#/$defs/beamParameters"}, "target": {"$ref": "#/$defs/target"}}, "required": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "type": "object"}, "beamParameters": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"end": {"$ref": "#/$defs/point"}, "start": {"$ref": "#/$defs/point"}}, "required": ["start", "end"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"height_mm": {"exclusiveMinimum": 0, "type": "number"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "height_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "column": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/strings"}, "operation_id": {"$ref": "#/$defs/id"}, "operation_type": {"const": "add_column"}, "parameters": {"$ref": "#/$defs/columnParameters"}, "target": {"$ref": "#/$defs/target"}}, "required": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "type": "object"}, "columnParameters": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"base": {"$ref": "#/$defs/point"}, "top": {"$ref": "#/$defs/point"}}, "required": ["base", "top"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"depth_mm": {"exclusiveMinimum": 0, "type": "number"}, "orientation": {"additionalProperties": false, "properties": {"x": {"type": "number"}, "y": {"type": "number"}}, "required": ["x", "y"], "type": "object"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "depth_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "hash": {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}, "id": {"minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]*$", "type": "string"}, "point": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}, "scope": {"additionalProperties": false, "properties": {"forbidden_ids": {"$ref": "#/$defs/strings"}, "target_ids": {"$ref": "#/$defs/strings"}}, "required": ["target_ids", "forbidden_ids"], "type": "object"}, "strings": {"items": {"minLength": 1, "type": "string"}, "type": "array", "uniqueItems": true}, "target": {"additionalProperties": false, "properties": {"storey_global_id": {"minLength": 1, "type": "string"}}, "required": ["storey_global_id"], "type": "object"}}, "$id": "text2ifc/ifc-repair-changeset-draft/0.3", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"base_model_fingerprint": {"$ref": "#/$defs/hash"}, "draft_id": {"$ref": "#/$defs/id"}, "evidence_refs": {"$ref": "#/$defs/strings"}, "operations": {"items": {"oneOf": [{"$ref": "#/$defs/beam"}, {"$ref": "#/$defs/column"}]}, "minItems": 1, "type": "array"}, "postconditions": {"$ref": "#/$defs/strings"}, "preconditions": {"$ref": "#/$defs/strings"}, "schema_version": {"const": "text2ifc/ifc-repair-changeset-draft/0.3"}, "scope": {"$ref": "#/$defs/scope"}, "semantic_manifest_ref": {"minLength": 1, "type": "string"}, "semantic_manifest_sha256": {"$ref": "#/$defs/hash"}, "semantic_summary": {"additionalProperties": false, "properties": {"conditional": {"minimum": 0, "type": "integer"}, "not_required": {"minimum": 0, "type": "integer"}, "required": {"minimum": 0, "type": "integer"}}, "required": ["required", "conditional", "not_required"], "type": "object"}, "source_request_hash": {"$ref": "#/$defs/hash"}}, "required": ["schema_version", "draft_id", "base_model_fingerprint", "source_request_hash", "semantic_manifest_ref", "semantic_manifest_sha256", "semantic_summary", "scope", "evidence_refs", "preconditions", "postconditions", "operations"], "title": "Provider Beam and Column IFC Repair ChangeSet Draft 0.3", "type": "object"}

## Previous validation feedback

[]

Rules:

1. Copy all canonical authority identifiers, parameters, scope, evidence, and
   hashes exactly; never rebuild the envelope from operation-local fields.
2. Include every offered operation exactly once and keep its `operation_id`,
   `operation_type`, `target`, `parameters`, and `evidence_refs` unchanged.
3. You receive only expanded operation-local semantic summaries.
4. Never request or emit raw cohort candidates, private Ground Truth,
   benchmark Gold, mutation mappings, or hidden original values.
5. Never emit semantic assignments or choose their source. The deterministic
   binder exclusively emits the five authorized source kinds.
6. Do not search targets/prototypes or emit STEP and low-level IFC objects.
7. Return JSON only.
8. Only the selected profiles appear below. A few-shot is structural guidance,
   never authority for project identity, dimensions, Type, or property values.
