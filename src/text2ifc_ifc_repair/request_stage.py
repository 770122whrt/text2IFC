"""Public-only Provider stage for natural-language IFC repair requests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from text2ifc_agent.prompt_registry import render_prompt
from text2ifc_agent.providers import (
    ProviderOutputError,
    redact_provider_payload,
    validate_provider_output,
)
from text2ifc_text.splits import atomic_write_text

from .registry import OperationRegistry, OperationRegistryError
from .prompt_profiles import (
    PromptProfileError,
    compact_profile_catalog,
    load_prompt_profiles,
)
from .repair_intent import (
    DEFAULT_REPAIR_INTENT_LIMITS,
    RepairIntent,
    RepairIntentCode,
    RepairIntentError,
    REPAIR_INTENT_BODY_SCHEMA_VERSION,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_2,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_3,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_4,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_5,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_6,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_7,
    REPAIR_INTENT_BODY_SCHEMA_VERSION_0_8,
    REPAIR_INTENT_SCHEMA_VERSION,
    REPAIR_INTENT_SCHEMA_VERSION_0_2,
    REPAIR_INTENT_SCHEMA_VERSION_0_3,
    REPAIR_INTENT_SCHEMA_VERSION_0_4,
    REPAIR_INTENT_SCHEMA_VERSION_0_5,
    REPAIR_INTENT_SCHEMA_VERSION_0_6,
    REPAIR_INTENT_SCHEMA_VERSION_0_7,
    REPAIR_INTENT_SCHEMA_VERSION_0_8,
    fingerprint_text,
    hash_request,
    load_repair_intent_body_schema,
    load_repair_intent_schema,
)


TEMPLATE_ID = "ifc-repair-intent.v0.1"
TEMPLATE_ID_0_2 = "ifc-repair-intent.v0.2"
TEMPLATE_ID_0_3 = "ifc-repair-intent.v0.3"
TEMPLATE_ID_0_4 = "ifc-repair-intent.v0.4"
TEMPLATE_ID_0_5 = "ifc-repair-intent.v0.5"
TEMPLATE_ID_0_6 = "ifc-repair-intent.v0.6"
TEMPLATE_ID_0_7 = "ifc-repair-intent.v0.7"
TEMPLATE_ID_0_8 = "ifc-repair-intent.v0.8"
_INTENT_CONTRACTS = {
    REPAIR_INTENT_SCHEMA_VERSION: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION,
        TEMPLATE_ID,
    ),
    REPAIR_INTENT_SCHEMA_VERSION_0_2: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_2,
        TEMPLATE_ID_0_2,
    ),
    REPAIR_INTENT_SCHEMA_VERSION_0_3: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_3,
        TEMPLATE_ID_0_3,
    ),
    REPAIR_INTENT_SCHEMA_VERSION_0_4: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_4,
        TEMPLATE_ID_0_4,
    ),
    REPAIR_INTENT_SCHEMA_VERSION_0_5: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_5,
        TEMPLATE_ID_0_5,
    ),
    REPAIR_INTENT_SCHEMA_VERSION_0_6: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_6,
        TEMPLATE_ID_0_6,
    ),
    REPAIR_INTENT_SCHEMA_VERSION_0_7: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_7,
        TEMPLATE_ID_0_7,
    ),
    REPAIR_INTENT_SCHEMA_VERSION_0_8: (
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_8,
        TEMPLATE_ID_0_8,
    ),
}
MAX_REQUEST_BYTES = DEFAULT_REPAIR_INTENT_LIMITS.max_request_bytes
MAX_PROVIDER_RESPONSE_BYTES = (
    DEFAULT_REPAIR_INTENT_LIMITS.max_provider_response_bytes
)
MAX_CORRECTION_ATTEMPTS = DEFAULT_REPAIR_INTENT_LIMITS.max_correction_attempts


def generate_repair_intent(
    *,
    provider: Any,
    request_id: str,
    repair_request: str,
    registry: OperationRegistry,
    output_dir: Path | str,
    max_attempts: int = MAX_CORRECTION_ATTEMPTS,
    intent_schema_version: str = REPAIR_INTENT_SCHEMA_VERSION,
) -> dict[str, Any]:
    """Generate one Registry-bound RepairIntent from bounded public data."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if len(repair_request.encode("utf-8")) > MAX_REQUEST_BYTES:
        return _failure(RepairIntentCode.REQUEST_TOO_LARGE, attempts=())
    if not 1 <= max_attempts <= MAX_CORRECTION_ATTEMPTS:
        return _failure(RepairIntentCode.ATTEMPT_BUDGET_INVALID, attempts=())

    contract = _INTENT_CONTRACTS.get(intent_schema_version)
    if contract is None:
        return _failure(RepairIntentCode.SCHEMA_INVALID, attempts=())
    body_schema_version, template_id = contract
    envelope_schema = load_repair_intent_schema(intent_schema_version)
    schema = load_repair_intent_body_schema(body_schema_version)
    source_request_hash = hash_request(repair_request)
    supported_operations = (
        _compact_supported_profiles(
            registry,
            intent_schema_version=intent_schema_version,
        )
        if intent_schema_version
        in {
            REPAIR_INTENT_SCHEMA_VERSION_0_5,
            REPAIR_INTENT_SCHEMA_VERSION_0_6,
            REPAIR_INTENT_SCHEMA_VERSION_0_7,
            REPAIR_INTENT_SCHEMA_VERSION_0_8,
        }
        else _supported_operations(registry)
    )
    feedback: list[dict[str, str]] = []
    rendered = render_prompt(
        template_id=template_id,
        inputs={
            "REPAIR_REQUEST": repair_request,
            "SUPPORTED_OPERATIONS": supported_operations,
            "REPAIR_INTENT_SCHEMA": schema,
            "VALIDATION_FEEDBACK": feedback,
        },
    )
    renderer_input = dict(rendered["inputs"])
    atomic_write_text(output / "renderer-input.json", _pretty_json(renderer_input))
    atomic_write_text(output / "rendered-prompt.md", str(rendered["text"]))

    attempts: list[dict[str, Any]] = []
    for attempt_number in range(1, max_attempts + 1):
        normalizations: list[str] = []
        if attempt_number > 1:
            rendered = render_prompt(
                template_id=template_id,
                inputs={**renderer_input, "VALIDATION_FEEDBACK": feedback},
            )
        provider_arguments = {
            "session_id": f"ifc-repair-intent-{request_id}",
            "prompt": str(rendered["text"]),
            "schema": schema,
            "state": {
                "request_id": request_id,
                "stage": "ifc_repair_intent",
                "attempt": attempt_number,
            },
        }
        try:
            provider_output, live_evidence = _call_provider(
                provider, provider_arguments
            )
        except ProviderOutputError as error:
            details = getattr(error, "details", {}) or {}
            safe_details = {
                key: details[key]
                for key in (
                    "provider",
                    "failure_class",
                    "exception_type",
                    "exception_chain",
                    "transport_attempts",
                    "session_id",
                    "estimated_input_tokens",
                    "max_input_tokens",
                )
                if key in details
            }
            issues = [
                _issue(
                    RepairIntentCode.PROVIDER_REQUEST_FAILED,
                    type(error).__name__,
                )
            ]
            attempt = _attempt_record(
                attempt_number=attempt_number,
                issues=issues,
                provider_metadata={"provider_error": safe_details},
                raw_text="",
                normalizations=normalizations,
            )
            attempts.append(attempt)
            atomic_write_text(
                output / f"attempt-{attempt_number:03d}.json",
                _pretty_json(attempt),
            )
            feedback = issues
            continue
        issues: list[dict[str, str]] = []
        intent: RepairIntent | None = None
        raw_text = provider_output.text
        if len(raw_text.encode("utf-8")) > MAX_PROVIDER_RESPONSE_BYTES:
            issues.append(
                _issue(
                    RepairIntentCode.PROVIDER_RESPONSE_TOO_LARGE,
                    "Provider response exceeds the public Stage 1 byte limit.",
                )
            )
        else:
            parse_status, parsed, parse_issues = provider_output.parse_json()
            if parse_status != "ok" or parsed is None:
                issues.extend(_normalize_issues(parse_issues))
            elif parse_issues:
                issues.extend(_normalize_issues(parse_issues))
            else:
                try:
                    body_errors = sorted(
                        Draft202012Validator(schema).iter_errors(parsed),
                        key=lambda error: tuple(
                            str(part) for part in error.absolute_path
                        ),
                    )
                    if body_errors:
                        error = body_errors[0]
                        raise RepairIntentError(
                            RepairIntentCode.SCHEMA_INVALID,
                            error.message,
                            path=_pointer(error.absolute_path),
                        )
                    parsed, normalizations = (
                        _fold_created_occurrence_property_operations(
                            parsed, registry=registry
                        )
                    )
                    if (
                        intent_schema_version
                        in {
                            REPAIR_INTENT_SCHEMA_VERSION_0_5,
                            REPAIR_INTENT_SCHEMA_VERSION_0_6,
                            REPAIR_INTENT_SCHEMA_VERSION_0_7,
                            REPAIR_INTENT_SCHEMA_VERSION_0_8,
                        }
                    ):
                        _validate_operation_routing(
                            parsed,
                            registry=registry,
                            intent_schema_version=intent_schema_version,
                        )
                    model = str(provider_output.metadata.get("model", ""))
                    if not model:
                        raise RepairIntentError(
                            RepairIntentCode.MODEL_FINGERPRINT_MISMATCH,
                            "Provider response metadata does not identify the model.",
                        )
                    operations = []
                    for raw_operation in parsed["operations"]:
                        operation = json.loads(json.dumps(raw_operation))
                        operation["parameters"] = registry.prepare_partial_parameters(
                            operation
                        )
                        operations.append(operation)
                    envelope = {
                        "schema_version": envelope_schema["$id"],
                        "request_id": request_id,
                        "source_request_hash": source_request_hash,
                        "model_fingerprint": fingerprint_text(model),
                        "prompt_fingerprint": str(
                            rendered["metadata"]["template_hash"]
                        ),
                        "operations": operations,
                        "provenance": parsed["provenance"],
                    }
                    if "unsupported_requests" in parsed:
                        envelope["unsupported_requests"] = parsed[
                            "unsupported_requests"
                        ]
                    if "semantic_bundles" in parsed:
                        envelope["semantic_bundles"] = parsed["semantic_bundles"]
                    intent = RepairIntent.from_dict(
                        envelope,
                        registry=registry,
                        require_complete=False,
                    )
                except OperationRegistryError as error:
                    issues.append(
                        _issue(
                            RepairIntentCode.UNSUPPORTED_OPERATION,
                            error.detail,
                            path="/operations",
                        )
                    )
                except PromptProfileError as error:
                    issues.append(
                        _issue(
                            RepairIntentCode.OPERATION_PROFILE_MISMATCH,
                            error.detail,
                            path="/operations",
                        )
                    )
                except RepairIntentError as error:
                    issues.append(_issue(error.code, error.detail, path=error.path))

        issues = sorted(
            issues,
            key=lambda item: (item["code"], item["path"], item["message"]),
        )
        attempt = _attempt_record(
            attempt_number=attempt_number,
            issues=issues,
            provider_metadata=provider_output.metadata,
            raw_text=raw_text,
            valid=intent is not None and not issues,
            normalizations=normalizations,
        )
        attempts.append(attempt)
        atomic_write_text(
            output / f"attempt-{attempt_number:03d}.json",
            _pretty_json(attempt),
        )
        _write_live_evidence(output, attempt_number, live_evidence)
        if intent is not None and not issues:
            unsupported_operations = _unsupported_operations(intent, registry)
            missing_parameters = (
                []
                if unsupported_operations
                else _missing_parameters(intent, registry)
            )
            missing_properties = (
                [] if unsupported_operations else _missing_properties(intent)
            )
            if (
                not unsupported_operations
                and not missing_parameters
                and not missing_properties
            ):
                intent = RepairIntent.from_dict(intent.to_dict(), registry=registry)
            classification = (
                "unsupported"
                if unsupported_operations
                else "clarification_required"
                if missing_parameters or missing_properties
                else "repair_intent"
            )
            atomic_write_text(
                output / "repair-intent.json", _pretty_json(intent.to_dict())
            )
            completeness = {
                "schema_version": "text2ifc/ifc-repair-intent-completeness/0.1",
                "status": classification,
                "missing_parameters": missing_parameters,
                "missing_properties": missing_properties,
                "unsupported_operations": unsupported_operations,
            }
            atomic_write_text(
                output / "repair-intent-completeness.json",
                _pretty_json(completeness),
            )
            return {
                "valid": True,
                "classification": classification,
                "intent": intent,
                "missing_parameters": missing_parameters,
                "missing_properties": missing_properties,
                "unsupported_operations": unsupported_operations,
                "reason_code": (
                    unsupported_operations[0]["reason_code"]
                    if unsupported_operations
                    else None
                ),
                "prompt": _prompt_identity(rendered),
                "attempts": attempts,
                "error_code": None,
            }
        feedback = issues

    return _failure(
        RepairIntentCode.RETRY_EXHAUSTED,
        attempts=tuple(attempts),
        prompt=_prompt_identity(rendered),
    )


def _call_provider(
    provider: Any, provider_arguments: Mapping[str, Any]
) -> tuple[Any, Mapping[str, Any] | None]:
    generate_live = getattr(provider, "generate_live", None)
    if callable(generate_live):
        live_result = generate_live(**provider_arguments)
        return validate_provider_output(live_result.output), {
            "request": live_result.request,
            "response": live_result.response,
            "events": list(live_result.events),
        }
    return (
        validate_provider_output(provider.generate_candidate(**provider_arguments)),
        None,
    )


def _missing_parameters(
    intent: RepairIntent,
    registry: OperationRegistry,
) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for operation in intent.operations:
        paths = registry.missing_required_parameters(operation.to_dict())
        if paths:
            missing.append(
                {"operation_id": operation.operation_id, "paths": list(paths)}
            )
    return missing


def _unsupported_operations(
    intent: RepairIntent,
    registry: OperationRegistry,
) -> list[dict[str, str]]:
    unsupported: list[dict[str, str]] = []
    explicit_ids: set[tuple[str, str]] = set()
    has_unregistered = False
    for request in intent.unsupported_requests:
        if request.kind == "unregistered_action":
            has_unregistered = True
            unsupported.append(
                {
                    "operation_id": "",
                    "reason_code": "REPAIR_REQUEST_OUT_OF_SCOPE",
                }
            )
            continue
        operation = next(
            item
            for item in intent.operations
            if item.operation_id == request.operation_id
        )
        if request.capability_id.startswith("structural_analysis_"):
            reason_code = "STRUCTURAL_ANALYSIS_UNSUPPORTED"
        else:
            decision = registry.assess_intent_capability(operation.to_dict())
            reason_code = str(decision.get("reason_code") or "")
            if not reason_code:
                family = (
                    operation.routing_intent.component_family
                    if operation.routing_intent is not None
                    else ""
                )
                reason_code = {
                    "beam": "BEAM_GEOMETRY_UNSUPPORTED",
                    "column": "COLUMN_GEOMETRY_UNSUPPORTED",
                }.get(family, "OPERATION_UNSUPPORTED")
        explicit_ids.add((operation.operation_id, reason_code))
        unsupported.append(
            {
                "operation_id": operation.operation_id,
                "reason_code": reason_code,
            }
        )
    for operation in intent.operations:
        decision = registry.assess_intent_capability(operation.to_dict())
        if str(decision.get("status")) != "unsupported":
            continue
        pair = (
            operation.operation_id,
            str(decision.get("reason_code") or "OPERATION_UNSUPPORTED"),
        )
        if pair in explicit_ids:
            continue
        unsupported.append(
            {
                "operation_id": operation.operation_id,
                "reason_code": pair[1],
            }
        )
    reason_codes = {item["reason_code"] for item in unsupported}
    if (
        has_unregistered and intent.operations
    ) or len(reason_codes) > 1:
        return [
            {
                **item,
                "reason_code": "REPAIR_REQUEST_CONTAINS_UNSUPPORTED_ACTIONS",
            }
            for item in unsupported
        ]
    return unsupported


def _missing_properties(intent: RepairIntent) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for operation in intent.operations:
        for property_index, property_intent in enumerate(
            operation.property_intents
        ):
            if property_intent.missing_fields:
                missing.append(
                    {
                        "operation_id": operation.operation_id,
                        "property_index": property_index,
                        "fields": list(property_intent.missing_fields),
                    }
                )
    return missing


def _pointer(parts: Any) -> str:
    tokens = [str(part).replace("~", "~0").replace("/", "~1") for part in parts]
    return "/" + "/".join(tokens) if tokens else ""


def _supported_operations(registry: OperationRegistry) -> list[dict[str, Any]]:
    return [
        {
            "operation_type": operation_type,
            "target_ifc_classes": list(
                registry.require(operation_type).target_ifc_classes
            ),
            "prototype_ifc_classes": list(
                registry.require(operation_type).prototype_ifc_classes
            ),
            "prototype_dimension_paths": {
                key: list(path)
                for key, path in sorted(
                    registry.require(operation_type).prototype_dimension_paths.items()
                )
            },
            "parameter_schema": dict(
                registry.require(operation_type).parameter_schema
            ),
            "capability_constraints": dict(
                registry.require(operation_type).capability_constraints
            ),
        }
        for operation_type in registry.operation_types
    ]


def _compact_supported_profiles(
    registry: OperationRegistry,
    *,
    intent_schema_version: str,
) -> list[dict[str, Any]]:
    profile_ids = []
    for operation_type in registry.operation_types:
        profile_id = registry.require(operation_type).prompt_profile_id
        if profile_id is None:
            raise PromptProfileError(
                "PROFILE_BINDING_MISSING", operation_type
            )
        profile_ids.append(
            _profile_id_for_intent_contract(
                profile_id,
                intent_schema_version=intent_schema_version,
            )
        )
    catalog = list(
        compact_profile_catalog(
            load_prompt_profiles(),
            include_profile_ids=profile_ids,
        )
    )
    for item in catalog:
        definition = registry.require(str(item["operation_type"]))
        item["intent_parameter_schema"] = dict(
            definition.intent_parameter_schema or definition.parameter_schema
        )
        if definition.intent_target_schema is not None:
            item["intent_target_schema"] = dict(
                definition.intent_target_schema
            )
    return catalog


def _profile_id_for_intent_contract(
    profile_id: str,
    *,
    intent_schema_version: str,
) -> str:
    structural_profiles = {
        "beam.add.v0.3": "beam.add",
        "column.add.v0.3": "column.add",
    }
    base_profile = structural_profiles.get(profile_id)
    if base_profile is not None:
        if intent_schema_version == REPAIR_INTENT_SCHEMA_VERSION_0_5:
            return base_profile
        if intent_schema_version == REPAIR_INTENT_SCHEMA_VERSION_0_6:
            return f"{base_profile}.v0.2"
    return profile_id


def _validate_operation_routing(
    document: Mapping[str, Any],
    *,
    registry: OperationRegistry,
    intent_schema_version: str,
) -> None:
    profiles = load_prompt_profiles()
    for index, operation in enumerate(document.get("operations", ())):
        operation_type = str(operation.get("operation_type", ""))
        definition = registry.require(operation_type)
        expected_profile_id = (
            None
            if definition.prompt_profile_id is None
            else _profile_id_for_intent_contract(
                definition.prompt_profile_id,
                intent_schema_version=intent_schema_version,
            )
        )
        routing = operation.get("routing_intent")
        if not isinstance(routing, Mapping) or expected_profile_id is None:
            raise RepairIntentError(
                RepairIntentCode.OPERATION_PROFILE_MISMATCH,
                operation_type,
                path=f"/operations/{index}/routing_intent",
            )
        profile = profiles.get(expected_profile_id)
        actual = (
            str(routing.get("component_family", "")),
            str(routing.get("action", "")),
            str(routing.get("operation_profile", "")),
        )
        expected = (
            profile.component_family if profile else "",
            profile.action if profile else "",
            expected_profile_id,
        )
        if actual != expected or profile is None:
            raise RepairIntentError(
                RepairIntentCode.OPERATION_PROFILE_MISMATCH,
                f"expected={expected!r} actual={actual!r}",
                path=f"/operations/{index}/routing_intent",
            )


def _fold_created_occurrence_property_operations(
    document: Mapping[str, Any],
    *,
    registry: OperationRegistry,
) -> tuple[dict[str, Any], list[str]]:
    """Fold an unbound property-only operation into its unique new Window.

    A Provider may express one user action as ``add Window`` followed by
    ``set properties on the Window hosted by that wall``.  The second operation
    cannot safely resolve before the new occurrence exists and could otherwise
    select a surviving Window.  Normalize only the narrow, lossless case where
    the host wall identifies exactly one add operation and the property
    operation carries no independent target or semantic side effects.
    """

    normalized = json.loads(json.dumps(document))
    if normalized.get("schema_version") not in {
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_4,
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_5,
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_6,
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_7,
        REPAIR_INTENT_BODY_SCHEMA_VERSION_0_8,
    }:
        return normalized, []

    operations = normalized.get("operations")
    if not isinstance(operations, list):
        return normalized, []

    additions_by_wall: dict[str, list[dict[str, Any]]] = {}
    for operation in operations:
        try:
            definition = registry.require(str(operation.get("operation_type", "")))
        except OperationRegistryError:
            continue
        created_class = definition.editable_occurrence_ifc_class
        if created_class is None:
            continue
        target = operation.get("target_query")
        if not isinstance(target, Mapping):
            continue
        wall_global_id = target.get("global_id")
        if isinstance(wall_global_id, str) and wall_global_id:
            operation["_created_occurrence_class"] = created_class
            additions_by_wall.setdefault(wall_global_id, []).append(operation)

    removed_ids: set[int] = set()
    normalization_codes: list[str] = []
    for property_operation in operations:
        if not _is_foldable_created_occurrence_property_operation(property_operation):
            continue
        target = property_operation["target_query"]
        matches = additions_by_wall.get(str(target["host_global_id"]), [])
        matches = [
            item
            for item in matches
            if set(target.get("allowed_ifc_classes", ()))
            == {item.get("_created_occurrence_class")}
        ]
        if len(matches) != 1:
            continue
        addition = matches[0]
        if not _merge_created_window_properties(addition, property_operation):
            continue
        removed_ids.add(id(property_operation))
        normalization_codes.append(
            "FOLD_CREATED_WINDOW_OCCURRENCE_PROPERTIES:"
            f"{property_operation.get('operation_id', '')}->"
            f"{addition.get('operation_id', '')}"
        )

    if removed_ids:
        normalized["operations"] = [
            operation for operation in operations if id(operation) not in removed_ids
        ]
    for operation in normalized.get("operations", ()):
        operation.pop("_created_occurrence_class", None)
    return normalized, normalization_codes


def _is_foldable_created_occurrence_property_operation(
    operation: Mapping[str, Any],
) -> bool:
    if operation.get("operation_type") != "set_occurrence_properties":
        return False
    target = operation.get("target_query")
    if not isinstance(target, Mapping):
        return False
    if target.get("global_id"):
        return False
    if len(set(target.get("allowed_ifc_classes", ()))) != 1:
        return False
    if not target.get("host_global_id"):
        return False
    if operation.get("parameters"):
        return False
    for field in (
        "attribute_intents",
        "semantic_bundle_refs",
    ):
        if operation.get(field):
            return False
    if operation.get("occurrence_reuse_intent") is not None:
        return False
    return bool(
        operation.get("property_intents")
        or operation.get("quantity_intents")
    )


def _fold_created_window_property_operations(
    document: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Backward-compatible private test seam for the v0.4 Window path."""

    from .operations import create_default_registry

    return _fold_created_occurrence_property_operations(
        document, registry=create_default_registry()
    )


def _merge_created_window_properties(
    addition: dict[str, Any],
    property_operation: Mapping[str, Any],
) -> bool:
    addition_prototype = addition.get("prototype_intent")
    property_prototype = property_operation.get("prototype_intent")
    if (
        addition_prototype is not None
        and property_prototype is not None
        and addition_prototype != property_prototype
    ):
        return False
    if addition_prototype is None and property_prototype is not None:
        addition["prototype_intent"] = property_prototype

    existing = list(addition.get("property_intents", ()))
    by_slot: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for property_intent in existing:
        slot = _property_intent_slot(property_intent)
        if slot is not None:
            by_slot[slot] = property_intent
    for property_intent in property_operation.get("property_intents", ()):
        slot = _property_intent_slot(property_intent)
        if slot is not None and slot in by_slot:
            if by_slot[slot] != property_intent:
                return False
            continue
        existing.append(property_intent)
        if slot is not None:
            by_slot[slot] = property_intent
    addition["property_intents"] = existing

    existing_quantities = list(addition.get("quantity_intents", ()))
    quantities_by_slot: dict[
        tuple[str, str, str], Mapping[str, Any]
    ] = {}
    for quantity_intent in existing_quantities:
        slot = _quantity_intent_slot(quantity_intent)
        if slot is not None:
            quantities_by_slot[slot] = quantity_intent
    for quantity_intent in property_operation.get("quantity_intents", ()):
        slot = _quantity_intent_slot(quantity_intent)
        if slot is not None and slot in quantities_by_slot:
            if quantities_by_slot[slot] != quantity_intent:
                return False
            continue
        existing_quantities.append(quantity_intent)
        if slot is not None:
            quantities_by_slot[slot] = quantity_intent
    addition["quantity_intents"] = existing_quantities

    provenance = list(addition.get("provenance", ()))
    seen = {_canonical_json(item) for item in provenance}
    for source in property_operation.get("provenance", ()):
        key = _canonical_json(source)
        if key not in seen:
            provenance.append(source)
            seen.add(key)
    addition["provenance"] = provenance
    return True


def _property_intent_slot(
    property_intent: Mapping[str, Any],
) -> tuple[str, str, str] | None:
    set_name = property_intent.get("set_name")
    property_name = property_intent.get("property_name")
    if not isinstance(set_name, str) or not isinstance(property_name, str):
        return None
    return (
        set_name,
        property_name,
        str(property_intent.get("scope", "occurrence_direct")),
    )


def _quantity_intent_slot(
    quantity_intent: Mapping[str, Any],
) -> tuple[str, str, str] | None:
    scope = quantity_intent.get("scope")
    set_name = quantity_intent.get("set_name")
    quantity_name = quantity_intent.get("quantity_name")
    if not all(
        isinstance(item, str)
        for item in (scope, set_name, quantity_name)
    ):
        return None
    return str(scope), str(set_name), str(quantity_name)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize_issues(values: list[dict[str, Any]]) -> list[dict[str, str]]:
    return [
        _issue(
            str(item.get("code", "PROVIDER_JSON_INVALID")),
            str(item.get("message", "Provider JSON is invalid.")),
            path=str(item.get("path", "")),
        )
        for item in values
    ]


def _issue(
    code: RepairIntentCode | str, message: str, *, path: str = ""
) -> dict[str, str]:
    stable_code = code.value if isinstance(code, RepairIntentCode) else code
    return {"code": stable_code, "path": path, "message": message[:1000]}


def _failure(
    error_code: RepairIntentCode | str,
    *,
    attempts: tuple[dict[str, Any], ...],
    prompt: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "valid": False,
        "classification": "invalid",
        "intent": None,
        "prompt": dict(prompt or {}),
        "attempts": list(attempts),
        "error_code": (
            error_code.value
            if isinstance(error_code, RepairIntentCode)
            else error_code
        ),
    }


def _prompt_identity(rendered: Mapping[str, Any]) -> dict[str, str]:
    metadata = rendered["metadata"]
    return {
        "template_id": str(metadata["template_id"]),
        "template_hash": str(metadata["template_hash"]),
    }


def _bounded_redacted_excerpt(value: str) -> str:
    redacted = str(_redact_private(value))
    return redacted[: DEFAULT_REPAIR_INTENT_LIMITS.max_attempt_excerpt_chars]


def _redact_private(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for term in DEFAULT_REPAIR_INTENT_LIMITS.private_canary_terms:
            redacted = redacted.replace(term, "[REDACTED_PRIVATE]")
        return redacted
    if isinstance(value, Mapping):
        return {str(key): _redact_private(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact_private(item) for item in value]
    return value


def _attempt_record(
    *,
    attempt_number: int,
    issues: list[dict[str, str]],
    provider_metadata: Mapping[str, Any],
    raw_text: str,
    valid: bool = False,
    normalizations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "attempt": attempt_number,
        "status": "valid" if valid else "invalid",
        "issues": issues,
        "provider_metadata": _redact_private(
            redact_provider_payload(provider_metadata)
        ),
        "response_sha256": fingerprint_text(raw_text),
        "response_excerpt": _bounded_redacted_excerpt(raw_text),
        "normalizations": list(normalizations or ()),
    }


def _write_live_evidence(
    output: Path,
    attempt_number: int,
    evidence: Mapping[str, Any] | None,
) -> None:
    if evidence is None:
        return
    atomic_write_text(
        output / f"live-attempt-{attempt_number:03d}.json",
        _pretty_json(_redact_private(redact_provider_payload(evidence))),
    )


def _pretty_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"


__all__ = [
    "MAX_CORRECTION_ATTEMPTS",
    "MAX_PROVIDER_RESPONSE_BYTES",
    "MAX_REQUEST_BYTES",
    "TEMPLATE_ID",
    "TEMPLATE_ID_0_2",
    "TEMPLATE_ID_0_3",
    "TEMPLATE_ID_0_4",
    "generate_repair_intent",
]
