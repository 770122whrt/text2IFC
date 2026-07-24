import hashlib
import json
from pathlib import Path

import ifcopenshell

from text2ifc_ifc_repair.mutation import remove_windows_and_openings_batch


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "dataset" / "ifc" / "train" / "vvo.ifc"
SOURCE_SHA256 = "b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc"
TARGETS = (
    {
        "wall_global_id": "0jltRti3rFigAmdXYhXxuZ",
        "opening_global_id": "2IUEnGd5v4Yfg1ZkLtd0Yb",
        "window_global_id": "2IUEnGd5v4Yfg1ZlPtd0Yb",
    },
    {
        "wall_global_id": "0jltRti3rFigAmdXYhXxqI",
        "opening_global_id": "08xWVL$9z6JRwr3piJHoAz",
        "window_global_id": "08xWVL$9z6JRwr3oWJHoAz",
    },
    {
        "wall_global_id": "2HNE4WMQ1CXebZMaih8Xi_",
        "opening_global_id": "1B$rgWypT66viEf30I1iSa",
        "window_global_id": "1B$rgWypT66viEf2CI1iSa",
    },
    {
        "wall_global_id": "2CsmzAChHF6O6maGXlo6yJ",
        "opening_global_id": "2dYMXn0_5AKRbD_1mUIAqJ",
        "window_global_id": "2dYMXn0_5AKRbD_0yUIAqJ",
    },
    {
        "wall_global_id": "1cbLGwmrv8LAj2u11O6kyr",
        "opening_global_id": "3CUgKOb6T3Vgk4LBnR_Z8F",
        "window_global_id": "3CUgKOb6T3Vgk4LAzR_Z8F",
    },
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_batch_mutation_removes_five_chains_in_one_damaged_ifc(
    tmp_path: Path,
) -> None:
    output = tmp_path / "vvo-five-window"

    result = remove_windows_and_openings_batch(
        source_path=SOURCE,
        output_dir=output,
        targets=TARGETS,
        expected_source_sha256=SOURCE_SHA256,
    )

    assert result["valid"] is True
    assert result["target_count"] == 5
    assert _sha256(SOURCE) == SOURCE_SHA256
    damaged = ifcopenshell.open(str(output / "damaged.ifc"))
    assert damaged.schema == "IFC2X3"
    assert len(damaged.by_type("IfcWindow")) == 18
    assert len(damaged.by_type("IfcOpeningElement")) == 52
    for target in TARGETS:
        assert damaged.by_guid(target["wall_global_id"]) is not None
        for field in ("opening_global_id", "window_global_id"):
            try:
                damaged.by_guid(target[field])
            except RuntimeError:
                pass
            else:
                raise AssertionError(f"{field} was not removed")

    manifest = json.loads(
        (output / "mutation_manifest.private.json").read_text(encoding="utf-8")
    )
    assert manifest["schema_version"].endswith("/0.2")
    assert manifest["mutation_type"] == "remove_windows_and_openings_batch"
    assert len(manifest["targets"]) == 5
    assert [target["target_id"] for target in manifest["targets"]] == [
        "window-repair-001",
        "window-repair-002",
        "window-repair-003",
        "window-repair-004",
        "window-repair-005",
    ]
    assert all(
        target["prototype_evidence"]["source"]
        == "damaged_ifc_surviving_type"
        and target["prototype_evidence"]["surviving_occurrence_count"] >= 1
        for target in manifest["targets"]
    )

    report = json.loads(
        (output / "mutation_report.json").read_text(encoding="utf-8")
    )
    assert report["checks"]["all_target_regions_closed"] is True
    assert report["checks"]["all_host_walls_preserved"] is True
    assert len(report["geometry"]["targets"]) == 5
    assert all(
        item["target_region_closed"] for item in report["geometry"]["targets"]
    )


def test_batch_mutation_is_deterministic(tmp_path: Path) -> None:
    hashes = []
    reports = []
    for name in ("first", "second"):
        result = remove_windows_and_openings_batch(
            source_path=SOURCE,
            output_dir=tmp_path / name,
            targets=TARGETS,
            expected_source_sha256=SOURCE_SHA256,
        )
        hashes.append(result["damaged_sha256"])
        reports.append((tmp_path / name / "mutation_report.json").read_bytes())

    assert hashes[0] == hashes[1]
    assert reports[0] == reports[1]
