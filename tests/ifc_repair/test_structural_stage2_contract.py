from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

import text2ifc_ifc_repair.prompt_profiles as prompt_profiles_module
from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.prompt_profiles import (
    PromptProfileError,
    load_prompt_profiles,
    select_prompt_profiles,
)
from text2ifc_ifc_repair.provider_stage import generate_bound_changeset
from text2ifc_ifc_repair.semantic_authoring import parse_semantic_manifest


MODEL = "sha256:" + "a" * 64
REQUEST = "sha256:" + "b" * 64
MANIFEST_HASH = "sha256:" + "c" * 64
STOREY_ID = "0K_MqVdrL0JOCMi_GblRwJ"
BEAM_EVIDENCE = "resolved:/operations/beam-1/context/candidate_targets/0"
COLUMN_EVIDENCE = (
    "resolved:/operations/column-1/context/candidate_targets/0"
)
WINDOW_ID = "1hOSvn6df7F8_7GcBWlRLx"
H1_STOREY_ID = "1xS3BCk291UvhgP2dvNMKI"
WINDOW_EVIDENCE = "resolved:/operations/window-property-1/context/candidate_targets/0"


class _Provider:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[dict] = []

    def generate_candidate(self, **kwargs) -> ProviderOutput:
        self.calls.append(kwargs)
        return ProviderOutput(
            text=json.dumps(self.response, ensure_ascii=False),
            metadata={"provider": "fixture", "model": "fixture-model"},
        )


def _beam_parameters() -> dict:
    return {
        "axis": {
            "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
            "end": {"x_mm": 5000, "y_mm": 0, "z_mm": 3000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 300,
            "height_mm": 500,
        },
    }


def _column_parameters() -> dict:
    return {
        "axis": {
            "base": {"x_mm": 1000, "y_mm": 2000, "z_mm": 0},
            "top": {"x_mm": 1000, "y_mm": 2000, "z_mm": 3000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 0, "y": 1},
        },
    }


def _resolved_operations() -> tuple[dict, dict]:
    candidate = {
        "ifc_global_id": STOREY_ID,
        "ifc_class": "IfcBuildingStorey",
    }
    return (
        {
            "operation_id": "beam-1",
            "operation_type": "add_beam",
            "target_global_id": STOREY_ID,
            "scope_ids": [STOREY_ID],
            "evidence_pointers": [BEAM_EVIDENCE],
            "parameters": _beam_parameters(),
            "authorized_semantics": [],
            "context": {
                "model_fingerprint": MODEL,
                "candidate_targets": [candidate],
            },
        },
        {
            "operation_id": "column-1",
            "operation_type": "add_column",
            "target_global_id": STOREY_ID,
            "scope_ids": [STOREY_ID],
            "evidence_pointers": [COLUMN_EVIDENCE],
            "parameters": _column_parameters(),
            "authorized_semantics": [],
            "context": {
                "model_fingerprint": MODEL,
                "candidate_targets": [candidate],
            },
        },
    )


def _manifest(operation_id: str, operation_type: str):
    family = "beam" if operation_type == "add_beam" else "column"
    ifc_type = "IfcBeamType" if family == "beam" else "IfcColumnType"
    return parse_semantic_manifest(
        {
            "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.3",
            "manifest_id": f"manifest-{operation_id}",
            "operation_id": operation_id,
            "operation_type": operation_type,
            "base_model_fingerprint": MODEL,
            "policy": {
                "policy_id": f"{family}.add.l2",
                "policy_version": "0.1",
            },
            "assignments": [
                {
                    "operation_id": operation_id,
                    "scope": f"{family}_occurrence",
                    "fact_key": "relationship:type",
                    "source_fact_key": "relationship:type",
                    "value": f"GENERATED-{ifc_type.upper()}-{operation_id}",
                    "value_type": ifc_type,
                    "unit": None,
                    "ownership": "type_inherited",
                    "applicability": "required",
                    "source_kind": "deterministic_derived",
                    "source_ref": f"generated-type:{operation_id}",
                    "provenance": ["generated-type-template:0.1"],
                    "authoring_action": "inherit_from_type",
                }
            ],
        }
    )


def _manifests() -> tuple:
    return (
        _manifest("beam-1", "add_beam"),
        _manifest("column-1", "add_column"),
    )


def _property_manifest():
    return parse_semantic_manifest(
        {
            "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.3",
            "manifest_id": "manifest-window-property-1",
            "operation_id": "window-property-1",
            "operation_type": "set_occurrence_properties",
            "base_model_fingerprint": MODEL,
            "policy": {
                "policy_id": "occurrence.property.l2",
                "policy_version": "0.1",
            },
            "assignments": [
                {
                    "operation_id": "window-property-1",
                    "scope": "window_occurrence",
                    "fact_key": "pset:Pset_WindowCommon.FireRating",
                    "source_fact_key": "request:/properties/0",
                    "value": "EI60",
                    "value_type": "IfcLabel",
                    "unit": None,
                    "ownership": "occurrence_direct",
                    "applicability": "required",
                    "source_kind": "explicit_value",
                    "source_ref": "request:/properties/0",
                    "provenance": ["request:r1-h1"],
                    "authoring_action": "set_occurrence_pset",
                }
            ],
        }
    )


def _legacy_property_manifest():
    """Mirror the frozen H1 exact-property manifest contract (0.1)."""

    return parse_semantic_manifest(
        {
            "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.1",
            "manifest_id": "manifest-window-property-1-legacy",
            "operation_id": "window-property-1",
            "operation_type": "set_occurrence_properties",
            "base_model_fingerprint": MODEL,
            "policy": {
                "policy_id": "occurrence.property.l2",
                "policy_version": "0.1",
            },
            "assignments": [
                {
                    "operation_id": "window-property-1",
                    "fact_key": "pset:Pset_WindowCommon.FireRating",
                    "source_fact_key": "request:/properties/0",
                    "value": "EI60",
                    "value_type": "IfcLabel",
                    "unit": None,
                    "ownership": "occurrence_direct",
                    "applicability": "conditional",
                    "source_kind": "explicit_request",
                    "source_ref": "request:/properties/0",
                    "provenance": ["request:r1-h1"],
                    "authoring_action": "set_occurrence_pset",
                }
            ],
        }
    )


def _mixed_resolved_operations() -> tuple[dict, dict]:
    beam = deepcopy(_resolved_operations()[0])
    return (
        beam,
        {
            "operation_id": "window-property-1",
            "operation_type": "set_occurrence_properties",
            "target_global_id": WINDOW_ID,
            "scope_ids": [WINDOW_ID],
            "evidence_pointers": [WINDOW_EVIDENCE],
            "parameters": {},
            "authorized_semantics": [],
            "context": {
                "model_fingerprint": MODEL,
                "candidate_targets": [
                    {
                        "ifc_global_id": WINDOW_ID,
                        "ifc_class": "IfcWindow",
                    }
                ],
            },
        },
    )


def _mixed_draft() -> dict:
    draft = deepcopy(_draft())
    draft["schema_version"] = "text2ifc/ifc-repair-changeset-draft/0.2"
    draft["draft_id"] = "draft-r1-h1"
    draft["semantic_summary"]["required"] = 2
    draft["scope"]["target_ids"] = [STOREY_ID, WINDOW_ID]
    draft["evidence_refs"] = [BEAM_EVIDENCE, WINDOW_EVIDENCE]
    draft["operations"] = [
        draft["operations"][0],
        {
            "operation_id": "window-property-1",
            "operation_type": "set_occurrence_properties",
            "target": {"element_global_id": WINDOW_ID},
            "parameters": {},
            "evidence_refs": [WINDOW_EVIDENCE],
        },
    ]
    return draft


def _run_mixed(tmp_path: Path, draft: dict) -> dict:
    return generate_bound_changeset(
        provider=_Provider(draft),
        case_id="r1-h1-mixed-stage2",
        repair_request="Add the Beam and set Window FireRating atomically.",
        source_request_hash=REQUEST,
        resolved_operations=_mixed_resolved_operations(),
        model_fingerprint=MODEL,
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        semantic_manifests=(
            _manifest("beam-1", "add_beam"),
            _property_manifest(),
        ),
        semantic_manifest_hashes={
            "beam-1": MANIFEST_HASH,
            "window-property-1": MANIFEST_HASH,
        },
    )


def test_h1_mixed_stage2_prompt_exposes_complete_canonical_authority(
    tmp_path: Path,
) -> None:
    operations = [deepcopy(item) for item in _mixed_resolved_operations()]
    operations[0]["target_global_id"] = H1_STOREY_ID
    operations[0]["scope_ids"] = [H1_STOREY_ID]
    operations[0]["context"]["candidate_targets"][0]["ifc_global_id"] = (
        H1_STOREY_ID
    )
    draft = _mixed_draft()
    draft["scope"]["target_ids"] = [WINDOW_ID, H1_STOREY_ID]
    draft["operations"][0]["target"] = {
        "storey_global_id": H1_STOREY_ID
    }

    output = tmp_path / "h1-canonical-authority"
    result = generate_bound_changeset(
        provider=_Provider(draft),
        case_id="r1-h1-canonical-authority",
        repair_request="Add the Beam and set Window FireRating atomically.",
        source_request_hash=REQUEST,
        resolved_operations=operations,
        model_fingerprint=MODEL,
        registry=create_default_registry(),
        output_dir=output,
        max_attempts=1,
        semantic_manifests=(
            _manifest("beam-1", "add_beam"),
            _property_manifest(),
        ),
        semantic_manifest_hashes={
            "beam-1": MANIFEST_HASH,
            "window-property-1": MANIFEST_HASH,
        },
    )

    renderer_input = json.loads(
        (output / "attempt-001" / "renderer-input.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["valid"] is True
    assert renderer_input["RESOLVED_OPERATIONS"]["scope"] == {
        "target_ids": [WINDOW_ID, H1_STOREY_ID],
        "forbidden_ids": [],
    }
    assert renderer_input["RESOLVED_OPERATIONS"]["evidence_refs"] == [
        BEAM_EVIDENCE,
        WINDOW_EVIDENCE,
    ]
    assert [
        item["operation_id"]
        for item in renderer_input["RESOLVED_OPERATIONS"]["operations"]
    ] == ["beam-1", "window-property-1"]
    assert result["prompt"]["template_id"] == "ifc-repair-changeset.v0.5"
    rendered_prompt = (
        output / "attempt-001" / "rendered-prompt.md"
    ).read_text(encoding="utf-8")
    normalized_prompt = " ".join(rendered_prompt.split()).lower()
    assert "canonical envelope authority" in normalized_prompt
    assert "preserve every list order" in normalized_prompt
    assert "do not reconstruct or sort" in normalized_prompt


def test_h1_mixed_manifest_versions_preserve_each_assignment_contract(
    tmp_path: Path,
) -> None:
    result = generate_bound_changeset(
        provider=_Provider(_mixed_draft()),
        case_id="r1-h1-mixed-manifest-versions",
        repair_request="Add the Beam and set Window FireRating atomically.",
        source_request_hash=REQUEST,
        resolved_operations=_mixed_resolved_operations(),
        model_fingerprint=MODEL,
        registry=create_default_registry(),
        output_dir=tmp_path / "h1-mixed-manifest-versions",
        max_attempts=1,
        semantic_manifests=(
            _manifest("beam-1", "add_beam"),
            _legacy_property_manifest(),
        ),
        semantic_manifest_hashes={
            "beam-1": MANIFEST_HASH,
            "window-property-1": MANIFEST_HASH,
        },
    )

    assert result["valid"] is True
    assert result["changeset"]["schema_version"] == (
        "text2ifc/ifc-repair-changeset/0.5"
    )
    assignments = {
        operation["operation_id"]: operation["semantic_assignments"]
        for operation in result["changeset"]["operations"]
    }
    assert assignments["beam-1"][0]["source_kind"] == "deterministic_derived"
    assert assignments["beam-1"][0]["scope"] == "beam_occurrence"
    assert assignments["window-property-1"][0]["source_kind"] == "explicit_request"
    assert "scope" not in assignments["window-property-1"][0]
    assert "derivation" not in assignments["window-property-1"][0]


def _draft() -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-changeset-draft/0.3",
        "draft_id": "draft-structural-1",
        "base_model_fingerprint": MODEL,
        "source_request_hash": REQUEST,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": MANIFEST_HASH,
        "semantic_summary": {
            "required": 2,
            "conditional": 0,
            "not_required": 0,
        },
        "scope": {"target_ids": [STOREY_ID], "forbidden_ids": []},
        "evidence_refs": [BEAM_EVIDENCE, COLUMN_EVIDENCE],
        "preconditions": [
            "target_exists",
            "structural_axis_available",
            "structural_type_authorized",
        ],
        "postconditions": [
            "beam_geometry_matches",
            "beam_contained_in_storey",
            "beam_type_bound",
            "column_geometry_matches",
            "column_contained_in_base_storey",
            "column_type_bound",
        ],
        "operations": [
            {
                "operation_id": "beam-1",
                "operation_type": "add_beam",
                "target": {"storey_global_id": STOREY_ID},
                "parameters": _beam_parameters(),
                "evidence_refs": [BEAM_EVIDENCE],
            },
            {
                "operation_id": "column-1",
                "operation_type": "add_column",
                "target": {"storey_global_id": STOREY_ID},
                "parameters": _column_parameters(),
                "evidence_refs": [COLUMN_EVIDENCE],
            },
        ],
    }


def _run(tmp_path: Path, draft: dict) -> tuple[dict, _Provider]:
    provider = _Provider(draft)
    result = generate_bound_changeset(
        provider=provider,
        case_id="structural-stage2",
        repair_request="add the resolved beam and column",
        source_request_hash=REQUEST,
        resolved_operations=_resolved_operations(),
        model_fingerprint=MODEL,
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        semantic_manifests=_manifests(),
        semantic_manifest_hashes={
            "beam-1": MANIFEST_HASH,
            "column-1": MANIFEST_HASH,
        },
    )
    return result, provider


def test_structural_stage2_profiles_are_separate_draft_only_contracts() -> None:
    registry = create_default_registry()
    beam = registry.require("add_beam")
    column = registry.require("add_column")

    assert beam.prompt_profile_id == "beam.add.v0.3"
    assert column.prompt_profile_id == "column.add.v0.3"
    assert beam.stage2_prompt_profile_id == "beam.add.stage2.v0.1"
    assert column.stage2_prompt_profile_id == "column.add.stage2.v0.1"

    selected = select_prompt_profiles(
        [beam.stage2_prompt_profile_id, column.stage2_prompt_profile_id]
    )
    assert selected.profile_ids == (
        "beam.add.stage2.v0.1",
        "column.add.stage2.v0.1",
    )
    assert selected.few_shot_ids == (
        "beam.add.stage2.v0.1.complete",
        "column.add.stage2.v0.1.complete",
    )
    payload = selected.to_dict()
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "prototype_intent",
        "target_query",
        "property_intents",
        "attribute_intents",
        "semantic_bundle_refs",
        "occurrence_reuse_intent",
        '"status"',
    ):
        assert forbidden not in serialized

    for example in payload["few_shots"]:
        assert example["output_schema"] == (
            "text2ifc/ifc-repair-stage2-operation/0.1"
        )
        assert set(example["expected"]) == {
            "operation_id",
            "operation_type",
            "target",
            "parameters",
            "evidence_refs",
        }


def test_h1_mixed_binder_rejects_property_target_drift(
    tmp_path: Path,
) -> None:
    draft = _mixed_draft()
    draft["operations"][1]["target"]["element_global_id"] = (
        "0FOREIGNWINDOWTARGET00"
    )

    result = _run_mixed(tmp_path, draft)

    assert result["valid"] is False
    assert {
        issue["code"] for issue in result["issues"]
    } == {"DRAFT_AUTHORITY_TARGET_MISMATCH"}
    assert result["changeset"] is None


def test_h1_mixed_binder_accepts_set_equivalent_scope_without_identity_drift(
    tmp_path: Path,
) -> None:
    operations = [deepcopy(item) for item in _mixed_resolved_operations()]
    operations[0]["target_global_id"] = H1_STOREY_ID
    operations[0]["scope_ids"] = [H1_STOREY_ID]
    operations[0]["context"]["candidate_targets"][0]["ifc_global_id"] = (
        H1_STOREY_ID
    )
    draft = _mixed_draft()
    draft["scope"]["target_ids"] = [H1_STOREY_ID, WINDOW_ID]
    draft["operations"][0]["target"] = {
        "storey_global_id": H1_STOREY_ID
    }

    result = generate_bound_changeset(
        provider=_Provider(draft),
        case_id="r1-h1-reordered-scope",
        repair_request="Add the Beam and set Window FireRating atomically.",
        source_request_hash=REQUEST,
        resolved_operations=operations,
        model_fingerprint=MODEL,
        registry=create_default_registry(),
        output_dir=tmp_path / "h1-reordered-scope",
        max_attempts=1,
        semantic_manifests=(
            _manifest("beam-1", "add_beam"),
            _property_manifest(),
        ),
        semantic_manifest_hashes={
            "beam-1": MANIFEST_HASH,
            "window-property-1": MANIFEST_HASH,
        },
    )

    # Root's frozen set-semantics family permits identifier reordering while
    # rejecting missing, extra and duplicate identifiers. Exact authority
    # membership remains mandatory regardless of the draft's identifier order.
    assert result["valid"] is True
    assert set(result["changeset"]["scope"]["target_ids"]) == {
        WINDOW_ID, H1_STOREY_ID
    }


def test_stage2_few_shot_expected_cannot_drift_from_declared_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = json.loads(
        (
            prompt_profiles_module.DEFAULT_PROFILE_DIR
            / "beam.add.stage2.v0.1.json"
        ).read_text(encoding="utf-8")
    )
    example = json.loads(
        (
            prompt_profiles_module.PROJECT_ROOT
            / profile["few_shots"][0]["path"]
        ).read_text(encoding="utf-8")
    )
    example["expected"]["parameters"]["prototype_intent"] = None

    example_path = (
        tmp_path
        / "prompts/agent/ifc-repair-few-shots/beam-stage2-invalid.json"
    )
    example_path.parent.mkdir(parents=True)
    example_path.write_text(
        json.dumps(example, ensure_ascii=False), encoding="utf-8"
    )
    raw = example_path.read_bytes()
    profile["few_shots"] = [
        {
            "example_id": example["example_id"],
            "path": (
                "prompts/agent/ifc-repair-few-shots/beam-stage2-invalid.json"
            ),
            "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        }
    ]
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    (profile_dir / "beam.add.stage2.v0.1.json").write_text(
        json.dumps(profile, ensure_ascii=False), encoding="utf-8"
    )
    monkeypatch.setattr(prompt_profiles_module, "PROJECT_ROOT", tmp_path)

    with pytest.raises(
        PromptProfileError,
        match="STAGE2_FEW_SHOT_EXPECTED_SCHEMA_INVALID",
    ):
        load_prompt_profiles(profile_dir)


def test_structural_stage2_projection_and_unchanged_authority_bind(
    tmp_path: Path,
) -> None:
    result, provider = _run(tmp_path, _draft())

    assert result["valid"] is True, result
    assert result["classification"] == "bound_changeset"
    selection = json.loads(
        (tmp_path / "prompt-profile-selection.json").read_text(
            encoding="utf-8"
        )
    )
    assert selection["profile_ids"] == [
        "beam.add.stage2.v0.1",
        "column.add.stage2.v0.1",
    ]
    renderer_input = json.loads(
        (tmp_path / "attempt-001/renderer-input.json").read_text(
            encoding="utf-8"
        )
    )
    assert renderer_input["CHANGESET_SCHEMA"]["$id"] == (
        "text2ifc/ifc-repair-changeset-draft/0.3"
    )
    assert renderer_input["RESOLVED_OPERATIONS"] == {
        "scope": {"target_ids": [STOREY_ID], "forbidden_ids": []},
        "evidence_refs": [BEAM_EVIDENCE, COLUMN_EVIDENCE],
        "operations": _draft()["operations"],
    }
    serialized_call = json.dumps(
        provider.calls[0], ensure_ascii=False, sort_keys=True
    )
    assert "prototype_intent" not in serialized_call
    assert "target_query" not in serialized_call
    for forbidden in (
        "prototype_ifc_classes",
        "prototype_dimension_paths",
        "IfcBeamType",
        "IfcColumnType",
        "generated_type",
    ):
        assert forbidden not in serialized_call
    for operation in result["changeset"]["operations"]:
        assert operation["parameters"] == next(
            item["parameters"]
            for item in _draft()["operations"]
            if item["operation_id"] == operation["operation_id"]
        )
        type_assignments = [
            item
            for item in operation["semantic_assignments"]
            if item["fact_key"] == "relationship:type"
        ]
        assert len(type_assignments) == 1
        assert "prototype_intent" not in operation


@pytest.mark.parametrize(
    ("case", "mutate", "expected_code"),
    [
        (
            "beam-coordinate",
            lambda draft: draft["operations"][0]["parameters"]["axis"][
                "end"
            ].update(x_mm=5100),
            "DRAFT_AUTHORITY_PARAMETERS_MISMATCH",
        ),
        (
            "column-section",
            lambda draft: draft["operations"][1]["parameters"][
                "section"
            ].update(depth_mm=650),
            "DRAFT_AUTHORITY_PARAMETERS_MISMATCH",
        ),
        (
            "column-orientation",
            lambda draft: draft["operations"][1]["parameters"][
                "section"
            ]["orientation"].update(x=1, y=0),
            "DRAFT_AUTHORITY_PARAMETERS_MISMATCH",
        ),
        (
            "target",
            lambda draft: draft["operations"][0]["target"].update(
                storey_global_id="0FOREIGNAAAAAAAAAAAAAA"
            ),
            "DRAFT_AUTHORITY_TARGET_MISMATCH",
        ),
        (
            "operation-evidence",
            lambda draft: draft["operations"][0].update(
                evidence_refs=[COLUMN_EVIDENCE]
            ),
            "DRAFT_AUTHORITY_OPERATION_EVIDENCE_MISMATCH",
        ),
        (
            "resolved-scope",
            lambda draft: draft["scope"].update(
                target_ids=[STOREY_ID, "0FOREIGNAAAAAAAAAAAAAA"]
            ),
            "DRAFT_AUTHORITY_SCOPE_MISMATCH",
        ),
        (
            "envelope-evidence",
            lambda draft: draft.update(evidence_refs=[BEAM_EVIDENCE]),
            "DRAFT_AUTHORITY_EVIDENCE_MISMATCH",
        ),
        (
            "cardinality",
            lambda draft: draft["operations"].pop(),
            "DRAFT_AUTHORITY_OPERATION_CARDINALITY_MISMATCH",
        ),
        (
            "operation-id",
            lambda draft: draft["operations"][0].update(
                operation_id="beam-foreign"
            ),
            "DRAFT_AUTHORITY_OPERATION_ID_SET_MISMATCH",
        ),
        (
            "operation-type",
            lambda draft: draft["operations"][0].update(
                operation_type="add_column",
                parameters=_column_parameters(),
            ),
            "DRAFT_AUTHORITY_OPERATION_TYPE_MISMATCH",
        ),
    ],
)
def test_structural_binder_rejects_provider_changes_to_resolved_authority(
    tmp_path: Path,
    case: str,
    mutate,
    expected_code: str,
) -> None:
    draft = deepcopy(_draft())
    mutate(draft)

    result, _ = _run(tmp_path / case, draft)

    assert result["valid"] is False
    assert expected_code in {issue["code"] for issue in result["issues"]}
    assert result["changeset"] is None
    assert not (tmp_path / case / "bound-changeset.json").exists()


@pytest.mark.parametrize(
    ("case", "mutate", "expected_path_prefix"),
    [
        (
            "historical-prototype-intent",
            lambda draft: draft["operations"][0]["parameters"].update(
                prototype_intent=None
            ),
            "/operations/",
        ),
        (
            "unknown-parameter",
            lambda draft: draft["operations"][1]["parameters"].update(
                guessed_height_mm=3000
            ),
            "/operations/",
        ),
        (
            "missing-required-geometry",
            lambda draft: draft["operations"][0]["parameters"]["axis"].pop(
                "end"
            ),
            "/operations/",
        ),
        (
            "wrong-parameter-nesting",
            lambda draft: draft["operations"][1]["parameters"].update(
                orientation={"x": 0, "y": 1}
            ),
            "/operations/",
        ),
        (
            "wrong-target-shape",
            lambda draft: draft["operations"][0].update(
                target={"target_global_id": STOREY_ID}
            ),
            "/operations/",
        ),
        (
            "downgraded-draft-contract",
            lambda draft: draft.update(
                schema_version="text2ifc/ifc-repair-changeset-draft/0.2"
            ),
            "/schema_version",
        ),
    ],
)
def test_structural_draft_rejects_non_executable_shapes_before_binding(
    tmp_path: Path,
    case: str,
    mutate,
    expected_path_prefix: str,
) -> None:
    draft = deepcopy(_draft())
    mutate(draft)

    result, _ = _run(tmp_path / case, draft)

    assert result["valid"] is False
    assert {issue["code"] for issue in result["issues"]} == {
        "DRAFT_SCHEMA_VALIDATION_ERROR"
    }
    assert any(
        issue["path"].startswith(expected_path_prefix)
        for issue in result["issues"]
    )
    assert result["changeset"] is None
    assert not (tmp_path / case / "bound-changeset.json").exists()
