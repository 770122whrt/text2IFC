from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
from jsonschema import Draft202012Validator

from text2ifc_knowledge import property_search
from text2ifc_knowledge.property_search import (
    InMemoryVectorIndex,
    QdrantVectorIndex,
    VectorHit,
    build_standard_property_records,
    default_standard_corpus_fingerprint,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SemanticFixtureEmbedding:
    model_id = "fixture-semantic"
    model_version = "fixture-semantic/0.1"
    model_fingerprint = "historical-test-only"

    def embed(self, texts):
        vectors = []
        for text in texts:
            normalized = text.casefold().replace("_", "")
            vectors.append(
                [
                    float("external" in normalized or "isexternal" in normalized),
                    float("load" in normalized or "loadbearing" in normalized),
                    float("selfclos" in normalized or "automatic close" in normalized),
                    float("fire" in normalized),
                ]
            )
        return vectors


class IneligibleHitVectorIndex:
    def __init__(self) -> None:
        self.embedding_provider = SemanticFixtureEmbedding()
        self.built_record_ids: tuple[str, ...] = ()

    def ensure_versioned(self, records, *, collection_version: str) -> str:
        del collection_version
        self.built_record_ids = tuple(record.record_id for record in records)
        return "built"

    def search_allowed(self, text: str, *, allowed_record_ids, limit: int):
        del text, allowed_record_ids, limit
        return (VectorHit("record-not-in-eligible-set", 1.0),)


class ExpectedCandidateVectorIndex:
    """Deterministic external-index seam for retrieval-eligibility tests."""

    def __init__(self, expected_path: str) -> None:
        self.embedding_provider = SemanticFixtureEmbedding()
        self.expected_path = expected_path
        self.expected_record_id: str | None = None
        self.search_text: str | None = None
        self.allowed_record_ids: frozenset[str] = frozenset()

    def ensure_versioned(self, records, *, collection_version: str) -> str:
        del collection_version
        self.expected_record_id = next(
            record.record_id
            for record in records
            if record.canonical_path == self.expected_path
        )
        return "built"

    def search_allowed(self, text: str, *, allowed_record_ids, limit: int):
        del limit
        self.search_text = text
        self.allowed_record_ids = frozenset(allowed_record_ids)
        if self.expected_record_id not in self.allowed_record_ids:
            return ()
        return (VectorHit(self.expected_record_id, 1.0),)


def _runtime_module():
    module_name = "text2ifc_knowledge.property_runtime"
    assert importlib.util.find_spec(module_name) is not None, (
        "Plan 12.1-02 property runtime module is missing"
    )
    return importlib.import_module(module_name)


def _policy() -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/property-resolution-policy/0.2",
        "policy_id": "ifc2x3.single-value.vector-reranker",
        "version": "0.2",
        "max_candidates": 5,
        "max_attempts": 2,
        "vector_required": True,
        "minimum_retrieval_score": 0.5,
        "alias_authority": False,
        "vector_top1_authority": False,
        "vector_margin_authority": False,
        "standard_selection": "stage_1_5_required",
        "project_or_custom": "explicit_confirmation_required",
        "explicit_canonical": "exact_path_bypass",
        "supported_template": "TypePropertySingleValue",
        "supported_scope": "occurrence_direct",
    }


def _records(project_root: Path):
    registry = load_ifc2x3_registry(project_root)
    records = build_standard_property_records(
        registry,
        corpus_fingerprint=default_standard_corpus_fingerprint(),
    )
    return registry, records


def _runtime(project_root: Path, *, vector_index=None):
    module = _runtime_module()
    registry, records = _records(project_root)
    index = vector_index or InMemoryVectorIndex(SemanticFixtureEmbedding())
    return module.create_property_runtime(
        registry=registry,
        standard_records=records,
        project_records=(),
        vector_index=index,
        policy_document=_policy(),
        corpus_version="ifc2x3-property-records/0.2",
        embedding_model_version="fixture-semantic/0.1",
        document_renderer_version="property-record-text/0.1",
        collection_version="ifc2x3-property-vector/0.2",
        runtime_mode="offline_test",
    )


def _retrieve(runtime, *, target_class: str, phrase: str, claim_id: str = "claim-1"):
    return runtime.retrieve(
        run_id="run-1",
        request_id="request-1",
        model_id="model-1",
        operation_id=f"operation-{claim_id}",
        operation_type="set_occurrence_properties",
        claim_id=claim_id,
        property_phrase=phrase,
        target_ifc_class=target_class,
        raw_value=True,
        raw_unit=None,
        scope="occurrence_direct",
    )


def _paths(result) -> list[str]:
    return [item["canonical_path"] for item in result.candidate_set["candidates"]]


def test_bge_embedding_provider_releases_only_loaded_transient_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trim_calls: list[str] = []
    monkeypatch.setattr(
        property_search,
        "_trim_current_process_working_set",
        lambda: trim_calls.append("trim"),
    )
    provider = property_search.BgeM3EmbeddingProvider(
        model_path="unused-offline-model",
        model_version="test",
    )
    loaded_model = object()
    provider._model = loaded_model

    provider.release_transient_resources()

    assert provider._model is None
    assert trim_calls == ["trim"]


def test_local_embedding_native_bootstrap_loads_msvc_before_torch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def load_msvc():
        events.append("msvc")
        return (object(), object(), object())

    class TorchFixture:
        __version__ = "2.9-test"

    def import_module(name: str):
        events.append(f"import:{name}")
        return TorchFixture()

    monkeypatch.setattr(
        property_search,
        "_prepare_windows_torch_runtime",
        load_msvc,
    )
    monkeypatch.setattr(importlib, "import_module", import_module)

    assert property_search.prepare_local_embedding_native_runtime() == {
        "status": "ready",
        "msvc_runtime_handle_count": 3,
        "torch_version": "2.9-test",
    }
    assert events == ["msvc", "import:torch"]


def test_property_runtime_warmup_exercises_embedding_before_live_use(
    project_root: Path,
) -> None:
    runtime = _runtime(project_root)
    calls: list[str] = []

    class WarmIndex:
        def warmup(self) -> dict[str, object]:
            calls.append("embedding")
            return {
                "status": "ready",
                "embedding_count": 1,
            }

    runtime.vector_index = WarmIndex()

    assert runtime.warmup() == {
        "status": "ready",
        "embedding_count": 1,
    }
    assert calls == ["embedding"]

def test_active_runtime_module_is_additive_and_non_executable() -> None:
    module = _runtime_module()
    assert hasattr(module, "PropertyKnowledgeRuntime")
    assert hasattr(module, "PropertyRuntimeHealth")
    assert hasattr(module, "PropertyRetrievalResult")

    result_fields = set(module.PropertyRetrievalResult.__dataclass_fields__)
    assert result_fields == {"query", "candidate_set", "health"}
    assert "exact_intent" not in result_fields


@pytest.mark.parametrize(
    ("target_class", "phrase", "expected_path"),
    [
        ("IfcWindow", "external property", "Pset_WindowCommon.IsExternal"),
        ("IfcDoor", "automatic close", "Pset_DoorCommon.SelfClosing"),
        ("IfcWall", "external property", "Pset_WallCommon.IsExternal"),
        (
            "IfcWallStandardCase",
            "external property",
            "Pset_WallCommon.IsExternal",
        ),
        ("IfcBeam", "load property", "Pset_BeamCommon.LoadBearing"),
        ("IfcColumn", "load property", "Pset_ColumnCommon.LoadBearing"),
    ],
)
def test_class_applicable_scalar_filter_precedes_vector_topk(
    project_root: Path,
    target_class: str,
    phrase: str,
    expected_path: str,
) -> None:
    runtime = _runtime(project_root)
    result = _retrieve(runtime, target_class=target_class, phrase=phrase)

    assert result.health["status"] == "ready"
    assert result.health["runtime_mode"] == "offline_test"
    assert result.health["acceptance_eligible"] is False
    assert expected_path in _paths(result)
    assert len(result.candidate_set["candidates"]) <= 5
    assert all(
        target_class in item["applicable_classes"]
        or (
            target_class == "IfcWallStandardCase"
            and "IfcWall" in item["applicable_classes"]
        )
        for item in result.candidate_set["candidates"]
    )


def test_query_candidate_and_health_documents_are_closed_public_and_stable(
    project_root: Path,
) -> None:
    runtime = _runtime(project_root)
    first = _retrieve(
        runtime,
        target_class="IfcBeam",
        phrase="load property",
        claim_id="claim-stable",
    )
    second = _retrieve(
        runtime,
        target_class="IfcBeam",
        phrase="load property",
        claim_id="claim-stable",
    )
    assert first == second

    query_schema = json.loads(
        (
            PROJECT_ROOT
            / "schemas/agent/ifc-property-resolution-query-0.2.schema.json"
        ).read_text(encoding="utf-8")
    )
    candidate_schema = json.loads(
        (
            PROJECT_ROOT
            / "schemas/agent/ifc-property-candidate-set-0.1.schema.json"
        ).read_text(encoding="utf-8")
    )
    assert not list(Draft202012Validator(query_schema).iter_errors(first.query))
    assert not list(
        Draft202012Validator(candidate_schema).iter_errors(first.candidate_set)
    )
    assert first.query["property_phrase"] == "load property"
    assert first.query["target_ifc_class"] == "IfcBeam"
    assert first.query["raw_value_kind"] == "boolean"
    assert first.query["scope"] == "occurrence_direct"

    serialized = json.dumps(
        {
            "query": first.query,
            "candidate_set": first.candidate_set,
            "health": first.health,
        },
        ensure_ascii=False,
        sort_keys=True,
    ).lower()
    for forbidden in (
        "reviewed_alias",
        "property_aliases",
        "source_hash",
        "benchmark_gold",
        "exact_intent",
    ):
        assert forbidden not in serialized


def test_historical_alias_loader_cannot_change_active_result(
    project_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_loaded(*args, **kwargs):
        del args, kwargs
        raise AssertionError("historical aliases must not be loaded")

    monkeypatch.setattr(property_search, "load_reviewed_aliases", fail_if_loaded)
    runtime = _runtime(project_root)
    result = _retrieve(
        runtime,
        target_class="IfcWindow",
        phrase="external property",
    )
    assert "Pset_WindowCommon.IsExternal" in _paths(result)


def test_post_search_ineligible_id_fails_closed(project_root: Path) -> None:
    module = _runtime_module()
    runtime = _runtime(project_root, vector_index=IneligibleHitVectorIndex())
    with pytest.raises(
        module.PropertyRuntimeError,
        match="PROPERTY_VECTOR_INELIGIBLE_HIT",
    ):
        _retrieve(runtime, target_class="IfcWindow", phrase="external property")


def test_type_owned_scope_has_no_eligible_candidates(
    project_root: Path,
) -> None:
    runtime = _runtime(project_root)
    type_owned = runtime.retrieve(
        run_id="run-1",
        request_id="request-1",
        model_id="model-1",
        operation_id="operation-1",
        operation_type="set_occurrence_properties",
        claim_id="claim-type",
        property_phrase="external property",
        target_ifc_class="IfcWindow",
        raw_value=True,
        raw_unit=None,
        scope="type_owned",
    )
    assert type_owned.candidate_set["candidates"] == []


@pytest.mark.parametrize(
    (
        "case_id",
        "target_class",
        "phrase",
        "raw_value",
        "expected_path",
    ),
    [
        (
            "p12w04",
            "IfcWindow",
            "窗的防火等级",
            True,
            "Pset_WindowCommon.FireRating",
        ),
        (
            "p12d04",
            "IfcDoor",
            "door fire rating",
            True,
            "Pset_DoorCommon.FireRating",
        ),
        (
            "p12c04",
            "IfcColumn",
            "column load bearing",
            "yes",
            "Pset_ColumnCommon.LoadBearing",
        ),
        (
            "p12b04",
            "IfcBeam",
            "beam reference code",
            42,
            "Pset_BeamCommon.Reference",
        ),
        (
            "p12m04",
            "IfcWall",
            "wall acoustic performance flag",
            True,
            "Pset_WallCommon.AcousticRating",
        ),
    ],
)
def test_incompatible_value_does_not_remove_property_before_vector_retrieval(
    project_root: Path,
    case_id: str,
    target_class: str,
    phrase: str,
    raw_value: object,
    expected_path: str,
) -> None:
    index = ExpectedCandidateVectorIndex(expected_path)
    runtime = _runtime(project_root, vector_index=index)

    result = runtime.retrieve(
        run_id="run-boundary",
        request_id="request-boundary",
        model_id="model-boundary",
        operation_id=f"operation-{case_id}",
        operation_type="set_occurrence_properties",
        claim_id=case_id,
        property_phrase=phrase,
        target_ifc_class=target_class,
        raw_value=raw_value,
        raw_unit=None,
        scope="occurrence_direct",
    )

    assert index.expected_record_id in index.allowed_record_ids
    assert _paths(result) == [expected_path]
    assert result.query["raw_value"] == raw_value
    assert index.search_text is not None
    assert phrase in index.search_text
    assert f"class {target_class}" in index.search_text
    assert "scope occurrence_direct" in index.search_text
    assert "operation set_occurrence_properties" in index.search_text
    assert "value kind" not in index.search_text
    assert "unit " not in index.search_text


def test_invalid_policy_is_rejected_before_index_build(project_root: Path) -> None:
    module = _runtime_module()
    registry, records = _records(project_root)
    invalid = _policy()
    invalid["alias_authority"] = True

    with pytest.raises(module.PropertyRuntimeError, match="PROPERTY_POLICY_INVALID"):
        module.create_property_runtime(
            registry=registry,
            standard_records=records,
            project_records=(),
            vector_index=InMemoryVectorIndex(SemanticFixtureEmbedding()),
            policy_document=invalid,
            corpus_version="ifc2x3-property-records/0.2",
            embedding_model_version="fixture-semantic/0.1",
            document_renderer_version="property-record-text/0.1",
            collection_version="ifc2x3-property-vector/0.2",
            runtime_mode="offline_test",
        )


def test_production_default_is_not_ready_before_calibrated_policy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _runtime_module()

    def must_not_construct(*args, **kwargs):
        del args, kwargs
        raise AssertionError("model must not load before policy admission")

    monkeypatch.setattr(module, "BgeM3EmbeddingProvider", must_not_construct)
    runtime = module.create_default_property_runtime(
        qdrant_path=tmp_path / "qdrant",
        policy_path=tmp_path / "missing-policy.json",
    )
    assert runtime.health.to_dict() == {
        "status": "not_ready",
        "reason_code": "PROPERTY_POLICY_UNAVAILABLE",
        "runtime_mode": "production",
        "acceptance_eligible": False,
        "corpus_version": "ifc2x3-property-records/0.2",
        "embedding_model_id": "BAAI/bge-m3",
        "embedding_model_version": "configured",
        "document_renderer_version": "property-record-text/0.1",
        "collection_version": "ifc2x3-property-vector/0.2",
        "collection_status": None,
        "record_count": 0,
    }
    with pytest.raises(module.PropertyRuntimeError, match="PROPERTY_POLICY_UNAVAILABLE"):
        _retrieve(runtime, target_class="IfcBeam", phrase="load property")


def test_missing_bge_and_qdrant_have_distinct_pre_provider_reasons(
    tmp_path: Path,
) -> None:
    module = _runtime_module()

    def missing_bge(**kwargs):
        del kwargs
        raise RuntimeError("BGE_M3_DEPENDENCY_UNAVAILABLE")

    bge = module.create_default_property_runtime(
        qdrant_path=tmp_path / "qdrant-bge",
        policy_document=_policy(),
        runtime_mode="offline_test",
        embedding_provider_factory=missing_bge,
    )
    assert bge.health.reason_code == "BGE_M3_UNAVAILABLE"

    class FixtureEmbedding(SemanticFixtureEmbedding):
        def __init__(self, **kwargs) -> None:
            assert kwargs["local_files_only"] is True

    def missing_qdrant(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("QDRANT_DEPENDENCY_UNAVAILABLE")

    qdrant = module.create_default_property_runtime(
        qdrant_path=tmp_path / "qdrant-missing",
        policy_document=_policy(),
        runtime_mode="offline_test",
        embedding_provider_factory=FixtureEmbedding,
        vector_index_factory=missing_qdrant,
    )
    assert qdrant.health.reason_code == "QDRANT_UNAVAILABLE"


def test_production_runtime_config_resolves_repo_local_assets_without_download(
    tmp_path: Path,
) -> None:
    module = _runtime_module()
    model_path = tmp_path / ".cache/models/BAAI-bge-m3"
    model_path.mkdir(parents=True)

    config = module.load_property_runtime_config({}, project_root=tmp_path)

    assert config.project_root == tmp_path.resolve()
    assert config.embedding_model_path == str(model_path.resolve())
    assert config.qdrant_path == (
        tmp_path / ".cache/property-resolution/qdrant"
    ).resolve()
    assert config.qdrant_url is None
    assert config.local_files_only is True


def test_production_runtime_config_resolves_relative_environment_overrides(
    tmp_path: Path,
) -> None:
    module = _runtime_module()
    config = module.load_property_runtime_config(
        {
            "TEXT2IFC_PROPERTY_BGE_MODEL_PATH": "models/bge-m3",
            "TEXT2IFC_PROPERTY_BGE_MODEL_VERSION": "local-approved/0.1",
            "TEXT2IFC_PROPERTY_QDRANT_PATH": "vectors/qdrant",
            "TEXT2IFC_PROPERTY_BGE_DEVICE": "cpu",
        },
        project_root=tmp_path,
    )

    assert config.embedding_model_path == str(
        (tmp_path / "models/bge-m3").resolve()
    )
    assert config.embedding_model_version == "local-approved/0.1"
    assert config.qdrant_path == (tmp_path / "vectors/qdrant").resolve()
    assert config.device == "cpu"


def test_environment_runtime_factory_forwards_one_resolved_production_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _runtime_module()
    captured: dict[str, Any] = {}
    sentinel = object()

    def capture(**kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(module, "create_default_property_runtime", capture)
    result = module.create_property_runtime_from_environment(
        {
            "TEXT2IFC_PROPERTY_BGE_MODEL_PATH": "models/bge-m3",
            "TEXT2IFC_PROPERTY_QDRANT_PATH": "vectors/qdrant",
        },
        project_root=tmp_path,
    )

    assert result is sentinel
    assert captured["runtime_mode"] == "production"
    assert captured["embedding_model_path"] == str(
        (tmp_path / "models/bge-m3").resolve()
    )
    assert captured["qdrant_path"] == (tmp_path / "vectors/qdrant").resolve()
    assert captured["qdrant_url"] is None


def test_runtime_config_rejects_ambiguous_qdrant_location(tmp_path: Path) -> None:
    module = _runtime_module()

    with pytest.raises(
        module.PropertyRuntimeConfigurationError,
        match="PROPERTY_QDRANT_LOCATION_AMBIGUOUS",
    ):
        module.load_property_runtime_config(
            {
                "TEXT2IFC_PROPERTY_QDRANT_PATH": "vectors/qdrant",
                "TEXT2IFC_PROPERTY_QDRANT_URL": "http://127.0.0.1:6333",
            },
            project_root=tmp_path,
        )


def test_windows_bge_loader_preloads_system_msvc_runtime(
    tmp_path: Path,
) -> None:
    system32 = tmp_path / "System32"
    system32.mkdir()
    expected = (
        system32 / "msvcp140.dll",
        system32 / "vcruntime140.dll",
        system32 / "vcruntime140_1.dll",
    )
    for path in expected:
        path.touch()
    loaded: list[Path] = []

    def fixture_loader(path: str):
        loaded.append(Path(path))
        return object()

    handles = property_search._prepare_windows_torch_runtime(
        os_name="nt",
        system_root=tmp_path,
        dll_loader=fixture_loader,
    )

    assert tuple(loaded) == expected
    assert len(handles) == len(expected)


def test_non_windows_bge_loader_does_not_load_dlls() -> None:
    def fail_if_loaded(path: str):
        raise AssertionError(f"unexpected DLL load: {path}")

    assert property_search._prepare_windows_torch_runtime(
        os_name="posix",
        system_root=Path("unused"),
        dll_loader=fail_if_loaded,
    ) == ()


def test_bge_identity_uses_configured_version_without_reading_weight_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = tmp_path / "bge-m3"
    model.mkdir()
    (model / "model.safetensors").touch()

    def fail_if_opened(*args, **kwargs):
        del args, kwargs
        raise AssertionError("model weights must not be hashed at startup")

    monkeypatch.setattr(Path, "open", fail_if_opened)
    first = property_search._embedding_model_fingerprint(
        str(model),
        model_version="bge-m3/local-v1",
    )
    second = property_search._embedding_model_fingerprint(
        str(model),
        model_version="bge-m3/local-v2",
    )

    assert first == "configured:BAAI/bge-m3:bge-m3/local-v1"
    assert second == "configured:BAAI/bge-m3:bge-m3/local-v2"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows DLL ordering contract")
def test_public_repair_api_loads_before_torch_in_fresh_process() -> None:
    probe = subprocess.run(
        [
            sys.executable,
            "-X",
            "faulthandler",
            "-c",
            (
                "from text2ifc_ifc_repair.api import RepairAPI; "
                "import torch; "
                "print(RepairAPI.__name__, torch.__version__)"
            ),
        ],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert probe.returncode == 0, probe.stdout + probe.stderr
    assert "RepairAPI" in probe.stdout


def test_qdrant_collection_build_reuse_version_change_and_allowed_filter(
    project_root: Path,
    tmp_path: Path,
) -> None:
    registry, records = _records(project_root)
    del registry
    selected = tuple(
        record
        for record in records
        if record.canonical_path
        in {
            "Pset_WindowCommon.IsExternal",
            "Pset_DoorCommon.IsExternal",
        }
    )
    index = QdrantVectorIndex(
        SemanticFixtureEmbedding(),
        collection_name="phase12_1_property_runtime",
        path=tmp_path / "qdrant",
    )
    try:
        assert index.ensure_versioned(
            selected,
            collection_version="ifc2x3-property-vector/0.2",
        ) == "built"
        assert index.ensure_versioned(
            selected,
            collection_version="ifc2x3-property-vector/0.2",
        ) == "reused"
        assert index.ensure_versioned(
            selected,
            collection_version="ifc2x3-property-vector/0.3-test",
        ) == "rebuilt"

        window_id = next(
            record.record_id
            for record in selected
            if record.canonical_path == "Pset_WindowCommon.IsExternal"
        )
        hits = index.search_allowed(
            "external property",
            allowed_record_ids={window_id},
            limit=5,
        )
        assert [hit.record_id for hit in hits] == [window_id]
    finally:
        index.close()
