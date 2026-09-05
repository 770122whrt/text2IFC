"""Offline full-chain preflight for the composite path (zero Provider).

Drives the REAL production ``RepairAPI`` (Stage 1 intent, target resolution,
Stage 2 binding, apply, reopen, strict L0/L1/L2) for every frozen composite
case, with only the external Provider transport mocked via the established
``_MockTransport``/``TranscriptProvider`` replay seam used by
``tests/ifc_repair/test_phase12_live_uat.py:1369``.  The intent and changeset
responses are derived deterministically from the frozen case bindings, so the
public path — including retrieval over the real index — is exercised
end-to-end offline.  This is the preflight required before any genuine
Provider call (AGENTS.md Section 4.2; specification Section 10.1).

Every artifact produced here is OFFLINE evidence only and must never be
reported as live-Provider evidence.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import ifcopenshell
import pytest

from scripts.ifc_repair import run_phase12_live_uat as live  # noqa: E402
from scripts.ifc_repair.composite_evidence.composite_proof import (  # noqa: E402
    CompositeProofError,
    verify_composite_case,
)
from scripts.ifc_repair.composite_evidence.offline_driver import (  # noqa: E402
    _resolve_opening_global_id,
    _resolve_wall_global_id,
    _structural_type_assignment,
    _hosted_type_assignment,
    _canonical_fill_door_parameters,
    load_freeze,
)
from scripts.ifc_repair.composite_evidence.preservation import (  # noqa: E402
    CompositePreservationError,
    verify_exact_composed_delta,
    verify_no_unrelated_mutation,
)
from scripts.ifc_repair.composite_evidence.strict_reopen import (  # noqa: E402
    strict_reopen_verification,
)
from tests.ifc_repair.test_phase12_live_uat import (  # noqa: E402
    _MockTransport,
    _labeled_prompt_json,
    _public_source,
    _prompt_json,
)
from tests.ifc_repair.test_property_resolution_family_e2e import (  # noqa: E402
    _FamilyEmbedding,
    _runtime as _offline_property_runtime,
)

FREEZE = load_freeze()
CASES_BY_ID = {case["case_id"]: case for case in FREEZE["cases"]}
MODEL_PATHS = {
    model_id: ROOT / str(model["path"]) for model_id, model in FREEZE["models"].items()
}


class _CompositeFamilyEmbedding(_FamilyEmbedding):
    """Offline fixture embedding with a fire-rating dimension.

    The shared family fixture recognizes external / self-closing / load-bearing
    semantics.  The frozen C5 hero case carries a ``Pset_DoorCommon.FireRating``
    natural-language claim, so the offline property runtime used by THIS test
    extends the fixture with a fire-rating dimension; the live runtime uses
    real embeddings where the phrase resolves normally.
    """

    def embed(self, texts):
        base = super().embed(texts)
        vectors = []
        for text, vector in zip(texts, base, strict=True):
            normalized = text.casefold().replace("_", "")
            vectors.append(
                [
                    *vector,
                    float(
                        "firerating" in normalized
                        or "fire rating" in normalized
                        or "防火" in normalized
                    ),
                ]
            )
        return vectors


def _composite_property_runtime():
    """Offline property runtime with the composite embedding (same seam)."""

    import json as _json

    from text2ifc_knowledge.property_runtime import create_property_runtime
    from text2ifc_knowledge.property_search import InMemoryVectorIndex
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
    policy = _json.loads(
        (
            ROOT
            / "schemas/ifc/knowledge/property_resolution_policy.v0.2.json"
        ).read_text(encoding="utf-8")
    )
    return create_property_runtime(
        registry=registry,
        standard_records=records,
        project_records=(),
        vector_index=InMemoryVectorIndex(_CompositeFamilyEmbedding()),
        policy_document=policy,
        corpus_version="ifc2x3-property-records/0.2",
        embedding_model_version="fixture-family-semantic/0.1",
        document_renderer_version="property-record-text/0.1",
        collection_version="ifc2x3-property-vector/0.2",
        runtime_mode="offline_test",
    )


def _sha256_text(value: str) -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _storey_query(case: Mapping[str, Any]) -> dict[str, Any]:
    query: dict[str, Any] = {
        "schema_version": "text2ifc/ifc-target-query/0.1",
        "allowed_ifc_classes": ["IfcBuildingStorey"],
        "names": [str(case["storey"]["name"])],
    }
    return query


def _routing_intent(operation_type: str, excerpt: str) -> dict[str, Any]:
    family = {
        "add_beam": "beam",
        "add_column": "column",
        "fill_existing_opening_with_door": "door",
        "add_door_with_opening_to_wall": "door",
        "add_window_with_opening_to_wall": "window",
    }[operation_type]
    action = {
        "add_beam": "add",
        "add_column": "add",
        "fill_existing_opening_with_door": "fill_existing_opening",
        "add_door_with_opening_to_wall": "add_with_opening",
        "add_window_with_opening_to_wall": "add_with_opening",
    }[operation_type]
    profile = {
        "add_beam": "beam.add.v0.3",
        "add_column": "column.add.v0.3",
        "fill_existing_opening_with_door": "door.fill-existing-opening.v0.3",
        "add_door_with_opening_to_wall": "door.add-with-opening.v0.3",
        "add_window_with_opening_to_wall": "window.add-with-opening.v0.2",
    }[operation_type]
    return {
        "component_family": family,
        "action": action,
        "operation_profile": profile,
        "source": _public_source(excerpt),
    }


def _hosted_parameters(
    case: Mapping[str, Any], op: Mapping[str, Any], model: Any
) -> dict[str, Any]:
    """Canonical parameters for hosted ops, derived from frozen bindings."""

    operation_type = str(op["operation_type"])
    if operation_type == "fill_existing_opening_with_door":
        opening_id = _resolve_opening_global_id(
            model, op["expected_target"]["opening_query"]
        )
        return _canonical_fill_door_parameters(
            model, opening_id, dict(op["parameters"])
        )
    return dict(op["parameters"])


def _property_intents(case: Mapping[str, Any], op: Mapping[str, Any]) -> list[dict]:
    return [
        {
            "intent_kind": "natural_language_property",
            "property_phrase": str(intent["natural_language"]),
            "raw_value": intent["value"],
            "raw_unit": None,
            "scope": "occurrence_direct",
            "source": _public_source(str(intent["natural_language"])),
        }
        for intent in case.get("property_intents", ())
        if intent["scope_operation_id"] == op["operation_id"]
    ]


class _CompositeReplayTransport(_MockTransport):
    """Deterministic replay transport over the frozen composite cases."""

    def __init__(self) -> None:
        super().__init__([])
        self.current_case: dict[str, Any] | None = None

    def set_case_document(self, case: Mapping[str, Any]) -> None:
        self.current_case = dict(case)

    def generate_live(
        self,
        *,
        session_id: str,
        prompt: str,
        schema: dict[str, Any],
        state: dict[str, Any],
    ) -> Any:
        stage = str(state["stage"])
        case = self.current_case
        assert case is not None, "replay transport case not bound"
        if stage == "ifc_repair_intent":
            content = self._intent_response(case, prompt)
        elif stage == "ifc_property_resolution":
            content = self._property_resolution_response(prompt)
        elif stage == "ifc_repair_bound_changeset":
            content = self._changeset_response(case, prompt, schema=schema)
        else:
            raise AssertionError(stage)
        self.responses.append({"content": content})
        return super().generate_live(
            session_id=session_id,
            prompt=prompt,
            schema=schema,
            state=state,
        )

    # -- Stage 1 --------------------------------------------------------
    def _intent_response(self, case: Mapping[str, Any], prompt: str) -> dict[str, Any]:
        model = ifcopenshell.open(str(MODEL_PATHS[case["model_id"]]))
        request = str(case["request"])
        operations = []
        for op in case["operations"]:
            operation_type = str(op["operation_type"])
            if operation_type in ("add_beam", "add_column"):
                target_query = _storey_query(case)
                parameters = dict(op["parameters"])
            else:
                if operation_type == "fill_existing_opening_with_door":
                    opening_id = _resolve_opening_global_id(
                        model, op["expected_target"]["opening_query"]
                    )
                    target_query = {
                        "schema_version": "text2ifc/ifc-target-query/0.1",
                        "allowed_ifc_classes": ["IfcOpeningElement"],
                        "geometry_capabilities": ["measured_hosted_opening"],
                        "geometry_constraints": op["expected_target"][
                            "opening_query"
                        ]["geometry_constraints"],
                        "max_candidates": 5,
                        "winner_margin": 10,
                    }
                else:
                    target_query = {
                        "schema_version": "text2ifc/ifc-target-query/0.1",
                        "allowed_ifc_classes": ["IfcWall"],
                        "direction": op["expected_target"]["wall_query"].get(
                            "direction"
                        ),
                        "geometry_capabilities": ["straight_wall"],
                        "geometry_constraints": op["expected_target"]["wall_query"][
                            "geometry_constraints"
                        ],
                        "max_candidates": 5,
                        "winner_margin": 10,
                    }
                parameters = _intent_parameters(op)
            operations.append(
                {
                    "operation_id": op["operation_id"],
                    "operation_type": operation_type,
                    "routing_intent": _routing_intent(operation_type, request),
                    "target_query": target_query,
                    "parameters": parameters,
                    "attribute_intents": [],
                    "property_intents": _property_intents(case, op),
                    "semantic_bundle_refs": [],
                    "quantity_intents": [],
                    "occurrence_reuse_intent": None,
                    "prototype_intent": None,
                    "provenance": [_public_source(request[:2048])],
                }
            )
        unsupported = [
            {
                "unsupported_id": "unsupported-1",
                "kind": "registered_capability",
                "operation_id": "C5-beam-01",
                "capability_id": "structural_analysis_node",
                "source": _public_source("create a structural analysis node"),
            }
        ]
        return {
            "schema_version": "text2ifc/ifc-repair-intent-body/0.8",
            "operations": operations,
            "unsupported_requests": (
                unsupported if case["case_id"] == "C5-N" else []
            ),
            "semantic_bundles": [],
            "provenance": [_public_source(request[:2048])],
        }

    # -- Stage 1.5 ------------------------------------------------------
    @staticmethod
    def _property_resolution_response(prompt: str) -> dict[str, Any]:
        query = _labeled_prompt_json(prompt, "PROPERTY_QUERY")
        candidate_set = _labeled_prompt_json(prompt, "CANDIDATE_SET")
        phrase = str(query["property_phrase"]).casefold()
        if "fire rating" in phrase:
            suffix = ".FireRating"
        elif "external" in phrase or "外窗" in phrase:
            suffix = ".IsExternal"
        else:
            raise AssertionError(f"unexpected property phrase: {phrase}")
        selected = next(
            item
            for item in candidate_set["candidates"]
            if str(item["canonical_path"]).endswith(suffix)
        )
        return {
            "schema_version": "text2ifc/ifc-property-rerank-decision/0.1",
            "decision": "confirmed",
            "selected_candidate_id": selected["candidate_id"],
            "conflicting_candidate_ids": [],
            "clarification_question": None,
        }

    # -- Stage 2 --------------------------------------------------------
    def _changeset_response(
        self,
        case: Mapping[str, Any],
        prompt: str,
        *,
        schema: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Provider DRAFT: plain operations only.

        The immutable semantic assignments are attached by
        ``bind_repair_changeset`` from the semantic manifests, never authored
        by the Provider draft (that is the production authority contract).
        """

        projection = _prompt_json(prompt, "Resolved operation projection")
        raw_operations = projection["operations"]
        operations = []
        scope: list[str] = []
        evidence: list[str] = []
        if isinstance(raw_operations, list):
            for operation in raw_operations:
                operations.append(
                    {
                        "operation_id": operation["operation_id"],
                        "operation_type": operation["operation_type"],
                        "target": operation["target"],
                        "parameters": operation["parameters"],
                        "evidence_refs": list(operation["evidence_refs"]),
                    }
                )
                scope.extend(
                    str(value)
                    for value in operation.get("scope_ids", ())
                    or [operation["target"].get(key) for key in operation["target"]]
                )
                evidence.extend(str(v) for v in operation["evidence_refs"])
        else:
            from text2ifc_ifc_repair.operations import create_default_registry

            registry = create_default_registry()
            for operation_id, operation in raw_operations.items():
                operations.append(
                    {
                        "operation_id": operation_id,
                        "operation_type": operation["operation_type"],
                        "target": registry.bind_resolved_target(
                            str(operation["operation_type"]),
                            str(operation["target_global_id"]),
                        ),
                        "parameters": operation["parameters"],
                        "evidence_refs": [str(v) for v in operation["evidence_pointers"]],
                    }
                )
                scope.extend(str(value) for value in operation["scope_ids"])
                evidence.extend(str(v) for v in operation["evidence_pointers"])
        binding_lines = prompt.split("## Immutable bindings", 1)[1].split(
            "## Resolved operation projection", 1
        )[0]
        import re

        bindings = dict(
            re.findall(r"^- ([^:]+): (.+)$", binding_lines, flags=re.MULTILINE)
        )
        return {
            "schema_version": str(schema["$id"]),
            "draft_id": f"draft-composite-{case['case_id']}",
            "base_model_fingerprint": bindings["model"],
            "source_request_hash": bindings["source request"],
            "semantic_manifest_ref": bindings["semantic manifest ref"],
            "semantic_manifest_sha256": bindings["semantic manifest hash"],
            "semantic_summary": _prompt_json(prompt, "Semantic group counts"),
            "scope": {
                "target_ids": sorted(set(scope)),
                "forbidden_ids": [],
            },
            "evidence_refs": sorted(set(evidence)),
            "preconditions": [],
            "postconditions": [],
            "operations": operations,
        }


def _select_candidate(prompt: str, suffix: str) -> str:
    candidate_set = _prompt_json(prompt, "CANDIDATE_SET")
    selected = next(
        item
        for item in candidate_set["candidates"]
        if str(item["canonical_path"]).endswith(suffix)
    )
    return str(selected["candidate_id"])


def _intent_parameters(op: Mapping[str, Any]) -> dict[str, Any]:
    """Stage 1 intent parameters (public request facts only).

    The add-door intent schema does not carry canonical overall dimensions
    (they are resolved from the opening request facts), so they are projected
    out here; everything else passes through as frozen.
    """

    parameters = dict(op["parameters"])
    door = parameters.get("door")
    if isinstance(door, dict) and str(op["operation_type"]) == "add_door_with_opening_to_wall":
        parameters["door"] = {
            key: value
            for key, value in door.items()
            if key in {"operation_type", "formal_enum_explicit", "notdefined_accepted"}
        }
    return parameters



@pytest.mark.parametrize("case_id", ["C1", "C2", "C3", "C4", "C5"])
def test_offline_full_chain_public_api_succeeds_and_proves(
    tmp_path: Path, case_id: str
) -> None:
    """Full public API chain for every positive composite case.

    C3/C4/C5 (window-containing) were previously blocked by the mixed-manifest
    binding defect; that defect was fixed (see DEFECT-RECORD.md) and these
    cases now bind, apply, and prove end to end offline.
    """

    case = CASES_BY_ID[case_id]
    source = MODEL_PATHS[case["model_id"]]
    transport = _CompositeReplayTransport()
    transport.set_case_document(case)
    provider = live.TranscriptProvider(transport)
    provider.set_case(case_id)
    runtime = tmp_path / f"runtime-{case_id}"

    from text2ifc_ifc_repair.api import RepairAPI

    api = RepairAPI(
        runtime,
        provider=provider,
        intent_schema_version=live.REPAIR_INTENT_SCHEMA_VERSION_0_8,
        property_knowledge_runtime=_composite_property_runtime(),
    )
    final = api.start(source, str(case["request"]))
    assert final.status == "succeeded", (
        final.reason_code,
        json.dumps(getattr(final, "artifacts", {}), default=str),
    )
    assert final.complete_repair_success is True
    assert final.successful_artifact_publishable is True

    run_root = runtime / "runs" / final.run_id
    strict = strict_reopen_verification(
        runtime=runtime,
        final=live._result_summary(final),
        source_path=source,
        expected_source_sha256="sha256:"
        + str(FREEZE["models"][case["model_id"]]["sha256"]),
    )
    assert strict["status"] == "passed", strict

    changeset_path = run_root / "changeset" / "bound-changeset.json"
    if not changeset_path.is_file():
        changeset_path = run_root / "changeset.json"
    changeset = json.loads(changeset_path.read_text(encoding="utf-8"))
    manifest_rel = str(final.artifacts["manifest"])
    evidence_path = (run_root / manifest_rel).parent / "terminal" / "evidence.json"
    application = json.loads(evidence_path.read_text(encoding="utf-8"))["evidence"][
        "application"
    ]
    repaired = Path(str(final.artifacts["successful_ifc"]))
    if not repaired.is_absolute():
        repaired = run_root / repaired

    proof = verify_composite_case(
        case=case,
        changeset=changeset,
        application=application,
        source_model=ifcopenshell.open(str(source)),
        repaired_model=ifcopenshell.open(str(repaired)),
        source_path=source,
        repaired_path=repaired,
        live_attempt_evidence=[],
    )
    assert proof["status"] == "passed"
    preservation_exact = verify_exact_composed_delta(
        case=case,
        application=application,
        source_model=ifcopenshell.open(str(source)),
        repaired_model=ifcopenshell.open(str(repaired)),
    )
    assert preservation_exact["status"] == "exact_delta_verified"
    preservation_comparator = verify_no_unrelated_mutation(
        case=case,
        application=application,
        source_path=source,
        repaired_path=repaired,
    )
    assert preservation_comparator["status"] == "passed"


def test_offline_full_chain_negative_twin_fails_closed(tmp_path: Path) -> None:
    case = CASES_BY_ID["C5-N"]
    source = MODEL_PATHS[case["model_id"]]
    transport = _CompositeReplayTransport()
    transport.set_case_document(case)
    provider = live.TranscriptProvider(transport)
    provider.set_case("C5-N")
    runtime = tmp_path / "runtime-c5n"

    from text2ifc_ifc_repair.api import RepairAPI

    api = RepairAPI(
        runtime,
        provider=provider,
        intent_schema_version=live.REPAIR_INTENT_SCHEMA_VERSION_0_8,
        property_knowledge_runtime=_composite_property_runtime(),
    )
    import hashlib

    before = hashlib.sha256(source.read_bytes()).hexdigest()
    final = api.start(source, str(case["request"]))
    after = hashlib.sha256(source.read_bytes()).hexdigest()

    assert final.status == "unsupported"
    assert final.successful_artifact_publishable is False
    assert before == after, "negative twin must not mutate the source"
    stage2_attempts = [a for a in provider.attempts if a.get("stage") == "stage2"]
    assert not stage2_attempts, "negative twin must not reach Stage 2"
    assert not getattr(final, "artifacts", {}).get("successful_ifc")


def test_window_manifests_now_carry_canonical_source_kinds() -> None:
    """Post-fix sentinel: the mixed-manifest binding defect stays fixed.

    Before the fix, the window policy-facts hook gated ``canonical_source_kind``
    on an ``authorized_occurrence_assignment`` and the ``use_v03`` scope set
    omitted ``window_occurrence``; a window manifest therefore stayed at v0.1
    with raw source kinds, and any changeset mixing window with beam/column
    failed to bind (``BOUND_CHANGESET_INVALID``).  Full history, failure
    family, and fix: ``docs/validation/repair-composite-milestone/
    DEFECT-RECORD.md`` and ``tests/ifc_repair/test_mixed_manifest_binding.py``.
    This sentinel alerts if the defect ever regresses.
    """

    from text2ifc_ifc_repair.operations import create_default_registry

    registry = create_default_registry()
    operation = {
        "operation_id": "sentinel-window-1",
        "operation_type": "add_window_with_opening_to_wall",
        "target": {"wall_global_id": "ANY-WALL"},
        "parameters": {
            "position": {
                "reference": "wall_local_start",
                "center_offset_mm": 2000,
            },
            "opening": {
                "width_mm": 1200,
                "height_mm": 1500,
                "sill_height_mm": 900,
            },
            "window": {"fit_opening": True},
        },
    }
    facts = registry.build_semantic_policy_facts(
        "add_window_with_opening_to_wall", operation=operation
    )
    assert facts
    assert all(
        fact.canonical_source_kind == "deterministic_derived" for fact in facts
    ), "window policy facts lost their canonical source kind — defect regression"
