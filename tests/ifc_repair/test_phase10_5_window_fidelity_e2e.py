from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import ifcopenshell

from text2ifc_ifc_repair.evaluation import (
    EvaluationExecutionPolicy,
    execute_validation_and_diff,
)
from scripts.ifc_repair.run_phase10_5_window_fidelity_uat import (
    _latest_delegated_result_path,
    _live_artifact_hashes,
    build_live_command,
)


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = (
    ROOT
    / "dataset/manifests/ifc-repair-cases/"
    "phase10.5-window-fidelity-cases.json"
)
RUNNER = ROOT / "scripts/ifc_repair/run_phase10_5_window_fidelity_uat.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _small_ifc(path: Path, *, candidate: bool = False) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    model.create_entity("IfcCartesianPoint")
    if candidate:
        model.create_entity("IfcDirection")
    model.write(str(path))


def test_frozen_matrix_has_five_modes_hashes_and_exact_public_facts() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = payload["cases"]

    assert payload["schema_version"] == (
        "text2ifc/phase10.5-window-fidelity-cases/0.1"
    )
    assert {item["mode"] for item in cases} == {
        "complete_explicit",
        "exact_occurrence",
        "same_type_consensus",
        "same_type_conflict",
        "five_window_bundle",
    }
    assert len(cases) == 5
    for case in cases:
        source = ROOT / case["source"]["path"]
        assert source.is_file()
        assert _sha256(source) == case["source"]["sha256"]
        assert case["public_request"].strip()
        assert case["public_facts"]
    advanced = next(
        item for item in cases if item["mode"] == "five_window_bundle"
    )
    for role in ("damaged", "repaired_reference"):
        artifact = ROOT / advanced[role]["path"]
        assert _sha256(artifact) == advanced[role]["sha256"]


def test_runner_projects_only_public_matrix_and_no_fallback(tmp_path: Path) -> None:
    output = tmp_path / "uat"
    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--output",
            str(output),
            "--skip-offline",
            "--skip-performance",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    result = json.loads(
        (output / "phase10.5-uat-result.json").read_text(encoding="utf-8")
    )
    assert result["status"] == "passed"
    assert result["live"] == {
        "status": "not_run",
        "synthetic_fallback": False,
    }
    assert len(result["matrix"]) == 5
    serialized = json.dumps(result["matrix"], ensure_ascii=False).casefold()
    for private_canary in (
        "mutation_manifest.private",
        "benchmark_gold",
        "private_original_ifc",
    ):
        assert private_canary not in serialized
    assert all(
        item["repair_intent_version"]
        == "text2ifc/ifc-repair-intent/0.4"
        and item["bound_changeset_version"]
        == "text2ifc/ifc-repair-changeset/0.3"
        for item in result["matrix"]
    )


def test_small_cold_warm_acceleration_preserves_full_diff_and_limits(
    tmp_path: Path,
) -> None:
    baseline = tmp_path / "baseline.ifc"
    candidate = tmp_path / "candidate.ifc"
    _small_ifc(baseline)
    _small_ifc(candidate, candidate=True)
    policy = EvaluationExecutionPolicy(
        mode="accelerated",
        deadline_seconds=180,
        max_workers=2,
        rss_limit_bytes=4 * 1024**3,
    )
    cold = execute_validation_and_diff(
        damaged_ifc_path=baseline,
        repaired_ifc_path=candidate,
        cache_dir=tmp_path / "cache",
        policy=policy,
    )
    warm = execute_validation_and_diff(
        damaged_ifc_path=baseline,
        repaired_ifc_path=candidate,
        cache_dir=tmp_path / "cache",
        policy=policy,
    )

    assert cold["status"] == warm["status"] == "passed"
    assert cold["results"]["diff"] == warm["results"]["diff"]
    assert (
        cold["results"]["validation"]["comparison"]
        == warm["results"]["validation"]["comparison"]
    )
    assert {
        item["status"]
        for item in cold["results"]["validation"]["cache"].values()
    } == {"miss"}
    assert {
        item["status"]
        for item in warm["results"]["validation"]["cache"].values()
    } == {"hit"}
    for result in (cold, warm):
        assert result["metrics"]["wall_seconds"] <= 180
        assert 0 < result["metrics"]["peak_rss_bytes"] <= 4 * 1024**3
        assert result["metrics"]["worker_count"] == 2


def test_conflict_and_batch_contracts_are_explicit_in_manifest() -> None:
    cases = json.loads(MANIFEST.read_text(encoding="utf-8"))["cases"]
    conflict = next(item for item in cases if item["mode"] == "same_type_conflict")
    batch = next(item for item in cases if item["mode"] == "five_window_bundle")

    assert "expected_terminal=clarification_required" in conflict["public_facts"]
    assert "expected_publication=false" in conflict["public_facts"]
    assert "operation_count=5" in batch["public_facts"]
    assert "changeset_count=1" in batch["public_facts"]
    assert "atomic_rollback=true" in batch["public_facts"]
    assert "shared_type_mutation=false" in batch["public_facts"]


def test_live_command_explicitly_requests_phase10_5_contracts(
    tmp_path: Path,
) -> None:
    command = build_live_command(tmp_path / "live", tmp_path / ".env")

    assert "--intent-schema-version" in command
    version_index = command.index("--intent-schema-version") + 1
    assert command[version_index] == "text2ifc/ifc-repair-intent/0.4"
    assert "--live" in command
    assert "--output-root" in command


def test_live_evidence_discovers_timestamped_delegated_run(tmp_path: Path) -> None:
    live = tmp_path / "live"
    older = live / "uat-001"
    latest = live / "uat-002"
    older.mkdir(parents=True)
    latest.mkdir(parents=True)
    (older / "result.json").write_text("{}", encoding="utf-8")
    (latest / "result.json").write_text('{"status":"passed"}', encoding="utf-8")
    prompt = (
        latest
        / "runtime/runs/repair-001/intent/rendered-prompt.md"
    )
    prompt.parent.mkdir(parents=True)
    prompt.write_text("bounded prompt", encoding="utf-8")

    assert _latest_delegated_result_path(live) == latest / "result.json"
    hashes = _live_artifact_hashes(live)
    assert hashes == [
        {
            "path": (
                "uat-002/runtime/runs/repair-001/intent/"
                "rendered-prompt.md"
            ),
            "sha256": f"sha256:{_sha256(prompt)}",
            "bytes": len("bounded prompt"),
        }
    ]
