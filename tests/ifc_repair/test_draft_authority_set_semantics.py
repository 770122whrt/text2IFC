"""Failure family: draft authority scope/evidence order semantics.

Root cause (composite milestone live C3): ``_require_exact_draft_authority``
compared ``scope.target_ids`` and ``evidence_refs`` with strict ordered list
equality, while the deterministic authority itself builds both as
``sorted(set(...))``.  A live Provider that returns the same identifiers in a
different order is a set-equivalent draft, yet was rejected with
``DRAFT_AUTHORITY_SCOPE_MISMATCH`` / ``DRAFT_AUTHORITY_EVIDENCE_MISMATCH``.

The contract published to the Provider (changeset draft schema) declares
these fields with ``uniqueItems: true`` — i.e. they are identifier sets, not
ordered sequences.  This family freezes the repaired invariant: set-equivalent
reordering binds; any identifier drift, duplication, or forbidden-set change
still fails closed.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from text2ifc_agent.providers import ProviderOutput
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.provider_stage import generate_bound_changeset
from text2ifc_ifc_repair.semantic_authoring import parse_semantic_manifest


MODEL = "sha256:" + "a" * 64
REQUEST = "sha256:" + "b" * 64
MANIFEST_HASH = "sha256:" + "c" * 64
STOREY_ID = "0K_MqVdrL0JOCMi_GblRwJ"
STOREY_ID_2 = "0K_MqVdrL0JOCMi_GblRwK"
BEAM_EVIDENCE = "resolved:/operations/beam-1/context/candidate_targets/0"
COLUMN_EVIDENCE = "resolved:/operations/column-1/context/candidate_targets/0"


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
        "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
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
            "policy": {"policy_id": f"{family}.add.l2", "policy_version": "0.1"},
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


def _resolved_operations() -> tuple[dict, dict]:
    storey_candidate = {
        "ifc_global_id": STOREY_ID,
        "ifc_class": "IfcBuildingStorey",
    }
    storey_candidate_2 = {
        "ifc_global_id": STOREY_ID_2,
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
                "candidate_targets": [storey_candidate],
            },
        },
        {
            "operation_id": "column-1",
            "operation_type": "add_column",
            "target_global_id": STOREY_ID_2,
            "scope_ids": [STOREY_ID_2],
            "evidence_pointers": [COLUMN_EVIDENCE],
            "parameters": _column_parameters(),
            "authorized_semantics": [],
            "context": {
                "model_fingerprint": MODEL,
                "candidate_targets": [storey_candidate_2],
            },
        },
    )


def _draft() -> dict:
    return {
        "schema_version": "text2ifc/ifc-repair-changeset-draft/0.3",
        "draft_id": "draft-set-semantics-1",
        "base_model_fingerprint": MODEL,
        "source_request_hash": REQUEST,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": MANIFEST_HASH,
        "semantic_summary": {
            "required": 2,
            "conditional": 0,
            "not_required": 0,
        },
        "scope": {"target_ids": [STOREY_ID_2, STOREY_ID], "forbidden_ids": []},
        "evidence_refs": [COLUMN_EVIDENCE, BEAM_EVIDENCE],
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
                "target": {"storey_global_id": STOREY_ID_2},
                "parameters": _column_parameters(),
                "evidence_refs": [COLUMN_EVIDENCE],
            },
        ],
    }


def _run(tmp_path: Path, draft: dict) -> dict:
    return generate_bound_changeset(
        provider=_Provider(draft),
        case_id="draft-authority-set-semantics",
        repair_request="add the resolved beam and column",
        source_request_hash=REQUEST,
        resolved_operations=_resolved_operations(),
        model_fingerprint=MODEL,
        registry=create_default_registry(),
        output_dir=tmp_path,
        max_attempts=1,
        semantic_manifests=(
            _manifest("beam-1", "add_beam"),
            _manifest("column-1", "add_column"),
        ),
        semantic_manifest_hashes={
            "beam-1": MANIFEST_HASH,
            "column-1": MANIFEST_HASH,
        },
    )


def test_reordered_scope_target_ids_bind() -> None:
    """Same identifier set, provider order — binds (live C3 shape)."""

    result = _run(Path("composite-evidence-setsem-01"), _draft())

    assert result["valid"] is True, result
    assert result["classification"] == "bound_changeset"
    assert set(result["changeset"]["scope"]["target_ids"]) == {
        STOREY_ID,
        STOREY_ID_2,
    }


def test_reordered_evidence_refs_bind() -> None:
    """Same evidence pointer set, provider order — binds."""

    draft = _draft()
    draft["evidence_refs"] = [BEAM_EVIDENCE, COLUMN_EVIDENCE]

    result = _run(Path("composite-evidence-setsem-02"), draft)

    assert result["valid"] is True, result


def test_reordered_operation_evidence_refs_bind() -> None:
    """Operation-level evidence pointer set in provider order — binds."""

    draft = _draft()
    draft["operations"][0]["evidence_refs"] = [BEAM_EVIDENCE]
    draft["operations"][1]["evidence_refs"] = [COLUMN_EVIDENCE]

    result = _run(Path("composite-evidence-setsem-03"), draft)

    assert result["valid"] is True, result


def test_reordered_forbidden_ids_bind() -> None:
    """A reordered but set-equal forbidden set passes the authority check."""

    foreign_a = "0FOREIGNAAAAAAAAAAAAAA"
    foreign_b = "0FOREIGNBBBBBBBBBBBBBB"
    from text2ifc_ifc_repair.changesets import _require_exact_draft_authority

    authority = {
        "scope": {
            "target_ids": [STOREY_ID, STOREY_ID_2],
            "forbidden_ids": [foreign_a, foreign_b],
        },
        "evidence_refs": [BEAM_EVIDENCE, COLUMN_EVIDENCE],
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
                "target": {"storey_global_id": STOREY_ID_2},
                "parameters": _column_parameters(),
                "evidence_refs": [COLUMN_EVIDENCE],
            },
        ],
    }
    draft_view = deepcopy(authority)
    draft_view["scope"]["target_ids"] = [STOREY_ID_2, STOREY_ID]
    draft_view["scope"]["forbidden_ids"] = [foreign_b, foreign_a]
    draft_view["evidence_refs"] = [COLUMN_EVIDENCE, BEAM_EVIDENCE]
    draft_view["operations"][0]["evidence_refs"] = [BEAM_EVIDENCE]
    draft_view["operations"][1]["evidence_refs"] = [COLUMN_EVIDENCE]

    _require_exact_draft_authority(draft_view, authority)


@pytest.mark.parametrize(
    ("case", "mutate", "expected_code"),
    [
        (
            "scope-extra-target",
            lambda draft: draft["scope"]["target_ids"].append(
                "0FOREIGNAAAAAAAAAAAAAA"
            ),
            "DRAFT_AUTHORITY_SCOPE_MISMATCH",
        ),
        (
            "scope-missing-target",
            lambda draft: draft["scope"]["target_ids"].pop(),
            "DRAFT_AUTHORITY_SCOPE_MISMATCH",
        ),
        (
            "scope-duplicate-target",
            lambda draft: draft["scope"]["target_ids"].append(STOREY_ID),
            "DRAFT_SCHEMA_VALIDATION_ERROR",
        ),
        (
            "evidence-extra-ref",
            lambda draft: draft["evidence_refs"].append(
                "resolved:/operations/foreign/context/candidate_targets/0"
            ),
            "DRAFT_AUTHORITY_EVIDENCE_MISMATCH",
        ),
        (
            "evidence-missing-ref",
            lambda draft: draft["evidence_refs"].pop(),
            "DRAFT_AUTHORITY_EVIDENCE_MISMATCH",
        ),
        (
            "evidence-duplicate-ref",
            lambda draft: draft["evidence_refs"].append(BEAM_EVIDENCE),
            "DRAFT_SCHEMA_VALIDATION_ERROR",
        ),
    ],
)
def test_identifier_drift_still_fails_closed(
    case: str, mutate, expected_code: str
) -> None:
    draft = _draft()
    mutate(draft)

    result = _run(Path(f"composite-evidence-setsem-drift-{case}"), draft)

    assert result["valid"] is False, case
    assert any(
        expected_code in str(issue.get("code", ""))
        for issue in result["issues"]
    ), (case, result["issues"])
