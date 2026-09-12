"""Failure-family regression tests for the mixed-manifest binding defect.

Defect (frozen before the fix): a ChangeSet mixing a structural operation
(``add_beam``/``add_column``, whose policy-facts hooks emit
``canonical_source_kind="deterministic_derived"`` → manifest v0.3) with a
window operation (whose hook gated the canonical kind on
``authorized_occurrence_assignment`` → manifest v0.1) negotiated the bound
envelope DOWN to schema 0.2, whose ``source_kind`` enum does not contain
``deterministic_derived``.  ``bind_repair_changeset`` then failed with
``BOUND_CHANGESET_INVALID`` on the FIRST (structural) operation — no window
composite could ever bind through the live/public path.

Violated invariant: manifest-version negotiation must not downgrade the
envelope below the vocabulary the manifests themselves carry.  Fix: the
window hook sets the canonical kind unconditionally, exactly like its
siblings (beam/column/door), so a window manifest is v0.3 and mixed families
negotiate the 0.4 envelope where both vocabularies are legal.

Family coverage (AGENTS.md: positive, negative, boundary, cross-scene):

* positive — mixed beam+window / column+window / three-family manifests bind
  (these were the original red family);
* boundary — window-only and structural-only manifests keep binding;
* negative — genuinely illegal source kinds still fail closed under every
  envelope (the fix must not weaken validation);
* cross-scene — varied window geometry and multiple repeated operations.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_ifc_repair.changesets import bind_repair_changeset  # noqa: E402
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402
from text2ifc_ifc_repair.production_evidence import (  # noqa: E402
    ApplicabilityDecision,
    ProductionEvidence,
)
from text2ifc_ifc_repair.semantic_authoring import (  # noqa: E402
    build_semantic_manifest,
    parse_semantic_manifest,
    semantic_manifest_to_dict,
)

MODEL = "sha256:" + "a" * 64
REQUEST = "sha256:" + "b" * 64
MANIFEST_HASH = "sha256:" + "c" * 64


def _window_operation(operation_id: str = "W-1") -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_window_with_opening_to_wall",
        "target": {"wall_global_id": "WALL-1"},
        "parameters": {
            "position": {"reference": "wall_local_start", "center_offset_mm": 2000},
            "opening": {"width_mm": 1200, "height_mm": 1500, "sill_height_mm": 900},
            "window": {"fit_opening": True},
        },
    }


def _beam_operation(operation_id: str = "B-1") -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_beam",
        "target": {"storey_global_id": "STOREY-1"},
        "parameters": {
            "axis": {
                "start": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
                "end": {"x_mm": 6000, "y_mm": 0, "z_mm": 3000},
            },
            "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
        },
    }


def _column_operation(operation_id: str = "C-1") -> dict:
    return {
        "operation_id": operation_id,
        "operation_type": "add_column",
        "target": {"storey_global_id": "STOREY-1"},
        "parameters": {
            "axis": {
                "base": {"x_mm": 0, "y_mm": 0, "z_mm": 0},
                "top": {"x_mm": 0, "y_mm": 0, "z_mm": 3000},
            },
            "section": {
                "shape": "rectangle",
                "width_mm": 400,
                "depth_mm": 600,
                "orientation": {"x": 0, "y": 1},
            },
        },
    }


def _manifest_document(operation: dict) -> dict:
    """Build the REAL manifest the live path produces for one operation.

    Mirrors ``api.py``'s call shape: policy facts from the registry hook, an
    applicability decision per policy spec, then
    ``registry.build_semantic_manifest``.
    """

    registry = create_default_registry()
    operation_id = operation["operation_id"]
    operation_type = operation["operation_type"]
    policy = registry.require_evaluation_policy(operation_type)
    facts = registry.build_semantic_policy_facts(
        operation_type, operation=operation
    )
    applicability = {
        spec.check_id: ApplicabilityDecision(
            check_id=spec.check_id,
            applicability=spec.applicability.value,
            mandatory=spec.applicability.value == "required",
            outcome="evaluable",
            verified_absence=False,
            evidence_pointer=f"resolved:/operations/{operation_id}",
        )
        for spec in policy.semantic_facts
    }
    evidence = ProductionEvidence(
        expected_facts_by_operation={operation_id: facts},
        candidate_facts_by_operation={},
        applicability_by_operation={operation_id: applicability},
        operation_types={operation_id: operation_type},
        conflicts=(),
    )
    manifest = build_semantic_manifest(
        production_evidence=evidence,
        operation_id=operation_id,
        base_model_fingerprint=MODEL,
        registry=registry,
    )
    return semantic_manifest_to_dict(manifest)


def _negotiated_envelope(manifest_documents: list[dict]) -> str:
    """Mirror ``provider_stage.py`` bound-schema negotiation exactly."""

    versions = {doc["schema_version"] for doc in manifest_documents}
    if versions == {"text2ifc/ifc-repair-semantic-manifest/0.3"}:
        return "text2ifc/ifc-repair-changeset/0.4"
    if versions == {"text2ifc/ifc-repair-semantic-manifest/0.2"}:
        return "text2ifc/ifc-repair-changeset/0.3"
    return "text2ifc/ifc-repair-changeset/0.2"


def _bind(operations: list[dict]) -> dict:
    manifest_documents = [_manifest_document(op) for op in operations]
    manifests = [parse_semantic_manifest(doc) for doc in manifest_documents]
    scope_ids = list(
        dict.fromkeys(next(iter(op["target"].values())) for op in operations)
    )
    draft = {
        "schema_version": "text2ifc/ifc-repair-changeset-draft/0.2",
        "draft_id": "draft-mixed",
        "base_model_fingerprint": MODEL,
        "source_request_hash": REQUEST,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": MANIFEST_HASH,
        "semantic_summary": {
            "required": sum(len(doc["assignments"]) for doc in manifest_documents),
            "conditional": 0,
            "not_required": 0,
        },
        "scope": {"target_ids": scope_ids, "forbidden_ids": []},
        "evidence_refs": [
            f"request:/operations/{op['operation_id']}" for op in operations
        ],
        "preconditions": [],
        "postconditions": [],
        "operations": [
            {
                "operation_id": op["operation_id"],
                "operation_type": op["operation_type"],
                "target": op["target"],
                "parameters": op["parameters"],
                "evidence_refs": [f"request:/operations/{op['operation_id']}"],
            }
            for op in operations
        ],
    }
    return bind_repair_changeset(
        draft=draft,
        semantic_manifests=manifests,
        semantic_manifest_hashes={
            op["operation_id"]: MANIFEST_HASH for op in operations
        },
        source_request_hash=REQUEST,
        base_model_fingerprint=MODEL,
        bound_schema_version=_negotiated_envelope(manifest_documents),
    )


# ---------------------------------------------------------------------------
# Mechanism assertion + positive: mixed families bind (original red family)
# ---------------------------------------------------------------------------


def test_window_policy_facts_carry_canonical_source_kind() -> None:
    """The window hook must set the canonical kind like its siblings.

    Without it the window manifest downgrades to v0.1 and every mixed-family
    changeset fails to bind (envelope negotiated to 0.2 while structural
    manifests carry 0.3-only vocabulary).
    """

    registry = create_default_registry()
    facts = registry.build_semantic_policy_facts(
        "add_window_with_opening_to_wall", operation=_window_operation()
    )
    assert facts
    assert all(
        fact.canonical_source_kind == "deterministic_derived" for fact in facts
    ), [fact.canonical_source_kind for fact in facts]


def test_beam_plus_window_manifests_bind() -> None:
    bound = _bind([_beam_operation(), _window_operation()])
    assert bound["binding_status"] == "bound"
    assert bound["schema_version"] == "text2ifc/ifc-repair-changeset/0.4"
    assert [op["operation_id"] for op in bound["operations"]] == ["B-1", "W-1"]


def test_column_plus_window_manifests_bind() -> None:
    bound = _bind([_column_operation(), _window_operation()])
    assert bound["binding_status"] == "bound"
    assert bound["schema_version"] == "text2ifc/ifc-repair-changeset/0.4"


def test_three_family_mixed_manifests_bind() -> None:
    bound = _bind(
        [
            _beam_operation("B-1"),
            _column_operation("C-1"),
            _window_operation("W-1"),
        ]
    )
    assert bound["binding_status"] == "bound"
    assert bound["schema_version"] == "text2ifc/ifc-repair-changeset/0.4"


def test_repeated_mixed_operations_bind() -> None:
    bound = _bind(
        [
            _beam_operation("B-1"),
            _beam_operation("B-2"),
            _column_operation("C-1"),
            _window_operation("W-1"),
            _window_operation("W-2"),
        ]
    )
    assert bound["binding_status"] == "bound"
    assert len(bound["operations"]) == 5


# ---------------------------------------------------------------------------
# Boundary: single-family envelopes must stay green
# ---------------------------------------------------------------------------


def test_window_only_manifest_binds() -> None:
    bound = _bind([_window_operation()])
    assert bound["binding_status"] == "bound"
    assert bound["schema_version"] in {
        "text2ifc/ifc-repair-changeset/0.4",
        "text2ifc/ifc-repair-changeset/0.3",
    }


def test_beam_only_manifest_binds() -> None:
    bound = _bind([_beam_operation()])
    assert bound["binding_status"] == "bound"
    assert bound["schema_version"] == "text2ifc/ifc-repair-changeset/0.4"


def test_column_only_manifest_binds() -> None:
    bound = _bind([_column_operation()])
    assert bound["binding_status"] == "bound"
    assert bound["schema_version"] == "text2ifc/ifc-repair-changeset/0.4"


# ---------------------------------------------------------------------------
# Negative: the fix must not weaken validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_kind", ["totally_fabricated_kind", "deterministic_policy", "surviving_target"]
)
def test_illegal_source_kind_still_fails_closed_under_0_4(bad_kind: str) -> None:
    """Raw v0.1 vocabulary must NOT silently pass the 0.4 envelope.

    The fix upgrades the window manifest to v0.3; it must not relax the 0.4
    schema.  An assignment carrying a raw or fabricated ``source_kind`` under
    a 0.4 envelope still fails validation.
    """

    from text2ifc_ifc_repair.changesets import validate_changeset

    document = {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": "changeset-bad",
        "binding_status": "bound",
        "base_model_fingerprint": MODEL,
        "source_request_hash": REQUEST,
        "semantic_manifest_ref": "semantic-manifest.json",
        "semantic_manifest_sha256": MANIFEST_HASH,
        "scope": {"target_ids": ["WALL-1"], "forbidden_ids": []},
        "evidence_refs": ["request:/operations/W-1"],
        "preconditions": [],
        "postconditions": [],
        "operations": [
            {
                "operation_id": "W-1",
                "operation_type": "add_window_with_opening_to_wall",
                "target": {"wall_global_id": "WALL-1"},
                "parameters": _window_operation()["parameters"],
                "evidence_refs": ["request:/operations/W-1"],
                "semantic_manifest": {
                    "manifest_id": "m",
                    "policy_id": "window.add-with-opening.l2",
                    "policy_version": "0.1",
                },
                "semantic_assignments": [
                    {
                        "operation_id": "W-1",
                        "scope": "window_occurrence",
                        "fact_key": "attribute:OverallWidth",
                        "source_fact_key": "attribute:OverallWidth",
                        "value": 1200.0,
                        "value_type": "IfcPositiveLengthMeasure",
                        "unit": None,
                        "ownership": "occurrence_direct",
                        "applicability": "required",
                        "source_kind": bad_kind,
                        "source_ref": "resolved:/operations/W-1/parameters/opening",
                        "provenance": ["operation:W-1"],
                        "authoring_action": "set_attribute",
                    }
                ],
            }
        ],
    }
    issues = validate_changeset(document)
    assert any("source_kind" in issue.path for issue in issues), bad_kind


# ---------------------------------------------------------------------------
# Cross-scene: window parameter variation keeps the mechanism working
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "width,height,sill,offset",
    [
        (900, 1200, 900, 1000),
        (1800, 2100, 0, 4500),
        (1200, 1500, 900, 2000),
    ],
)
def test_mixed_binding_with_varied_window_geometry(
    width: float, height: float, sill: float, offset: float
) -> None:
    window = _window_operation()
    window["parameters"]["opening"]["width_mm"] = width
    window["parameters"]["opening"]["height_mm"] = height
    window["parameters"]["opening"]["sill_height_mm"] = sill
    window["parameters"]["position"]["center_offset_mm"] = offset
    bound = _bind([_column_operation(), window])
    assert bound["binding_status"] == "bound"
