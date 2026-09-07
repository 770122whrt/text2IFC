# IFC Repair ChangeSet Draft Generator 0.5

Return exactly one JSON draft conforming to `CHANGESET_SCHEMA`. Deterministic
code, not the Provider, binds and authors semantic assignments.

## Public request

在标高7恢复一根缺失的水平直线矩形梁，中心轴从 (-3316.629521, -3863.522838, -285) mm 到 (-3316.629521, -8803.522838, -285) mm，截面宽 455 mm、高 570 mm，并精确复用 GlobalId 为 17tPjyQtf2L9JnbXXmcTTd、名称为 S_支撑梁-1-ZC1 700x800 C30 的现有 IfcBeamType；同时精确复用现有 IfcMaterial `C_钢筋砼C30` 作为这根恢复梁的 occurrence-level Material，并将新恢复梁的表面颜色设为 RGB=(0.92, 0.12, 0.18)。


## Immutable bindings

- source request: sha256:447c486fcb61361c50a8202a90f6736fe2fe5bdd66f29ee173c3263af8efe6d3
- model: sha256:a611a682c79a79ace18a16bf5f1497bf32fe43a9447b92af22168149b36d20e4
- semantic manifest ref: changeset/semantic-manifest-restore-beam-1.json
- semantic manifest hash: sha256:f6d31fbd7e324cb16ed78f8f5b684e86153c960d217761abaa233f7d5dacc7d3

## Resolved operation projection

{"evidence_refs": ["resolved:/operations/restore-beam-1/context/candidate_targets/0"], "operations": [{"appearance": {"blue": 0.18, "green": 0.12, "intent_kind": "surface_color_rgb", "red": 0.92}, "evidence_refs": ["resolved:/operations/restore-beam-1/context/candidate_targets/0"], "operation_id": "restore-beam-1", "operation_type": "add_beam", "parameters": {"axis": {"end": {"x_mm": -3316.629521, "y_mm": -8803.522838, "z_mm": -285.0}, "start": {"x_mm": -3316.629521, "y_mm": -3863.522838, "z_mm": -285.0}}, "section": {"height_mm": 570, "shape": "rectangle", "width_mm": 455}}, "target": {"storey_global_id": "1vTeahUkP60PdWqwCTjUuM"}}], "scope": {"forbidden_ids": [], "target_ids": ["1vTeahUkP60PdWqwCTjUuM"]}}

The entire `RESOLVED_OPERATIONS` object is the canonical envelope authority.
Copy its `scope`, `evidence_refs`, and every operation exactly. Preserve every
list order shown there; do not reconstruct or sort any union yourself.

## Semantic group counts

{"conditional": 11, "not_required": 0, "required": 2}

## Explicit user slot references

["material:C_-C30"]

## Selected operation contracts, profiles, and sentinel few-shots

{"few_shots": [{"case": "complete", "example_id": "beam.add.stage2.v0.1.complete", "expected": {"evidence_refs": ["resolved:/operations/beam-example-1/context/candidate_targets/0"], "operation_id": "beam-example-1", "operation_type": "add_beam", "parameters": {"axis": {"end": {"x_mm": 5000, "y_mm": 0, "z_mm": 3000}, "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000}}, "section": {"height_mm": 500, "shape": "rectangle", "width_mm": 300}}, "target": {"storey_global_id": "EXAMPLE-STOREY-BEAM"}}, "output_schema": "text2ifc/ifc-repair-stage2-operation/0.1", "profile_id": "beam.add.stage2.v0.1", "rule": "Copy the deterministic resolved operation exactly; Stage 2 does not emit intent, Type, property, status, clarification, or unsupported-result fields.", "schema_version": "text2ifc/ifc-repair-stage2-few-shot/0.1", "sentinel": "EXAMPLE_ONLY"}], "operation_contracts": [{"operation_type": "add_beam", "parameter_schema": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"end": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}, "start": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}}, "required": ["start", "end"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"height_mm": {"exclusiveMinimum": 0, "type": "number"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "height_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "postcondition_names": ["beam_geometry_matches", "beam_contained_in_storey", "beam_type_bound"], "precondition_names": ["target_exists", "structural_axis_available", "structural_type_authorized"], "target_ifc_classes": ["IfcBuildingStorey"], "target_schema": {"additionalProperties": false, "properties": {"storey_global_id": {"minLength": 1, "type": "string"}}, "required": ["storey_global_id"], "type": "object"}}], "selected_profiles": [{"action": "add", "component_family": "beam", "draft_responsibility": "Copy the deterministic resolved target, geometry parameters, and evidence references into the Draft operation exactly. Consumed upstream authority is not recreated or reinterpreted.", "few_shot_output_schema": "text2ifc/ifc-repair-stage2-operation/0.1", "few_shots": [{"example_id": "beam.add.stage2.v0.1.complete", "path": "prompts/agent/ifc-repair-few-shots/beam-add-stage2-v0.1-complete.json", "sha256": "sha256:0cfebe0759f75b33346f86c01e580f387f5bb12549e55d32692f9d6187433e39"}], "operation_type": "add_beam", "profile_hash": "sha256:6281a88273c828c8e52057652c6f91982e7d03975a93e79e2f2629e68675ad4b", "profile_id": "beam.add.stage2.v0.1", "profile_version": "0.1", "schema_version": "text2ifc/ifc-repair-prompt-profile/0.3", "stage": "stage2", "stage2_projection_fields": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "target_ifc_classes": ["IfcBuildingStorey"]}]}

## Draft schema

{"$defs": {"beam": {"additionalProperties": false, "properties": {"appearance": {"oneOf": [{"type": "null"}, {"additionalProperties": false, "properties": {"blue": {"maximum": 1, "minimum": 0, "type": "number"}, "green": {"maximum": 1, "minimum": 0, "type": "number"}, "intent_kind": {"const": "surface_color_rgb"}, "red": {"maximum": 1, "minimum": 0, "type": "number"}}, "required": ["intent_kind", "red", "green", "blue"], "type": "object"}]}, "evidence_refs": {"$ref": "#/$defs/strings"}, "operation_id": {"$ref": "#/$defs/id"}, "operation_type": {"const": "add_beam"}, "parameters": {"$ref": "#/$defs/beamParameters"}, "target": {"$ref": "#/$defs/target"}}, "required": ["operation_id", "operation_type", "target", "parameters", "evidence_refs", "appearance"], "type": "object"}, "beamParameters": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"end": {"$ref": "#/$defs/point"}, "start": {"$ref": "#/$defs/point"}}, "required": ["start", "end"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"height_mm": {"exclusiveMinimum": 0, "type": "number"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "height_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "column": {"additionalProperties": false, "properties": {"appearance": {"oneOf": [{"type": "null"}, {"additionalProperties": false, "properties": {"blue": {"maximum": 1, "minimum": 0, "type": "number"}, "green": {"maximum": 1, "minimum": 0, "type": "number"}, "intent_kind": {"const": "surface_color_rgb"}, "red": {"maximum": 1, "minimum": 0, "type": "number"}}, "required": ["intent_kind", "red", "green", "blue"], "type": "object"}]}, "evidence_refs": {"$ref": "#/$defs/strings"}, "operation_id": {"$ref": "#/$defs/id"}, "operation_type": {"const": "add_column"}, "parameters": {"$ref": "#/$defs/columnParameters"}, "target": {"$ref": "#/$defs/target"}}, "required": ["operation_id", "operation_type", "target", "parameters", "evidence_refs", "appearance"], "type": "object"}, "columnParameters": {"additionalProperties": false, "properties": {"axis": {"additionalProperties": false, "properties": {"base": {"$ref": "#/$defs/point"}, "top": {"$ref": "#/$defs/point"}}, "required": ["base", "top"], "type": "object"}, "section": {"additionalProperties": false, "properties": {"depth_mm": {"exclusiveMinimum": 0, "type": "number"}, "orientation": {"additionalProperties": false, "properties": {"x": {"type": "number"}, "y": {"type": "number"}}, "required": ["x", "y"], "type": "object"}, "shape": {"const": "rectangle"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["shape", "width_mm", "depth_mm"], "type": "object"}}, "required": ["axis", "section"], "type": "object"}, "hash": {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}, "id": {"minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]*$", "type": "string"}, "point": {"additionalProperties": false, "properties": {"x_mm": {"type": "number"}, "y_mm": {"type": "number"}, "z_mm": {"type": "number"}}, "required": ["x_mm", "y_mm", "z_mm"], "type": "object"}, "scope": {"additionalProperties": false, "properties": {"forbidden_ids": {"$ref": "#/$defs/strings"}, "target_ids": {"$ref": "#/$defs/strings"}}, "required": ["target_ids", "forbidden_ids"], "type": "object"}, "strings": {"items": {"minLength": 1, "type": "string"}, "type": "array", "uniqueItems": true}, "target": {"additionalProperties": false, "properties": {"storey_global_id": {"minLength": 1, "type": "string"}}, "required": ["storey_global_id"], "type": "object"}}, "$id": "text2ifc/ifc-repair-changeset-draft/0.4", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"base_model_fingerprint": {"$ref": "#/$defs/hash"}, "draft_id": {"$ref": "#/$defs/id"}, "evidence_refs": {"$ref": "#/$defs/strings"}, "operations": {"items": {"oneOf": [{"$ref": "#/$defs/beam"}, {"$ref": "#/$defs/column"}]}, "minItems": 1, "type": "array"}, "postconditions": {"$ref": "#/$defs/strings"}, "preconditions": {"$ref": "#/$defs/strings"}, "schema_version": {"const": "text2ifc/ifc-repair-changeset-draft/0.4"}, "scope": {"$ref": "#/$defs/scope"}, "semantic_manifest_ref": {"minLength": 1, "type": "string"}, "semantic_manifest_sha256": {"$ref": "#/$defs/hash"}, "semantic_summary": {"additionalProperties": false, "properties": {"conditional": {"minimum": 0, "type": "integer"}, "not_required": {"minimum": 0, "type": "integer"}, "required": {"minimum": 0, "type": "integer"}}, "required": ["required", "conditional", "not_required"], "type": "object"}, "source_request_hash": {"$ref": "#/$defs/hash"}}, "required": ["schema_version", "draft_id", "base_model_fingerprint", "source_request_hash", "semantic_manifest_ref", "semantic_manifest_sha256", "semantic_summary", "scope", "evidence_refs", "preconditions", "postconditions", "operations"], "title": "Provider Structural IFC Repair ChangeSet Draft 0.4 with Appearance", "type": "object"}

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
