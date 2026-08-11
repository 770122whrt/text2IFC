"""Run a public-only Beam/Column repair against one damaged IFC2X3 model."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.evaluation import evaluation_to_dict  # noqa: E402
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository  # noqa: E402
from text2ifc_ifc_repair.indexer import build_ifc_index  # noqa: E402
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402
from text2ifc_ifc_repair.production_evidence import (  # noqa: E402
    build_production_evidence,
)
from text2ifc_ifc_repair.repair_intent import RepairIntent  # noqa: E402
from text2ifc_ifc_repair.resolution_flow import (  # noqa: E402
    resolve_repair_intent,
)
from text2ifc_ifc_repair.semantic_authoring import (  # noqa: E402
    semantic_manifest_expected_facts,
    semantic_manifest_to_dict,
)


SCHEMA_VERSION = "text2ifc/phase12-public-structural-repair/0.1"
PUBLIC_BUNDLE_SCHEMA_VERSION = (
    "text2ifc/phase12-public-structural-request/0.1"
)
STRUCTURAL_OPERATION_TYPES = frozenset({"add_beam", "add_column"})
_FORBIDDEN_PUBLIC_KEY_PARTS = frozenset(
    {
        "original",
        "mutation",
        "deleted",
        "removed",
        "step",
        "private",
        "gold",
    }
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _text_sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (
        value
        if isinstance(value, str)
        else json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            default=str,
        )
    )
    path.write_text(rendered.rstrip() + "\n", encoding="utf-8")


def validate_public_request_bundle(bundle: Any) -> None:
    """Reject structurally forbidden benchmark channels without echoing values."""

    if not isinstance(bundle, Mapping):
        raise ValueError("PUBLIC_STRUCTURAL_BUNDLE_OBJECT_REQUIRED")

    pending: list[Any] = [bundle]
    while pending:
        value = pending.pop()
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                normalized = str(raw_key).casefold().replace("-", "_")
                tokens = tuple(part for part in normalized.split("_") if part)
                if any(
                    forbidden in tokens
                    for forbidden in _FORBIDDEN_PUBLIC_KEY_PARTS
                ):
                    raise ValueError("PUBLIC_STRUCTURAL_BUNDLE_PRIVATE_FIELD")
                pending.append(child)
        elif isinstance(value, (list, tuple)):
            pending.extend(value)

    version = bundle.get("schema_version")
    if version != PUBLIC_BUNDLE_SCHEMA_VERSION:
        raise ValueError("PUBLIC_STRUCTURAL_BUNDLE_SCHEMA_UNSUPPORTED")
    if not isinstance(bundle.get("request"), str) or not str(
        bundle["request"]
    ).strip():
        raise ValueError("PUBLIC_STRUCTURAL_REQUEST_REQUIRED")
    if not isinstance(bundle.get("operations"), list):
        raise ValueError("PUBLIC_STRUCTURAL_OPERATIONS_REQUIRED")


def _intent_document(
    bundle: Mapping[str, Any],
    *,
    damaged_hash: str,
) -> dict[str, Any]:
    request = str(bundle["request"])
    request_hash = _text_sha256(request)
    prompt_hash = _text_sha256(
        "phase12-frozen-public-structural-request/0.1"
    )
    operations: list[dict[str, Any]] = []
    for index, raw in enumerate(bundle["operations"]):
        if not isinstance(raw, Mapping):
            raise ValueError("PUBLIC_STRUCTURAL_OPERATION_OBJECT_REQUIRED")
        operation_type = str(raw.get("operation_type", ""))
        if operation_type not in STRUCTURAL_OPERATION_TYPES:
            raise ValueError("PUBLIC_STRUCTURAL_OPERATION_UNSUPPORTED")
        family = operation_type.removeprefix("add_")
        excerpt = str(raw.get("request_excerpt") or request)[:2048]
        source = {
            "source_kind": "user_request",
            "reference": f"request:/operations/{index}",
            "excerpt": excerpt,
        }
        target_query = raw.get("target_query")
        if not isinstance(target_query, Mapping):
            raise ValueError("PUBLIC_STRUCTURAL_TARGET_QUERY_REQUIRED")
        operation_id = str(
            raw.get("operation_id") or f"{family}-operation-{index + 1}"
        )
        operations.append(
            {
                "operation_id": operation_id,
                "operation_type": operation_type,
                "routing_intent": {
                    "component_family": family,
                    "action": "add",
                    "operation_profile": f"{family}.add",
                    "source": source,
                },
                "target_query": dict(target_query),
                "parameters": dict(raw.get("parameters") or {}),
                "attribute_intents": list(raw.get("attribute_intents") or []),
                "property_intents": list(raw.get("property_intents") or []),
                "semantic_bundle_refs": list(
                    raw.get("semantic_bundle_refs") or []
                ),
                "quantity_intents": list(raw.get("quantity_intents") or []),
                "occurrence_reuse_intent": raw.get(
                    "occurrence_reuse_intent"
                ),
                "prototype_intent": raw.get("prototype_intent"),
                "provenance": [source],
            }
        )
    if not operations:
        raise ValueError("PUBLIC_STRUCTURAL_OPERATION_SET_EMPTY")
    top_source = {
        "source_kind": "user_request",
        "reference": "request:/text",
        "excerpt": request[:2048],
    }
    return {
        "schema_version": "text2ifc/ifc-repair-intent/0.5",
        "request_id": str(bundle.get("request_id") or "phase12-public-request"),
        "source_request_hash": request_hash,
        "model_fingerprint": damaged_hash,
        "prompt_fingerprint": prompt_hash,
        "operations": operations,
        "semantic_bundles": [],
        "provenance": [top_source],
    }


def _build_authority(
    *,
    intent: RepairIntent,
    resolution: Any,
    registry: Any,
    records: Mapping[str, Any],
    type_records: Mapping[str, Any],
    base_model_fingerprint: str,
) -> tuple[Any, tuple[Any, ...], dict[str, Any], str, str]:
    operation_headers = {
        "operations": [
            {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
            }
            for operation in resolution.operations
        ]
    }
    policy_facts: dict[str, tuple[Any, ...]] = {}
    verified_absence: dict[str, tuple[str, ...]] = {}
    for operation in resolution.operations:
        bound_operation = {
            "operation_id": operation.operation_id,
            "operation_type": operation.operation_type,
            "target": {"storey_global_id": operation.target_global_id},
            "parameters": operation.to_dict()["parameters"],
        }
        policy_facts[operation.operation_id] = (
            registry.build_semantic_policy_facts(
                operation.operation_type,
                operation=bound_operation,
            )
        )
        policy = registry.require_evaluation_policy(operation.operation_type)
        verified_absence[operation.operation_id] = tuple(
            specification.check_id
            for specification in policy.semantic_facts
            if specification.applicability.value == "conditional"
        )
    evidence = build_production_evidence(
        intent=intent,
        resolution=resolution,
        changeset=operation_headers,
        registry=registry,
        records_by_global_id=records,
        type_records_by_global_id=type_records,
        deterministic_policy_facts_by_operation=policy_facts,
        verified_absent_categories_by_operation=verified_absence,
    )
    manifests = tuple(
        registry.build_semantic_manifest(
            evidence.operation_types[operation_id],
            production_evidence=evidence,
            operation_id=operation_id,
            base_model_fingerprint=base_model_fingerprint,
        )
        for operation_id in sorted(evidence.operation_types)
    )
    documents = [semantic_manifest_to_dict(item) for item in manifests]
    if len(manifests) == 1:
        manifest_payload: Any = documents[0]
        manifest_name = "semantic-manifest.json"
    else:
        manifest_payload = {
            "schema_version": (
                "text2ifc/ifc-repair-semantic-manifest-bundle/0.1"
            ),
            "manifests": documents,
        }
        manifest_name = "semantic-manifests.json"
    canonical = (
        json.dumps(
            manifest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )
    return (
        evidence,
        manifests,
        manifest_payload,
        manifest_name,
        _text_sha256(canonical),
    )


def _production_evidence_document(evidence: Any) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/phase12-production-evidence/0.1",
        "operation_types": dict(evidence.operation_types),
        "expected_facts_by_operation": {
            operation_id: [
                {
                    "fact_key": fact.fact_key,
                    "value": fact.value,
                    "value_type": fact.value_type,
                    "unit": fact.unit,
                    "inherited": fact.inherited,
                    "source_kind": fact.source_kind.value,
                    "source_ref": fact.source_ref,
                    "provenance": list(fact.provenance),
                }
                for fact in facts
            ]
            for operation_id, facts in evidence.expected_facts_by_operation.items()
        },
        "applicability_by_operation": {
            operation_id: {
                check_id: {
                    "applicability": decision.applicability,
                    "mandatory": decision.mandatory,
                    "outcome": decision.outcome,
                    "verified_absence": decision.verified_absence,
                    "evidence_pointer": decision.evidence_pointer,
                }
                for check_id, decision in decisions.items()
            }
            for operation_id, decisions in evidence.applicability_by_operation.items()
        },
        "conflicts": [
            {
                "operation_id": item.operation_id,
                "fact_key": item.fact_key,
                "selected_source": item.selected_source.value,
                "rejected_source": item.rejected_source.value,
                "selected_ref": item.selected_ref,
                "rejected_ref": item.rejected_ref,
                "reason": item.reason,
            }
            for item in evidence.conflicts
        ],
    }


def _bound_changeset(
    *,
    bundle: Mapping[str, Any],
    intent: RepairIntent,
    resolution: Any,
    manifests: tuple[Any, ...],
    manifest_name: str,
    manifest_hash: str,
    damaged_hash: str,
) -> dict[str, Any]:
    by_operation = {item.operation_id: item for item in manifests}
    operations: list[dict[str, Any]] = []
    for resolved in resolution.operations:
        manifest = by_operation[resolved.operation_id]
        document = semantic_manifest_to_dict(manifest)
        operations.append(
            {
                "operation_id": resolved.operation_id,
                "operation_type": resolved.operation_type,
                "target": {
                    "storey_global_id": resolved.target_global_id,
                },
                "parameters": resolved.to_dict()["parameters"],
                "evidence_refs": list(resolved.evidence_pointers),
                "semantic_manifest": {
                    "manifest_id": manifest.manifest_id,
                    "policy_id": manifest.policy_id,
                    "policy_version": manifest.policy_version,
                },
                "semantic_assignments": document["assignments"],
            }
        )
    return {
        "schema_version": "text2ifc/ifc-repair-changeset/0.4",
        "changeset_id": str(
            bundle.get("changeset_id") or "phase12-public-changeset"
        ),
        "binding_status": "bound",
        "base_model_fingerprint": damaged_hash,
        "source_request_hash": intent.source_request_hash,
        "semantic_manifest_ref": manifest_name,
        "semantic_manifest_sha256": manifest_hash,
        "scope": {
            "target_ids": list(
                dict.fromkeys(
                    item.target_global_id for item in resolution.operations
                )
            ),
            "forbidden_ids": [],
        },
        "evidence_refs": list(
            dict.fromkeys(
                pointer
                for item in resolution.operations
                for pointer in item.evidence_pointers
            )
        ),
        "preconditions": [
            "structural_targets_resolved",
            "structural_geometry_authorized",
            "structural_semantics_bound",
        ],
        "postconditions": [
            "structural_geometry_matches",
            "structural_containment_matches",
            "structural_type_matches",
        ],
        "operations": operations,
    }


def run_public_repair(
    *,
    damaged_ifc: Path,
    public_request_bundle: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Resolve, bind, apply, reopen and evaluate using public inputs only."""

    bundle = json.loads(public_request_bundle.read_text(encoding="utf-8"))
    validate_public_request_bundle(bundle)
    if output_root.exists():
        raise FileExistsError(f"output already exists: {output_root}")
    output_root.mkdir(parents=True)
    damaged_copy = output_root / "damaged.ifc"
    shutil.copy2(damaged_ifc, damaged_copy)
    damaged_hash = _sha256(damaged_copy)
    request = str(bundle["request"])
    registry = create_default_registry()
    intent = RepairIntent.from_dict(
        _intent_document(bundle, damaged_hash=damaged_hash),
        registry=registry,
        require_complete=False,
    )
    index_path = output_root / "target-index.sqlite"
    metadata = build_ifc_index(damaged_copy, index_path)
    if metadata.source_ifc_sha256 != damaged_hash:
        raise RuntimeError("PUBLIC_DAMAGED_IFC_FINGERPRINT_MISMATCH")
    with SQLiteIndexRepository.open(index_path) as repository:
        resolution = resolve_repair_intent(
            intent,
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
        )
        records = {
            item.ifc_global_id: item for item in repository.iter_records()
        }
        type_records = {
            item.ifc_global_id: item
            for item in repository.iter_type_records()
        }
    if resolution.status != "resolved":
        raise RuntimeError(
            "PUBLIC_STRUCTURAL_RESOLUTION_FAILED:"
            + json.dumps(resolution.to_dict(), ensure_ascii=False)
        )
    (
        evidence,
        manifests,
        manifest_payload,
        manifest_name,
        manifest_hash,
    ) = _build_authority(
        intent=intent,
        resolution=resolution,
        registry=registry,
        records=records,
        type_records=type_records,
        base_model_fingerprint=damaged_hash,
    )
    changeset = _bound_changeset(
        bundle=bundle,
        intent=intent,
        resolution=resolution,
        manifests=manifests,
        manifest_name=manifest_name,
        manifest_hash=manifest_hash,
        damaged_hash=damaged_hash,
    )
    _write(output_root / manifest_name, manifest_payload)
    repaired = output_root / "repaired.ifc"
    application = apply_changeset(
        damaged_ifc_path=damaged_copy,
        repair_request=request,
        changeset=changeset,
        output_path=repaired,
        registry=registry,
    )
    if not application.get("valid") or not application.get("published"):
        raise RuntimeError(
            "PUBLIC_STRUCTURAL_APPLICATION_FAILED:"
            + json.dumps(application.get("issues"), ensure_ascii=False)
        )
    expected = {
        manifest.operation_id: semantic_manifest_expected_facts(manifest)
        for manifest in manifests
    }
    evaluation = evaluation_to_dict(
        evaluate_production(
            ProductionEvaluationInputs(
                damaged_ifc_path=damaged_copy,
                repaired_ifc_path=repaired,
                changeset=changeset,
                application_result=application,
                registry=registry,
                expected_facts_by_operation=expected,
            )
        )
    )
    if not evaluation["complete_repair_success"]:
        raise RuntimeError(
            "PUBLIC_STRUCTURAL_EVALUATION_FAILED:"
            + json.dumps(evaluation, ensure_ascii=False, default=str)
        )
    allowed = {
        str(item["global_id"])
        for result in application["operations"]
        for kind in ("created", "modified", "removed")
        for item in result["changes"].get(kind, ())
        if item.get("global_id")
    }
    comparison = compare_ifc_models(
        damaged_copy,
        repaired,
        allowed_changed_ids=allowed,
    )
    if not comparison["complete_preservation_success"]:
        raise RuntimeError("PUBLIC_STRUCTURAL_PRESERVATION_FAILED")
    boundary = {
        "schema_version": "text2ifc/production-input-boundary/0.2",
        "entrypoint": "run_phase12_public_structural_repair.py",
        "ifc_inputs": ["damaged_ifc_path"],
        "request_inputs": ["public_request_bundle"],
        "original_ifc_supplied": False,
        "mutation_manifest_supplied": False,
        "deleted_object_ids_supplied": False,
        "private_comparator_available_during_repair": False,
        "damaged_ifc_sha256": damaged_hash,
        "request_sha256": intent.source_request_hash,
        "public_request_bundle_sha256": _sha256(public_request_bundle),
        "resolved_target_count": len(resolution.operations),
    }
    operation_families = {
        family: sum(
            item.operation_type == f"add_{family}"
            for item in resolution.operations
        )
        for family in ("beam", "column")
    }
    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": str(bundle.get("case_id") or "phase12-public-structural"),
        "status": "passed",
        "provider_evidence_mode": "offline_bound_deterministic",
        "synthetic_fallback_used": False,
        "operation_count": len(resolution.operations),
        "operation_families": {
            key: value for key, value in operation_families.items() if value
        },
        "one_atomic_changeset": True,
        "production_input_boundary": boundary,
        "artifacts": {},
    }
    _write(output_root / "request.txt", request)
    _write(output_root / "repair-intent.json", intent.to_dict())
    _write(output_root / "target-resolution.json", resolution.to_dict())
    _write(
        output_root / "production-evidence.json",
        _production_evidence_document(evidence),
    )
    _write(output_root / "changeset.json", changeset)
    _write(output_root / "application.json", application)
    _write(output_root / "evaluation.json", evaluation)
    _write(output_root / "comparison.json", comparison)
    _write(output_root / "production-boundary.json", boundary)
    artifact_names = (
        "damaged.ifc",
        "repaired.ifc",
        "request.txt",
        "repair-intent.json",
        "target-resolution.json",
        "production-evidence.json",
        manifest_name,
        "changeset.json",
        "application.json",
        "evaluation.json",
        "comparison.json",
        "production-boundary.json",
    )
    for name in artifact_names:
        path = output_root / name
        manifest["artifacts"][name] = {
            "path": name,
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
    _write(output_root / "manifest.json", manifest)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--damaged-ifc", type=Path, required=True)
    parser.add_argument(
        "--public-request-bundle",
        type=Path,
        required=True,
    )
    parser.add_argument("--output-root", type=Path, required=True)
    arguments = parser.parse_args(argv)
    result = run_public_repair(
        damaged_ifc=arguments.damaged_ifc,
        public_request_bundle=arguments.public_request_bundle,
        output_root=arguments.output_root,
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "case_id": result["case_id"],
                "operation_count": result["operation_count"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
