# IFC Repair ChangeSet Draft Generator 0.2

Return exactly one JSON object conforming to `CHANGESET_SCHEMA`. This output is
a non-executable draft. Deterministic code, not you, binds semantic assignments.

## Public request

请修复这个 IFC2X3 文件中墙体 2CsmzAChHF6O6maGXlo6PS 的实例属性关联。该墙的几何、Type、材料、颜色和其他对象均须保留。请按下述明确要求写入实例 Pset_WallCommon：Reference 为字符串 "240"，IsExternal 为布尔 true，ExtendToStructure 为布尔 false，LoadBearing 为布尔 false。上述属性值也可在输入 IFC 尚存的独立 Pset_WallCommon 属性集中核对；不要修改共享 Type，不要增加其他属性，也不要更改任何几何。请输出修复后的完整 IFC。


## Immutable bindings

- source request: sha256:78b31c7a44102d2d5d34a110d8417b4e8857a0d4f2ad97a1411609e334fbb598
- model: sha256:7fb29d1f19d1e10ae44c7af432d8d2aa74379ccb434f9344a34ed5e01b7766d6
- semantic manifest ref: changeset/semantic-manifest-restore-wall-properties.json
- semantic manifest hash: sha256:809ddb4373dfcce29cdeb0d72ad5e89755bfe0f471f8228ff5745335682c2710

## Resolved operation projection

{"evidence_refs": ["resolved:/operations/restore-wall-properties/context/candidate_targets/0"], "operations": [{"evidence_refs": ["resolved:/operations/restore-wall-properties/context/candidate_targets/0"], "operation_id": "restore-wall-properties", "operation_type": "set_occurrence_properties", "parameters": {}, "target": {"element_global_id": "2CsmzAChHF6O6maGXlo6PS"}}], "scope": {"forbidden_ids": [], "target_ids": ["2CsmzAChHF6O6maGXlo6PS"]}}

## Semantic group counts

{"conditional": 4, "not_required": 0, "required": 0}

## Explicit user slot references

["pset:Pset_WallCommon.ExtendToStructure", "pset:Pset_WallCommon.IsExternal", "pset:Pset_WallCommon.LoadBearing", "pset:Pset_WallCommon.Reference"]

## Registered operation contracts

{"few_shots": [], "operation_contracts": [{"capability_constraints": {"geometry_mutation": false, "ifc_schemas": ["IFC2X3"], "mutation_scope": "occurrence_only", "property_templates": ["IfcPropertySingleValue"], "semantic_authoring_scope": "explicit_request_only", "shared_type_mutation": false}, "operation_type": "set_occurrence_properties", "parameter_schema": {"$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "maxProperties": 0, "type": "object"}, "postcondition_names": ["target_preserved", "requested_properties_match", "shared_type_unchanged"], "precondition_names": ["target_exists", "target_class_supported", "property_assignments_bound"], "prototype_dimension_paths": {}, "prototype_ifc_classes": [], "target_ifc_classes": ["IfcBeam", "IfcColumn", "IfcDoor", "IfcWall", "IfcWallStandardCase", "IfcWindow"], "target_schema": {"$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"element_global_id": {"minLength": 1, "type": "string"}}, "required": ["element_global_id"], "type": "object"}}], "selected_profiles": [{"action": "set_properties", "classification_terms": ["property", "pset", "属性", "set property"], "component_family": "occurrence", "conditional_slots": [], "few_shots": [], "forbidden_inferences": ["property value", "shared Type mutation", "custom property confirmation"], "operation_type": "set_occurrence_properties", "optional_slots": [], "profile_hash": "sha256:7b95c00e8f19ff4990053698c42dd182e385931260a2929d0edecbd19dbbec2b", "profile_id": "occurrence.set-properties", "profile_version": "0.1", "program_derived_slots": ["canonical property typing after knowledge resolution"], "required_slots": ["/target_query", "/property_intents"], "schema_version": "text2ifc/ifc-repair-prompt-profile/0.1", "slot_summary": "Existing occurrence target and one or more explicit scalar property values.", "stage2_projection_fields": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "supported_capabilities": ["IfcPropertySingleValue", "occurrence_direct"], "target_ifc_classes": ["IfcBeam", "IfcColumn", "IfcDoor", "IfcWall", "IfcWallStandardCase", "IfcWindow"], "unsupported_capabilities": ["enumerated_value", "list_value", "table_value", "complex_property", "type_owned"]}]}

## Draft schema

{"$defs": {"hash": {"pattern": "^sha256:[0-9a-f]{64}$", "type": "string"}, "id": {"minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]*$", "type": "string"}, "operation": {"additionalProperties": false, "properties": {"evidence_refs": {"$ref": "#/$defs/strings"}, "operation_id": {"$ref": "#/$defs/id"}, "operation_type": {"$ref": "#/$defs/id"}, "parameters": {"type": "object"}, "target": {"minProperties": 1, "type": "object"}}, "required": ["operation_id", "operation_type", "target", "parameters", "evidence_refs"], "type": "object"}, "scope": {"additionalProperties": false, "properties": {"forbidden_ids": {"$ref": "#/$defs/strings"}, "target_ids": {"$ref": "#/$defs/strings"}}, "required": ["target_ids", "forbidden_ids"], "type": "object"}, "strings": {"items": {"minLength": 1, "type": "string"}, "type": "array", "uniqueItems": true}}, "$id": "text2ifc/ifc-repair-changeset-draft/0.2", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"base_model_fingerprint": {"$ref": "#/$defs/hash"}, "draft_id": {"$ref": "#/$defs/id"}, "evidence_refs": {"$ref": "#/$defs/strings"}, "operations": {"items": {"$ref": "#/$defs/operation"}, "minItems": 1, "type": "array"}, "postconditions": {"$ref": "#/$defs/strings"}, "preconditions": {"$ref": "#/$defs/strings"}, "schema_version": {"const": "text2ifc/ifc-repair-changeset-draft/0.2"}, "scope": {"$ref": "#/$defs/scope"}, "semantic_manifest_ref": {"minLength": 1, "type": "string"}, "semantic_manifest_sha256": {"$ref": "#/$defs/hash"}, "semantic_summary": {"additionalProperties": false, "properties": {"conditional": {"minimum": 0, "type": "integer"}, "not_required": {"minimum": 0, "type": "integer"}, "required": {"minimum": 0, "type": "integer"}}, "required": ["required", "conditional", "not_required"], "type": "object"}, "source_request_hash": {"$ref": "#/$defs/hash"}}, "required": ["schema_version", "draft_id", "base_model_fingerprint", "source_request_hash", "semantic_manifest_ref", "semantic_manifest_sha256", "semantic_summary", "scope", "evidence_refs", "preconditions", "postconditions", "operations"], "title": "Provider IFC Repair ChangeSet Draft 0.2", "type": "object"}

## Previous validation feedback

[]

Rules:

1. Copy operation IDs, types, targets, parameters, scope, and evidence exactly.
2. Echo all hashes and the manifest reference exactly.
3. Do not emit semantic assignments, Pset values, material/classification
   resource payloads, Type facts, STEP IDs/text, or low-level IFC objects.
4. Do not search, select a prototype, authorize facts, or add custom slots.
5. Return JSON only. The draft cannot be applied until deterministic binding.

## Single-operation shape

Use the exact draft schema above; one operation remains a one-item array.

## Multiple-operation shape

Use the same envelope; include each resolved operation once without merging.
