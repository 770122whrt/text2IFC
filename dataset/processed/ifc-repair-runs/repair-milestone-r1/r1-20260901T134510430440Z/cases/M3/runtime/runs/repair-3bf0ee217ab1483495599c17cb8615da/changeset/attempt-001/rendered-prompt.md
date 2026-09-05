# IFC Repair ChangeSet Draft Generator 0.5

Return exactly one JSON draft conforming to `CHANGESET_SCHEMA`. Deterministic
code, not the Provider, binds and authors semantic assignments.

## Public request

在 00 begane grond 添加一根新的竖直矩形柱，中心轴底点为 (25000, 60000, 0) mm，顶点为 (25000, 60000, 3000) mm，截面宽 400 mm、深 600 mm，局部宽度方向为 (1, 0)。为它创建独立的 Column Type，并将其设置为承重构件。

## Immutable bindings

- source request: sha256:1abb29da38d8c29e15936a31249389bfbcb122a3e27a1da34e309a70809f0837
- model: sha256:79f294c643438ac7a494e4871857244c2de0eefa536eda5977af20640a301a22
- semantic manifest ref: changeset/semantic-manifest-add-column-1.json
- semantic manifest hash: sha256:a1e71fb369c4f9698085186396faebf65e4be97f176cec914fcd618da5a4bcb8

## Resolved operation projection

{"evidence_refs": ["resolved:/operations/add-column-1/context/candidate_targets/0"], "operations": [{"evidence_refs": ["resolved:/operations/add-column-1/context/candidate_targets/0"], "operation_id": "add-column-1", "operation_type": "add_column", "parameters": {"axis": {"base": {"x_mm": 25000.0, "y_mm": 60000.0, "z_mm": 0.0}, "top": {"x_mm": 25000.0, "y_mm": 60000.0, "z_mm": 3000.0}}, "section": {"depth_mm": 600, "orientation": {"x": 1, "y": 0}, "shape": "rectangle", "width_mm": 400}}, "target": {"storey_global_id": "02GkOQJZz4x9WAhoZkM67S"}}], "scope": {"forbidden_ids": [], "target_ids": ["02GkOQJZz4x9WAhoZkM67S"]}}

The entire `RESOLVED_OPERATIONS` object is the canonical envelope authority.
Copy its `scope`, `evidence_refs`, and every operation exactly. Preserve every
list order shown there; do not reconstruct or sort any union yourself.

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
