"""Validate the checked-in IFC repair success-case collection.

The command is intentionally independent from the production evaluator. It
checks that frozen proof artifacts still agree with their manifests and can be
used as a release/checkpoint gate before adding another operation family.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import ifcopenshell
import ifcopenshell.util.element
from jsonschema import Draft202012Validator
from text2ifc_agent.prompt_registry import load_prompt_registry

try:
    from scripts.ifc_repair.audit_door_repair_triplet import (
        DOOR_OPERATION_TYPES,
        audit_case,
    )
except ModuleNotFoundError:  # Direct script execution from scripts/ifc_repair.
    from audit_door_repair_triplet import DOOR_OPERATION_TYPES, audit_case
from text2ifc_ifc_repair.audit import audit_changeset
from text2ifc_ifc_repair.compare import profile_normalized_model_diff
from text2ifc_ifc_repair.evaluation_policy import (
    STRUCTURAL_L1_CHECK_IDS,
    EvidenceSourceKind,
)
from text2ifc_ifc_repair.geometry import (
    opening_dimensions_mm,
    opening_position_in_wall_mm,
)
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository
from text2ifc_ifc_repair.indexer import build_ifc_index
from text2ifc_ifc_repair.mutation import remove_structural_members
from text2ifc_ifc_repair.operations import create_default_registry
from text2ifc_ifc_repair.operations.hosted_opening import deterministic_global_id
from text2ifc_ifc_repair.prompt_profiles import (
    compact_profile_catalog,
    load_prompt_profiles,
    select_prompt_profiles,
)
from text2ifc_ifc_repair.production_evidence import build_production_evidence
from text2ifc_ifc_repair.property_admissibility import admit_property_decision
from text2ifc_ifc_repair.property_intent import NaturalLanguagePropertyIntent
from text2ifc_ifc_repair.property_resolution_stage import (
    TEMPLATE_ID as PROPERTY_RESOLUTION_TEMPLATE_ID,
)
from text2ifc_ifc_repair.repair_intent import RepairIntent
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent
from text2ifc_ifc_repair.run_models import hash_json
from text2ifc_ifc_repair.semantic_authoring import semantic_manifest_to_dict
from text2ifc_ifc_repair.semantic_facts import (
    SemanticFact,
    extract_ifc_semantic_facts,
    extract_property_facts,
)
from text2ifc_ifc_repair.type_templates import type_authority_fingerprint
from text2ifc_knowledge.property_search import (
    PropertyResolutionDecision,
    ResolvedExactProperty,
    build_standard_property_records,
    default_standard_corpus_fingerprint,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry


ROOT = Path(__file__).resolve().parents[2]
PROPERTY_RESOLUTION_TEMPLATE_HASH = str(
    load_prompt_registry()[PROPERTY_RESOLUTION_TEMPLATE_ID]["sha256"]
)
DEFAULT_COLLECTION = (
    ROOT / "dataset" / "processed" / "proof" / "ifc-repair-success-cases"
)
MANDATORY_LEVELS = ("L1", "L2")
BOUND_CHANGESET_ROLES = ("bound_changeset", "bound_changeset_replayed")
PRODUCTION_EVALUATION_ROLES = (
    "production_publication_evidence",
    "production_evaluation",
)
STRUCTURAL_OPERATION_TYPES = frozenset({"add_beam", "add_column"})
STRUCTURAL_FAMILY_BY_OPERATION = {
    "add_beam": "beam",
    "add_column": "column",
}
STRUCTURAL_OCCURRENCE_CLASS = {
    "beam": "IfcBeam",
    "column": "IfcColumn",
}
CURRENT_STAGE_1_5_REASON = "PROPERTY_ADMISSIBLE_STAGE_1_5"
HISTORICAL_ALIAS_REASON = "REVIEWED_ALIAS_EXACT"


def _profile_id_for_intent_schema(
    operation_type: str,
    *,
    intent_schema_version: str,
) -> str:
    profile_id = str(
        create_default_registry().require(operation_type).prompt_profile_id
    )
    if profile_id in {"beam.add.v0.3", "column.add.v0.3"}:
        base_profile_id = profile_id.removesuffix(".v0.3")
        if intent_schema_version == "text2ifc/ifc-repair-intent/0.5":
            return base_profile_id
        if intent_schema_version == "text2ifc/ifc-repair-intent/0.6":
            return f"{base_profile_id}.v0.2"
    return profile_id


STRUCTURAL_TYPE_CLASS = {
    "beam": "IfcBeamType",
    "column": "IfcColumnType",
}
_PHASE12_SOURCE_CONTRACTS = {
    "dataset/ifc/test/d7n.ifc": (
        "43b6756b88874f9525f6a511d7dc718844dac59b638a11e3fbc36b321e0ab8b7",
        3_293_724,
    ),
    "dataset/ifc/train/vvo.ifc": (
        "b6c435be955aeb6b2998f42a62f4ebf8c3f91eb7d373ca71a2dcedfeb95b3fdc",
        2_409_268,
    ),
}
_PHASE12_DAMAGE_TARGET_IDS = {
    "phase12-d7n-beam-loadbearing": {"1RnWak0Kr6GxkeYF4Sd_bw"},
    "phase12-d7n-column-loadbearing": {"3dldEzenf9LvnDJYNNzLsH"},
    "phase12-d7n-beam-column-atomic": {
        "1RnWak0Kr6GxkeYF4Sd_bw",
        "3dldEzenf9LvnDJYNNzLsH",
    },
    "phase12-vvo-beam-material-present": {"17tPjyQtf2L9JnbXXmcTUF"},
    "phase12-vvo-column-material-absent": {"1rsYNObuDC4euALdw6WUK4"},
    "phase12-vvo-door-window-beam-column-atomic": {
        "2IUEnGd5v4Yfg1ZlPtd0qa",
        "1B$rgWypT66viEf2CI1iIv",
        "2dYMXn0_5AKRbD_0yUIAqJ",
        "08xWVL$9z6JRwr3oWJHoAz",
        "2dYMXn0_5AKRbD_1mUIAqJ",
        "08xWVL$9z6JRwr3piJHoAz",
    },
}
_PHASE12_MIXED_DAMAGED_SHA256 = (
    "6824086b4171cce034acaa23ad51c3020d87ed44c0aead62979a4b4ad17c4db3"
)
_STRUCTURAL_PRIVATE_CANARY_MARKERS = (
    "canary-structural",
    "private-gold",
    "gold-changeset",
)
_STRUCTURAL_FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "original_ifc_path",
        "mutation_manifest",
        "deleted_object_ids",
        "removed_global_id",
        "removed_step_id",
        "private_geometry",
        "gold_changeset",
    }
)


@dataclass
class ProofValidationResult:
    status: str
    collection_root: str
    case_count: int = 0
    operation_count: int = 0
    checked_file_count: int = 0
    reopened_ifc_count: int = 0
    independently_recomputed_case_count: int = 0
    legacy_unverifiable_case_count: int = 0
    strict_stage_1_5_case_count: int = 0
    historical_property_artifact_case_count: int = 0
    errors: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    cases: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "text2ifc/ifc-repair-proof-validation/0.2",
            "status": self.status,
            "collection_root": self.collection_root,
            "case_count": self.case_count,
            "operation_count": self.operation_count,
            "checked_file_count": self.checked_file_count,
            "reopened_ifc_count": self.reopened_ifc_count,
            "independently_recomputed_case_count": (
                self.independently_recomputed_case_count
            ),
            "legacy_unverifiable_case_count": self.legacy_unverifiable_case_count,
            "strict_stage_1_5_case_count": self.strict_stage_1_5_case_count,
            "historical_property_artifact_case_count": (
                self.historical_property_artifact_case_count
            ),
            "errors": self.errors,
            "limitations": self.limitations,
            "cases": self.cases,
        }


PROOF_VALIDATION_SCHEMA = (
    ROOT / "schemas/agent/ifc-repair-proof-validation-0.2.schema.json"
)


def validate_proof_validation_document(document: Mapping[str, Any]) -> None:
    schema = _read_json(PROOF_VALIDATION_SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(dict(document))


def validate_success_case_collection(
    collection_root: Path | str = DEFAULT_COLLECTION,
) -> ProofValidationResult:
    root = Path(collection_root).resolve()
    result = ProofValidationResult(status="failed", collection_root=root.as_posix())
    try:
        collection = _read_json(root / "manifest.json")
        cases = collection.get("cases")
        if not isinstance(cases, list):
            raise ValueError("collection manifest cases must be a list")
        if int(collection.get("case_count", -1)) != len(cases):
            raise ValueError("collection case_count does not match cases")
        case_ids = [str(item.get("case_id")) for item in cases]
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("collection case_id values must be unique")
        result.case_count = len(cases)
        for case in cases:
            try:
                summary = _validate_case(root, case)
                result.cases.append(summary)
                result.operation_count += summary["operation_count"]
                result.checked_file_count += summary["checked_file_count"]
                result.reopened_ifc_count += summary["reopened_ifc_count"]
                if summary["audit_coverage"] == "strict_recomputed":
                    result.independently_recomputed_case_count += 1
                else:
                    result.legacy_unverifiable_case_count += 1
                    result.limitations.append(
                        f"{summary['case_id']}: {summary['independent_reaudit_error']}"
                    )
                property_coverage = summary.get("property_authority_coverage")
                if property_coverage == "strict_stage_1_5_recomputed":
                    result.strict_stage_1_5_case_count += 1
                elif property_coverage == "historical_property_artifact_only":
                    result.historical_property_artifact_case_count += 1
            except Exception as error:
                case_id = str(case.get("case_id", "<unknown>"))
                result.errors.append(f"{case_id}: {error}")
    except Exception as error:
        result.errors.append(f"collection: {error}")
    result.status = "passed" if not result.errors else "failed"
    return result


def _validate_case(root: Path, case: Mapping[str, Any]) -> dict[str, Any]:
    case_id = str(case["case_id"])
    if case.get("status") != "accepted":
        raise ValueError("case status must be accepted")
    operation_count = int(case["operation_count"])
    if operation_count < 1:
        raise ValueError("operation_count must be positive")

    report_path = _safe_path(root, str(case["report"]))
    files_path = _safe_path(root, str(case["files"]))
    if not report_path.is_file():
        raise FileNotFoundError(f"missing report: {report_path}")
    files_manifest = _read_json(files_path)
    if files_manifest.get("case_id") != case_id:
        raise ValueError("FILES.json case_id mismatch")
    case_root = files_path.parent

    entries = files_manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("FILES.json files must be a non-empty list")
    listed_paths: set[str] = set()
    roles: dict[str, Path] = {}
    checked_file_count = 0
    for entry in entries:
        relative = str(entry["path"])
        if relative in listed_paths:
            raise ValueError(f"duplicate FILES.json path: {relative}")
        listed_paths.add(relative)
        artifact = _safe_path(case_root, relative)
        if not artifact.is_file():
            raise FileNotFoundError(f"proof.artifact.missing:{relative}")
        expected_size = int(entry["size_bytes"])
        actual_size = artifact.stat().st_size
        if actual_size != expected_size:
            raise ValueError(
                f"size mismatch for {relative}: {actual_size} != {expected_size}"
            )
        if entry.get("sha256") is None:
            raise ValueError(f"proof.hash.required:{relative}")
        expected_hash = _normalize_sha256(str(entry["sha256"]))
        actual_hash = _sha256(artifact)
        if actual_hash != expected_hash:
            raise ValueError(f"proof.hash.sha256:{relative}")
        role = str(entry["role"])
        if role in roles:
            raise ValueError(f"duplicate artifact role: {role}")
        roles[role] = artifact
        checked_file_count += 1

    actual_paths = {
        path.relative_to(case_root).as_posix()
        for path in case_root.rglob("*")
        if path.is_file()
    }
    expected_paths = listed_paths | {"FILES.json", "REPORT.md"}
    if actual_paths != expected_paths:
        missing = sorted(expected_paths - actual_paths)
        unindexed = sorted(actual_paths - expected_paths)
        raise ValueError(
            f"FILES.json coverage mismatch; missing={missing}, unindexed={unindexed}"
        )

    required_role_paths = {
        "original_ground_truth": _safe_path(root, str(case["original_ifc"])),
        "repair_input_ifc": _safe_path(root, str(case["damaged_ifc"])),
        "published_repair_output": _safe_path(root, str(case["repaired_ifc"])),
    }
    reopened_ifc_count = 0
    models: dict[str, Any] = {}
    for role, manifest_path in required_role_paths.items():
        artifact = roles.get(role)
        if artifact is None or artifact != manifest_path:
            raise ValueError(f"{role} path does not match collection manifest")
        model = ifcopenshell.open(str(artifact))
        if model.schema != "IFC2X3":
            raise ValueError(f"{role} schema is {model.schema}, expected IFC2X3")
        models[role] = model
        reopened_ifc_count += 1

    damaged_hash = _sha256(required_role_paths["repair_input_ifc"])
    changeset_path = _path_for_any_role(roles, BOUND_CHANGESET_ROLES)
    changeset = _read_json(changeset_path)
    if _normalize_sha256(str(changeset["base_model_fingerprint"])) != damaged_hash:
        raise ValueError("Bound ChangeSet base_model_fingerprint mismatch")
    expected_operation_types = {
        str(item)
        for item in case.get(
            "operation_types", (case.get("operation_type"),)
        )
        if item is not None
    }
    if not expected_operation_types:
        raise ValueError("case operation types must be non-empty")
    _check_operations(
        changeset.get("operations"),
        operation_count=operation_count,
        operation_types=expected_operation_types,
        source="Bound ChangeSet",
    )
    structural_operation_count = sum(
        str(operation.get("operation_type")) in STRUCTURAL_OPERATION_TYPES
        for operation in changeset.get("operations", ())
        if isinstance(operation, Mapping)
    )
    existing_structural_property_operations = [
        operation
        for operation in changeset.get("operations", ())
        if isinstance(operation, Mapping)
        and _is_existing_structural_property_operation(
            operation,
            damaged_model=models["repair_input_ifc"],
        )
    ]
    has_structural_operations = (
        structural_operation_count > 0
        or bool(existing_structural_property_operations)
    )
    if existing_structural_property_operations:
        raise ValueError(
            "l0.structural.proof:existing_occurrence_property_not_curated"
        )

    intent: Mapping[str, Any] | None = None
    intent_path = roles.get("stage1_repair_intent")
    if intent_path is not None:
        intent = _read_json(intent_path)
        _check_operations(
            intent.get("operations"),
            operation_count=operation_count,
            operation_types=expected_operation_types,
            source="RepairIntent",
        )
    elif case.get("provider_evidence_mode") == "offline_bound_deterministic":
        _check_prompt_profile_evidence(
            roles,
            changeset=changeset,
            operation_count=operation_count,
        )
    else:
        raise ValueError("missing stage1_repair_intent")

    source_manifest_path = roles.get("source_run_manifest")
    source_manifest = (
        _read_json(source_manifest_path)
        if source_manifest_path is not None
        else None
    )
    if source_manifest is not None:
        if source_manifest.get("synthetic_fallback_used") is not False:
            if has_structural_operations:
                raise ValueError("l0.structural.no-fallback")
            raise ValueError("source run used synthetic fallback")
        if source_manifest.get("public_targeting", {}).get("guid_free") is True:
            _check_guid_free_targeting(
                roles,
                operation_count=operation_count,
                operation_types=expected_operation_types,
                name_free=(
                    source_manifest.get("public_targeting", {}).get("name_free")
                    is True
                ),
            )
    elif has_structural_operations:
        raise ValueError("l0.structural.no-fallback:source_run_manifest_missing")

    live_authority = _unrecomputed_property_authority(
        intent=intent,
        roles=roles,
    )
    if has_structural_operations:
        if intent is None:
            raise ValueError("l0.structural.provenance:intent_missing")
        if source_manifest is None:
            raise ValueError("l0.structural.no-fallback:source_run_manifest_missing")
        _audit_structural_bound_changeset(
            roles=roles,
            damaged_ifc_path=required_role_paths["repair_input_ifc"],
            changeset=changeset,
        )
        live_authority = _audit_structural_provenance_chain(
            case=case,
            roles=roles,
            intent=intent,
            changeset=changeset,
            damaged_sha256=damaged_hash,
            damaged_ifc_path=required_role_paths["repair_input_ifc"],
            source_manifest=source_manifest,
        )

    application_path = roles.get("application_result")
    independent = {"l1_operation_count": 0, "l2_operation_count": 0}
    independent_reaudit_error: str | None = None
    if application_path is not None:
        application = _read_json(application_path)
        expected_application_ids = [
            str(item.get("operation_id"))
            for item in changeset.get("operations", ())
        ]
        actual_application_ids = [
            str(item.get("operation_id"))
            for item in application.get("operations", ())
            if isinstance(item, Mapping)
        ]
        if (
            application.get("valid") is not True
            or application.get("published") is not True
            or len(application.get("operations", ())) != operation_count
            or actual_application_ids != expected_application_ids
        ):
            raise ValueError("application_result is not a complete publication")
        independent = audit_repaired_operations(
            changeset=changeset,
            application=application,
            damaged_model=models["repair_input_ifc"],
            repaired_model=models["published_repair_output"],
        )
    else:
        independent_reaudit_error = (
            "legacy Proof does not retain application_result role mappings; "
            "saved L1/L2 evidence was checked but cannot be independently "
            "recomputed by the current operation registry"
        )
    if has_structural_operations:
        _audit_structural_type_and_semantic_authority(
            changeset=changeset,
            damaged_model=models["repair_input_ifc"],
            repaired_model=models["published_repair_output"],
        )
        _audit_structural_production_isolation(
            roles=roles,
            damaged_sha256=damaged_hash,
            changeset=changeset,
            operation_count=operation_count,
        )
        _audit_structural_source_manifest(
            source_manifest=source_manifest,
            source_manifest_path=source_manifest_path,
            case_root=case_root,
        )
        if case.get("phase") == "12":
            evidence_mode = str(case.get("provider_evidence_mode") or "")
            damage_manifest = source_manifest
            damage_case_id = case_id
            if evidence_mode == "live":
                if source_manifest.get("schema_version") != (
                    "text2ifc/phase12-live-proof-source/0.1"
                ):
                    raise ValueError("l0.structural.live:source_manifest_schema")
                damage_manifest, damage_case_id = _audit_live_base_damage_authority(
                    roles=roles,
                    source_manifest=source_manifest,
                    original_ifc_path=required_role_paths["original_ground_truth"],
                    damaged_ifc_path=required_role_paths["repair_input_ifc"],
                )
                live_authority["base_damage_case_id"] = damage_case_id
            elif source_manifest.get("schema_version") != (
                "text2ifc/phase12-offline-case/0.1"
            ):
                raise ValueError("l0.structural.damage:source_manifest_schema")
            _audit_phase12_damage_provenance(
                case=case,
                roles=roles,
                source_manifest=damage_manifest,
                damage_case_id=damage_case_id,
                original_model=models["original_ground_truth"],
                damaged_model=models["repair_input_ifc"],
                original_ifc_path=required_role_paths["original_ground_truth"],
                damaged_ifc_path=required_role_paths["repair_input_ifc"],
            )
        _audit_structural_preservation(
            changeset=changeset,
            damaged_model=models["repair_input_ifc"],
            repaired_model=models["published_repair_output"],
        )
    injected_failure_path = roles.get("injected_failure_application")
    if injected_failure_path is not None:
        injected = _read_json(injected_failure_path)
        if (
            injected.get("valid") is not False
            or injected.get("published") is not False
        ):
            raise ValueError("injected failure did not fail closed")

    production_path = _path_for_any_role(roles, PRODUCTION_EVALUATION_ROLES)
    production = _read_json(production_path)
    _check_success_evaluation(production, operation_count=operation_count)
    private_path = roles.get("private_ground_truth_evaluation")
    if private_path is not None:
        _check_success_evaluation(
            _read_json(private_path),
            operation_count=operation_count,
        )
    release_path = roles.get("l0_l1_l2_release_decision")
    audit_path = roles.get("three_way_l0_l1_l2_audit")
    if release_path is not None or audit_path is not None:
        if release_path is None or audit_path is None:
            raise ValueError("three-way audit artifact set is incomplete")
        release = _read_json(release_path)
        if (
            release.get("l0_pass") is not True
            or release.get("l1_pass") is not True
            or release.get("l2_pass") is not True
            or release.get("publishable") is not True
            or release.get("blocking_findings")
        ):
            raise ValueError("L0/L1/L2 release decision is not publishable")
        audit = _read_json(audit_path)
        if audit.get("release_decision") != release:
            raise ValueError("three-way audit release decision mismatch")

    independent_triplet_audit_publishable: bool | None = None
    if expected_operation_types & DOOR_OPERATION_TYPES:
        triplet = audit_case(case_root, write=False)
        triplet_release = triplet["release_decision"]
        independent_triplet_audit_publishable = bool(
            triplet_release.get("l0_pass") is True
            and triplet_release.get("l1_pass") is True
            and triplet_release.get("l2_pass") is True
            and triplet_release.get("publishable") is True
            and not triplet_release.get("blocking_findings")
        )
        if not independent_triplet_audit_publishable:
            raise ValueError("independent three-way audit is not publishable")

    return {
        "case_id": case_id,
        "status": "passed",
        "operation_count": operation_count,
        "checked_file_count": checked_file_count,
        "reopened_ifc_count": reopened_ifc_count,
        "operation_types": sorted(expected_operation_types),
        "audit_coverage": (
            "strict_recomputed"
            if independent_reaudit_error is None
            else "legacy_artifact_only"
        ),
        "independent_reaudit_error": independent_reaudit_error,
        "independent_l1_operation_count": independent["l1_operation_count"],
        "independent_l2_operation_count": independent["l2_operation_count"],
        "independent_triplet_audit_publishable": (
            independent_triplet_audit_publishable
        ),
        "structural_audit_coverage": (
            "strict_structural_recomputed"
            if has_structural_operations
            else "not_applicable"
        ),
        "independent_structural_operation_count": structural_operation_count,
        "damaged_sha256": f"sha256:{damaged_hash}",
        "changeset_schema_version": changeset.get("schema_version"),
        **live_authority,
    }


def audit_repaired_operations(
    *,
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    damaged_model: Any | None = None,
    repaired_model: Any,
) -> dict[str, int]:
    """Recompute operation L1/L2 from the repaired IFC, not saved verdicts."""

    registry = create_default_registry()
    application_by_id = {
        str(item.get("operation_id")): item
        for item in application.get("operations", ())
        if isinstance(item, Mapping)
    }
    l1_count = 0
    l2_count = 0
    for operation in changeset.get("operations", ()):
        operation_id = str(operation.get("operation_id"))
        operation_type = str(operation.get("operation_type"))
        if operation_type in STRUCTURAL_OPERATION_TYPES:
            if damaged_model is None:
                raise ValueError(
                    f"independent structural audit missing damaged model: {operation_id}"
                )
            family = STRUCTURAL_FAMILY_BY_OPERATION[operation_type]
            occurrence_id = deterministic_global_id(operation, family)
            if _optional_guid(damaged_model, occurrence_id) is not None:
                raise ValueError(
                    f"l1.structural.product:{operation_id}:already_present_in_damaged"
                )
            occurrence = _optional_guid(repaired_model, occurrence_id)
            if occurrence is None or not occurrence.is_a(
                STRUCTURAL_OCCURRENCE_CLASS[family]
            ):
                raise ValueError(
                    f"l1.structural.product:{operation_id}:deterministic_occurrence_missing"
                )
            l1 = registry.dispatch(
                "comparison_adapter",
                operation,
                before_model=damaged_model,
                after_model=repaired_model,
                application={},
                role_mapping={family: occurrence_id},
            )
            checks = l1.get("l1_checks") if isinstance(l1, Mapping) else None
            if not isinstance(checks, Mapping):
                raise ValueError(
                    f"independent L1 failed: {operation_id}:not_evaluable"
                )
            failed_l1 = [
                check_id
                for check_id in STRUCTURAL_L1_CHECK_IDS
                if not isinstance(checks.get(check_id), Mapping)
                or checks[check_id].get("status") != "passed"
            ]
            if failed_l1 or l1.get("valid") is not True:
                detail = ",".join(failed_l1 or ("not_evaluable",))
                raise ValueError(f"independent L1 failed: {operation_id}:{detail}")
            l1_count += 1

            definition = registry.require(operation_type)
            policy = registry.require_evaluation_policy(operation_type)
            occurrence_role = _occurrence_role(definition)
            actual = extract_ifc_semantic_facts(
                occurrence,
                policy=policy,
                source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
                source_ref=occurrence_id,
                provenance=("independent-proof-audit", operation_id),
            )
            expected = _independent_expected_facts(
                registry=registry,
                operation=operation,
                changes={},
                actual=actual,
                occurrence_role=occurrence_role,
                repaired_model=repaired_model,
                allow_application_or_actual_fallback=False,
            )
            semantic_checks = registry.evaluate_semantics(
                operation_type,
                expected_facts=expected,
                repaired_facts=actual,
            )
            failed_l2 = [
                check
                for check in semantic_checks
                if check.mandatory and check.status.value != "passed"
            ]
            if failed_l2:
                detail = ",".join(
                    f"{item.check_id}:{item.status.value}" for item in failed_l2
                )
                raise ValueError(
                    f"independent L2 failed: {operation_id}:{detail}"
                )
            l2_count += 1
            continue

        applied = application_by_id.get(operation_id)
        if applied is None:
            raise ValueError(f"independent audit missing application: {operation_id}")
        changes = applied.get("changes")
        if not isinstance(changes, Mapping):
            raise ValueError(f"independent audit invalid application: {operation_id}")

        l1 = registry.dispatch(
            "postcondition_checker",
            operation,
            model=repaired_model,
            application=changes,
        )
        if not isinstance(l1, Mapping) or l1.get("valid") is not True:
            raise ValueError(f"independent L1 failed: {operation_id}")
        l1_count += 1

        definition = registry.require(str(operation.get("operation_type")))
        policy = registry.require_evaluation_policy(definition.operation_type)
        occurrence_role = _occurrence_role(definition)
        occurrence_id = _application_role_id(changes, occurrence_role)
        try:
            occurrence = repaired_model.by_guid(occurrence_id)
        except RuntimeError as error:
            raise ValueError(
                f"independent L2 occurrence missing: {operation_id}"
            ) from error
        actual = extract_ifc_semantic_facts(
            occurrence,
            policy=policy,
            source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
            source_ref=occurrence_id,
            provenance=("independent-proof-audit", operation_id),
        )
        expected = _independent_expected_facts(
            registry=registry,
            operation=operation,
            changes=changes,
            actual=actual,
            occurrence_role=occurrence_role,
            repaired_model=repaired_model,
        )
        checks = registry.evaluate_semantics(
            definition.operation_type,
            expected_facts=expected,
            repaired_facts=actual,
        )
        failed = [
            check
            for check in checks
            if check.mandatory and check.status.value != "passed"
        ]
        if failed:
            details = ",".join(
                f"{item.check_id}:{item.status.value}" for item in failed
            )
            raise ValueError(f"independent L2 failed: {operation_id}:{details}")
        l2_count += 1
    return {"l1_operation_count": l1_count, "l2_operation_count": l2_count}


def _occurrence_role(definition: Any) -> str:
    semantic_role = str(definition.evaluation_policy.semantic_role)
    if semantic_role not in definition.semantic_scope_roles:
        raise ValueError(
            f"independent audit occurrence role unresolved: {definition.operation_type}"
        )
    return semantic_role


def _application_role_id(changes: Mapping[str, Any], role: str) -> str:
    matches = [
        str(item.get("global_id"))
        for section in ("created", "modified")
        for item in changes.get(section, ())
        if isinstance(item, Mapping) and item.get("role") == role
    ]
    if len(matches) != 1:
        raise ValueError(f"independent audit role mapping invalid: {role}")
    return matches[0]


def _independent_expected_facts(
    *,
    registry: Any,
    operation: Mapping[str, Any],
    changes: Mapping[str, Any],
    actual: tuple[SemanticFact, ...],
    occurrence_role: str,
    repaired_model: Any,
    allow_application_or_actual_fallback: bool = True,
) -> tuple[SemanticFact, ...]:
    operation_id = str(operation["operation_id"])
    facts = list(
        registry.build_semantic_policy_facts(
            str(operation["operation_type"]), operation=operation
        )
    )
    actual_by_key = {fact.fact_key: fact for fact in actual}

    def add(
        fact_key: str,
        value: Any,
        *,
        value_type: str | None = None,
        unit: str | None = None,
        inherited: bool = False,
        scope: str | None = None,
    ) -> None:
        if value is None or any(item.fact_key == fact_key for item in facts):
            return
        observed = actual_by_key.get(fact_key)
        facts.append(
            SemanticFact(
                fact_key=fact_key,
                value=value,
                value_type=(
                    value_type
                    if value_type is not None
                    else None if observed is None else observed.value_type
                ),
                unit=(unit if unit is not None else None if observed is None else observed.unit),
                inherited=inherited,
                pset_path=(
                    fact_key.partition(":")[2]
                    if fact_key.startswith(("pset:", "quantity:"))
                    else None
                ),
                entity_source=f"independent-proof-audit:{operation_id}",
                source_kind=EvidenceSourceKind.DETERMINISTIC_POLICY,
                source_ref=f"changeset:/operations/{operation_id}",
                provenance=("independent-proof-audit", operation_id),
                occurrence_scope=scope or f"{occurrence_role}_occurrence",
                canonical_source_kind="deterministic_derived",
            )
        )

    for assignment in operation.get("semantic_assignments", ()):
        if not isinstance(assignment, Mapping):
            continue
        add(
            str(assignment.get("fact_key")),
            assignment.get("value"),
            value_type=str(assignment.get("value_type") or "") or None,
            unit=(
                None
                if assignment.get("unit") is None
                else str(assignment.get("unit"))
            ),
            inherited=assignment.get("ownership") == "type_inherited",
            scope=str(assignment.get("scope") or f"{occurrence_role}_occurrence"),
        )

    resolved = changes.get("resolved")
    resolved = resolved if isinstance(resolved, Mapping) else {}
    target = operation.get("target")
    target = target if isinstance(target, Mapping) else {}
    parameters = operation.get("parameters")
    parameters = parameters if isinstance(parameters, Mapping) else {}
    host_id = (
        parameters.get("host_wall_global_id")
        or target.get("wall_global_id")
        or _optional_application_role_id(changes, "host_wall")
    )
    add("relationship:host", host_id)
    expected_storey_id = resolved.get("storey_global_id")
    if expected_storey_id is None and host_id:
        try:
            host = repaired_model.by_guid(str(host_id))
        except RuntimeError:
            host = None
        if host is not None:
            storey = ifcopenshell.util.element.get_container(
                host, ifc_class="IfcBuildingStorey"
            )
            expected_storey_id = (
                None if storey is None else str(storey.GlobalId)
            )
    add("relationship:storey", expected_storey_id)
    add(
        "relationship:type",
        resolved.get(f"{occurrence_role}_type_global_id")
        or (
            _optional_application_role_id(changes, f"{occurrence_role}_type")
            if allow_application_or_actual_fallback
            else None
        )
        or (
            _optional_application_role_id(
                changes, f"generated_{occurrence_role}_type"
            )
            if allow_application_or_actual_fallback
            else None
        )
        or (
            None
            if not allow_application_or_actual_fallback
            or actual_by_key.get("relationship:type") is None
            else actual_by_key["relationship:type"].value
        ),
    )
    unique = {
        (fact.fact_key, repr(fact.value), fact.occurrence_scope): fact
        for fact in facts
    }
    return tuple(unique[key] for key in sorted(unique))


def _optional_application_role_id(
    changes: Mapping[str, Any], role: str
) -> str | None:
    matches = [
        str(item.get("global_id"))
        for section in ("created", "modified")
        for item in changes.get(section, ())
        if isinstance(item, Mapping) and item.get("role") == role
    ]
    return matches[0] if len(matches) == 1 else None


def _optional_guid(model: Any, global_id: str) -> Any | None:
    try:
        return model.by_guid(str(global_id))
    except RuntimeError:
        return None


def _is_existing_structural_property_operation(
    operation: Mapping[str, Any], *, damaged_model: Any
) -> bool:
    if str(operation.get("operation_type")) != "set_occurrence_properties":
        return False
    target = operation.get("target")
    target = target if isinstance(target, Mapping) else {}
    occurrence = _optional_guid(
        damaged_model, str(target.get("element_global_id") or "")
    )
    return occurrence is not None and occurrence.is_a() in {
        "IfcBeam",
        "IfcColumn",
    }


def _audit_structural_bound_changeset(
    *,
    roles: Mapping[str, Path],
    damaged_ifc_path: Path,
    changeset: Mapping[str, Any],
) -> None:
    request_path = roles.get("user_request")
    if request_path is None:
        raise ValueError("l0.structural.changeset-audit:user_request_missing")
    audit = audit_changeset(
        damaged_ifc_path=damaged_ifc_path,
        repair_request=_retained_request_text(request_path),
        changeset=changeset,
        registry=create_default_registry(),
    )
    if audit.get("valid") is not True:
        codes = sorted(
            str(issue.get("code") or "UNKNOWN")
            for issue in audit.get("issues", ())
            if isinstance(issue, Mapping)
        )
        raise ValueError(
            "l0.structural.changeset-audit:" + ",".join(codes or ["INVALID"])
        )


def _audit_structural_provenance_chain(
    *,
    case: Mapping[str, Any],
    roles: Mapping[str, Path],
    intent: Mapping[str, Any],
    changeset: Mapping[str, Any],
    damaged_sha256: str,
    damaged_ifc_path: Path,
    source_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    request_path = roles.get("user_request")
    resolution_path = roles.get("deterministic_target_resolution")
    if request_path is None or resolution_path is None:
        raise ValueError("l0.structural.provenance:request_or_resolution_missing")
    request_sha256 = "sha256:" + hashlib.sha256(
        _retained_request_text(request_path).encode("utf-8")
    ).hexdigest()
    damaged_prefixed = f"sha256:{damaged_sha256}"
    if (
        changeset.get("source_request_hash") != request_sha256
        or intent.get("source_request_hash") != request_sha256
        or _normalize_sha256(str(intent.get("model_fingerprint")))
        != damaged_sha256
        or _normalize_sha256(str(changeset.get("base_model_fingerprint")))
        != damaged_sha256
    ):
        raise ValueError("l0.structural.provenance:request_or_model_hash")

    bound_operations = {
        str(item["operation_id"]): item
        for item in changeset.get("operations", ())
        if isinstance(item, Mapping) and item.get("operation_id")
    }
    intent_identity = [
        (str(item.get("operation_id")), str(item.get("operation_type")))
        for item in intent.get("operations", ())
        if isinstance(item, Mapping)
    ]
    bound_identity = [
        (str(item.get("operation_id")), str(item.get("operation_type")))
        for item in changeset.get("operations", ())
        if isinstance(item, Mapping)
    ]
    if intent_identity != bound_identity:
        raise ValueError("l0.structural.provenance:intent_operation_identity")
    if len(bound_operations) != len(bound_identity):
        raise ValueError("l0.structural.provenance:duplicate_operation_identity")
    intent_operations = {
        str(item["operation_id"]): item
        for item in intent.get("operations", ())
        if isinstance(item, Mapping) and item.get("operation_id")
    }
    registry = create_default_registry()
    for operation_id, operation in intent_operations.items():
        operation_type = str(operation.get("operation_type"))
        if operation_type not in STRUCTURAL_OPERATION_TYPES:
            continue
        family = STRUCTURAL_FAMILY_BY_OPERATION[operation_type]
        routing = operation.get("routing_intent")
        routing = routing if isinstance(routing, Mapping) else {}
        expected_profile_id = _profile_id_for_intent_schema(
            operation_type,
            intent_schema_version=str(intent.get("schema_version") or ""),
        )
        if (
            routing.get("component_family") != family
            or routing.get("action") != "add"
            or routing.get("operation_profile") != expected_profile_id
        ):
            raise ValueError(
                f"l0.structural.provenance:routing_binding:{operation_id}"
            )

    resolution = _read_json(resolution_path)
    if (
        _normalize_sha256(str(resolution.get("source_ifc_sha256")))
        != damaged_sha256
        or _normalize_sha256(str(resolution.get("model_fingerprint")))
        != damaged_sha256
    ):
        raise ValueError("l0.structural.provenance:resolution_model_hash")
    resolved_identity = [
        (str(item.get("operation_id")), str(item.get("operation_type")))
        for item in resolution.get("operations", ())
        if isinstance(item, Mapping)
    ]
    if resolution.get("status") != "resolved" or resolved_identity != bound_identity:
        raise ValueError("l0.structural.provenance:resolution_operation_identity")
    for resolved in resolution.get("operations", ()):
        if not isinstance(resolved, Mapping):
            continue
        bound = bound_operations.get(str(resolved.get("operation_id")))
        if bound is None:
            raise ValueError("l0.structural.provenance:resolution_binding")
        if str(bound.get("operation_type")) in STRUCTURAL_OPERATION_TYPES:
            source_intent = intent_operations.get(str(resolved.get("operation_id")))
            if source_intent is None:
                raise ValueError("l0.structural.provenance:intent_operation_identity")
            target = bound.get("target")
            target = target if isinstance(target, Mapping) else {}
            target_query = source_intent.get("target_query")
            target_query = target_query if isinstance(target_query, Mapping) else {}
            explicit_target = target_query.get("global_id")
            if (
                str(resolved.get("target_global_id"))
                != str(target.get("storey_global_id"))
                or resolved.get("parameters") != bound.get("parameters")
                or source_intent.get("parameters") != bound.get("parameters")
                or (
                    explicit_target is not None
                    and str(explicit_target) != str(target.get("storey_global_id"))
                )
            ):
                raise ValueError("l0.structural.provenance:resolution_binding")

    manifest_ref = str(changeset.get("semantic_manifest_ref") or "")
    manifest_matches = [path for path in roles.values() if path.name == manifest_ref]
    if len(manifest_matches) != 1:
        raise ValueError("l0.structural.provenance:semantic_manifest_missing")
    manifest_path = manifest_matches[0]
    bundle = _read_json(manifest_path)
    if (
        _normalize_sha256(str(changeset.get("semantic_manifest_sha256")))
        != _canonical_document_sha256(bundle)
    ):
        raise ValueError("l0.structural.provenance:semantic_manifest_hash")
    raw_manifests = bundle.get("manifests")
    if isinstance(raw_manifests, list):
        manifest_documents = raw_manifests
    elif bundle.get("operation_id"):
        manifest_documents = [bundle]
    else:
        manifest_documents = []
    manifests = {
        str(item.get("operation_id")): item
        for item in manifest_documents
        if isinstance(item, Mapping) and item.get("operation_id")
    }
    for operation_id, operation in bound_operations.items():
        if str(operation.get("operation_type")) not in STRUCTURAL_OPERATION_TYPES:
            continue
        manifest = manifests.get(operation_id)
        reference = operation.get("semantic_manifest")
        reference = reference if isinstance(reference, Mapping) else {}
        if (
            manifest is None
            or manifest.get("operation_type") != operation.get("operation_type")
            or manifest.get("manifest_id") != reference.get("manifest_id")
            or manifest.get("base_model_fingerprint") != damaged_prefixed
            or manifest.get("assignments") != operation.get("semantic_assignments")
        ):
            raise ValueError("l0.structural.provenance:semantic_manifest_binding")

    property_authority = _audit_structural_authority_replay(
        damaged_ifc_path=damaged_ifc_path,
        damaged_sha256=damaged_sha256,
        intent=intent,
        changeset=changeset,
        retained_resolution=resolution,
        retained_manifest=bundle,
        roles=roles,
        provider_evidence_mode=str(case.get("provider_evidence_mode") or ""),
    )

    evidence_mode = str(case.get("provider_evidence_mode") or "")
    source_evidence_mode = str(
        source_manifest.get("provider_evidence_mode") or ""
    )
    if source_evidence_mode != evidence_mode:
        raise ValueError(
            "l0.structural.provenance:provider_evidence_mode_binding"
        )
    if evidence_mode == "offline_bound_deterministic":
        return property_authority
    if evidence_mode != "live":
        raise ValueError("l0.structural.provenance:provider_evidence_mode")
    return {
        **property_authority,
        **_audit_live_transcript_authority(
            case=case,
            roles=roles,
            source_manifest=source_manifest,
            intent=intent,
            changeset=changeset,
        ),
    }


class _RetainedStage15PropertyResolver:
    """Recompute current admissibility from retained public evidence only."""

    def __init__(
        self,
        *,
        case_root: Path,
        roles: Mapping[str, Path],
        provider_evidence_mode: str,
    ) -> None:
        self.case_root = case_root
        self.artifacts = {path.resolve() for path in roles.values()}
        self.provider_evidence_mode = provider_evidence_mode
        self.registry = load_ifc2x3_registry(ROOT)
        self.records = build_standard_property_records(
            self.registry,
            corpus_fingerprint=default_standard_corpus_fingerprint(),
        )
        self.policy = _read_json(
            ROOT
            / "schemas/ifc/knowledge/property_resolution_policy.v0.2.json"
        )
        self.recomputed_claim_count = 0

    def resolve(self, query: Any) -> PropertyResolutionDecision:
        del query
        raise ValueError("l0.structural.provenance:property_claim_binding")

    def resolve_for_claim(
        self,
        *,
        operation_id: str,
        operation_type: str,
        claim_id: str,
        claim: NaturalLanguagePropertyIntent,
        query: Any,
    ) -> PropertyResolutionDecision:
        query_path, query_document = self._query_for_claim(
            operation_id=operation_id,
            operation_type=operation_type,
            claim_id=claim_id,
        )
        if (
            query_document.get("target_ifc_class") != query.target_ifc_class
            or query_document.get("property_phrase") != claim.property_phrase
            or query_document.get("raw_value") != claim.raw_value
            or query_document.get("raw_unit") != claim.raw_unit
            or query_document.get("scope") != claim.scope
        ):
            raise ValueError(
                "l0.structural.provenance:property_query_claim_binding"
            )
        claim_root = query_path.parent
        candidate_path = self._require_listed(claim_root / "candidate-set.json")
        candidate_set = _read_json(candidate_path)
        decision, trace = self._provider_decision(
            claim_root=claim_root,
            operation_id=operation_id,
            claim_id=claim_id,
        )
        user_result_path = claim_root / "decision-result-user.json"
        if user_result_path.resolve() in self.artifacts:
            provider_admission_path = self._require_listed(
                claim_root / "admissibility-provider.json"
            )
            provider_admission = admit_property_decision(
                query=query_document,
                candidate_set=candidate_set,
                decision=decision,
                decision_trace=trace,
                policy=self.policy,
                records=self.records,
                registry=self.registry,
                claim=claim,
                project_length_unit=query.project_length_unit,
            )
            if (
                provider_admission.status != "clarification_required"
                or provider_admission.exact_intent is not None
                or provider_admission.to_dict()
                != _read_json(provider_admission_path)
            ):
                raise ValueError(
                    "l0.structural.provenance:property_provider_clarification_replay"
                )
            provider_conflicts = decision.get("conflicting_candidate_ids")
            decision, trace = self._user_decision(
                claim_root=claim_root,
                operation_id=operation_id,
                claim_id=claim_id,
                query_document=query_document,
                candidate_set=candidate_set,
                provider_conflicts=provider_conflicts,
            )
            admission_names = ("admissibility-user.json",)
            exact_names = ("exact-intent-user.json",)
        else:
            admission_names = (
                "admissibility-provider.json",
                "admissibility.json",
            )
            exact_names = ("exact-intent-provider.json", "exact-intent.json")
        admission_path = self._one_existing_listed(
            claim_root,
            admission_names,
            "property_admissibility_missing",
        )
        retained_admission = _read_json(admission_path)
        admission = admit_property_decision(
            query=query_document,
            candidate_set=candidate_set,
            decision=decision,
            decision_trace=trace,
            policy=self.policy,
            records=self.records,
            registry=self.registry,
            claim=claim,
            project_length_unit=query.project_length_unit,
        )
        if (
            admission.status != "passed"
            or admission.exact_intent is None
            or admission.to_dict() != retained_admission
        ):
            raise ValueError(
                "l0.structural.provenance:property_admissibility_replay"
            )
        exact_paths = [
            path
            for name in exact_names
            if (path := claim_root / name).resolve() in self.artifacts
        ]
        if len(exact_paths) > 1:
            raise ValueError(
                "l0.structural.provenance:property_exact_intent_duplicate"
            )
        if exact_paths and _read_json(exact_paths[0]) != admission.exact_intent.to_dict():
            raise ValueError(
                "l0.structural.provenance:property_exact_intent_replay"
            )
        exact = admission.exact_intent
        self.recomputed_claim_count += 1
        return PropertyResolutionDecision(
            status="standard_resolved",
            reason_code=CURRENT_STAGE_1_5_REASON,
            exact_intent=ResolvedExactProperty(
                set_name=exact.set_name,
                property_name=exact.property_name,
                value=exact.value,
                requested_value_type=exact.requested_value_type,
                requested_unit=exact.requested_unit,
                scope=exact.scope,
            ),
            # Candidate observability is retained separately. It is not an
            # executable authority and is deliberately not hash-gated here.
            candidates=(),
        )

    def _user_decision(
        self,
        *,
        claim_root: Path,
        operation_id: str,
        claim_id: str,
        query_document: Mapping[str, Any],
        candidate_set: Mapping[str, Any],
        provider_conflicts: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        result = _read_json(
            self._require_listed(claim_root / "decision-result-user.json")
        )
        decision = result.get("decision")
        trace = result.get("trace")
        if not isinstance(decision, dict) or not isinstance(trace, dict):
            raise ValueError(
                "l0.structural.provenance:property_user_decision_binding"
            )
        selected = str(decision.get("selected_candidate_id") or "")
        offered = {
            str(item.get("candidate_id") or "")
            for item in candidate_set.get("candidates", ())
            if isinstance(item, Mapping)
        }
        conflicts = {
            str(item) for item in provider_conflicts
        } if isinstance(provider_conflicts, list) else set()
        if (
            result.get("valid") is not True
            or result.get("classification") != "confirmed"
            or result.get("evidence_class") != "public_user_answer"
            or result.get("acceptance_eligible") is not False
            or result.get("attempts") != []
            or decision.get("decision") != "confirmed"
            or not selected
            or selected not in offered
            or selected not in conflicts
            or decision.get("conflicting_candidate_ids") != []
            or decision.get("clarification_question") is not None
            or trace.get("status") != "valid"
            or trace.get("evidence_class") != "public_user_answer"
            or trace.get("operation_id") != operation_id
            or trace.get("claim_id") != claim_id
            or trace.get("query_id") != query_document.get("query_id")
            or trace.get("candidate_set_id")
            != candidate_set.get("candidate_set_id")
        ):
            raise ValueError(
                "l0.structural.provenance:property_user_decision_binding"
            )
        self._validate_user_answer_transition(
            operation_id=operation_id,
            claim_id=claim_id,
            selected_candidate_id=selected,
        )
        return decision, trace

    def _validate_user_answer_transition(
        self,
        *,
        operation_id: str,
        claim_id: str,
        selected_candidate_id: str,
    ) -> None:
        state_paths = [
            path for path in self.artifacts if path.name == "state.json"
        ]
        if len(state_paths) != 1:
            raise ValueError(
                "l0.structural.provenance:property_user_answer_binding"
            )
        transitions = _read_json(state_paths[0]).get("transitions")
        if not isinstance(transitions, list):
            raise ValueError(
                "l0.structural.provenance:property_user_answer_binding"
            )
        clarifications = [
            item.get("clarification")
            for item in transitions
            if isinstance(item, Mapping)
            and isinstance(item.get("clarification"), Mapping)
            and item["clarification"].get("reason_code")
            == "property_resolution"
            and item["clarification"].get("operation_id") == operation_id
            and item["clarification"].get("claim_id") == claim_id
        ]
        answers = [
            item.get("answer")
            for item in transitions
            if isinstance(item, Mapping)
            and item.get("from_stage") == "clarification_required"
            and isinstance(item.get("answer"), Mapping)
            and item["answer"].get("kind") == "select_candidate"
            and item["answer"].get("candidate_token")
            == selected_candidate_id
        ]
        offered_tokens = {
            str(candidate.get("token") or "")
            for clarification in clarifications
            for candidate in clarification.get("candidates", ())
            if isinstance(candidate, Mapping)
        }
        if (
            len(clarifications) != 1
            or len(answers) != 1
            or selected_candidate_id not in offered_tokens
        ):
            raise ValueError(
                "l0.structural.provenance:property_user_answer_binding"
            )

    def _query_for_claim(
        self,
        *,
        operation_id: str,
        operation_type: str,
        claim_id: str,
    ) -> tuple[Path, dict[str, Any]]:
        matches: list[tuple[Path, dict[str, Any]]] = []
        for path in self.artifacts:
            if path.name != "query.json":
                continue
            try:
                relative = path.relative_to(self.case_root)
            except ValueError:
                continue
            if "property-resolution" not in relative.parts:
                continue
            document = _read_json(path)
            if (
                document.get("operation_id") == operation_id
                and document.get("operation_type") == operation_type
                and document.get("claim_id") == claim_id
            ):
                matches.append((path, document))
        if len(matches) != 1:
            raise ValueError(
                "l0.structural.provenance:property_evidence_group"
            )
        return matches[0]

    def _provider_decision(
        self,
        *,
        claim_root: Path,
        operation_id: str,
        claim_id: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        valid_attempts: list[tuple[Path, dict[str, Any]]] = []
        for path in self.artifacts:
            if path.name != "trace.json" or claim_root not in path.parents:
                continue
            trace = _read_json(path)
            if (
                trace.get("operation_id") == operation_id
                and trace.get("claim_id") == claim_id
                and trace.get("status") == "valid"
            ):
                valid_attempts.append((path, trace))
        if len(valid_attempts) != 1:
            raise ValueError(
                "l0.structural.provenance:property_provider_decision"
            )
        trace_path, trace = valid_attempts[0]
        for name in (
            "parsed-response.json",
            "provider-metadata.json",
            "raw-response.json",
            "rendered-prompt.txt",
            "renderer-input.json",
            "trace.json",
            "validation-feedback.json",
        ):
            self._require_listed(trace_path.parent / name)
        if self.provider_evidence_mode == "live":
            if (
                trace.get("evidence_class") != "live"
                or trace.get("acceptance_eligible") is not True
            ):
                raise ValueError(
                    "l0.structural.provenance:property_live_evidence"
                )
        elif self.provider_evidence_mode == "offline_bound_deterministic":
            if trace.get("evidence_class") != "injected_offline":
                raise ValueError(
                    "l0.structural.provenance:property_offline_evidence"
                )
        else:
            raise ValueError(
                "l0.structural.provenance:property_evidence_mode"
            )
        decision = _read_json(trace_path.parent / "parsed-response.json")
        result_path = claim_root / "decision-result-provider.json"
        if result_path.resolve() in self.artifacts:
            result = _read_json(result_path)
            if (
                result.get("valid") is not True
                or result.get("decision") != decision
                or result.get("trace") != trace
            ):
                raise ValueError(
                    "l0.structural.provenance:property_decision_result_binding"
                )
        return decision, trace

    def _require_listed(self, path: Path) -> Path:
        resolved = path.resolve()
        if resolved not in self.artifacts or not resolved.is_file():
            raise ValueError(
                "l0.structural.provenance:property_evidence_group"
            )
        return resolved

    def _one_existing_listed(
        self,
        root: Path,
        names: tuple[str, ...],
        reason: str,
    ) -> Path:
        matches = [
            path.resolve()
            for name in names
            if (path := root / name).resolve() in self.artifacts
        ]
        if len(matches) != 1:
            raise ValueError(f"l0.structural.provenance:{reason}")
        return matches[0]


def _natural_property_claim_count(intent: Mapping[str, Any]) -> int:
    return sum(
        1
        for operation in intent.get("operations", ())
        if isinstance(operation, Mapping)
        for claim in operation.get("property_intents", ())
        if isinstance(claim, Mapping)
        and claim.get("intent_kind") == "natural_language_property"
    )


def _unrecomputed_property_authority(
    *,
    intent: Mapping[str, Any] | None,
    roles: Mapping[str, Path],
) -> dict[str, Any]:
    """Classify cases that have not passed strict Stage 1.5 replay."""

    property_claim_count = _natural_property_claim_count(intent or {})
    reason_codes: set[str] = set()
    if property_claim_count:
        resolution_path = roles.get("deterministic_target_resolution")
        if resolution_path is not None:
            retained_resolution = _read_json(resolution_path)
            reason_codes = {
                str(item.get("decision", {}).get("reason_code") or "")
                for item in retained_resolution.get("property_resolutions", ())
                if isinstance(item, Mapping)
                and isinstance(item.get("decision"), Mapping)
                and item.get("decision", {}).get("reason_code")
            }
    return {
        "property_authority_coverage": (
            "historical_property_artifact_only"
            if property_claim_count
            else "not_applicable"
        ),
        "property_claim_count": property_claim_count,
        "property_reason_codes": sorted(reason_codes),
        "historical_alias_present": HISTORICAL_ALIAS_REASON in reason_codes,
        "current_property_acceptance_eligible": property_claim_count == 0,
    }


def _without_property_candidate_observability(
    document: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = json.loads(json.dumps(dict(document), ensure_ascii=False))
    for resolution in normalized.get("property_resolutions", ()):
        if isinstance(resolution, dict):
            resolution["candidates"] = []
    return normalized


def _audit_structural_authority_replay(
    *,
    damaged_ifc_path: Path,
    damaged_sha256: str,
    intent: Mapping[str, Any],
    changeset: Mapping[str, Any],
    retained_resolution: Mapping[str, Any],
    retained_manifest: Mapping[str, Any],
    roles: Mapping[str, Path],
    provider_evidence_mode: str,
) -> dict[str, Any]:
    registry = create_default_registry()
    parsed_intent = RepairIntent.from_dict(
        dict(intent),
        registry=registry,
        require_complete=False,
    )
    property_claim_count = _natural_property_claim_count(intent)
    retained_property_resolutions = [
        item
        for item in retained_resolution.get("property_resolutions", ())
        if isinstance(item, Mapping)
    ]
    reason_codes = {
        str(item.get("decision", {}).get("reason_code") or "")
        for item in retained_property_resolutions
        if isinstance(item.get("decision"), Mapping)
    }
    if property_claim_count and reason_codes != {CURRENT_STAGE_1_5_REASON}:
        if CURRENT_STAGE_1_5_REASON in reason_codes:
            raise ValueError(
                "l0.structural.provenance:mixed_property_authority"
            )
        return {
            "property_authority_coverage": "historical_property_artifact_only",
            "property_claim_count": property_claim_count,
            "property_reason_codes": sorted(reason_codes),
            "historical_alias_present": HISTORICAL_ALIAS_REASON in reason_codes,
            "current_property_acceptance_eligible": False,
        }
    if len(retained_property_resolutions) != property_claim_count:
        raise ValueError(
            "l0.structural.provenance:property_resolution_count"
        )
    property_resolver = None
    if property_claim_count:
        property_resolver = _RetainedStage15PropertyResolver(
            case_root=roles["source_run_manifest"].parent,
            roles=roles,
            provider_evidence_mode=provider_evidence_mode,
        )
    with tempfile.TemporaryDirectory(prefix="phase12-proof-authority-") as tmp:
        index_path = Path(tmp) / "independent-index.sqlite"
        metadata = build_ifc_index(damaged_ifc_path, index_path)
        if _normalize_sha256(str(metadata.source_ifc_sha256)) != damaged_sha256:
            raise ValueError("l0.structural.provenance:replay_index_hash")
        with SQLiteIndexRepository.open(index_path) as repository:
            replayed = resolve_repair_intent(
                parsed_intent,
                repository,
                expected_source_sha256=metadata.source_ifc_sha256,
                operation_registry=registry,
                property_knowledge_resolver=property_resolver,
            )
            records = {
                item.ifc_global_id: item for item in repository.iter_records()
            }
            type_records = {
                item.ifc_global_id: item
                for item in repository.iter_type_records()
            }
    if replayed.status != "resolved" or _without_property_candidate_observability(
        replayed.to_dict()
    ) != _without_property_candidate_observability(retained_resolution):
        raise ValueError("l0.structural.provenance:resolution_replay")
    if (
        property_resolver is not None
        and property_resolver.recomputed_claim_count != property_claim_count
    ):
        raise ValueError(
            "l0.structural.provenance:property_replay_count"
        )

    bound_operations = {
        str(item.get("operation_id")): item
        for item in changeset.get("operations", ())
        if isinstance(item, Mapping) and item.get("operation_id")
    }
    operation_headers = {
        "operations": [
            {
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
            }
            for operation in replayed.operations
        ]
    }
    policy_facts: dict[str, tuple[Any, ...]] = {}
    verified_absence: dict[str, tuple[str, ...]] = {}
    for operation in replayed.operations:
        bound_operation = bound_operations.get(operation.operation_id)
        if not isinstance(bound_operation, Mapping):
            raise ValueError("l0.structural.provenance:changeset_replay_binding")
        if (
            bound_operation.get("operation_type") != operation.operation_type
            or bound_operation.get("parameters")
            != operation.to_dict()["parameters"]
            or _bound_target_global_id(bound_operation)
            != str(operation.target_global_id)
        ):
            raise ValueError("l0.structural.provenance:changeset_replay_binding")
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
        intent=parsed_intent,
        resolution=replayed,
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
            base_model_fingerprint=f"sha256:{damaged_sha256}",
        )
        for operation_id in sorted(evidence.operation_types)
        if evidence.operation_types[operation_id] in STRUCTURAL_OPERATION_TYPES
    )
    documents = [semantic_manifest_to_dict(item) for item in manifests]
    raw_retained = retained_manifest.get("manifests")
    retained_documents = (
        list(raw_retained)
        if isinstance(raw_retained, list)
        else [retained_manifest]
    )
    retained_by_operation = {
        str(item.get("operation_id")): item
        for item in retained_documents
        if isinstance(item, Mapping) and item.get("operation_id")
    }
    if set(retained_by_operation) != set(bound_operations):
        raise ValueError("l0.structural.provenance:semantic_manifest_operation_set")
    if any(
        retained_by_operation.get(str(document.get("operation_id"))) != document
        for document in documents
    ):
        raise ValueError("l0.structural.provenance:semantic_authority_replay")
    return {
        "property_authority_coverage": (
            "strict_stage_1_5_recomputed"
            if property_claim_count
            else "not_applicable"
        ),
        "property_claim_count": property_claim_count,
        "property_reason_codes": sorted(reason_codes),
        "historical_alias_present": False,
        "current_property_acceptance_eligible": True,
    }


def _bound_target_global_id(operation: Mapping[str, Any]) -> str:
    operation_type = str(operation.get("operation_type") or "")
    field = {
        "add_beam": "storey_global_id",
        "add_column": "storey_global_id",
        "add_window_with_opening_to_wall": "wall_global_id",
        "add_opening_to_wall": "wall_global_id",
        "add_door_with_opening_to_wall": "wall_global_id",
        "fill_existing_opening_with_door": "opening_global_id",
    }.get(operation_type)
    target = operation.get("target")
    target = target if isinstance(target, Mapping) else {}
    return "" if field is None else str(target.get(field) or "")


def _retained_request_text(path: Path) -> str:
    """Decode the runner's canonical text artifact back to its hashed value."""

    return path.read_text(encoding="utf-8").rstrip()


def _canonical_document_sha256(value: Any) -> str:
    canonical = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _structural_operations(
    changeset: Mapping[str, Any],
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        operation
        for operation in changeset.get("operations", ())
        if isinstance(operation, Mapping)
        and str(operation.get("operation_type")) in STRUCTURAL_OPERATION_TYPES
    )


def _audit_structural_type_and_semantic_authority(
    *,
    changeset: Mapping[str, Any],
    damaged_model: Any,
    repaired_model: Any,
) -> None:
    registry = create_default_registry()
    for operation in _structural_operations(changeset):
        operation_id = str(operation["operation_id"])
        operation_type = str(operation["operation_type"])
        family = STRUCTURAL_FAMILY_BY_OPERATION[operation_type]
        occurrence_id = deterministic_global_id(operation, family)
        occurrence = _optional_guid(repaired_model, occurrence_id)
        if occurrence is None:
            raise ValueError(
                f"l1.structural.product:{operation_id}:occurrence_missing"
            )
        type_assignments = [
            assignment
            for assignment in operation.get("semantic_assignments", ())
            if isinstance(assignment, Mapping)
            and assignment.get("fact_key") == "relationship:type"
        ]
        if len(type_assignments) != 1:
            raise ValueError(
                f"l1.structural.relationships:{operation_id}:type_assignment_count"
            )
        assignment = type_assignments[0]
        expected_type_id = str(assignment.get("value") or "")
        expected_type_class = STRUCTURAL_TYPE_CLASS[family]
        if (
            not expected_type_id
            or assignment.get("value_type") != expected_type_class
            or assignment.get("ownership") != "type_inherited"
            or assignment.get("scope") != f"{family}_occurrence"
        ):
            raise ValueError(
                f"l2.structural.type-authority:{operation_id}:assignment_contract"
            )
        repaired_type = _optional_guid(repaired_model, expected_type_id)
        if repaired_type is None or not repaired_type.is_a(expected_type_class):
            raise ValueError(
                f"l2.structural.type-authority:{operation_id}:type_missing_or_class"
            )
        damaged_type = _optional_guid(damaged_model, expected_type_id)
        if damaged_type is not None:
            if not damaged_type.is_a(expected_type_class):
                raise ValueError(
                    f"l2.structural.type-authority:{operation_id}:reused_type_class"
                )
            if type_authority_fingerprint(damaged_type) != type_authority_fingerprint(
                repaired_type
            ):
                raise ValueError(
                    f"l2.structural.type-authority:{operation_id}:reused_type_fingerprint"
                )
        else:
            _audit_generated_structural_type(
                family=family,
                operation=operation,
                assignment=assignment,
                repaired_type=repaired_type,
            )

        policy = registry.require_evaluation_policy(operation_type)
        actual = extract_ifc_semantic_facts(
            occurrence,
            policy=policy,
            source_kind=EvidenceSourceKind.REPAIRED_OUTPUT,
            source_ref=occurrence_id,
            provenance=("independent-proof-authority", operation_id),
        )
        requested_direct = {
            (str(item.get("fact_key")), str(item.get("scope")))
            for item in operation.get("semantic_assignments", ())
            if isinstance(item, Mapping)
            and item.get("ownership") == "occurrence_direct"
            and str(item.get("fact_key", "")).startswith(("pset:", "material:"))
        }
        actual_direct = {
            # The fact is extracted from the independently identified member;
            # bind its physical scope here instead of inheriting the legacy
            # SemanticFact default ("window_occurrence").
            (fact.fact_key, f"{family}_occurrence")
            for fact in actual
            if not fact.inherited
            and fact.fact_key.startswith(("pset:", "material:"))
        }
        direct_quantities = {
            (
                f"quantity:{fact.set_name}.{fact.property_name}",
                f"{family}_occurrence",
            )
            for fact in extract_property_facts(occurrence)
            if fact.set_kind == "quantity" and not fact.inherited
        }
        requested_quantities = {
            (str(item.get("fact_key")), str(item.get("scope")))
            for item in operation.get("semantic_assignments", ())
            if isinstance(item, Mapping)
            and item.get("ownership") == "occurrence_direct"
            and str(item.get("fact_key", "")).startswith("quantity:")
        }
        _audit_structural_direct_relationships(
            occurrence=occurrence,
            operation=operation,
            family=family,
        )
        if actual_direct != requested_direct or direct_quantities != requested_quantities:
            raise ValueError(
                f"l2.structural.semantic-scope:{operation_id}:direct_fact_set:"
                f"expected={sorted(requested_direct | requested_quantities)}:"
                f"actual={sorted(actual_direct | direct_quantities)}"
            )


def _audit_structural_direct_relationships(
    *,
    occurrence: Any,
    operation: Mapping[str, Any],
    family: str,
) -> None:
    operation_id = str(operation["operation_id"])
    scope = f"{family}_occurrence"
    direct_assignments = [
        item
        for item in operation.get("semantic_assignments", ())
        if isinstance(item, Mapping)
        and item.get("ownership") == "occurrence_direct"
        and item.get("scope") == scope
    ]
    expected_psets: dict[str, set[str]] = {}
    expected_quantities: dict[str, set[str]] = {}
    expected_material_groups: set[tuple[str, str]] = set()
    for assignment in direct_assignments:
        fact_key = str(assignment.get("fact_key") or "")
        if fact_key.startswith("pset:"):
            set_name, separator, property_name = fact_key.removeprefix(
                "pset:"
            ).partition(".")
            if not separator or not set_name or not property_name:
                raise ValueError(
                    f"l2.structural.semantic-scope:{operation_id}:pset_key"
                )
            expected_psets.setdefault(set_name, set()).add(property_name)
        elif fact_key.startswith("quantity:"):
            set_name, separator, quantity_name = fact_key.removeprefix(
                "quantity:"
            ).partition(".")
            if not separator or not set_name or not quantity_name:
                raise ValueError(
                    f"l2.structural.semantic-scope:{operation_id}:quantity_key"
                )
            expected_quantities.setdefault(set_name, set()).add(quantity_name)
        elif fact_key.startswith("material:"):
            expected_material_groups.add(
                (
                    str(assignment.get("authoring_action") or ""),
                    str(assignment.get("source_ref") or ""),
                )
            )

    property_relations = [
        relation
        for relation in getattr(occurrence, "IsDefinedBy", ())
        if relation.is_a("IfcRelDefinesByProperties")
    ]
    seen_psets: set[str] = set()
    seen_quantities: set[str] = set()
    for relation in property_relations:
        if tuple(relation.RelatedObjects) != (occurrence,):
            raise ValueError(
                f"l2.structural.semantic-scope:{operation_id}:shared_direct_relation"
            )
        definition = relation.RelatingPropertyDefinition
        name = str(getattr(definition, "Name", "") or "")
        if definition.is_a("IfcPropertySet"):
            if name in seen_psets or name not in expected_psets:
                raise ValueError(
                    f"l2.structural.semantic-scope:{operation_id}:pset_cardinality"
                )
            names = [str(item.Name) for item in definition.HasProperties]
            if len(names) != len(set(names)) or set(names) != expected_psets[name]:
                raise ValueError(
                    f"l2.structural.semantic-scope:{operation_id}:pset_members"
                )
            seen_psets.add(name)
        elif definition.is_a("IfcElementQuantity"):
            if name in seen_quantities or name not in expected_quantities:
                raise ValueError(
                    f"l2.structural.semantic-scope:{operation_id}:quantity_cardinality"
                )
            names = [str(item.Name) for item in definition.Quantities]
            if len(names) != len(set(names)) or set(names) != expected_quantities[name]:
                raise ValueError(
                    f"l2.structural.semantic-scope:{operation_id}:quantity_members"
                )
            seen_quantities.add(name)
        else:
            raise ValueError(
                f"l2.structural.semantic-scope:{operation_id}:definition_class"
            )
    if seen_psets != set(expected_psets) or seen_quantities != set(
        expected_quantities
    ):
        raise ValueError(
            f"l2.structural.semantic-scope:{operation_id}:direct_relation_cardinality"
        )

    associations = list(getattr(occurrence, "HasAssociations", ()))
    material_relations = [
        relation
        for relation in associations
        if relation.is_a("IfcRelAssociatesMaterial")
    ]
    if len(material_relations) != len(expected_material_groups) or len(
        material_relations
    ) != len(associations):
        raise ValueError(
            f"l2.structural.semantic-scope:{operation_id}:material_cardinality"
        )
    if any(tuple(relation.RelatedObjects) != (occurrence,) for relation in material_relations):
        raise ValueError(
            f"l2.structural.semantic-scope:{operation_id}:shared_material_relation"
        )


def _audit_generated_structural_type(
    *,
    family: str,
    operation: Mapping[str, Any],
    assignment: Mapping[str, Any],
    repaired_type: Any,
) -> None:
    operation_id = str(operation["operation_id"])
    if assignment.get("source_kind") not in {
        "deterministic_derived",
        "deterministic_policy",
    }:
        raise ValueError(
            f"l2.structural.type-authority:{operation_id}:generated_source"
        )
    derivation = assignment.get("derivation")
    if not isinstance(derivation, Mapping):
        raise ValueError(
            f"l2.structural.type-authority:{operation_id}:derivation_missing"
        )
    expected_type_class = STRUCTURAL_TYPE_CLASS[family]
    expected_template_id = f"text2ifc-rectangular-{family}-type"
    template_version = str(derivation.get("template_version") or "")
    formal = derivation.get("formal_attributes")
    template = derivation.get("template")
    if (
        derivation.get("ifc_class") != expected_type_class
        or derivation.get("template_id") != expected_template_id
        or template_version != "0.1"
        or not isinstance(formal, Mapping)
        or dict(formal)
        or not isinstance(template, Mapping)
    ):
        raise ValueError(
            f"l2.structural.type-authority:{operation_id}:derivation_contract"
        )
    digest = hash_json(
        {
            "template_id": expected_template_id,
            "template_version": template_version,
            "ifc_class": expected_type_class,
            "formal_attributes": dict(formal),
            "template": dict(template),
        }
    )
    if derivation.get("template_digest") != digest:
        raise ValueError(
            f"l2.structural.type-authority:{operation_id}:template_digest"
        )
    raw_section = operation.get("parameters", {}).get("section", {})
    dimension_keys = (
        ("width_mm", "height_mm")
        if family == "beam"
        else ("width_mm", "depth_mm")
    )
    section = {
        "shape": "rectangle",
        **{key: float(raw_section[key]) for key in dimension_keys},
    }
    expected_template = {
        "name": f"Text2IFC generated {family} type {operation_id}",
        "predefined_type": "NOTDEFINED",
        "section": section,
        "section_digest": hash_json(
            {"ifc_class": expected_type_class, "section": section}
        ),
    }
    if dict(template) != expected_template:
        raise ValueError(
            f"l2.structural.type-authority:{operation_id}:template_contract"
        )
    expected_name = str(expected_template["name"])
    actual_attributes = {
        "Name": getattr(repaired_type, "Name", None),
        "Description": getattr(repaired_type, "Description", None),
        "ElementType": getattr(repaired_type, "ElementType", None),
        "PredefinedType": getattr(repaired_type, "PredefinedType", None),
    }
    expected_attributes = {
        "Name": expected_name,
        "Description": f"{expected_template_id}/{template_version}",
        "ElementType": expected_name,
        "PredefinedType": "NOTDEFINED",
    }
    if actual_attributes != expected_attributes:
        raise ValueError(
            f"l2.structural.type-authority:{operation_id}:formal_attributes"
        )


def _audit_structural_production_isolation(
    *,
    roles: Mapping[str, Path],
    damaged_sha256: str,
    changeset: Mapping[str, Any],
    operation_count: int,
) -> None:
    boundary_path = roles.get("production_input_boundary")
    if boundary_path is None:
        raise ValueError("l0.structural.isolation:boundary_missing")
    boundary = _read_json(boundary_path)
    entrypoint = boundary.get("entrypoint")
    passed = (
        boundary.get("schema_version")
        == "text2ifc/production-input-boundary/0.2"
        and isinstance(entrypoint, str)
        and entrypoint.startswith("run_phase12_")
        and entrypoint.endswith(".py")
        and Path(entrypoint).name == entrypoint
        and boundary.get("ifc_inputs") == ["damaged_ifc_path"]
        and boundary.get("request_inputs") == ["public_request_bundle"]
        and boundary.get("original_ifc_supplied") is False
        and boundary.get("mutation_manifest_supplied") is False
        and boundary.get("deleted_object_ids_supplied") is False
        and boundary.get("private_comparator_available_during_repair") is False
        and _normalize_sha256(str(boundary.get("damaged_ifc_sha256")))
        == damaged_sha256
        and boundary.get("request_sha256")
        == changeset.get("source_request_hash")
        and int(boundary.get("resolved_target_count", -1)) == operation_count
    )
    if not passed:
        raise ValueError("l0.structural.isolation:production_boundary")

    private_roles = {
        "original_ground_truth",
        "repair_input_ifc",
        "published_repair_output",
        "private_ground_truth_evaluation",
        "mutation_manifest_private",
    }
    for role, path in roles.items():
        if role in private_roles or path.suffix.casefold() not in {
            ".json",
            ".txt",
            ".md",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        folded = text.casefold()
        compact = re.sub(r"[^a-z0-9]+", "", folded)
        if any(
            marker in folded
            or re.sub(r"[^a-z0-9]+", "", marker) in compact
            for marker in _STRUCTURAL_PRIVATE_CANARY_MARKERS
        ):
            raise ValueError("l0.structural.isolation:private_canary")
        if path.suffix.casefold() == ".json":
            _assert_no_structural_private_keys(
                json.loads(path.read_text(encoding="utf-8"))
            )


def _assert_no_structural_private_keys(value: Any) -> None:
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, Mapping):
            for raw_key, child in item.items():
                separated = re.sub(
                    r"(?<=[a-z0-9])(?=[A-Z])", "_", str(raw_key)
                )
                normalized = separated.casefold().replace("-", "_")
                if normalized in _STRUCTURAL_FORBIDDEN_PUBLIC_KEYS:
                    raise ValueError("l0.structural.isolation:private_field")
                pending.append(child)
        elif isinstance(item, (list, tuple)):
            pending.extend(item)


def _audit_live_transcript_authority(
    *,
    case: Mapping[str, Any],
    roles: Mapping[str, Path],
    source_manifest: Mapping[str, Any],
    intent: Mapping[str, Any],
    changeset: Mapping[str, Any],
) -> dict[str, Any]:
    live_contract = source_manifest.get("live_contract")
    if not isinstance(live_contract, Mapping):
        raise ValueError("l0.structural.live:contract_missing")
    result_path = roles.get("live_provider_result")
    provider_draft_path = roles.get("live_provider_draft")
    profile_path = roles.get("live_prompt_profile_selection")
    if result_path is None or provider_draft_path is None or profile_path is None:
        raise ValueError("l0.structural.live:retained_authority_missing")
    case_root = roles["source_run_manifest"].parent
    bindings = (
        ("live_uat_result", result_path),
        ("provider_draft", provider_draft_path),
        ("prompt_profile_selection", profile_path),
    )
    for prefix, path in bindings:
        relative = str(live_contract.get(f"{prefix}_path") or "")
        if _safe_path(case_root, relative) != path or _normalize_sha256(
            str(live_contract.get(f"{prefix}_sha256"))
        ) != _sha256(path):
            raise ValueError(f"l0.structural.live:{prefix}_binding")
    live_result = _read_json(result_path)
    provider_draft = _read_json(provider_draft_path)
    try:
        from scripts.ifc_repair.curate_phase12_live_proof import (
            audit_live_artifact_binding,
            audit_live_uat_result,
        )
    except ModuleNotFoundError:  # Direct script execution.
        from curate_phase12_live_proof import (  # type: ignore[no-redef]
            audit_live_artifact_binding,
            audit_live_uat_result,
        )
    try:
        transcript = audit_live_uat_result(live_result)
        live_case_id = str(live_contract.get("case_id") or "")
        if live_case_id not in transcript.get("success_case_ids", ()):
            raise ValueError("live case is not a strict success")
        audit_live_artifact_binding(
            live_result,
            case_id=live_case_id,
            intent=intent,
            provider_draft=provider_draft,
            changeset=changeset,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"l0.structural.live:transcript:{error}") from error
    operation_types = {
        str(item.get("operation_type"))
        for item in changeset.get("operations", ())
        if isinstance(item, Mapping)
    }
    registry = create_default_registry()
    expected_profile_ids = sorted(
        {
            str(registry.require(operation_type).prompt_profile_id)
            for operation_type in operation_types
        }
    )
    expected_selection = select_prompt_profiles(expected_profile_ids).to_dict()
    profiles = load_prompt_profiles()
    stage1_profile_ids = sorted(
        {
            str(registry.require(operation_type).prompt_profile_id)
            for operation_type in registry.operation_types
        }
    )
    stage1_catalog = compact_profile_catalog(
        profiles,
        include_profile_ids=stage1_profile_ids,
    )
    expected_stage1 = {
        "profile_ids": [str(item["profile_id"]) for item in stage1_catalog],
        "profile_versions": [
            str(item["profile_version"]) for item in stage1_catalog
        ],
        "profile_hashes": [str(item["profile_hash"]) for item in stage1_catalog],
        "few_shot_ids": [],
        "few_shot_hashes": [],
    }
    selection = _read_json(profile_path)
    if selection != expected_selection:
        raise ValueError("l0.structural.live:prompt_profile_registry_binding")
    expected_versions = [
        str(item["profile_version"]) for item in expected_selection["profiles"]
    ]
    result_case = next(
        item
        for item in live_result["cases"]
        if isinstance(item, Mapping) and item.get("case_id") == live_case_id
    )
    for attempt in result_case.get("attempts", ()):
        if not isinstance(attempt, Mapping):
            raise ValueError("l0.structural.live:attempt_profile_binding")
        stage = attempt.get("stage")
        if stage == "property_resolution":
            if (
                attempt.get("template_id") != PROPERTY_RESOLUTION_TEMPLATE_ID
                or attempt.get("template_hash")
                != PROPERTY_RESOLUTION_TEMPLATE_HASH
                or any(
                    attempt.get(key) not in (None, [])
                    for key in (
                        "profile_ids",
                        "profile_versions",
                        "profile_hashes",
                        "few_shot_ids",
                        "few_shot_hashes",
                    )
                )
            ):
                raise ValueError("l0.structural.live:attempt_template_binding")
            continue
        if stage == "stage1":
            expected_attempt = expected_stage1
        elif stage == "stage2":
            expected_attempt = {
                "profile_ids": expected_selection["profile_ids"],
                "profile_versions": expected_versions,
                "profile_hashes": expected_selection["profile_hashes"],
                "few_shot_ids": expected_selection["few_shot_ids"],
                "few_shot_hashes": expected_selection["few_shot_hashes"],
            }
        else:
            raise ValueError("l0.structural.live:attempt_profile_binding")
        if any(
            attempt.get(key) != value
            for key, value in expected_attempt.items()
        ):
            raise ValueError("l0.structural.live:attempt_profile_binding")
    return {
        "provider_evidence_mode": "live",
        "live_transcript_status": "strict_recomputed",
    }


def _audit_live_base_damage_authority(
    *,
    roles: Mapping[str, Path],
    source_manifest: Mapping[str, Any],
    original_ifc_path: Path,
    damaged_ifc_path: Path,
) -> tuple[Mapping[str, Any], str]:
    contract = source_manifest.get("base_damage_contract")
    if not isinstance(contract, Mapping):
        raise ValueError("l0.structural.live:base_damage_contract_missing")
    base_path = roles.get("base_damage_source_manifest")
    private_path = roles.get("mutation_manifest_private")
    if base_path is None or not base_path.is_file():
        raise ValueError("l0.structural.live:base_damage_manifest_missing")
    if private_path is None or not private_path.is_file():
        raise ValueError("l0.structural.live:base_damage_evidence_missing")
    case_root = roles["source_run_manifest"].parent
    try:
        base_bound = _safe_path(case_root, str(contract["source_manifest_path"]))
        private_bound = _safe_path(case_root, str(contract["mutation_manifest_path"]))
        bindings_pass = bool(
            base_bound == base_path
            and private_bound == private_path
            and _normalize_sha256(str(contract["source_manifest_sha256"]))
            == _sha256(base_path)
            and _normalize_sha256(str(contract["mutation_manifest_sha256"]))
            == _sha256(private_path)
            and _normalize_sha256(str(contract["original_ifc_sha256"]))
            == _sha256(original_ifc_path)
            and _normalize_sha256(str(contract["damaged_ifc_sha256"]))
            == _sha256(damaged_ifc_path)
        )
    except (KeyError, TypeError, ValueError):
        bindings_pass = False
    if not bindings_pass:
        raise ValueError("l0.structural.live:base_damage_binding")
    base = _read_json(base_path)
    case_id = str(contract.get("case_id") or "")
    if (
        base.get("schema_version") != "text2ifc/phase12-offline-case/0.1"
        or base.get("case_id") != case_id
        or case_id not in _PHASE12_DAMAGE_TARGET_IDS
        or base.get("source") != source_manifest.get("source")
        or base.get("damage") != source_manifest.get("damage")
    ):
        raise ValueError("l0.structural.live:base_damage_contract")
    return base, case_id


def _audit_structural_source_manifest(
    *,
    source_manifest: Mapping[str, Any],
    source_manifest_path: Path | None,
    case_root: Path,
) -> None:
    if source_manifest_path is None:
        raise ValueError("l0.structural.no-fallback:source_run_manifest_missing")
    if source_manifest.get("synthetic_fallback_used") is not False:
        raise ValueError("l0.structural.no-fallback")
    artifacts = source_manifest.get("artifacts")
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise ValueError("proof.hash.source-manifest-artifacts")
    for name, entry in artifacts.items():
        if not isinstance(entry, Mapping):
            raise ValueError(f"proof.hash.source-manifest-entry:{name}")
        relative = str(entry.get("path") or name)
        path = _safe_path(case_root, relative)
        if not path.is_file():
            raise ValueError(f"proof.artifact.missing:{relative}")
        if int(entry.get("bytes", -1)) != path.stat().st_size:
            raise ValueError(f"proof.hash.source-manifest-size:{relative}")
        if _normalize_sha256(str(entry.get("sha256"))) != _sha256(path):
            raise ValueError(f"proof.hash.source-manifest-sha256:{relative}")


def _audit_phase12_damage_provenance(
    *,
    case: Mapping[str, Any],
    roles: Mapping[str, Path],
    source_manifest: Mapping[str, Any],
    damage_case_id: str,
    original_model: Any,
    damaged_model: Any,
    original_ifc_path: Path,
    damaged_ifc_path: Path,
) -> None:
    if case.get("phase") != "12":
        raise ValueError("l0.structural.damage:phase_binding")
    expected_scope = "cross_scene_same_family_bimnet"
    if (
        case.get("evidence_scope") != expected_scope
        or source_manifest.get("evidence_scope") != expected_scope
    ):
        raise ValueError("l0.structural.damage:evidence_scope")

    expected_target_ids = _PHASE12_DAMAGE_TARGET_IDS.get(damage_case_id)
    if expected_target_ids is None:
        raise ValueError("l0.structural.damage:case_contract")
    source_record = source_manifest.get("source")
    source_record = source_record if isinstance(source_record, Mapping) else {}
    source_relative = str(source_record.get("path") or "").replace("\\", "/")
    frozen_contract = _PHASE12_SOURCE_CONTRACTS.get(source_relative)
    if frozen_contract is None:
        raise ValueError("l0.structural.damage:frozen_source_path")
    frozen_hash, frozen_size = frozen_contract
    frozen_source_path = ROOT / source_relative
    if (
        not frozen_source_path.is_file()
        or _sha256(frozen_source_path) != frozen_hash
        or frozen_source_path.stat().st_size != frozen_size
    ):
        raise ValueError("l0.structural.damage:frozen_source_drift")

    private_path = roles.get("mutation_manifest_private")
    if private_path is None:
        raise ValueError("l0.structural.damage:private_manifest_missing")
    private = _read_json(private_path)
    if private.get("visibility") not in {
        None,
        "evaluator_only_after_production",
    }:
        raise ValueError("l0.structural.damage:visibility")

    original_hash = _sha256(original_ifc_path)
    damaged_hash = _sha256(damaged_ifc_path)
    for label, source in (
        ("source_manifest", source_manifest.get("source")),
        ("private_manifest", private.get("source")),
    ):
        if not isinstance(source, Mapping):
            raise ValueError(f"l0.structural.damage:{label}_source")
        if source.get("schema") != "IFC2X3":
            raise ValueError(f"l0.structural.damage:{label}_schema")
        if _normalize_sha256(str(source.get("sha256"))) != original_hash:
            raise ValueError("l0.structural.damage:source_hash")
        if int(source.get("size_bytes", -1)) != original_ifc_path.stat().st_size:
            raise ValueError("l0.structural.damage:source_size")
    if original_hash != frozen_hash or original_ifc_path.stat().st_size != frozen_size:
        raise ValueError("l0.structural.damage:frozen_source_binding")

    damaged_record = private.get("damaged_ifc")
    if (
        not isinstance(damaged_record, Mapping)
        or _normalize_sha256(str(damaged_record.get("sha256"))) != damaged_hash
    ):
        raise ValueError("l0.structural.damage:damaged_hash")

    targets = private.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ValueError("l0.structural.damage:targets")
    target_ids: set[str] = set()
    target_classes: dict[str, str] = {}
    authorized_root_ids: set[str] = set()
    for target in targets:
        if not isinstance(target, Mapping):
            raise ValueError("l0.structural.damage:target_record")
        entity_record = target.get("entity")
        if not isinstance(entity_record, Mapping):
            raise ValueError("l0.structural.damage:target_entity")
        global_id = str(entity_record.get("global_id") or "")
        if not global_id or global_id in target_ids:
            raise ValueError("l0.structural.damage:target_identity")
        target_ids.add(global_id)
        target_classes[global_id] = str(entity_record.get("ifc_class") or "")
        original = _optional_guid(original_model, global_id)
        if (
            original is None
            or original.is_a() != str(entity_record.get("ifc_class"))
            or _optional_guid(damaged_model, global_id) is not None
        ):
            raise ValueError(f"l0.structural.damage:target_state:{global_id}")
        authorized_root_ids.add(global_id)
        for relationship in original_model.get_inverse(original):
            if relationship.is_a("IfcRelationship"):
                authorized_root_ids.add(str(relationship.GlobalId))
        for relationship in getattr(original, "IsDefinedBy", ()):
            if relationship.is_a("IfcRelDefinesByProperties"):
                definition = relationship.RelatingPropertyDefinition
                if definition is not None and definition.is_a("IfcRoot"):
                    authorized_root_ids.add(str(definition.GlobalId))
        for survivor_role in ("type", "storey"):
            survivor = target.get(survivor_role)
            if not isinstance(survivor, Mapping) or not survivor.get("global_id"):
                continue
            survivor_id = str(survivor["global_id"])
            if _optional_guid(damaged_model, survivor_id) is None:
                raise ValueError(
                    f"l0.structural.damage:{survivor_role}_removed:{survivor_id}"
                )

    if target_ids != expected_target_ids:
        raise ValueError("l0.structural.damage:frozen_target_set")
    damage = source_manifest.get("damage")
    if not isinstance(damage, Mapping):
        raise ValueError("l0.structural.damage:public_damage_record")
    private_schema = str(private.get("schema_version") or "")
    if private_schema == (
        "text2ifc/ifc-repair-structural-mutation-private/0.1"
    ):
        if (
            private.get("mutation_type") != "remove_structural_members"
            or damage.get("schema_version")
            != "text2ifc/ifc-repair-structural-mutation-report/0.1"
            or damage.get("mutation_type") != "remove_structural_members"
            or damage.get("valid") is not True
            or _normalize_sha256(str(damage.get("source_sha256")))
            != original_hash
            or _normalize_sha256(str(damage.get("damaged_sha256")))
            != damaged_hash
            or damage.get("counts") != private.get("counts")
        ):
            raise ValueError("l0.structural.damage:mutation_report_binding")
        beam_ids = tuple(
            sorted(
                global_id
                for global_id, ifc_class in target_classes.items()
                if ifc_class == "IfcBeam"
            )
        )
        column_ids = tuple(
            sorted(
                global_id
                for global_id, ifc_class in target_classes.items()
                if ifc_class == "IfcColumn"
            )
        )
        if len(beam_ids) + len(column_ids) != len(target_ids):
            raise ValueError("l0.structural.damage:structural_target_class")
        with tempfile.TemporaryDirectory(
            prefix="phase12-proof-damage-"
        ) as temporary:
            replay_root = Path(temporary) / "mutation"
            replay = remove_structural_members(
                source_path=frozen_source_path,
                output_dir=replay_root,
                beam_global_ids=beam_ids,
                column_global_ids=column_ids,
                expected_source_sha256=frozen_hash,
            )
            if (
                _normalize_sha256(str(replay.get("damaged_sha256")))
                != damaged_hash
                or _sha256(replay_root / "damaged.ifc") != damaged_hash
            ):
                raise ValueError("l0.structural.damage:deterministic_replay")
    elif private_schema == "text2ifc/phase12-private-damage-manifest/0.1":
        expected_mixed_targets = {
            (str(item.get("global_id") or ""), "IfcDoor")
            for item in damage.get("removed_doors", ())
            if isinstance(item, Mapping)
        }
        for item in damage.get("removed_windows", ()):
            if isinstance(item, Mapping):
                expected_mixed_targets.add(
                    (str(item.get("global_id") or ""), "IfcWindow")
                )
                expected_mixed_targets.add(
                    (
                        str(item.get("opening_global_id") or ""),
                        "IfcOpeningElement",
                    )
                )
        if (
            damage.get("door_openings_removed") is not False
            or damage.get("window_openings_removed") is not True
            or {
                (global_id, ifc_class)
                for global_id, ifc_class in target_classes.items()
            }
            != expected_mixed_targets
            or damaged_hash != _PHASE12_MIXED_DAMAGED_SHA256
        ):
            raise ValueError("l0.structural.damage:mixed_damage_binding")
    else:
        raise ValueError("l0.structural.damage:private_manifest_schema")

    try:
        changes = profile_normalized_model_diff(
            original_model,
            damaged_model,
        )["changes"]
    except Exception as error:
        raise ValueError(
            f"l0.structural.damage:not_evaluable:{type(error).__name__}"
        ) from error
    if changes.get("created"):
        raise ValueError("l0.structural.damage:created_root")
    actual_changed = {
        str(item["global_id"])
        for section in ("modified", "removed")
        for item in changes.get(section, ())
    }
    removed_ids = {
        str(item["global_id"]) for item in changes.get("removed", ())
    }
    if not target_ids <= removed_ids:
        raise ValueError("l0.structural.damage:target_diff")
    unexpected = sorted(actual_changed - authorized_root_ids)
    if unexpected:
        raise ValueError(
            "l0.structural.damage:undeclared_root:" + ",".join(unexpected)
        )


def _audit_structural_preservation(
    *,
    changeset: Mapping[str, Any],
    damaged_model: Any,
    repaired_model: Any,
) -> None:
    try:
        profiled = profile_normalized_model_diff(damaged_model, repaired_model)
    except Exception as error:
        raise ValueError(
            f"l0.structural.preservation:not_evaluable:{type(error).__name__}"
        ) from error
    changes = profiled.get("changes")
    if not isinstance(changes, Mapping):
        raise ValueError("l0.structural.preservation:not_evaluable")
    if changes.get("removed"):
        raise ValueError("l0.structural.preservation:removed_root")

    operations = tuple(
        operation
        for operation in changeset.get("operations", ())
        if isinstance(operation, Mapping)
    )
    expected_products = _independent_created_product_contract(operations)
    occurrence_ids = set(expected_products)
    allowed: set[str] = set(occurrence_ids)
    relation_extensions: dict[str, tuple[str, set[str]]] = {}
    for occurrence_id in sorted(occurrence_ids):
        expected_class, operation, role = expected_products[occurrence_id]
        occurrence = _optional_guid(repaired_model, occurrence_id)
        if (
            occurrence is None
            or not occurrence.is_a(expected_class)
            or _optional_guid(damaged_model, occurrence_id) is not None
        ):
            raise ValueError(
                f"l0.structural.preservation:created_product:{occurrence_id}"
            )
        _collect_created_product_root_authority(
            occurrence=occurrence,
            occurrence_id=occurrence_id,
            operation=operation,
            role=role,
            damaged_model=damaged_model,
            allowed=allowed,
            relation_extensions=relation_extensions,
        )

    for operation in operations:
        for assignment in operation.get("semantic_assignments", ()):
            if (
                isinstance(assignment, Mapping)
                and assignment.get("fact_key") == "relationship:type"
                and assignment.get("value")
                and _optional_guid(damaged_model, str(assignment["value"])) is None
            ):
                allowed.add(str(assignment["value"]))

    actual = {
        str(item["global_id"])
        for section in ("created", "modified", "removed")
        for item in changes.get(section, ())
    }
    unexpected = sorted(actual - allowed)
    if unexpected:
        raise ValueError(
            "l0.structural.preservation:undeclared_root:" + ",".join(unexpected)
        )
    for change in changes.get("modified", ()):
        global_id = str(change["global_id"])
        extension = relation_extensions.get(global_id)
        if extension is None or not _is_exact_root_relationship_extension(
            change,
            field=extension[0],
            authorized_new_ids=extension[1],
            damaged_model=damaged_model,
            repaired_model=repaired_model,
        ):
            raise ValueError(
                f"l0.structural.preservation:modified_root:{global_id}"
            )


def _independent_created_product_contract(
    operations: tuple[Mapping[str, Any], ...],
) -> dict[str, tuple[str, Mapping[str, Any], str]]:
    contracts: dict[str, tuple[str, Mapping[str, Any], str]] = {}
    for operation in operations:
        operation_type = str(operation.get("operation_type"))
        if operation_type == "add_beam":
            roles = (("beam", "IfcBeam"),)
        elif operation_type == "add_column":
            roles = (("column", "IfcColumn"),)
        elif operation_type == "add_window_with_opening_to_wall":
            roles = (("window", "IfcWindow"), ("opening", "IfcOpeningElement"))
        elif operation_type == "add_door_with_opening_to_wall":
            roles = (("door", "IfcDoor"), ("opening", "IfcOpeningElement"))
        elif operation_type == "fill_existing_opening_with_door":
            roles = (("door", "IfcDoor"),)
        else:
            raise ValueError(
                f"l0.structural.preservation:operation_unsupported:{operation_type}"
            )
        for role, ifc_class in roles:
            global_id = deterministic_global_id(operation, role)
            previous = contracts.get(global_id)
            if previous is not None and previous[0] != ifc_class:
                raise ValueError("l0.structural.preservation:identity_collision")
            contracts[global_id] = (ifc_class, operation, role)
    return contracts


def _collect_created_product_root_authority(
    *,
    occurrence: Any,
    occurrence_id: str,
    operation: Mapping[str, Any],
    role: str,
    damaged_model: Any,
    allowed: set[str],
    relation_extensions: dict[str, tuple[str, set[str]]],
) -> None:
    relation_groups = (
        getattr(occurrence, "ContainedInStructure", ()),
        getattr(occurrence, "IsDefinedBy", ()),
        getattr(occurrence, "HasAssociations", ()),
        getattr(occurrence, "FillsVoids", ()),
        getattr(occurrence, "VoidsElements", ()),
        getattr(occurrence, "HasFillings", ()),
    )
    unique_relations = {
        int(item.id()): item for group in relation_groups for item in group
    }
    _audit_created_product_relation_cardinality(
        occurrence=occurrence,
        operation=operation,
        role=role,
        relations=tuple(unique_relations.values()),
    )
    for relation in unique_relations.values():
        relation_class = str(relation.is_a())
        extension_field: str | None = None
        if relation_class == "IfcRelContainedInSpatialStructure":
            if occurrence not in relation.RelatedElements:
                raise ValueError("l0.structural.preservation:containment_binding")
            if role in {"beam", "column"}:
                target = operation.get("target")
                target = target if isinstance(target, Mapping) else {}
                if str(relation.RelatingStructure.GlobalId) != str(
                    target.get("storey_global_id")
                ):
                    raise ValueError(
                        "l0.structural.preservation:containment_binding"
                    )
            extension_field = "RelatedElements"
        elif relation_class == "IfcRelDefinesByType":
            expected_types = _expected_relation_values(
                operation,
                role=role,
                fact_prefix="relationship:type",
            )
            if (
                occurrence not in relation.RelatedObjects
                or expected_types
                != {str(relation.RelatingType.GlobalId)}
            ):
                raise ValueError("l0.structural.preservation:type_binding")
            extension_field = "RelatedObjects"
        elif relation_class == "IfcRelDefinesByProperties":
            definition = relation.RelatingPropertyDefinition
            expected_sets = _expected_direct_set_names(operation, role=role)
            if (
                occurrence not in relation.RelatedObjects
                or str(getattr(definition, "Name", "") or "") not in expected_sets
            ):
                raise ValueError("l0.structural.preservation:property_binding")
            extension_field = "RelatedObjects"
        elif relation_class == "IfcRelAssociatesMaterial":
            if (
                occurrence not in relation.RelatedObjects
                or not _expected_relation_values(
                    operation,
                    role=role,
                    fact_prefix="material:",
                )
            ):
                raise ValueError("l0.structural.preservation:material_binding")
            extension_field = "RelatedObjects"
        elif relation_class == "IfcRelAssociatesClassification":
            if (
                occurrence not in relation.RelatedObjects
                or not _expected_relation_values(
                    operation,
                    role=role,
                    fact_prefix="classification:",
                )
            ):
                raise ValueError(
                    "l0.structural.preservation:classification_binding"
                )
            extension_field = "RelatedObjects"
        elif relation_class == "IfcRelFillsElement":
            expected_opening_id = _expected_opening_id(operation)
            expected_filling_ids = {
                deterministic_global_id(operation, candidate)
                for candidate in ("door", "window")
                if str(operation.get("operation_type"))
                in {
                    f"add_{candidate}_with_opening_to_wall",
                    "fill_existing_opening_with_door",
                }
            }
            if (
                str(relation.RelatingOpeningElement.GlobalId)
                != expected_opening_id
                or str(relation.RelatedBuildingElement.GlobalId)
                not in expected_filling_ids
            ):
                raise ValueError("l0.structural.preservation:fill_binding")
        elif relation_class == "IfcRelVoidsElement":
            target = operation.get("target")
            target = target if isinstance(target, Mapping) else {}
            parameters = operation.get("parameters")
            parameters = parameters if isinstance(parameters, Mapping) else {}
            expected_wall_id = str(
                target.get("wall_global_id")
                or parameters.get("host_wall_global_id")
                or ""
            )
            if (
                role != "opening"
                or str(relation.RelatedOpeningElement.GlobalId) != occurrence_id
                or str(relation.RelatingBuildingElement.GlobalId)
                != expected_wall_id
            ):
                raise ValueError("l0.structural.preservation:void_binding")
        else:
            raise ValueError(
                f"l0.structural.preservation:relationship_unsupported:{relation_class}"
            )
        relation_id = str(relation.GlobalId)
        allowed.add(relation_id)
        if extension_field is not None:
            _record_relation_extension(
                relation_extensions,
                relation_id=relation_id,
                field=extension_field,
                occurrence_id=occurrence_id,
            )
        for attribute in ("RelatingType", "RelatingPropertyDefinition"):
            relating = getattr(relation, attribute, None)
            relating_id = getattr(relating, "GlobalId", None)
            if (
                relating_id
                and _optional_guid(damaged_model, str(relating_id)) is None
            ):
                allowed.add(str(relating_id))


def _audit_created_product_relation_cardinality(
    *,
    occurrence: Any,
    operation: Mapping[str, Any],
    role: str,
    relations: tuple[Any, ...],
) -> None:
    operation_id = str(operation.get("operation_id") or "")
    operation_type = str(operation.get("operation_type") or "")
    expected_types = _expected_relation_values(
        operation, role=role, fact_prefix="relationship:type"
    )
    expected_sets = _expected_direct_set_names(operation, role=role)
    expected_materials = _expected_relation_values(
        operation, role=role, fact_prefix="material:"
    )
    expected_classifications = _expected_relation_values(
        operation, role=role, fact_prefix="classification:"
    )
    expected = Counter(
        {
            "IfcRelContainedInSpatialStructure": 0 if role == "opening" else 1,
            "IfcRelDefinesByType": len(expected_types),
            "IfcRelDefinesByProperties": len(expected_sets),
            "IfcRelAssociatesMaterial": len(expected_materials),
            "IfcRelAssociatesClassification": len(expected_classifications),
            "IfcRelFillsElement": (
                1
                if role in {"door", "window", "opening"}
                and operation_type
                in {
                    "add_window_with_opening_to_wall",
                    "add_door_with_opening_to_wall",
                    "fill_existing_opening_with_door",
                }
                else 0
            ),
            "IfcRelVoidsElement": (
                1
                if role == "opening"
                and operation_type
                in {
                    "add_window_with_opening_to_wall",
                    "add_door_with_opening_to_wall",
                }
                else 0
            ),
        }
    )
    actual = Counter(str(relation.is_a()) for relation in relations)
    expected += Counter()
    actual += Counter()
    if actual != expected:
        raise ValueError(
            f"l0.structural.preservation:relationship_cardinality:{operation_id}:"
            f"{role}:expected={dict(sorted(expected.items()))}:"
            f"actual={dict(sorted(actual.items()))}"
        )
    direct_classes = {
        "IfcRelDefinesByProperties",
        "IfcRelAssociatesMaterial",
        "IfcRelAssociatesClassification",
    }
    if any(
        str(relation.is_a()) in direct_classes
        and tuple(relation.RelatedObjects) != (occurrence,)
        for relation in relations
    ):
        raise ValueError(
            f"l0.structural.preservation:shared_direct_relation:{operation_id}:{role}"
        )


def _record_relation_extension(
    contracts: dict[str, tuple[str, set[str]]],
    *,
    relation_id: str,
    field: str,
    occurrence_id: str,
) -> None:
    previous = contracts.get(relation_id)
    if previous is None:
        contracts[relation_id] = (field, {occurrence_id})
        return
    if previous[0] != field:
        raise ValueError("l0.structural.preservation:relation_contract_collision")
    previous[1].add(occurrence_id)


def _expected_relation_values(
    operation: Mapping[str, Any],
    *,
    role: str,
    fact_prefix: str,
) -> set[str]:
    scope = f"{role}_occurrence"
    return {
        str(item.get("value"))
        for item in operation.get("semantic_assignments", ())
        if isinstance(item, Mapping)
        and item.get("scope") == scope
        and str(item.get("fact_key") or "").startswith(fact_prefix)
        and item.get("value") is not None
    }


def _expected_direct_set_names(
    operation: Mapping[str, Any], *, role: str
) -> set[str]:
    scope = f"{role}_occurrence"
    names: set[str] = set()
    for item in operation.get("semantic_assignments", ()):
        if (
            not isinstance(item, Mapping)
            or item.get("scope") != scope
            or item.get("ownership") != "occurrence_direct"
        ):
            continue
        fact_key = str(item.get("fact_key") or "")
        if fact_key.startswith("pset:"):
            names.add(fact_key.removeprefix("pset:").partition(".")[0])
        elif fact_key.startswith("quantity:"):
            set_name = fact_key.removeprefix("quantity:").partition(".")[0]
            names.add(
                "BaseQuantities"
                if set_name in {"window-base", "door-base", "opening-base"}
                else set_name
            )
    return names


def _expected_opening_id(operation: Mapping[str, Any]) -> str:
    if str(operation.get("operation_type")) == "fill_existing_opening_with_door":
        target = operation.get("target")
        target = target if isinstance(target, Mapping) else {}
        return str(target.get("opening_global_id") or "")
    return deterministic_global_id(operation, "opening")


def _is_exact_root_relationship_extension(
    change: Mapping[str, Any],
    *,
    field: str,
    authorized_new_ids: set[str],
    damaged_model: Any,
    repaired_model: Any,
) -> bool:
    before = change.get("before")
    after = change.get("after")
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        return False
    before_attributes = dict(before.get("attributes") or {})
    after_attributes = dict(after.get("attributes") or {})
    before_values = before_attributes.pop(field, None)
    after_values = after_attributes.pop(field, None)
    if before_attributes != after_attributes:
        return False
    if (
        before.get("ifc_class") != after.get("ifc_class")
        or before.get("name") != after.get("name")
    ):
        return False
    relation_id = str(change.get("global_id") or "")
    before_relation = _optional_guid(damaged_model, relation_id)
    after_relation = _optional_guid(repaired_model, relation_id)
    if (
        before_relation is None
        or after_relation is None
        or _relationship_non_endpoint_fingerprint(before_relation, field=field)
        != _relationship_non_endpoint_fingerprint(after_relation, field=field)
    ):
        return False
    before_ids = _normalized_root_ids(before_values)
    after_ids = _normalized_root_ids(after_values)
    added = after_ids - before_ids
    return bool(added) and not (before_ids - after_ids) and added <= authorized_new_ids


def _relationship_non_endpoint_fingerprint(
    relation: Any, *, field: str
) -> tuple[Any, ...]:
    return tuple(
        (
            relation.attribute_name(index),
            _ifc_value_fingerprint(relation[index], seen=set(), depth=0),
        )
        for index in range(len(relation))
        if relation.attribute_name(index) != field
    )


def _ifc_value_fingerprint(
    value: Any, *, seen: set[int], depth: int
) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)):
        return tuple(
            _ifc_value_fingerprint(item, seen=set(seen), depth=depth)
            for item in value
        )
    if hasattr(value, "is_a") and hasattr(value, "id"):
        global_id = getattr(value, "GlobalId", None)
        if global_id:
            return ("root", str(value.is_a()), str(global_id))
        step_id = int(value.id())
        if step_id in seen or depth >= 8:
            return ("cycle", str(value.is_a()))
        nested_seen = set(seen)
        nested_seen.add(step_id)
        return (
            str(value.is_a()),
            tuple(
                (
                    value.attribute_name(index),
                    _ifc_value_fingerprint(
                        value[index], seen=nested_seen, depth=depth + 1
                    ),
                )
                for index in range(len(value))
            ),
        )
    return repr(value)


def _normalized_root_ids(value: Any) -> set[str]:
    values = value if isinstance(value, list) else [value]
    return {
        str(item["global_id"])
        for item in values
        if isinstance(item, Mapping) and item.get("global_id")
    }


def _infer_application_from_ifc(
    *,
    changeset: Mapping[str, Any],
    damaged_model: Any,
    repaired_model: Any,
) -> dict[str, Any]:
    """Recover legacy Window application roles from the actual IFC graph."""

    damaged_window_ids = {
        str(item.GlobalId) for item in damaged_model.by_type("IfcWindow")
    }
    available = [
        item
        for item in repaired_model.by_type("IfcWindow")
        if str(item.GlobalId) not in damaged_window_ids
    ]
    used: set[str] = set()
    operations = []
    for operation in changeset.get("operations", ()):
        operation_id = str(operation.get("operation_id"))
        if operation.get("operation_type") != "add_window_with_opening_to_wall":
            raise ValueError(
                f"legacy application inference unsupported: {operation_id}"
            )
        target = operation.get("target") or {}
        parameters = operation.get("parameters") or {}
        opening_parameters = parameters.get("opening") or {}
        position_parameters = parameters.get("position") or {}
        wall_id = str(target.get("wall_global_id"))
        expected = {
            "width": float(opening_parameters["width_mm"]),
            "height": float(opening_parameters["height_mm"]),
            "sill": float(opening_parameters["sill_height_mm"]),
            "center": float(position_parameters["center_offset_mm"]),
        }
        matches = []
        for window in available:
            window_id = str(window.GlobalId)
            if window_id in used or len(window.FillsVoids) != 1:
                continue
            opening = window.FillsVoids[0].RelatingOpeningElement
            if len(opening.VoidsElements) != 1:
                continue
            wall = opening.VoidsElements[0].RelatingBuildingElement
            if str(wall.GlobalId) != wall_id:
                continue
            dimensions = opening_dimensions_mm(opening)
            position = opening_position_in_wall_mm(opening, wall)
            actual = {
                "width": float(dimensions["width"]),
                "height": float(dimensions["height"]),
                "sill": float(position["sill_height"]),
                "center": float(position["center_offset"]),
            }
            if all(abs(actual[key] - expected[key]) <= 1.0 for key in expected):
                matches.append((window, opening, wall))
        if len(matches) != 1:
            raise ValueError(
                f"legacy application inference ambiguous: {operation_id}:{len(matches)}"
            )
        window, opening, wall = matches[0]
        used.add(str(window.GlobalId))
        fills = window.FillsVoids[0]
        voids = opening.VoidsElements[0]
        window_type = ifcopenshell.util.element.get_type(window)
        storey = ifcopenshell.util.element.get_container(
            window, ifc_class="IfcBuildingStorey"
        )
        created = [
            {"role": "opening", "global_id": str(opening.GlobalId)},
            {"role": "window", "global_id": str(window.GlobalId)},
            {"role": "voids_relationship", "global_id": str(voids.GlobalId)},
            {"role": "fills_relationship", "global_id": str(fills.GlobalId)},
        ]
        operations.append(
            {
                "operation_id": operation_id,
                "operation_type": operation["operation_type"],
                "changes": {
                    "created": created,
                    "modified": [
                        {"role": "host_wall", "global_id": str(wall.GlobalId)}
                    ],
                    "removed": [],
                    "resolved": {
                        "window_type_global_id": (
                            None
                            if window_type is None
                            else str(window_type.GlobalId)
                        ),
                        "storey_global_id": (
                            None if storey is None else str(storey.GlobalId)
                        ),
                    },
                },
            }
        )
    if len(used) != len(operations):
        raise ValueError("legacy application inference did not bind all operations")
    return {"valid": True, "published": True, "operations": operations}


def _check_operations(
    operations: Any,
    *,
    operation_count: int,
    operation_types: set[str],
    source: str,
) -> None:
    if not isinstance(operations, list) or len(operations) != operation_count:
        raise ValueError(f"{source} operation count mismatch")
    actual_types = {str(item.get("operation_type")) for item in operations}
    if actual_types != operation_types:
        raise ValueError(f"{source} operation_type mismatch: {sorted(actual_types)}")


def _check_prompt_profile_evidence(
    roles: Mapping[str, Path],
    *,
    changeset: Mapping[str, Any],
    operation_count: int,
) -> None:
    path = roles.get("prompt_profile_evidence")
    if path is None:
        raise ValueError("missing prompt_profile_evidence")
    evidence = _read_json(path)
    if evidence.get("schema_version") != (
        "text2ifc/phase11-prompt-routing-proof/0.1"
    ):
        raise ValueError("prompt profile evidence schema mismatch")
    bindings = evidence.get("operation_bindings")
    if not isinstance(bindings, list) or len(bindings) != operation_count:
        raise ValueError("prompt profile operation binding count mismatch")
    operations = {
        str(item["operation_id"]): str(item["operation_type"])
        for item in changeset["operations"]
    }
    profiles = load_prompt_profiles()
    for binding in bindings:
        operation_id = str(binding["operation_id"])
        operation_type = str(binding["operation_type"])
        profile_id = str(binding["profile_id"])
        if operations.get(operation_id) != operation_type:
            raise ValueError("prompt profile operation binding mismatch")
        profile = profiles.get(profile_id)
        if profile is None or profile.operation_type != operation_type:
            raise ValueError("prompt profile registry binding mismatch")
        if profile.profile_hash != str(binding["profile_hash"]):
            raise ValueError("prompt profile hash mismatch")
    selected = evidence.get("selected")
    if not isinstance(selected, Mapping):
        raise ValueError("prompt profile selected evidence missing")
    if set(selected.get("profile_ids", ())) != {
        str(item["profile_id"]) for item in bindings
    }:
        raise ValueError("selected prompt profile set mismatch")


def _check_guid_free_targeting(
    roles: Mapping[str, Path],
    *,
    operation_count: int,
    operation_types: set[str],
    name_free: bool = False,
) -> None:
    request_path = roles.get("user_request")
    intent_path = roles.get("guid_free_repair_intent")
    resolution_path = roles.get("deterministic_target_resolution")
    if request_path is None or intent_path is None or resolution_path is None:
        raise ValueError("GUID-free targeting evidence is incomplete")
    request = request_path.read_text(encoding="utf-8")
    if re.search(
        r"(?<![0-9A-Za-z_$])[0-3][0-9A-Za-z_$]{21}(?![0-9A-Za-z_$])",
        request,
    ):
        raise ValueError("public request contains an IFC GlobalId")
    intent = _read_json(intent_path)
    _check_operations(
        intent.get("operations"),
        operation_count=operation_count,
        operation_types=operation_types,
        source="GUID-free RepairIntent",
    )
    for operation in intent["operations"]:
        query = operation.get("target_query", {})
        if any(
            query.get(field) is not None
            for field in ("global_id", "storey_global_id", "host_global_id")
        ):
            raise ValueError("public target_query contains an IFC GlobalId")
        if name_free:
            if query.get("names") or query.get("storey_name"):
                raise ValueError(
                    "name-free target_query contains a name selector"
                )
            constraints = query.get("geometry_constraints")
            allowed_classes = set(query.get("allowed_ifc_classes", ()))
            has_bounded_geometry = (
                isinstance(constraints, list)
                and len(constraints) >= 2
                and (
                    bool(query.get("direction"))
                    or (
                        allowed_classes == {"IfcOpeningElement"}
                        and len(constraints) >= 4
                    )
                )
            )
            if (
                not has_bounded_geometry
            ):
                raise ValueError(
                    "name-free target_query lacks bounded geometry selectors"
                )
        elif not query.get("names") or not query.get("storey_name"):
            raise ValueError("public target_query lacks name/storey selectors")
    resolution = _read_json(resolution_path)
    if resolution.get("status") != "resolved":
        raise ValueError("deterministic target resolution did not resolve")
    operations = resolution.get("operations")
    if not isinstance(operations, list) or len(operations) != operation_count:
        raise ValueError("target resolution operation count mismatch")
    if any(not item.get("target_global_id") for item in operations):
        raise ValueError("target resolution lacks an internal binding")


def _check_success_evaluation(
    evaluation: Mapping[str, Any],
    *,
    operation_count: int,
) -> None:
    if evaluation.get("status") != "passed":
        raise ValueError("production evaluation status is not passed")
    if evaluation.get("complete_repair_success") is not True:
        raise ValueError("complete_repair_success is not true")
    if evaluation.get("successful_artifact_publishable") is not True:
        raise ValueError("successful_artifact_publishable is not true")
    for section in ("application", "preservation"):
        payload = evaluation.get(section)
        if not isinstance(payload, Mapping) or payload.get("status") != "passed":
            raise ValueError(f"evaluation {section} gate is not passed")
    operations = evaluation.get("operations")
    if not isinstance(operations, list) or len(operations) != operation_count:
        raise ValueError("evaluation operation count mismatch")
    for operation in operations:
        levels = {
            str(item.get("level")): str(item.get("status"))
            for item in operation.get("levels", ())
        }
        for level in MANDATORY_LEVELS:
            if levels.get(level) != "passed":
                raise ValueError(
                    f"{operation.get('operation_id')} {level} is not passed"
                )


def _path_for_any_role(roles: Mapping[str, Path], candidates: Iterable[str]) -> Path:
    matches = [roles[role] for role in candidates if role in roles]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one artifact role from {tuple(candidates)}")
    return matches[0]


def _safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"path escapes proof root: {relative}") from error
    return path


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def _normalize_sha256(value: str) -> str:
    normalized = value.removeprefix("sha256:").lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"invalid SHA-256 value: {value}")
    return normalized


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate frozen IFC repair proof cases."
    )
    parser.add_argument(
        "--collection-root",
        "--root",
        dest="collection_root",
        type=Path,
        default=DEFAULT_COLLECTION,
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = validate_success_case_collection(args.collection_root)
    document = result.to_dict()
    validate_proof_validation_document(document)
    if args.as_json:
        print(json.dumps(document, ensure_ascii=False, indent=2))
    else:
        print(
            f"status={result.status} cases={result.case_count} "
            f"operations={result.operation_count} "
            f"files={result.checked_file_count} "
            f"ifc_reopened={result.reopened_ifc_count}"
        )
        for error in result.errors:
            print(f"ERROR {error}")
    return 0 if result.status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
