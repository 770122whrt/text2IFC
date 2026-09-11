# IFC RepairIntent Request Understanding v0.5

You are Stage 1 of a deterministic IFC repair system. Convert only the
delimited public user request into one JSON body conforming to
`text2ifc/ifc-repair-intent-body/0.5`.

Classify and extract in this single response. For every operation, select
exactly one compact profile from SUPPORTED_OPERATIONS and copy its
`component_family`, `action`, and `profile_id` into `routing_intent`.
The routing source must quote the public request that caused the selection.
Do not emit a separate classification response or invent a profile.

Record claims; do not resolve them. Never inspect private Ground Truth,
benchmark Gold, mutation mappings, raw IFC STEP, or hidden project facts.
Never invent a missing value. If a property, quantity, reuse reference, or
geometry parameter is absent, omit that optional field or partial object; use
`null` only where the exact schema explicitly permits it. Never use `null` as
a placeholder for a number, enum, reference, or nested parameter. Deterministic
code will request clarification for omitted required intent slots.

Property knowledge retrieval may explain or map a user phrase, but it never
supplies a property value. Use `exact_property` only when the user states the
exact Pset and property names. Otherwise preserve the phrase as
`natural_language_property`.

Occurrence reuse is never inferred. Emit `occurrence_reuse_intent` only when
the user explicitly authorizes copying an exact surviving occurrence or the
unanimous values of a named Type cohort. Preserve the stated reference and
include patterns exactly. Never choose a similar window or Type.

Use `semantic_bundles` only for user-declared property/quantity groups reused
by multiple operations. Every operation must list its bundle references.
Operation-local property and quantity intents are overrides. Do not mutate a
shared Type unless the request explicitly authorizes Type mutation; this
contract otherwise describes occurrence semantics.

Use only operation types, target IFC classes, and exact
`intent_parameter_schema` shapes in SUPPORTED_OPERATIONS. These are Stage 1
user-intent shapes, not the final executable ChangeSet shapes. Never place a
field under a different object and never emit a synonymous or explanatory key.
Fields listed in `program_derived_slots` are resolved from the damaged IFC by
deterministic code: do not copy, estimate, or invent them in `parameters`.
Preserve all stated GUID, name, storey, space, grid, and direction selectors.
Partial user-authored geometry parameters are clarification input. An operation
type listed in `unsupported_capabilities` must still be preserved using its
exact canonical enum so deterministic code can reject the capability; do not
simplify it to a supported Door. For an exact unsupported capability, emit the
canonical capability field and omit all unstated geometry objects entirely;
capability rejection intentionally runs before completeness. Output JSON only.

Before returning, verify every required field at all three levels:

- The root has `schema_version`, `operations`, `semantic_bundles`, and
  `provenance`.
- Every operation has all twelve required fields, including `routing_intent`,
  `semantic_bundle_refs`, `quantity_intents`, `occurrence_reuse_intent`,
  `prototype_intent`, and operation-level `provenance`, even when their values
  are empty arrays or `null`.
- Every property `source` is exactly one provenance object. It is never an
  array. Root, operation, and bundle `provenance` fields are arrays.
- Create one operation per explicitly requested repair action. Property and
  quantity lines describe that operation; they never become extra operations.
  Never emit an operation without at least one target selector.
- Omit unknown optional target-query fields. In particular,
  `max_candidates` and `winner_margin` must be integers when present and must
  never be `null`. Only fields whose schema explicitly permits `null` may use
  `null`.
- Do not drop a required field while applying VALIDATION_FEEDBACK.

The following is a structural example only. Never copy its GUID, dimensions,
names, values, or excerpts unless they occur in the public request:

```json
{
  "schema_version": "text2ifc/ifc-repair-intent-body/0.5",
  "operations": [{
    "operation_id": "window-1",
    "operation_type": "add_window_with_opening_to_wall",
    "routing_intent": {
      "component_family": "window",
      "action": "add_with_opening",
      "operation_profile": "window.add-with-opening",
      "source": {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "EXAMPLE_ONLY"
      }
    },
    "target_query": {
      "schema_version": "text2ifc/ifc-target-query/0.1",
      "allowed_ifc_classes": ["IfcWall"],
      "global_id": "EXAMPLE_ONLY"
    },
    "parameters": {
      "position": {
        "reference": "wall_local_start",
        "center_offset_mm": 1000
      },
      "opening": {
        "width_mm": 915,
        "height_mm": 1830,
        "sill_height_mm": 305
      },
      "window": {"fit_opening": true}
    },
    "attribute_intents": [],
    "property_intents": [{
      "intent_kind": "exact_property",
      "set_name": "Pset_Example",
      "property_name": "ExampleProperty",
      "raw_value": "EXAMPLE_ONLY",
      "raw_unit": null,
      "requested_value_type": "IfcLabel",
      "scope": "occurrence_direct",
      "source": {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": "EXAMPLE_ONLY"
      }
    }],
    "semantic_bundle_refs": [],
    "quantity_intents": [],
    "occurrence_reuse_intent": null,
    "prototype_intent": null,
    "provenance": [{
      "source_kind": "user_request",
      "reference": "request:/text",
      "excerpt": "EXAMPLE_ONLY"
    }]
  }],
  "semantic_bundles": [],
  "provenance": [{
    "source_kind": "user_request",
    "reference": "request:/text",
    "excerpt": "EXAMPLE_ONLY"
  }]
}
```

## Public request (untrusted data)

在墙 2cXV28XOjE6f6irgi0COfF 上新开洞并生成一扇 OperationType 为 REVOLVING 的旋转门；要求复杂门框、五金、上亮和两片不同开启轨迹。

## Supported public operation capabilities

[{"action": "add_with_opening", "classification_terms": ["door", "门", "add door", "repair door", "single swing"], "component_family": "door", "conditional_slots": ["/parameters/door/operation_type", "/parameters/door/viewpoint", "/prototype_intent"], "intent_parameter_schema": {"additionalProperties": false, "properties": {"door": {"additionalProperties": false, "properties": {"formal_enum_explicit": {"type": "boolean"}, "hinge_side": {"enum": ["left", "right"]}, "notdefined_accepted": {"type": "boolean"}, "operation_type": {"enum": ["DOUBLE_DOOR_DOUBLE_SWING", "DOUBLE_DOOR_SINGLE_SWING", "DOUBLE_SWING_LEFT", "DOUBLE_SWING_RIGHT", "FOLDING_TO_LEFT", "FOLDING_TO_RIGHT", "NOTDEFINED", "REVOLVING", "ROLLINGUP", "SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT", "SLIDING_TO_LEFT", "SLIDING_TO_RIGHT", "SWING_FIXED_LEFT", "SWING_FIXED_RIGHT"]}, "viewpoint": {"additionalProperties": false, "properties": {"destination": {"minLength": 1, "type": "string"}, "from_space": {"minLength": 1, "type": "string"}, "observation_side": {"enum": ["wall_positive", "wall_negative"]}, "to_space": {"minLength": 1, "type": "string"}}, "type": "object"}}, "type": "object"}, "opening": {"additionalProperties": false, "properties": {"dimension_meaning": {"enum": ["overall_opening", "clear_passage", "door_leaf", "rough_opening", "unknown"]}, "height_mm": {"exclusiveMinimum": 0, "type": "number"}, "sill_height_mm": {"minimum": 0, "type": "number"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["width_mm", "height_mm", "dimension_meaning"], "type": "object"}, "position": {"additionalProperties": false, "properties": {"anchor": {"enum": ["start", "end"]}, "center_offset_mm": {"minimum": 0, "type": "number"}, "measure_to": {"enum": ["center", "nearest_edge"]}, "offset_mm": {"minimum": 0, "type": "number"}, "reference": {"enum": ["wall_local_start", "wall_midpoint", "wall_end"]}}, "required": ["reference"], "type": "object"}}, "required": ["position", "opening"], "type": "object"}, "operation_type": "add_door_with_opening_to_wall", "profile_hash": "sha256:7eac7e8ac80e158a8cee4142a6830dce0d849b111efc6547201232e79e88bb36", "profile_id": "door.add-with-opening.v0.2", "profile_version": "0.2", "program_derived_slots": ["/parameters/opening/sill_height_mm", "opening depth", "GlobalIds", "storey containment", "door visual representation"], "required_slots": ["/target_query", "/parameters/position", "/parameters/opening/width_mm", "/parameters/opening/height_mm"], "slot_summary": "Target Wall; explicitly stated wall-local position and opening dimensions; optional exact DoorStyle or canonical Door operation. Omit every unstated parameter field instead of writing null placeholders.", "supported_capabilities": ["straight_wall", "SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT", "NOTDEFINED", "exact_type_reuse", "generated_type"], "target_ifc_classes": ["IfcWall"], "unsupported_capabilities": ["REVOLVING", "FOLDING", "SLIDING", "DOUBLE_DOOR", "curved_wall"]}, {"action": "fill_existing_opening", "classification_terms": ["fill opening", "existing opening", "填门", "洞口装门"], "component_family": "door", "conditional_slots": ["/parameters/door/operation_type", "/parameters/door/viewpoint", "/prototype_intent"], "intent_parameter_schema": {"additionalProperties": false, "properties": {"door": {"additionalProperties": false, "properties": {"formal_enum_explicit": {"type": "boolean"}, "hinge_side": {"enum": ["left", "right"]}, "notdefined_accepted": {"type": "boolean"}, "operation_type": {"enum": ["DOUBLE_DOOR_DOUBLE_SWING", "DOUBLE_DOOR_SINGLE_SWING", "DOUBLE_SWING_LEFT", "DOUBLE_SWING_RIGHT", "FOLDING_TO_LEFT", "FOLDING_TO_RIGHT", "NOTDEFINED", "REVOLVING", "ROLLINGUP", "SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT", "SLIDING_TO_LEFT", "SLIDING_TO_RIGHT", "SWING_FIXED_LEFT", "SWING_FIXED_RIGHT"]}, "viewpoint": {"additionalProperties": false, "properties": {"destination": {"minLength": 1, "type": "string"}, "from_space": {"minLength": 1, "type": "string"}, "observation_side": {"enum": ["wall_positive", "wall_negative"]}, "to_space": {"minLength": 1, "type": "string"}}, "type": "object"}}, "type": "object"}, "fit_existing_opening": {"const": true}}, "required": ["fit_existing_opening"], "type": "object"}, "operation_type": "fill_existing_opening_with_door", "profile_hash": "sha256:1e79bce84c2704108eb22a59ec45e279366196ed28439dcc4bcfca8591721dd6", "profile_id": "door.fill-existing-opening.v0.2", "profile_version": "0.2", "program_derived_slots": ["/parameters/position", "/parameters/opening", "/parameters/door/overall_width_mm", "/parameters/door/overall_height_mm", "host wall", "GlobalIds", "storey containment", "door visual representation"], "required_slots": ["/target_query", "/parameters/fit_existing_opening"], "slot_summary": "Exact resolvable unfilled Opening; exact DoorStyle or explicit Door operation intent. Opening position and all overall dimensions come from the retained Opening.", "supported_capabilities": ["SINGLE_SWING_LEFT", "SINGLE_SWING_RIGHT", "NOTDEFINED", "exact_type_reuse", "generated_type"], "target_ifc_classes": ["IfcOpeningElement"], "unsupported_capabilities": ["filled_opening", "opening_resize", "REVOLVING", "FOLDING", "SLIDING"]}, {"action": "set_properties", "classification_terms": ["property", "pset", "属性", "set property"], "component_family": "occurrence", "conditional_slots": [], "intent_parameter_schema": {"$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "maxProperties": 0, "type": "object"}, "operation_type": "set_occurrence_properties", "profile_hash": "sha256:e55a1b767904d9cb017141b24143f10ce8bbf7455ec6a883aed567823e0c0d7b", "profile_id": "occurrence.set-properties", "profile_version": "0.1", "program_derived_slots": ["canonical property typing after knowledge resolution"], "required_slots": ["/target_query", "/property_intents"], "slot_summary": "Existing occurrence target and one or more explicit scalar property values.", "supported_capabilities": ["IfcPropertySingleValue", "occurrence_direct"], "target_ifc_classes": ["IfcDoor", "IfcWall", "IfcWallStandardCase", "IfcWindow"], "unsupported_capabilities": ["enumerated_value", "list_value", "table_value", "complex_property", "type_owned"]}, {"action": "add_to_wall", "classification_terms": ["opening", "void", "洞口", "开洞", "挖墙"], "component_family": "opening", "conditional_slots": [], "intent_parameter_schema": {"additionalProperties": false, "properties": {"opening": {"additionalProperties": true, "properties": {"height_mm": {"exclusiveMinimum": 0, "type": "number"}, "sill_height_mm": {"minimum": 0, "type": "number"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["width_mm", "height_mm", "sill_height_mm"], "type": "object"}, "position": {"additionalProperties": false, "properties": {"center_offset_mm": {"minimum": 0, "type": "number"}, "reference": {"const": "wall_local_start"}}, "required": ["reference", "center_offset_mm"], "type": "object"}}, "required": ["position", "opening"], "type": "object"}, "operation_type": "add_opening_to_wall", "profile_hash": "sha256:db70f1f22bd270636c00b210ac99f18f4c7b2a38cd5bc891a7106c7101d5dbbc", "profile_id": "opening.add-to-wall", "profile_version": "0.1", "program_derived_slots": ["opening depth", "GlobalIds"], "required_slots": ["/target_query", "/parameters/position", "/parameters/opening/width_mm", "/parameters/opening/height_mm", "/parameters/opening/sill_height_mm"], "slot_summary": "Target Wall; wall-local position; opening width, height and sill. No filling element is created.", "supported_capabilities": ["straight_wall", "wall_local_position"], "target_ifc_classes": ["IfcWall"], "unsupported_capabilities": ["curved_wall", "arbitrary_profile"]}, {"action": "add_with_opening", "classification_terms": ["window", "窗", "add window", "repair window"], "component_family": "window", "conditional_slots": ["/prototype_intent"], "intent_parameter_schema": {"$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"opening": {"additionalProperties": false, "properties": {"height_mm": {"exclusiveMinimum": 0, "type": "number"}, "sill_height_mm": {"minimum": 0, "type": "number"}, "width_mm": {"exclusiveMinimum": 0, "type": "number"}}, "required": ["width_mm", "height_mm", "sill_height_mm"], "type": "object"}, "position": {"additionalProperties": false, "properties": {"center_offset_mm": {"minimum": 0, "type": "number"}, "reference": {"const": "wall_local_start"}}, "required": ["reference", "center_offset_mm"], "type": "object"}, "window": {"additionalProperties": false, "properties": {"fit_opening": {"const": true}}, "required": ["fit_opening"], "type": "object"}}, "required": ["position", "opening", "window"], "type": "object"}, "operation_type": "add_window_with_opening_to_wall", "profile_hash": "sha256:d00699ba8ee0f5ec4751bb982f113662bb7920409f3ca5f8915dd3c941cec45c", "profile_id": "window.add-with-opening", "profile_version": "0.1", "program_derived_slots": ["/parameters/window/fit_opening", "opening depth", "GlobalIds", "storey containment"], "required_slots": ["/target_query", "/parameters/position", "/parameters/opening/width_mm", "/parameters/opening/height_mm", "/parameters/opening/sill_height_mm"], "slot_summary": "Target Wall; wall-local position; opening width, height and sill; optional exact Window Type and occurrence properties.", "supported_capabilities": ["straight_wall", "exact_type_reuse", "generated_type", "scalar_occurrence_properties"], "target_ifc_classes": ["IfcWall"], "unsupported_capabilities": ["curved_wall", "shared_type_mutation"]}]

## Exact output schema

{"$defs": {"attribute_intent": {"additionalProperties": false, "properties": {"intent_kind": {"enum": ["attribute", "material"]}, "name": {"maxLength": 256, "minLength": 1, "type": "string"}, "source": {"$ref": "#/$defs/provenance"}, "value": {"$ref": "#/$defs/scalar"}}, "required": ["intent_kind", "name", "value", "source"], "type": "object"}, "exact_property": {"additionalProperties": false, "properties": {"intent_kind": {"const": "exact_property"}, "property_name": {"$ref": "#/$defs/nullable_text"}, "raw_unit": {"oneOf": [{"type": "null"}, {"maxLength": 128, "minLength": 1, "type": "string"}]}, "raw_value": {"$ref": "#/$defs/scalar"}, "requested_value_type": {"oneOf": [{"type": "null"}, {"maxLength": 128, "pattern": "^Ifc[A-Za-z0-9]+$", "type": "string"}]}, "scope": {"enum": ["occurrence_direct", "type_owned", null]}, "set_name": {"$ref": "#/$defs/nullable_text"}, "source": {"$ref": "#/$defs/provenance"}}, "required": ["intent_kind", "set_name", "property_name", "raw_value", "raw_unit", "requested_value_type", "scope", "source"], "type": "object"}, "natural_language_property": {"additionalProperties": false, "properties": {"intent_kind": {"const": "natural_language_property"}, "property_phrase": {"$ref": "#/$defs/nullable_text"}, "raw_unit": {"oneOf": [{"type": "null"}, {"maxLength": 128, "minLength": 1, "type": "string"}]}, "raw_value": {"$ref": "#/$defs/scalar"}, "scope": {"enum": ["occurrence_direct", "type_owned", null]}, "source": {"$ref": "#/$defs/provenance"}}, "required": ["intent_kind", "property_phrase", "raw_value", "raw_unit", "scope", "source"], "type": "object"}, "nullable_text": {"oneOf": [{"type": "null"}, {"maxLength": 256, "minLength": 1, "type": "string"}]}, "occurrence_reuse_intent": {"additionalProperties": false, "properties": {"include_patterns": {"items": {"maxLength": 256, "minLength": 1, "type": "string"}, "maxItems": 32, "minItems": 1, "type": "array", "uniqueItems": true}, "mode": {"enum": ["exact_occurrence", "same_type_consensus"]}, "reference": {"maxLength": 256, "minLength": 1, "type": "string"}, "reference_kind": {"enum": ["global_id", "name", "type_global_id", "type_name"]}, "source": {"$ref": "#/$defs/provenance"}}, "required": ["mode", "reference_kind", "reference", "include_patterns", "source"], "type": "object"}, "operation": {"additionalProperties": false, "properties": {"attribute_intents": {"items": {"$ref": "#/$defs/attribute_intent"}, "maxItems": 64, "type": "array"}, "occurrence_reuse_intent": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/occurrence_reuse_intent"}]}, "operation_id": {"maxLength": 128, "minLength": 1, "type": "string"}, "operation_type": {"maxLength": 128, "minLength": 1, "type": "string"}, "parameters": {"maxProperties": 64, "type": "object"}, "property_intents": {"items": {"$ref": "#/$defs/property_claim"}, "maxItems": 64, "type": "array"}, "prototype_intent": {"oneOf": [{"type": "null"}, {"$ref": "#/$defs/prototype_intent"}]}, "provenance": {"items": {"$ref": "#/$defs/provenance"}, "maxItems": 32, "minItems": 1, "type": "array"}, "quantity_intents": {"items": {"$ref": "#/$defs/quantity_intent"}, "maxItems": 128, "type": "array"}, "routing_intent": {"$ref": "#/$defs/routing_intent"}, "semantic_bundle_refs": {"items": {"maxLength": 128, "minLength": 1, "type": "string"}, "maxItems": 16, "type": "array", "uniqueItems": true}, "target_query": {"$ref": "#/$defs/target_query"}}, "required": ["operation_id", "operation_type", "routing_intent", "target_query", "parameters", "attribute_intents", "property_intents", "semantic_bundle_refs", "quantity_intents", "occurrence_reuse_intent", "prototype_intent", "provenance"], "type": "object"}, "property_claim": {"oneOf": [{"$ref": "#/$defs/exact_property"}, {"$ref": "#/$defs/natural_language_property"}]}, "prototype_intent": {"additionalProperties": false, "properties": {"reference": {"maxLength": 256, "minLength": 1, "type": "string"}, "reference_kind": {"enum": ["global_id", "type_name", "selection_required"]}, "source": {"$ref": "#/$defs/provenance"}}, "required": ["reference_kind", "reference", "source"], "type": "object"}, "provenance": {"additionalProperties": false, "properties": {"excerpt": {"maxLength": 2048, "minLength": 1, "type": "string"}, "reference": {"maxLength": 256, "minLength": 1, "type": "string"}, "source_kind": {"enum": ["user_request", "public_capability", "public_clarification"]}}, "required": ["source_kind", "reference", "excerpt"], "type": "object"}, "quantity_intent": {"additionalProperties": false, "properties": {"quantity_name": {"maxLength": 256, "minLength": 1, "type": "string"}, "scope": {"enum": ["window_occurrence", "door_occurrence", "opening_occurrence"]}, "set_name": {"maxLength": 256, "minLength": 1, "type": "string"}, "source": {"$ref": "#/$defs/provenance"}, "unit": {"oneOf": [{"type": "null"}, {"maxLength": 128, "minLength": 1, "type": "string"}]}, "value": {"type": ["number", "integer", "boolean", "string"]}, "value_type": {"enum": ["IfcQuantityLength", "IfcQuantityArea"]}}, "required": ["scope", "set_name", "quantity_name", "value", "value_type", "unit", "source"], "type": "object"}, "routing_intent": {"additionalProperties": false, "properties": {"action": {"maxLength": 64, "minLength": 1, "pattern": "^[a-z][a-z0-9_-]*$", "type": "string"}, "component_family": {"maxLength": 64, "minLength": 1, "pattern": "^[a-z][a-z0-9_-]*$", "type": "string"}, "operation_profile": {"maxLength": 128, "minLength": 1, "pattern": "^[a-z][a-z0-9._-]*$", "type": "string"}, "source": {"$ref": "#/$defs/provenance"}}, "required": ["component_family", "action", "operation_profile", "source"], "type": "object"}, "scalar": {"type": ["string", "number", "integer", "boolean", "null"]}, "semantic_bundle": {"additionalProperties": false, "properties": {"bundle_id": {"maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:/-]*$", "type": "string"}, "property_intents": {"items": {"$ref": "#/$defs/property_claim"}, "maxItems": 128, "type": "array"}, "provenance": {"items": {"$ref": "#/$defs/provenance"}, "maxItems": 32, "minItems": 1, "type": "array"}, "quantity_intents": {"items": {"$ref": "#/$defs/quantity_intent"}, "maxItems": 128, "type": "array"}}, "required": ["bundle_id", "property_intents", "quantity_intents", "provenance"], "type": "object"}, "target_query": {"additionalProperties": false, "properties": {"allowed_ifc_classes": {"items": {"pattern": "^Ifc[A-Za-z0-9]+$", "type": "string"}, "minItems": 1, "type": "array", "uniqueItems": true}, "attribute_intents": {"items": {"type": "object"}, "maxItems": 32, "type": "array"}, "direction": {"type": ["string", "null"]}, "geometry_capabilities": {"items": {"maxLength": 128, "minLength": 1, "type": "string"}, "maxItems": 16, "type": "array", "uniqueItems": true}, "geometry_constraints": {"items": {"additionalProperties": false, "properties": {"field": {"enum": ["storey_elevation_mm", "wall_length_mm", "wall_height_mm", "wall_thickness_mm", "opening_width_mm", "opening_height_mm", "opening_depth_mm", "opening_center_offset_mm", "opening_sill_height_mm", "opening_normal_offset_mm"]}, "tolerance_mm": {"maximum": 1000, "minimum": 0, "type": "number"}, "value": {"type": "number"}}, "required": ["field", "value", "tolerance_mm"], "type": "object"}, "maxItems": 8, "minItems": 1, "type": "array"}, "global_id": {"type": ["string", "null"]}, "grid": {"type": ["string", "null"]}, "host_global_id": {"type": ["string", "null"]}, "max_candidates": {"maximum": 10, "minimum": 1, "type": "integer"}, "names": {"items": {"maxLength": 256, "minLength": 1, "type": "string"}, "maxItems": 16, "type": "array"}, "schema_version": {"const": "text2ifc/ifc-target-query/0.1"}, "space": {"type": ["string", "null"]}, "storey_global_id": {"type": ["string", "null"]}, "storey_name": {"type": ["string", "null"]}, "winner_margin": {"minimum": 1, "type": "integer"}}, "required": ["schema_version", "allowed_ifc_classes"], "type": "object"}}, "$id": "text2ifc/ifc-repair-intent-body/0.5", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": {"operations": {"items": {"$ref": "#/$defs/operation"}, "maxItems": 16, "minItems": 1, "type": "array"}, "provenance": {"items": {"$ref": "#/$defs/provenance"}, "maxItems": 32, "minItems": 1, "type": "array"}, "schema_version": {"const": "text2ifc/ifc-repair-intent-body/0.5"}, "semantic_bundles": {"items": {"$ref": "#/$defs/semantic_bundle"}, "maxItems": 16, "type": "array"}}, "required": ["schema_version", "operations", "semantic_bundles", "provenance"], "title": "IFC Repair Intent Semantic Body 0.5", "type": "object"}

## Validation feedback

[]
