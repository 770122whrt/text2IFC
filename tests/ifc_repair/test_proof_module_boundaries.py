"""Proof auditing must not load a live runner or depend on a curator."""

import ast
import importlib
import inspect
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("name", ["validate_success_cases", "audit_door_repair_triplet", "live_audit"])
def test_proof_package_has_no_repair_script_dependency(name: str) -> None:
    module = importlib.import_module(f"text2ifc_proof.{name}")
    for node in ast.walk(ast.parse(inspect.getsource(module))):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("scripts.ifc_repair")
    result = subprocess.run(
        [sys.executable, "-c", f"import sys; import text2ifc_proof.{name}; "
         "assert not any(n.startswith('scripts.ifc_repair') for n in sys.modules)"],
        env=dict(os.environ, PYTHONPATH=os.pathsep.join(sys.path)),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("name", ["validate_success_cases", "audit_door_repair_triplet"])
def test_legacy_proof_module_and_cli_delegate_to_single_authority(name: str) -> None:
    authority = importlib.import_module(f"text2ifc_proof.{name}")
    legacy = importlib.import_module(f"scripts.ifc_repair.{name}")
    assert legacy is authority
    root = Path(__file__).resolve().parents[2]
    assert authority.ROOT == root
    result = subprocess.run(
        [sys.executable, str(root / f"scripts/ifc_repair/{name}.py"), "--help"],
        cwd=root.parent, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
