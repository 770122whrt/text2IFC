"""Grouped runners retain historical imports and command entry points."""

import importlib
from pathlib import Path
import subprocess
import sys

import pytest


GROUPS = {
    "audits": (
        "continue_phase10_3_live_changeset", "run_phase10_3_compatibility_matrix",
        "run_phase10_4_comparator_benchmark",
    ),
    "curators": (
        "curate_phase11_door_proof", "curate_phase11_live_proof",
        "curate_phase12_live_proof", "curate_phase12_structural_proof",
        "curate_repair_milestone_r1_proof",
    ),
    "offline": (
        "run_phase10_3_batch_offline", "run_phase10_3_vvo_offline",
        "run_phase11_offline", "run_phase11_public_triplet_repair",
        "run_phase12_1_semantic_evaluation", "run_phase12_offline",
        "run_phase12_public_structural_repair",
    ),
    "uat": (
        "run_phase10_1_full_replication_uat", "run_phase10_1_live_uat",
        "run_phase10_2_live_uat", "run_phase10_3_vvo_live",
        "run_phase10_5_window_fidelity_uat", "run_phase10_live_uat",
        "run_phase11_live_uat", "run_phase12_live_uat", "run_phase9_live_uat",
        "run_repair_milestone_r1",
    ),
}


@pytest.mark.parametrize("group,name", [(g, n) for g, names in GROUPS.items() for n in names])
def test_old_import_is_the_grouped_implementation(group: str, name: str) -> None:
    current = importlib.import_module(f"scripts.ifc_repair.{group}.{name}")
    legacy = importlib.import_module(f"scripts.ifc_repair.{name}")
    assert legacy is current
    assert legacy.main is current.main
    assert Path(current.__file__).parent.name == group


@pytest.mark.parametrize("group,name", [
    ("audits", "run_phase10_4_comparator_benchmark"),
    ("curators", "curate_phase12_live_proof"),
    ("offline", "run_phase12_public_structural_repair"),
    ("uat", "run_phase12_live_uat"),
])
def test_old_and_grouped_cli_work_outside_the_repository(group: str, name: str) -> None:
    root = Path(__file__).resolve().parents[2]
    for relative in (f"{name}.py", f"{group}/{name}.py"):
        result = subprocess.run(
            [sys.executable, str(root / "scripts/ifc_repair" / relative), "--help"],
            cwd=root.parent, capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout


def test_changed_scope_admission_binds_implementations_not_only_shims() -> None:
    from scripts.ifc_repair.uat import run_phase12_live_uat as runner

    required = {
        "scripts/ifc_repair/uat/run_phase12_live_uat.py",
        "scripts/ifc_repair/offline/run_phase12_offline.py",
        "scripts/ifc_repair/curators/curate_phase12_live_proof.py",
        "src/text2ifc_ifc_repair/production_evaluation.py",
        "src/text2ifc_proof/validate_success_cases.py",
        "src/text2ifc_proof/live_audit.py",
    }
    assert required <= runner.REQUIRED_CHANGED_SCOPE_FILES
