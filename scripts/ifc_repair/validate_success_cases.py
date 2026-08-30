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
from text2ifc_agent.openai_compat import estimate_openai_compatible_input_tokens
from text2ifc_agent.prompt_registry import load_prompt_registry, render_prompt
from text2ifc_agent.providers import (
    ProviderOutput,
    ProviderOutputError,
    validate_provider_output,
)

try:
    from scripts.ifc_repair.audit_door_repair_triplet import (
        DOOR_OPERATION_TYPES,
        audit_case,
    )
except ModuleNotFoundError:  # Direct script execution from scripts/ifc_repair.
    from audit_door_repair_triplet import DOOR_OPERATION_TYPES, audit_case
from text2ifc_ifc_repair.audit import audit_changeset
from text2ifc_ifc_repair.compare import (
    profile_normalized_model_diff,
    unreachable_non_root_fingerprint_multiset,
)
from text2ifc_ifc_repair.evaluation import evaluate_independent_l1
from text2ifc_ifc_repair.evaluation_models import EvaluationStatus
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
    MAX_PROPERTY_RESOLUTION_RESPONSE_BYTES,
    MAX_PROPERTY_RESOLUTION_RESPONSE_TOKENS,
    TEMPLATE_ID as PROPERTY_RESOLUTION_TEMPLATE_ID,
    _decision_issues as _property_decision_issues,
    _issue as _property_issue,
    _sort_issues as _sort_property_issues,
)
from text2ifc_ifc_repair.repair_intent import RepairIntent
from text2ifc_ifc_repair.request_stage import _unsupported_operations
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent
from text2ifc_ifc_repair.run_models import hash_json
from text2ifc_ifc_repair.run_store import RunStore
from text2ifc_ifc_repair.target_query import TargetQuery, resolve_target
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


@dataclass
class ProofValidationResultV03:
    """R1-capable boundary; the frozen 0.2 result remains unchanged."""

    status: str
    collection_root: str
    case_count: int = 0
    operation_count: int = 0
    checked_file_count: int = 0
    reopened_ifc_count: int = 0
    independently_recomputed_case_count: int = 0
    no_output_case_count: int = 0
    errors: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    cases: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "text2ifc/ifc-repair-proof-validation/0.3",
            "status": self.status,
            "collection_root": self.collection_root,
            "case_count": self.case_count,
            "operation_count": self.operation_count,
            "checked_file_count": self.checked_file_count,
            "reopened_ifc_count": self.reopened_ifc_count,
            "independently_recomputed_case_count": self.independently_recomputed_case_count,
            "no_output_case_count": self.no_output_case_count,
            "errors": self.errors,
            "limitations": self.limitations,
            "cases": self.cases,
        }


PROOF_VALIDATION_SCHEMA = (
    ROOT / "schemas/agent/ifc-repair-proof-validation-0.2.schema.json"
)
PROOF_VALIDATION_SCHEMA_V03 = (
    ROOT / "schemas/agent/ifc-repair-proof-validation-0.3.schema.json"
)
PROOF_TERMINAL_SCHEMA = (
    ROOT / "schemas/agent/ifc-repair-proof-terminal-0.1.schema.json"
)
PROOF_COLLECTION_SCHEMA_V02 = (
    ROOT / "schemas/agent/ifc-repair-proof-collection-0.2.schema.json"
)
PROOF_PROFILE_SCHEMA = (
    ROOT / "schemas/agent/ifc-repair-proof-profile-0.1.schema.json"
)
R1_CANONICAL_PROFILE = (
    ROOT / "docs/validation/repair-milestone-r1/repair-proof-profiles.json"
)
R1_CANONICAL_FREEZE = (
    ROOT / "docs/validation/repair-milestone-r1/repair-acceptance-freeze.json"
)
R1_CANONICAL_HANDOFF = (
    ROOT / "docs/handoffs/repair-milestone-r1-final-acceptance.md"
)
R1_CANONICAL_PROFILE_SHA256 = (
    "375463e43852483106e798a0692e6ed6bed8349de29554e5e0680a64f7340289"
)
R1_CANONICAL_FREEZE_SHA256 = (
    "e1a66e61de8cc56b1b99bb2cb376c7c78429fe4fc8e0a537e29c356a15dded70"
)
R1_CANONICAL_HANDOFF_SHA256 = (
    "bb8c7ecfbf5afd2c231b3be2ef21288101f25f0547e4f3ef770a1b349acff49e"
)


def validate_proof_validation_document(document: Mapping[str, Any]) -> None:
    schema = _read_json(PROOF_VALIDATION_SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(dict(document))


def validate_proof_validation_document_v03(
    document: Mapping[str, Any],
) -> None:
    schema = _read_json(PROOF_VALIDATION_SCHEMA_V03)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(dict(document))


def audit_r1_artifact_predicates(
    *,
    source_model: Any,
    repaired_model: Any,
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    predicates: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Recompute the request-specific R1 artifact predicates from IFC output."""

    registry = create_default_registry()
    operations = [
        item
        for item in changeset.get("operations", ())
        if isinstance(item, Mapping)
    ]
    application_by_id = {
        str(item.get("operation_id")): item
        for item in application.get("operations", ())
        if isinstance(item, Mapping)
    }
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for predicate in predicates:
        predicate_id = str(predicate.get("predicate_id") or "")
        kind = str(predicate.get("kind") or "")
        if not predicate_id or predicate_id in seen_ids:
            raise ValueError("proof.predicate.identity")
        seen_ids.add(predicate_id)
        if kind in {"occurrence_property", "occurrence_preservation"}:
            target = predicate.get("target")
            if not isinstance(target, Mapping):
                raise ValueError(f"proof.predicate.target:{predicate_id}")
            global_id = str(target.get("global_id") or "")
            ifc_class = str(target.get("ifc_class") or "")
            matches = [
                item
                for item in operations
                if item.get("operation_type") == "set_occurrence_properties"
                and str(item.get("target", {}).get("element_global_id") or "")
                == global_id
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"proof.predicate.occurrence_operation:{predicate_id}"
                )
            operation = matches[0]
            try:
                source_target = source_model.by_guid(global_id)
                repaired_target = repaired_model.by_guid(global_id)
            except RuntimeError as error:
                raise ValueError(
                    f"proof.predicate.target_missing:{predicate_id}"
                ) from error
            if (
                source_target.is_a() != ifc_class
                or repaired_target.is_a() != ifc_class
            ):
                raise ValueError(f"proof.predicate.target_class:{predicate_id}")
            applied = application_by_id.get(str(operation.get("operation_id")))
            if not isinstance(applied, Mapping) or not isinstance(
                applied.get("changes"), Mapping
            ):
                raise ValueError(f"proof.predicate.application:{predicate_id}")

        if kind == "occurrence_property":
            expected = predicate.get("property")
            if not isinstance(expected, Mapping):
                raise ValueError(
                    f"proof.predicate.occurrence_property:{predicate_id}"
                )
            set_name = str(expected.get("set_name") or "")
            property_name = str(expected.get("property_name") or "")
            fact_key = f"pset:{set_name}.{property_name}"
            assignments = [
                item
                for item in operation.get("semantic_assignments", ())
                if isinstance(item, Mapping)
                and item.get("fact_key") == fact_key
                and item.get("source_fact_key") == fact_key
            ]
            facts = [
                item
                for item in extract_property_facts(repaired_target)
                if item.set_name == set_name
                and item.property_name == property_name
                and not item.inherited
            ]
            if (
                len(assignments) != 1
                or assignments[0].get("value") != expected.get("value")
                or assignments[0].get("value_type") != expected.get("value_type")
                or assignments[0].get("ownership") != "occurrence_direct"
                or expected.get("scope") != "occurrence_direct"
                or len(facts) != 1
                or facts[0].value != expected.get("value")
                or facts[0].value_type != expected.get("value_type")
            ):
                raise ValueError(
                    f"proof.predicate.occurrence_property:{predicate_id}"
                )
            postcondition = registry.dispatch(
                "postcondition_checker",
                operation,
                model=repaired_model,
                application=applied["changes"],
            )
            if (
                not isinstance(postcondition, Mapping)
                or postcondition.get("valid") is not True
            ):
                raise ValueError(
                    f"proof.predicate.occurrence_property:{predicate_id}"
                )
        elif kind == "occurrence_preservation":
            comparison = registry.dispatch(
                "comparison_adapter",
                operation,
                before_model=source_model,
                after_model=repaired_model,
                application=applied["changes"],
                role_mapping={"target": global_id},
            )
            checks = (
                comparison.get("l1_checks")
                if isinstance(comparison, Mapping)
                else None
            )
            if (
                not isinstance(checks, Mapping)
                or not checks
                or any(
                    not isinstance(value, Mapping)
                    or value.get("status") != "passed"
                    for value in checks.values()
                )
            ):
                raise ValueError(
                    f"proof.predicate.occurrence_preservation:{predicate_id}"
                )
        elif kind == "structural_add":
            operation_type = str(predicate.get("operation_type") or "")
            matches = [
                item
                for item in operations
                if item.get("operation_type") == operation_type
            ]
            if len(matches) != 1 or operation_type not in STRUCTURAL_OPERATION_TYPES:
                raise ValueError(f"proof.predicate.structural_operation:{predicate_id}")
            operation = matches[0]
            applied = application_by_id.get(str(operation.get("operation_id")))
            if not isinstance(applied, Mapping):
                raise ValueError(f"proof.predicate.application:{predicate_id}")
            changes = applied.get("changes")
            resolved = changes.get("resolved") if isinstance(changes, Mapping) else None
            geometry = resolved.get("geometry") if isinstance(resolved, Mapping) else None
            section = geometry.get("section") if isinstance(geometry, Mapping) else None
            expected_geometry = {
                "axis_start_mm": predicate.get("axis_start_mm"),
                "axis_end_mm": predicate.get("axis_end_mm"),
            }
            if (
                not isinstance(geometry, Mapping)
                or not isinstance(section, Mapping)
                or any(
                    [float(value) for value in geometry.get(field, ())]
                    != [float(value) for value in expected]
                    for field, expected in expected_geometry.items()
                    if expected is not None
                )
                or float(section.get("width_mm", -1))
                != float(predicate.get("section_width_mm", -2))
                or float(
                    section.get(
                        "height_mm" if operation_type == "add_beam" else "depth_mm",
                        -1,
                    )
                )
                != float(predicate.get("section_height_mm", -2))
                or str(resolved.get("storey_global_id") or "")
                != str(predicate.get("storey_global_id") or "")
            ):
                raise ValueError(f"proof.predicate.structural_geometry:{predicate_id}")
            expected_orientation = predicate.get("orientation_xy")
            if expected_orientation is not None:
                actual_orientation = geometry.get("orientation", ())
                if [float(value) for value in actual_orientation[:2]] != [
                    float(value) for value in expected_orientation
                ]:
                    raise ValueError(f"proof.predicate.structural_geometry:{predicate_id}")
            created = changes.get("created", ())
            structural_role = STRUCTURAL_FAMILY_BY_OPERATION[operation_type]
            occurrences = [
                item for item in created
                if isinstance(item, Mapping) and item.get("role") == structural_role
            ]
            if len(occurrences) != 1:
                raise ValueError(f"proof.predicate.structural_created:{predicate_id}")
            occurrence = repaired_model.by_guid(str(occurrences[0]["global_id"]))
            type_policy = str(predicate.get("type_policy") or "")
            type_global_id = str(resolved.get("type_global_id") or "")
            created_types = [
                item for item in created
                if isinstance(item, Mapping) and item.get("role") == "structural_type"
            ]
            if type_policy == "generated":
                if len(created_types) != 1 or created_types[0].get("global_id") != type_global_id:
                    raise ValueError(f"proof.predicate.structural_type:{predicate_id}")
            elif type_policy == "reuse_exact_existing":
                if (
                    type_global_id != str(predicate.get("type_global_id") or "")
                    or created_types
                    or source_model.by_guid(type_global_id) is None
                ):
                    raise ValueError(f"proof.predicate.structural_type:{predicate_id}")
            else:
                raise ValueError(f"proof.predicate.structural_type_policy:{predicate_id}")
            expected_property = predicate.get("property")
            if isinstance(expected_property, Mapping):
                set_name = str(expected_property.get("set_name") or "")
                property_name = str(expected_property.get("property_name") or "")
                fact_key = f"pset:{set_name}.{property_name}"
                assignments = [
                    item for item in operation.get("semantic_assignments", ())
                    if isinstance(item, Mapping) and item.get("fact_key") == fact_key
                ]
                facts = [
                    item for item in extract_property_facts(occurrence)
                    if item.set_name == set_name
                    and item.property_name == property_name
                    and not item.inherited
                ]
                if (
                    len(assignments) != 1
                    or assignments[0].get("value") != expected_property.get("value")
                    or assignments[0].get("value_type") != expected_property.get("value_type")
                    or len(facts) != 1
                    or facts[0].value != expected_property.get("value")
                    or facts[0].value_type != expected_property.get("value_type")
                ):
                    raise ValueError(f"proof.predicate.structural_property:{predicate_id}")
        elif kind == "atomic_operation_set":
            expected_types = [str(value) for value in predicate.get("operation_types", ())]
            actual_types = [str(item.get("operation_type")) for item in operations]
            application_ids = [
                str(item.get("operation_id"))
                for item in application.get("operations", ())
                if isinstance(item, Mapping)
            ]
            if (
                Counter(actual_types) != Counter(expected_types)
                or application.get("valid") is not True
                or application.get("published") is not True
                or application_ids != [str(item.get("operation_id")) for item in operations]
            ):
                raise ValueError(f"proof.predicate.atomic_operation_set:{predicate_id}")
        else:
            raise ValueError(f"proof.predicate.kind:{predicate_id}")
        results.append(
            {"predicate_id": predicate_id, "kind": kind, "status": "passed"}
        )
    return results


def validate_r1_terminal_record(
    document: Mapping[str, Any],
    *,
    case_root: Path | str,
) -> dict[str, Any]:
    """Validate one explicit R1 pre-mutation/no-output terminal record."""

    schema = _read_json(PROOF_TERMINAL_SCHEMA)
    Draft202012Validator.check_schema(schema)
    if list(Draft202012Validator(schema).iter_errors(dict(document))):
        raise ValueError("proof.terminal.schema")
    root = Path(case_root).resolve()
    source = document["source"]
    source_path = _safe_path(root, str(source["path"]))
    actual = f"sha256:{_sha256(source_path)}"
    if (
        source.get("sha256_before") != actual
        or source.get("sha256_after") != actual
        or source.get("unchanged") is not True
    ):
        raise ValueError("proof.terminal.source_immutability")

    terminal_class = str(document["terminal_class"])
    if terminal_class == "SUCCESS":
        if document.get("resume_success") is not True:
            raise ValueError("proof.terminal.success")
        return {
            "status": "passed",
            "terminal_class": terminal_class,
            "source_immutable": True,
            "published_artifact_present": True,
        }

    stop = document.get("initial_stop")
    if not isinstance(stop, Mapping):
        raise ValueError("proof.terminal.initial_stop")
    if (
        stop.get("stage2_attempts") != 0
        or stop.get("apply_attempts") != 0
        or stop.get("published_outputs") != []
    ):
        raise ValueError("proof.terminal.pre_mutation")
    if terminal_class == "CLARIFICATION_THEN_SUCCESS":
        offered = stop.get("offered_identities")
        selected = stop.get("selected_identity")
        if (
            stop.get("status") != "clarification_required"
            or not isinstance(offered, list)
            or not offered
            or len(set(map(str, offered))) != len(offered)
            or selected not in offered
            or any(re.match(r"^candidate:\d+(?::|$)", str(item)) for item in offered)
            or not str(stop.get("lineage_id") or "")
            or stop.get("resume_lineage_same") is not True
            or document.get("resume_success") is not True
        ):
            raise ValueError("proof.terminal.clarification_lineage")
        published = True
    elif terminal_class == "INADMISSIBLE_VALUE_OR_CLARIFICATION":
        if (
            stop.get("status") != "clarification_required"
            or stop.get("deterministic_admissibility_status")
            != "clarification_required"
            or "." not in str(stop.get("resolved_property_identity") or "")
        ):
            raise ValueError("proof.terminal.value_admissibility")
        published = bool(document.get("resume_success"))
    elif terminal_class == "UNSUPPORTED_ATOMIC_GUARD":
        if (
            stop.get("status") != "unsupported"
            or stop.get("atomic_request") is not True
            or not stop.get("supported_capabilities")
            or not stop.get("unsupported_capabilities")
            or document.get("resume_success") is not False
        ):
            raise ValueError("proof.terminal.atomic_guard")
        published = False
    else:
        raise ValueError("proof.terminal.class")
    return {
        "status": "passed",
        "terminal_class": terminal_class,
        "source_immutable": True,
        "published_artifact_present": published,
    }


def audit_r1_inadmissible_value_replay(
    *,
    query: Mapping[str, Any],
    candidate_set: Mapping[str, Any],
    decision: Mapping[str, Any],
    decision_trace: Mapping[str, Any],
    claim: Mapping[str, Any],
    expected_property_identity: str,
    retained_admission: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-run the deterministic post-resolution value/type rejection."""

    registry = load_ifc2x3_registry(ROOT)
    records = build_standard_property_records(
        registry,
        corpus_fingerprint=default_standard_corpus_fingerprint(),
    )
    policy = _read_json(
        ROOT / "schemas/ifc/knowledge/property_resolution_policy.v0.2.json"
    )
    admission = admit_property_decision(
        query=query,
        candidate_set=candidate_set,
        decision=decision,
        decision_trace=decision_trace,
        policy=policy,
        records=records,
        registry=registry,
        claim=NaturalLanguagePropertyIntent.from_dict(claim),
    )
    document = admission.to_dict()
    selected_id = str(decision.get("selected_candidate_id") or "")
    selected = next(
        (
            item
            for item in candidate_set.get("candidates", ())
            if isinstance(item, Mapping)
            and str(item.get("candidate_id") or "") == selected_id
        ),
        None,
    )
    identity = (
        f"{selected.get('set_name')}.{selected.get('property_name')}"
        if isinstance(selected, Mapping)
        else ""
    )
    if (
        identity != expected_property_identity
        or admission.exact_intent is not None
        or admission.status != "rejected"
        or admission.reason_code
        not in {"PROPERTY_VALUE_TYPE_INCOMPATIBLE", "PROPERTY_UNIT_INCOMPATIBLE"}
        or (
            retained_admission is not None
            and dict(retained_admission) != document
        )
    ):
        raise ValueError("proof.terminal.value_admissibility_replay")
    return {
        "status": "passed",
        "resolved_property_identity": identity,
        "deterministic_status": admission.status,
        "reason_code": admission.reason_code,
        "exact_intent_constructed": False,
    }


def validate_r1_proof_collection(
    collection_root: Path | str,
) -> ProofValidationResultV03:
    """Validate an R1 collection without requiring private triplet truth."""

    root = Path(collection_root).resolve()
    result = ProofValidationResultV03(status="failed", collection_root=root.as_posix())
    try:
        collection = _read_json(root / "manifest.json")
        collection_schema = _read_json(PROOF_COLLECTION_SCHEMA_V02)
        Draft202012Validator.check_schema(collection_schema)
        Draft202012Validator(collection_schema).validate(collection)
        profile_path = _safe_path(root, str(collection["profile"]))
        profiles = _read_json(profile_path)
        profile_schema = _read_json(PROOF_PROFILE_SCHEMA)
        Draft202012Validator.check_schema(profile_schema)
        Draft202012Validator(profile_schema).validate(profiles)
        _validate_r1_profile_freeze(profile_path, profiles)
        if profiles.get("provenance_namespace") != collection.get(
            "provenance_namespace"
        ):
            raise ValueError("proof.profile.provenance_namespace")
        cases = collection["cases"]
        if int(collection["case_count"]) != len(cases):
            raise ValueError("proof.collection.case_count")
        case_ids = [str(case["case_id"]) for case in cases]
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("proof.collection.case_id")
        profiles_by_id = {
            str(profile["case_id"]): profile for profile in profiles["cases"]
        }
        if case_ids != list(profiles["execution_order"]):
            raise ValueError("proof.profile.execution_order")
        result.case_count = len(cases)
        for case in cases:
            case_id = str(case["case_id"])
            try:
                profile = profiles_by_id.get(case_id)
                if not isinstance(profile, Mapping):
                    raise ValueError("proof.profile.case_missing")
                if profile.get("terminal_class") != case.get("terminal_class"):
                    raise ValueError("proof.profile.terminal_class")
                summary = _validate_r1_case(
                    root=root,
                    case=case,
                    profile=profile,
                    provenance_namespace=str(collection["provenance_namespace"]),
                )
                result.cases.append(summary)
                result.operation_count += int(summary.get("operation_count", 0))
                result.checked_file_count += int(summary.get("checked_file_count", 0))
                result.reopened_ifc_count += int(summary.get("reopened_ifc_count", 0))
                result.independently_recomputed_case_count += 1
                if summary.get("published_artifact_present") is False:
                    result.no_output_case_count += 1
            except Exception as error:
                result.errors.append(f"{case_id}: {error}")
    except Exception as error:
        result.errors.append(f"collection: {error}")
    result.status = "passed" if not result.errors else "failed"
    return result


def _validate_r1_profile_freeze(
    profile_path: Path,
    profiles: Mapping[str, Any],
) -> None:
    if (
        _sha256(R1_CANONICAL_PROFILE) != R1_CANONICAL_PROFILE_SHA256
        or _sha256(R1_CANONICAL_FREEZE) != R1_CANONICAL_FREEZE_SHA256
        or _sha256(R1_CANONICAL_HANDOFF) != R1_CANONICAL_HANDOFF_SHA256
    ):
        raise ValueError("proof.profile.repository_authority_drift")
    if _sha256(profile_path) != R1_CANONICAL_PROFILE_SHA256:
        raise ValueError("proof.profile.authoritative_profile")
    freeze = profiles.get("freeze")
    if not isinstance(freeze, Mapping):
        raise ValueError("proof.profile.freeze")
    freeze_path = _safe_path(profile_path.parent, str(freeze.get("path") or ""))
    if (
        not freeze_path.is_file()
        or _normalize_sha256(str(freeze.get("sha256") or ""))
        != R1_CANONICAL_FREEZE_SHA256
        or _sha256(freeze_path) != R1_CANONICAL_FREEZE_SHA256
    ):
        raise ValueError("proof.profile.freeze_hash")


def _r1_frozen_case_authority(case_id: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Return the byte-frozen case/model pair, never a curated self-report."""

    if _sha256(R1_CANONICAL_FREEZE) != R1_CANONICAL_FREEZE_SHA256:
        raise ValueError("proof.case_authority.freeze_hash")
    freeze = _read_json(R1_CANONICAL_FREEZE)
    cases = [item for item in freeze.get("cases", ()) if item.get("case_id") == case_id]
    if len(cases) != 1:
        raise ValueError("proof.case_authority.case_id")
    case = cases[0]
    models = [
        item
        for item in freeze.get("models", ())
        if item.get("model_id") == case.get("model_id")
    ]
    if len(models) != 1:
        raise ValueError("proof.case_authority.model_id")
    return case, models[0]


def _r1_text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _audit_r1_frozen_case_authority(
    *,
    case_id: str,
    terminal: Mapping[str, Any],
    source_ifc_path: Path,
    roles: Mapping[str, Path],
) -> dict[str, str | None]:
    """Bind retained public source/request bytes to the canonical R1 freeze."""

    frozen, model = _r1_frozen_case_authority(case_id)
    source = terminal.get("source")
    if (
        not isinstance(source, Mapping)
        or source_ifc_path.stat().st_size != int(model.get("size_bytes", -1))
        or _sha256(source_ifc_path) != _normalize_sha256(str(model.get("sha256") or ""))
        or _normalize_sha256(str(source.get("sha256_before") or ""))
        != _normalize_sha256(str(model.get("sha256") or ""))
        or _normalize_sha256(str(source.get("sha256_after") or ""))
        != _normalize_sha256(str(model.get("sha256") or ""))
        or source.get("unchanged") is not True
    ):
        raise ValueError("proof.case_authority.source")
    if str(ifcopenshell.open(str(source_ifc_path)).schema) != str(model.get("schema") or ""):
        raise ValueError("proof.case_authority.source_schema")

    initial = str(frozen.get("request") or "")
    resume = frozen.get("resume")
    initial_role = "initial_user_request" if resume is not None else "user_request"
    initial_path = _require_r1_role(roles, initial_role)
    if (
        initial_path.read_text(encoding="utf-8").rstrip() != initial
        or _r1_text_sha256(initial) != _normalize_sha256(str(frozen.get("request_sha256") or ""))
    ):
        raise ValueError("proof.case_authority.request")
    effective = initial
    if resume is not None:
        answer_path = _require_r1_role(roles, "clarification_answer")
        answer = answer_path.read_text(encoding="utf-8").rstrip()
        if (
            answer != str(resume)
            or _r1_text_sha256(answer)
            != _normalize_sha256(str(frozen.get("resume_sha256") or ""))
        ):
            raise ValueError("proof.case_authority.resume")
        if case_id == "M1":
            effective = f"{initial}\n补充说明：{answer.strip()}"
        user_request = _require_r1_role(roles, "user_request")
        if user_request.read_text(encoding="utf-8").rstrip() != effective:
            raise ValueError("proof.case_authority.effective_request")
    return {
        "initial_hash": "sha256:" + _r1_text_sha256(initial),
        "effective_hash": "sha256:" + _r1_text_sha256(effective),
        "resume": None if resume is None else str(resume),
    }


def _audit_r1_request_hash_lineage(
    *,
    authority: Mapping[str, str | None],
    state: Mapping[str, Any] | Any,
    initial_intent: Mapping[str, Any],
    final_intent: Mapping[str, Any],
    changeset: Mapping[str, Any] | None,
    boundary: Mapping[str, Any] | None,
) -> None:
    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    initial_hash = str(authority["initial_hash"])
    effective_hash = str(authority["effective_hash"])
    if (
        state_document.get("request_hash") != initial_hash
        or initial_intent.get("source_request_hash") != initial_hash
        or final_intent.get("source_request_hash") != effective_hash
        or (changeset is not None and changeset.get("source_request_hash") != effective_hash)
        or (boundary is not None and boundary.get("request_sha256") != effective_hash)
    ):
        raise ValueError("proof.case_authority.request_lineage")


def _validate_r1_case(
    *,
    root: Path,
    case: Mapping[str, Any],
    profile: Mapping[str, Any],
    provenance_namespace: str,
) -> dict[str, Any]:
    case_id = str(case["case_id"])
    case_root = _safe_path(root, str(case["case_root"]))
    if not case_root.is_dir():
        raise ValueError("proof.case_root")
    checked_file_count, roles = _validate_r1_case_files(
        case_id=case_id,
        case_root=case_root,
        files_path=_safe_path(root, str(case["files"])),
        report_path=_safe_path(root, str(case["report"])),
    )
    terminal_path = _require_r1_declared_artifact(
        case_root=case_root,
        declared_path=_safe_path(root, str(case.get("terminal_record") or "")),
        roles=roles,
        role="proof_terminal_record",
    )
    terminal = _read_json(terminal_path)
    if terminal.get("case_id") != case_id:
        raise ValueError("proof.terminal.case_id")
    terminal_result = validate_r1_terminal_record(terminal, case_root=case_root)
    terminal_expectation = profile.get("terminal_expectation", {})
    if not isinstance(terminal_expectation, Mapping):
        raise ValueError("proof.profile.terminal_expectation")
    initial_stop = terminal.get("initial_stop", {})
    if not isinstance(initial_stop, Mapping) or any(
        initial_stop.get(key) != value
        for key, value in terminal_expectation.items()
    ):
        raise ValueError("proof.profile.terminal_expectation")
    terminal_source = _require_r1_declared_artifact(
        case_root=case_root,
        declared_path=_safe_path(case_root, str(terminal["source"]["path"])),
        roles=roles,
        role="repair_input_ifc",
    )
    case_authority = _audit_r1_frozen_case_authority(
        case_id=case_id,
        terminal=terminal,
        source_ifc_path=terminal_source,
        roles=roles,
    )
    source_model = ifcopenshell.open(str(terminal_source))
    if source_model.schema != "IFC2X3":
        raise ValueError("proof.ifc.schema")
    terminal_class = str(case["terminal_class"])
    predicates = profile.get("artifact_predicates", ())
    property_claim_count = int(profile.get("property_claim_count", 0))
    base = {
        "case_id": case_id,
        "provenance_namespace": provenance_namespace,
        "terminal_class": terminal_class,
        "status": "passed",
        "artifact_predicates": [],
        "property_authority_coverage": "not_applicable",
        "property_claim_count": property_claim_count,
        "current_property_acceptance_eligible": property_claim_count == 0,
        "source_immutable": bool(terminal_result["source_immutable"]),
        "published_artifact_present": bool(
            terminal_result["published_artifact_present"]
        ),
        "operation_count": 0,
        "checked_file_count": checked_file_count,
        "reopened_ifc_count": 1,
    }
    if terminal_class == "INADMISSIBLE_VALUE_OR_CLARIFICATION":
        replay = case.get("inadmissible_value_replay")
        if not isinstance(replay, Mapping):
            raise ValueError("proof.terminal.value_admissibility_replay_missing")
        replay_paths = {
            name: _safe_path(root, str(replay.get(name) or ""))
            for name in (
                "query",
                "candidate_set",
                "decision",
                "decision_trace",
                "claim",
                "retained_admission",
            )
        }
        if any(not path.is_file() for path in replay_paths.values()):
            raise ValueError("proof.terminal.value_admissibility_replay_artifact")
        m1_state_path = _require_r1_role(roles, "runtime_state")
        m1_state = _load_validated_r1_state(m1_state_path)
        m1_initial_intent_path = _r1_initial_request_intent_path(
            state=m1_state,
            state_path=m1_state_path,
            listed_paths=roles.values(),
            fallback=_require_r1_role(roles, "stage1_repair_intent"),
        )
        _audit_r1_m1_initial_replay_binding(
            replay_paths=replay_paths,
            roles=roles,
            state=m1_state,
            state_path=m1_state_path,
            expected_resume_answer=str(case_authority["resume"] or ""),
            initial_intent=_read_json(m1_initial_intent_path),
        )
        audit_r1_inadmissible_value_replay(
            query=_read_json(replay_paths["query"]),
            candidate_set=_read_json(replay_paths["candidate_set"]),
            decision=_read_json(replay_paths["decision"]),
            decision_trace=_read_json(replay_paths["decision_trace"]),
            claim=_read_json(replay_paths["claim"]),
            expected_property_identity=str(
                terminal["initial_stop"]["resolved_property_identity"]
            ),
            retained_admission=_read_json(replay_paths["retained_admission"]),
        )
    if terminal_class == "UNSUPPORTED_ATOMIC_GUARD":
        if predicates:
            raise ValueError("proof.guard.artifact_predicates")
        state_path = _require_r1_role(roles, "runtime_state")
        state = _load_validated_r1_state(state_path)
        if _normalize_sha256(str(state.source.sha256)) != _sha256(terminal_source):
            raise ValueError("proof.h4.source_binding")
        intent_path = _r1_bound_transition_artifact(
            state=state,
            state_path=state_path,
            artifact_key="intent",
            listed_paths=roles.values(),
            before_transition_id=state.transitions[-1].transition_id,
            require_unique=True,
        )
        declared_intent_path = _require_r1_role(roles, "stage1_repair_intent")
        if intent_path != declared_intent_path.resolve():
            raise ValueError("proof.h4.stage1_intent_binding")
        _audit_r1_request_hash_lineage(
            authority=case_authority,
            state=state,
            initial_intent=_read_json(intent_path),
            final_intent=_read_json(intent_path),
            changeset=None,
            boundary=(
                _read_json(roles["production_input_boundary"])
                if "production_input_boundary" in roles
                else None
            ),
        )
        live_audit = _audit_r1_live_provider_provenance(
            case_id=case_id,
            roles=roles,
            provider_intent=_read_json(intent_path),
            changeset=None,
            damaged_sha256=_sha256(terminal_source),
            validated_state=state,
        )
        attempts = live_audit["attempts"]
        replayed_guard = _audit_r1_unsupported_guard_replay(
            intent=_read_json(intent_path),
            state=state,
            expected_supported_capabilities=terminal_expectation.get(
                "supported_capabilities", ()
            ),
            expected_unsupported_capabilities=terminal_expectation.get(
                "unsupported_capabilities", ()
            ),
            expected_reason_code="STRUCTURAL_ANALYSIS_UNSUPPORTED",
            attempts=attempts,
        )
        for field in (
            "supported_capabilities",
            "unsupported_capabilities",
            "atomic_request",
            "stage2_attempts",
            "apply_attempts",
            "published_outputs",
        ):
            if initial_stop.get(field) != replayed_guard[field]:
                raise ValueError(f"proof.h4.terminal_replay:{field}")
        _audit_r1_h4_no_mutation_artifacts(
            roles=roles,
            source_ifc_path=terminal_source,
            validated_state=state,
        )
        return base
    if terminal_class == "CLARIFICATION_THEN_SUCCESS":
        state_path = _require_r1_role(roles, "runtime_state")
        state = _load_validated_r1_state(state_path)
        if _normalize_sha256(str(state.source.sha256)) != _sha256(terminal_source):
            raise ValueError("proof.h3.source_binding")
        expected_selected = str(
            terminal_expectation.get("selected_identity") or ""
        )
        lineage = _audit_r1_h3_state_selection(
            state=state,
            expected_selected_identity=expected_selected,
        )
        clarification_transition_id = lineage.get(
            "clarification_transition_id"
        )
        if not isinstance(clarification_transition_id, int):
            raise ValueError("proof.h3.clarification_lineage")
        initial_intent_path = _r1_bound_transition_artifact(
            state=state,
            state_path=state_path,
            artifact_key="intent",
            listed_paths=roles.values(),
            before_transition_id=clarification_transition_id,
            require_unique=True,
        )
        with tempfile.TemporaryDirectory(prefix="r1-h3-target-replay-") as scratch:
            final_target_replay = _audit_r1_h3_final_target_resolution_replay(
                source_ifc_path=terminal_source,
                initial_intent=_read_json(initial_intent_path),
                state=state,
                expected_selected_identity=expected_selected,
                scratch_root=Path(scratch),
            )
        replayed = final_target_replay["initial_replay"]
        h3_projected_intent = final_target_replay["projected_intent"]
        if (
            set(map(str, initial_stop.get("offered_identities", ())))
            != set(replayed["offered_identities"])
            or initial_stop.get("selected_identity")
            != replayed["selected_identity"]
            or initial_stop.get("lineage_id")
            != f"run:{lineage['run_id']}"
            or initial_stop.get("status") != "clarification_required"
            or initial_stop.get("reason_code") != "ambiguous_target"
            or initial_stop.get("stage2_attempts") != 0
            or initial_stop.get("apply_attempts") != 0
            or initial_stop.get("published_outputs") != []
        ):
            raise ValueError("proof.h3.terminal_replay")
    if terminal_result["published_artifact_present"] is not True:
        raise ValueError("proof.success.published_artifact")

    required = ("source_ifc", "repaired_ifc", "changeset", "application")
    role_by_name = {
        "source_ifc": "repair_input_ifc",
        "repaired_ifc": "published_repair_output",
        "changeset": "bound_changeset",
        "application": "application_result",
    }
    paths = {
        name: _require_r1_declared_artifact(
            case_root=case_root,
            declared_path=_safe_path(root, str(case.get(name) or "")),
            roles=roles,
            role=role_by_name[name],
        )
        for name in required
    }
    if terminal_source != paths["source_ifc"]:
        raise ValueError("proof.terminal.source_binding")
    repaired_model = ifcopenshell.open(str(paths["repaired_ifc"]))
    if source_model.schema != "IFC2X3" or repaired_model.schema != "IFC2X3":
        raise ValueError("proof.ifc.schema")
    changeset = _read_json(paths["changeset"])
    application = _read_json(paths["application"])
    success_state_path = _require_r1_role(roles, "runtime_state")
    success_state = _load_validated_r1_state(success_state_path)
    if _normalize_sha256(str(success_state.source.sha256)) != _sha256(
        terminal_source
    ):
        raise ValueError("proof.success.source_binding")
    final_intent_path = _r1_bound_transition_artifact(
        state=success_state,
        state_path=success_state_path,
        artifact_key="intent",
        listed_paths=roles.values(),
        before_transition_id=None,
        require_unique=False,
    )
    initial_request_intent_path = _r1_initial_request_intent_path(
        state=success_state,
        state_path=success_state_path,
        listed_paths=roles.values(),
        fallback=initial_intent_path if terminal_class == "CLARIFICATION_THEN_SUCCESS" else final_intent_path,
    )
    bound_changeset_path = _r1_bound_transition_artifact(
        state=success_state,
        state_path=success_state_path,
        artifact_key="changeset",
        listed_paths=roles.values(),
        before_transition_id=None,
        require_unique=True,
    )
    if _sha256(bound_changeset_path) != _sha256(paths["changeset"]):
        raise ValueError("proof.success.changeset_binding")
    _audit_r1_request_hash_lineage(
        authority=case_authority,
        state=success_state,
        initial_intent=_read_json(initial_request_intent_path),
        final_intent=_read_json(final_intent_path),
        changeset=changeset,
        boundary=(
            _read_json(roles["production_input_boundary"])
            if "production_input_boundary" in roles
            else None
        ),
    )
    provider_intent_path = (
        initial_intent_path
        if terminal_class == "CLARIFICATION_THEN_SUCCESS"
        else final_intent_path
    )
    _audit_r1_live_provider_provenance(
        case_id=case_id,
        roles=roles,
        provider_intent=_read_json(provider_intent_path),
        initial_provider_intent=_read_json(initial_request_intent_path),
        changeset=changeset,
        damaged_sha256=_sha256(terminal_source),
        validated_state=success_state,
    )
    operations = [
        item for item in changeset.get("operations", ()) if isinstance(item, Mapping)
    ]
    _audit_r1_exact_operation_set(changeset=changeset, profile=profile)
    application_ids = [
        str(item.get("operation_id"))
        for item in application.get("operations", ())
        if isinstance(item, Mapping)
    ]
    if (
        application.get("valid") is not True
        or application.get("published") is not True
        or application_ids != [str(item.get("operation_id")) for item in operations]
    ):
        raise ValueError("proof.application.publication")
    _audit_r1_success_terminal_binding(
        state=success_state,
        state_path=success_state_path,
        roles=roles,
        repaired_ifc_path=paths["repaired_ifc"],
        application=application,
    )
    audit_repaired_operations(
        changeset=changeset,
        application=application,
        damaged_model=source_model,
        repaired_model=repaired_model,
    )
    _audit_authorized_repair_preservation(
        damaged_ifc_path=paths["source_ifc"],
        repaired_ifc_path=paths["repaired_ifc"],
        changeset=changeset,
        application=application,
        damaged_model=source_model,
        repaired_model=repaired_model,
    )
    structural = any(
        item.get("operation_type") in STRUCTURAL_OPERATION_TYPES
        for item in operations
    )
    if structural:
        _audit_structural_type_and_semantic_authority(
            changeset=changeset,
            damaged_model=source_model,
            repaired_model=repaired_model,
        )
        if not any(
            item.get("operation_type") == "set_occurrence_properties"
            for item in operations
        ):
            _audit_structural_preservation(
                changeset=changeset,
                damaged_model=source_model,
                repaired_model=repaired_model,
            )
    predicate_results = audit_r1_artifact_predicates(
        source_model=source_model,
        repaired_model=repaired_model,
        changeset=changeset,
        application=application,
        predicates=predicates,
    )
    base.update(
        {
            "artifact_predicates": predicate_results,
            "operation_count": len(operations),
            "checked_file_count": checked_file_count,
            "reopened_ifc_count": 2,
        }
    )
    if property_claim_count:
        replay = case.get("authority_replay")
        if not isinstance(replay, Mapping):
            raise ValueError("proof.property.authority_replay_missing")
        replay_paths = {
            name: _safe_path(root, str(replay.get(name) or ""))
            for name in (
                "intent",
                "resolution",
                "semantic_manifest",
                "source_manifest",
                "evidence_root",
            )
        }
        if any(not path.exists() for path in replay_paths.values()):
            raise ValueError("proof.property.authority_replay_artifact")
        evidence_root = replay_paths["evidence_root"]
        if not evidence_root.is_dir():
            raise ValueError("proof.property.evidence_root")
        if _sha256(replay_paths["intent"]) != _sha256(final_intent_path):
            raise ValueError("proof.property.intent_state_binding")
        authority_roles = dict(roles)
        if authority_roles.get("source_run_manifest") != replay_paths["source_manifest"]:
            raise ValueError("proof.property.source_manifest_role")
        authority_intent = _read_json(replay_paths["intent"])
        if terminal_class == "CLARIFICATION_THEN_SUCCESS":
            authority_intent = h3_projected_intent
        authority = audit_current_property_authority_replay(
            source_ifc_path=paths["source_ifc"],
            source_sha256=_sha256(paths["source_ifc"]),
            intent=authority_intent,
            changeset=changeset,
            retained_resolution=_read_json(replay_paths["resolution"]),
            retained_manifest=_read_json(replay_paths["semantic_manifest"]),
            roles=authority_roles,
            provider_evidence_mode=str(case.get("provider_evidence_mode") or "live"),
        )
        if (
            authority.get("property_authority_coverage")
            != "strict_stage_1_5_recomputed"
            or authority.get("current_property_acceptance_eligible") is not True
            or int(authority.get("property_claim_count", -1))
            != property_claim_count
        ):
            raise ValueError("proof.property.authority_replay")
        base.update(authority)
    return base


def _validate_r1_case_files(
    *,
    case_id: str,
    case_root: Path,
    files_path: Path,
    report_path: Path,
) -> tuple[int, dict[str, Path]]:
    if files_path.parent != case_root or report_path.parent != case_root:
        raise ValueError("proof.files.case_root_binding")
    files = _read_json(files_path)
    if (
        files.get("schema_version") != "text2ifc/ifc-repair-proof-files/0.2"
        or files.get("case_id") != case_id
    ):
        raise ValueError("proof.files.contract")
    entries = files.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("proof.files.entries")
    listed: set[str] = set()
    roles: dict[str, Path] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("proof.files.entry")
        relative = str(entry.get("path") or "")
        role = str(entry.get("role") or "")
        if not relative or relative in listed or not role or role in roles:
            raise ValueError("proof.files.identity")
        listed.add(relative)
        artifact = _safe_path(case_root, relative)
        roles[role] = artifact
        if not artifact.is_file():
            raise ValueError(f"proof.artifact.missing:{relative}")
        if artifact.stat().st_size != int(entry.get("size_bytes", -1)):
            raise ValueError(f"proof.artifact.size:{relative}")
        if _sha256(artifact) != _normalize_sha256(str(entry.get("sha256") or "")):
            raise ValueError(f"proof.artifact.sha256:{relative}")
    if roles.get("proof_report") != report_path.resolve():
        raise ValueError("proof.files.report_role")
    actual = {
        path.relative_to(case_root).as_posix()
        for path in case_root.rglob("*")
        if path.is_file()
    }
    expected = listed | {files_path.name}
    if actual != expected:
        raise ValueError(
            f"proof.files.coverage:missing={sorted(expected-actual)}:unindexed={sorted(actual-expected)}"
        )
    return len(entries), roles


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
        state_path = roles.get("runtime_state")
        self.state = (
            None
            if state_path is None
            else _load_validated_r1_state(state_path)
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
        evidence_claim_id = (
            claim_id
            if self.state is None
            else _r1_effective_property_claim_id(
                state=self.state,
                base_claim_id=claim_id,
            )
        )
        query_path, query_document = self._query_for_claim(
            operation_id=operation_id,
            operation_type=operation_type,
            claim_id=evidence_claim_id,
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
            claim_id=evidence_claim_id,
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
                claim_id=evidence_claim_id,
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
    _manifest_operation_types: frozenset[str] | None = STRUCTURAL_OPERATION_TYPES,
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
        if _manifest_operation_types is None
        or evidence.operation_types[operation_id] in _manifest_operation_types
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


def audit_current_property_authority_replay(
    *,
    source_ifc_path: Path,
    source_sha256: str,
    intent: Mapping[str, Any],
    changeset: Mapping[str, Any],
    retained_resolution: Mapping[str, Any],
    retained_manifest: Mapping[str, Any],
    roles: Mapping[str, Path],
    provider_evidence_mode: str,
) -> dict[str, Any]:
    """Replay current Stage 1.5 authority for every registered operation."""

    return _audit_structural_authority_replay(
        damaged_ifc_path=source_ifc_path,
        damaged_sha256=source_sha256,
        intent=intent,
        changeset=changeset,
        retained_resolution=retained_resolution,
        retained_manifest=retained_manifest,
        roles=roles,
        provider_evidence_mode=provider_evidence_mode,
        _manifest_operation_types=None,
    )


def _bound_target_global_id(operation: Mapping[str, Any]) -> str:
    operation_type = str(operation.get("operation_type") or "")
    field = {
        "add_beam": "storey_global_id",
        "add_column": "storey_global_id",
        "add_window_with_opening_to_wall": "wall_global_id",
        "add_opening_to_wall": "wall_global_id",
        "add_door_with_opening_to_wall": "wall_global_id",
        "fill_existing_opening_with_door": "opening_global_id",
        "set_occurrence_properties": "element_global_id",
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
    _audit_production_input_isolation(
        roles=roles,
        boundary_path=boundary_path,
        damaged_sha256=damaged_sha256,
        request_sha256=str(changeset.get("source_request_hash") or ""),
        resolved_target_count=operation_count,
        expected_entrypoint=None,
        entrypoint_prefix="run_phase12_",
        boundary_error="l0.structural.isolation:production_boundary",
        private_canary_error="l0.structural.isolation:private_canary",
        private_field_error="l0.structural.isolation:private_field",
    )


def _audit_production_input_isolation(
    *,
    roles: Mapping[str, Path],
    boundary_path: Path,
    damaged_sha256: str,
    request_sha256: str,
    resolved_target_count: int,
    expected_entrypoint: str | None,
    entrypoint_prefix: str | None,
    boundary_error: str,
    private_canary_error: str,
    private_field_error: str,
) -> None:
    """Shared production boundary and public-artifact isolation contract."""

    boundary = _read_json(boundary_path)
    entrypoint = boundary.get("entrypoint")
    entrypoint_valid = bool(
        isinstance(entrypoint, str)
        and Path(entrypoint).name == entrypoint
        and entrypoint.endswith(".py")
        and (
            entrypoint == expected_entrypoint
            if expected_entrypoint is not None
            else isinstance(entrypoint_prefix, str)
            and entrypoint.startswith(entrypoint_prefix)
        )
    )
    if not (
        boundary.get("schema_version")
        == "text2ifc/production-input-boundary/0.2"
        and entrypoint_valid
        and boundary.get("ifc_inputs") == ["damaged_ifc_path"]
        and boundary.get("request_inputs") == ["public_request_bundle"]
        and boundary.get("original_ifc_supplied") is False
        and boundary.get("mutation_manifest_supplied") is False
        and boundary.get("deleted_object_ids_supplied") is False
        and boundary.get("private_comparator_available_during_repair") is False
        and _normalize_sha256(str(boundary.get("damaged_ifc_sha256") or ""))
        == _normalize_sha256(damaged_sha256)
        and str(boundary.get("request_sha256") or "") == request_sha256
        and isinstance(boundary.get("resolved_target_count"), int)
        and int(boundary["resolved_target_count"]) == resolved_target_count
    ):
        raise ValueError(boundary_error)

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
            raise ValueError(private_canary_error)
        if path.suffix.casefold() == ".json":
            _assert_no_structural_private_keys(
                json.loads(text),
                error_code=private_field_error,
            )


def _assert_no_structural_private_keys(
    value: Any,
    *,
    error_code: str = "l0.structural.isolation:private_field",
) -> None:
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
                    raise ValueError(error_code)
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


def _audit_authorized_repair_preservation(
    *,
    damaged_ifc_path: Path | str,
    repaired_ifc_path: Path | str,
    changeset: Mapping[str, Any],
    application: Mapping[str, Any],
    damaged_model: Any,
    repaired_model: Any,
) -> None:
    """Apply the registered operation adapters to the complete ChangeSet once."""

    try:
        level = evaluate_independent_l1(
            damaged_ifc_path=damaged_ifc_path,
            repaired_ifc_path=repaired_ifc_path,
            changeset=changeset,
            application_result=application,
            registry=create_default_registry(),
            reopened_models=(
                (damaged_model, None),
                (repaired_model, None),
            ),
        )
    except Exception as error:
        raise ValueError(
            "proof.global_preservation:not_evaluable:"
            + type(error).__name__
        ) from error
    if level.status is EvaluationStatus.PASSED:
        for operation in changeset.get("operations", ()):
            if (
                isinstance(operation, Mapping)
                and operation.get("operation_type")
                == "set_occurrence_properties"
            ):
                _audit_occurrence_property_exact_delta(
                    operation=operation,
                    damaged_model=damaged_model,
                    repaired_model=repaired_model,
                )
        if unreachable_non_root_fingerprint_multiset(
            damaged_model
        ) != unreachable_non_root_fingerprint_multiset(repaired_model):
            raise ValueError(
                "proof.global_preservation:nonroot_orphan_delta"
            )
        return
    failed = sorted(
        f"{check.check_id}={check.status.value}"
        for check in level.checks
        if check.status
        not in {EvaluationStatus.PASSED, EvaluationStatus.NOT_REQUIRED}
    )
    raise ValueError(
        "proof.global_preservation:"
        + (",".join(failed) if failed else level.status.value)
    )


def _audit_occurrence_property_exact_delta(
    *,
    operation: Mapping[str, Any],
    damaged_model: Any,
    repaired_model: Any,
) -> None:
    target_id = str(operation.get("target", {}).get("element_global_id") or "")
    before_target = _optional_guid(damaged_model, target_id)
    after_target = _optional_guid(repaired_model, target_id)
    if (
        before_target is None
        or after_target is None
        or before_target.is_a() != after_target.is_a()
        or _root_attributes_fingerprint(before_target)
        != _root_attributes_fingerprint(after_target)
    ):
        raise ValueError("proof.global_preservation:property_target")
    assignments_by_set: dict[str, dict[str, Mapping[str, Any]]] = {}
    for assignment in operation.get("semantic_assignments", ()):
        if not isinstance(assignment, Mapping):
            raise ValueError("proof.global_preservation:property_assignment")
        fact_key = str(assignment.get("fact_key") or "")
        if not fact_key.startswith("pset:") or "." not in fact_key:
            raise ValueError("proof.global_preservation:property_assignment")
        set_name, property_name = fact_key.removeprefix("pset:").split(".", 1)
        if (
            not set_name
            or not property_name
            or assignment.get("source_fact_key") != fact_key
            or assignment.get("ownership") != "occurrence_direct"
            or assignment.get("authoring_action") != "set_occurrence_pset"
            or property_name in assignments_by_set.setdefault(set_name, {})
        ):
            raise ValueError("proof.global_preservation:property_assignment")
        assignments_by_set[set_name][property_name] = assignment
    if not assignments_by_set:
        raise ValueError("proof.global_preservation:property_assignment")
    for set_name, assignments in assignments_by_set.items():
        before_relations = _direct_occurrence_pset_relations(
            before_target, set_name=set_name
        )
        after_relations = _direct_occurrence_pset_relations(
            after_target, set_name=set_name
        )
        if len(before_relations) > 1 or len(after_relations) != 1:
            raise ValueError("proof.global_preservation:property_pset_cardinality")
        after_relation = after_relations[0]
        after_pset = after_relation.RelatingPropertyDefinition
        if tuple(str(item.GlobalId) for item in after_relation.RelatedObjects) != (
            target_id,
        ):
            raise ValueError("proof.global_preservation:property_relation_scope")
        before_pset = (
            before_relations[0].RelatingPropertyDefinition
            if before_relations
            else None
        )
        if before_pset is None:
            if set(_property_map(after_pset)) != set(assignments):
                raise ValueError("proof.global_preservation:property_created_pset")
        else:
            before_relation = before_relations[0]
            if len(tuple(before_relation.RelatedObjects)) != 1:
                raise ValueError("proof.global_preservation:property_shared_pset")
            if (
                str(before_relation.GlobalId) != str(after_relation.GlobalId)
                or str(before_pset.GlobalId) != str(after_pset.GlobalId)
                or _root_attributes_fingerprint(
                    before_relation, exclude=frozenset()
                )
                != _root_attributes_fingerprint(
                    after_relation, exclude=frozenset()
                )
                or _root_attributes_fingerprint(
                    before_pset, exclude=frozenset({"HasProperties"})
                )
                != _root_attributes_fingerprint(
                    after_pset, exclude=frozenset({"HasProperties"})
                )
            ):
                raise ValueError("proof.global_preservation:property_pset_identity")
            before_properties = _property_map(before_pset)
            after_properties = _property_map(after_pset)
            if set(after_properties) != set(before_properties) | set(assignments):
                raise ValueError("proof.global_preservation:property_member_set")
            for property_name, before_property in before_properties.items():
                after_property = after_properties[property_name]
                if property_name in assignments:
                    if _entity_attributes_fingerprint(
                        before_property,
                        exclude=frozenset({"NominalValue", "Unit"}),
                    ) != _entity_attributes_fingerprint(
                        after_property,
                        exclude=frozenset({"NominalValue", "Unit"}),
                    ):
                        raise ValueError(
                            "proof.global_preservation:property_member_metadata"
                        )
                elif _entity_attributes_fingerprint(
                    before_property, exclude=frozenset()
                ) != _entity_attributes_fingerprint(
                    after_property, exclude=frozenset()
                ):
                    raise ValueError(
                        "proof.global_preservation:property_member_undeclared"
                    )
        after_properties = _property_map(after_pset)
        for property_name, assignment in assignments.items():
            prop = after_properties.get(property_name)
            nominal = None if prop is None else getattr(prop, "NominalValue", None)
            actual_value = None if nominal is None else nominal.wrappedValue
            actual_type = None if nominal is None else nominal.is_a()
            if (
                prop is None
                or actual_type != assignment.get("value_type")
                or actual_value != assignment.get("value")
                or getattr(prop, "Unit", None) is not None
                and assignment.get("unit") is None
            ):
                raise ValueError("proof.global_preservation:property_value")


def _direct_occurrence_pset_relations(
    target: Any,
    *,
    set_name: str,
) -> tuple[Any, ...]:
    return tuple(
        relation
        for relation in getattr(target, "IsDefinedBy", ())
        if relation.is_a("IfcRelDefinesByProperties")
        and relation.RelatingPropertyDefinition.is_a("IfcPropertySet")
        and str(relation.RelatingPropertyDefinition.Name or "") == set_name
    )


def _property_map(pset: Any) -> dict[str, Any]:
    properties = tuple(getattr(pset, "HasProperties", ()))
    mapped = {str(item.Name or ""): item for item in properties}
    if len(mapped) != len(properties) or any(not name for name in mapped):
        raise ValueError("proof.global_preservation:property_member_identity")
    return mapped


def _root_attributes_fingerprint(
    entity: Any,
    *,
    exclude: frozenset[str] = frozenset(),
) -> tuple[Any, ...]:
    return _entity_attributes_fingerprint(entity, exclude=exclude)


def _entity_attributes_fingerprint(
    entity: Any,
    *,
    exclude: frozenset[str],
) -> tuple[Any, ...]:
    return tuple(
        (
            entity.attribute_name(index),
            _ifc_value_fingerprint(entity[index], seen=set(), depth=0),
        )
        for index in range(len(entity))
        if entity.attribute_name(index) not in exclude
    )


def _audit_r1_exact_operation_set(
    *,
    changeset: Mapping[str, Any],
    profile: Mapping[str, Any],
) -> None:
    """Bind every successful ChangeSet to the exact frozen operation family set."""

    operations = tuple(
        operation
        for operation in changeset.get("operations", ())
        if isinstance(operation, Mapping)
    )
    operation_ids = [str(operation.get("operation_id") or "") for operation in operations]
    if (
        not operation_ids
        or any(not operation_id for operation_id in operation_ids)
        or len(set(operation_ids)) != len(operation_ids)
    ):
        raise ValueError("proof.changeset.operation_set:operation_id")
    predicates = tuple(
        predicate
        for predicate in profile.get("artifact_predicates", ())
        if isinstance(predicate, Mapping)
    )
    atomic = [
        predicate
        for predicate in predicates
        if predicate.get("kind") == "atomic_operation_set"
    ]
    if len(atomic) > 1:
        raise ValueError("proof.changeset.operation_set:profile_atomic")
    inferred = [
        str(predicate.get("operation_type") or "")
        for predicate in predicates
        if predicate.get("kind") == "structural_add"
    ]
    inferred.extend(
        "set_occurrence_properties"
        for predicate in predicates
        if predicate.get("kind") == "occurrence_property"
    )
    expected = (
        [str(value) for value in atomic[0].get("operation_types", ())]
        if atomic
        else inferred
    )
    if (
        not expected
        or any(not operation_type for operation_type in expected)
        or (atomic and inferred and Counter(expected) != Counter(inferred))
        or Counter(
            str(operation.get("operation_type") or "") for operation in operations
        )
        != Counter(expected)
        or len(operations) != len(expected)
    ):
        raise ValueError("proof.changeset.operation_set")


def _audit_r1_initial_target_resolution_replay(
    *,
    source_ifc_path: Path | str,
    initial_intent: Mapping[str, Any],
    retained_offered_identities: Iterable[str],
    selected_identity: str,
    expected_selected_identity: str,
    scratch_root: Path | str,
) -> dict[str, Any]:
    """Replay H3 target ambiguity without trusting token/rank/terminal summaries."""

    try:
        parsed_intent = RepairIntent.from_dict(
            initial_intent,
            registry=create_default_registry(),
        )
    except Exception as error:
        raise ValueError("proof.h3.initial_intent") from error
    scratch = Path(scratch_root)
    scratch.mkdir(parents=True, exist_ok=True)
    index_path = scratch / "h3-target-replay.sqlite"
    try:
        metadata = build_ifc_index(source_ifc_path, index_path)
        with SQLiteIndexRepository.open(index_path) as repository:
            replayed = resolve_repair_intent(
                parsed_intent,
                repository,
                expected_source_sha256=metadata.source_ifc_sha256,
                operation_registry=create_default_registry(),
            )
    except Exception as error:
        raise ValueError("proof.h3.initial_resolution:not_evaluable") from error
    if replayed.status != "clarification_required" or replayed.reason_code != "ambiguous":
        raise ValueError("proof.h3.initial_resolution")
    recomputed = {
        _stable_target_identity(candidate)
        for candidate in replayed.candidates
        if isinstance(candidate, Mapping)
    }
    retained = {str(value) for value in retained_offered_identities}
    if not recomputed or retained != recomputed:
        raise ValueError("proof.h3.offered_identity_set")
    selected = str(selected_identity)
    expected = str(expected_selected_identity)
    if selected != expected or selected not in retained or selected not in recomputed:
        raise ValueError("proof.h3.selected_identity")
    return {
        "status": replayed.status,
        "reason_code": replayed.reason_code,
        "offered_identities": sorted(recomputed),
        "selected_identity": selected,
    }


def _stable_target_identity(candidate: Mapping[str, Any]) -> str:
    ifc_class = str(candidate.get("ifc_class") or "")
    public_id = str(candidate.get("public_id") or "")
    if public_id.startswith("ifc:"):
        public_id = public_id.removeprefix("ifc:")
    if not ifc_class or not public_id or public_id.startswith("candidate:"):
        raise ValueError("proof.h3.candidate_identity")
    return f"{ifc_class}:{public_id}"


def _audit_r1_h3_state_selection(
    *,
    state: Mapping[str, Any] | Any,
    expected_selected_identity: str,
) -> dict[str, Any]:
    """Bind a transient clarification token to the retained stable identity set."""

    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    if state_document.get("stage") != "succeeded":
        raise ValueError("proof.h3.state_terminal")
    transitions = tuple(
        item
        for item in state_document.get("transitions", ())
        if isinstance(item, Mapping)
    )
    clarifications = [
        item
        for item in transitions
        if item.get("from_stage") == "intent_ready"
        and item.get("to_stage") == "clarification_required"
        and item.get("reason_code") == "ambiguous_target"
        and isinstance(item.get("clarification"), Mapping)
        and item["clarification"].get("reason_code") == "ambiguous_target"
    ]
    if len(clarifications) != 1:
        raise ValueError("proof.h3.clarification_lineage")
    clarification = clarifications[0]
    candidates = tuple(
        item
        for item in clarification["clarification"].get("candidates", ())
        if isinstance(item, Mapping)
    )
    token_to_identity: dict[str, str] = {}
    for candidate in candidates:
        token = str(candidate.get("token") or "")
        if not token or token in token_to_identity:
            raise ValueError("proof.h3.candidate_token")
        token_to_identity[token] = _stable_target_identity(candidate)
    offered_identities = set(token_to_identity.values())
    if not offered_identities or len(offered_identities) != len(token_to_identity):
        raise ValueError("proof.h3.offered_identity_set")

    clarification_index = transitions.index(clarification)
    forbidden_pre_clarification_stages = {
        "targets_resolved",
        "changeset_ready",
        "application_ready",
        "evaluated",
        "succeeded",
    }
    for transition in transitions[: clarification_index + 1]:
        if str(transition.get("to_stage") or "") in forbidden_pre_clarification_stages:
            raise ValueError("proof.h3.pre_mutation")
        result_artifacts = transition.get("result_artifacts")
        if isinstance(result_artifacts, Mapping) and result_artifacts:
            raise ValueError("proof.h3.pre_mutation")
    resumes = [
        item
        for item in transitions[clarification_index + 1 :]
        if item.get("from_stage") == "clarification_required"
        and item.get("to_stage") == "intent_ready"
        and isinstance(item.get("answer"), Mapping)
        and item["answer"].get("kind") == "select_candidate"
    ]
    if len(resumes) != 1:
        raise ValueError("proof.h3.resume_lineage")
    selected_token = str(resumes[0]["answer"].get("candidate_token") or "")
    selected_identity = token_to_identity.get(selected_token)
    if (
        selected_identity is None
        or selected_identity != str(expected_selected_identity)
        or selected_identity not in offered_identities
    ):
        raise ValueError("proof.h3.selected_identity")
    return {
        "offered_identities": sorted(offered_identities),
        "selected_identity": selected_identity,
        "clarification_transition_id": clarification.get("transition_id"),
        "operation_id": clarification["clarification"].get("operation_id"),
        "run_id": str(state_document.get("run_id") or ""),
    }


def _audit_r1_h3_final_target_resolution_replay(
    *,
    source_ifc_path: Path,
    initial_intent: Mapping[str, Any],
    state: Mapping[str, Any] | Any,
    expected_selected_identity: str,
    scratch_root: Path,
) -> dict[str, Any]:
    """Project H3's stable selection into an intent copy and replay final resolution."""

    lineage = _audit_r1_h3_state_selection(
        state=state,
        expected_selected_identity=expected_selected_identity,
    )
    initial_replay = _audit_r1_initial_target_resolution_replay(
        source_ifc_path=source_ifc_path,
        initial_intent=initial_intent,
        retained_offered_identities=lineage["offered_identities"],
        selected_identity=str(lineage["selected_identity"]),
        expected_selected_identity=expected_selected_identity,
        scratch_root=scratch_root,
    )
    selected_class, separator, selected_global_id = str(
        lineage["selected_identity"]
    ).partition(":")
    operation_id = str(lineage.get("operation_id") or "")
    projected = json.loads(json.dumps(dict(initial_intent), ensure_ascii=False))
    matching_operations = [
        operation
        for operation in projected.get("operations", ())
        if isinstance(operation, dict)
        and str(operation.get("operation_id") or "") == operation_id
    ]
    if not separator or not selected_global_id or len(matching_operations) != 1:
        raise ValueError("proof.h3.selected_identity")
    query = matching_operations[0].get("target_query")
    allowed = query.get("allowed_ifc_classes") if isinstance(query, Mapping) else None
    if not isinstance(allowed, list) or selected_class not in allowed:
        raise ValueError("proof.h3.selected_identity")
    matching_operations[0]["target_query"] = {
        key: value
        for key, value in query.items()
        if key
        in {
            "schema_version",
            "allowed_ifc_classes",
            "max_candidates",
            "winner_margin",
        }
    }
    matching_operations[0]["target_query"]["global_id"] = selected_global_id

    scratch_root.mkdir(parents=True, exist_ok=True)
    index_path = scratch_root / "final-target-index.sqlite"
    build_ifc_index(source_ifc_path, index_path)
    with SQLiteIndexRepository.open(index_path) as repository:
        resolution = resolve_target(
            repository,
            TargetQuery.from_dict(matching_operations[0]["target_query"]),
        )
        selected_record = repository.get_by_global_id(selected_global_id)
    if (
        resolution.status != "resolved"
        or selected_record is None
        or resolution.resolved_target_id != selected_record.record_id
        or selected_record.ifc_class != selected_class
    ):
        raise ValueError("proof.h3.final_resolution")
    return {
        "status": resolution.status,
        "resolved_identity": f"{selected_record.ifc_class}:{selected_global_id}",
        "projected_intent": projected,
        "initial_replay": initial_replay,
    }


def _audit_r1_unsupported_guard_replay(
    *,
    intent: Mapping[str, Any],
    state: Mapping[str, Any] | Any,
    expected_supported_capabilities: Iterable[str],
    expected_unsupported_capabilities: Iterable[str],
    expected_reason_code: str,
    attempts: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Recompute H4 routing and prove the retained run stopped pre-mutation."""

    registry = create_default_registry()
    try:
        parsed = RepairIntent.from_dict(intent, registry=registry)
    except Exception as error:
        raise ValueError("proof.h4.stage1_intent") from error
    expected_supported = sorted(str(value) for value in expected_supported_capabilities)
    expected_unsupported = sorted(
        str(value) for value in expected_unsupported_capabilities
    )
    supported = sorted(
        operation.operation_type
        for operation in parsed.operations
        if str(registry.assess_intent_capability(operation.to_dict()).get("status"))
        != "unsupported"
    )
    unsupported_capabilities = sorted(
        request.capability_id for request in parsed.unsupported_requests
    )
    unsupported = _unsupported_operations(parsed, registry)
    reason_codes = {str(item.get("reason_code") or "") for item in unsupported}
    if unsupported_capabilities != expected_unsupported or not unsupported:
        raise ValueError("proof.h4.unsupported_request")
    if supported != expected_supported:
        raise ValueError("proof.h4.supported_capability")
    if reason_codes != {str(expected_reason_code)}:
        raise ValueError("proof.h4.reason_code")

    state_document = (
        state.to_dict() if hasattr(state, "to_dict") else dict(state)
    )
    transitions = tuple(
        item
        for item in state_document.get("transitions", ())
        if isinstance(item, Mapping)
    )
    if (
        state_document.get("stage") != "unsupported"
        or state_document.get("reason_code") != expected_reason_code
        or not transitions
        or transitions[-1].get("to_stage") != "unsupported"
        or transitions[-1].get("reason_code") != expected_reason_code
    ):
        raise ValueError("proof.h4.state_terminal")
    forbidden_stages = {
        "targets_resolved",
        "changeset_ready",
        "application_ready",
        "evaluated",
        "succeeded",
    }
    if any(str(item.get("to_stage") or "") in forbidden_stages for item in transitions):
        raise ValueError("proof.h4.pre_mutation")
    result_artifacts: list[tuple[str, str]] = []
    for document in (*transitions, state_document):
        artifacts = document.get("result_artifacts", {})
        if isinstance(artifacts, Mapping):
            result_artifacts.extend(
                (str(key), str(value)) for key, value in artifacts.items()
            )
    forbidden_artifact_keys = {
        "successful_ifc",
        "repaired_ifc",
        "diagnostic_candidate",
        "candidate_ifc",
    }
    if any(
        key in forbidden_artifact_keys or value.casefold().endswith(".ifc")
        for key, value in result_artifacts
    ):
        raise ValueError("proof.h4.pre_mutation")
    retained_attempts = tuple(
        item for item in attempts if isinstance(item, Mapping)
    )
    stages = [str(item.get("stage") or "") for item in retained_attempts]
    if not stages or any(stage != "stage1" for stage in stages):
        raise ValueError("proof.h4.attempt_stage")
    return {
        "supported_capabilities": supported,
        "unsupported_capabilities": unsupported_capabilities,
        "atomic_request": bool(supported and unsupported_capabilities),
        "stage1_attempts": len(stages),
        "property_resolution_attempts": 0,
        "stage2_attempts": 0,
        "apply_attempts": 0,
        "published_outputs": [],
        "reason_code": expected_reason_code,
    }


def _r1_expected_stage1_profiles() -> list[dict[str, Any]]:
    registry = create_default_registry()
    profile_ids = sorted(
        {
            str(registry.require(operation_type).prompt_profile_id)
            for operation_type in registry.operation_types
        }
    )
    return compact_profile_catalog(
        load_prompt_profiles(),
        include_profile_ids=profile_ids,
    )


def _audit_r1_live_provider_provenance(
    *,
    case_id: str,
    roles: Mapping[str, Path],
    provider_intent: Mapping[str, Any],
    initial_provider_intent: Mapping[str, Any] | None = None,
    changeset: Mapping[str, Any] | None,
    damaged_sha256: str,
    validated_state: Mapping[str, Any] | Any | None = None,
) -> dict[str, Any]:
    """Reuse the stage-aware Plan 07 auditor for one frozen R1 case."""

    try:
        from scripts.ifc_repair.curate_phase12_live_proof import (
            _bind_stage1,
            _bind_stage2,
            _response_document,
            audit_live_attempts,
        )
    except ModuleNotFoundError:  # Direct script execution.
        from curate_phase12_live_proof import (  # type: ignore[no-redef]
            _bind_stage1,
            _bind_stage2,
            _response_document,
            audit_live_attempts,
        )

    result = _read_json(_require_r1_role(roles, "live_provider_result"))
    case_result = _read_json(
        _require_r1_role(roles, "live_provider_case_result")
    )
    matching = [
        item
        for item in result.get("cases", ())
        if isinstance(item, Mapping) and item.get("case_id") == case_id
    ]
    if len(matching) != 1 or dict(matching[0]) != case_result:
        raise ValueError("proof.live.case_result_binding")
    if (
        result.get("evidence_mode") != "live"
        or result.get("provider_evidence_mode") != "live"
        or result.get("execution_mode") != "production_live"
        or result.get("synthetic_fallback_used") is not False
        or case_result.get("synthetic_fallback_used") is not False
        or case_result.get("private_evidence_detected") is not False
    ):
        raise ValueError("proof.live.production_mode")
    if validated_state is None:
        raise ValueError("proof.live.case_result_state_binding")
    _audit_r1_case_result_state_binding(
        case_result=case_result,
        validated_state=validated_state,
    )

    natural_claim_count = _natural_property_claim_count(provider_intent)
    expected_stage15 = (
        {
            "template_id": PROPERTY_RESOLUTION_TEMPLATE_ID,
            "template_hash": PROPERTY_RESOLUTION_TEMPLATE_HASH,
        }
        if natural_claim_count
        else None
    )
    expected_stage2: Mapping[str, Any] | None = None
    provider_draft: Mapping[str, Any] | None = None
    if changeset is not None:
        operation_types = {
            str(item.get("operation_type") or "")
            for item in changeset.get("operations", ())
            if isinstance(item, Mapping)
        }
        registry = create_default_registry()
        expected_stage2 = select_prompt_profiles(
            sorted(
                {
                    str(registry.require(operation_type).prompt_profile_id)
                    for operation_type in operation_types
                }
            )
        ).to_dict()
        selection_path = _require_r1_role(
            roles, "live_prompt_profile_selection"
        )
        if _read_json(selection_path) != expected_stage2:
            raise ValueError("proof.live.prompt_profile_selection")
        provider_draft = _read_json(
            _require_r1_role(roles, "live_provider_draft")
        )

    state_document = (
        validated_state.to_dict()
        if hasattr(validated_state, "to_dict")
        else dict(validated_state or {"transitions": []})
    )
    expected_rounds = _r1_expected_live_attempt_rounds(
        state=state_document,
        property_resolution_expected=expected_stage15 is not None,
        stage2_expected=expected_stage2 is not None,
    )
    attempts = case_result.get("attempts")
    try:
        audit = audit_live_attempts(
            case_id=case_id,
            raw_attempts=attempts,
            expected_stage1_profiles=_r1_expected_stage1_profiles(),
            expected_stage2_selection=expected_stage2,
            expected_property_resolution_template=expected_stage15,
            expected_provider="deepseek-openai-compatible",
            expected_model="deepseek-v4-flash",
            expected_evidence_mode="live",
            expected_thinking={"type": "enabled"},
            expected_rounds=expected_rounds,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"proof.live.attempts:{error}") from error
    retained_attempts = [
        item for item in attempts if isinstance(item, Mapping)
    ] if isinstance(attempts, list) else []
    resume_stage1_expected = any(
        round_contract["lineage"] == "clarification-resume"
        and "stage1" in round_contract["stages"]
        for round_contract in expected_rounds
    )
    if resume_stage1_expected and initial_provider_intent is None:
        raise ValueError("proof.live.stage1_binding:initial_intent_required")
    expected_stage1_intents = {
        "initial": initial_provider_intent or provider_intent,
    }
    if resume_stage1_expected:
        expected_stage1_intents["clarification-resume"] = provider_intent
    _audit_r1_stage1_round_bindings(
        attempts=retained_attempts,
        response_document=_response_document,
        expected_intents_by_lineage=expected_stage1_intents,
    )
    if expected_stage15 is not None:
        _audit_r1_stage15_attempt_binding(
            roles=roles,
            attempts=retained_attempts,
            response_document=_response_document,
            provider_intent=provider_intent,
            state=(validated_state if validated_state is not None else {"transitions": []}),
        )
    if changeset is not None:
        assert provider_draft is not None
        stage2_attempts = [
            item for item in retained_attempts if item.get("stage") == "stage2"
        ]
        if not stage2_attempts:
            raise ValueError("proof.live.stage2_response")
        try:
            _bind_stage2(
                _response_document(stage2_attempts[-1]), provider_draft
            )
            _bind_stage2(provider_draft, changeset)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"proof.live.stage2_binding:{error}") from error
    _audit_r1_production_input_isolation(
        roles=roles,
        damaged_sha256=damaged_sha256,
        request_sha256=str(provider_intent.get("source_request_hash") or ""),
        resolved_target_count=(
            0
            if changeset is None
            else len(
                [
                    item
                    for item in changeset.get("operations", ())
                    if isinstance(item, Mapping)
                ]
            )
        ),
    )
    return {**audit, "attempts": retained_attempts}


def _audit_r1_case_result_state_binding(
    *,
    case_result: Mapping[str, Any],
    validated_state: Mapping[str, Any] | Any,
) -> None:
    """Bind the retained live terminal summary to the hash-valid RunStore state."""

    state_document = (
        validated_state.to_dict()
        if hasattr(validated_state, "to_dict")
        else dict(validated_state)
    )
    final = case_result.get("final")
    if not isinstance(final, Mapping):
        raise ValueError("proof.live.case_result_state_binding")
    succeeded = state_document.get("stage") == "succeeded"
    expected = {
        "run_id": state_document.get("run_id"),
        "state_version": state_document.get("state_version"),
        "status": state_document.get("stage"),
        "reason_code": state_document.get("reason_code"),
        "complete_repair_success": succeeded,
        "successful_artifact_publishable": succeeded,
        "artifacts": dict(state_document.get("result_artifacts") or {}),
    }
    if any(final.get(key) != value for key, value in expected.items()):
        raise ValueError("proof.live.case_result_state_binding")


def _audit_r1_h4_no_mutation_artifacts(
    *,
    roles: Mapping[str, Path],
    source_ifc_path: Path,
    validated_state: Mapping[str, Any] | Any,
) -> None:
    """Prove H4 retained no candidate IFC, ChangeSet, or application output."""

    terminal_error = "proof.h4.failure_terminal_evidence"
    state_document = (
        validated_state.to_dict()
        if hasattr(validated_state, "to_dict")
        else dict(validated_state)
    )
    source = source_ifc_path.resolve()
    retained_ifc = {
        path.resolve()
        for path in roles.values()
        if path.suffix.casefold() == ".ifc"
    }
    if retained_ifc != {source}:
        raise ValueError("proof.h4.no_mutation_artifacts")
    state_path = _require_r1_role(roles, "runtime_state").resolve()
    run_root = state_path.parent
    result_artifacts = state_document.get("result_artifacts")
    if not isinstance(result_artifacts, Mapping) or set(result_artifacts) != {
        "manifest",
        "evaluation",
        "evidence",
    }:
        raise ValueError("proof.h4.no_mutation_artifacts")
    listed = {path.resolve() for path in roles.values()}
    retained_terminal: dict[str, Path] = {}
    for name, relative in result_artifacts.items():
        artifact = _safe_path(run_root, str(relative)).resolve()
        if artifact not in listed or not artifact.is_file():
            raise ValueError("proof.h4.no_mutation_artifacts")
        retained_terminal[str(name)] = artifact

    try:
        runtime_result = RunStore(run_root.parent.parent).read_result(run_root.name)
    except Exception as error:
        raise ValueError(terminal_error) from error
    if (
        state_document.get("stage") != "unsupported"
        or runtime_result.run_id != state_document.get("run_id")
        or runtime_result.state_version != state_document.get("state_version")
        or runtime_result.status != state_document.get("stage")
        or runtime_result.reason_code != state_document.get("reason_code")
        or runtime_result.complete_repair_success is not False
        or runtime_result.successful_artifact_publishable is not False
        or dict(runtime_result.artifacts) != dict(result_artifacts)
    ):
        raise ValueError(terminal_error)
    case_result = _read_json(
        _require_r1_role(roles, "live_provider_case_result")
    )
    try:
        _audit_r1_case_result_state_binding(
            case_result=case_result,
            validated_state=validated_state,
        )
    except ValueError as error:
        raise ValueError(terminal_error) from error

    transitions = [
        item
        for item in state_document.get("transitions", ())
        if isinstance(item, Mapping)
    ]
    final_transition = transitions[-1] if transitions else None
    reason_code = state_document.get("reason_code")
    if (
        not isinstance(final_transition, Mapping)
        or final_transition.get("to_stage") != "unsupported"
        or final_transition.get("reason_code") != reason_code
        or dict(final_transition.get("result_artifacts") or {})
        != dict(result_artifacts)
    ):
        raise ValueError(terminal_error)

    manifest = _read_json(retained_terminal["manifest"])
    entries = manifest.get("artifacts")
    if (
        manifest.get("schema_version")
        != "text2ifc/ifc-repair-artifact-manifest/0.1"
        or not isinstance(entries, list)
        or len(entries) != 2
    ):
        raise ValueError(terminal_error)
    expected_entries = {
        retained_terminal["evaluation"]: "public_evaluation",
        retained_terminal["evidence"]: "public_evidence",
    }
    seen_entries: set[Path] = set()
    evidence_path = retained_terminal["evidence"]
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {
            "path",
            "sha256",
            "size_bytes",
            "role",
        }:
            raise ValueError(terminal_error)
        try:
            entry_path = _safe_path(
                run_root, str(entry.get("path") or "")
            ).resolve()
        except (OSError, ValueError) as error:
            raise ValueError(terminal_error) from error
        if (
            entry_path in seen_entries
            or expected_entries.get(entry_path) != entry.get("role")
            or _normalize_sha256(str(entry.get("sha256") or ""))
            != _sha256(entry_path)
            or int(entry.get("size_bytes", -1)) != entry_path.stat().st_size
        ):
            raise ValueError(terminal_error)
        seen_entries.add(entry_path)
    if seen_entries != set(expected_entries):
        raise ValueError(terminal_error)

    evidence_document = _read_json(evidence_path)
    public_evidence = evidence_document.get("evidence")
    evaluation_document = _read_json(retained_terminal["evaluation"])
    final = case_result.get("final")
    expected_evaluation = {
        "schema_version": "text2ifc/ifc-repair-evaluation-public/0.2",
        "policy_version": "phase8.1",
        "status": "not_evaluable",
        "reason": reason_code,
        "complete_repair_success": False,
        "successful_artifact_publishable": False,
        "diagnostic_artifact_retained": False,
        "application": {
            "check_id": "application.valid",
            "status": "not_evaluable",
            "reason": reason_code,
        },
        "preservation": {
            "check_id": "preservation.valid",
            "status": "not_evaluable",
            "reason": reason_code,
        },
        "operations": [],
    }
    if (
        evidence_document.get("terminal_status") != "unsupported"
        or not isinstance(public_evidence, Mapping)
        or not isinstance(final, Mapping)
        or set(public_evidence) != {"reason_code", "stage"}
        or public_evidence.get("reason_code") != reason_code
        or public_evidence.get("stage") != final_transition.get("from_stage")
        or final.get("reason_code") != reason_code
        or evaluation_document != expected_evaluation
    ):
        raise ValueError(terminal_error)

    for path in listed:
        if path.suffix.casefold() != ".json" or not path.is_file():
            continue
        document = _read_json(path)
        schema_version = str(document.get("schema_version") or "")
        if schema_version.startswith("text2ifc/ifc-repair-changeset") or {
            "valid",
            "published",
            "operations",
        }.issubset(document):
            raise ValueError("proof.h4.no_mutation_artifacts")


def _r1_expected_live_attempt_rounds(
    *,
    state: Mapping[str, Any] | Any,
    property_resolution_expected: bool,
    stage2_expected: bool,
) -> list[dict[str, Any]]:
    """Derive the exact R1 Provider lineage from retained clarification state."""

    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    answers = [
        transition.get("answer")
        for transition in state_document.get("transitions", ())
        if isinstance(transition, Mapping)
        and isinstance(transition.get("answer"), Mapping)
    ]
    add_detail = [answer for answer in answers if answer.get("kind") == "add_detail"]
    select_target = [
        answer for answer in answers if answer.get("kind") == "select_candidate"
    ]
    if len(add_detail) > 1 or len(select_target) > 1 or (add_detail and select_target):
        raise ValueError("proof.live.round_lineage")

    def _tail(*, include_stage1: bool) -> list[str]:
        stages = ["stage1"] if include_stage1 else []
        if property_resolution_expected:
            stages.append("property_resolution")
        if stage2_expected:
            stages.append("stage2")
        return stages

    if add_detail:
        initial = _tail(include_stage1=True)
        if stage2_expected:
            initial.remove("stage2")
        return [
            {"lineage": "initial", "stages": initial},
            {
                "lineage": "clarification-resume",
                "stages": _tail(include_stage1=True),
            },
        ]
    if select_target:
        resume = _tail(include_stage1=False)
        if not resume:
            raise ValueError("proof.live.round_lineage")
        return [
            {"lineage": "initial", "stages": ["stage1"]},
            {"lineage": "clarification-resume", "stages": resume},
        ]
    return [{"lineage": "initial", "stages": _tail(include_stage1=True)}]


def _audit_r1_stage1_round_bindings(
    *,
    attempts: Iterable[Mapping[str, Any]],
    response_document: Any,
    expected_intents_by_lineage: Mapping[str, Mapping[str, Any]],
) -> None:
    """Bind the authoritative Stage 1 response in every frozen R1 round."""

    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for attempt in attempts:
        if not isinstance(attempt, Mapping) or attempt.get("stage") != "stage1":
            continue
        lineage = str(attempt.get("lineage") or "")
        grouped.setdefault(lineage, []).append(attempt)
    if not expected_intents_by_lineage or set(grouped) != set(
        expected_intents_by_lineage
    ):
        raise ValueError("proof.live.stage1_binding")
    try:
        from scripts.ifc_repair.curate_phase12_live_proof import _bind_stage1
    except ModuleNotFoundError:  # Direct script execution.
        from curate_phase12_live_proof import _bind_stage1  # type: ignore[no-redef]
    for lineage, intent in expected_intents_by_lineage.items():
        try:
            document = response_document(grouped[lineage][-1])
            _bind_stage1(document, intent)
            if document.get("unsupported_requests", []) != intent.get(
                "unsupported_requests", []
            ):
                raise ValueError("LIVE_STAGE1_RESPONSE_ARTIFACT_MISMATCH")
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"proof.live.stage1_binding:{error}") from error


def _r1_transcript_response_text(response: Mapping[str, Any]) -> str | None:
    """Return the exact retained Provider text when the transport preserved it."""

    content = response.get("content")
    if isinstance(content, str):
        return content
    choices = response.get("choices")
    if isinstance(choices, list) and len(choices) == 1:
        choice = choices[0]
        message = choice.get("message") if isinstance(choice, Mapping) else None
        text = message.get("content") if isinstance(message, Mapping) else None
        if isinstance(text, str):
            return text
    if isinstance(content, Mapping):
        # Older retained fixtures stored the parsed document directly. Their
        # byte-level Provider text was not retained, so semantic equality is
        # checked below instead of inventing a serialization.
        return None
    raise ValueError("proof.live.property_attempt_raw_response")


def _audit_r1_stage15_attempt_binding(
    *,
    roles: Mapping[str, Path],
    attempts: Iterable[Mapping[str, Any]],
    response_document: Any,
    provider_intent: Mapping[str, Any],
    state: Mapping[str, Any] | Any,
) -> None:
    """Bind each transcript Stage 1.5 call to its case-local production evidence."""

    live_attempts = [
        item
        for item in attempts
        if isinstance(item, Mapping) and item.get("stage") == "property_resolution"
    ]
    listed = {path.resolve() for path in roles.values()}
    metadata_paths = [
        path.resolve()
        for path in listed
        if path.name == "provider-metadata.json"
        and "property-resolution" in path.parts
    ]
    if not live_attempts or len(metadata_paths) != len(live_attempts):
        raise ValueError("proof.live.property_attempt_binding")

    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    base_claims: set[tuple[str, str]] = set()
    for operation in provider_intent.get("operations", ()):
        if not isinstance(operation, Mapping):
            continue
        operation_id = str(operation.get("operation_id") or "")
        for property_index, claim in enumerate(
            operation.get("property_intents", ()), start=1
        ):
            if not isinstance(claim, Mapping) or claim.get("intent_kind") != "natural_language_property":
                continue
            base_claim = f"claim-{property_index:03d}"
            base_claims.add((operation_id, base_claim))
    resume_generations = [
        transition.get("stage_payload", {}).get("property_resolution_generation")
        for transition in state_document.get("transitions", ())
        if isinstance(transition, Mapping)
        and isinstance(transition.get("answer"), Mapping)
        and transition["answer"].get("kind") == "add_detail"
        and isinstance(transition.get("stage_payload"), Mapping)
    ]
    if any(not isinstance(item, int) for item in resume_generations) or len(resume_generations) > 1:
        raise ValueError("proof.live.property_claim_authority")
    expected_claims = set(base_claims)
    if resume_generations:
        generation = int(resume_generations[0])
        expected_claims.update(
            (operation_id, f"{claim_id}-resume-{generation:03d}")
            for operation_id, claim_id in base_claims
        )
    decision_claims: set[tuple[str, str]] = set()
    for transition in state_document.get("transitions", ()):
        if not isinstance(transition, Mapping):
            continue
        payload = transition.get("stage_payload")
        resolution = payload.get("property_resolution") if isinstance(payload, Mapping) else None
        if isinstance(resolution, Mapping) and resolution.get("checkpoint") == "decision":
            decision_claims.add(
                (str(resolution.get("operation_id") or ""), str(resolution.get("claim_id") or ""))
            )
    if state_document.get("transitions") and decision_claims != expected_claims:
        raise ValueError("proof.live.property_claim_checkpoint_set")
    for operation_id, claim_id in expected_claims:
        base_claim_id = claim_id.split("-resume-", 1)[0]
        if (operation_id, base_claim_id) not in base_claims:
            raise ValueError("proof.live.property_claim_authority")
        if "-resume-" in claim_id and claim_id != _r1_effective_property_claim_id(
            state=state_document,
            base_claim_id=base_claim_id,
        ):
            raise ValueError("proof.live.property_claim_authority")

    used_attempt_ids: set[str] = set()
    retained_groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for metadata_path in metadata_paths:
        attempt_root = metadata_path.parent
        required = {
            "metadata": metadata_path,
            "raw": (attempt_root / "raw-response.json").resolve(),
            "parsed": (attempt_root / "parsed-response.json").resolve(),
            "prompt": (attempt_root / "rendered-prompt.txt").resolve(),
            "trace": (attempt_root / "trace.json").resolve(),
            "renderer_input": (attempt_root / "renderer-input.json").resolve(),
            "feedback": (attempt_root / "validation-feedback.json").resolve(),
        }
        if any(path not in listed or not path.is_file() for path in required.values()):
            raise ValueError("proof.live.property_attempt_binding")

        metadata = _read_json(required["metadata"])
        response_id = str(metadata.get("response_id") or "")
        matches = [
            item
            for item in live_attempts
            if isinstance(item.get("metadata"), Mapping)
            and item["metadata"].get("response_id") == response_id
        ]
        if len(matches) != 1:
            raise ValueError("proof.live.property_attempt_binding")
        attempt = matches[0]
        attempt_id = str(attempt.get("attempt_id") or "")
        if not attempt_id or attempt_id in used_attempt_ids:
            raise ValueError("proof.live.property_attempt_binding")
        used_attempt_ids.add(attempt_id)

        attempt_metadata = attempt.get("metadata")
        assert isinstance(attempt_metadata, Mapping)
        if any(
            metadata.get(key) != attempt_metadata.get(key)
            for key in (
                "response_id",
                "provider",
                "model",
                "evidence_class",
                "usage",
                "request_configuration",
            )
        ):
            raise ValueError("proof.live.property_attempt_binding")
        request = attempt.get("request")
        response = attempt.get("response")
        raw = _read_json(required["raw"])
        transport = raw.get("transport")
        trace = _read_json(required["trace"])
        if (
            not isinstance(request, Mapping)
            or not isinstance(response, Mapping)
            or not isinstance(transport, Mapping)
            or transport.get("request") != request
            or transport.get("response") != response
        ):
            raise ValueError("proof.live.property_attempt_binding")
        transcript_text = _r1_transcript_response_text(response)
        if transcript_text is not None and raw.get("text") != transcript_text:
            raise ValueError("proof.live.property_attempt_raw_response")
        messages = request.get("messages")
        if (
            not isinstance(messages, list)
            or not messages
            or not isinstance(messages[0], Mapping)
            or messages[0].get("content")
            != required["prompt"].read_text(encoding="utf-8")
        ):
            raise ValueError("proof.live.property_attempt_binding")
        try:
            retained_parsed = json.loads(
                required["parsed"].read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as error:
            raise ValueError("proof.live.property_attempt_binding") from error

        renderer_input = _read_json(required["renderer_input"])
        if set(renderer_input) != {
            "PROPERTY_QUERY",
            "CANDIDATE_SET",
            "DECISION_SCHEMA",
            "PREVIOUS_VALIDATION_FEEDBACK",
        }:
            raise ValueError("proof.live.property_attempt_renderer")
        candidate_set = renderer_input.get("CANDIDATE_SET")
        decision_schema = renderer_input.get("DECISION_SCHEMA")
        candidates = candidate_set.get("candidates") if isinstance(candidate_set, Mapping) else None
        if not isinstance(decision_schema, Mapping) or not isinstance(candidates, list):
            raise ValueError("proof.live.property_attempt_renderer")
        frozen_decision_schema = _read_json(
            ROOT / "schemas" / "agent" / "ifc-property-rerank-decision-0.1.schema.json"
        )
        if decision_schema != frozen_decision_schema:
            raise ValueError("proof.live.property_attempt_schema")
        claim_root = attempt_root.parents[1]
        query_path = (claim_root / "query.json").resolve()
        candidate_path = (claim_root / "candidate-set.json").resolve()
        if (
            query_path not in listed
            or candidate_path not in listed
            or not query_path.is_file()
            or not candidate_path.is_file()
            or renderer_input["PROPERTY_QUERY"] != _read_json(query_path)
            or candidate_set != _read_json(candidate_path)
        ):
            raise ValueError("proof.live.property_attempt_renderer")
        rendered = render_prompt(
            template_id=PROPERTY_RESOLUTION_TEMPLATE_ID,
            inputs=renderer_input,
        )
        if (
            str(rendered["text"])
            != required["prompt"].read_text(encoding="utf-8")
            or rendered["metadata"].get("template_id")
            != trace.get("template_id")
            or rendered["metadata"].get("template_hash")
            != trace.get("template_hash")
        ):
            raise ValueError("proof.live.property_attempt_renderer")
        query_document = renderer_input["PROPERTY_QUERY"]
        if (
            trace.get("run_id") != query_document.get("run_id")
            or trace.get("operation_id") != query_document.get("operation_id")
            or trace.get("claim_id") != query_document.get("claim_id")
            or trace.get("query_id") != query_document.get("query_id")
            or trace.get("candidate_set_id")
            != candidate_set.get("candidate_set_id")
            or candidate_set.get("query_id") != query_document.get("query_id")
        ):
            raise ValueError("proof.live.property_attempt_renderer")
        offered_ids = frozenset(
            str(candidate.get("candidate_id") or "")
            for candidate in candidates
            if isinstance(candidate, Mapping)
        )
        raw_text = str(raw.get("text") or "")
        provider_output = ProviderOutput(text=raw_text, metadata={})
        parse_status = "not_parsed"
        parsed: Mapping[str, Any] | None = None
        recomputed_issues: list[dict[str, str]] = []
        if (
            len(raw_text.encode("utf-8"))
            > MAX_PROPERTY_RESOLUTION_RESPONSE_BYTES
            or estimate_openai_compatible_input_tokens(raw_text)
            > MAX_PROPERTY_RESOLUTION_RESPONSE_TOKENS
        ):
            recomputed_issues.append(
                _property_issue(
                    "PROPERTY_PROVIDER_RESPONSE_TOO_LARGE",
                    "",
                    "Provider response exceeds the Property Resolution limit.",
                )
            )
        else:
            try:
                validate_provider_output(provider_output)
            except ProviderOutputError:
                recomputed_issues.append(
                    _property_issue(
                        "PROPERTY_PRIVATE_OUTPUT_FORBIDDEN",
                        "",
                        "Provider output violates the public structured-output boundary.",
                    )
                )
            if not recomputed_issues:
                parse_status, parsed_document, parse_issues = provider_output.parse_json()
                parsed = parsed_document
                recomputed_issues.extend(
                    _property_issue(
                        str(item.get("code", "PROPERTY_PROVIDER_JSON_INVALID")),
                        str(item.get("path", "")),
                        str(item.get("message", "Provider JSON is invalid.")),
                    )
                    for item in parse_issues
                )
                if (
                    parse_status == "ok"
                    and isinstance(parsed, Mapping)
                    and not recomputed_issues
                ):
                    recomputed_issues.extend(
                        _property_decision_issues(
                            parsed,
                            schema=decision_schema,
                            offered_ids=offered_ids,
                        )
                    )
        recomputed_issues = _sort_property_issues(recomputed_issues)
        retained_feedback = json.loads(required["feedback"].read_text(encoding="utf-8"))
        if not isinstance(retained_feedback, list) or retained_feedback != recomputed_issues:
            raise ValueError("proof.live.property_attempt_feedback_recompute")
        independently_valid = isinstance(parsed, Mapping) and not recomputed_issues
        if (
            trace.get("parse_status") != parse_status
            or retained_parsed != parsed
            or trace.get("status")
            != ("valid" if independently_valid else "invalid")
            or trace.get("acceptance_eligible") is not independently_valid
            or (
                independently_valid
                and response_document(attempt) != parsed
            )
        ):
            raise ValueError("proof.live.property_attempt_status")

        if (
            trace.get("template_id") != attempt.get("template_id")
            or trace.get("template_hash") != attempt.get("template_hash")
            or trace.get("attempt") != attempt.get("stage_attempt")
            or trace.get("evidence_class") != "live"
        ):
            raise ValueError("proof.live.property_attempt_binding")
        operation_id = str(trace.get("operation_id") or "")
        claim_id = str(trace.get("claim_id") or "")
        if not operation_id or not claim_id:
            raise ValueError("proof.live.property_attempt_claim")
        retained_groups.setdefault((operation_id, claim_id), []).append(
            {
                "number": trace.get("attempt"),
                "status": "valid" if independently_valid else "invalid",
                "renderer": renderer_input,
                "feedback": retained_feedback,
                "attempt_id": attempt_id,
            }
        )

    live_positions = {str(item.get("attempt_id") or ""): index for index, item in enumerate(live_attempts)}
    if set(retained_groups) != expected_claims:
        raise ValueError("proof.live.property_claim_set")
    for evidence in retained_groups.values():
        ordered = sorted(evidence, key=lambda item: int(item["number"]))
        numbers = [item["number"] for item in ordered]
        if numbers not in ([1], [1, 2]):
            raise ValueError("proof.live.property_attempt_sequence")
        first_renderer = ordered[0]["renderer"]
        if (
            not isinstance(first_renderer, Mapping)
            or not isinstance(ordered[0]["feedback"], list)
            or first_renderer.get(
            "PREVIOUS_VALIDATION_FEEDBACK"
            ) != []
            or (numbers == [1] and ordered[0]["status"] != "valid")
            or (numbers == [1] and ordered[0]["feedback"] != [])
        ):
            raise ValueError("proof.live.property_attempt_feedback")
        if numbers == [1, 2]:
            first, second = ordered
            if (
                not isinstance(second["renderer"], Mapping)
                or not isinstance(second["feedback"], list)
                or
                first["status"] != "invalid"
                or second["status"] != "valid"
                or not first["feedback"]
                or second["feedback"] != []
                or live_positions[second["attempt_id"]]
                != live_positions[first["attempt_id"]] + 1
                or second["renderer"].get("PREVIOUS_VALIDATION_FEEDBACK")
                != first["feedback"]
                or {
                    key: value
                    for key, value in second["renderer"].items()
                    if key != "PREVIOUS_VALIDATION_FEEDBACK"
                }
                != {
                    key: value
                    for key, value in first_renderer.items()
                    if key != "PREVIOUS_VALIDATION_FEEDBACK"
                }
            ):
                raise ValueError("proof.live.property_attempt_retry_binding")

    if used_attempt_ids != {
        str(item.get("attempt_id") or "") for item in live_attempts
    }:
        raise ValueError("proof.live.property_attempt_binding")


def _audit_r1_production_input_isolation(
    *,
    roles: Mapping[str, Path],
    damaged_sha256: str,
    request_sha256: str,
    resolved_target_count: int,
) -> None:
    _audit_production_input_isolation(
        roles=roles,
        boundary_path=_require_r1_role(roles, "production_input_boundary"),
        damaged_sha256=damaged_sha256,
        request_sha256=request_sha256,
        resolved_target_count=resolved_target_count,
        # The frozen R1 plan deliberately defers the exact command to the
        # post-approval execution manifest.  Until that runner/manifest exists,
        # this is only a basename/shape check; readiness must remain blocked.
        expected_entrypoint=None,
        entrypoint_prefix="run_",
        boundary_error="proof.live.production_input_boundary",
        private_canary_error="proof.live.private_canary",
        private_field_error="proof.live.private_field",
    )


def _require_r1_role(roles: Mapping[str, Path], role: str) -> Path:
    path = roles.get(role)
    if path is None or not path.is_file():
        raise ValueError(f"proof.files.required_role:{role}")
    return path


def _require_r1_declared_artifact(
    *,
    case_root: Path,
    declared_path: Path,
    roles: Mapping[str, Path],
    role: str,
) -> Path:
    root = case_root.resolve()
    declared = declared_path.resolve()
    retained = roles.get(role)
    if (
        retained is None
        or retained.resolve() != declared
        or not declared.is_relative_to(root)
        or not declared.is_file()
    ):
        raise ValueError(f"proof.files.declared_artifact:{role}")
    return declared


def _load_validated_r1_state(state_path: Path) -> Any:
    resolved = state_path.resolve(strict=True)
    run_root = resolved.parent
    runs_root = run_root.parent
    if resolved.name != "state.json" or runs_root.name != "runs":
        raise ValueError("proof.runtime_state.location")
    if (run_root / ".terminal-publication.json").exists():
        raise ValueError("proof.runtime_state.pending_publication")
    try:
        store = RunStore(runs_root.parent)
        state = store.load(run_root.name)
        result = store.read_result(run_root.name)
    except Exception as error:
        raise ValueError("proof.runtime_state.invalid") from error
    if (
        state.run_id != run_root.name
        or result.run_id != state.run_id
        or result.state_version != state.state_version
        or result.status != state.stage.value
        or result.reason_code != state.reason_code
        or dict(result.artifacts) != dict(state.result_artifacts)
    ):
        raise ValueError("proof.runtime_state.identity")
    return state


def _audit_r1_success_terminal_binding(
    *,
    state: Mapping[str, Any] | Any,
    state_path: Path,
    roles: Mapping[str, Path],
    repaired_ifc_path: Path,
    application: Mapping[str, Any],
) -> None:
    """Bind a successful Proof to the atomic RunStore publication commit."""

    error = "proof.success.terminal_publication"
    document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    transitions = [
        item
        for item in document.get("transitions", ())
        if isinstance(item, Mapping)
    ]
    result_artifacts = document.get("result_artifacts")
    if (
        document.get("stage") != "succeeded"
        or document.get("reason_code") is not None
        or not transitions
        or transitions[-1].get("to_stage") != "succeeded"
        or transitions[-1].get("reason_code") is not None
        or transitions[-1].get("stage_payload") != {"status": "succeeded"}
        or not isinstance(result_artifacts, Mapping)
        or transitions[-1].get("result_artifacts") != result_artifacts
        or set(result_artifacts)
        != {"manifest", "successful_ifc", "evaluation"}
    ):
        raise ValueError(error)

    run_root = state_path.resolve(strict=True).parent
    listed = {path.resolve(strict=True) for path in roles.values()}

    def _artifact(reference: Any) -> Path:
        if not isinstance(reference, str) or not reference:
            raise ValueError(error)
        path = _safe_path(run_root, reference)
        if not path.is_file() or path.resolve() not in listed:
            raise ValueError(error)
        return path.resolve()

    manifest_path = _artifact(result_artifacts["manifest"])
    successful_path = _artifact(result_artifacts["successful_ifc"])
    evaluation_path = _artifact(result_artifacts["evaluation"])
    if (
        successful_path != repaired_ifc_path.resolve(strict=True)
        or roles.get("production_publication_manifest") != manifest_path
        or roles.get("production_evaluation") != evaluation_path
        or roles.get("application_result") is None
        or _read_json(roles["application_result"]) != application
    ):
        raise ValueError(error)

    evaluation = _read_json(evaluation_path)
    if (
        evaluation.get("schema_version")
        != "text2ifc/ifc-repair-evaluation-public/0.2"
        or evaluation.get("complete_repair_success") is not True
        or evaluation.get("successful_artifact_publishable") is not True
    ):
        raise ValueError(error)

    manifest = _read_json(manifest_path)
    entries = manifest.get("artifacts")
    if (
        manifest.get("schema_version")
        != "text2ifc/ifc-repair-artifact-manifest/0.1"
        or not isinstance(entries, list)
        or len(entries) != 3
    ):
        raise ValueError(error)
    by_role: dict[str, Path] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError(error)
        role = str(entry.get("role") or "")
        path = _artifact(entry.get("path"))
        if (
            role in by_role
            or _normalize_sha256(str(entry.get("sha256") or ""))
            != _sha256(path)
            or int(entry.get("size_bytes", -1)) != path.stat().st_size
        ):
            raise ValueError(error)
        by_role[role] = path
    if (
        set(by_role)
        != {"public_evaluation", "public_evidence", "successful_ifc"}
        or by_role["public_evaluation"] != evaluation_path
        or by_role["successful_ifc"] != successful_path
        or roles.get("production_publication_evidence")
        != by_role["public_evidence"]
    ):
        raise ValueError(error)
    evidence = _read_json(by_role["public_evidence"])
    public_evidence = evidence.get("evidence")
    if (
        evidence.get("terminal_status") != "succeeded"
        or not isinstance(public_evidence, Mapping)
        or public_evidence.get("application") != application
    ):
        raise ValueError(error)


def _r1_bound_transition_artifact(
    *,
    state: Mapping[str, Any] | Any,
    state_path: Path,
    artifact_key: str,
    listed_paths: Iterable[Path],
    before_transition_id: int | None,
    require_unique: bool,
) -> Path:
    """Resolve one RunStore SHA binding and require its file was in FILES 0.2."""

    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    matches: list[Mapping[str, Any]] = []
    for transition in state_document.get("transitions", ()):
        if not isinstance(transition, Mapping):
            continue
        transition_id = transition.get("transition_id")
        if (
            before_transition_id is not None
            and isinstance(transition_id, int)
            and transition_id >= before_transition_id
        ):
            continue
        payload = transition.get("stage_payload")
        binding = payload.get(artifact_key) if isinstance(payload, Mapping) else None
        if isinstance(binding, Mapping):
            matches.append(binding)
    if not matches or (require_unique and len(matches) != 1):
        raise ValueError(f"proof.runtime_state.artifact_binding:{artifact_key}")
    binding = matches[-1]
    if set(binding) != {"path", "sha256", "schema_version"} or not str(
        binding.get("schema_version") or ""
    ):
        raise ValueError(f"proof.runtime_state.artifact_binding:{artifact_key}")
    run_root = state_path.resolve(strict=True).parent
    artifact = _safe_path(run_root, str(binding.get("path") or ""))
    listed = {path.resolve(strict=True) for path in listed_paths}
    if (
        not artifact.is_file()
        or artifact.resolve() not in listed
        or _normalize_sha256(str(binding.get("sha256") or ""))
        != _sha256(artifact)
    ):
        raise ValueError(f"proof.runtime_state.artifact_binding:{artifact_key}")
    return artifact.resolve()


def _r1_effective_property_claim_id(
    *,
    state: Mapping[str, Any] | Any,
    base_claim_id: str,
) -> str:
    """Derive the exact M1 resume claim from its hash-chained generation."""

    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    resume_generations: list[int] = []
    for transition in state_document.get("transitions", ()):
        if not isinstance(transition, Mapping):
            continue
        answer = transition.get("answer")
        payload = transition.get("stage_payload")
        if not isinstance(answer, Mapping) or answer.get("kind") != "add_detail":
            continue
        generation = (
            payload.get("property_resolution_generation")
            if isinstance(payload, Mapping)
            else None
        )
        if not isinstance(generation, int) or generation < 1:
            raise ValueError("proof.m1.property_resolution_generation")
        resume_generations.append(generation)
    if not resume_generations:
        return str(base_claim_id)
    if len(resume_generations) != 1:
        raise ValueError("proof.m1.resume_lineage")
    return f"{base_claim_id}-resume-{resume_generations[0]:03d}"


def _r1_initial_request_intent_path(
    *,
    state: Mapping[str, Any] | Any,
    state_path: Path,
    listed_paths: Iterable[Path],
    fallback: Path,
) -> Path:
    """Resolve the intent before add-detail; target selection keeps the request."""

    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    add_detail_ids = [
        transition.get("transition_id")
        for transition in state_document.get("transitions", ())
        if isinstance(transition, Mapping)
        and isinstance(transition.get("answer"), Mapping)
        and transition["answer"].get("kind") == "add_detail"
    ]
    if not add_detail_ids:
        return fallback.resolve()
    if len(add_detail_ids) != 1 or not isinstance(add_detail_ids[0], int):
        raise ValueError("proof.m1.resume_lineage")
    return _r1_bound_transition_artifact(
        state=state,
        state_path=state_path,
        artifact_key="intent",
        listed_paths=listed_paths,
        before_transition_id=add_detail_ids[0],
        require_unique=True,
    )


def _audit_r1_m1_initial_replay_binding(
    *,
    replay_paths: Mapping[str, Path],
    roles: Mapping[str, Path],
    state: Mapping[str, Any] | Any,
    state_path: Path,
    expected_resume_answer: str,
    initial_intent: Mapping[str, Any],
) -> None:
    """Bind M1's initial rejection to the case-local base-claim evidence."""

    listed = {path.resolve() for path in roles.values()}
    required_names = {
        "query": "query.json",
        "candidate_set": "candidate-set.json",
        "decision": "parsed-response.json",
        "decision_trace": "trace.json",
        "claim": "claim.json",
        "retained_admission": "admissibility-provider.json",
    }
    if (
        set(replay_paths) != set(required_names)
        or any(
            path.resolve() not in listed
            or not path.is_file()
            or path.name != required_names[name]
            for name, path in replay_paths.items()
        )
    ):
        raise ValueError("proof.m1.initial_replay_binding")
    paths = {name: path.resolve() for name, path in replay_paths.items()}
    claim_root = paths["query"].parent
    if (
        paths["candidate_set"].parent != claim_root
        or paths["claim"].parent != claim_root
        or paths["retained_admission"].parent != claim_root
        or paths["decision"].parent != paths["decision_trace"].parent
        or claim_root not in paths["decision_trace"].parents
        or "property-resolution" not in paths["decision_trace"].parts
    ):
        raise ValueError("proof.m1.initial_replay_binding")
    query = _read_json(paths["query"])
    candidate_set = _read_json(paths["candidate_set"])
    trace = _read_json(paths["decision_trace"])
    claim_id = str(query.get("claim_id") or "")
    operation_id = str(query.get("operation_id") or "")
    claim_suffix = claim_id.removeprefix("claim-")
    matching_operations = [
        operation
        for operation in initial_intent.get("operations", ())
        if isinstance(operation, Mapping)
        and str(operation.get("operation_id") or "") == operation_id
    ]
    if (
        len(matching_operations) != 1
        or not claim_suffix.isdigit()
        or claim_id != f"claim-{int(claim_suffix):03d}"
    ):
        raise ValueError("proof.m1.initial_claim")
    property_intents = matching_operations[0].get("property_intents")
    claim_index = int(claim_suffix) - 1
    if (
        not isinstance(property_intents, list)
        or claim_index < 0
        or claim_index >= len(property_intents)
        or not isinstance(property_intents[claim_index], Mapping)
        or property_intents[claim_index].get("intent_kind")
        != "natural_language_property"
        or _read_json(paths["claim"]) != property_intents[claim_index]
    ):
        raise ValueError("proof.m1.initial_claim")
    state_document = state.to_dict() if hasattr(state, "to_dict") else dict(state)
    run_id = str(state_document.get("run_id") or "")
    if (
        not claim_id
        or "-resume-" in claim_id
        or not run_id
        or query.get("run_id") != run_id
        or trace.get("run_id") != run_id
        or trace.get("claim_id") != claim_id
        or trace.get("operation_id") != query.get("operation_id")
        or trace.get("query_id") != query.get("query_id")
        or trace.get("candidate_set_id")
        != candidate_set.get("candidate_set_id")
    ):
        raise ValueError("proof.m1.initial_replay_binding")
    checkpoints: list[str] = []
    checkpoint_payloads: dict[str, Mapping[str, Any]] = {}
    add_detail_index: int | None = None
    add_detail_clarification_id: str | None = None
    clarification_indexes: list[int] = []
    clarification_id: str | None = None
    for index, transition in enumerate(state_document.get("transitions", ())):
        if not isinstance(transition, Mapping):
            continue
        answer = transition.get("answer")
        if isinstance(answer, Mapping) and answer.get("kind") == "add_detail":
            answer_payload = transition.get("stage_payload")
            transition_id = transition.get("transition_id")
            state_version = transition.get("state_version")
            generation = (
                answer_payload.get("property_resolution_generation")
                if isinstance(answer_payload, Mapping)
                else None
            )
            if (
                not isinstance(transition_id, int)
                or not isinstance(state_version, int)
                or not isinstance(generation, int)
                or generation != transition_id
                or state_version != transition_id
                or not isinstance(answer_payload.get("clarification_id"), str)
                or not str(answer_payload["clarification_id"]).strip()
            ):
                raise ValueError("proof.m1.resume_lineage")
            if (
                add_detail_index is not None
                or answer.get("detail") != expected_resume_answer
                or transition.get("from_stage") != "clarification_required"
                or transition.get("to_stage") != "intent_ready"
                or not isinstance(answer_payload, Mapping)
                or not isinstance(
                    answer_payload.get("property_resolution_generation"), int
                )
                or int(answer_payload["property_resolution_generation"]) < 1
            ):
                raise ValueError("proof.m1.resume_answer")
            add_detail_index = index
            add_detail_clarification_id = str(answer_payload["clarification_id"])
        if (
            transition.get("to_stage") == "clarification_required"
            and answer is None
        ):
            clarification = transition.get("clarification")
            answer_modes = (
                clarification.get("answer_modes")
                if isinstance(clarification, Mapping)
                else None
            )
            if (
                transition.get("from_stage") != "intent_ready"
                or
                transition.get("reason_code") != "property_resolution"
                or not isinstance(clarification, Mapping)
                or not isinstance(clarification.get("clarification_id"), str)
                or not str(clarification["clarification_id"]).strip()
                or clarification.get("run_id") != run_id
                or clarification.get("operation_id")
                != query.get("operation_id")
                or clarification.get("claim_id") != claim_id
                or clarification.get("reason_code") != "property_resolution"
                or not isinstance(answer_modes, list)
                or "add_detail" not in answer_modes
            ):
                raise ValueError("proof.m1.resume_clarification")
            clarification_indexes.append(index)
            clarification_id = str(clarification["clarification_id"])
        payload = transition.get("stage_payload")
        resolution = payload.get("property_resolution") if isinstance(payload, Mapping) else None
        if not isinstance(resolution, Mapping):
            continue
        if (
            resolution.get("run_id") == run_id
            and resolution.get("operation_id") == query.get("operation_id")
            and resolution.get("claim_id") == claim_id
        ):
            checkpoints.append(str(resolution.get("checkpoint") or ""))
            checkpoint_payloads[str(resolution.get("checkpoint") or "")] = resolution
            if add_detail_index is not None:
                raise ValueError("proof.m1.initial_replay_order")
    if checkpoints != ["candidates", "decision", "admissibility"]:
        raise ValueError("proof.m1.initial_replay_checkpoint")
    if (
        add_detail_index is None
        or len(clarification_indexes) != 1
        or clarification_indexes[0] + 1 != add_detail_index
        or add_detail_clarification_id != clarification_id
    ):
        raise ValueError("proof.m1.resume_lineage")
    forbidden_pre_clarification_stages = {
        "targets_resolved",
        "changeset_ready",
        "application_ready",
        "evaluated",
        "succeeded",
    }
    clarification_index = clarification_indexes[0]
    for transition in state_document.get("transitions", ())[: clarification_index + 1]:
        if not isinstance(transition, Mapping):
            continue
        if str(transition.get("to_stage") or "") in forbidden_pre_clarification_stages:
            raise ValueError("proof.m1.initial_stop")
        result_artifacts = transition.get("result_artifacts")
        if isinstance(result_artifacts, Mapping) and result_artifacts:
            raise ValueError("proof.m1.initial_stop")
    expected_by_checkpoint = {
        "candidates": {
            "query": paths["query"],
            "candidate_set": paths["candidate_set"],
        },
        "admissibility": {"admissibility": paths["retained_admission"]},
    }
    run_root = state_path.resolve().parent
    for checkpoint, expected_artifacts in expected_by_checkpoint.items():
        artifacts = checkpoint_payloads[checkpoint].get("artifacts")
        if not isinstance(artifacts, Mapping):
            raise ValueError("proof.m1.initial_replay_artifact")
        for artifact_name, expected_path in expected_artifacts.items():
            reference = artifacts.get(artifact_name)
            if not isinstance(reference, Mapping):
                raise ValueError("proof.m1.initial_replay_artifact")
            artifact = _safe_path(run_root, str(reference.get("path") or ""))
            if (
                artifact.resolve() != expected_path
                or artifact.resolve() not in listed
                or _normalize_sha256(str(reference.get("sha256") or ""))
                != _sha256(artifact)
            ):
                raise ValueError("proof.m1.initial_replay_artifact")
    decision_artifacts = checkpoint_payloads["decision"].get("artifacts")
    decision_reference = (
        decision_artifacts.get("decision")
        if isinstance(decision_artifacts, Mapping)
        else None
    )
    if not isinstance(decision_reference, Mapping):
        raise ValueError("proof.m1.initial_replay_artifact")
    decision_result = _safe_path(run_root, str(decision_reference.get("path") or ""))
    decision_document = _read_json(decision_result)
    if (
        decision_result.resolve() not in listed
        or _normalize_sha256(str(decision_reference.get("sha256") or ""))
        != _sha256(decision_result)
        or decision_document.get("decision") != _read_json(paths["decision"])
        or decision_document.get("trace") != _read_json(paths["decision_trace"])
    ):
        raise ValueError("proof.m1.initial_replay_artifact")


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
    manifest_path = args.collection_root.resolve() / "manifest.json"
    manifest = _read_json(manifest_path)
    if manifest.get("schema_version") == "text2ifc/ifc-repair-proof-collection/0.2":
        result = validate_r1_proof_collection(args.collection_root)
        document = result.to_dict()
        validate_proof_validation_document_v03(document)
    else:
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
