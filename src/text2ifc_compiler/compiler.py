import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from text2ifc_contract.validation import ValidationIssue
from text2ifc_contract.validation import validate_document

from .bootstrap import build_ifc
from .verification import IfcValidationIssue, verify_ifc


@dataclass(frozen=True)
class CompilationResult:
    output_path: Path | None = None
    input_issues: tuple[ValidationIssue, ...] = ()
    ifc_issues: tuple[IfcValidationIssue, ...] = ()

    @property
    def success(self) -> bool:
        return (
            self.output_path is not None
            and not self.input_issues
            and not self.ifc_issues
        )


def compile_document(
    document: Mapping[str, Any], output_path: str | Path
) -> CompilationResult:
    input_issues = tuple(validate_document(document))
    if input_issues:
        return CompilationResult(input_issues=input_issues)

    output = Path(output_path).resolve()
    bootstrap = build_ifc(document)
    ifc_issues = verify_ifc(bootstrap.ifc_file, express_rules=False)
    if ifc_issues:
        return CompilationResult(ifc_issues=ifc_issues)

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)

        bootstrap.ifc_file.write(str(temporary_path))
        reopened_issues = verify_ifc(temporary_path)
        if reopened_issues:
            return CompilationResult(ifc_issues=reopened_issues)

        os.replace(temporary_path, output)
        temporary_path = None
        return CompilationResult(output_path=output)
    except OSError as exc:
        return CompilationResult(
            ifc_issues=(
                IfcValidationIssue(
                    code="IFC_OUTPUT_ERROR",
                    entity="",
                    attribute=str(output),
                    message=f"{type(exc).__name__}: {exc}",
                ),
            )
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
