from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, order=True)
class IfcValidationIssue:
    code: str
    entity: str
    attribute: str
    message: str


def open_ifc(path: str | Path) -> Any:
    raise NotImplementedError("IFC inspection is not implemented.")


def verify_ifc(source: Any) -> tuple[IfcValidationIssue, ...]:
    raise NotImplementedError("IFC verification is not implemented.")


def hierarchy_snapshot(source: Any) -> dict[str, Any]:
    raise NotImplementedError("Hierarchy inspection is not implemented.")


def containment_map(source: Any) -> dict[str, str]:
    raise NotImplementedError("Containment inspection is not implemented.")


def identity_map(source: Any) -> dict[str, str]:
    raise NotImplementedError("Identity inspection is not implemented.")

