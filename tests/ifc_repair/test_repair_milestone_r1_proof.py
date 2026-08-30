from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import ifcopenshell
import pytest
from jsonschema import Draft202012Validator

from scripts.ifc_repair import validate_success_cases as proof_validator
from text2ifc_ifc_repair.apply import apply_changeset
from text2ifc_ifc_repair.operations import create_default_registry


ROOT = Path(__file__).resolve().parents[2]
TARGET_ID = "0000000000000000000001"


def _source_model(path: Path, ifc_class: str) -> None:
    model = ifcopenshell.file(schema="IFC2X3")
    organization = model.create_entity("IfcOrganization", Name="R1 Proof")
    application = model.create_entity(
        "IfcApplication",
        ApplicationDeveloper=organization,
        Version="0.1",
        ApplicationFullName="R1 Proof fixture",
        ApplicationIdentifier="text2ifc",
    )
    person = model.create_entity("IfcPerson", FamilyName="Tester")
    user = model.create_entity(
        "IfcPersonAndOrganization",
        ThePerson=person,
        TheOrganization=organization,
    )
    history = model.create_entity(
        "IfcOwnerHistory",
        OwningUser=user,
        OwningApplication=application,
        ChangeAction="ADDED",
        CreationDate=0,
    )
    model.create_entity(
        ifc_class,
        GlobalId=TARGET_ID,
        OwnerHistory=history,
        Name=f"R1 target {ifc_class}",
    )
    model.write(str(path))


def _property_operation(
    *,
    ifc_class: str,
    set_name: str,
    property_name: str,
    value_type: str,
    value: Any,
) -> dict[str, Any]:
    operation_id = f"r1-{ifc_class.casefold()}-property"
    fact_key = f"pset:{set_name}.{property_name}"
    return {
        "operation_id": operation_id,
        "operation_type": "set_occurrence_properties",
        "target": {"element_global_id": TARGET_ID},
        "parameters": {},
        "evidence_refs": ["property-resolution:/claim-001/decision.json"],
        "semantic_manifest": {
            "manifest_id": f"manifest-{operation_id}",
            "policy_id": "occurrence.property.l2",
            "policy_version": "0.1",
        },
        "semantic_assignments": [
            {
                "operation_id": operation_id,
                "fact_key": fact_key,
                "source_fact_key": fact_key,
                "value": value,
                "value_type": value_type,
                "unit": None,
                "ownership": "occurrence_direct",
                "applicability": "required",
                "source_kind": "explicit_request",
                "source_ref": "property-resolution:/claim-001/decision.json",
                "provenance": ["property-resolution:fixture"],
                "authoring_action": "set_occurrence_pset",
            }
        ],
    }


def _apply_property_case(
    tmp_path: Path,
    *,
    ifc_class: str,
    set_name: str,
    property_name: str,
    value_type: str,
    value: Any,
) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    source = tmp_path / "source.ifc"
    repaired = tmp_path / "repaired.ifc"
    _source_model(source, ifc_class)
    request = f"Set {set_name}.{property_name} on {TARGET_ID}."
    operation = _property_operation(
        ifc_class=ifc_class,
        set_name=set_name,
        property_name=property_name,
        value_type=value_type,
        value=value,
    )
    changeset = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.2",
        "changeset_id": f"changeset-{operation['operation_id']}",
        "binding_status": "bound",
        "base_model_fingerprint": "sha256:"
        + hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_request_hash": "sha256:"
        + hashlib.sha256(request.encode("utf-8")).hexdigest(),
        "scope": {"target_ids": [TARGET_ID], "forbidden_ids": []},
        "evidence_refs": ["property-resolution:/claim-001/decision.json"],
        "preconditions": ["target_exists"],
        "postconditions": ["requested_properties_match"],
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": "sha256:" + "c" * 64,
        "operations": [operation],
    }
    application = apply_changeset(
        damaged_ifc_path=source,
        repair_request=request,
        changeset=changeset,
        output_path=repaired,
        registry=create_default_registry(),
    )
    assert application["valid"] is True, application
    assert application["published"] is True, application
    return source, repaired, changeset, application


def _property_predicates(
    *,
    ifc_class: str,
    set_name: str,
    property_name: str,
    value_type: str,
    value: Any,
) -> list[dict[str, Any]]:
    return [
        {
            "predicate_id": "exact-occurrence-property",
            "kind": "occurrence_property",
            "target": {"global_id": TARGET_ID, "ifc_class": ifc_class},
            "property": {
                "set_name": set_name,
                "property_name": property_name,
                "value_type": value_type,
                "value": value,
                "scope": "occurrence_direct",
            },
        },
        {
            "predicate_id": "occurrence-preservation",
            "kind": "occurrence_preservation",
            "target": {"global_id": TARGET_ID, "ifc_class": ifc_class},
        },
    ]


def test_proof_validation_v03_represents_all_frozen_r1_terminal_families() -> None:
    schema_path = (
        ROOT / "schemas/agent/ifc-repair-proof-validation-0.3.schema.json"
    )
    assert schema_path.is_file()
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    terminal_classes = (
        "SUCCESS",
        "CLARIFICATION_THEN_SUCCESS",
        "INADMISSIBLE_VALUE_OR_CLARIFICATION",
        "UNSUPPORTED_ATOMIC_GUARD",
    )
    payload = proof_validator.ProofValidationResultV03(
        status="passed",
        collection_root="fixture",
        case_count=4,
        independently_recomputed_case_count=4,
        no_output_case_count=1,
        cases=[
            {
                "case_id": f"case-{index}",
                "provenance_namespace": "repair-milestone-r1",
                "terminal_class": terminal_class,
                "status": "passed",
                "artifact_predicates": [],
                "property_authority_coverage": (
                    "not_applicable"
                    if terminal_class == "UNSUPPORTED_ATOMIC_GUARD"
                    else "strict_stage_1_5_recomputed"
                ),
                "property_claim_count": (
                    0 if terminal_class == "UNSUPPORTED_ATOMIC_GUARD" else 1
                ),
                "current_property_acceptance_eligible": True,
                "source_immutable": True,
                "published_artifact_present": terminal_class
                != "UNSUPPORTED_ATOMIC_GUARD",
            }
            for index, terminal_class in enumerate(terminal_classes, start=1)
        ],
    ).to_dict()

    Draft202012Validator(schema).validate(payload)
    assert payload["schema_version"] == (
        "text2ifc/ifc-repair-proof-validation/0.3"
    )

    old = proof_validator.ProofValidationResult(
        status="passed",
        collection_root="legacy",
    ).to_dict()
    assert old["schema_version"] == (
        "text2ifc/ifc-repair-proof-validation/0.2"
    )


@pytest.mark.parametrize(
    ("ifc_class", "set_name", "property_name", "value_type", "value"),
    (
        (
            "IfcWindow",
            "Pset_WindowCommon",
            "IsExternal",
            "IfcBoolean",
            True,
        ),
        ("IfcDoor", "Pset_DoorCommon", "FireRating", "IfcLabel", "EI60"),
        (
            "IfcBeam",
            "Pset_BeamCommon",
            "Reference",
            "IfcIdentifier",
            "B-204",
        ),
        (
            "IfcColumn",
            "Pset_ColumnCommon",
            "LoadBearing",
            "IfcBoolean",
            True,
        ),
        (
            "IfcWallStandardCase",
            "Pset_WallCommon",
            "AcousticRating",
            "IfcLabel",
            "Rw 50",
        ),
    ),
)
def test_r1_occurrence_property_predicates_recompute_exact_value_and_preservation(
    tmp_path: Path,
    ifc_class: str,
    set_name: str,
    property_name: str,
    value_type: str,
    value: Any,
) -> None:
    source, repaired, changeset, application = _apply_property_case(
        tmp_path,
        ifc_class=ifc_class,
        set_name=set_name,
        property_name=property_name,
        value_type=value_type,
        value=value,
    )

    result = proof_validator.audit_r1_artifact_predicates(
        source_model=ifcopenshell.open(str(source)),
        repaired_model=ifcopenshell.open(str(repaired)),
        changeset=changeset,
        application=application,
        predicates=_property_predicates(
            ifc_class=ifc_class,
            set_name=set_name,
            property_name=property_name,
            value_type=value_type,
            value=value,
        ),
    )

    assert [item["status"] for item in result] == ["passed", "passed"]


def test_r1_occurrence_property_predicate_fails_closed_on_tampered_value(
    tmp_path: Path,
) -> None:
    source, repaired, changeset, application = _apply_property_case(
        tmp_path,
        ifc_class="IfcWindow",
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value_type="IfcBoolean",
        value=True,
    )
    predicates = _property_predicates(
        ifc_class="IfcWindow",
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value_type="IfcBoolean",
        value=False,
    )

    with pytest.raises(ValueError, match="proof.predicate.occurrence_property"):
        proof_validator.audit_r1_artifact_predicates(
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired)),
            changeset=changeset,
            application=application,
            predicates=predicates,
        )


@pytest.mark.parametrize(
    ("tamper", "match"),
    (
        ("target", "proof.predicate.occurrence_operation"),
        ("property", "proof.predicate.occurrence_property"),
    ),
)
def test_r1_occurrence_property_predicate_fails_closed_on_target_or_property(
    tmp_path: Path,
    tamper: str,
    match: str,
) -> None:
    source, repaired, changeset, application = _apply_property_case(
        tmp_path,
        ifc_class="IfcDoor",
        set_name="Pset_DoorCommon",
        property_name="FireRating",
        value_type="IfcLabel",
        value="EI60",
    )
    predicates = _property_predicates(
        ifc_class="IfcDoor",
        set_name="Pset_DoorCommon",
        property_name="FireRating",
        value_type="IfcLabel",
        value="EI60",
    )
    if tamper == "target":
        predicates[0]["target"]["global_id"] = "0000000000000000000002"
    else:
        predicates[0]["property"]["property_name"] = "IsExternal"
    with pytest.raises(ValueError, match=match):
        proof_validator.audit_r1_artifact_predicates(
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired)),
            changeset=changeset,
            application=application,
            predicates=predicates,
        )


def test_r1_occurrence_preservation_fails_closed_on_placement_tamper(
    tmp_path: Path,
) -> None:
    source, repaired, changeset, application = _apply_property_case(
        tmp_path,
        ifc_class="IfcWindow",
        set_name="Pset_WindowCommon",
        property_name="IsExternal",
        value_type="IfcBoolean",
        value=True,
    )
    model = ifcopenshell.open(str(repaired))
    target = model.by_guid(TARGET_ID)
    point = model.create_entity("IfcCartesianPoint", Coordinates=(1.0, 0.0, 0.0))
    axis = model.create_entity("IfcAxis2Placement3D", Location=point)
    target.ObjectPlacement = model.create_entity(
        "IfcLocalPlacement", PlacementRelTo=None, RelativePlacement=axis
    )
    model.write(str(repaired))

    with pytest.raises(ValueError, match="proof.predicate.occurrence_preservation"):
        proof_validator.audit_r1_artifact_predicates(
            source_model=ifcopenshell.open(str(source)),
            repaired_model=ifcopenshell.open(str(repaired)),
            changeset=changeset,
            application=application,
            predicates=_property_predicates(
                ifc_class="IfcWindow",
                set_name="Pset_WindowCommon",
                property_name="IsExternal",
                value_type="IfcBoolean",
                value=True,
            ),
        )


@pytest.mark.parametrize(
    "terminal_record",
    (
        {
            "terminal_class": "CLARIFICATION_THEN_SUCCESS",
            "initial_stop": {
                "status": "clarification_required",
                "reason_code": "ambiguous_target",
                "stage2_attempts": 0,
                "apply_attempts": 0,
                "published_outputs": [],
                "offered_identities": ["IfcWindow:window-1", "IfcWindow:window-2"],
                "selected_identity": "IfcWindow:window-2",
                "lineage_id": "run:terminal-case",
                "resume_lineage_same": True,
            },
            "resume_success": True,
        },
        {
            "terminal_class": "INADMISSIBLE_VALUE_OR_CLARIFICATION",
            "initial_stop": {
                "status": "clarification_required",
                "reason_code": "PROPERTY_VALUE_TYPE_INCOMPATIBLE",
                "stage2_attempts": 0,
                "apply_attempts": 0,
                "published_outputs": [],
                "resolved_property_identity": "Pset_DoorCommon.FireRating",
                "deterministic_admissibility_status": "clarification_required",
            },
            "resume_success": True,
        },
        {
            "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
            "initial_stop": {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
                "stage2_attempts": 0,
                "apply_attempts": 0,
                "published_outputs": [],
                "supported_capabilities": ["add_beam"],
                "unsupported_capabilities": ["structural_analysis_node"],
                "atomic_request": True,
            },
            "resume_success": False,
        },
    ),
)
def test_r1_no_output_terminal_records_are_formal_and_fail_closed(
    tmp_path: Path,
    terminal_record: dict[str, Any],
) -> None:
    source = tmp_path / "source.ifc"
    _source_model(source, "IfcWindow")
    digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    record = {
        "schema_version": "text2ifc/ifc-repair-proof-terminal/0.1",
        "case_id": "terminal-case",
        "source": {
            "path": "source.ifc",
            "sha256_before": digest,
            "sha256_after": digest,
            "unchanged": True,
        },
        **terminal_record,
    }

    result = proof_validator.validate_r1_terminal_record(
        record,
        case_root=tmp_path,
    )

    assert result["status"] == "passed"
    assert result["source_immutable"] is True
    if record["terminal_class"] == "UNSUPPORTED_ATOMIC_GUARD":
        assert result["published_artifact_present"] is False


def test_r1_no_output_terminal_rejects_stage2_leakage(tmp_path: Path) -> None:
    source = tmp_path / "source.ifc"
    _source_model(source, "IfcBeam")
    digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    record = {
        "schema_version": "text2ifc/ifc-repair-proof-terminal/0.1",
        "case_id": "H4",
        "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
        "source": {
            "path": "source.ifc",
            "sha256_before": digest,
            "sha256_after": digest,
            "unchanged": True,
        },
        "initial_stop": {
            "status": "unsupported",
            "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
            "stage2_attempts": 1,
            "apply_attempts": 0,
            "published_outputs": [],
            "supported_capabilities": ["add_beam"],
            "unsupported_capabilities": ["structural_analysis_node"],
            "atomic_request": True,
        },
        "resume_success": False,
    }

    with pytest.raises(ValueError, match="proof.terminal.pre_mutation"):
        proof_validator.validate_r1_terminal_record(record, case_root=tmp_path)


def test_r1_clarification_terminal_rejects_dynamic_candidate_rank_identity(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _source_model(source, "IfcWindow")
    digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    record = {
        "schema_version": "text2ifc/ifc-repair-proof-terminal/0.1",
        "case_id": "H3",
        "terminal_class": "CLARIFICATION_THEN_SUCCESS",
        "source": {
            "path": "source.ifc",
            "sha256_before": digest,
            "sha256_after": digest,
            "unchanged": True,
        },
        "initial_stop": {
            "status": "clarification_required",
            "reason_code": "ambiguous_target",
            "stage2_attempts": 0,
            "apply_attempts": 0,
            "published_outputs": [],
            "offered_identities": ["candidate:1:IfcWindow:stable-guid"],
            "selected_identity": "candidate:1:IfcWindow:stable-guid",
            "lineage_id": "run:H3",
            "resume_lineage_same": True,
        },
        "resume_success": True,
    }
    with pytest.raises(ValueError, match="proof.terminal.clarification_lineage"):
        proof_validator.validate_r1_terminal_record(record, case_root=tmp_path)


def test_r1_incompatible_value_replays_property_identity_before_type_rejection() -> None:
    from tests.ifc_repair.test_property_admissibility import (
        _candidate,
        _candidate_set,
        _claim,
        _decision,
        _query,
        _trace,
    )
    from text2ifc_knowledge.property_search import (
        build_standard_property_records,
        default_standard_corpus_fingerprint,
    )
    from text2ifc_knowledge.registry import load_ifc2x3_registry

    registry = load_ifc2x3_registry(ROOT)
    records = build_standard_property_records(
        registry,
        corpus_fingerprint=default_standard_corpus_fingerprint(),
    )
    record = next(
        item
        for item in records
        if item.canonical_path == "Pset_DoorCommon.FireRating"
    )
    claim = _claim(phrase="fire rating", value=True)
    query = _query(claim, target_class="IfcDoor")
    candidate_set = _candidate_set(
        query, [_candidate(record, rank=1, score=0.92)]
    )
    decision = _decision(
        "confirmed",
        selected=candidate_set["candidates"][0]["candidate_id"],
    )

    result = proof_validator.audit_r1_inadmissible_value_replay(
        query=query,
        candidate_set=candidate_set,
        decision=decision,
        decision_trace=_trace(query, candidate_set),
        claim=claim.to_dict(),
        expected_property_identity="Pset_DoorCommon.FireRating",
    )

    assert result == {
        "status": "passed",
        "resolved_property_identity": "Pset_DoorCommon.FireRating",
        "deterministic_status": "rejected",
        "reason_code": "PROPERTY_VALUE_TYPE_INCOMPATIBLE",
        "exact_intent_constructed": False,
    }


def test_r1_stage15_authority_replay_accepts_pure_window_occurrence(
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair import run_phase12_live_uat as live_uat
    from tests.ifc_repair.test_phase12_live_uat import _ProductionPathTransport
    from tests.ifc_repair.test_property_resolution_family_e2e import (
        _runtime as offline_property_runtime,
    )

    case = next(
        item
        for item in live_uat.DEFAULT_CASES
        if item.case_id == "window-semantic-canary"
    )
    provider = live_uat.TranscriptProvider(_ProductionPathTransport())
    provider.set_case(case.case_id)
    case_root = tmp_path / "window"
    final = live_uat._production_case_executor(
        case,
        provider,
        case_root,
        property_knowledge_runtime=offline_property_runtime(),
    )
    assert final["status"] == "succeeded"
    run_root = case_root / "runtime" / "runs" / str(final["run_id"])
    source_manifest = run_root / "proof-source-manifest.json"
    source_manifest.write_text(
        json.dumps(
            {
                "provider_evidence_mode": "offline_bound_deterministic",
                "synthetic_fallback_used": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    roles = {
        f"artifact-{index}": path
        for index, path in enumerate(run_root.rglob("*"), start=1)
        if path.is_file()
    }
    roles["source_run_manifest"] = source_manifest
    intent = json.loads(
        (run_root / "intent" / "repair-intent.json").read_text(
            encoding="utf-8"
        )
    )
    changeset = json.loads(
        (run_root / "changeset" / "bound-changeset.json").read_text(
            encoding="utf-8"
        )
    )
    resolution = json.loads(
        (run_root / "resolution.json").read_text(encoding="utf-8")
    )
    semantic_manifest = json.loads(
        (run_root / "semantic-manifest.json").read_text(encoding="utf-8")
    )

    authority = proof_validator.audit_current_property_authority_replay(
        source_ifc_path=live_uat.SOURCE,
        source_sha256=proof_validator._normalize_sha256(
            "sha256:" + hashlib.sha256(live_uat.SOURCE.read_bytes()).hexdigest()
        ),
        intent=intent,
        changeset=changeset,
        retained_resolution=resolution,
        retained_manifest=semantic_manifest,
        roles=roles,
        provider_evidence_mode="offline_bound_deterministic",
    )

    assert authority["property_authority_coverage"] == (
        "strict_stage_1_5_recomputed"
    )
    assert authority["property_claim_count"] == 1
    assert authority["current_property_acceptance_eligible"] is True


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_case_files(case_root: Path, case_id: str) -> None:
    (case_root / "REPORT.md").write_text(f"# {case_id}\n", encoding="utf-8")
    entries = []
    for index, artifact in enumerate(
        sorted(
            path
            for path in case_root.rglob("*")
            if path.is_file() and path.name not in {"FILES.json", "REPORT.md"}
        ),
        start=1,
    ):
        entries.append(
            {
                "path": artifact.relative_to(case_root).as_posix(),
                "role": f"artifact-{index:04d}",
                "sha256": "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "size_bytes": artifact.stat().st_size,
            }
        )
    _write_json(
        case_root / "FILES.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-files/0.2",
            "case_id": case_id,
            "files": entries,
        },
    )


def _r1_profile(case_id: str, terminal_class: str) -> dict[str, Any]:
    return {
        "profile_id": f"r1-{case_id}",
        "case_id": case_id,
        "provenance_namespace": "repair-milestone-r1",
        "terminal_class": terminal_class,
        "artifact_predicates": [],
    }


def _write_fixture_freeze(root: Path, content: str = "{}\n") -> str:
    path = root / "freeze.json"
    path.write_text(content, encoding="utf-8")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_canonical_collection_skeleton(
    root: Path,
    *,
    terminal_overrides: dict[str, str] | None = None,
) -> None:
    profile_source = (
        ROOT / "docs/validation/repair-milestone-r1/repair-proof-profiles.json"
    )
    freeze_source = (
        ROOT / "docs/validation/repair-milestone-r1/repair-acceptance-freeze.json"
    )
    profile_path = root / profile_source.name
    freeze_path = root / freeze_source.name
    profile_path.write_bytes(profile_source.read_bytes())
    freeze_path.write_bytes(freeze_source.read_bytes())
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    overrides = terminal_overrides or {}
    cases = []
    for item in profile["cases"]:
        case_id = str(item["case_id"])
        case_root = f"cases/{case_id}"
        cases.append(
            {
                "case_id": case_id,
                "status": "accepted",
                "terminal_class": overrides.get(
                    case_id,
                    str(item["terminal_class"]),
                ),
                "case_root": case_root,
                "files": f"{case_root}/FILES.json",
                "report": f"{case_root}/REPORT.md",
                "terminal_record": f"{case_root}/terminal.json",
            }
        )
    _write_json(
        root / "manifest.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-collection/0.2",
            "provenance_namespace": "repair-milestone-r1",
            "profile": profile_path.name,
            "case_count": len(cases),
            "cases": cases,
        },
    )


def test_r1_no_output_terminal_accepts_without_fabricated_repaired_ifc(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.ifc"
    _source_model(source, "IfcBeam")
    digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    result = proof_validator.validate_r1_terminal_record(
        {
            "schema_version": "text2ifc/ifc-repair-proof-terminal/0.1",
            "case_id": "H4",
            "terminal_class": "UNSUPPORTED_ATOMIC_GUARD",
            "source": {
                "path": "source.ifc",
                "sha256_before": digest,
                "sha256_after": digest,
                "unchanged": True,
            },
            "initial_stop": {
                "status": "unsupported",
                "reason_code": "STRUCTURAL_ANALYSIS_UNSUPPORTED",
                "stage2_attempts": 0,
                "apply_attempts": 0,
                "published_outputs": [],
                "supported_capabilities": ["add_beam"],
                "unsupported_capabilities": ["structural_analysis_node"],
                "atomic_request": True,
            },
            "resume_success": False,
        },
        case_root=tmp_path,
    )

    assert result["status"] == "passed"
    assert result["source_immutable"] is True
    assert result["published_artifact_present"] is False
    assert not (tmp_path / "repaired.ifc").exists()


def test_r1_collection_rejects_profile_terminal_contract_drift(
    tmp_path: Path,
) -> None:
    _write_canonical_collection_skeleton(
        tmp_path,
        terminal_overrides={"H4": "SUCCESS"},
    )

    result = proof_validator.validate_r1_proof_collection(tmp_path)

    assert result.status == "failed"
    assert "H4: proof.profile.terminal_class" in result.errors


def test_r1_profile_is_machine_readable_and_bound_to_the_accepted_freeze() -> None:
    profile_path = ROOT / "docs/validation/repair-milestone-r1/repair-proof-profiles.json"
    schema_path = ROOT / "schemas/agent/ifc-repair-proof-profile-0.1.schema.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(profile)
    freeze_path = ROOT / "docs/validation/repair-milestone-r1/repair-acceptance-freeze.json"
    assert profile["freeze"]["sha256"] == (
        "sha256:" + hashlib.sha256(freeze_path.read_bytes()).hexdigest()
    )
    assert profile["execution_order"] == [
        "E1", "E2", "E3", "E4", "M1", "M2", "M3", "H1", "H2", "H3", "H4", "A1"
    ]
    assert [item["case_id"] for item in profile["cases"]] == profile["execution_order"]


@pytest.mark.parametrize(
    ("case_name", "predicate"),
    (
        (
            "phase12-vvo-beam-material-present",
            {
                "predicate_id": "beam-add",
                "kind": "structural_add",
                "operation_type": "add_beam",
                "storey_global_id": "1vTeahUkP60PdWqwCTjUuM",
                "axis_start_mm": [200000, 200000, 0],
                "axis_end_mm": [203000, 204000, 0],
                "section_width_mm": 300,
                "section_height_mm": 500,
                "type_policy": "generated",
            },
        ),
        (
            "phase12-vvo-column-material-absent",
            {
                "predicate_id": "column-add",
                "kind": "structural_add",
                "operation_type": "add_column",
                "storey_global_id": "1vTeahUkP60PdWqwCTjeRs",
                "axis_start_mm": [210000, 210000, 0],
                "axis_end_mm": [210000, 210000, 6000],
                "section_width_mm": 400,
                "section_height_mm": 600,
                "orientation_xy": [0, 1],
                "type_policy": "generated",
            },
        ),
    ),
)
def test_r1_structural_add_predicate_reuses_frozen_beam_column_proof(
    case_name: str,
    predicate: dict[str, Any],
) -> None:
    case_root = (
        ROOT
        / "dataset/processed/proof/ifc-repair-success-cases/structural/single"
        / case_name
    )
    result = proof_validator.audit_r1_artifact_predicates(
        source_model=ifcopenshell.open(str(case_root / "damaged.ifc")),
        repaired_model=ifcopenshell.open(str(case_root / "repaired.ifc")),
        changeset=json.loads((case_root / "changeset.json").read_text(encoding="utf-8")),
        application=json.loads((case_root / "application.json").read_text(encoding="utf-8")),
        predicates=[predicate],
    )
    assert result == [
        {
            "predicate_id": predicate["predicate_id"],
            "kind": "structural_add",
            "status": "passed",
        }
    ]


def test_r1_structural_add_predicate_fails_closed_on_tampered_geometry() -> None:
    case_root = (
        ROOT
        / "dataset/processed/proof/ifc-repair-success-cases/structural/single"
        / "phase12-vvo-beam-material-present"
    )
    predicate = {
        "predicate_id": "beam-add",
        "kind": "structural_add",
        "operation_type": "add_beam",
        "storey_global_id": "1vTeahUkP60PdWqwCTjUuM",
        "axis_start_mm": [200001, 200000, 0],
        "axis_end_mm": [203000, 204000, 0],
        "section_width_mm": 300,
        "section_height_mm": 500,
        "type_policy": "generated",
    }
    with pytest.raises(ValueError, match="proof.predicate.structural_geometry"):
        proof_validator.audit_r1_artifact_predicates(
            source_model=ifcopenshell.open(str(case_root / "damaged.ifc")),
            repaired_model=ifcopenshell.open(str(case_root / "repaired.ifc")),
            changeset=json.loads((case_root / "changeset.json").read_text(encoding="utf-8")),
            application=json.loads((case_root / "application.json").read_text(encoding="utf-8")),
            predicates=[predicate],
        )


def test_r1_curator_rejects_injected_validation_for_noncanonical_collection(
    tmp_path: Path,
) -> None:
    from scripts.ifc_repair.curate_repair_milestone_r1_proof import curate_r1_proof

    source_root = tmp_path / "candidate"
    destination_root = tmp_path / "curated"
    source_root.mkdir()
    freeze_hash = _write_fixture_freeze(source_root)
    _write_json(
        source_root / "profiles.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-profiles/0.1",
            "provenance_namespace": "repair-milestone-r1",
            "freeze": {"path": "freeze.json", "sha256": freeze_hash},
            "execution_order": ["arbitrary-case"],
            "cases": [_r1_profile("arbitrary-case", "SUCCESS")],
        },
    )
    _write_json(
        source_root / "manifest.json",
        {
            "schema_version": "text2ifc/ifc-repair-proof-collection/0.2",
            "provenance_namespace": "repair-milestone-r1",
            "profile": "profiles.json",
            "case_count": 1,
            "cases": [{
                "case_id": "arbitrary-case",
                "status": "accepted",
                "terminal_class": "SUCCESS",
                "case_root": "cases/arbitrary-case",
                "files": "cases/arbitrary-case/FILES.json",
                "report": "cases/arbitrary-case/REPORT.md",
                "terminal_record": "cases/arbitrary-case/terminal.json",
            }],
        },
    )
    (source_root / "cases" / "arbitrary-case").mkdir(parents=True)
    _write_case_files(source_root / "cases" / "arbitrary-case", "arbitrary-case")

    with pytest.raises(ValueError, match="R1_CURATOR_VALIDATION_FAILED"):
        curate_r1_proof(
            source_root=source_root,
            destination_root=destination_root,
            validation_document={
                "schema_version": "text2ifc/ifc-repair-proof-validation/0.3",
                "status": "passed",
                "collection_root": source_root.as_posix(),
                "case_count": 1,
                "operation_count": 1,
                "checked_file_count": 0,
                "reopened_ifc_count": 2,
                "independently_recomputed_case_count": 1,
                "no_output_case_count": 0,
                "errors": [],
                "limitations": [],
                "cases": [{
                    "case_id": "arbitrary-case",
                    "provenance_namespace": "repair-milestone-r1",
                    "terminal_class": "SUCCESS",
                    "status": "passed",
                    "artifact_predicates": [],
                    "property_authority_coverage": "not_applicable",
                    "property_claim_count": 0,
                    "current_property_acceptance_eligible": True,
                    "source_immutable": True,
                    "published_artifact_present": True,
                }],
            },
        )

    assert not destination_root.exists()
