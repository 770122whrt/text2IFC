"""Typed, Gold-free semantic compiler input for IFC repair operations."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatchcase
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence
import uuid

import ifcopenshell.guid

from jsonschema import Draft202012Validator

from .evaluation_policy import EvidenceSourceKind, SemanticApplicability
from .production_evidence import ProductionEvidence
from .registry import OperationRegistry


SEMANTIC_MANIFEST_SCHEMA_VERSION = "text2ifc/ifc-repair-semantic-manifest/0.1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_MANIFEST_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-semantic-manifest-0.1.schema.json"
)
_SUPPORTED_FACT_KINDS = frozenset(
    {"relationship", "attribute", "pset", "quantity", "material", "classification", "label"}
)
_AUTHORIZED_SOURCES = frozenset(
    {
        EvidenceSourceKind.EXPLICIT_REQUEST,
        EvidenceSourceKind.SURVIVING_TARGET,
        EvidenceSourceKind.SURVIVING_HOST,
        EvidenceSourceKind.SURVIVING_TYPE,
        EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
        EvidenceSourceKind.APPROVED_PROTOTYPE,
        EvidenceSourceKind.DETERMINISTIC_POLICY,
    }
)


class SemanticManifestError(ValueError):
    """Stable machine-readable semantic manifest failure."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class SemanticOwnership(str, Enum):
    OCCURRENCE_DIRECT = "occurrence_direct"
    TYPE_INHERITED = "type_inherited"


class SemanticAuthoringAction(str, Enum):
    SET_ATTRIBUTE = "set_attribute"
    SET_OCCURRENCE_PSET = "set_occurrence_pset"
    SET_QUANTITY = "set_quantity"
    REUSE_MATERIAL = "reuse_material"
    REUSE_CLASSIFICATION = "reuse_classification"
    BIND_RELATIONSHIP = "bind_relationship"
    INHERIT_FROM_TYPE = "inherit_from_type"


@dataclass(frozen=True)
class SemanticAssignment:
    operation_id: str
    fact_key: str
    source_fact_key: str
    value: Any
    value_type: str
    unit: str | None
    ownership: SemanticOwnership
    applicability: SemanticApplicability
    source_kind: EvidenceSourceKind
    source_ref: str
    provenance: tuple[str, ...]
    authoring_action: SemanticAuthoringAction


@dataclass(frozen=True)
class SemanticManifest:
    schema_version: str
    manifest_id: str
    operation_id: str
    operation_type: str
    base_model_fingerprint: str
    policy_id: str
    policy_version: str
    assignments: tuple[SemanticAssignment, ...]


def semantic_assignment_identity(
    assignment: SemanticAssignment,
) -> tuple[str, str, str, str]:
    """Return the operation-neutral deterministic assignment identity."""

    return (
        assignment.operation_id,
        assignment.fact_key,
        assignment.ownership.value,
        assignment.authoring_action.value,
    )


def order_semantic_assignments(
    assignments: Sequence[SemanticAssignment],
) -> tuple[SemanticAssignment, ...]:
    """Deduplicate identical assignments, reject conflicts, and sort stably."""

    by_slot: dict[tuple[str, str], SemanticAssignment] = {}
    for assignment in assignments:
        slot = (assignment.operation_id, assignment.fact_key)
        previous = by_slot.get(slot)
        if previous is not None and previous != assignment:
            raise SemanticManifestError(
                "CONFLICTING_SEMANTIC_ASSIGNMENT", assignment.fact_key
            )
        by_slot[slot] = assignment
    return tuple(sorted(by_slot.values(), key=semantic_assignment_identity))


@lru_cache(maxsize=1)
def _cached_schema() -> dict[str, Any]:
    schema = json.loads(SEMANTIC_MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_semantic_manifest_schema() -> dict[str, Any]:
    return copy.deepcopy(_cached_schema())


def parse_semantic_manifest(document: Any) -> SemanticManifest:
    if not isinstance(document, Mapping):
        raise SemanticManifestError("INVALID_SEMANTIC_MANIFEST", "expected object")
    if document.get("schema_version") != SEMANTIC_MANIFEST_SCHEMA_VERSION:
        raise SemanticManifestError(
            "SEMANTIC_MANIFEST_SCHEMA_VERSION_MISMATCH",
            repr(document.get("schema_version")),
        )
    assignments = document.get("assignments")
    if not isinstance(assignments, Sequence) or isinstance(assignments, (str, bytes)):
        raise SemanticManifestError("INVALID_SEMANTIC_ASSIGNMENTS", "expected array")
    operation_id = str(document.get("operation_id") or "")
    for index, payload in enumerate(assignments):
        _validate_assignment_semantics(payload, operation_id=operation_id, index=index)
    structural = sorted(
        Draft202012Validator(_cached_schema()).iter_errors(document),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if structural:
        error = structural[0]
        raise SemanticManifestError("SEMANTIC_MANIFEST_SCHEMA_INVALID", error.message)

    parsed = order_semantic_assignments(
        tuple(_parse_assignment(payload) for payload in assignments)
    )
    policy = document["policy"]
    return SemanticManifest(
        schema_version=SEMANTIC_MANIFEST_SCHEMA_VERSION,
        manifest_id=str(document["manifest_id"]),
        operation_id=operation_id,
        operation_type=str(document["operation_type"]),
        base_model_fingerprint=str(document["base_model_fingerprint"]),
        policy_id=str(policy["policy_id"]),
        policy_version=str(policy["policy_version"]),
        assignments=parsed,
    )


def semantic_manifest_to_dict(manifest: SemanticManifest) -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "manifest_id": manifest.manifest_id,
        "operation_id": manifest.operation_id,
        "operation_type": manifest.operation_type,
        "base_model_fingerprint": manifest.base_model_fingerprint,
        "policy": {
            "policy_id": manifest.policy_id,
            "policy_version": manifest.policy_version,
        },
        "assignments": [
            {
                "operation_id": item.operation_id,
                "fact_key": item.fact_key,
                "source_fact_key": item.source_fact_key,
                "value": copy.deepcopy(item.value),
                "value_type": item.value_type,
                "unit": item.unit,
                "ownership": item.ownership.value,
                "applicability": item.applicability.value,
                "source_kind": item.source_kind.value,
                "source_ref": item.source_ref,
                "provenance": list(item.provenance),
                "authoring_action": item.authoring_action.value,
            }
            for item in manifest.assignments
        ],
    }


def build_semantic_manifest(
    *,
    production_evidence: ProductionEvidence,
    operation_id: str,
    base_model_fingerprint: str,
    registry: OperationRegistry,
) -> SemanticManifest:
    """Compile the same authoritative facts used by L2 into authoring input."""

    try:
        operation_type = production_evidence.operation_types[operation_id]
        facts = production_evidence.expected_facts_by_operation[operation_id]
        decisions = production_evidence.applicability_by_operation[operation_id]
    except KeyError as error:
        raise SemanticManifestError(
            "SEMANTIC_MANIFEST_OPERATION_NOT_FOUND", operation_id
        ) from error
    policy = registry.require_evaluation_policy(operation_type)
    assignments: list[dict[str, Any]] = []
    for fact in facts:
        spec = next(
            (
                candidate
                for candidate in policy.semantic_facts
                if fnmatchcase(fact.fact_key, candidate.fact_pattern)
            ),
            None,
        )
        if spec is None:
            applicability = (
                SemanticApplicability.REQUIRED
                if fact.source_kind is EvidenceSourceKind.EXPLICIT_REQUEST
                else SemanticApplicability.CONDITIONAL
            )
        else:
            decision = decisions[spec.check_id]
            if decision.outcome != "evaluable":
                continue
            applicability = spec.applicability
        source_fact_key = next(
            (
                item.partition(":")[2]
                for item in fact.provenance
                if item.startswith("source_fact_key:")
            ),
            fact.fact_key,
        )
        ownership = (
            SemanticOwnership.TYPE_INHERITED
            if fact.source_kind
            in {
                EvidenceSourceKind.SURVIVING_TYPE,
                EvidenceSourceKind.APPROVED_PROTOTYPE,
            }
            else SemanticOwnership.OCCURRENCE_DIRECT
        )
        assignments.append(
            {
                "operation_id": operation_id,
                "fact_key": fact.fact_key,
                "source_fact_key": source_fact_key,
                "value": copy.deepcopy(fact.value),
                "value_type": fact.value_type or "IfcValue",
                "unit": fact.unit,
                "ownership": ownership.value,
                "applicability": applicability.value,
                "source_kind": fact.source_kind.value,
                "source_ref": fact.source_ref,
                "provenance": list(fact.provenance),
                "authoring_action": _authoring_action(
                    fact.fact_key, ownership
                ).value,
            }
        )
    identity = json.dumps(
        {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "base_model_fingerprint": base_model_fingerprint,
            "policy_id": policy.policy_id,
            "policy_version": policy.version,
            "assignments": assignments,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return parse_semantic_manifest(
        {
            "schema_version": SEMANTIC_MANIFEST_SCHEMA_VERSION,
            "manifest_id": f"semantic-manifest-{hashlib.sha256(identity).hexdigest()[:24]}",
            "operation_id": operation_id,
            "operation_type": operation_type,
            "base_model_fingerprint": base_model_fingerprint,
            "policy": {
                "policy_id": policy.policy_id,
                "policy_version": policy.version,
            },
            "assignments": assignments,
        }
    )


def _authoring_action(
    fact_key: str, ownership: SemanticOwnership
) -> SemanticAuthoringAction:
    if ownership is SemanticOwnership.TYPE_INHERITED:
        return SemanticAuthoringAction.INHERIT_FROM_TYPE
    category = fact_key.partition(":")[0]
    return {
        "relationship": SemanticAuthoringAction.BIND_RELATIONSHIP,
        "attribute": SemanticAuthoringAction.SET_ATTRIBUTE,
        "label": SemanticAuthoringAction.SET_ATTRIBUTE,
        "pset": SemanticAuthoringAction.SET_OCCURRENCE_PSET,
        "quantity": SemanticAuthoringAction.SET_QUANTITY,
        "material": SemanticAuthoringAction.REUSE_MATERIAL,
        "classification": SemanticAuthoringAction.REUSE_CLASSIFICATION,
    }[category]


def apply_semantic_assignments(
    *,
    model: Any,
    operation: Mapping[str, Any],
    application: Mapping[str, Any],
    target_role: str,
) -> dict[str, Any]:
    """Apply bound assignments through operation-neutral IFC2X3 graph primitives."""

    if operation.get("semantic_assignments") is None:
        return {"created": [], "skipped": []}
    created_roles = {
        str(item.get("role")): str(item.get("global_id"))
        for item in application.get("created", ())
    }
    target_id = created_roles.get(target_role)
    if not target_id:
        raise SemanticManifestError("SEMANTIC_TARGET_ROLE_MISSING", target_role)
    target = model.by_guid(target_id)
    assignments = tuple(operation["semantic_assignments"])
    skipped: list[str] = []
    created: list[dict[str, str]] = []
    updated: list[dict[str, str]] = []

    _preflight_direct_psets(target, assignments)

    for item in assignments:
        if item["ownership"] == SemanticOwnership.TYPE_INHERITED.value:
            skipped.append(str(item["fact_key"]))
            continue
        if item["authoring_action"] != SemanticAuthoringAction.SET_ATTRIBUTE.value:
            continue
        attribute = str(item["fact_key"]).split(":", 1)[1]
        if not hasattr(target, attribute):
            raise SemanticManifestError("SEMANTIC_ATTRIBUTE_UNSUPPORTED", attribute)
        setattr(target, attribute, item["value"])

    psets: dict[str, list[Mapping[str, Any]]] = {}
    quantities: dict[str, list[Mapping[str, Any]]] = {}
    for item in assignments:
        if item["ownership"] == SemanticOwnership.TYPE_INHERITED.value:
            continue
        category, path = str(item["fact_key"]).split(":", 1)
        if category == "pset":
            set_name, _ = path.rsplit(".", 1)
            psets.setdefault(set_name, []).append(item)
        elif category == "quantity":
            set_name, _ = path.rsplit(".", 1)
            quantities.setdefault(set_name, []).append(item)

    owner_history = getattr(target, "OwnerHistory", None)
    requires_owner_history = bool(psets or quantities) or any(
        item["ownership"] != SemanticOwnership.TYPE_INHERITED.value
        and str(item["authoring_action"])
        in {
            SemanticAuthoringAction.REUSE_MATERIAL.value,
            SemanticAuthoringAction.REUSE_CLASSIFICATION.value,
        }
        for item in assignments
    )
    if requires_owner_history and owner_history is None:
        raise SemanticManifestError("SEMANTIC_OWNER_HISTORY_MISSING", target_id)
    for set_name, members in sorted(psets.items()):
        direct = _direct_psets(target, set_name)
        if not direct and all(
            _inherited_property_matches(target, item) for item in members
        ):
            skipped.extend(str(item["fact_key"]) for item in members)
            continue
        if direct:
            pset = direct[0]
            by_name = {
                str(prop.Name): prop
                for prop in pset.HasProperties
            }
            appended = list(pset.HasProperties)
            for item in sorted(members, key=lambda value: value["fact_key"]):
                property_name = str(item["fact_key"]).rsplit(".", 1)[1]
                existing = by_name.get(property_name)
                if existing is None:
                    existing = model.create_entity(
                        "IfcPropertySingleValue",
                        Name=property_name,
                        NominalValue=_ifc_typed_value(model, item),
                    )
                    appended.append(existing)
                    by_name[property_name] = existing
                    updated.append(
                        {
                            "role": "semantic_pset_property_appended",
                            "ifc_class": existing.is_a(),
                            "global_id": f"step:{existing.id()}",
                        }
                    )
                else:
                    existing.NominalValue = _ifc_typed_value(model, item)
                    updated.append(
                        {
                            "role": "semantic_pset_property_updated",
                            "ifc_class": existing.is_a(),
                            "global_id": f"step:{existing.id()}",
                        }
                    )
            pset.HasProperties = appended
            continue
        role = "semantic_pset"
        pset = model.create_entity(
            "IfcPropertySet",
            GlobalId=_semantic_global_id(operation, f"{role}:{set_name}"),
            OwnerHistory=owner_history,
            Name=set_name,
            HasProperties=[
                model.create_entity(
                    "IfcPropertySingleValue",
                    Name=str(item["fact_key"]).rsplit(".", 1)[1],
                    NominalValue=_ifc_typed_value(model, item),
                )
                for item in sorted(members, key=lambda value: value["fact_key"])
            ],
        )
        relation = model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=_semantic_global_id(operation, f"{role}:relationship:{set_name}"),
            OwnerHistory=owner_history,
            RelatedObjects=[target],
            RelatingPropertyDefinition=pset,
        )
        created.extend(
            (
                {"role": role, "ifc_class": pset.is_a(), "global_id": str(pset.GlobalId)},
                {"role": "semantic_pset_relationship", "ifc_class": relation.is_a(), "global_id": str(relation.GlobalId)},
            )
        )

    for set_name, members in sorted(quantities.items()):
        role = "semantic_quantities"
        quantity_set_name = "BaseQuantities" if set_name == "window-base" else set_name
        quantity_entities = []
        for item in sorted(members, key=lambda value: value["fact_key"]):
            name = str(item["fact_key"]).rsplit(".", 1)[1]
            if name == "Area":
                quantity_entities.append(model.create_entity("IfcQuantityArea", Name=name, AreaValue=float(item["value"])))
            else:
                quantity_entities.append(model.create_entity("IfcQuantityLength", Name=name, LengthValue=float(item["value"])))
        quantity_set = model.create_entity(
            "IfcElementQuantity",
            GlobalId=_semantic_global_id(operation, f"{role}:{quantity_set_name}"),
            OwnerHistory=owner_history,
            Name=quantity_set_name,
            Quantities=quantity_entities,
        )
        relation = model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=_semantic_global_id(operation, f"{role}:relationship:{quantity_set_name}"),
            OwnerHistory=owner_history,
            RelatedObjects=[target],
            RelatingPropertyDefinition=quantity_set,
        )
        created.extend(
            (
                {"role": role, "ifc_class": quantity_set.is_a(), "global_id": str(quantity_set.GlobalId)},
                {"role": "semantic_quantity_relationship", "ifc_class": relation.is_a(), "global_id": str(relation.GlobalId)},
            )
        )

    association_actions = {
        SemanticAuthoringAction.REUSE_MATERIAL.value: (
            "IfcRelAssociatesMaterial", "RelatingMaterial", "semantic_material_relationship"
        ),
        SemanticAuthoringAction.REUSE_CLASSIFICATION.value: (
            "IfcRelAssociatesClassification", "RelatingClassification", "semantic_classification_relationship"
        ),
    }
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for item in assignments:
        action = str(item["authoring_action"])
        if item["ownership"] != SemanticOwnership.TYPE_INHERITED.value and action in association_actions:
            grouped.setdefault((action, str(item["source_ref"])), []).append(item)
    role_counts: dict[str, int] = {}
    for (action, source_ref), _ in sorted(grouped.items()):
        ifc_class, attribute, base_role = association_actions[action]
        role_counts[base_role] = role_counts.get(base_role, 0) + 1
        role = (
            base_role
            if role_counts[base_role] == 1
            else f"{base_role}_{role_counts[base_role]}"
        )
        resource = _resolve_public_resource(model, source_ref)
        relation = model.create_entity(
            ifc_class,
            GlobalId=_semantic_global_id(operation, role),
            OwnerHistory=owner_history,
            RelatedObjects=[target],
            **{attribute: resource},
        )
        created.append({"role": role, "ifc_class": relation.is_a(), "global_id": str(relation.GlobalId)})

    _verify_bound_relationships(model=model, target=target, assignments=assignments)
    return {"created": created, "updated": updated, "skipped": skipped}


def _preflight_direct_psets(
    target: Any, assignments: Sequence[Mapping[str, Any]]
) -> None:
    set_names = {
        str(item["fact_key"]).split(":", 1)[1].rsplit(".", 1)[0]
        for item in assignments
        if item["ownership"] == SemanticOwnership.OCCURRENCE_DIRECT.value
        and str(item["fact_key"]).startswith("pset:")
    }
    for set_name in sorted(set_names):
        direct = _direct_psets(target, set_name)
        if len(direct) > 1:
            raise SemanticManifestError(
                "DUPLICATE_DIRECT_PROPERTY_SET", set_name
            )
        if not direct:
            continue
        names = [str(prop.Name) for prop in direct[0].HasProperties]
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            raise SemanticManifestError(
                "DUPLICATE_DIRECT_PROPERTY", f"{set_name}.{duplicates[0]}"
            )


def _direct_psets(target: Any, set_name: str) -> list[Any]:
    return [
        relation.RelatingPropertyDefinition
        for relation in getattr(target, "IsDefinedBy", ())
        if relation.is_a("IfcRelDefinesByProperties")
        and relation.RelatingPropertyDefinition.is_a("IfcPropertySet")
        and str(relation.RelatingPropertyDefinition.Name) == set_name
    ]


def _inherited_property_matches(
    target: Any, assignment: Mapping[str, Any]
) -> bool:
    path = str(assignment["fact_key"]).split(":", 1)[1]
    set_name, property_name = path.rsplit(".", 1)
    matches: list[Any] = []
    for relation in getattr(target, "IsDefinedBy", ()):
        if not relation.is_a("IfcRelDefinesByType"):
            continue
        for pset in getattr(relation.RelatingType, "HasPropertySets", ()) or ():
            if not pset.is_a("IfcPropertySet") or str(pset.Name) != set_name:
                continue
            matches.extend(
                prop
                for prop in pset.HasProperties
                if str(prop.Name) == property_name
            )
    if len(matches) != 1:
        return False
    nominal = matches[0].NominalValue
    actual = None if nominal is None else nominal.wrappedValue
    actual_type = None if nominal is None else nominal.is_a()
    return (
        actual == assignment["value"]
        and actual_type == assignment["value_type"]
    )


def _ifc_typed_value(model: Any, assignment: Mapping[str, Any]) -> Any:
    value_type = str(assignment.get("value_type") or "IfcLabel")
    try:
        return model.create_entity(value_type, assignment["value"])
    except Exception as error:
        raise SemanticManifestError("SEMANTIC_VALUE_TYPE_UNSUPPORTED", value_type) from error


def _resolve_public_resource(model: Any, source_ref: str) -> Any:
    reference = source_ref.removeprefix("resource:")
    if reference.startswith("guid:"):
        resource = model.by_guid(reference.removeprefix("guid:"))
    elif reference.startswith("step:"):
        resource = model.by_id(int(reference.removeprefix("step:")))
    else:
        raise SemanticManifestError("SEMANTIC_RESOURCE_REF_INVALID", source_ref)
    if resource is None:
        raise SemanticManifestError("SEMANTIC_RESOURCE_NOT_FOUND", source_ref)
    return resource


def _verify_bound_relationships(*, model: Any, target: Any, assignments: Sequence[Mapping[str, Any]]) -> None:
    for item in assignments:
        if item["authoring_action"] != SemanticAuthoringAction.BIND_RELATIONSHIP.value:
            continue
        role = str(item["fact_key"]).split(":", 1)[1]
        expected = str(item["value"])
        if role == "host":
            actual = {
                str(relation.RelatingBuildingElement.GlobalId)
                for opening in target.FillsVoids
                for relation in opening.RelatingOpeningElement.VoidsElements
            }
        elif role == "storey":
            actual = {str(relation.RelatingStructure.GlobalId) for relation in target.ContainedInStructure}
        elif role == "type":
            actual = {
                str(relation.RelatingType.GlobalId)
                for relation in target.IsDefinedBy
                if relation.is_a("IfcRelDefinesByType")
            }
        else:
            raise SemanticManifestError("SEMANTIC_RELATIONSHIP_UNSUPPORTED", role)
        if actual != {expected}:
            raise SemanticManifestError("SEMANTIC_RELATIONSHIP_MISMATCH", f"{role}:{expected}")


def _semantic_global_id(operation: Mapping[str, Any], role: str) -> str:
    canonical = json.dumps(operation, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    value = uuid.uuid5(uuid.NAMESPACE_URL, f"https://text2ifc.local/ifc-repair/semantic/{role}/{canonical}")
    global_id = ifcopenshell.guid.compress(value.hex)
    return global_id


def _validate_assignment_semantics(payload: Any, *, operation_id: str, index: int) -> None:
    if not isinstance(payload, Mapping):
        raise SemanticManifestError("INVALID_SEMANTIC_ASSIGNMENT", str(index))
    if str(payload.get("operation_id") or "") != operation_id:
        raise SemanticManifestError(
            "CROSS_OPERATION_SEMANTIC_ASSIGNMENT", str(payload.get("operation_id"))
        )
    provenance = payload.get("provenance")
    if not isinstance(provenance, Sequence) or isinstance(provenance, (str, bytes)) or not provenance or any(not str(item).strip() for item in provenance):
        raise SemanticManifestError("MISSING_SEMANTIC_PROVENANCE", str(index))
    try:
        source = EvidenceSourceKind(str(payload.get("source_kind")))
    except ValueError as error:
        raise SemanticManifestError(
            "UNAUTHORIZED_SEMANTIC_SOURCE", str(payload.get("source_kind"))
        ) from error
    if source not in _AUTHORIZED_SOURCES:
        raise SemanticManifestError("UNAUTHORIZED_SEMANTIC_SOURCE", source.value)
    fact_key = str(payload.get("fact_key") or "")
    fact_kind = fact_key.partition(":")[0]
    if fact_kind not in _SUPPORTED_FACT_KINDS:
        raise SemanticManifestError("UNSUPPORTED_SEMANTIC_FACT_KIND", fact_key)
    if _contains_non_finite(payload.get("value")):
        raise SemanticManifestError("NON_FINITE_SEMANTIC_VALUE", fact_key)
    ownership = str(payload.get("ownership") or "")
    action = str(payload.get("authoring_action") or "")
    if (
        action == SemanticAuthoringAction.SET_OCCURRENCE_PSET.value
        and ownership != SemanticOwnership.OCCURRENCE_DIRECT.value
    ):
        raise SemanticManifestError(
            "SEMANTIC_OWNERSHIP_ACTION_MISMATCH", fact_key
        )
    if (
        source is EvidenceSourceKind.EXPLICIT_REQUEST
        and fact_kind == "pset"
        and (
            ownership != SemanticOwnership.OCCURRENCE_DIRECT.value
            or action != SemanticAuthoringAction.SET_OCCURRENCE_PSET.value
        )
    ):
        raise SemanticManifestError(
            "SEMANTIC_OWNERSHIP_ACTION_MISMATCH", fact_key
        )


def _parse_assignment(payload: Mapping[str, Any]) -> SemanticAssignment:
    return SemanticAssignment(
        operation_id=str(payload["operation_id"]),
        fact_key=str(payload["fact_key"]),
        source_fact_key=str(payload["source_fact_key"]),
        value=copy.deepcopy(payload["value"]),
        value_type=str(payload["value_type"]),
        unit=None if payload["unit"] is None else str(payload["unit"]),
        ownership=SemanticOwnership(str(payload["ownership"])),
        applicability=SemanticApplicability(str(payload["applicability"])),
        source_kind=EvidenceSourceKind(str(payload["source_kind"])),
        source_ref=str(payload["source_ref"]),
        provenance=tuple(str(item) for item in payload["provenance"]),
        authoring_action=SemanticAuthoringAction(str(payload["authoring_action"])),
    )


def _contains_non_finite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Mapping):
        return any(_contains_non_finite(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_non_finite(item) for item in value)
    return False


__all__ = [
    "SEMANTIC_MANIFEST_SCHEMA_VERSION",
    "SemanticAssignment",
    "SemanticAuthoringAction",
    "SemanticManifest",
    "SemanticManifestError",
    "SemanticOwnership",
    "load_semantic_manifest_schema",
    "build_semantic_manifest",
    "apply_semantic_assignments",
    "order_semantic_assignments",
    "parse_semantic_manifest",
    "semantic_assignment_identity",
    "semantic_manifest_to_dict",
]
