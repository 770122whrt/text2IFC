"""Prepare the tracked Windows torch runtime before IFC repair collection."""

from __future__ import annotations

from text2ifc_knowledge.property_search import _prepare_windows_torch_runtime
import json
from pathlib import Path
import pytest


_prepare_windows_torch_runtime()


@pytest.fixture(scope="session")
def phase11_frozen_proof(tmp_path_factory):
    """Read the approved package mapping; never recreate the old Proof root."""
    from scripts.proof.package import materialize_bundle

    root = Path(__file__).resolve().parents[2] / "dataset/processed/proof/repair/phase11/reference-cases"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    bundle = next(b for b in manifest["legacy_bundles"] if b["old_root"] == "dataset/processed/proof/ifc-repair-success-cases")
    destination = tmp_path_factory.mktemp("phase11-proof") / "frozen"
    materialize_bundle(root, bundle, destination)
    return destination
