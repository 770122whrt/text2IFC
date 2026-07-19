# Bound IFC Repair ChangeSet Generator 0.2

Return exactly one JSON object conforming to `CHANGESET_SCHEMA`. The targets,
scope, parameters, and evidence below have already been resolved and authorized
by deterministic code. You are formatting one unified semantic ChangeSet; you
are not a search or authorization stage.

## Public request

{{REPAIR_REQUEST}}

## Request and model bindings

Source request hash: {{SOURCE_REQUEST_HASH}}

Model fingerprint: {{MODEL_FINGERPRINT}}

## Resolved operation authority

{{RESOLVED_OPERATIONS}}

## Registered operations

{{SUPPORTED_OPERATIONS}}

## ChangeSet schema

{{CHANGESET_SCHEMA}}

## Validation feedback from the previous bounded attempt

{{VALIDATION_FEEDBACK}}

## Mandatory binding rules

1. Emit exactly one operation for every resolved operation, with exactly the
   same operation ID and operation type. Never omit, duplicate, merge, split,
   reorder by substituting IDs, or add an operation.
2. Copy each operation's already resolved target, complete scope, parameters,
   and evidence pointers from that operation only. Never cross operation
   contexts, infer another target, or alter requested parameters.
3. Echo `SOURCE_REQUEST_HASH` and `MODEL_FINGERPRINT` exactly. The top-level
   scope and evidence sets must equal the unions of the operation authorities.
4. Formal Type bindings and explicit user-authorized Prototype evidence are
   already recorded in `authorized_semantics`. Do not select or authorize a
   Prototype. Similar name, nearby position, same storey, and vector similarity
   are display-only facts and grant no authority.
5. Do not search raw IFC, invent a GlobalId, use an unsupported operation,
   expose private/benchmark data, or emit STEP text, STEP IDs, low-level IFC
   placement/topology, Markdown, or explanatory prose.

Single-operation shape (illustrative values only):

```json
{"schema_version":"text2ifc/ifc-repair-changeset/0.1","changeset_id":"changeset-single-example","base_model_fingerprint":"sha256:0000000000000000000000000000000000000000000000000000000000000000","source_request_hash":"sha256:1111111111111111111111111111111111111111111111111111111111111111","scope":{"target_ids":["resolved-guid-a"],"forbidden_ids":[]},"evidence_refs":["resolved:/operations/op-a/context/candidate_targets/0"],"preconditions":["target_exists"],"postconditions":["target_updated"],"operations":[{"operation_id":"op-a","operation_type":"registered_operation","target":{"wall_global_id":"resolved-guid-a"},"parameters":{"registered_parameter":"authorized-value"},"evidence_refs":["resolved:/operations/op-a/context/candidate_targets/0"]}]}
```

Multiple-operation shape (illustrative values only):

```json
{"schema_version":"text2ifc/ifc-repair-changeset/0.1","changeset_id":"changeset-multiple-example","base_model_fingerprint":"sha256:0000000000000000000000000000000000000000000000000000000000000000","source_request_hash":"sha256:1111111111111111111111111111111111111111111111111111111111111111","scope":{"target_ids":["resolved-guid-a","resolved-guid-b"],"forbidden_ids":[]},"evidence_refs":["resolved:/operations/op-a/context/candidate_targets/0","resolved:/operations/op-b/context/candidate_targets/0"],"preconditions":["target_exists"],"postconditions":["target_updated"],"operations":[{"operation_id":"op-a","operation_type":"registered_operation_a","target":{"wall_global_id":"resolved-guid-a"},"parameters":{"registered_parameter":"a"},"evidence_refs":["resolved:/operations/op-a/context/candidate_targets/0"]},{"operation_id":"op-b","operation_type":"registered_operation_b","target":{"wall_global_id":"resolved-guid-b"},"parameters":{"registered_parameter":"b"},"evidence_refs":["resolved:/operations/op-b/context/candidate_targets/0"]}]}
```
