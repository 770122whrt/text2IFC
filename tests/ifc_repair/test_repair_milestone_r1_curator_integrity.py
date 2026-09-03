from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.ifc_repair import curate_repair_milestone_r1_proof as curator


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PROFILE = (
    ROOT / "docs/validation/repair-milestone-r1/repair-proof-profiles.json"
)
CANONICAL_FREEZE = (
    ROOT / "docs/validation/repair-milestone-r1/repair-acceptance-freeze.json"
)


class _ValidationResult:
    def __init__(self, document: dict[str, Any]) -> None:
        self._document = copy.deepcopy(document)

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._document)


def _validation_at_root(
    document: dict[str, Any],
    root: Path,
) -> _ValidationResult:
    staged_document = copy.deepcopy(document)
    staged_document["collection_root"] = Path(root).resolve().as_posix()
    return _ValidationResult(staged_document)


def _assert_private_stage_call(
    calls: list[Path],
    *,
    source: Path,
    destination: Path,
) -> None:
    assert len(calls) == 1
    assert calls[0] != source.resolve()
    assert calls[0] != destination.resolve()
    assert calls[0].parent == destination.parent.resolve()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_canonical_candidate(root: Path) -> tuple[dict[str, Any], list[str]]:
    root.mkdir(parents=True)
    profile = _read_json(CANONICAL_PROFILE)
    freeze = CANONICAL_FREEZE.read_bytes()
    (root / "repair-proof-profiles.json").write_bytes(
        CANONICAL_PROFILE.read_bytes()
    )
    (root / "repair-acceptance-freeze.json").write_bytes(freeze)

    profiles_by_id = {
        str(item["case_id"]): item for item in profile["cases"]
    }
    case_ids = [str(case_id) for case_id in profile["execution_order"]]
    _write_json(
        root / "manifest.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-collection/0.2",
            "provenance_namespace": "repair-milestone-r1",
            "profile": "repair-proof-profiles.json",
            "case_count": len(case_ids),
            "cases": [
                {
                    "case_id": case_id,
                    "status": "accepted",
                    "terminal_class": profiles_by_id[case_id]["terminal_class"],
                    "case_root": f"cases/{case_id}",
                    "files": f"cases/{case_id}/FILES.json",
                    "report": f"cases/{case_id}/REPORT.md",
                    "terminal_record": f"cases/{case_id}/terminal.json",
                }
                for case_id in case_ids
            ],
        },
    )
    return profile, case_ids


def _passed_validation(
    *, source: Path, profile: dict[str, Any], case_ids: list[str]
) -> dict[str, Any]:
    profiles_by_id = {
        str(item["case_id"]): item for item in profile["cases"]
    }
    return {
        "schema_version": "text2ifc/ifc-repair-proof-validation/0.3",
        "status": "passed",
        "collection_root": source.resolve().as_posix(),
        "case_count": len(case_ids),
        "independently_recomputed_case_count": len(case_ids),
        "no_output_case_count": 1,
        "errors": [],
        "cases": [
            {
                "case_id": case_id,
                "provenance_namespace": "repair-milestone-r1",
                "terminal_class": profiles_by_id[case_id]["terminal_class"],
                "status": "passed",
                "artifact_predicates": [],
                "property_authority_coverage": (
                    "strict_stage_1_5_recomputed"
                    if int(profiles_by_id[case_id].get("property_claim_count", 0))
                    else "not_applicable"
                ),
                "property_claim_count": int(
                    profiles_by_id[case_id].get("property_claim_count", 0)
                ),
                "current_property_acceptance_eligible": True,
                "source_immutable": True,
                "published_artifact_present": case_id != "H4",
            }
            for case_id in case_ids
        ],
    }


def test_external_validation_cannot_bypass_fresh_failed_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "candidate"
    destination = tmp_path / "curated"
    profile, case_ids = _write_canonical_candidate(source)
    injected_pass = _passed_validation(
        source=source,
        profile=profile,
        case_ids=case_ids,
    )
    fresh_failure = copy.deepcopy(injected_pass)
    fresh_failure["status"] = "failed"
    fresh_failure["errors"] = ["independent validator rejected candidate"]
    calls: list[Path] = []

    def _validate(root: Path) -> _ValidationResult:
        calls.append(Path(root).resolve())
        return _validation_at_root(fresh_failure, root)

    monkeypatch.setattr(curator, "validate_r1_proof_collection", _validate)

    with pytest.raises(ValueError, match="R1_CURATOR_VALIDATION_FAILED"):
        curator.curate_r1_proof(
            source_root=source,
            destination_root=destination,
            validation_document=injected_pass,
        )

    _assert_private_stage_call(
        calls,
        source=source,
        destination=destination,
    )
    assert not destination.exists()
    assert list(tmp_path.glob(".curated-stage-*")) == []


def test_external_validation_must_exactly_match_fresh_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "candidate"
    destination = tmp_path / "curated"
    profile, case_ids = _write_canonical_candidate(source)
    fresh_pass = _passed_validation(
        source=source,
        profile=profile,
        case_ids=case_ids,
    )
    injected_drift = copy.deepcopy(fresh_pass)
    injected_drift["cases"][0]["property_claim_count"] = 99
    calls: list[Path] = []

    def _validate(root: Path) -> _ValidationResult:
        calls.append(Path(root).resolve())
        return _validation_at_root(fresh_pass, root)

    monkeypatch.setattr(curator, "validate_r1_proof_collection", _validate)

    with pytest.raises(
        ValueError,
        match="R1_CURATOR_VALIDATION_DOCUMENT_MISMATCH",
    ):
        curator.curate_r1_proof(
            source_root=source,
            destination_root=destination,
            validation_document=injected_drift,
        )

    _assert_private_stage_call(
        calls,
        source=source,
        destination=destination,
    )
    assert not destination.exists()
    assert list(tmp_path.glob(".curated-stage-*")) == []


def test_external_validation_collection_root_rebind_is_limited_to_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "candidate"
    destination = tmp_path / "curated"
    unrelated = tmp_path / "unrelated"
    profile, case_ids = _write_canonical_candidate(source)
    fresh_pass = _passed_validation(
        source=source,
        profile=profile,
        case_ids=case_ids,
    )
    diagnostic_drift = copy.deepcopy(fresh_pass)
    diagnostic_drift["collection_root"] = unrelated.resolve().as_posix()
    calls: list[Path] = []

    def _validate(root: Path) -> _ValidationResult:
        calls.append(Path(root).resolve())
        return _validation_at_root(fresh_pass, root)

    monkeypatch.setattr(curator, "validate_r1_proof_collection", _validate)

    with pytest.raises(
        ValueError,
        match="R1_CURATOR_VALIDATION_DOCUMENT_MISMATCH",
    ):
        curator.curate_r1_proof(
            source_root=source,
            destination_root=destination,
            validation_document=diagnostic_drift,
        )

    _assert_private_stage_call(
        calls,
        source=source,
        destination=destination,
    )
    assert not destination.exists()
    assert list(tmp_path.glob(".curated-stage-*")) == []


def test_fresh_validation_case_counts_must_match_its_canonical_case_sequence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "candidate"
    destination = tmp_path / "curated"
    profile, case_ids = _write_canonical_candidate(source)
    inconsistent_fresh_pass = _passed_validation(
        source=source,
        profile=profile,
        case_ids=case_ids,
    )
    inconsistent_fresh_pass["case_count"] = len(case_ids) - 1
    calls: list[Path] = []

    def _validate(root: Path) -> _ValidationResult:
        calls.append(Path(root).resolve())
        return _validation_at_root(inconsistent_fresh_pass, root)

    monkeypatch.setattr(curator, "validate_r1_proof_collection", _validate)

    with pytest.raises(
        ValueError,
        match="R1_CURATOR_VALIDATED_CASE_COUNT",
    ):
        curator.curate_r1_proof(
            source_root=source,
            destination_root=destination,
        )

    _assert_private_stage_call(
        calls,
        source=source,
        destination=destination,
    )
    assert not destination.exists()
    assert list(tmp_path.glob(".curated-stage-*")) == []


def test_matching_fresh_validation_curates_exact_canonical_12_case_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "candidate"
    destination = tmp_path / "curated"
    profile, case_ids = _write_canonical_candidate(source)
    fresh_pass = _passed_validation(
        source=source,
        profile=profile,
        case_ids=case_ids,
    )
    calls: list[Path] = []

    def _validate(root: Path) -> _ValidationResult:
        calls.append(Path(root).resolve())
        return _validation_at_root(fresh_pass, root)

    monkeypatch.setattr(curator, "validate_r1_proof_collection", _validate)

    result = curator.curate_r1_proof(
        source_root=source,
        destination_root=destination,
        validation_document=copy.deepcopy(fresh_pass),
    )

    _assert_private_stage_call(
        calls,
        source=source,
        destination=destination,
    )
    assert case_ids == [
        "E1",
        "E2",
        "E3",
        "E4",
        "M1",
        "M2",
        "M3",
        "H1",
        "H2",
        "H3",
        "H4",
        "A1",
    ]
    assert result["case_ids"] == case_ids
    assert len(result["case_ids"]) == 12
    curation = _read_json(destination / "CURATION.json")
    assert curation["case_ids"] == case_ids
    validation_binding = curation["proof_validation"]
    validation_path = destination / validation_binding["path"]
    assert validation_path.is_file()
    assert validation_binding["sha256"] == (
        "sha256:" + hashlib.sha256(validation_path.read_bytes()).hexdigest()
    )
    persisted_validation = _read_json(validation_path)
    assert persisted_validation["schema_version"] == (
        "text2ifc/ifc-repair-proof-validation/0.3"
    )
    assert persisted_validation["collection_root"] == destination.resolve().as_posix()

    validation_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="R1_CURATOR_VALIDATION_REPORT_HASH"):
        curator.validate_curated_r1_proof(destination)


def test_curation_validates_and_publishes_one_private_stage_snapshot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "candidate"
    destination = tmp_path / "curated"
    profile, case_ids = _write_canonical_candidate(source)
    source_manifest_before = (source / "manifest.json").read_bytes()
    diagnostic_pass = _passed_validation(
        source=source,
        profile=profile,
        case_ids=case_ids,
    )
    validated_roots: list[Path] = []

    def _validate(root: Path) -> _ValidationResult:
        private_stage = Path(root).resolve()
        validated_roots.append(private_stage)
        source_manifest = _read_json(source / "manifest.json")
        source_manifest["tampered_after_private_copy"] = True
        _write_json(source / "manifest.json", source_manifest)
        assert private_stage != source.resolve()
        assert (private_stage / "manifest.json").read_bytes() == source_manifest_before
        return _ValidationResult(
            _passed_validation(
                source=private_stage,
                profile=profile,
                case_ids=case_ids,
            )
        )

    monkeypatch.setattr(curator, "validate_r1_proof_collection", _validate)

    result = curator.curate_r1_proof(
        source_root=source,
        destination_root=destination,
        validation_document=diagnostic_pass,
    )

    assert len(validated_roots) == 1
    assert validated_roots[0].parent == destination.parent.resolve()
    assert validated_roots[0] != destination.resolve()
    assert result["case_ids"] == case_ids
    assert (destination / "manifest.json").read_bytes() == source_manifest_before
    assert _read_json(source / "manifest.json")["tampered_after_private_copy"] is True


def test_self_consistent_profile_and_freeze_drift_still_requires_fresh_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "candidate"
    destination = tmp_path / "curated"
    profile, case_ids = _write_canonical_candidate(source)
    drifted_freeze = b'{"drifted": true}\n'
    (source / "repair-acceptance-freeze.json").write_bytes(drifted_freeze)
    profile["freeze"]["sha256"] = (
        "sha256:" + hashlib.sha256(drifted_freeze).hexdigest()
    )
    _write_json(source / "repair-proof-profiles.json", profile)
    injected_pass = _passed_validation(
        source=source,
        profile=profile,
        case_ids=case_ids,
    )
    fresh_failure = copy.deepcopy(injected_pass)
    fresh_failure["status"] = "failed"
    fresh_failure["errors"] = ["canonical profile/freeze binding rejected"]
    calls: list[Path] = []

    def _validate(root: Path) -> _ValidationResult:
        calls.append(Path(root).resolve())
        return _validation_at_root(fresh_failure, root)

    monkeypatch.setattr(curator, "validate_r1_proof_collection", _validate)

    with pytest.raises(ValueError, match="R1_CURATOR_VALIDATION_FAILED"):
        curator.curate_r1_proof(
            source_root=source,
            destination_root=destination,
            validation_document=injected_pass,
        )

    _assert_private_stage_call(
        calls,
        source=source,
        destination=destination,
    )
    assert not destination.exists()
    assert list(tmp_path.glob(".curated-stage-*")) == []
