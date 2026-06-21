"""Strict IFC2X3 artifact evidence and validation gate."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import ifcopenshell

from text2ifc_compiler.verification import verify_ifc


MAX_HEADER_BYTES = 4 * 1024 * 1024
FILE_SCHEMA_DECLARATION = re.compile(
    r"FILE_SCHEMA\s*\(\s*\((.*?)\)\s*\)\s*;",
    re.IGNORECASE | re.DOTALL,
)
QUOTED_IDENTIFIER = re.compile(r"'([^']+)'")


@dataclass(frozen=True)
class SchemaDeclarationEvidence:
    declaration_count: int
    identifiers: tuple[str, ...]


@dataclass(frozen=True)
class Ifc2x3ArtifactResult:
    success: bool
    declared_file_schema: str | None
    declared_schema_identifiers: tuple[str, ...]
    file_schema_declaration_count: int
    reopened_schema: str | None
    ifc_validation_error_count: int
    issues: tuple[dict[str, Any], ...]
    validation_errors: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["declared_schema_identifiers"] = list(
            self.declared_schema_identifiers
        )
        value["issues"] = list(self.issues)
        value["validation_errors"] = list(self.validation_errors)
        return value


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _header_text(path: Path) -> str:
    with path.open("rb") as stream:
        payload = stream.read(MAX_HEADER_BYTES)
    text = payload.decode("latin-1")
    header_start = re.search(r"\bHEADER\s*;", text, re.IGNORECASE)
    if not header_start:
        return text
    header_tail = text[header_start.end() :]
    header_end = re.search(r"\bENDSEC\s*;", header_tail, re.IGNORECASE)
    if not header_end:
        return text[header_start.start() :]
    return header_tail[: header_end.start()]


def parse_step_schema(path: str | Path) -> SchemaDeclarationEvidence:
    header = _header_text(Path(path))
    declarations = FILE_SCHEMA_DECLARATION.findall(header)
    identifiers = tuple(
        identifier.strip().upper()
        for declaration in declarations
        for identifier in QUOTED_IDENTIFIER.findall(declaration)
    )
    return SchemaDeclarationEvidence(
        declaration_count=len(declarations),
        identifiers=identifiers,
    )


def check_ifc2x3_artifact(path: str | Path) -> Ifc2x3ArtifactResult:
    artifact = Path(path)
    issues: list[dict[str, Any]] = []
    validation_errors: tuple[dict[str, Any], ...] = ()
    evidence = SchemaDeclarationEvidence(0, ())
    reopened_schema: str | None = None

    try:
        evidence = parse_step_schema(artifact)
    except OSError as exc:
        issues.append(
            _issue(
                "IFC_ARTIFACT_READ_FAILED",
                "/artifact",
                f"{type(exc).__name__}: {exc}",
            )
        )

    if evidence.declaration_count == 0:
        issues.append(
            _issue(
                "FILE_SCHEMA_MISSING",
                "/header/FILE_SCHEMA",
                "The STEP header has no FILE_SCHEMA declaration.",
            )
        )
    elif evidence.declaration_count != 1:
        issues.append(
            _issue(
                "FILE_SCHEMA_DECLARATION_COUNT",
                "/header/FILE_SCHEMA",
                "The STEP header must contain exactly one FILE_SCHEMA declaration.",
            )
        )
    if evidence.declaration_count == 1 and len(evidence.identifiers) != 1:
        issues.append(
            _issue(
                "FILE_SCHEMA_IDENTIFIER_COUNT",
                "/header/FILE_SCHEMA",
                "FILE_SCHEMA must contain exactly one schema identifier.",
            )
        )

    declared_schema = (
        evidence.identifiers[0]
        if evidence.declaration_count == 1
        and len(evidence.identifiers) == 1
        else None
    )
    if declared_schema is not None and declared_schema != "IFC2X3":
        issues.append(
            _issue(
                "DECLARED_SCHEMA_NOT_IFC2X3",
                "/header/FILE_SCHEMA/0",
                f"Declared schema is {declared_schema!r}, expected 'IFC2X3'.",
            )
        )

    model = None
    if declared_schema is not None:
        try:
            model = ifcopenshell.open(str(artifact))
            reopened_schema = str(model.schema).upper()
        except Exception as exc:
            issues.append(
                _issue(
                    "IFC_REOPEN_FAILED",
                    "/reopen",
                    f"{type(exc).__name__}: {exc}",
                )
            )

    if reopened_schema is not None and reopened_schema != "IFC2X3":
        issues.append(
            _issue(
                "REOPENED_SCHEMA_NOT_IFC2X3",
                "/reopen/schema",
                f"Reopened schema is {reopened_schema!r}, expected 'IFC2X3'.",
            )
        )
    if (
        declared_schema is not None
        and reopened_schema is not None
        and declared_schema != reopened_schema
    ):
        issues.append(
            _issue(
                "SCHEMA_DECLARATION_REOPEN_MISMATCH",
                "/schema",
                "The STEP declaration and reopened IfcOpenShell schema differ.",
            )
        )

    if model is not None:
        try:
            errors = verify_ifc(model)
            validation_errors = tuple(
                {
                    "code": item.code,
                    "entity": item.entity,
                    "attribute": item.attribute,
                    "message": item.message,
                }
                for item in errors
            )
        except Exception as exc:
            issues.append(
                _issue(
                    "IFC_VALIDATION_FAILED",
                    "/validation",
                    f"{type(exc).__name__}: {exc}",
                )
            )
        else:
            if validation_errors:
                issues.append(
                    _issue(
                        "IFC_VALIDATION_ERRORS",
                        "/validation",
                        (
                            f"Full IFC/EXPRESS validation reported "
                            f"{len(validation_errors)} error(s)."
                        ),
                    )
                )

    return Ifc2x3ArtifactResult(
        success=not issues,
        declared_file_schema=declared_schema,
        declared_schema_identifiers=evidence.identifiers,
        file_schema_declaration_count=evidence.declaration_count,
        reopened_schema=reopened_schema,
        ifc_validation_error_count=len(validation_errors),
        issues=tuple(issues),
        validation_errors=validation_errors,
    )
