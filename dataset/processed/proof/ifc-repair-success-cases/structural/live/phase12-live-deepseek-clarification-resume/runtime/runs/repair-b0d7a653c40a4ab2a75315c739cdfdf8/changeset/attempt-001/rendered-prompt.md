# IFC Repair ChangeSet Draft Generator 0.4

Return exactly one JSON draft conforming to `CHANGESET_SCHEMA`. Deterministic
code, not the Provider, binds and authors semantic assignments.

## Public request

On the IFC Building Storey named "Level 1", add one vertical straight rectangular Column with center-axis base (120000, 120000, 0) mm and top (120000, 120000, 6000) mm, a section 400 mm wide and 600 mm deep, and local width direction (0, 1). Set its natural-language property "load bearing status or external status" to true, but do not choose between those two meanings without clarification.

## Immutable bindings

- source request: sha256:9a008ca96cbb317d63fa53aa7bc10b4845924859ef0a8f309f228d866e93169a
- model: sha256:25240558bcbe23c1bbf4916d0b9a0fbbde8202d63dbc7a488ef633ab40eb6127
- semantic manifest ref: changeset/semantic-manifest-add_column_1.json
- semantic manifest hash: sha256:5cb292318f4828b9ca75d1c6a243bba28503fd816df30469e5cb1e583e0bae06

## Resolved operation projection

{"evidence_refs": ["resolved:/operations/add_column_1/context/candidate_targets/0"], "operations": [{"evidence_refs": ["resolved:/operations/add_column_1/context/candidate_targets/0"], "operation_id": "add_column_1", "operation_type": "add_column", "parameters": {"axis": {"base": {"x_mm": 120000.0, "y_mm": 120000.0, "z_mm": 0.0}, "top": {"x_mm": 120000.0, "y_mm": 120000.0, "z_mm": 6000.0}}, "section": {"depth_mm": 600, "orientation": {"x": 0, "y": 1}, "shape": "rectangle", "width_mm": 400}}, "target": {"storey_global_id": "0K_MqVdrL0JOCMi_GblRwJ"}}], "scope": {"forbidden_ids": [], "target_ids": ["0K_MqVdrL0JOCMi_GblRwJ"]}}

## Semantic group counts

{"conditional": 2, "not_required": 0, "required": 2}

## Explicit user slot references

["pset:Pset_ColumnCommon.LoadBearing"]

## Selected operation contracts, profiles, and sentinel few-shots

{"few_shots": [{"case": "complete", "example_id": "column.add.stage2.v0.1.complete", "expected": {"evidence_refs": ["resolved:/operations/column-example-1/context/candidate_targets/0"], "operation_id": "column-example-1", "operation_type": "add_column", "parameters": {"axis": {"base": {"x_mm": 1000, "y_mm": 2000, "z_mm": 0}, "top": {"x_mm": 1000, "y_mm": 2000, "z_mm": 3000}}, "section": {"depth_mm": 600, "orientation": {"x": 0, "y": 1}, "shape": "rectangle", "width_mm": 400}}, "target": {"storey_global_id": "EXAMPLE-STOREY-COLUMN"}}, "output_schema": "text2ifc/ifc-repair-stage2-operation/0.1", "profile_id": "column.add.stage2.v0.1", "rule": "Copy the deterministic resolved operation exactly; Stage 2 does not emit intent, Type, property, status, clarification, or unsupported-result fields.", "schema_version": "text2ifc/ifc-repair-stage2-few-shot/0.1", "sentinel": "EXAMPLE_ONLY"}], "operation_contracts": [{"operation_type": "add_column", "parameter_schema": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"base": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}, "top": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}}, "required": ["base", "top"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"depth_mm": {"exclusiveMinimum": 0, "type": "number"}, "orientation": {"additionalProperties": false, "properties": {"x": {"type": "number"}, "y": {"type": "number"}}, "required": ["x", "y"], "type": "object"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "depth_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "postcondition_names": ["column_geometry_matches", "column_contained_in_base_storey", "column_type_bound"], "precondition_names": ["target_exists", "structural_axis_available", "structural_type_authorized"], "target_ifc_classes": ["IfcBuildingStorey"], "target_schema": {"additionalProperties": false, "properties": {"storey_global_id": {"minLength": 1, "type": "string"}}, "required": ["storey_global_id"], "type": "object"}}], "selected_profiles": [{"action": "add", "component_family": "column", "draft_responsibility": "Copy the deterministic resolved target, geometry parameters, and evidence references into the Draft operation exactly. Consumed upstream authority is not recreated or reinterpreted.", "few_shot_output_schema": "text2ifc/ifc-repair-stage2-operation/0.1", "few_shots": [{"example_id": "column.add.stage2.v0.1.complete", "path": "prompts/agent/ifc-repair-few-shots/column-add-stage2-v0.1-complete.json", "sha256": "sha256:da873c3b68f1d5e9981747baa4e18c6b1d333f44c72d2e0895d4cf86c282053f"}], "operation_type": "add_column", "profile_hash": "sha256:4246f8ab76aeee47ab60b8479773c4573003b30df7348e9a19e59496934b03ab", "profile_id": "column.add.stage2.v0.1", "profile_version": "0.1", "schema_version": "text2ifc/ifc-repair-prompt-profile/0.3", "stage": "stage2", "stage2_projection_fields": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "target_ifc_classes": ["IfcBuildingStorey"]}]}

## Draft schema

{"$defs": {"beam": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/strings"}, "operation_id": {"$ref": "#/$defs/id"}, "operation_type": {"const": "add_beam"}, "parameters": {"$ref": "#/$defs/beamParameters"}, "target": {"$ref": "#/$defs/target"}}, "required": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "type": "object"}, "beamParameters": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"end": {"$ref": "#/$defs/point"}, "start": {"$ref": "#/$defs/point"}}, "required": ["start", "end"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"height_mm": {"exclusiveMinimum": 0, "type": "number"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "height_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "column": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/strings"}, "operation_id": {"$ref": "#/$defs/id"}, "operation_type": {"const": "add_column"}, "parameters": {"$ref": "#/$defs/columnParameters"}, "target": {"$ref": "#/$defs/target"}}, "required": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "type": "object"}, "columnParameters": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"base": {"$ref": "#/$defs/point"}, "top": {"$ref": "#/$defs/point"}}, "required": ["base", "top"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"depth_mm": {"exclusiveMinimum": 0, "type": "number"}, "orientation": {"additionalProperties": false, "properties": {"x": {"type": "number"}, "y": {"type": "number"}}, "required": ["x", "y"], "type": "object"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "depth_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "hash": {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}, "id": {"minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]*$", "type": "string"}, "point": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}, "scope": {"additionalProperties": false, "properties": {"forbidden_ids": {"$ref": "#/$defs/strings"}, "target_ids": {"$ref": "#/$defs/strings"}}, "required": ["target_ids", "forbidden_ids"], "type": "object"}, "strings": {"items": {"minLength": 1, "type": "string"}, "type": "array", "uniqueItems": true}, "target": {"additionalProperties": false, "properties": {"storey_global_id": {"minLength": 1, "type": "string"}}, "required": ["storey_global_id"], "type": "object"}}, "$id": "text2ifc/ifc-repair-changeset-draft/0.3", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"base_model_fingerprint": {"$ref": "#/$defs/hash"}, "draft_id": {"$ref": "#/$defs/id"}, "evidence_refs": {"$ref": "#/$defs/strings"}, "operations": {"items": {"oneOf": [{"$ref": "#/$defs/beam"}, {"$ref": "#/$defs/column"}]}, "minItems": 1, "type": "array"}, "postconditions": {"$ref": "#/$defs/strings"}, "preconditions": {"$ref": "#/$defs/strings"}, "schema_version": {"const": "text2ifc/ifc-repair-changeset-draft/0.3"}, "scope": {"$ref": "#/$defs/scope"}, "semantic_manifest_ref": {"minLength": 1, "type": "string"}, "semantic_manifest_sha256": {"$ref": "#/$defs/hash"}, "semantic_summary": {"additionalProperties": false, "properties": {"conditional": {"minimum": 0, "type": "integer"}, "not_required": {"minimum": 0, "type": "integer"}, "required": {"minimum": 0, "type": "integer"}}, "required": ["required", "conditional", "not_required"], "type": "object"}, "source_request_hash": {"$ref": "#/$defs/hash"}}, "required": ["schema_version", "draft_id", "base_model_fingerprint", "source_request_hash", "semantic_manifest_ref", "semantic_manifest_sha256", "semantic_summary", "scope", "evidence_refs", "preconditions", "postconditions", "operations"], "title": "Provider Beam and Column IFC Repair ChangeSet Draft 0.3", "type": "object"}

## Previous validation feedback

[]

Rules:

1. Copy all resolved identifiers, parameters, scope, evidence, and hashes.
2. You receive only expanded operation-local semantic summaries.
3. Never request or emit raw cohort candidates, private Ground Truth,
   benchmark Gold, mutation mappings, or hidden original values.
4. Never emit semantic assignments or choose their source. The deterministic
   binder exclusively emits the five authorized source kinds.
5. Do not search targets/prototypes or emit STEP and low-level IFC objects.
6. Return JSON only.
7. Only the selected profiles appear below. A few-shot is structural guidance,
   never authority for project identity, dimensions, Type, or property values.
