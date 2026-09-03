from __future__ import annotations

from dataclasses import replace

import pytest

from text2ifc_ifc_repair.index_models import (
    AliasFact,
    ElementRecord,
    PropertyFact,
    TypeRecord,
)
from text2ifc_ifc_repair.indexer import normalize_alias
from text2ifc_ifc_repair.occurrence_semantics import (
    FactPolicy,
    OccurrenceSemanticSource,
    derive_geometry_assignments,
    expand_semantic_bundles,
    explicit_assignments,
    fact_policy,
    resolve_occurrence_reuse,
)
from text2ifc_ifc_repair.repair_intent import (
    OccurrenceReuseIntent,
    OccurrenceSemanticBundle,
    OperationIntent,
)


def _source(text: str = "copy this occurrence") -> dict:
    return {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": text,
    }


def _property(name: str, value: object, *, unit: str | None = None) -> PropertyFact:
    return PropertyFact(
        set_kind="pset",
        set_name="Pset_WindowCommon",
        property_name=name,
        value=value,
        value_type="IfcLabel" if isinstance(value, str) else "IfcBoolean",
        unit=unit,
        inherited=False,
        provenance=f"IfcPropertySingleValue:{name}",
    )


def _record(
    guid: str,
    name: str,
    type_guid: str = "TYPE-GUID",
    properties: tuple[PropertyFact, ...] = (),
) -> ElementRecord:
    return ElementRecord(
        record_id=f"ifc:{guid}",
        ifc_global_id=guid,
        identity_reliable=True,
        ifc_class="IfcWindow",
        name=name,
        long_name=None,
        tag=None,
        object_type=None,
        type_name="Window Type A",
        type_global_id=type_guid,
        storey_name="Level 1",
        storey_global_id="STOREY",
        geometry_capability="rectilinear",
        aliases=(
            AliasFact(normalize_alias(name), name, "name", "IfcRoot.Name"),
        ),
        properties=properties,
    )


class Repository:
    def __init__(
        self,
        records: tuple[ElementRecord, ...],
        types: tuple[TypeRecord, ...] = (),
    ) -> None:
        self.records = records
        self.types = types

    def get_by_global_id(self, guid: str):
        return next((item for item in self.records if item.ifc_global_id == guid), None)

    def find_aliases(self, value: str):
        return [
            item
            for item in self.records
            if any(alias.normalized_value == value for alias in item.aliases)
        ]

    def iter_records(self):
        return iter(self.records)

    def get_type_by_global_id(self, guid: str):
        return next((item for item in self.types if item.ifc_global_id == guid), None)

    def find_type_aliases(self, value: str):
        return [
            item
            for item in self.types
            if any(alias.normalized_value == value for alias in item.aliases)
        ]


def _reuse(
    *,
    mode: str = "exact_occurrence",
    kind: str = "global_id",
    reference: str = "WINDOW-1",
) -> OccurrenceReuseIntent:
    return OccurrenceReuseIntent.from_dict(
        {
            "mode": mode,
            "reference_kind": kind,
            "reference": reference,
            "include_patterns": ["Pset_WindowCommon.*"],
            "source": _source(),
        }
    )


def _operation() -> OperationIntent:
    return OperationIntent.from_dict(
        {
            "operation_id": "op-1",
            "operation_type": "add_window_with_opening_to_wall",
            "target_query": {
                "schema_version": "text2ifc/ifc-target-query/0.1",
                "allowed_ifc_classes": ["IfcWall"],
                "names": ["North wall"],
            },
            "parameters": {
                "position": {
                    "reference": "wall_local_start",
                    "center_offset_mm": 1000.0,
                },
                "opening": {
                    "width_mm": 1000.0,
                    "height_mm": 2000.0,
                    "sill_height_mm": 900.0,
                },
                "window": {"fit_opening": True},
            },
            "attribute_intents": [],
            "property_intents": [],
            "semantic_bundle_refs": [],
            "quantity_intents": [],
            "occurrence_reuse_intent": None,
            "prototype_intent": None,
            "provenance": [_source()],
        }
    )


def _type() -> TypeRecord:
    return TypeRecord(
        record_id="type:TYPE-GUID",
        ifc_global_id="TYPE-GUID",
        identity_reliable=True,
        ifc_class="IfcWindowStyle",
        name="Window Type A",
        applicable_occurrence=None,
        predefined_type=None,
        element_type=None,
        aliases=(
            AliasFact(
                normalize_alias("Window Type A"),
                "Window Type A",
                "name",
                "IfcTypeObject.Name",
            ),
        ),
    )


@pytest.mark.parametrize("kind,reference", [("global_id", "WINDOW-1"), ("name", "A-101")])
def test_exact_occurrence_resolves_guid_or_exact_name(kind: str, reference: str) -> None:
    repository = Repository(
        (_record("WINDOW-1", "A-101", properties=(_property("IsExternal", True),)),)
    )
    result = resolve_occurrence_reuse(
        repository, _reuse(kind=kind, reference=reference), operation_id="op-1"
    )
    assert result.status == "resolved"
    assert result.assignments[0].source_kind is OccurrenceSemanticSource.APPROVED_OCCURRENCE_PROTOTYPE


@pytest.mark.parametrize(
    "records,reason",
    [
        ((), "OCCURRENCE_REFERENCE_NOT_FOUND"),
        (
            (_record("WINDOW-1", "A-101"), _record("WINDOW-2", "A-101")),
            "OCCURRENCE_REFERENCE_AMBIGUOUS",
        ),
    ],
)
def test_exact_name_fails_closed(records, reason: str) -> None:
    result = resolve_occurrence_reuse(
        Repository(records),
        _reuse(kind="name", reference="A-101"),
        operation_id="op-1",
    )
    assert result.status == "clarification_required"
    assert result.reason_code == reason


def test_unanimous_type_cohort_resolves_and_conflicts_clarify() -> None:
    first = _record(
        "WINDOW-1", "A-101", properties=(_property("AcousticRating", "Rw35"),)
    )
    second = _record(
        "WINDOW-2", "A-102", properties=(_property("AcousticRating", "Rw35"),)
    )
    repository = Repository((first, second), (_type(),))
    reuse = _reuse(
        mode="same_type_consensus",
        kind="type_global_id",
        reference="TYPE-GUID",
    )
    resolved = resolve_occurrence_reuse(repository, reuse, operation_id="op-1")
    assert resolved.status == "resolved"
    assert resolved.assignments[0].source_kind is OccurrenceSemanticSource.AUTHORIZED_TYPE_COHORT

    mixed_value = Repository(
        (
            first,
            replace(
                second,
                properties=(_property("AcousticRating", "Rw40"),),
            ),
        ),
        (_type(),),
    )
    conflict = resolve_occurrence_reuse(
        mixed_value, reuse, operation_id="op-1"
    )
    assert conflict.status == "clarification_required"
    assert conflict.reason_code == "TYPE_COHORT_FACT_CONFLICT"
    assert not conflict.assignments


def test_empty_cohort_and_mixed_unit_fail_closed() -> None:
    reuse = _reuse(
        mode="same_type_consensus",
        kind="type_global_id",
        reference="TYPE-GUID",
    )
    empty = resolve_occurrence_reuse(
        Repository((), (_type(),)), reuse, operation_id="op-1"
    )
    assert empty.reason_code == "TYPE_COHORT_EMPTY"

    records = (
        _record("WINDOW-1", "A", properties=(_property("Rating", "35", unit="dB"),)),
        _record("WINDOW-2", "B", properties=(_property("Rating", "35", unit="Pa"),)),
    )
    mixed = resolve_occurrence_reuse(
        Repository(records, (_type(),)), reuse, operation_id="op-1"
    )
    assert mixed.reason_code == "TYPE_COHORT_FACT_CONFLICT"


def test_contextual_facts_are_excluded_and_geometry_is_derived() -> None:
    assert fact_policy("Pset_WindowCommon.GlobalId") is FactPolicy.IDENTITY_CONTEXTUAL
    assert fact_policy("Constraints.Level") is FactPolicy.HOST_STOREY_DERIVED
    assert fact_policy("BaseQuantities.Width") is FactPolicy.GEOMETRY_DERIVED

    repository = Repository(
        (
            _record(
                "WINDOW-1",
                "A",
                properties=(
                    _property("GlobalId", "must-not-copy"),
                    _property("AcousticRating", "Rw35"),
                ),
            ),
        )
    )
    result = resolve_occurrence_reuse(
        repository, _reuse(), operation_id="op-1"
    )
    assert [item.fact_key for item in result.assignments] == [
        "pset:Pset_WindowCommon.AcousticRating"
    ]
    derived = derive_geometry_assignments(_operation())
    assert {item.fact_key for item in derived} >= {
        "quantity:window-base.Width",
        "quantity:window-base.Height",
        "quantity:window-base.Area",
    }
    assert all(
        item.source_kind is OccurrenceSemanticSource.DETERMINISTIC_DERIVED
        for item in derived
    )
    by_key = {item.fact_key: item for item in derived}
    assert by_key["quantity:window-base.Width"].value == 1000.0
    assert by_key["quantity:window-base.Width"].unit == "mm"
    assert by_key["quantity:window-base.Area"].value == 2_000_000.0
    assert by_key["quantity:window-base.Area"].unit == "mm2"


def test_window_policy_omits_managed_quantities_without_inventing_sill_qto() -> None:
    from text2ifc_ifc_repair.operations import create_default_registry

    operation = _operation()
    authorized = [
        item.to_dict() for item in derive_geometry_assignments(operation)
    ]
    payload = {
        "operation_id": operation.operation_id,
        "operation_type": operation.operation_type,
        "parameters": operation.parameters,
        "authorized_semantics": authorized,
    }
    facts = create_default_registry().build_semantic_policy_facts(
        operation.operation_type,
        operation=payload,
    )

    assert {item.fact_key for item in facts} == {
        "attribute:OverallWidth",
        "attribute:OverallHeight",
    }
    assert {
        item.canonical_source_kind for item in facts
    } == {"deterministic_derived"}
    assert all(
        item["fact_key"] != "quantity:window-base.SillHeight"
        for item in authorized
    )


def test_bundle_expansion_is_ordered_and_operation_local_override_wins() -> None:
    base = _operation()
    bundle = OccurrenceSemanticBundle.from_dict(
        {
            "bundle_id": "b1",
            "property_intents": [
                {
                    "intent_kind": "exact_property",
                    "set_name": "Pset_WindowCommon",
                    "property_name": "IsExternal",
                    "raw_value": False,
                    "raw_unit": None,
                    "requested_value_type": "IfcBoolean",
                    "scope": "occurrence_direct",
                    "source": _source(),
                }
            ],
            "quantity_intents": [],
            "provenance": [_source()],
        }
    )
    operation_doc = base.to_dict()
    operation_doc["semantic_bundle_refs"] = ["b1"]
    operation_doc["property_intents"] = [
        {
            **bundle.property_intents[0].to_dict(),
            "raw_value": True,
        }
    ]
    operation = OperationIntent.from_dict(operation_doc)

    properties, _ = expand_semantic_bundles(operation, (bundle,))
    assert properties[0].value is True
    assignments = explicit_assignments(operation, (bundle,))
    assert assignments[0].value is True
