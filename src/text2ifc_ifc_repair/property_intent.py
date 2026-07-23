"""Operation-neutral exact IFC property intent contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .repair_intent import PublicProvenance


class PropertyResolutionStatus(str, Enum):
    """Deterministic outcomes used by the exact-property resolver."""

    STANDARD_RESOLVED = "standard_resolved"
    CUSTOM_CONFIRMATION_REQUIRED = "custom_confirmation_required"
    CLARIFICATION_REQUIRED = "clarification_required"


@dataclass(frozen=True)
class ExactPropertyIntent:
    """A claim copied from public user text, never an authorization."""

    set_name: str | None
    property_name: str | None
    value: Any
    requested_value_type: str | None
    requested_unit: str | None
    scope: str | None
    source: "PublicProvenance"
    intent_kind: str = "pset_property"

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ExactPropertyIntent":
        from .repair_intent import PublicProvenance

        return cls(
            set_name=_optional_text(value["set_name"]),
            property_name=_optional_text(value["property_name"]),
            value=value["value"],
            requested_value_type=_optional_text(value["requested_value_type"]),
            requested_unit=_optional_text(value["requested_unit"]),
            scope=_optional_text(value["scope"]),
            source=PublicProvenance.from_dict(value["source"]),
        )

    @property
    def missing_fields(self) -> tuple[str, ...]:
        missing: list[str] = []
        if self.set_name is None:
            missing.append("set_name")
        if self.property_name is None:
            missing.append("property_name")
        if self.value is None:
            missing.append("value")
        return tuple(missing)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_kind": self.intent_kind,
            "set_name": self.set_name,
            "property_name": self.property_name,
            "value": self.value,
            "requested_value_type": self.requested_value_type,
            "requested_unit": self.requested_unit,
            "scope": self.scope,
            "source": self.source.to_dict(),
        }


def _optional_text(value: Any) -> str | None:
    return None if value is None else str(value)


__all__ = [
    "ExactPropertyIntent",
    "PropertyResolutionStatus",
]
