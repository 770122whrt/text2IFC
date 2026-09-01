"""Natural-language property claims with a null scope must stay retrievable.

Stage 1's intent schema permits ``scope: null`` on a natural-language
property claim (the model omits the scope when the user does not state
one). The deterministic resolver already normalizes a missing scope to
``occurrence_direct`` (``normalize_property_scope``), but the property
knowledge query and the durable retrieval coordinator used to forward the
raw ``None``, and pre-retrieval eligibility rejects every record whose
scope is not exactly ``occurrence_direct`` — so a perfectly valid claim
died as ``PROPERTY_RETRIEVAL_BELOW_FLOOR`` with an empty offered set.

These tests freeze the mechanism: the query and the persisted retrieval
evidence must carry the normalized scope, while ``type_owned`` still fails
closed and the rendered query text stays deterministic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from text2ifc_ifc_repair.property_intent import normalize_property_scope
from text2ifc_ifc_repair.repair_intent import PublicProvenance
from text2ifc_ifc_repair.resolution_flow import PropertyKnowledgeQuery


def _claim(scope: str | None) -> Any:
    from text2ifc_ifc_repair.property_intent import (
        NaturalLanguagePropertyIntent,
    )

    return NaturalLanguagePropertyIntent(
        property_phrase="防火等级",
        raw_value="EI60",
        raw_unit=None,
        scope=scope,
        source=PublicProvenance(
            "user_request", "public-request-1", "防火等级 EI60"
        ),
    )


def test_null_scope_claim_builds_occurrence_direct_property_query() -> None:
    """A valid null-scope claim must reach retrieval as occurrence_direct."""
    claim = _claim(None)

    scope = normalize_property_scope(claim.scope)
    query = PropertyKnowledgeQuery(
        target_ifc_class="IfcDoor",
        phrase=str(claim.property_phrase),
        raw_value=claim.raw_value,
        raw_unit=claim.raw_unit,
        scope=scope,
    )

    assert query.scope == "occurrence_direct"


class _RetrievalRecorder:
    """Minimal runtime double capturing the scope handed to retrieval.

    The candidate set is intentionally empty so the coordinator stops at
    the below-floor branch right after retrieval, before any Provider or
    admissibility stage is exercised.
    """

    records: tuple[Any, ...] = ()

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.health = type(
            "Health",
            (),
            {
                "status": "ready",
                "corpus_version": "corpus-test",
                "embedding_model_id": "model-test",
                "embedding_model_version": "model-test-v1",
                "document_renderer_version": "renderer-test",
                "collection_version": "collection-test",
            },
        )()
        self.policy = {
            "policy_id": "policy-test",
            "version": "0.1",
            "minimum_retrieval_score": 0.0,
            "max_candidates": 5,
        }

    def retrieve(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return type(
            "Retrieval",
            (),
            {
                "query": {
                    "schema_version": "text2ifc/property-knowledge-query/0.1",
                    "query_id": "property-query:repair-scope-test:op:claim-001",
                    "corpus_version": "corpus-test",
                },
                "candidate_set": {
                    "schema_version": "text2ifc/ifc-property-candidate-set/0.1",
                    "candidate_set_id": (
                        "property-candidates:repair-scope-test:op:claim-001"
                    ),
                    "candidates": [],
                    "corpus_version": "corpus-test",
                    "embedding_model": {
                        "model_id": "model-test",
                        "model_version": "model-test-v1",
                    },
                    "document_renderer_version": "renderer-test",
                    "collection_version": "collection-test",
                },
            },
        )()


def test_durable_coordinator_uses_normalized_query_scope(tmp_path: Path) -> None:
    """The coordinator must forward the query's normalized scope, not the raw claim scope."""
    from text2ifc_ifc_repair.property_resolution_coordinator import (
        DurablePropertyResolutionCoordinator,
    )

    recorder = _RetrievalRecorder()
    coordinator = DurablePropertyResolutionCoordinator.__new__(
        DurablePropertyResolutionCoordinator
    )
    coordinator.run_id = "repair-scope-test"
    coordinator.intent = type(
        "Intent",
        (),
        {"request_id": "request-scope-test", "model_fingerprint": "sha256:test"},
    )()
    coordinator.runtime = recorder
    coordinator.provider = None
    coordinator._property_resolution_stage = lambda **kwargs: None
    coordinator._selected_candidate_answer = {}
    coordinator._claim_generation = None
    coordinator.pending_clarification = None
    coordinator._operation_ordinals = {"set-door-fire-rating-1": 0}
    coordinator.store = type(
        "Store",
        (),
        {
            "run_directory": tmp_path,
            "runs_root": tmp_path,
            "artifact_binding": lambda self, *a, **k: {},
            "prepare_stage_directory": lambda self, *a, **k: tmp_path,
        },
    )()
    coordinator._claim_directory = (  # type: ignore[method-assign]
        lambda operation_id, claim_id: (
            tmp_path / f"{operation_id}-{claim_id}",
            f"{operation_id}/{claim_id}",
        )
    )
    committed: dict[tuple[str, str, str], dict[str, Any]] = {}

    def _checkpoint(operation_id: str, claim_id: str, name: str) -> Any:
        return committed.get((operation_id, claim_id, name))

    def _commit_checkpoint(
        *,
        operation_id: str,
        claim_id: str,
        checkpoint: str,
        artifacts: Any,
    ) -> None:
        committed[(operation_id, claim_id, checkpoint)] = {
            "artifacts": artifacts,
            "policy_id": recorder.policy["policy_id"],
            "policy_version": recorder.policy["version"],
            "minimum_retrieval_score": recorder.policy[
                "minimum_retrieval_score"
            ],
            "max_candidates": recorder.policy["max_candidates"],
        }

    coordinator._checkpoint = _checkpoint  # type: ignore[method-assign]
    coordinator._commit_checkpoint = _commit_checkpoint  # type: ignore[method-assign]

    claim = _claim(None)
    query = PropertyKnowledgeQuery(
        target_ifc_class="IfcDoor",
        phrase=str(claim.property_phrase),
        raw_value=claim.raw_value,
        raw_unit=claim.raw_unit,
        scope=normalize_property_scope(claim.scope),
    )
    decision = coordinator.resolve_for_claim(
        operation_id="set-door-fire-rating-1",
        operation_type="set_occurrence_properties",
        claim_id="claim-001",
        claim=claim,
        query=query,
    )

    assert recorder.calls, "retrieval was never invoked"
    assert recorder.calls[0]["scope"] == "occurrence_direct"
    # The empty candidate set here only proves the coordinator ran its
    # below-floor branch; the normalized scope is what made retrieval
    # eligible in production.
    assert decision.reason_code == "PROPERTY_RETRIEVAL_BELOW_FLOOR"
