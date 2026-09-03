"""Provider-backed generation of one public semantic IFC repair ChangeSet."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import (
    ProviderOutputError,
    redact_provider_payload,
    validate_provider_output,
)
from text2ifc_text.splits import atomic_write_text

from .changesets import (
    BOUND_CHANGESET_SCHEMA_VERSION_0_3,
    BOUND_CHANGESET_SCHEMA_VERSION_0_4,
    BOUND_CHANGESET_SCHEMA_VERSION_0_5,
    DRAFT_CHANGESET_SCHEMA_VERSION_0_3,
    bind_repair_changeset,
    load_changeset_draft_schema,
    load_changeset_schema,
    validate_changeset,
    validate_changeset_draft,
)
from .prompt_profiles import select_prompt_profiles
from .registry import OperationRegistry, OperationRegistryError


TEMPLATE_ID = "ifc-repair-changeset.v0.1"
BOUND_TEMPLATE_ID = "ifc-repair-changeset.v0.2"
BOUND_TEMPLATE_ID_0_3 = "ifc-repair-changeset.v0.3"
BOUND_TEMPLATE_ID_0_4 = "ifc-repair-changeset.v0.4"
BOUND_TEMPLATE_ID_0_5 = "ifc-repair-changeset.v0.5"
_PRIVATE_CANARIES = (
    "private_original",
    "mutation_manifest",
    "benchmark_gold",
    "iso-10303-21;",
)


def generate_bound_changeset(
    *,
    provider: Any,
    case_id: str,
    repair_request: str,
    source_request_hash: str,
    resolved_operations: Any,
    model_fingerprint: str,
    base_model_fingerprint: str | None = None,
    registry: OperationRegistry,
    output_dir: Path | str,
    max_attempts: int = 2,
    semantic_manifests: Any = (),
    semantic_manifest_hashes: Mapping[str, str] | None = None,
    semantic_manifest_ref: str = "semantic-manifest.json",
) -> dict[str, Any]:
    """Generate one ChangeSet from complete operation-scoped public authority."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if max_attempts not in (1, 2):
        raise ValueError("BOUND_CHANGESET_ATTEMPT_LIMIT_INVALID")
    operations = [_plain_operation(item) for item in resolved_operations]
    base_fingerprint = base_model_fingerprint or model_fingerprint
    input_issues, resolved_document = _resolved_input_issues(
        operations, model_fingerprint=model_fingerprint, registry=registry
    )
    if input_issues:
        result = _invalid_result(input_issues)
        atomic_write_text(output / "diagnostics.json", _json({"valid": False, "issues": input_issues}))
        return result

    used_operation_types = tuple(
        sorted({str(item["operation_type"]) for item in operations})
    )
    used_definitions = tuple(
        registry.require(name) for name in used_operation_types
    )
    manifests = tuple(semantic_manifests)
    structural_compact_mode = bool(manifests) and all(
        definition.stage2_prompt_profile_id for definition in used_definitions
    )
    supported_operations: Any = [
        (
            _stage2_operation_contract(registry, name)
            if structural_compact_mode
            else _operation_contract(registry, name)
        )
        for name in used_operation_types
    ]
    selected_profile_ids = []
    for name in used_operation_types:
        definition = registry.require(name)
        selected_profile_ids.append(
            definition.stage2_prompt_profile_id
            if structural_compact_mode
            else definition.prompt_profile_id
        )
    profile_selection = None
    if selected_profile_ids and all(selected_profile_ids):
        profile_selection = select_prompt_profiles(
            str(item) for item in selected_profile_ids
        )
        selection_document = profile_selection.to_dict()
        supported_operations = {
            "operation_contracts": supported_operations,
            "selected_profiles": selection_document["profiles"],
            "few_shots": selection_document["few_shots"],
        }
        atomic_write_text(
            output / "prompt-profile-selection.json",
            _json(selection_document),
        )
    manifest_hashes = dict(semantic_manifest_hashes or {})
    compact_mode = bool(manifests)
    manifest_versions = frozenset(item.schema_version for item in manifests)
    semantic_contract_v03 = (
        "text2ifc/ifc-repair-semantic-manifest/0.3" in manifest_versions
    )
    semantic_contract_v02 = (
        not semantic_contract_v03
        and "text2ifc/ifc-repair-semantic-manifest/0.2" in manifest_versions
    )
    mixed_semantic_contract = len(manifest_versions) > 1
    manifest_hash = (
        manifest_hashes.get(manifests[0].operation_id, "") if compact_mode else ""
    )
    provider_schema = (
        load_changeset_draft_schema(DRAFT_CHANGESET_SCHEMA_VERSION_0_3)
        if structural_compact_mode
        else load_changeset_draft_schema()
        if compact_mode
        else load_changeset_schema()
    )
    resolved_authority = (
        _structural_draft_authority(operations, registry=registry)
        if compact_mode
        else None
    )
    prompt_operations = (
        resolved_authority if compact_mode else resolved_document
    )
    semantic_summary = _semantic_summary(manifests)
    explicit_slot_refs = sorted(
        {
            assignment.source_fact_key
            for manifest in manifests
            for assignment in manifest.assignments
            if assignment.source_kind.value in {"explicit_request", "explicit_value"}
        }
    )
    feedback: list[dict[str, str]] = []
    last_result = _invalid_result([])
    for attempt_index in range(1, max_attempts + 1):
        attempt_dir = output / f"attempt-{attempt_index:03d}"
        attempt_dir.mkdir(parents=True, exist_ok=True)
        renderer_input = {
            "REPAIR_REQUEST": repair_request,
            "SOURCE_REQUEST_HASH": source_request_hash,
            "MODEL_FINGERPRINT": base_fingerprint,
            "RESOLVED_OPERATIONS": prompt_operations,
            "SUPPORTED_OPERATIONS": supported_operations,
            "CHANGESET_SCHEMA": provider_schema,
            "VALIDATION_FEEDBACK": feedback,
            "SEMANTIC_MANIFEST_REF": semantic_manifest_ref,
            "SEMANTIC_MANIFEST_SHA256": manifest_hash,
            "SEMANTIC_SUMMARY": semantic_summary,
            "EXPLICIT_REQUEST_SLOT_REFS": explicit_slot_refs,
        }
        rendered = render_prompt(
            template_id=(
                BOUND_TEMPLATE_ID_0_5
                if semantic_contract_v03
                else BOUND_TEMPLATE_ID_0_3
                if semantic_contract_v02
                else BOUND_TEMPLATE_ID
            ),
            inputs=renderer_input,
        )
        atomic_write_text(attempt_dir / "renderer-input.json", _json(renderer_input))
        atomic_write_text(attempt_dir / "rendered-prompt.md", rendered["text"])
        try:
            provider_output = _call_bound_provider(provider, {
                "session_id": f"ifc-repair-{case_id}",
                "prompt": rendered["text"],
                "schema": provider_schema,
                "state": {"case_id": case_id, "stage": "ifc_repair_bound_changeset", "attempt": attempt_index},
            }, attempt_dir)
        except ProviderOutputError:
            issues = [_issue("STEP_OR_PRIVATE_OUTPUT_FORBIDDEN", "/", "Provider output failed the public structured-output boundary")]
            atomic_write_text(
                attempt_dir / "diagnostics.json",
                _json({"schema_version": "text2ifc/ifc-repair-provider-stage/0.2", "valid": False, "parse_status": "rejected", "issues": issues}),
            )
            feedback = issues
            last_result = _invalid_result(issues, prompt=_prompt_identity(rendered))
            continue
        atomic_write_text(attempt_dir / "raw-response.txt", provider_output.text)
        atomic_write_text(
            attempt_dir / "provider-metadata.json",
            _json(redact_provider_payload(provider_output.metadata)),
        )
        parse_status, parsed, parse_issues = provider_output.parse_json()
        issues = [dict(issue) for issue in parse_issues]
        if parse_status == "ok" and parsed is not None:
            if compact_mode and parsed.get("schema_version") == "text2ifc/ifc-repair-changeset/0.1":
                legacy_issues = [
                    {"code": issue.code, "path": issue.path, "message": issue.message}
                    for issue in validate_changeset(parsed)
                ]
                if not legacy_issues:
                    legacy_issues = _bound_binding_issues(
                        parsed,
                        operations=operations,
                        resolved_document=resolved_document,
                        source_request_hash=source_request_hash,
                        base_model_fingerprint=base_fingerprint,
                        registry=registry,
                    )
                issues.extend(legacy_issues)
                if not issues:
                    parsed = _upgrade_legacy_draft(
                        parsed,
                        semantic_manifest_ref=semantic_manifest_ref,
                        semantic_manifest_hash=manifest_hash,
                        semantic_summary=semantic_summary,
                        resolved_authority=resolved_authority,
                    )
            contract_issues = (
                validate_changeset_draft(
                    parsed,
                    expected_version=(
                        DRAFT_CHANGESET_SCHEMA_VERSION_0_3
                        if structural_compact_mode
                        else None
                    ),
                )
                if compact_mode
                else validate_changeset(parsed)
            )
            issues.extend(
                {"code": issue.code, "path": issue.path, "message": issue.message}
                for issue in contract_issues
            )
            if not issues:
                if compact_mode:
                    try:
                        bound = bind_repair_changeset(
                            draft=parsed,
                            semantic_manifests=manifests,
                            semantic_manifest_hashes=manifest_hashes,
                            source_request_hash=source_request_hash,
                            base_model_fingerprint=base_fingerprint,
                            bound_schema_version=(
                                BOUND_CHANGESET_SCHEMA_VERSION_0_5
                                if mixed_semantic_contract
                                else BOUND_CHANGESET_SCHEMA_VERSION_0_4
                                if semantic_contract_v03
                                else BOUND_CHANGESET_SCHEMA_VERSION_0_3
                                if semantic_contract_v02
                                else "text2ifc/ifc-repair-changeset/0.2"
                            ),
                            resolved_authority=(
                                resolved_authority
                            ),
                        )
                    except ValueError as error:
                        issues.append(_issue(str(error).split(":", 1)[0], "/", str(error)))
                else:
                    issues.extend(
                        _bound_binding_issues(
                            parsed,
                            operations=operations,
                            resolved_document=resolved_document,
                            source_request_hash=source_request_hash,
                            base_model_fingerprint=base_fingerprint,
                            registry=registry,
                        )
                    )
        issues = _sort_issue_dicts(issues)
        diagnostics = {
            "schema_version": "text2ifc/ifc-repair-provider-stage/0.2",
            "valid": parsed is not None and not issues,
            "parse_status": parse_status,
            "issues": issues,
        }
        atomic_write_text(attempt_dir / "diagnostics.json", _json(diagnostics))
        if parsed is not None and not issues:
            if compact_mode:
                atomic_write_text(output / "provider-draft.json", _json(parsed))
                atomic_write_text(output / "bound-changeset.json", _json(bound))
                result_changeset = bound
                classification = "bound_changeset"
            else:
                atomic_write_text(output / "predicted-changeset.json", _json(parsed))
                result_changeset = parsed
                classification = "changeset"
            return {
                "valid": True,
                "classification": classification,
                "changeset": result_changeset,
                "draft": parsed if compact_mode else None,
                "prompt": _prompt_identity(rendered),
                "issues": [],
            }
        feedback = issues
        last_result = _invalid_result(issues, prompt=_prompt_identity(rendered))
    return last_result


def _compact_operation_projection(operations: list[dict[str, Any]]) -> dict[str, Any]:
    allowed = {
        "operation_id", "operation_type", "target_global_id", "scope_ids",
        "parameters", "evidence_pointers",
    }
    return {
        "operations": {
            str(operation["operation_id"]): {
                key: operation[key] for key in sorted(allowed) if key in operation
            }
            for operation in operations
        }
    }


def _structural_draft_authority(
    operations: list[dict[str, Any]],
    *,
    registry: OperationRegistry,
) -> dict[str, Any]:
    projected_operations = []
    for operation in operations:
        projected_operations.append(
            {
                "operation_id": str(operation["operation_id"]),
                "operation_type": str(operation["operation_type"]),
                "target": registry.bind_resolved_target(
                    str(operation["operation_type"]),
                    operation.get("target_global_id"),
                ),
                "parameters": json.loads(
                    json.dumps(
                        operation["parameters"],
                        ensure_ascii=False,
                        allow_nan=False,
                    )
                ),
                "evidence_refs": [
                    str(item) for item in operation["evidence_pointers"]
                ],
            }
        )
    return {
        "scope": {
            "target_ids": sorted(
                {
                    str(scope_id)
                    for operation in operations
                    for scope_id in operation["scope_ids"]
                }
            ),
            "forbidden_ids": [],
        },
        "evidence_refs": sorted(
            {
                str(pointer)
                for operation in operations
                for pointer in operation["evidence_pointers"]
            }
        ),
        "operations": projected_operations,
    }
def _semantic_summary(manifests: tuple[Any, ...]) -> dict[str, int]:
    values = {"required": 0, "conditional": 0, "not_required": 0}
    for manifest in manifests:
        for assignment in manifest.assignments:
            values[assignment.applicability.value] += 1
    return values


def _upgrade_legacy_draft(
    changeset: Mapping[str, Any],
    *,
    semantic_manifest_ref: str,
    semantic_manifest_hash: str,
    semantic_summary: Mapping[str, int],
    resolved_authority: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate released 0.1 first, then rebuild draft authority deterministically."""

    if resolved_authority is None:
        raise ValueError("LEGACY_DRAFT_AUTHORITY_REQUIRED")

    return {
        "schema_version": "text2ifc/ifc-repair-changeset-draft/0.2",
        "draft_id": str(changeset["changeset_id"]).replace("changeset", "draft", 1),
        "base_model_fingerprint": changeset["base_model_fingerprint"],
        "source_request_hash": changeset["source_request_hash"],
        "semantic_manifest_ref": semantic_manifest_ref,
        "semantic_manifest_sha256": semantic_manifest_hash,
        "semantic_summary": dict(semantic_summary),
        "scope": resolved_authority["scope"],
        "evidence_refs": resolved_authority["evidence_refs"],
        "preconditions": changeset["preconditions"],
        "postconditions": changeset["postconditions"],
        "operations": resolved_authority["operations"],
    }


def generate_repair_changeset(
    *,
    provider: Any,
    case_id: str,
    repair_request: str,
    source_request_hash: str,
    public_spec: Mapping[str, Any],
    public_context: Mapping[str, Any],
    registry: OperationRegistry,
    output_dir: Path | str,
) -> dict[str, Any]:
    """Generate and validate a ChangeSet using public inputs exclusively."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    changeset_schema = load_changeset_schema()
    supported_operations = [
        {
            "operation_type": operation_type,
            "target_ifc_classes": list(
                registry.require(operation_type).target_ifc_classes
            ),
            "prototype_ifc_classes": list(
                registry.require(operation_type).prototype_ifc_classes
            ),
            "target_schema": dict(
                registry.require(operation_type).target_schema
                or {"type": "object", "minProperties": 1}
            ),
            "parameter_schema": dict(
                registry.require(operation_type).parameter_schema
            ),
            "precondition_names": list(
                registry.require(operation_type).precondition_names
            ),
            "postcondition_names": list(
                registry.require(operation_type).postcondition_names
            ),
            "capability_constraints": dict(
                registry.require(operation_type).capability_constraints
            ),
        }
        for operation_type in registry.operation_types
    ]
    renderer_input = {
        "REPAIR_REQUEST": repair_request,
        "PUBLIC_REPAIR_SPEC": dict(public_spec),
        "PUBLIC_CONTEXT": dict(public_context),
        "SOURCE_REQUEST_HASH": source_request_hash,
        "SUPPORTED_OPERATIONS": supported_operations,
        "CHANGESET_SCHEMA": changeset_schema,
    }
    rendered = render_prompt(template_id=TEMPLATE_ID, inputs=renderer_input)
    atomic_write_text(output / "renderer-input.json", _json(renderer_input))
    atomic_write_text(output / "rendered-prompt.md", rendered["text"])

    provider_arguments = {
        "session_id": f"ifc-repair-{case_id}",
        "prompt": rendered["text"],
        "schema": changeset_schema,
        "state": {"case_id": case_id, "stage": "ifc_repair_changeset"},
    }
    generate_live = getattr(provider, "generate_live", None)
    if callable(generate_live):
        live_result = generate_live(**provider_arguments)
        provider_output = validate_provider_output(live_result.output)
        atomic_write_text(
            output / "live-request.json",
            _json(redact_provider_payload(live_result.request)),
        )
        atomic_write_text(
            output / "live-response.json",
            _json(redact_provider_payload(live_result.response)),
        )
        atomic_write_text(
            output / "live-events.jsonl",
            "".join(
                json.dumps(
                    redact_provider_payload(event),
                    ensure_ascii=False,
                    sort_keys=True,
                    allow_nan=False,
                    separators=(",", ":"),
                )
                + "\n"
                for event in live_result.events
            ),
        )
    else:
        provider_output = validate_provider_output(
            provider.generate_candidate(**provider_arguments)
        )
    atomic_write_text(output / "raw-response.txt", provider_output.text)
    atomic_write_text(
        output / "provider-metadata.json",
        _json(redact_provider_payload(provider_output.metadata)),
    )
    parse_status, parsed, parse_issues = provider_output.parse_json()
    issues: list[dict[str, str]] = [dict(issue) for issue in parse_issues]
    if parse_status == "ok" and parsed is not None:
        issues.extend(
            {"code": issue.code, "path": issue.path, "message": issue.message}
            for issue in validate_changeset(parsed)
        )
        if not issues:
            issues.extend(
                _binding_issues(
                    parsed,
                    source_request_hash=source_request_hash,
                    public_spec=public_spec,
                    public_context=public_context,
                    registry=registry,
                )
            )
    issues = sorted(
        issues,
        key=lambda issue: (issue.get("code", ""), issue.get("path", ""), issue.get("message", "")),
    )
    diagnostics = {
        "schema_version": "text2ifc/ifc-repair-provider-stage/0.1",
        "valid": not issues and parsed is not None,
        "parse_status": parse_status,
        "issues": issues,
    }
    atomic_write_text(output / "diagnostics.json", _json(diagnostics))
    if issues or parsed is None:
        return {
            "valid": False,
            "classification": "invalid",
            "changeset": None,
            "prompt": _prompt_identity(rendered),
            "issues": issues,
        }

    atomic_write_text(output / "predicted-changeset.json", _json(parsed))
    return {
        "valid": True,
        "classification": "changeset",
        "changeset": parsed,
        "prompt": _prompt_identity(rendered),
        "issues": [],
    }


def _binding_issues(
    changeset: Mapping[str, Any],
    *,
    source_request_hash: str,
    public_spec: Mapping[str, Any],
    public_context: Mapping[str, Any],
    registry: OperationRegistry,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if changeset["base_model_fingerprint"] != public_context.get(
        "base_model_fingerprint"
    ):
        issues.append(
            {
                "code": "BASE_MODEL_FINGERPRINT_MISMATCH",
                "path": "/base_model_fingerprint",
                "message": "Provider ChangeSet is not bound to the public context model.",
            }
        )
    if changeset["source_request_hash"] != source_request_hash:
        issues.append(
            {
                "code": "SOURCE_REQUEST_HASH_MISMATCH",
                "path": "/source_request_hash",
                "message": "Provider ChangeSet is not bound to the repair request.",
            }
        )
    candidate_ids = {
        str(candidate.get("ifc_global_id"))
        for candidate in public_context.get("candidate_targets", [])
    }
    referenced_definitions = []
    for index, operation in enumerate(changeset["operations"]):
        try:
            definition = registry.require(str(operation["operation_type"]))
            referenced_definitions.append(definition)
        except OperationRegistryError as error:
            issues.append(
                {
                    "code": error.code,
                    "path": f"/operations/{index}/operation_type",
                    "message": error.detail,
                }
            )
            continue
        operation_contract_issues = [
            *registry.validate_target(operation),
            *registry.validate_parameters(operation),
        ]
        issues.extend(
            {
                "code": issue.code,
                "path": f"/operations/{index}" + issue.path,
                "message": issue.message,
            }
            for issue in operation_contract_issues
        )
        target_ids = [
            str(value)
            for key, value in operation["target"].items()
            if key.endswith("_global_id")
        ]
        for target_id in target_ids:
            if target_id not in candidate_ids:
                issues.append(
                    {
                        "code": "PROVIDER_TARGET_OUTSIDE_CONTEXT",
                        "path": f"/operations/{index}/target",
                        "message": target_id,
                    }
                )
    if not set(changeset["scope"]["target_ids"]).issubset(candidate_ids):
        issues.append(
            {
                "code": "PROVIDER_SCOPE_OUTSIDE_CONTEXT",
                "path": "/scope/target_ids",
                "message": "ChangeSet scope contains a target absent from public context.",
            }
        )
    allowed_preconditions = {
        name
        for definition in referenced_definitions
        for name in definition.precondition_names
    }
    allowed_postconditions = {
        name
        for definition in referenced_definitions
        for name in definition.postcondition_names
    }
    issues.extend(
        _condition_issues(
            changeset["preconditions"],
            allowed=allowed_preconditions,
            path="/preconditions",
            code="UNDECLARED_PRECONDITION",
        )
    )
    issues.extend(
        _condition_issues(
            changeset["postconditions"],
            allowed=allowed_postconditions,
            path="/postconditions",
            code="UNDECLARED_POSTCONDITION",
        )
    )
    evidence_documents = {"spec": public_spec, "context": public_context}
    for index, evidence_ref in enumerate(changeset["evidence_refs"]):
        namespace, pointer = evidence_ref.split(":", 1)
        if namespace not in evidence_documents:
            issues.append(
                {
                    "code": "INVALID_EVIDENCE_NAMESPACE",
                    "path": f"/evidence_refs/{index}",
                    "message": namespace,
                }
            )
            continue
        if not _json_pointer_exists(evidence_documents[namespace], pointer):
            issues.append(
                {
                    "code": "EVIDENCE_POINTER_NOT_FOUND",
                    "path": f"/evidence_refs/{index}",
                    "message": evidence_ref,
                }
            )
    return issues


def _resolved_input_issues(
    operations: list[dict[str, Any]],
    *,
    model_fingerprint: str,
    registry: OperationRegistry,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    issues: list[dict[str, str]] = []
    operation_ids = [str(item.get("operation_id", "")) for item in operations]
    if not operations or len(operation_ids) != len(set(operation_ids)) or any(not item for item in operation_ids):
        issues.append(_issue("RESOLVED_OPERATION_SET_INVALID", "/operations", "operation IDs must be non-empty and unique"))
    document_operations: dict[str, Any] = {}
    for index, operation in enumerate(operations):
        operation_id = str(operation.get("operation_id", ""))
        context = operation.get("context")
        if not isinstance(context, Mapping):
            issues.append(_issue("UNRESOLVED_OPERATION_CONTEXT", f"/operations/{index}/context", operation_id))
            continue
        if context.get("model_fingerprint") != model_fingerprint:
            issues.append(_issue("RESOLVED_MODEL_FINGERPRINT_MISMATCH", f"/operations/{index}/context/model_fingerprint", operation_id))
        try:
            definition = registry.require(str(operation.get("operation_type", "")))
        except OperationRegistryError as error:
            issues.append(_issue(error.code, f"/operations/{index}/operation_type", error.detail))
            continue
        target_id = operation.get("target_global_id")
        candidates = context.get("candidate_targets", [])
        matching = [candidate for candidate in candidates if candidate.get("ifc_global_id") == target_id]
        if len(matching) != 1:
            issues.append(_issue("UNRESOLVED_OPERATION_TARGET", f"/operations/{index}/target_global_id", str(target_id)))
        if target_id not in operation.get("scope_ids", []):
            issues.append(_issue("RESOLVED_SCOPE_INCOMPLETE", f"/operations/{index}/scope_ids", str(target_id)))
        parameter_issues = registry.validate_parameters(operation)
        issues.extend(
            _issue(item.code, f"/operations/{index}{item.path}", item.message)
            for item in parameter_issues
        )
        if not operation.get("evidence_pointers"):
            issues.append(_issue("RESOLVED_EVIDENCE_REQUIRED", f"/operations/{index}/evidence_pointers", operation_id))
        if not set(operation.get("scope_ids", [])).issubset(
            {str(candidate.get("ifc_global_id")) for candidate in candidates}
        ):
            issues.append(_issue("RESOLVED_SCOPE_OUTSIDE_CONTEXT", f"/operations/{index}/scope_ids", operation_id))
        document_operations[operation_id] = {
            **operation,
            "registered_target_ifc_classes": list(definition.target_ifc_classes),
            "registered_prototype_ifc_classes": list(
                definition.prototype_ifc_classes
            ),
        }
    document = {"operations": document_operations}
    if _contains_private_or_step(document):
        issues.append(_issue("PRIVATE_CONTEXT_FORBIDDEN", "/operations", "private or STEP canary detected"))
    return _sort_issue_dicts(issues), document


def _bound_binding_issues(
    changeset: Mapping[str, Any],
    *,
    operations: list[dict[str, Any]],
    resolved_document: Mapping[str, Any],
    source_request_hash: str,
    base_model_fingerprint: str,
    registry: OperationRegistry,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    expected = {str(item["operation_id"]): item for item in operations}
    actual_operations = list(changeset["operations"])
    actual_ids = [str(item["operation_id"]) for item in actual_operations]
    if len(actual_operations) != len(expected):
        issues.append(_issue("OPERATION_CARDINALITY_MISMATCH", "/operations", f"expected {len(expected)}, received {len(actual_operations)}"))
    if set(actual_ids) != set(expected):
        issues.append(_issue("OPERATION_ID_SET_MISMATCH", "/operations", "ChangeSet operation IDs must exactly equal resolved IDs"))
    if changeset["source_request_hash"] != source_request_hash:
        issues.append(_issue("SOURCE_REQUEST_HASH_MISMATCH", "/source_request_hash", "stale request binding"))
    if changeset["base_model_fingerprint"] != base_model_fingerprint:
        issues.append(_issue("BASE_MODEL_FINGERPRINT_MISMATCH", "/base_model_fingerprint", "stale model binding"))

    expected_scope = {str(scope_id) for item in operations for scope_id in item["scope_ids"]}
    actual_scope = list(changeset["scope"]["target_ids"])
    if len(actual_scope) != len(expected_scope) or set(actual_scope) != expected_scope:
        issues.append(_issue("CHANGESET_SCOPE_SET_MISMATCH", "/scope/target_ids", "scope must equal the resolved union"))
    expected_evidence = {str(pointer) for item in operations for pointer in item["evidence_pointers"]}
    if set(changeset["evidence_refs"]) != expected_evidence:
        issues.append(_issue("CHANGESET_EVIDENCE_SET_MISMATCH", "/evidence_refs", "evidence must equal the resolved union"))

    referenced_definitions = []
    for index, operation in enumerate(actual_operations):
        operation_id = str(operation["operation_id"])
        authority = expected.get(operation_id)
        if authority is None:
            continue
        if operation["operation_type"] != authority["operation_type"]:
            issues.append(_issue("OPERATION_TYPE_MISMATCH", f"/operations/{index}/operation_type", operation_id))
        try:
            definition = registry.require(str(operation["operation_type"]))
            referenced_definitions.append(definition)
            contract_issues = [*registry.validate_target(operation), *registry.validate_parameters(operation)]
            issues.extend(
                _issue(item.code, f"/operations/{index}{item.path}", item.message)
                for item in contract_issues
            )
        except OperationRegistryError as error:
            issues.append(_issue(error.code, f"/operations/{index}/operation_type", error.detail))
        target_ids = {
            str(value)
            for key, value in operation["target"].items()
            if key.endswith("_global_id")
        }
        if target_ids != {authority["target_global_id"]}:
            issues.append(_issue("OPERATION_TARGET_OUTSIDE_CONTEXT", f"/operations/{index}/target", operation_id))
        if operation["parameters"] != authority["parameters"]:
            issues.append(_issue("OPERATION_PARAMETERS_MISMATCH", f"/operations/{index}/parameters", operation_id))
        allowed_evidence = set(authority["evidence_pointers"])
        if set(operation["evidence_refs"]) != allowed_evidence:
            issues.append(_issue("CROSS_OPERATION_EVIDENCE", f"/operations/{index}/evidence_refs", operation_id))
        for evidence_index, evidence_ref in enumerate(operation["evidence_refs"]):
            namespace, pointer = evidence_ref.split(":", 1)
            if namespace != "resolved" or not _json_pointer_exists(resolved_document, pointer):
                issues.append(_issue("EVIDENCE_POINTER_NOT_FOUND", f"/operations/{index}/evidence_refs/{evidence_index}", evidence_ref))

    allowed_preconditions = {name for definition in referenced_definitions for name in definition.precondition_names}
    allowed_postconditions = {name for definition in referenced_definitions for name in definition.postcondition_names}
    issues.extend(_condition_issues(changeset["preconditions"], allowed=allowed_preconditions, path="/preconditions", code="UNDECLARED_PRECONDITION"))
    issues.extend(_condition_issues(changeset["postconditions"], allowed=allowed_postconditions, path="/postconditions", code="UNDECLARED_POSTCONDITION"))
    if _contains_private_or_step(changeset):
        issues.append(_issue("STEP_OR_PRIVATE_OUTPUT_FORBIDDEN", "/", "private or STEP content detected"))
    return _sort_issue_dicts(issues)


def _plain_operation(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise ValueError("RESOLVED_OPERATION_INVALID")
    return json.loads(json.dumps(dict(value), ensure_ascii=False, allow_nan=False))


def _call_bound_provider(provider: Any, arguments: Mapping[str, Any], attempt_dir: Path):
    generate_live = getattr(provider, "generate_live", None)
    if callable(generate_live):
        live_result = generate_live(**arguments)
        atomic_write_text(attempt_dir / "live-request.json", _json(redact_provider_payload(live_result.request)))
        atomic_write_text(attempt_dir / "live-response.json", _json(redact_provider_payload(live_result.response)))
        atomic_write_text(
            attempt_dir / "live-events.jsonl",
            "".join(_json(redact_provider_payload(event)) for event in live_result.events),
        )
        return validate_provider_output(live_result.output)
    generate_candidate = getattr(provider, "generate_candidate", None)
    if not callable(generate_candidate):
        raise ProviderOutputError("PROVIDER_INTERFACE_UNSUPPORTED")
    return validate_provider_output(generate_candidate(**arguments))


def _operation_contract(registry: OperationRegistry, operation_type: str) -> dict[str, Any]:
    definition = registry.require(operation_type)
    return {
        "operation_type": operation_type,
        "target_ifc_classes": list(definition.target_ifc_classes),
        "prototype_ifc_classes": list(definition.prototype_ifc_classes),
        "prototype_dimension_paths": {
            key: list(path)
            for key, path in sorted(definition.prototype_dimension_paths.items())
        },
        "target_schema": dict(definition.target_schema or {"type": "object", "minProperties": 1}),
        "parameter_schema": dict(definition.parameter_schema),
        "precondition_names": list(definition.precondition_names),
        "postcondition_names": list(definition.postcondition_names),
        "capability_constraints": dict(definition.capability_constraints),
    }


def _stage2_operation_contract(
    registry: OperationRegistry,
    operation_type: str,
) -> dict[str, Any]:
    """Expose only the executable Draft responsibility for structural Stage 2."""

    definition = registry.require(operation_type)
    return {
        "operation_type": operation_type,
        "target_ifc_classes": list(definition.target_ifc_classes),
        "target_schema": dict(
            definition.target_schema
            or {"type": "object", "minProperties": 1}
        ),
        "parameter_schema": dict(definition.parameter_schema),
        "precondition_names": list(definition.precondition_names),
        "postcondition_names": list(definition.postcondition_names),
    }


def _contains_private_or_step(value: Any) -> bool:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
    return any(canary in rendered for canary in _PRIVATE_CANARIES)


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _sort_issue_dicts(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(issues, key=lambda item: (item.get("code", ""), item.get("path", ""), item.get("message", "")))


def _invalid_result(
    issues: list[dict[str, str]], *, prompt: Mapping[str, str] | None = None
) -> dict[str, Any]:
    return {
        "valid": False,
        "classification": "invalid",
        "changeset": None,
        "prompt": None if prompt is None else dict(prompt),
        "issues": _sort_issue_dicts(issues),
    }


def _condition_issues(
    values: list[str],
    *,
    allowed: set[str],
    path: str,
    code: str,
) -> list[dict[str, str]]:
    if not allowed:
        return []
    return [
        {
            "code": code,
            "path": f"{path}/{index}",
            "message": value,
        }
        for index, value in enumerate(values)
        if value not in allowed
    ]


def _json_pointer_exists(document: Any, pointer: str) -> bool:
    if not pointer.startswith("/"):
        return False
    current = document
    for raw_token in pointer[1:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if token not in current:
                return False
            current = current[token]
        elif isinstance(current, list):
            if not token.isdigit() or int(token) >= len(current):
                return False
            current = current[int(token)]
        else:
            return False
    return True


def _prompt_identity(rendered: Mapping[str, Any]) -> dict[str, str]:
    metadata = rendered["metadata"]
    return {
        "template_id": str(metadata["template_id"]),
        "template_hash": str(metadata["template_hash"]),
    }


def _json(payload: Any) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
