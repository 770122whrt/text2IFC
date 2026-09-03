from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import ifcopenshell


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "ifc_repair" / "validate_human_proof_layout.py"


def _write_ifc(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ifcopenshell.file(schema="IFC2X3").write(path)


def _write_case(
    collection: Path,
    case_id: str,
    *,
    outcome: str,
) -> dict[str, object]:
    case_root = collection / "accepted-cases" / case_id
    case_root.mkdir(parents=True)
    (case_root / "REPORT.md").write_text(f"# {case_id}\n", encoding="utf-8")
    (case_root / "request.txt").write_text("repair request\n", encoding="utf-8")
    _write_ifc(case_root / "damaged.ifc")
    authority = collection / "machine-authority" / "cases" / case_id
    authority.mkdir(parents=True)
    document: dict[str, object] = {
        "case_id": case_id,
        "outcome": outcome,
        "authority_path": f"machine-authority/cases/{case_id}",
        "report": f"accepted-cases/{case_id}/REPORT.md",
        "request": f"accepted-cases/{case_id}/request.txt",
        "damaged_ifc": f"accepted-cases/{case_id}/damaged.ifc",
    }
    if outcome == "repaired":
        _write_ifc(case_root / "repaired.ifc")
        document["repaired_ifc"] = f"accepted-cases/{case_id}/repaired.ifc"
    else:
        (case_root / "NO-REPAIR.md").write_text(
            "# No repaired output\n", encoding="utf-8"
        )
        document["no_repair_report"] = f"accepted-cases/{case_id}/NO-REPAIR.md"
    return document


def test_validates_visible_repair_and_no_output_cases(tmp_path: Path) -> None:
    collection = tmp_path / "proof" / "repair-milestone-r1"
    collection.mkdir(parents=True)
    (collection / "README.md").write_text("# R1\n", encoding="utf-8")
    (collection / "REPORT.md").write_text("# R1 report\n", encoding="utf-8")
    cases = [
        _write_case(collection, "E1", outcome="repaired"),
        _write_case(collection, "H4", outcome="no_output"),
    ]
    (collection / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "text2ifc/human-proof-collection/0.1",
                "collection_id": "r1-test",
                "cases": cases,
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(collection), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    result = json.loads(completed.stdout)
    assert result == {
        "schema_version": "text2ifc/human-proof-layout-validation/0.1",
        "status": "passed",
        "collection_id": "r1-test",
        "case_count": 2,
        "repaired_case_count": 1,
        "no_output_case_count": 1,
        "ifc_reopen_count": 3,
        "errors": [],
    }


def test_rejects_repaired_ifc_in_no_output_guard(tmp_path: Path) -> None:
    collection = tmp_path / "proof" / "guard-collection"
    collection.mkdir(parents=True)
    (collection / "README.md").write_text("# Guard\n", encoding="utf-8")
    (collection / "REPORT.md").write_text("# Guard report\n", encoding="utf-8")
    guard = _write_case(collection, "H4", outcome="no_output")
    _write_ifc(collection / "accepted-cases" / "H4" / "repaired.ifc")
    (collection / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "text2ifc/human-proof-collection/0.1",
                "collection_id": "guard-test",
                "cases": [guard],
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(collection), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "H4: no-output case must not expose repaired.ifc" in completed.stdout


def test_requires_explicit_role_for_original_ifc(tmp_path: Path) -> None:
    collection = tmp_path / "proof" / "triplet-collection"
    collection.mkdir(parents=True)
    (collection / "README.md").write_text("# Triplet\n", encoding="utf-8")
    (collection / "REPORT.md").write_text("# Triplet report\n", encoding="utf-8")
    case = _write_case(collection, "complete", outcome="repaired")
    original = collection / "accepted-cases" / "complete" / "original.ifc"
    _write_ifc(original)
    case["original_ifc"] = "accepted-cases/complete/original.ifc"
    (collection / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "text2ifc/human-proof-collection/0.1",
                "collection_id": "triplet-test",
                "cases": [case],
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(collection), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "complete: original_ifc requires an explicit original_role" in completed.stdout

def test_rejects_missing_declared_machine_authority(tmp_path: Path) -> None:
    collection = tmp_path / "proof" / "authority-collection"
    collection.mkdir(parents=True)
    (collection / "README.md").write_text("# Authority\n", encoding="utf-8")
    (collection / "REPORT.md").write_text("# Authority report\n", encoding="utf-8")
    case = _write_case(collection, "E1", outcome="repaired")
    case["authority_path"] = "machine-authority/cases/missing"
    (collection / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "text2ifc/human-proof-collection/0.1",
                "collection_id": "authority-test",
                "cases": [case],
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(collection), "--json"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "E1: authority_path does not exist" in completed.stdout