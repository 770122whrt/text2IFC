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
import ifcopenshell.util.element
import ifcopenshell.util.unit

from jsonschema import Draft202012Validator

from .evaluation_policy import EvidenceSourceKind, SemanticApplicability
from .production_evidence import ProductionEvidence
from .registry import OperationRegistry
from .semantic_facts import SemanticFact, apply_effective_material_precedence


SEMANTIC_MANIFEST_SCHEMA_VERSION = "text2ifc/ifc-repair-semantic-manifest/0.1"
SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2 = "text2ifc/ifc-repair-semantic-manifest/0.2"
SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3 = "text2ifc/ifc-repair-semantic-manifest/0.3"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SEMANTIC_MANIFEST_SCHEMA_PATH = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-semantic-manifest-0.1.schema.json"
)
SEMANTIC_MANIFEST_SCHEMA_PATH_0_2 = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-semantic-manifest-0.2.schema.json"
)
SEMANTIC_MANIFEST_SCHEMA_PATH_0_3 = (
    PROJECT_ROOT / "schemas" / "agent" / "ifc-repair-semantic-manifest-0.3.schema.json"
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


class CanonicalSemanticSource(str, Enum):
    EXPLICIT_VALUE = "explicit_value"
    DETERMINISTIC_DERIVED = "deterministic_derived"
    TYPE_INHERITED = "type_inherited"
    APPROVED_OCCURRENCE_PROTOTYPE = "approved_occurrence_prototype"
    AUTHORIZED_TYPE_COHORT = "authorized_type_cohort"


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
    source_kind: EvidenceSourceKind | CanonicalSemanticSource
    source_ref: str
    provenance: tuple[str, ...]
    authoring_action: SemanticAuthoringAction
    scope: str = "window_occurrence"
    derivation: Mapping[str, Any] | None = None


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
) -> tuple[str, str, str, str, str]:
    """Return the operation-neutral deterministic assignment identity."""

    return (
        assignment.operation_id,
        assignment.scope,
        assignment.fact_key,
        assignment.ownership.value,
        assignment.authoring_action.value,
    )


def order_semantic_assignments(
    assignments: Sequence[SemanticAssignment],
) -> tuple[SemanticAssignment, ...]:
    """Deduplicate identical assignments, reject conflicts, and sort stably."""

    by_slot: dict[tuple[str, str, str], SemanticAssignment] = {}
    for assignment in assignments:
        slot = (
            assignment.operation_id,
            assignment.scope,
            assignment.fact_key,
        )
        previous = by_slot.get(slot)
        if previous is not None and previous != assignment:
            raise SemanticManifestError(
                "CONFLICTING_SEMANTIC_ASSIGNMENT", assignment.fact_key
            )
        by_slot[slot] = assignment
    return tuple(sorted(by_slot.values(), key=semantic_assignment_identity))


@lru_cache(maxsize=3)
def _cached_schema(version: str = SEMANTIC_MANIFEST_SCHEMA_VERSION) -> dict[str, Any]:
    path = {
        SEMANTIC_MANIFEST_SCHEMA_VERSION: SEMANTIC_MANIFEST_SCHEMA_PATH,
        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2: SEMANTIC_MANIFEST_SCHEMA_PATH_0_2,
        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3: SEMANTIC_MANIFEST_SCHEMA_PATH_0_3,
    }.get(version)
    if path is None:
        raise SemanticManifestError(
            "SEMANTIC_MANIFEST_SCHEMA_VERSION_MISMATCH", version
        )
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def load_semantic_manifest_schema(
    version: str = SEMANTIC_MANIFEST_SCHEMA_VERSION,
) -> dict[str, Any]:
    return copy.deepcopy(_cached_schema(version))


def parse_semantic_manifest(document: Any) -> SemanticManifest:
    if not isinstance(document, Mapping):
        raise SemanticManifestError("INVALID_SEMANTIC_MANIFEST", "expected object")
    version = str(document.get("schema_version"))
    if version not in {
        SEMANTIC_MANIFEST_SCHEMA_VERSION,
        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2,
        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3,
    }:
        raise SemanticManifestError(
            "SEMANTIC_MANIFEST_SCHEMA_VERSION_MISMATCH",
            repr(document.get("schema_version")),
        )
    assignments = document.get("assignments")
    if not isinstance(assignments, Sequence) or isinstance(assignments, (str, bytes)):
        raise SemanticManifestError("INVALID_SEMANTIC_ASSIGNMENTS", "expected array")
    operation_id = str(document.get("operation_id") or "")
    for index, payload in enumerate(assignments):
        _validate_assignment_semantics(
            payload,
            operation_id=operation_id,
            index=index,
            schema_version=version,
        )
    structural = sorted(
        Draft202012Validator(_cached_schema(version)).iter_errors(document),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if structural:
        error = structural[0]
        raise SemanticManifestError("SEMANTIC_MANIFEST_SCHEMA_INVALID", error.message)

    parsed = order_semantic_assignments(
        tuple(_parse_assignment(payload, schema_version=version) for payload in assignments)
    )
    policy = document["policy"]
    return SemanticManifest(
        schema_version=version,
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
                **(
                    {"scope": item.scope}
                    if manifest.schema_version in {
                        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2,
                        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3,
                    }
                    else {}
                ),
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
                **(
                    {"derivation": None if item.derivation is None else dict(item.derivation)}
                    if manifest.schema_version in {
                        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2,
                        SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3,
                    }
                    else {}
                ),
            }
            for item in manifest.assignments
        ],
    }


def semantic_manifest_expected_facts(
    manifest: SemanticManifest,
) -> tuple[SemanticFact, ...]:
    """Rehydrate public L2 authority for offline/private benchmark comparison."""

    return apply_effective_material_precedence(
        SemanticFact(
            fact_key=assignment.fact_key,
            value=copy.deepcopy(assignment.value),
            value_type=assignment.value_type,
            unit=assignment.unit,
            inherited=assignment.ownership is SemanticOwnership.TYPE_INHERITED,
            pset_path=(
                assignment.fact_key.partition(":")[2]
                if assignment.fact_key.startswith(("pset:", "quantity:"))
                else None
            ),
            entity_source=f"semantic-manifest:{manifest.operation_id}",
            source_kind=_legacy_source_kind(assignment.source_kind),
            source_ref=assignment.source_ref,
            provenance=assignment.provenance,
            occurrence_scope=assignment.scope,
            canonical_source_kind=(
                assignment.source_kind.value
                if isinstance(assignment.source_kind, CanonicalSemanticSource)
                else None
            ),
            derivation=assignment.derivation,
        )
        for assignment in manifest.assignments
    )


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
    use_v02 = any(
        fact.canonical_source_kind is not None for fact in facts
    )
    use_v03 = use_v02 and any(
        fact.occurrence_scope
        in {"door_occurrence", "beam_occurrence", "column_occurrence"}
        for fact in facts
    )
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
            if fact.fact_key == "relationship:type"
            or fact.source_kind
            in {
                EvidenceSourceKind.SURVIVING_TYPE,
                EvidenceSourceKind.APPROVED_PROTOTYPE,
            }
            else SemanticOwnership.OCCURRENCE_DIRECT
        )
        if fact.fact_key != "relationship:type" and fact.canonical_source_kind in {
            CanonicalSemanticSource.EXPLICIT_VALUE.value,
            CanonicalSemanticSource.DETERMINISTIC_DERIVED.value,
            CanonicalSemanticSource.APPROVED_OCCURRENCE_PROTOTYPE.value,
            CanonicalSemanticSource.AUTHORIZED_TYPE_COHORT.value,
        }:
            ownership = SemanticOwnership.OCCURRENCE_DIRECT
        source_kind = (
            _canonical_source_kind(fact)
            if use_v02
            else fact.source_kind.value
        )
        assignments.append(
            {
                "operation_id": operation_id,
                **({"scope": fact.occurrence_scope} if use_v02 else {}),
                "fact_key": fact.fact_key,
                "source_fact_key": source_fact_key,
                "value": copy.deepcopy(fact.value),
                "value_type": fact.value_type or "IfcValue",
                "unit": fact.unit,
                "ownership": ownership.value,
                "applicability": applicability.value,
                "source_kind": source_kind,
                "source_ref": fact.source_ref,
                "provenance": list(fact.provenance),
                "authoring_action": _authoring_action(
                    fact.fact_key, ownership
                ).value,
                **(
                    {
                        "derivation": (
                            None
                            if fact.derivation is None
                            else dict(fact.derivation)
                        )
                    }
                    if use_v02
                    else {}
                ),
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
            "schema_version": (
                SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3
                if use_v03
                else SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2
                if use_v02
                else SEMANTIC_MANIFEST_SCHEMA_VERSION
            ),
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
    modified_roles = {
        str(item.get("role")): str(item.get("global_id"))
        for item in application.get("modified", ())
    }
    target_id = created_roles.get(target_role) or modified_roles.get(target_role)
    if not target_id:
        raise SemanticManifestError("SEMANTIC_TARGET_ROLE_MISSING", target_role)
    target = model.by_guid(target_id)
    assignments = tuple(operation["semantic_assignments"])
    scopes = {
        str(item.get("scope", "window_occurrence"))
        for item in assignments
    }
    if len(scopes) > 1:
        raise SemanticManifestError(
            "SEMANTIC_SCOPE_CARDINALITY_INVALID",
            ",".join(sorted(scopes)),
        )
    scope = next(iter(scopes), "window_occurrence")
    scoped_role = lambda role: _scoped_semantic_role(role, scope)
    skipped: list[str] = []
    created: list[dict[str, str]] = []
    updated: list[dict[str, str]] = []
    modified: list[dict[str, str]] = []

    material_plans = _preflight_material_assignments(
        model=model,
        target=target,
        assignments=assignments,
    )
    skipped.extend(
        fact_key
        for plan in material_plans.values()
        if plan["skip"]
        for fact_key in plan["fact_keys"]
    )
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
    quantities: dict[str, dict[str, Mapping[str, Any]]] = {}
    for item in assignments:
        if item["ownership"] == SemanticOwnership.TYPE_INHERITED.value:
            continue
        category, path = str(item["fact_key"]).split(":", 1)
        if category == "pset":
            set_name, _ = _assignment_pset_path(item)
            psets.setdefault(set_name, []).append(item)
        elif category == "quantity":
            set_name, _ = path.rsplit(".", 1)
            canonical_set_name = (
                "BaseQuantities"
                if set_name in {"window-base", "door-base", "opening-base"}
                else set_name
            )
            quantity_name = path.rsplit(".", 1)[1]
            members = quantities.setdefault(canonical_set_name, {})
            previous = members.get(quantity_name)
            if previous is None or _quantity_assignment_priority(
                item
            ) > _quantity_assignment_priority(previous):
                members[quantity_name] = item

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
    pset_role_count = 0
    for set_name, members in sorted(psets.items()):
        direct = _direct_psets(target, set_name)
        if direct:
            pset = direct[0]
            relations = _direct_pset_relations(target, set_name)
            relation = relations[0]
            if len(relation.RelatedObjects) > 1:
                pset = ifcopenshell.util.element.copy_deep(
                    model,
                    pset,
                    exclude=("OwnerHistory",),
                )
                pset.GlobalId = _semantic_global_id(
                    operation,
                    f"semantic_pset_copy_on_write:{set_name}",
                )
                pset.OwnerHistory = owner_history
                relation.RelatedObjects = [
                    item for item in relation.RelatedObjects if item != target
                ]
                modified.append(
                    {
                        "role": scoped_role(
                            "semantic_shared_pset_relationship"
                        ),
                        "ifc_class": relation.is_a(),
                        "global_id": str(relation.GlobalId),
                    }
                )
                copied_relation = model.create_entity(
                    "IfcRelDefinesByProperties",
                    GlobalId=_semantic_global_id(
                        operation,
                        f"semantic_pset_relationship_copy_on_write:{set_name}",
                    ),
                    OwnerHistory=owner_history,
                    RelatedObjects=[target],
                    RelatingPropertyDefinition=pset,
                )
                created.extend(
                    (
                        {
                            "role": scoped_role(
                                "semantic_pset_copy_on_write"
                            ),
                            "ifc_class": pset.is_a(),
                            "global_id": str(pset.GlobalId),
                        },
                        {
                            "role": scoped_role(
                                "semantic_pset_relationship_copy_on_write"
                            ),
                            "ifc_class": copied_relation.is_a(),
                            "global_id": str(copied_relation.GlobalId),
                        },
                    )
                )
            else:
                modified.append(
                    {
                        "role": scoped_role("semantic_pset_updated"),
                        "ifc_class": pset.is_a(),
                        "global_id": str(pset.GlobalId),
                    }
                )
            by_name = {
                str(prop.Name): prop
                for prop in pset.HasProperties
            }
            appended = list(pset.HasProperties)
            for item in sorted(members, key=lambda value: value["fact_key"]):
                _, property_name = _assignment_pset_path(item)
                existing = by_name.get(property_name)
                if existing is None:
                    existing = model.create_entity(
                        "IfcPropertySingleValue",
                        Name=property_name,
                        NominalValue=_ifc_typed_value(model, item),
                        Unit=_ifc_assignment_unit(model, item),
                    )
                    appended.append(existing)
                    by_name[property_name] = existing
                    updated.append(
                        {
                            "role": scoped_role(
                                "semantic_pset_property_appended"
                            ),
                            "ifc_class": existing.is_a(),
                            "global_id": f"step:{existing.id()}",
                        }
                    )
                else:
                    existing.NominalValue = _ifc_typed_value(model, item)
                    existing.Unit = _ifc_assignment_unit(model, item)
                    updated.append(
                        {
                            "role": scoped_role(
                                "semantic_pset_property_updated"
                            ),
                            "ifc_class": existing.is_a(),
                            "global_id": f"step:{existing.id()}",
                        }
                    )
            pset.HasProperties = appended
            continue
        pset_role_count += 1
        role = scoped_role(
            "semantic_pset"
            if pset_role_count == 1
            else f"semantic_pset_{pset_role_count}"
        )
        relationship_role = scoped_role(
            "semantic_pset_relationship"
            if pset_role_count == 1
            else f"semantic_pset_relationship_{pset_role_count}"
        )
        pset = model.create_entity(
            "IfcPropertySet",
            GlobalId=_semantic_global_id(operation, f"{role}:{set_name}"),
            OwnerHistory=owner_history,
            Name=set_name,
            HasProperties=[
                model.create_entity(
                    "IfcPropertySingleValue",
                    Name=_assignment_pset_path(item)[1],
                    NominalValue=_ifc_typed_value(model, item),
                    Unit=_ifc_assignment_unit(model, item),
                )
                for item in sorted(members, key=lambda value: value["fact_key"])
            ],
        )
        relation = model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=_semantic_global_id(
                operation, f"{relationship_role}:{set_name}"
            ),
            OwnerHistory=owner_history,
            RelatedObjects=[target],
            RelatingPropertyDefinition=pset,
        )
        created.extend(
            (
                {"role": role, "ifc_class": pset.is_a(), "global_id": str(pset.GlobalId)},
                {"role": relationship_role, "ifc_class": relation.is_a(), "global_id": str(relation.GlobalId)},
            )
        )

    for set_name, members_by_name in sorted(quantities.items()):
        role = scoped_role("semantic_quantities")
        relationship_role = scoped_role(
            "semantic_quantity_relationship"
        )
        quantity_set_name = set_name
        quantity_entities = []
        for item in sorted(
            members_by_name.values(),
            key=lambda value: value["fact_key"],
        ):
            name = str(item["fact_key"]).rsplit(".", 1)[1]
            value_type = str(item["value_type"])
            if value_type in {"IfcQuantityArea", "IfcAreaMeasure"}:
                quantity_entities.append(
                    model.create_entity(
                        "IfcQuantityArea",
                        Name=name,
                        AreaValue=_quantity_value_in_project_units(
                            model, item, dimension=2
                        ),
                    )
                )
            elif value_type in {"IfcQuantityLength", "IfcLengthMeasure"}:
                quantity_entities.append(
                    model.create_entity(
                        "IfcQuantityLength",
                        Name=name,
                        LengthValue=_quantity_value_in_project_units(
                            model, item, dimension=1
                        ),
                    )
                )
            else:
                raise SemanticManifestError(
                    "SEMANTIC_QUANTITY_TYPE_UNSUPPORTED", value_type
                )
        quantity_set = model.create_entity(
            "IfcElementQuantity",
            GlobalId=_semantic_global_id(operation, f"{role}:{quantity_set_name}"),
            OwnerHistory=owner_history,
            Name=quantity_set_name,
            Quantities=quantity_entities,
        )
        relation = model.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=_semantic_global_id(
                operation,
                f"{relationship_role}:{quantity_set_name}",
            ),
            OwnerHistory=owner_history,
            RelatedObjects=[target],
            RelatingPropertyDefinition=quantity_set,
        )
        created.extend(
            (
                {"role": role, "ifc_class": quantity_set.is_a(), "global_id": str(quantity_set.GlobalId)},
                {"role": relationship_role, "ifc_class": relation.is_a(), "global_id": str(relation.GlobalId)},
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
        if action == SemanticAuthoringAction.REUSE_MATERIAL.value:
            plan = material_plans[source_ref]
            if plan["skip"]:
                continue
            resource = plan["resource"]
            if resource is None:
                resource = model.create_entity(
                    "IfcMaterial", Name=plan["create_label"]
                )
        else:
            resource = _resolve_public_resource(model, source_ref)
        scoped_base_role = scoped_role(base_role)
        role_counts[scoped_base_role] = role_counts.get(scoped_base_role, 0) + 1
        role = (
            scoped_base_role
            if role_counts[scoped_base_role] == 1
            else f"{scoped_base_role}_{role_counts[scoped_base_role]}"
        )
        relation = model.create_entity(
            ifc_class,
            GlobalId=_semantic_global_id(operation, role),
            OwnerHistory=owner_history,
            RelatedObjects=[target],
            **{attribute: resource},
        )
        created.append({"role": role, "ifc_class": relation.is_a(), "global_id": str(relation.GlobalId)})

    _verify_bound_relationships(model=model, target=target, assignments=assignments)
    return {
        "created": created,
        "modified": modified,
        "updated": updated,
        "skipped": skipped,
    }


def _preflight_direct_psets(
    target: Any, assignments: Sequence[Mapping[str, Any]]
) -> None:
    set_names = {
        _assignment_pset_path(item)[0]
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


def _preflight_material_assignments(
    *,
    model: Any,
    target: Any,
    assignments: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for item in assignments:
        if (
            item["ownership"] == SemanticOwnership.OCCURRENCE_DIRECT.value
            and item["authoring_action"]
            == SemanticAuthoringAction.REUSE_MATERIAL.value
        ):
            grouped.setdefault(str(item["source_ref"]), []).append(item)
    if len(grouped) > 1:
        raise SemanticManifestError(
            "STRUCTURAL_MATERIAL_CARDINALITY_INVALID",
            ",".join(sorted(grouped)),
        )
    if not grouped:
        return {}

    direct = [
        relation.RelatingMaterial
        for relation in getattr(target, "HasAssociations", ())
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    if len(direct) > 1:
        raise SemanticManifestError(
            "STRUCTURAL_DIRECT_MATERIAL_AMBIGUOUS", str(target.GlobalId)
        )
    type_relations = [
        relation
        for relation in getattr(target, "IsDefinedBy", ())
        if relation.is_a("IfcRelDefinesByType")
    ]
    if len(type_relations) > 1:
        raise SemanticManifestError(
            "STRUCTURAL_TYPE_RELATIONSHIP_AMBIGUOUS", str(target.GlobalId)
        )
    inherited = []
    if type_relations:
        inherited = [
            relation.RelatingMaterial
            for relation in type_relations[0].RelatingType.HasAssociations
            if relation.is_a("IfcRelAssociatesMaterial")
        ]
    if len(inherited) > 1:
        raise SemanticManifestError(
            "STRUCTURAL_TYPE_MATERIAL_AMBIGUOUS",
            str(type_relations[0].RelatingType.GlobalId),
        )

    plans: dict[str, dict[str, Any]] = {}
    for source_ref, members in grouped.items():
        facts = {str(item["fact_key"]) for item in members}
        values = {str(item["value"]) for item in members}
        if len(values) != 1:
            raise SemanticManifestError(
                "STRUCTURAL_MATERIAL_ASSIGNMENT_CONFLICT", source_ref
            )
        sample = members[0]
        resource, create_label = _resolve_exact_material_authority(
            model=model,
            assignment=sample,
        )
        plan = {
            "resource": resource,
            "create_label": create_label,
            "fact_keys": sorted(facts),
            "skip": False,
        }
        if direct:
            if _material_plan_matches(direct[0], plan):
                plan["skip"] = True
            else:
                raise SemanticManifestError(
                    "STRUCTURAL_MATERIAL_DIRECT_CONFLICT", source_ref
                )
        elif inherited:
            if _material_plan_matches(inherited[0], plan):
                plan["skip"] = True
            else:
                raise SemanticManifestError(
                    "STRUCTURAL_MATERIAL_TYPE_CONFLICT", source_ref
                )
        plans[source_ref] = plan
    return plans


def _resolve_exact_material_authority(
    *,
    model: Any,
    assignment: Mapping[str, Any],
) -> tuple[Any | None, str | None]:
    source_ref = str(assignment["source_ref"])
    if source_ref.startswith("resource:"):
        return _resolve_public_resource(model, source_ref), None
    if (
        str(assignment.get("source_kind"))
        not in {
            EvidenceSourceKind.EXPLICIT_REQUEST.value,
            CanonicalSemanticSource.EXPLICIT_VALUE.value,
        }
        or not source_ref.startswith("request:/")
        or str(assignment.get("value_type")) != "IfcMaterial"
        or not str(assignment.get("fact_key", "")).startswith("material:")
    ):
        raise SemanticManifestError(
            "SEMANTIC_MATERIAL_AUTHORITY_INVALID", source_ref
        )
    value = assignment.get("value")
    if not isinstance(value, str) or not value or value.strip() != value:
        raise SemanticManifestError(
            "SEMANTIC_MATERIAL_LABEL_INVALID", repr(value)
        )
    matches = [
        material
        for material in model.by_type("IfcMaterial")
        if str(getattr(material, "Name", "")) == value
    ]
    if len(matches) > 1:
        raise SemanticManifestError(
            "SEMANTIC_MATERIAL_LABEL_AMBIGUOUS", value
        )
    return (matches[0], None) if matches else (None, value)


def _material_plan_matches(resource: Any, plan: Mapping[str, Any]) -> bool:
    if plan["resource"] is not None:
        return resource == plan["resource"]
    return (
        resource.is_a("IfcMaterial")
        and str(getattr(resource, "Name", "")) == plan["create_label"]
    )


def _direct_psets(target: Any, set_name: str) -> list[Any]:
    return [
        relation.RelatingPropertyDefinition
        for relation in _direct_pset_relations(target, set_name)
    ]


def _direct_pset_relations(target: Any, set_name: str) -> list[Any]:
    return [
        relation
        for relation in getattr(target, "IsDefinedBy", ())
        if relation.is_a("IfcRelDefinesByProperties")
        and relation.RelatingPropertyDefinition.is_a("IfcPropertySet")
        and str(relation.RelatingPropertyDefinition.Name) == set_name
    ]


def _assignment_pset_path(
    assignment: Mapping[str, Any],
) -> tuple[str, str]:
    """Recover exact IFC names while keeping the comparison key normalized."""

    source_key = str(assignment.get("source_fact_key") or "")
    if (
        assignment.get("source_kind")
        in {
            EvidenceSourceKind.EXPLICIT_REQUEST.value,
            CanonicalSemanticSource.EXPLICIT_VALUE.value,
        }
        and source_key.startswith("pset:")
    ):
        path = source_key.removeprefix("pset:")
    else:
        path = str(assignment["fact_key"]).removeprefix("pset:")
    if "." not in path:
        raise SemanticManifestError("SEMANTIC_PSET_PATH_INVALID", path)
    return tuple(path.rsplit(".", 1))  # type: ignore[return-value]


def _ifc_typed_value(model: Any, assignment: Mapping[str, Any]) -> Any:
    value_type = str(assignment.get("value_type") or "IfcLabel")
    try:
        return model.create_entity(value_type, assignment["value"])
    except Exception as error:
        raise SemanticManifestError("SEMANTIC_VALUE_TYPE_UNSUPPORTED", value_type) from error


def _quantity_value_in_project_units(
    model: Any,
    assignment: Mapping[str, Any],
    *,
    dimension: int,
) -> float:
    value = float(assignment["value"])
    raw_unit = assignment.get("unit")
    if raw_unit is None:
        return value
    unit = str(raw_unit).strip().casefold().replace("²", "2")
    factors = (
        {"m": 1.0, "mm": 1e-3, "cm": 1e-2}
        if dimension == 1
        else {"m2": 1.0, "mm2": 1e-6, "cm2": 1e-4}
    )
    factor = factors.get(unit)
    if factor is None:
        raise SemanticManifestError(
            "SEMANTIC_QUANTITY_UNIT_UNSUPPORTED", str(raw_unit)
        )
    try:
        unit_type = "LENGTHUNIT" if dimension == 1 else "AREAUNIT"
        has_explicit_unit = any(
            str(getattr(unit, "UnitType", "")) == unit_type
            for project in model.by_type("IfcProject")
            if getattr(project, "UnitsInContext", None) is not None
            for unit in project.UnitsInContext.Units
        )
        project_unit_scale = float(
            ifcopenshell.util.unit.calculate_unit_scale(model, unit_type)
        )
        if dimension > 1 and not has_explicit_unit:
            project_unit_scale = float(
                ifcopenshell.util.unit.calculate_unit_scale(model, "LENGTHUNIT")
            ) ** dimension
    except Exception as error:
        raise SemanticManifestError(
            "SEMANTIC_PROJECT_UNIT_UNRESOLVED", type(error).__name__
        ) from error
    if project_unit_scale <= 0:
        raise SemanticManifestError(
            "SEMANTIC_PROJECT_UNIT_UNRESOLVED", repr(project_unit_scale)
        )
    return value * factor / project_unit_scale


def _quantity_assignment_priority(item: Mapping[str, Any]) -> int:
    """Prefer a user-authorized occurrence quantity over a derived default."""

    return (
        1
        if str(item.get("source_kind")) == "deterministic_derived"
        else 2
    )


def _ifc_assignment_unit(
    model: Any,
    assignment: Mapping[str, Any],
) -> Any | None:
    """Materialize an explicit SI unit for authored scalar Pset values."""

    raw = assignment.get("unit")
    if raw is None:
        return None
    token = str(raw).strip().casefold().replace("²", "2").replace("³", "3")
    definitions = {
        "m": ("LENGTHUNIT", None, "METRE"),
        "mm": ("LENGTHUNIT", "MILLI", "METRE"),
        "cm": ("LENGTHUNIT", "CENTI", "METRE"),
        "m2": ("AREAUNIT", None, "SQUARE_METRE"),
        "mm2": ("AREAUNIT", "MILLI", "SQUARE_METRE"),
        "cm2": ("AREAUNIT", "CENTI", "SQUARE_METRE"),
        "m3": ("VOLUMEUNIT", None, "CUBIC_METRE"),
        "mm3": ("VOLUMEUNIT", "MILLI", "CUBIC_METRE"),
        "cm3": ("VOLUMEUNIT", "CENTI", "CUBIC_METRE"),
    }
    definition = definitions.get(token)
    if definition is None:
        raise SemanticManifestError(
            "SEMANTIC_PROPERTY_UNIT_UNSUPPORTED", str(raw)
        )
    unit_type, prefix, name = definition
    for unit in model.by_type("IfcSIUnit"):
        if (
            str(getattr(unit, "UnitType", "")) == unit_type
            and getattr(unit, "Prefix", None) == prefix
            and str(getattr(unit, "Name", "")) == name
        ):
            return unit
    return model.create_entity(
        "IfcSIUnit",
        UnitType=unit_type,
        Prefix=prefix,
        Name=name,
    )


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


def _scoped_semantic_role(role: str, scope: str) -> str:
    prefixes = {
        "target_occurrence": None,
        "window_occurrence": None,
        "opening_occurrence": "opening",
        "door_occurrence": "door",
        "beam_occurrence": "beam",
        "column_occurrence": "column",
    }
    if scope not in prefixes:
        raise SemanticManifestError("SEMANTIC_SCOPE_UNSUPPORTED", scope)
    family = prefixes[scope]
    if family is None:
        return role
    prefix = "semantic_"
    suffix = role[len(prefix):] if role.startswith(prefix) else role
    return f"semantic_{family}_{suffix}"


def _validate_assignment_semantics(
    payload: Any,
    *,
    operation_id: str,
    index: int,
    schema_version: str,
) -> None:
    if not isinstance(payload, Mapping):
        raise SemanticManifestError("INVALID_SEMANTIC_ASSIGNMENT", str(index))
    if str(payload.get("operation_id") or "") != operation_id:
        raise SemanticManifestError(
            "CROSS_OPERATION_SEMANTIC_ASSIGNMENT", str(payload.get("operation_id"))
        )
    provenance = payload.get("provenance")
    if not isinstance(provenance, Sequence) or isinstance(provenance, (str, bytes)) or not provenance or any(not str(item).strip() for item in provenance):
        raise SemanticManifestError("MISSING_SEMANTIC_PROVENANCE", str(index))
    source_value = str(payload.get("source_kind"))
    try:
        source: EvidenceSourceKind | CanonicalSemanticSource = (
            CanonicalSemanticSource(source_value)
            if schema_version in {
                SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2,
                SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3,
            }
            else EvidenceSourceKind(source_value)
        )
    except ValueError as error:
        raise SemanticManifestError(
            "UNAUTHORIZED_SEMANTIC_SOURCE", str(payload.get("source_kind"))
        ) from error
    if isinstance(source, EvidenceSourceKind) and source not in _AUTHORIZED_SOURCES:
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
        source in {
            EvidenceSourceKind.EXPLICIT_REQUEST,
            CanonicalSemanticSource.EXPLICIT_VALUE,
        }
        and fact_kind == "pset"
        and (
            ownership != SemanticOwnership.OCCURRENCE_DIRECT.value
            or action != SemanticAuthoringAction.SET_OCCURRENCE_PSET.value
        )
    ):
        raise SemanticManifestError(
            "SEMANTIC_OWNERSHIP_ACTION_MISMATCH", fact_key
        )


def _parse_assignment(
    payload: Mapping[str, Any],
    *,
    schema_version: str,
) -> SemanticAssignment:
    source_value = str(payload["source_kind"])
    return SemanticAssignment(
        operation_id=str(payload["operation_id"]),
        fact_key=str(payload["fact_key"]),
        source_fact_key=str(payload["source_fact_key"]),
        value=copy.deepcopy(payload["value"]),
        value_type=str(payload["value_type"]),
        unit=None if payload["unit"] is None else str(payload["unit"]),
        ownership=SemanticOwnership(str(payload["ownership"])),
        applicability=SemanticApplicability(str(payload["applicability"])),
        source_kind=(
            CanonicalSemanticSource(source_value)
            if schema_version in {
                SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2,
                SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3,
            }
            else EvidenceSourceKind(source_value)
        ),
        source_ref=str(payload["source_ref"]),
        provenance=tuple(str(item) for item in payload["provenance"]),
        authoring_action=SemanticAuthoringAction(str(payload["authoring_action"])),
        scope=str(payload.get("scope", "window_occurrence")),
        derivation=(
            None
            if payload.get("derivation") is None
            else copy.deepcopy(dict(payload["derivation"]))
        ),
    )


def _legacy_source_kind(
    source: EvidenceSourceKind | CanonicalSemanticSource,
) -> EvidenceSourceKind:
    if isinstance(source, EvidenceSourceKind):
        return source
    return {
        CanonicalSemanticSource.EXPLICIT_VALUE: EvidenceSourceKind.EXPLICIT_REQUEST,
        CanonicalSemanticSource.DETERMINISTIC_DERIVED: EvidenceSourceKind.DETERMINISTIC_POLICY,
        CanonicalSemanticSource.TYPE_INHERITED: EvidenceSourceKind.SURVIVING_TYPE,
        CanonicalSemanticSource.APPROVED_OCCURRENCE_PROTOTYPE: EvidenceSourceKind.APPROVED_PROTOTYPE,
        CanonicalSemanticSource.AUTHORIZED_TYPE_COHORT: EvidenceSourceKind.AUTHORIZED_TYPE_COHORT,
    }[source]


def _canonical_source_kind(fact: SemanticFact) -> str:
    if fact.canonical_source_kind is not None:
        return CanonicalSemanticSource(fact.canonical_source_kind).value
    if (
        fact.fact_key == "relationship:type"
        and fact.source_kind is EvidenceSourceKind.DETERMINISTIC_POLICY
        and fact.derivation is not None
    ):
        return CanonicalSemanticSource.DETERMINISTIC_DERIVED.value
    if fact.inherited or fact.source_kind in {
        EvidenceSourceKind.SURVIVING_TYPE,
        EvidenceSourceKind.APPROVED_PROTOTYPE,
    }:
        return CanonicalSemanticSource.TYPE_INHERITED.value
    return {
        EvidenceSourceKind.EXPLICIT_REQUEST: CanonicalSemanticSource.EXPLICIT_VALUE,
        EvidenceSourceKind.AUTHORIZED_TYPE_COHORT: CanonicalSemanticSource.AUTHORIZED_TYPE_COHORT,
        EvidenceSourceKind.DETERMINISTIC_POLICY: CanonicalSemanticSource.DETERMINISTIC_DERIVED,
        EvidenceSourceKind.SURVIVING_TARGET: CanonicalSemanticSource.DETERMINISTIC_DERIVED,
        EvidenceSourceKind.SURVIVING_HOST: CanonicalSemanticSource.DETERMINISTIC_DERIVED,
    }.get(
        fact.source_kind,
        CanonicalSemanticSource.DETERMINISTIC_DERIVED,
    ).value


def _contains_non_finite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, Mapping):
        return any(_contains_non_finite(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_non_finite(item) for item in value)
    return False


__all__ = [
    "CanonicalSemanticSource",
    "SEMANTIC_MANIFEST_SCHEMA_VERSION",
    "SEMANTIC_MANIFEST_SCHEMA_VERSION_0_2",
    "SEMANTIC_MANIFEST_SCHEMA_VERSION_0_3",
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
    "semantic_manifest_expected_facts",
    "semantic_manifest_to_dict",
]
