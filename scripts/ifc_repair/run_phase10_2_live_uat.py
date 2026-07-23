"""Real Phase 10.2 DeepSeek + BGE-M3 + Qdrant LargeBuilding UAT."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ifcopenshell

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from text2ifc_agent.openai_compat import (  # noqa: E402
    OpenAICompatibleLiveProvider,
    load_openai_compatible_config,
    load_openai_compatible_runtime_config,
)
from text2ifc_ifc_repair.api import RepairAPI  # noqa: E402
from text2ifc_knowledge.property_search import (  # noqa: E402
    BgeM3EmbeddingProvider,
    PropertyKnowledgeResolver,
    QdrantVectorIndex,
    build_standard_property_records,
    collection_fingerprint,
    default_standard_corpus_fingerprint,
    load_property_resolution_policy,
    load_reviewed_aliases,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry  # noqa: E402


SOURCE = ROOT / "dataset/external/bim-whale-ifc-samples/LargeBuilding/IFC/LargeBuilding.ifc"
DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair/phase10.2-live-uat"
DEFAULT_MODEL_PATH = ROOT / ".cache/models/BAAI-bge-m3"
WINDOW_ID = "2cXV28XOjE6f6irgi0CO4t"
TOKEN_GUARD = 65_536
REQUEST = (
    f"将 GlobalId 为 {WINDOW_ID} 的 IfcWindow 标记为外窗，"
    "属性值为 true。只修改这个窗户 occurrence，不修改共享 Type。"
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-config", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--allow-model-download", action="store_true")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.check_config == args.live:
        parser.error("choose exactly one of --check-config or --live")
    environment = _environment(args.env_file)
    config = _config_result(environment)
    if args.check_config:
        print(_json(config))
        return 0 if config["status"] == "ready" else 2
    if config["status"] != "ready":
        print(_json(config))
        return 2

    run_root = args.output_root / datetime.now(timezone.utc).strftime(
        "uat-%Y%m%dT%H%M%S%fZ"
    )
    run_root.mkdir(parents=True, exist_ok=False)
    result = _run(
        run_root,
        environment,
        allow_model_download=args.allow_model_download,
    )
    _write(run_root / "live-uat-result.json", result)
    print(_json(result))
    return 0 if result["status"] == "passed" else 2


def _run(
    output: Path,
    environment: dict[str, str],
    *,
    allow_model_download: bool,
) -> dict[str, Any]:
    fixture = output / "fixture"
    fixture.mkdir()
    damaged = fixture / "damaged.ifc"
    _remove_direct_property(SOURCE, damaged)

    registry = load_ifc2x3_registry()
    corpus_fingerprint = default_standard_corpus_fingerprint()
    records = build_standard_property_records(
        registry,
        corpus_fingerprint=corpus_fingerprint,
    )
    aliases = load_reviewed_aliases()
    embedding = BgeM3EmbeddingProvider(
        model_path=(
            str(DEFAULT_MODEL_PATH)
            if (DEFAULT_MODEL_PATH / "pytorch_model.bin").is_file()
            else "BAAI/bge-m3"
        ),
        local_files_only=(
            (DEFAULT_MODEL_PATH / "pytorch_model.bin").is_file()
            or not allow_model_download
        ),
    )
    vector = QdrantVectorIndex(
        embedding,
        collection_name="text2ifc_ifc2x3_properties_v01",
        path=output.parent / "_knowledge" / "qdrant",
    )
    fingerprint = collection_fingerprint(
        corpus_fingerprint=corpus_fingerprint,
        aliases=aliases,
        embedding_provider=embedding,
    )
    try:
        vector_status = vector.ensure(
            records,
            collection_fingerprint=fingerprint,
        )
    except Exception as error:
        vector.close()
        return {
            "schema_version": "text2ifc/phase10.2-live-uat/0.1",
            "status": "failed",
            "reason_code": str(error)[:256],
            "stage": "knowledge_preparation",
            "synthetic_fallback": False,
        }
    policy = load_property_resolution_policy()
    resolver = PropertyKnowledgeResolver(
        registry=registry,
        records=records,
        aliases=aliases,
        vector_index=vector,
        max_candidates=policy.max_candidates,
        vector_min_score=policy.vector_min_score,
        vector_min_margin=policy.vector_min_margin,
    )
    runtime = output / "runtime"
    try:
        api = RepairAPI(
            runtime,
            provider=OpenAICompatibleLiveProvider(
                config=load_openai_compatible_runtime_config(environment)
            ),
            intent_schema_version="text2ifc/ifc-repair-intent/0.3",
            property_knowledge_resolver=resolver,
        )
        final = api.start(damaged, REQUEST)
        run_dir = runtime / final.run_directory
        evidence_paths = sorted(
            path.relative_to(run_dir).as_posix()
            for path in (run_dir / "property-resolution").rglob("*.json")
        ) if (run_dir / "property-resolution").is_dir() else []
        actual = None
        evaluation = {}
        if "evaluation" in final.artifacts:
            evaluation = json.loads(
                (run_dir / final.artifacts["evaluation"]).read_text(
                    encoding="utf-8"
                )
            )
        production_levels = {
            str(item["level"]): str(item["status"])
            for operation in evaluation.get("operations", ())
            for item in operation.get("levels", ())
        }
        if "successful_ifc" in final.artifacts:
            repaired = ifcopenshell.open(
                str(run_dir / final.artifacts["successful_ifc"])
            )
            actual = _direct_property(
                repaired.by_guid(WINDOW_ID),
                "Pset_WindowCommon",
                "IsExternal",
            )
        attempts = {
            "stage1": len(list(run_dir.rglob("intent/attempt-*.json"))),
            "stage2": len(
                list(run_dir.rglob("changeset/attempt-*/provider-metadata.json"))
            ),
        }
        passed = (
            final.successful_artifact_publishable
            and attempts["stage1"] > 0
            and attempts["stage2"] > 0
            and actual == {
                "value": True,
                "value_type": "IfcBoolean",
                "ownership": "occurrence_direct",
            }
            and production_levels
            == {"L1": "passed", "L2": "passed", "L3": "not_required"}
            and len(evidence_paths) == 3
        )
        result = {
            "schema_version": "text2ifc/phase10.2-live-uat/0.1",
            "status": "passed" if passed else "failed",
            "reason_code": final.reason_code,
            "run_id": final.run_id,
            "terminal_status": final.status,
            "request": REQUEST,
            "source_sha256": _sha256(SOURCE),
            "damaged_sha256": _sha256(damaged),
            "provider_attempts": attempts,
            "knowledge_health": {
                "status": "ready",
                "embedding_model": embedding.model_id,
                "embedding_model_fingerprint": embedding.model_fingerprint,
                "qdrant_mode": "local",
                "collection_status": vector_status,
                "collection_fingerprint": fingerprint,
                "record_count": len(records),
            },
            "property_resolution_evidence": evidence_paths,
            "requested_property_actual": actual,
            "production_levels": production_levels,
            "successful_ifc": final.artifacts.get("successful_ifc"),
            "successful_ifc_sha256": (
                _sha256(run_dir / final.artifacts["successful_ifc"])
                if "successful_ifc" in final.artifacts
                else None
            ),
            "synthetic_fallback": False,
        }
        vector.close()
        return result
    except Exception as error:
        result = {
            "schema_version": "text2ifc/phase10.2-live-uat/0.1",
            "status": "failed",
            "reason_code": str(
                getattr(error, "code", type(error).__name__)
            )[:256],
            "stage": "repair_pipeline",
            "knowledge_health": {
                "status": "ready",
                "embedding_model": embedding.model_id,
                "collection_status": vector_status,
            },
            "synthetic_fallback": False,
        }
        vector.close()
        return result


def _remove_direct_property(source: Path, output: Path) -> None:
    model = ifcopenshell.open(str(source))
    target = model.by_guid(WINDOW_ID)
    removed = 0
    for relation in target.IsDefinedBy:
        if not relation.is_a("IfcRelDefinesByProperties"):
            continue
        pset = relation.RelatingPropertyDefinition
        if not pset.is_a("IfcPropertySet") or pset.Name != "Pset_WindowCommon":
            continue
        properties = [
            item for item in pset.HasProperties if item.Name != "IsExternal"
        ]
        removed += len(pset.HasProperties) - len(properties)
        pset.HasProperties = properties
    if removed != 1:
        raise ValueError(f"DAMAGE_PROPERTY_CARDINALITY:{removed}")
    model.write(str(output))


def _direct_property(
    element: Any,
    set_name: str,
    property_name: str,
) -> dict[str, Any] | None:
    matches = []
    for relation in element.IsDefinedBy:
        if relation.is_a("IfcRelDefinesByProperties"):
            pset = relation.RelatingPropertyDefinition
            if pset.is_a("IfcPropertySet") and pset.Name == set_name:
                matches.extend(
                    item for item in pset.HasProperties
                    if item.Name == property_name
                )
    if len(matches) != 1 or matches[0].NominalValue is None:
        return None
    return {
        "value": matches[0].NominalValue.wrappedValue,
        "value_type": matches[0].NominalValue.is_a(),
        "ownership": "occurrence_direct",
    }


def _config_result(environment: dict[str, str]) -> dict[str, Any]:
    config = load_openai_compatible_config(environment)
    ready = (
        bool(config.get("configured"))
        and config.get("max_input_tokens") == TOKEN_GUARD
        and config.get("max_completion_tokens") == TOKEN_GUARD
    )
    return {
        "status": "ready" if ready else "not_configured",
        "provider": config.get("provider", "deepseek-openai-compatible"),
        "model": config.get("model"),
        "max_input_tokens": config.get("max_input_tokens"),
        "max_completion_tokens": config.get("max_completion_tokens"),
        "missing": list(config.get("missing", [])),
        "secret_redacted": True,
    }


def _environment(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if path.is_file():
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json(value) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
