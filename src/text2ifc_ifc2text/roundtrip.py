"""Artifact-oriented orchestration for the IFC2Text phase-1 baseline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from text2ifc_text.splits import atomic_write_text

from .compare import compare_ifc_buildings
from .description import render_design_description
from .facts import extract_building_facts


ROUNDTRIP_SCHEMA_VERSION = "text2ifc/ifc2text-roundtrip/0.1"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def prepare_roundtrip_baseline(
    source_ifc: str | Path,
    output_dir: str | Path,
    *,
    infer_spaces: bool = True,
) -> dict[str, Any]:
    """Extract source facts and the only text allowed to cross into reconstruction."""
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    facts = extract_building_facts(source_ifc, infer_spaces=infer_spaces)
    description = render_design_description(facts)
    facts_path = output / "source-facts.json"
    description_path = output / "design-description.md"
    manifest_path = output / "roundtrip.json"
    atomic_write_text(facts_path, _json(facts))
    atomic_write_text(description_path, description)
    manifest = {
        "schema_version": ROUNDTRIP_SCHEMA_VERSION,
        "stage": "prepared",
        "source": facts["source"],
        "source_facts_path": str(facts_path),
        "reconstruction_input_path": str(description_path),
        "truth_boundary": {
            "reconstruction_receives": ["design-description.md"],
            "reconstruction_must_not_receive": ["source IFC", "source-facts.json", "source GlobalIds"],
        },
        "reconstruction": {"status": "not_run"},
        "comparison": {"status": "not_run"},
    }
    atomic_write_text(manifest_path, _json(manifest))
    return manifest


def finalize_roundtrip_baseline(
    source_ifc: str | Path,
    reconstructed_ifc: str | Path,
    output_dir: str | Path,
    *,
    reconstruction_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare a reconstructed IFC and update the phase-1 artifact bundle."""
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "roundtrip.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = prepare_roundtrip_baseline(source_ifc, output, infer_spaces=True)
    comparison = compare_ifc_buildings(source_ifc, reconstructed_ifc)
    compare_path = output / "compare.json"
    atomic_write_text(compare_path, _json(comparison))
    manifest.update(
        {
            "stage": "compared",
            "reconstruction": {
                "status": "completed",
                "ifc_path": str(Path(reconstructed_ifc).resolve()),
                "evidence": reconstruction_evidence or {},
            },
            "comparison": {
                "status": "completed",
                "report_path": str(compare_path),
                "summary": comparison["summary"],
                "reconstruction_consistent": comparison["status"]["reconstruction_consistent"],
            },
        }
    )
    atomic_write_text(manifest_path, _json(manifest))
    return manifest
