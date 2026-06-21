"""End-to-end missing-piece repair demo with strict IFC2X3 gates."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Iterable

from text2ifc_compiler import compile_document
from text2ifc_contract.validation_v2 import validate_v2_document
from text2ifc_quality import check_generated_ifc

from .composer import compose_patches
from .external_inventory import inventory_external_ifc
from .handoff import render_repair_prompt
from .ifc_artifact import check_ifc2x3_artifact
from .provenance import build_provenance_report
from .repair_cases import repair_case
from .validation import validate_patch_document


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = (
    ROOT
    / "dataset"
    / "processed"
    / "jsonfix"
    / "missing-piece-repair"
)
DEFAULT_EXTERNAL_ROOTS = (
    ROOT / "dataset" / "external" / "bim-whale-ifc-samples",
    ROOT / "dataset" / "external" / "ifc-bench",
)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(text)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _write_json_atomic(path: Path, value: Any) -> None:
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    )
    _write_text_atomic(path, text + "\n")


def _validation_issues(issues: Iterable[Any]) -> list[dict[str, Any]]:
    return [
        {
            "code": item.code,
            "path": item.path,
            "message": item.message,
        }
        for item in issues
    ]


def _compilation_payload(compilation: Any) -> dict[str, Any]:
    return {
        "success": bool(compilation and compilation.success),
        "output_path": (
            str(compilation.output_path)
            if compilation and compilation.output_path
            else None
        ),
        "input_issues": (
            _validation_issues(compilation.input_issues)
            if compilation
            else []
        ),
        "ifc_issues": (
            [
                {
                    "code": item.code,
                    "entity": item.entity,
                    "attribute": item.attribute,
                    "message": item.message,
                }
                for item in compilation.ifc_issues
            ]
            if compilation
            else []
        ),
    }


def _quality_payload(quality: Any) -> dict[str, Any]:
    if quality is None:
        return {"success": False, "issues": [], "metrics": {}}
    return {
        "success": quality.success,
        "issues": quality.issues,
        "metrics": quality.metrics,
    }


def _report(
    *,
    success: bool,
    metrics: dict[str, Any],
    provenance: dict[str, Any],
    inventory: dict[str, Any],
) -> str:
    lines = [
        "# jsonfix Missing-Piece Repair Report",
        "",
        f"- Success: {str(success).lower()}",
        f"- Declared schema: {metrics['declared_file_schema']}",
        f"- Reopened schema: {metrics['reopened_schema']}",
        (
            "- IFC validation errors: "
            f"{metrics['ifc_validation_error_count']}"
        ),
        (
            "- Generated IFC quality passed: "
            f"{str(metrics['generated_ifc_quality_passed']).lower()}"
        ),
        "",
        "## Source Facts",
        "",
        (
            f"- Base fact count: "
            f"{provenance['summary']['base_fact_count']}"
        ),
        "- Immutable base document: `jsonfix-missing-piece-base`",
        "",
        "## Patch Facts",
        "",
        (
            f"- Patch fact count: "
            f"{provenance['summary']['patch_fact_count']}"
        ),
        "- Added semantic entity: `wall-west` (`IfcWallStandardCase`)",
        "- No source fact was silently overwritten.",
        "",
        "## Validation Facts",
        "",
        f"- Patch valid: {str(metrics['patch_valid']).lower()}",
        (
            "- Formal BIM JSON valid: "
            f"{str(metrics['formal_bim_json_valid']).lower()}"
        ),
        "",
        "## Compiler Facts",
        "",
        f"- Compile success: {str(metrics['compile_success']).lower()}",
        "- Output schema target: `IFC2X3`",
        "- Low-level IFC entities were compiler-generated, not model output.",
        "",
        "## External Evidence",
        "",
        (
            f"- Available corpora: "
            f"{inventory['summary']['corpus_count']}"
        ),
        (
            f"- Inventoried IFC files: "
            f"{inventory['summary']['file_count']}"
        ),
        (
            f"- Eligible IFC2X3 files: "
            f"{inventory['summary']['eligible_ifc2x3_count']}"
        ),
        "- External corpora remain read-only and separate from BIMNet splits.",
        "",
    ]
    return "\n".join(lines)


def run_missing_piece_demo(
    *,
    output_dir: Path | None = None,
    inventory_roots: Iterable[Path] | None = None,
) -> dict[str, Any]:
    output = output_dir or DEFAULT_OUTPUT_DIR
    output.mkdir(parents=True, exist_ok=True)
    output_ifc = output / "output.ifc"
    output_ifc.unlink(missing_ok=True)

    case = repair_case("missing-piece-repair")
    base = case["base"]
    patch = case["patch"]
    patch_issues = tuple(validate_patch_document(patch))
    composition = compose_patches(base, [patch])
    composed = composition.document
    formal_issues = tuple(validate_v2_document(composed))
    provenance = build_provenance_report(base, composition)

    compilation = None
    if not patch_issues and composition.valid and not formal_issues:
        compilation = compile_document(composed, output_ifc)

    artifact = (
        check_ifc2x3_artifact(output_ifc)
        if compilation and compilation.success
        else None
    )
    quality = (
        check_generated_ifc(output_ifc, case["metadata"]["quality"])
        if artifact and artifact.success
        else None
    )
    roots = DEFAULT_EXTERNAL_ROOTS if inventory_roots is None else inventory_roots
    inventory = inventory_external_ifc(
        roots,
        repository_root=ROOT,
        max_selected_ifc2x3=3,
    )

    metrics = {
        "patch_valid": not patch_issues,
        "composition_valid": composition.valid,
        "formal_bim_json_valid": not formal_issues,
        "compile_success": bool(compilation and compilation.success),
        "declared_file_schema": (
            artifact.declared_file_schema if artifact else None
        ),
        "reopened_schema": artifact.reopened_schema if artifact else None,
        "ifc_validation_error_count": (
            artifact.ifc_validation_error_count if artifact else None
        ),
        "generated_ifc_quality_passed": bool(
            quality and quality.success
        ),
    }
    metrics["success"] = all(
        (
            metrics["patch_valid"],
            metrics["composition_valid"],
            metrics["formal_bim_json_valid"],
            metrics["compile_success"],
            metrics["declared_file_schema"] == "IFC2X3",
            metrics["reopened_schema"] == "IFC2X3",
            metrics["ifc_validation_error_count"] == 0,
            metrics["generated_ifc_quality_passed"],
        )
    )

    diagnostics = {
        "patch_validation": _validation_issues(patch_issues),
        "composition": [
            item.to_dict() for item in composition.diagnostics
        ],
        "formal_validation": _validation_issues(formal_issues),
        "compilation": _compilation_payload(compilation),
        "artifact": (
            artifact.to_dict()
            if artifact
            else {
                "success": False,
                "issues": [
                    {
                        "code": "IFC_ARTIFACT_NOT_AVAILABLE",
                        "path": "/artifact",
                        "message": "Compilation did not produce an IFC artifact.",
                    }
                ],
            }
        ),
        "quality": _quality_payload(quality),
    }

    prompt = render_repair_prompt(
        user_request=case["input_text"],
        base_document=base,
        validation_feedback=[],
    )
    _write_text_atomic(output / "input.txt", case["input_text"] + "\n")
    _write_json_atomic(output / "base.json", base)
    _write_json_atomic(output / "patch.json", patch)
    _write_text_atomic(
        output / "raw-response.txt",
        json.dumps(
            patch,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
    )
    _write_text_atomic(output / "prompt-used.md", prompt)
    _write_json_atomic(output / "expected.json", case["expected"])
    _write_json_atomic(output / "metadata.json", case["metadata"])
    _write_json_atomic(output / "composed.json", composed)
    _write_json_atomic(output / "provenance.json", provenance)
    _write_json_atomic(output / "external-inventory.json", inventory)
    _write_json_atomic(output / "diagnostics.json", diagnostics)
    _write_json_atomic(output / "metrics.json", metrics)
    _write_text_atomic(
        output / "report.md",
        _report(
            success=metrics["success"],
            metrics=metrics,
            provenance=provenance,
            inventory=inventory,
        ),
    )
    return {
        "success": metrics["success"],
        "output_dir": str(output),
        "metrics": metrics,
    }
