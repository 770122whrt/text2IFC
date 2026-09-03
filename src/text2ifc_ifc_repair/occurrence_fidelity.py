"""Canonical Window/Opening occurrence snapshots and classified comparison."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from jsonschema import Draft202012Validator

from .semantic_facts import semantic_fact_key_token


SCHEMA_VERSION = "text2ifc/ifc-window-occurrence-comparison/0.1"
GENERIC_SCHEMA_VERSION = "text2ifc/ifc-occurrence-comparison/0.2"
CLASSIFICATIONS = (
    "matched",
    "not_in_user_text",
    "unsupported_authoring",
    "wrong_value",
    "ownership_only",
)
DEFAULT_DETAIL_LIMIT = 256
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class OccurrenceFact:
    fact_key: str
    value: Any
    value_type: str
    unit: str | None
    ownership: str
    owner_ref: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "ownership": self.ownership,
            "owner_ref": self.owner_ref,
        }


@dataclass(frozen=True)
class OccurrenceSnapshot:
    window_global_id: str
    window_name: str | None
    opening_global_id: str | None
    opening_name: str | None
    facts: Mapping[str, OccurrenceFact]

    def identity_dict(self) -> dict[str, Any]:
        return {
            "window_global_id": self.window_global_id,
            "window_name": self.window_name,
            "opening_global_id": self.opening_global_id,
            "opening_name": self.opening_name,
        }


@dataclass(frozen=True)
class GenericOccurrenceSnapshot:
    entity_global_id: str
    entity_name: str | None
    ifc_class: str
    scope: str
    role: str
    related_opening_global_id: str | None
    facts: Mapping[str, OccurrenceFact]

    def identity_dict(self) -> dict[str, Any]:
        return {
            "entity_global_id": self.entity_global_id,
            "entity_name": self.entity_name,
            "ifc_class": self.ifc_class,
            "scope": self.scope,
            "role": self.role,
            "related_opening_global_id": self.related_opening_global_id,
        }


def snapshot_window_occurrence(
    model: Any,
    window_global_id: str,
) -> OccurrenceSnapshot:
    """Snapshot effective scalar facts with direct-over-Type precedence."""

    window = model.by_guid(window_global_id)
    if window is None or not window.is_a("IfcWindow"):
        raise ValueError(f"WINDOW_MAPPING_INVALID:{window_global_id}")
    openings = {
        fill.RelatingOpeningElement.id(): fill.RelatingOpeningElement
        for fill in getattr(window, "FillsVoids", ())
    }
    if len(openings) > 1:
        raise ValueError(f"WINDOW_OPENING_MAPPING_AMBIGUOUS:{window_global_id}")
    opening = next(iter(openings.values()), None)
    facts: dict[str, OccurrenceFact] = {}
    _snapshot_attributes(window, "window_occurrence", facts)
    _snapshot_effective_properties(window, "window_occurrence", facts)
    _snapshot_quantities(window, "window_occurrence", facts)
    if opening is not None:
        _snapshot_attributes(opening, "opening_occurrence", facts)
        _snapshot_effective_properties(opening, "opening_occurrence", facts)
        _snapshot_quantities(opening, "opening_occurrence", facts)
        hosts = {
            str(relation.RelatingBuildingElement.GlobalId)
            for relation in getattr(opening, "VoidsElements", ())
        }
        if len(hosts) == 1:
            _put(
                facts,
                "opening_occurrence:relationship:host",
                next(iter(hosts)),
                "IfcGloballyUniqueId",
                None,
                "derived_relationship",
                f"guid:{opening.GlobalId}",
            )
    return OccurrenceSnapshot(
        window_global_id=str(window.GlobalId),
        window_name=_text(getattr(window, "Name", None)),
        opening_global_id=(
            None if opening is None else str(opening.GlobalId)
        ),
        opening_name=(
            None if opening is None else _text(getattr(opening, "Name", None))
        ),
        facts=dict(sorted(facts.items())),
    )


def snapshot_ifc_occurrence(
    model: Any,
    entity_global_id: str,
    *,
    scope: str,
    role: str,
) -> GenericOccurrenceSnapshot:
    """Snapshot one supported IFC occurrence without family-specific dispatch."""

    entity = model.by_guid(entity_global_id)
    if entity is None or entity.is_a() not in {
        "IfcWindow",
        "IfcDoor",
        "IfcOpeningElement",
    }:
        raise ValueError(f"OCCURRENCE_MAPPING_INVALID:{entity_global_id}")
    facts: dict[str, OccurrenceFact] = {}
    _snapshot_attributes(entity, scope, facts)
    _snapshot_effective_properties(entity, scope, facts)
    _snapshot_quantities(entity, scope, facts)
    opening = None
    if entity.is_a() in {"IfcWindow", "IfcDoor"}:
        openings = {
            fill.RelatingOpeningElement.id(): fill.RelatingOpeningElement
            for fill in getattr(entity, "FillsVoids", ())
        }
        if len(openings) > 1:
            raise ValueError(
                f"OCCURRENCE_OPENING_MAPPING_AMBIGUOUS:{entity_global_id}"
            )
        opening = next(iter(openings.values()), None)
        if opening is not None:
            hosts = {
                str(relation.RelatingBuildingElement.GlobalId)
                for relation in getattr(opening, "VoidsElements", ())
            }
            if len(hosts) == 1:
                _put(
                    facts,
                    f"{scope}:relationship:host",
                    next(iter(hosts)),
                    "IfcGloballyUniqueId",
                    None,
                    "derived_relationship",
                    f"guid:{opening.GlobalId}",
                )
    elif entity.is_a("IfcOpeningElement"):
        opening = entity
        hosts = {
            str(relation.RelatingBuildingElement.GlobalId)
            for relation in getattr(entity, "VoidsElements", ())
        }
        if len(hosts) == 1:
            _put(
                facts,
                f"{scope}:relationship:host",
                next(iter(hosts)),
                "IfcGloballyUniqueId",
                None,
                "derived_relationship",
                f"guid:{entity.GlobalId}",
            )
    return GenericOccurrenceSnapshot(
        entity_global_id=str(entity.GlobalId),
        entity_name=_text(getattr(entity, "Name", None)),
        ifc_class=entity.is_a(),
        scope=scope,
        role=role,
        related_opening_global_id=(
            None if opening is None else str(opening.GlobalId)
        ),
        facts=dict(sorted(facts.items())),
    )


def compare_occurrence_snapshots(
    *,
    expected: OccurrenceSnapshot,
    actual: OccurrenceSnapshot,
    authorization_ledger: Iterable[str] = (),
    authorization_ownership: Mapping[str, str] | None = None,
    required_fact_keys: Iterable[str] | None = None,
    complete_replication: bool = False,
    geometry_relationship_success: bool = True,
    source_hashes: Mapping[str, str | None] | None = None,
    detail_limit: int = DEFAULT_DETAIL_LIMIT,
    schema_version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    """Classify effective facts without treating identity as semantic truth."""

    if detail_limit < 1:
        raise ValueError("OCCURRENCE_DETAIL_LIMIT_INVALID")
    authorized = set(authorization_ledger)
    authorized_ownership = dict(authorization_ownership or {})
    required = (
        set(authorized)
        if required_fact_keys is None
        else set(required_fact_keys)
    )
    details: list[dict[str, Any]] = []
    keys = sorted(set(expected.facts) | set(actual.facts))
    for key in keys:
        left = expected.facts.get(key)
        right = actual.facts.get(key)
        is_required = key in required
        if (
            complete_replication
            and left is not None
            and key not in authorized
        ):
            classification = "not_in_user_text"
        elif left is None:
            classification = "not_in_user_text"
        elif right is None:
            classification = (
                "unsupported_authoring"
                if key in authorized
                else "not_in_user_text"
            )
        elif not _equivalent(left, right):
            classification = "wrong_value"
        elif (
            right.ownership != "occurrence_direct"
            and (
                authorized_ownership.get(key)
                or left.ownership
            )
            == "occurrence_direct"
        ):
            # A Type-inherited value cannot silently satisfy a Ground Truth
            # occurrence-direct requirement.
            classification = "unsupported_authoring"
        elif (
            left.ownership != right.ownership
            or left.owner_ref != right.owner_ref
        ):
            classification = "ownership_only"
        else:
            classification = "matched"
        details.append(
            {
                "fact_key": key,
                "classification": classification,
                "required": is_required,
                "expected": None if left is None else left.public_dict(),
                "actual": None if right is None else right.public_dict(),
            }
        )

    counts = {
        name: sum(item["classification"] == name for item in details)
        for name in CLASSIFICATIONS
    }
    blocking = {
        item["classification"]
        for item in details
        if item["required"]
    }
    semantic_success = not bool(
        blocking & {"unsupported_authoring", "wrong_value"}
    )
    occurrence_success = semantic_success and (
        not complete_replication or "not_in_user_text" not in blocking
    )
    report = {
        "schema_version": schema_version,
        "source_hashes": dict(source_hashes or {}),
        "mapping": {
            "expected": expected.identity_dict(),
            "actual": actual.identity_dict(),
        },
        "counts": counts,
        "details": details[:detail_limit],
        "truncated": len(details) > detail_limit,
        "detail_total": len(details),
        "geometry_relationship_success": bool(geometry_relationship_success),
        "semantic_fidelity_success": semantic_success,
        "occurrence_fidelity_success": (
            bool(geometry_relationship_success) and occurrence_success
        ),
        "authoring_exactness": counts["ownership_only"] == 0
        and expected.identity_dict() == actual.identity_dict(),
    }
    _validate_report(report)
    return report


def compare_window_occurrences(
    original_path: str | Path,
    repaired_path: str | Path,
    *,
    original_window_global_id: str,
    repaired_window_global_id: str,
    authorization_ledger: Iterable[str] = (),
    authorization_ownership: Mapping[str, str] | None = None,
    required_fact_keys: Iterable[str] | None = None,
    complete_replication: bool = False,
    geometry_relationship_success: bool = True,
    detail_limit: int = DEFAULT_DETAIL_LIMIT,
) -> dict[str, Any]:
    original = Path(original_path)
    repaired = Path(repaired_path)
    expected_model = ifcopenshell.open(str(original))
    repaired_model = ifcopenshell.open(str(repaired))
    return compare_occurrence_snapshots(
        expected=snapshot_window_occurrence(
            expected_model, original_window_global_id
        ),
        actual=snapshot_window_occurrence(
            repaired_model, repaired_window_global_id
        ),
        authorization_ledger=authorization_ledger,
        authorization_ownership=authorization_ownership,
        required_fact_keys=required_fact_keys,
        complete_replication=complete_replication,
        geometry_relationship_success=geometry_relationship_success,
        source_hashes={
            "original": _sha256(original),
            "repaired": _sha256(repaired),
        },
        detail_limit=detail_limit,
    )


def snapshot_from_semantic_facts(
    facts: Iterable[Any],
    *,
    window_global_id: str,
) -> OccurrenceSnapshot:
    """Project the public authorization ledger into comparator key space."""

    projected: dict[str, OccurrenceFact] = {}
    priorities: dict[str, int] = {}
    for fact in facts:
        key = str(fact.fact_key)
        category, separator, path = key.partition(":")
        if not separator:
            continue
        # This comparator owns occurrence attributes/Psets/quantities. Host,
        # Type, material and classification truth remain with their registered
        # L1/L2 checks and must not become impossible duplicate requirements.
        if category == "label":
            source_kind = getattr(
                getattr(fact, "source_kind", None),
                "value",
                str(getattr(fact, "source_kind", "")),
            )
            if source_kind != "explicit_request":
                continue
            key = f"attribute:{path}"
        elif category not in {"attribute", "pset", "quantity"}:
            continue
        if key.startswith(
            (
                "quantity:window-base.",
                "quantity:door-base.",
                "quantity:opening-base.",
            )
        ):
            key = key.replace(
                key.split(".", 1)[0] + ".",
                "quantity:BaseQuantities.",
                1,
            )
        scope = str(getattr(fact, "occurrence_scope", "window_occurrence"))
        scoped_key = (
            key
            if key.startswith(
                (
                    "window_occurrence:",
                    "door_occurrence:",
                    "opening_occurrence:",
                )
            )
            else f"{scope}:{key}"
        )
        source_kind = getattr(
            getattr(fact, "source_kind", None),
            "value",
            str(getattr(fact, "source_kind", "")),
        )
        priority = {
            "explicit_request": 3,
            "authorized_type_cohort": 2,
            "approved_prototype": 2,
            "deterministic_policy": 1,
        }.get(str(source_kind), 2)
        if priority < priorities.get(scoped_key, -1):
            continue
        projected[scoped_key] = OccurrenceFact(
            fact_key=scoped_key,
            value=_scalar(fact.value),
            value_type=str(fact.value_type or "IfcValue"),
            unit=_normalize_unit(fact.unit),
            ownership=(
                "type_inherited"
                if bool(getattr(fact, "inherited", False))
                else "occurrence_direct"
            ),
            owner_ref=str(fact.source_ref),
        )
        priorities[scoped_key] = priority
    return OccurrenceSnapshot(
        window_global_id=window_global_id,
        window_name=None,
        opening_global_id=None,
        opening_name=None,
        facts=dict(sorted(projected.items())),
    )


def _snapshot_attributes(
    entity: Any,
    scope: str,
    facts: dict[str, OccurrenceFact],
) -> None:
    attributes = (
        "Name",
        "ObjectType",
        "Tag",
        "OverallWidth",
        "OverallHeight",
    )
    for name in attributes:
        if not hasattr(entity, name):
            continue
        value = getattr(entity, name, None)
        if value is None:
            continue
        _put(
            facts,
            f"{scope}:attribute:{name}",
            _scalar(value),
            _attribute_type(entity, name, value),
            None,
            "occurrence_direct",
            f"guid:{entity.GlobalId}",
        )


def _snapshot_effective_properties(
    entity: Any,
    scope: str,
    facts: dict[str, OccurrenceFact],
) -> None:
    inherited: dict[tuple[str, str], tuple[Any, Any]] = {}
    direct: dict[tuple[str, str], tuple[Any, Any]] = {}
    for relation in getattr(entity, "IsDefinedBy", ()):
        if relation.is_a("IfcRelDefinesByType"):
            for pset in getattr(relation.RelatingType, "HasPropertySets", ()) or ():
                if pset.is_a("IfcPropertySet"):
                    for prop in pset.HasProperties:
                        if prop.is_a("IfcPropertySingleValue"):
                            inherited[(str(pset.Name), str(prop.Name))] = (
                                prop,
                                pset,
                            )
        elif relation.is_a("IfcRelDefinesByProperties"):
            pset = relation.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet"):
                for prop in pset.HasProperties:
                    if prop.is_a("IfcPropertySingleValue"):
                        direct[(str(pset.Name), str(prop.Name))] = (prop, pset)
    for (set_name, property_name), (prop, pset) in {
        **inherited,
        **direct,
    }.items():
        nominal = prop.NominalValue
        if nominal is None:
            continue
        ownership = (
            "occurrence_direct"
            if (set_name, property_name) in direct
            else "type_inherited"
        )
        _put(
            facts,
            (
                f"{scope}:pset:{semantic_fact_key_token(set_name)}."
                f"{semantic_fact_key_token(property_name)}"
            ),
            _scalar(nominal.wrappedValue),
            nominal.is_a(),
            _unit_token(getattr(prop, "Unit", None))
            or _implicit_project_unit(entity, nominal.is_a()),
            ownership,
            f"guid:{pset.GlobalId}",
        )


def _snapshot_quantities(
    entity: Any,
    scope: str,
    facts: dict[str, OccurrenceFact],
) -> None:
    for relation in getattr(entity, "IsDefinedBy", ()):
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        qto = relation.RelatingPropertyDefinition
        if not qto.is_a("IfcElementQuantity"):
            continue
        for quantity in qto.Quantities:
            if quantity.is_a("IfcQuantityLength"):
                value = quantity.LengthValue
            elif quantity.is_a("IfcQuantityArea"):
                value = quantity.AreaValue
            else:
                continue
            _put(
                facts,
                f"{scope}:quantity:{qto.Name}.{quantity.Name}",
                _scalar(value),
                quantity.is_a(),
                _unit_token(getattr(quantity, "Unit", None))
                or _implicit_project_unit(entity, quantity.is_a()),
                "occurrence_direct",
                f"guid:{qto.GlobalId}",
            )


def _put(
    facts: dict[str, OccurrenceFact],
    key: str,
    value: Any,
    value_type: str,
    unit: str | None,
    ownership: str,
    owner_ref: str,
) -> None:
    fact = OccurrenceFact(
        key,
        value,
        value_type,
        _normalize_unit(unit),
        ownership,
        owner_ref,
    )
    previous = facts.get(key)
    if previous is not None and previous != fact:
        raise ValueError(f"DUPLICATE_OCCURRENCE_FACT:{key}")
    facts[key] = fact


def _equivalent(left: OccurrenceFact, right: OccurrenceFact) -> bool:
    left_unit = _normalize_unit(left.unit)
    right_unit = _normalize_unit(right.unit)
    values_equal = left.value == right.value
    units_equivalent = left.unit is None or left_unit == right_unit
    if (
        isinstance(left.value, (int, float))
        and not isinstance(left.value, bool)
        and isinstance(right.value, (int, float))
        and not isinstance(right.value, bool)
        and left_unit is not None
        and right_unit is not None
    ):
        converted = _values_in_si(
            float(left.value), left_unit, float(right.value), right_unit
        )
        if converted is not None:
            values_equal = math.isclose(
                converted[0],
                converted[1],
                rel_tol=0.0,
                abs_tol=1e-9,
            )
            units_equivalent = True
    return (
        values_equal
        and left.value_type == right.value_type
        # A missing authorized unit means the source made no unit claim; it
        # must not reject a repaired value whose IFC graph resolves an
        # explicit/project unit. Explicit user units remain strict.
        and units_equivalent
    )


def _values_in_si(
    left_value: float,
    left_unit: str,
    right_value: float,
    right_unit: str,
) -> tuple[float, float] | None:
    scales = {
        "mm": (1, 1e-3),
        "cm": (1, 1e-2),
        "m": (1, 1.0),
        "mm2": (2, 1e-6),
        "cm2": (2, 1e-4),
        "m2": (2, 1.0),
        "mm3": (3, 1e-9),
        "cm3": (3, 1e-6),
        "m3": (3, 1.0),
    }
    left = scales.get(left_unit)
    right = scales.get(right_unit)
    if left is None or right is None or left[0] != right[0]:
        return None
    return left_value * left[1], right_value * right[1]


def _normalize_unit(unit: str | None) -> str | None:
    if unit is None:
        return None
    token = "".join(str(unit).strip().casefold().split())
    return {
        "millimetre": "mm",
        "millimeter": "mm",
        "metre": "m",
        "meter": "m",
        "squaremetre": "m2",
        "squaremeter": "m2",
        "m²": "m2",
    }.get(token, token)


def _unit_token(unit: Any) -> str | None:
    if unit is None:
        return None
    prefix = _text(getattr(unit, "Prefix", None))
    name = _text(getattr(unit, "Name", None))
    if prefix == "MILLI" and name == "METRE":
        return "mm"
    if name == "METRE":
        return "m"
    if prefix == "MILLI" and name == "SQUARE_METRE":
        return "mm2"
    if prefix == "CENTI" and name == "SQUARE_METRE":
        return "cm2"
    if name == "SQUARE_METRE":
        return "m2"
    if prefix == "MILLI" and name == "CUBIC_METRE":
        return "mm3"
    if prefix == "CENTI" and name == "CUBIC_METRE":
        return "cm3"
    if name == "CUBIC_METRE":
        return "m3"
    return ":".join(item for item in (prefix, name) if item) or unit.is_a()


def _implicit_project_unit(entity: Any, value_type: str) -> str | None:
    dimension = {
        "IfcQuantityLength": 1,
        "IfcLengthMeasure": 1,
        "IfcPositiveLengthMeasure": 1,
        "IfcQuantityArea": 2,
        "IfcAreaMeasure": 2,
        "IfcQuantityVolume": 3,
        "IfcVolumeMeasure": 3,
    }.get(value_type)
    if dimension is None:
        return None
    try:
        unit_type = (
            "LENGTHUNIT" if dimension == 1 else (
                "AREAUNIT" if dimension == 2 else "VOLUMEUNIT"
            )
        )
        has_explicit_unit = any(
            str(getattr(unit, "UnitType", "")) == unit_type
            for project in entity.file.by_type("IfcProject")
            if getattr(project, "UnitsInContext", None) is not None
            for unit in project.UnitsInContext.Units
        )
        scale = float(
            ifcopenshell.util.unit.calculate_unit_scale(entity.file, unit_type)
        )
        if dimension > 1 and not has_explicit_unit:
            scale = float(
                ifcopenshell.util.unit.calculate_unit_scale(
                    entity.file,
                    "LENGTHUNIT",
                )
            ) ** dimension
    except Exception:
        return None
    base = next(
        (
            token
            for value, token in ((1.0, "m"), (1e-2, "cm"), (1e-3, "mm"))
            if math.isclose(
                scale,
                value**dimension,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ),
        None,
    )
    if base is None:
        return None
    return base if dimension == 1 else f"{base}{dimension}"


def _attribute_type(entity: Any, name: str, value: Any) -> str:
    return {
        "Name": "IfcLabel",
        "ObjectType": "IfcLabel",
        "Tag": "IfcIdentifier",
        "OverallWidth": "IfcPositiveLengthMeasure",
        "OverallHeight": "IfcPositiveLengthMeasure",
    }.get(name, type(value).__name__)


def _scalar(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 9)
    if isinstance(value, (str, bool, int)) or value is None:
        return value
    return str(value)


def _text(value: Any) -> str | None:
    return None if value is None else str(value)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_report(report: Mapping[str, Any]) -> None:
    schema_name = (
        "ifc-occurrence-comparison-0.2.schema.json"
        if report.get("schema_version") == GENERIC_SCHEMA_VERSION
        else "ifc-window-occurrence-comparison-0.1.schema.json"
    )
    schema = json.loads(
        (
            ROOT
            / f"schemas/agent/{schema_name}"
        ).read_text(encoding="utf-8")
    )
    errors = list(Draft202012Validator(schema).iter_errors(report))
    if errors:
        raise ValueError(f"OCCURRENCE_REPORT_INVALID:{errors[0].message}")


__all__ = [
    "CLASSIFICATIONS",
    "OccurrenceFact",
    "GenericOccurrenceSnapshot",
    "OccurrenceSnapshot",
    "GENERIC_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "compare_occurrence_snapshots",
    "compare_window_occurrences",
    "snapshot_window_occurrence",
    "snapshot_ifc_occurrence",
    "snapshot_from_semantic_facts",
]
