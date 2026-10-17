"""Source discovery uses tiny STEP fixtures, never the real source corpus."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.ifc_repair.dataset_batch.sources import discover_sources


FORMAL_ROOT = Path("dataset/processed/ifc-repair/repair-comparison/formal")
REGISTER = Path("dataset/external/ifc-asset-register.jsonl")


def _step(tag: str, schema: str = "IFC2X3") -> bytes:
    return (
        "ISO-10303-21;\nHEADER;\n"
        f"FILE_DESCRIPTION(('{tag}'),'2;1');\n"
        "FILE_NAME('test.ifc','',(),(),'','','');\n"
        f"FILE_SCHEMA(('{schema}'));\nENDSEC;\n"
        "DATA;\n#1=IFCPROJECT($,$,$,$,$,$,$,$,$);\n"
        "ENDSEC;\nEND-ISO-10303-21;\n"
    ).encode("ascii")


def _json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _write_register(root: Path, rows: list[dict]) -> None:
    path = root / REGISTER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _asset(root: Path, name: str, **updates) -> dict:
    content = _step(name)
    path = Path(f"dataset/external/fixtures/{name}.ifc")
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_bytes(content)
    evidence = Path("dataset/external/fixtures/LICENSE")
    (root / evidence).write_text("MIT fixture license notice", encoding="utf-8")
    row = {
        "asset_id": name,
        "source_id": "fixture-source",
        "source_family": name,
        "building_group": f"fixture-family-{name}",
        "local_path": path.as_posix(),
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "header_schema": "IFC2X3",
        "license": "MIT",
        "source_url": "https://example.test/source",
        "license_evidence": evidence.as_posix(),
        "rights_clear_for_collection": True,
        "source_permission_status": "explicit_local_or_attributed_use",
        "redistribution": "allowed_with_license_conditions",
        "element_classes": {"IfcWall": 4, "IfcDoor": 2},
    }
    row.update(updates)
    return row


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    for n in range(1, 21):
        case = f"formal-{n:03d}"
        private = tmp_path / FORMAL_ROOT / case / "private"
        private.mkdir(parents=True)
        content = _step(case)
        (private / "reference.ifc").write_bytes(content)
        evidence = private / "LICENSE"
        evidence.write_text("MIT formal fixture notice", encoding="utf-8")
        review = {
            "status": "accepted_by_delegation",
            "human_viewed": n == 1,
            "authorization": {"user_quote": "保留已有审阅记录"},
        }
        _json(
            private / "task.json",
            {
                "case_id": case,
                "source_sha256": hashlib.sha256(content).hexdigest(),
                "source": {
                    "asset_id": f"old-asset-{n}",
                    "source_id": "formal-source",
                    "license": "MIT",
                    "source_url": "https://example.test/formal",
                    "license_evidence": evidence.relative_to(tmp_path).as_posix(),
                    "scene_family": f"formal-family-{n}",
                    "element_classes": {"IfcWall": 1},
                },
                "review": review,
            },
        )
    _write_register(tmp_path, [])
    return tmp_path


def test_discovers_forty_unique_inputs_and_keeps_ordered_reserves(corpus: Path):
    rows = [_asset(corpus, f"extra-{n:03d}") for n in range(25)]
    _write_register(corpus, rows)

    result = discover_sources(corpus)

    assert result["schema_version"] == "text2ifc/ifc-repair-dataset-sources/1.0"
    assert len(result["sources"]) == 40
    assert len(result["reserve_candidates"]) == 5
    assert [x["source_id"] for x in result["sources"][:20]] == [
        f"formal-{n:03d}" for n in range(1, 21)
    ]
    assert [x["source_id"] for x in result["sources"][20:]] == [
        f"external-{n:03d}" for n in range(1, 21)
    ]
    assert [x["source_id"] for x in result["reserve_candidates"]] == [
        f"reserve-{n:03d}" for n in range(1, 6)
    ]
    combined = result["sources"] + result["reserve_candidates"]
    assert len({x["source_sha256"] for x in combined}) == 45
    assert all(not Path(x["input_path"]).is_absolute() for x in combined)
    assert all(x["schema"] == "IFC2X3" for x in combined)
    assert all(x["size_bytes"] < 20_000_000 for x in combined)
    assert all(x["admission"]["status"] == "pending_fresh_validation" for x in combined)


def test_preserves_reviews_and_does_not_assign_them_to_new_derivatives(corpus: Path):
    old_review = {"status": "human_accepted", "human_viewed": True, "comment": "old only"}
    row = _asset(corpus, "reviewed", review=old_review, human_viewed=True)
    _write_register(corpus, [row])

    result = discover_sources(corpus, additional_count=1)

    formal, external = result["sources"][0], result["sources"][-1]
    assert formal["review"] == json.loads(
        (corpus / FORMAL_ROOT / "formal-001/private/task.json").read_text(encoding="utf-8")
    )["review"]
    assert formal["human_viewed"] is True
    assert external["review"] == old_review
    assert external["human_viewed"] is True
    assert all(
        source["derived_review"] == {"status": "pending_human_review", "human_viewed": False}
        for source in [formal, external]
    )
    assert external["source_url"] == row["source_url"]
    assert row["license_evidence"] in external["license_evidence"]["local_paths"]
    assert external["rights"]["training_admission"] == "not_evaluated"


def test_excludes_nonpermitted_stale_and_duplicate_sources(corpus: Path):
    valid = _asset(corpus, "valid")
    duplicate = _asset(corpus, "duplicate")
    (corpus / duplicate["local_path"]).write_bytes((corpus / valid["local_path"]).read_bytes())
    duplicate.update(sha256=valid["sha256"], size_bytes=valid["size_bytes"])
    formal = _asset(corpus, "formal-copy")
    formal_bytes = (corpus / FORMAL_ROOT / "formal-001/private/reference.ifc").read_bytes()
    (corpus / formal["local_path"]).write_bytes(formal_bytes)
    formal.update(sha256=hashlib.sha256(formal_bytes).hexdigest(), size_bytes=len(formal_bytes))
    wrong_schema = _asset(corpus, "ifc4")
    data = _step("ifc4", "IFC4")
    (corpus / wrong_schema["local_path"]).write_bytes(data)
    wrong_schema.update(sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
    rows = [
        valid,
        duplicate,
        formal,
        wrong_schema,
        _asset(corpus, "no-derivatives", license="CC-BY-ND-4.0"),
        _asset(corpus, "unknown-license", license="repository-MIT-model-rights-review-required"),
        _asset(corpus, "hash-mismatch", sha256="0" * 64),
        _asset(corpus, "size-mismatch", size_bytes=1),
        _asset(corpus, "missing-file", local_path="dataset/external/absent.ifc"),
        _asset(corpus, "no-license-proof", license_evidence="dataset/external/absent-LICENSE"),
        _asset(corpus, "no-rights", rights_clear_for_collection=False),
        _asset(corpus, "escape", local_path="../outside.ifc"),
    ]
    _write_register(corpus, rows)

    result = discover_sources(corpus, additional_count=1)

    assert len(result["sources"]) == 21
    assert not result["reserve_candidates"]
    reasons = result["excluded_summary"]["by_reason"]
    assert reasons == {
        "duplicate_content": 1,
        "formal_content_duplicate": 1,
        "not_ifc2x3": 1,
        "license_forbids_derivatives": 1,
        "license_unclear": 1,
        "hash_mismatch": 1,
        "size_mismatch": 1,
        "missing_file": 1,
        "license_evidence_missing": 1,
        "rights_not_clear": 1,
        "unsafe_path": 1,
    }


def test_actual_twenty_megabyte_boundary_is_strict(corpus: Path):
    row = _asset(corpus, "large")
    path = corpus / row["local_path"]
    with path.open("ab") as stream:
        stream.truncate(20_000_000)
    row.update(size_bytes=20_000_000)
    _write_register(corpus, [row])
    result = discover_sources(corpus, additional_count=0)
    assert result["excluded_summary"]["by_reason"] == {"size_limit": 1}


def test_selection_is_deterministic_and_prioritizes_source_then_type_diversity(corpus: Path):
    rows = [
        _asset(corpus, "a-small", source_id="a", element_classes={"IfcWall": 1}),
        _asset(corpus, "a-rich", source_id="a", element_classes={"IfcWall": 1, "IfcDoor": 1, "IfcWindow": 1}),
        _asset(corpus, "b", source_id="b", element_classes={"IfcBeam": 1}),
        _asset(corpus, "c", source_id="c", element_classes={"IfcColumn": 1}),
    ]
    _write_register(corpus, rows)
    first = discover_sources(corpus, additional_count=3)
    _write_register(corpus, list(reversed(rows)))
    second = discover_sources(corpus, additional_count=3)
    chosen = first["sources"][20:]
    assert [s["registered_asset_id"] for s in chosen] == ["a-rich", "b", "c"]
    assert [s["source_sha256"] for s in chosen] == [s["source_sha256"] for s in second["sources"][20:]]
    assert [s["source_id"] for s in chosen] == [s["source_id"] for s in second["sources"][20:]]


def test_old_validation_numbers_are_not_fresh_admission(corpus: Path):
    row = _asset(corpus, "stale", strict_ifc2x3_pass=True, native_errors=0, geometry_failures=0)
    row["header_schema"] = "IFC4"
    _write_register(corpus, [row])
    selected = discover_sources(corpus, additional_count=1)["sources"][-1]
    assert selected["schema"] == "IFC2X3"
    assert selected["admission"]["status"] == "pending_fresh_validation"
    assert selected["selection_evidence"]["basis"] == "registered_metadata_not_fresh_admission"


@pytest.mark.parametrize("problem", ["missing", "duplicate", "hash", "source_hash", "schema"])
def test_formal_mothers_fail_closed(corpus: Path, problem: str):
    private = corpus / FORMAL_ROOT / "formal-020/private"
    if problem == "missing":
        (private / "reference.ifc").unlink()
    elif problem == "duplicate":
        data = (corpus / FORMAL_ROOT / "formal-001/private/reference.ifc").read_bytes()
        (private / "reference.ifc").write_bytes(data)
        task = json.loads((private / "task.json").read_text(encoding="utf-8"))
        task["source_sha256"] = hashlib.sha256(data).hexdigest()
        _json(private / "task.json", task)
    elif problem == "hash":
        task = json.loads((private / "task.json").read_text(encoding="utf-8"))
        task["source_sha256"] = "0" * 64
        _json(private / "task.json", task)
    elif problem == "source_hash":
        task = json.loads((private / "task.json").read_text(encoding="utf-8"))
        task["source"]["source_sha256"] = "0" * 64
        _json(private / "task.json", task)
    else:
        data = _step("formal-020", "IFC4")
        (private / "reference.ifc").write_bytes(data)
        task = json.loads((private / "task.json").read_text(encoding="utf-8"))
        task["source_sha256"] = hashlib.sha256(data).hexdigest()
        _json(private / "task.json", task)
    with pytest.raises(ValueError, match="formal-020"):
        discover_sources(corpus, additional_count=0)


def test_latest_asset_rights_cannot_be_overridden_by_a_permissive_license_label(corpus: Path):
    row = _asset(corpus, "revoked-derivatives")
    _write_register(corpus, [row])
    for date, allowed in [("20260924-v7", True), ("20260926-v8", False)]:
        prefix = "ifc-readiness" if "v7" in date else "ifc-expand"
        path = corpus / f"dataset/external/_checks/{prefix}-{date}/rights/rights.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "asset_id": row["asset_id"],
            "license_registered": "MIT",
            "publish_repaired_or_mutated_ifc": allowed,
        }) + "\n", encoding="utf-8")
    result = discover_sources(corpus, additional_count=0)
    assert result["excluded_summary"]["by_reason"] == {"license_forbids_derivatives": 1}


@pytest.mark.parametrize("count", [-1, True, 1.5])
def test_invalid_additional_count_is_rejected(corpus: Path, count):
    with pytest.raises(ValueError, match="additional_count"):
        discover_sources(corpus, additional_count=count)


def test_insufficient_pool_does_not_silently_return_incomplete_batch(corpus: Path):
    _write_register(corpus, [_asset(corpus, "only-one")])
    with pytest.raises(ValueError, match="additional.*2.*1"):
        discover_sources(corpus, additional_count=2)
