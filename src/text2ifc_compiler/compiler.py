from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from text2ifc_contract.validation import ValidationIssue

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
    raise NotImplementedError("Phase 2 compiler is not implemented.")
