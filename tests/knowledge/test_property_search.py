from __future__ import annotations

from pathlib import Path

from text2ifc_knowledge.property_search import (
    InMemoryVectorIndex,
    PropertyAlias,
    PropertyKnowledgeQuery,
    PropertyKnowledgeResolver,
    PropertyKnowledgeStore,
    build_standard_property_records,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry


class SemanticFixtureEmbedding:
    model_id = "fixture-semantic"
    model_fingerprint = "sha256:fixture-semantic"

    def embed(self, texts):
        vectors = []
        for text in texts:
            normalized = text.casefold()
            vectors.append(
                [
                    float("external" in normalized or "外" in normalized),
                    float("thermal" in normalized or "传热" in normalized),
                    float("load" in normalized or "承重" in normalized),
                ]
            )
        return vectors


def _records(project_root: Path):
    registry = load_ifc2x3_registry(project_root)
    return registry, build_standard_property_records(
        registry,
        corpus_fingerprint="sha256:official-ifc2x3-fixture",
    )


def test_standard_records_cover_full_registry_and_authoring_boundary(
    project_root: Path,
) -> None:
    registry, records = _records(project_root)
    by_path = {(item.set_name, item.property_name): item for item in records}

    assert len(records) >= 1832
    external = by_path[("Pset_WindowCommon", "IsExternal")]
    assert external.authority == "ifc2x3_psd"
    assert external.authorable is True
    assert external.value_type == "IfcBoolean"
    assert external.source_hash == "sha256:official-ifc2x3-fixture"

    reference = by_path[("Pset_ActionRequest", "RequestSourceName")]
    assert reference.authorable is False
    assert reference.template_type == "TypePropertyReferenceValue"

    assert external.is_applicable("IfcWindow", registry)
    wall_external = by_path[("Pset_WallCommon", "IsExternal")]
    assert wall_external.is_applicable("IfcWallStandardCase", registry)
    assert not wall_external.is_applicable("IfcDoor", registry)


def test_property_store_reuses_matching_corpus_and_rebuilds_on_drift(
    project_root: Path,
    tmp_path: Path,
) -> None:
    _, records = _records(project_root)
    store = PropertyKnowledgeStore(tmp_path / "property-knowledge.sqlite")

    first = store.ensure_standard_corpus(
        corpus_fingerprint="sha256:corpus-a",
        records=records[:8],
    )
    second = store.ensure_standard_corpus(
        corpus_fingerprint="sha256:corpus-a",
        records=records[:8],
    )
    third = store.ensure_standard_corpus(
        corpus_fingerprint="sha256:corpus-b",
        records=records[8:12],
    )

    assert first.status == "built"
    assert second.status == "reused"
    assert third.status == "rebuilt"
    assert len(store.load_records()) == 4
    assert store.corpus_fingerprint == "sha256:corpus-b"


def test_exact_and_reviewed_alias_resolve_without_vector_authority(
    project_root: Path,
) -> None:
    registry, records = _records(project_root)
    aliases = (
        PropertyAlias(
            alias="外窗",
            set_name="Pset_WindowCommon",
            property_name="IsExternal",
            language="zh",
            review_status="reviewed",
        ),
    )
    resolver = PropertyKnowledgeResolver(
        registry=registry,
        records=records,
        aliases=aliases,
    )

    exact = resolver.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcWindow",
            phrase="Pset_WindowCommon.IsExternal",
            raw_value=True,
        )
    )
    alias = resolver.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcWindow",
            phrase="外窗",
            raw_value=True,
        )
    )

    assert exact.status == "standard_resolved"
    assert exact.reason_code == "CANONICAL_EXACT"
    assert alias.status == "standard_resolved"
    assert alias.reason_code == "REVIEWED_ALIAS_EXACT"
    assert alias.exact_intent is not None
    assert alias.exact_intent.set_name == "Pset_WindowCommon"
    assert alias.exact_intent.property_name == "IsExternal"


def test_keyword_vector_consensus_resolves_but_vector_only_does_not(
    project_root: Path,
) -> None:
    registry, records = _records(project_root)
    aliases = (
        PropertyAlias(
            alias="外窗",
            set_name="Pset_WindowCommon",
            property_name="IsExternal",
            language="zh",
            review_status="reviewed",
        ),
    )
    vector_index = InMemoryVectorIndex(SemanticFixtureEmbedding())
    vector_index.build(records)
    resolver = PropertyKnowledgeResolver(
        registry=registry,
        records=records,
        aliases=aliases,
        vector_index=vector_index,
    )

    consensus = resolver.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcWindow",
            phrase="把这个窗户标记为外窗",
            raw_value=True,
        )
    )
    vector_only = resolver.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcWindow",
            phrase="这是建筑外围构件",
            raw_value=True,
        )
    )

    assert consensus.status == "standard_resolved"
    assert consensus.reason_code == "HYBRID_CONSENSUS"
    assert vector_only.status == "clarification_required"
    assert vector_only.reason_code == "VECTOR_ONLY_NOT_AUTHORIZED"


def test_custom_project_candidate_always_requires_confirmation(
    project_root: Path,
) -> None:
    registry, records = _records(project_root)
    resolver = PropertyKnowledgeResolver(
        registry=registry,
        records=records,
        aliases=(),
    )

    result = resolver.resolve(
        PropertyKnowledgeQuery(
            target_ifc_class="IfcWindow",
            phrase="Custom_Asset.AssetCode",
            raw_value="W-007",
        )
    )

    assert result.status == "custom_confirmation_required"
    assert result.reason_code == "UNKNOWN_PROPERTY"
