"""Run the frozen Phase 12 d7n/vvo structural and four-family matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
from contextlib import closing
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from text2ifc_knowledge.property_search import (  # noqa: E402
    _prepare_windows_torch_runtime,
)

_prepare_windows_torch_runtime()

import ifcopenshell  # noqa: E402

from text2ifc_agent.providers import ProviderOutput  # noqa: E402
from text2ifc_ifc_repair.apply import apply_changeset  # noqa: E402
from text2ifc_ifc_repair.benchmark_evaluation import (  # noqa: E402
    ProductionEvaluationInputs,
    evaluate_production,
)
from text2ifc_ifc_repair.compare import compare_ifc_models  # noqa: E402
from text2ifc_ifc_repair.evaluation import evaluation_to_dict  # noqa: E402
from text2ifc_ifc_repair.index_store import SQLiteIndexRepository  # noqa: E402
from text2ifc_ifc_repair.indexer import build_ifc_index  # noqa: E402
from text2ifc_ifc_repair.mutation import remove_structural_members  # noqa: E402
from text2ifc_ifc_repair.operations import create_default_registry  # noqa: E402
from text2ifc_ifc_repair.property_admissibility import (  # noqa: E402
    admit_property_decision,
)
from text2ifc_ifc_repair.property_intent import (  # noqa: E402
    NaturalLanguagePropertyIntent,
)
from text2ifc_ifc_repair.property_resolution_stage import (  # noqa: E402
    generate_property_resolution_decision,
)
from text2ifc_ifc_repair.repair_intent import (  # noqa: E402
    PublicProvenance,
    RepairIntent,
)
from text2ifc_ifc_repair.resolution_flow import resolve_repair_intent  # noqa: E402
from text2ifc_ifc_repair.semantic_authoring import (  # noqa: E402
    parse_semantic_manifest,
    semantic_manifest_expected_facts,
    semantic_manifest_to_dict,
)
from text2ifc_knowledge.property_search import (  # noqa: E402
    PropertyKnowledgeQuery,
    PropertyResolutionDecision,
    ResolvedExactProperty,
    create_historical_alias_baseline_resolver,
    normalize_property_value,
)
from text2ifc_knowledge.registry import load_ifc2x3_registry  # noqa: E402
from text2ifc_knowledge.property_runtime import (  # noqa: E402
    create_default_property_runtime,
)
from scripts.ifc_repair.run_phase12_public_structural_repair import (  # noqa: E402
    _bound_changeset,
    _build_authority,
    _intent_document,
    _production_evidence_document,
    _run_public_repair_with_resolver as run_public_repair,
)


DEFAULT_OUTPUT = ROOT / "dataset/processed/ifc-repair/phase12-offline"
D7N = ROOT / "dataset/ifc/test/d7n.ifc"
VVO = ROOT / "dataset/ifc/train/vvo.ifc"
FOUR_FAMILY_BASE = (
    ROOT
    / "dataset/processed/proof/ifc-repair-success-cases"
    / "mixed/door-window/vvo-authority-triplet-public-repair"
)

D7N_BEAM_ID = "1RnWak0Kr6GxkeYF4Sd_bw"
D7N_COLUMN_ID = "3dldEzenf9LvnDJYNNzLsH"
D7N_BEAM_STOREY = "0K_MqVdrL0JOCMi_Gblgiw"
D7N_COLUMN_STOREY = "0K_MqVdrL0JOCMi_GblRwJ"
VVO_BEAM_ID = "17tPjyQtf2L9JnbXXmcTUF"
VVO_COLUMN_ID = "1rsYNObuDC4euALdw6WUK4"
VVO_BEAM_STOREY = "1vTeahUkP60PdWqwCTjUuM"
VVO_COLUMN_STOREY = "1vTeahUkP60PdWqwCTjeRs"
VVO_MIXED_STOREY = "1vTeahUkP60PdWqwCTjSGJ"

SUCCESS_CASE_IDS = (
    "phase12-d7n-beam-loadbearing",
    "phase12-d7n-column-loadbearing",
    "phase12-d7n-beam-column-atomic",
    "phase12-vvo-beam-material-present",
    "phase12-vvo-column-material-absent",
    "phase12-vvo-door-window-beam-column-atomic",
)
FAILURE_CASE_IDS = (
    "phase12-d7n-beam-column-rollback",
    "phase12-vvo-door-window-beam-column-rollback",
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


def _write_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        allow_nan=False,
        default=str,
    ).rstrip() + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"PHASE12_JSON_OBJECT_REQUIRED:{path}")
    return value


class _FrozenOfflinePropertyProvider:
    """One-shot offline oracle that must select an actually rendered offer."""

    def __init__(self, *, candidate_id: str, canonical_path: str) -> None:
        self.candidate_id = candidate_id
        self.canonical_path = canonical_path
        self.call_count = 0

    def generate_candidate(self, **kwargs: Any) -> ProviderOutput:
        self.call_count += 1
        if self.call_count != 1:
            raise RuntimeError("PHASE12_1_OFFLINE_PROPERTY_PROVIDER_REUSED")
        prompt = str(kwargs["prompt"])
        if self.candidate_id not in prompt or self.canonical_path not in prompt:
            raise RuntimeError("PHASE12_1_EXPECTED_PROPERTY_NOT_RENDERED")
        if kwargs["state"].get("provider_call_ordinal") != "property_resolution":
            raise RuntimeError("PHASE12_1_PROPERTY_STAGE_ORDINAL_MISMATCH")
        return ProviderOutput(
            text=json.dumps(
                {
                    "schema_version": (
                        "text2ifc/ifc-property-rerank-decision/0.1"
                    ),
                    "decision": "confirmed",
                    "selected_candidate_id": self.candidate_id,
                    "conflicting_candidate_ids": [],
                    "clarification_question": None,
                },
                ensure_ascii=False,
            ),
            metadata={
                "provider": "phase12.1-frozen-offline-oracle",
                "evidence_class": "injected_offline",
            },
        )


class _OfflineStage15PropertyResolver:
    """Run actual retrieval, Stage1.5 and admissibility for offline cases."""

    def __init__(
        self,
        *,
        runtime: Any,
        output_root: Path,
        expected_paths: Mapping[tuple[str, str], str],
    ) -> None:
        self.runtime = runtime
        self.output_root = output_root
        self.expected_paths = dict(expected_paths)

    def resolve(self, query: PropertyKnowledgeQuery) -> PropertyResolutionDecision:
        del query
        raise RuntimeError("PHASE12_1_PROPERTY_CLAIM_BINDING_REQUIRED")

    def resolve_for_claim(
        self,
        *,
        operation_id: str,
        operation_type: str,
        claim_id: str,
        claim: NaturalLanguagePropertyIntent,
        query: PropertyKnowledgeQuery,
    ) -> PropertyResolutionDecision:
        expected = self.expected_paths.get((operation_id, claim_id))
        if expected is None:
            raise RuntimeError("PHASE12_1_OFFLINE_PROPERTY_EXPECTATION_MISSING")
        claim_root = self.output_root / operation_id / claim_id
        retrieval = self.runtime.retrieve(
            run_id="phase12-offline-matrix",
            request_id=f"request-{operation_id}",
            model_id="phase12-offline-frozen-oracle",
            operation_id=operation_id,
            operation_type=operation_type,
            claim_id=claim_id,
            property_phrase=str(claim.property_phrase),
            target_ifc_class=query.target_ifc_class,
            raw_value=claim.raw_value,
            raw_unit=claim.raw_unit,
            scope=claim.scope,
            project_length_unit=query.project_length_unit,
        )
        _write(claim_root / "query.json", retrieval.query)
        _write(claim_root / "candidate-set.json", retrieval.candidate_set)
        selected = next(
            (
                item
                for item in retrieval.candidate_set["candidates"]
                if item["canonical_path"] == expected
            ),
            None,
        )
        if selected is None:
            return PropertyResolutionDecision(
                status="clarification_required",
                reason_code="PROPERTY_EXPECTED_CANDIDATE_NOT_RETRIEVED",
                exact_intent=None,
                candidates=(),
            )
        provider = _FrozenOfflinePropertyProvider(
            candidate_id=str(selected["candidate_id"]),
            canonical_path=expected,
        )
        stage_result = generate_property_resolution_decision(
            query=retrieval.query,
            candidate_set=retrieval.candidate_set,
            output_dir=claim_root / "provider",
            provider=provider,
        )
        if not stage_result.get("valid") or stage_result.get("decision") is None:
            raise RuntimeError(
                "PHASE12_1_OFFLINE_PROPERTY_STAGE_FAILED:"
                + str(stage_result.get("error_code") or "UNKNOWN")
            )
        decision = dict(stage_result["decision"])
        trace = _read(claim_root / "provider/attempt-001/trace.json")
        policy = dict(self.runtime.policy or {})
        admission = admit_property_decision(
            query=retrieval.query,
            candidate_set=retrieval.candidate_set,
            decision=decision,
            decision_trace=trace,
            policy=policy,
            records=self.runtime.records,
            registry=self.runtime.registry,
            claim=claim,
            project_length_unit=query.project_length_unit,
        )
        _write(claim_root / "admissibility.json", admission.to_dict())
        if admission.status != "passed" or admission.exact_intent is None:
            return PropertyResolutionDecision(
                status=(
                    "unsupported"
                    if admission.status == "unsupported"
                    else "clarification_required"
                ),
                reason_code=admission.reason_code,
                exact_intent=None,
                candidates=(),
            )
        exact = admission.exact_intent
        return PropertyResolutionDecision(
            status="standard_resolved",
            reason_code="PROPERTY_ADMISSIBLE_STAGE_1_5",
            exact_intent=ResolvedExactProperty(
                set_name=exact.set_name,
                property_name=exact.property_name,
                value=exact.value,
                requested_value_type=exact.requested_value_type,
                requested_unit=exact.requested_unit,
                scope=exact.scope,
            ),
            candidates=(),
        )


def _offline_expected_property_paths(
    operations: Iterable[Mapping[str, Any]],
) -> dict[tuple[str, str], str]:
    expected_by_operation_type = {
        "add_beam": "Pset_BeamCommon.LoadBearing",
        "add_column": "Pset_ColumnCommon.LoadBearing",
    }
    expected: dict[tuple[str, str], str] = {}
    for operation in operations:
        claims = list(operation.get("property_intents") or [])
        if not claims:
            continue
        operation_type = str(operation["operation_type"])
        canonical_path = expected_by_operation_type.get(operation_type)
        if canonical_path is None or len(claims) != 1:
            raise RuntimeError("PHASE12_1_OFFLINE_PROPERTY_FIXTURE_UNFROZEN")
        expected[(str(operation["operation_id"]), "claim-001")] = canonical_path
    return expected


def _beam_parameters(*, x_mm: float, y_mm: float, z_mm: float) -> dict[str, Any]:
    return {
        "axis": {
            "start": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": z_mm},
            "end": {"x_mm": x_mm + 3000, "y_mm": y_mm + 4000, "z_mm": z_mm},
        },
        "section": {"shape": "rectangle", "width_mm": 300, "height_mm": 500},
    }


def _column_parameters(*, x_mm: float, y_mm: float) -> dict[str, Any]:
    return {
        "axis": {
            "base": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": 0},
            "top": {"x_mm": x_mm, "y_mm": y_mm, "z_mm": 6000},
        },
        "section": {
            "shape": "rectangle",
            "width_mm": 400,
            "depth_mm": 600,
            "orientation": {"x": 0, "y": 1},
        },
    }


def _load_bearing(family: str, index: int) -> dict[str, Any]:
    phrase = f"{family} is load bearing"
    return {
        "intent_kind": "natural_language_property",
        "property_phrase": phrase,
        "raw_value": True,
        "raw_unit": None,
        "scope": "occurrence_direct",
        "source": {
            "source_kind": "user_request",
            "reference": f"request:/operations/{index}/properties/0",
            "excerpt": phrase,
        },
    }


def _material(label: str, index: int) -> dict[str, Any]:
    return {
        "intent_kind": "material",
        "name": f"material:{label}",
        "value": label,
        "source": {
            "source_kind": "user_request",
            "reference": f"request:/operations/{index}/materials/0",
            "excerpt": f"material={label}",
        },
    }


def _operation(
    *,
    case_id: str,
    family: str,
    index: int,
    storey_id: str,
    parameters: Mapping[str, Any],
    load_bearing: bool = False,
    material: str | None = None,
) -> dict[str, Any]:
    return {
        "operation_id": f"{case_id}-{family}-{index + 1}",
        "operation_type": f"add_{family}",
        "target_query": {
            "schema_version": "text2ifc/ifc-target-query/0.1",
            "allowed_ifc_classes": ["IfcBuildingStorey"],
            "global_id": storey_id,
        },
        "parameters": dict(parameters),
        "property_intents": (
            [_load_bearing(family, index)] if load_bearing else []
        ),
        "attribute_intents": (
            [_material(material, index)] if material is not None else []
        ),
    }


def _bundle(case_id: str, request: str, operations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "text2ifc/phase12-public-structural-request/0.1",
        "case_id": case_id,
        "request_id": f"request-{case_id}",
        "changeset_id": f"changeset-{case_id}",
        "request": request.strip(),
        "operations": operations,
    }


def _structural_specs() -> dict[str, dict[str, Any]]:
    return {
        "phase12-d7n-beam-loadbearing": {
            "source": D7N,
            "beam_ids": (D7N_BEAM_ID,),
            "column_ids": (),
            "operations": [
                _operation(
                    case_id="phase12-d7n-beam-loadbearing",
                    family="beam",
                    index=0,
                    storey_id=D7N_BEAM_STOREY,
                    parameters=_beam_parameters(x_mm=100000, y_mm=100000, z_mm=0),
                    load_bearing=True,
                )
            ],
            "request": "Add one horizontal rectangular Beam and make the Beam load bearing.",
        },
        "phase12-d7n-column-loadbearing": {
            "source": D7N,
            "beam_ids": (),
            "column_ids": (D7N_COLUMN_ID,),
            "operations": [
                _operation(
                    case_id="phase12-d7n-column-loadbearing",
                    family="column",
                    index=0,
                    storey_id=D7N_COLUMN_STOREY,
                    parameters=_column_parameters(x_mm=110000, y_mm=110000),
                    load_bearing=True,
                )
            ],
            "request": "Add one vertical rectangular Column and make the Column load bearing.",
        },
        "phase12-d7n-beam-column-atomic": {
            "source": D7N,
            "beam_ids": (D7N_BEAM_ID,),
            "column_ids": (D7N_COLUMN_ID,),
            "operations": [
                _operation(
                    case_id="phase12-d7n-beam-column-atomic",
                    family="beam",
                    index=0,
                    storey_id=D7N_COLUMN_STOREY,
                    parameters=_beam_parameters(x_mm=120000, y_mm=120000, z_mm=3000),
                ),
                _operation(
                    case_id="phase12-d7n-beam-column-atomic",
                    family="column",
                    index=1,
                    storey_id=D7N_COLUMN_STOREY,
                    parameters=_column_parameters(x_mm=123000, y_mm=124000),
                ),
            ],
            "request": "Add one Beam supported by one Column in one atomic ChangeSet.",
        },
        "phase12-vvo-beam-material-present": {
            "source": VVO,
            "beam_ids": (VVO_BEAM_ID,),
            "column_ids": (),
            "operations": [
                _operation(
                    case_id="phase12-vvo-beam-material-present",
                    family="beam",
                    index=0,
                    storey_id=VVO_BEAM_STOREY,
                    parameters=_beam_parameters(x_mm=200000, y_mm=200000, z_mm=0),
                    material="C_钢筋砼C30",
                )
            ],
            "request": "Add one horizontal rectangular Beam with explicitly authorized material C_钢筋砼C30.",
        },
        "phase12-vvo-column-material-absent": {
            "source": VVO,
            "beam_ids": (),
            "column_ids": (VVO_COLUMN_ID,),
            "operations": [
                _operation(
                    case_id="phase12-vvo-column-material-absent",
                    family="column",
                    index=0,
                    storey_id=VVO_COLUMN_STOREY,
                    parameters=_column_parameters(x_mm=210000, y_mm=210000),
                )
            ],
            "request": "Add one vertical rectangular Column; no material is specified.",
        },
    }


def _artifact_index(case_root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(case_root).as_posix(): {
            "path": path.relative_to(case_root).as_posix(),
            "sha256": _sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in sorted(case_root.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }


def _augment_source_case(
    *,
    case_root: Path,
    source: Path,
    mutation_root: Path,
) -> dict[str, Any]:
    shutil.copy2(source, case_root / "original.ifc")
    shutil.copy2(
        mutation_root / "mutation_manifest.private.json",
        case_root / "mutation_manifest.private.json",
    )
    shutil.copy2(
        mutation_root / "mutation_report.json",
        case_root / "mutation_report.json",
    )
    manifest = _read(case_root / "manifest.json")
    manifest["schema_version"] = "text2ifc/phase12-offline-case/0.1"
    manifest["evidence_scope"] = "cross_scene_same_family_bimnet"
    manifest["source"] = {
        "path": source.relative_to(ROOT).as_posix(),
        "schema": "IFC2X3",
        "size_bytes": source.stat().st_size,
        "sha256": _sha256(source),
    }
    manifest["damage"] = _read(mutation_root / "mutation_report.json")
    manifest["artifacts"] = _artifact_index(case_root)
    _write(case_root / "manifest.json", manifest)
    return manifest


def _run_structural_case(
    *,
    case_id: str,
    spec: Mapping[str, Any],
    accepted_root: Path,
    scratch_root: Path,
    property_runtime: Any,
) -> dict[str, Any]:
    source = Path(spec["source"])
    mutation_root = scratch_root / case_id
    remove_structural_members(
        source_path=source,
        output_dir=mutation_root,
        beam_global_ids=tuple(spec["beam_ids"]),
        column_global_ids=tuple(spec["column_ids"]),
        expected_source_sha256=_sha256(source).removeprefix("sha256:"),
    )
    request_bundle = scratch_root / f"{case_id}.request.json"
    _write(
        request_bundle,
        _bundle(case_id, str(spec["request"]), list(spec["operations"])),
    )
    case_root = accepted_root / case_id
    property_resolver = _OfflineStage15PropertyResolver(
        runtime=property_runtime,
        output_root=case_root / "property-resolution",
        expected_paths=_offline_expected_property_paths(spec["operations"]),
    )
    run_public_repair(
        damaged_ifc=mutation_root / "damaged.ifc",
        public_request_bundle=request_bundle,
        output_root=case_root,
        property_knowledge_resolver=property_resolver,
    )
    manifest = _augment_source_case(
        case_root=case_root,
        source=source,
        mutation_root=mutation_root,
    )
    return {
        "case_id": case_id,
        "status": "passed",
        "relative_path": case_root.relative_to(accepted_root.parent).as_posix(),
        "operation_count": int(manifest["operation_count"]),
        "operation_types": sorted(
            {
                item["operation_type"]
                for item in _read(case_root / "changeset.json")["operations"]
            }
        ),
    }


def _shift_structural_sources(value: Any, *, offset: int) -> Any:
    if isinstance(value, dict):
        return {
            key: _shift_structural_sources(child, offset=offset)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [_shift_structural_sources(child, offset=offset) for child in value]
    if isinstance(value, str):
        return re.sub(
            r"request:/operations/(\d+)",
            lambda match: (
                f"request:/operations/{int(match.group(1)) + offset}"
            ),
            value,
        )
    return value


def _upgrade_legacy_mixed_operation(operation: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(operation))
    operation_type = str(result["operation_type"])
    routing = {
        "add_window_with_opening_to_wall": (
            "window",
            "add",
            "window.add-with-opening",
        ),
        "fill_existing_opening_with_door": (
            "door",
            "fill",
            "door.fill-existing-opening.v0.2",
        ),
    }
    try:
        family, action, profile = routing[operation_type]
    except KeyError as error:
        raise ValueError(
            f"PHASE12_LEGACY_MIXED_OPERATION_UNSUPPORTED:{operation_type}"
        ) from error
    provenance = list(result.get("provenance") or [])
    if not provenance:
        raise ValueError("PHASE12_LEGACY_MIXED_PROVENANCE_MISSING")
    result["routing_intent"] = {
        "component_family": family,
        "action": action,
        "operation_profile": profile,
        "source": provenance[0],
    }
    result.setdefault("property_intents", [])
    result.setdefault("quantity_intents", [])
    result.setdefault("semantic_bundle_refs", [])
    result.setdefault("occurrence_reuse_intent", None)
    return result


def _mixed_private_manifest(original: Path, damaged: Path) -> dict[str, Any]:
    mapping = _read(FOUR_FAMILY_BASE / "private-evaluation/benchmark-mapping.json")
    model = ifcopenshell.open(str(original))
    targets: list[dict[str, Any]] = []
    for index, item in enumerate(mapping["damage"]["removed_doors"], start=1):
        targets.append(_private_target(model, str(item["global_id"]), f"door-{index}"))
    for index, item in enumerate(mapping["damage"]["removed_windows"], start=1):
        targets.append(_private_target(model, str(item["global_id"]), f"window-{index}"))
        targets.append(
            _private_target(
                model,
                str(item["opening_global_id"]),
                f"window-opening-{index}",
            )
        )
    return {
        "schema_version": "text2ifc/phase12-private-damage-manifest/0.1",
        "visibility": "evaluator_only_after_production",
        "source": {
            "path": VVO.relative_to(ROOT).as_posix(),
            "schema": "IFC2X3",
            "size_bytes": original.stat().st_size,
            "sha256": _sha256(original),
        },
        "damaged_ifc": {"path": "damaged.ifc", "sha256": _sha256(damaged)},
        "targets": targets,
        "role_mapping": {
            target["role"]: target["entity"]["global_id"] for target in targets
        },
    }


def _private_target(model: Any, global_id: str, role: str) -> dict[str, Any]:
    entity = model.by_guid(global_id)
    return {
        "role": role,
        "entity": {
            "ifc_class": str(entity.is_a()),
            "global_id": str(entity.GlobalId),
            "step_id": int(entity.id()),
            "name": None if entity.Name is None else str(entity.Name),
        },
    }


def _mixed_intent_document(
    *,
    request: str,
    damaged_hash: str,
    duplicate_beam: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    base = _read(FOUR_FAMILY_BASE / "agent/repair-intent.json")
    case_id = (
        "phase12-vvo-door-window-beam-column-rollback"
        if duplicate_beam
        else "phase12-vvo-door-window-beam-column-atomic"
    )
    structural_operations = [
        _operation(
            case_id=case_id,
            family="beam",
            index=0,
            storey_id=VVO_MIXED_STOREY,
            parameters=_beam_parameters(x_mm=100000, y_mm=100000, z_mm=3000),
        ),
        _operation(
            case_id=case_id,
            family="column",
            index=1,
            storey_id=VVO_MIXED_STOREY,
            parameters=_column_parameters(x_mm=103000, y_mm=104000),
        ),
    ]
    if duplicate_beam:
        structural_operations.append(
            _operation(
                case_id=case_id,
                family="beam",
                index=2,
                storey_id=VVO_MIXED_STOREY,
                parameters=_beam_parameters(
                    x_mm=100000,
                    y_mm=100000,
                    z_mm=3000,
                ),
            )
        )
    structural_bundle = _bundle(case_id, request, structural_operations)
    structural = _intent_document(structural_bundle, damaged_hash=damaged_hash)
    shifted = _shift_structural_sources(
        structural["operations"],
        offset=len(base["operations"]),
    )
    intent = {
        "schema_version": "text2ifc/ifc-repair-intent/0.5",
        "request_id": f"request-{case_id}",
        "source_request_hash": _text_sha256(request),
        "model_fingerprint": damaged_hash,
        "prompt_fingerprint": _text_sha256(
            "phase12-frozen-public-four-family-request/0.1"
        ),
        "operations": [
            *(
                _upgrade_legacy_mixed_operation(item)
                for item in base["operations"]
            ),
            *shifted,
        ],
        "semantic_bundles": [],
        "provenance": [
            {
                "source_kind": "user_request",
                "reference": "request:/text",
                "excerpt": request[:2048],
            }
        ],
    }
    public_bundle = {
        "schema_version": "text2ifc/phase12-public-four-family-request/0.1",
        "case_id": case_id,
        "changeset_id": f"changeset-{case_id}",
        "request": request,
        "repair_intent": intent,
    }
    return intent, public_bundle


def _legacy_manifest_document(
    operation: Mapping[str, Any],
    *,
    damaged_hash: str,
) -> dict[str, Any]:
    reference = operation.get("semantic_manifest")
    reference = reference if isinstance(reference, Mapping) else {}
    return {
        "schema_version": "text2ifc/ifc-repair-semantic-manifest/0.3",
        "manifest_id": str(reference.get("manifest_id") or ""),
        "operation_id": str(operation["operation_id"]),
        "operation_type": str(operation["operation_type"]),
        "base_model_fingerprint": damaged_hash,
        "policy": {
            "policy_id": str(reference.get("policy_id") or ""),
            "policy_version": str(reference.get("policy_version") or ""),
        },
        "assignments": deepcopy(list(operation.get("semantic_assignments") or [])),
    }


def _run_mixed_case(
    *,
    output_root: Path,
    duplicate_beam: bool,
    property_runtime: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    case_id = (
        "phase12-vvo-door-window-beam-column-rollback"
        if duplicate_beam
        else "phase12-vvo-door-window-beam-column-atomic"
    )
    case_root = output_root / case_id
    case_root.mkdir(parents=True)
    original = case_root / "original.ifc"
    damaged = case_root / "damaged.ifc"
    shutil.copy2(FOUR_FAMILY_BASE / "01-original.ifc", original)
    shutil.copy2(FOUR_FAMILY_BASE / "02-damaged.ifc", damaged)
    damaged_hash = _sha256(damaged)
    base_request = (
        FOUR_FAMILY_BASE / "input/request.txt"
    ).read_text(encoding="utf-8").strip()
    request = (
        base_request
        + "\nAdd one horizontal rectangular Beam and one vertical rectangular "
        "Column on the exact authorized Storey in the same atomic ChangeSet."
    )
    if duplicate_beam:
        request += " Add a second Beam on the same axis for rollback verification."
    intent_document, public_bundle = _mixed_intent_document(
        request=request,
        damaged_hash=damaged_hash,
        duplicate_beam=duplicate_beam,
    )
    public_bundle_path = case_root / "public-request-bundle.json"
    _write(public_bundle_path, public_bundle)
    registry = create_default_registry()
    intent = RepairIntent.from_dict(
        intent_document,
        registry=registry,
        require_complete=False,
    )
    index_path = case_root / "target-index.sqlite"
    metadata = build_ifc_index(damaged, index_path)
    property_resolver = _OfflineStage15PropertyResolver(
        runtime=property_runtime,
        output_root=case_root / "property-resolution",
        expected_paths=_offline_expected_property_paths(intent_document["operations"]),
    )
    with SQLiteIndexRepository.open(index_path) as repository:
        resolution = resolve_repair_intent(
            intent,
            repository,
            expected_source_sha256=metadata.source_ifc_sha256,
            operation_registry=registry,
            property_knowledge_resolver=property_resolver,
        )
        records = {item.ifc_global_id: item for item in repository.iter_records()}
        type_records = {
            item.ifc_global_id: item for item in repository.iter_type_records()
        }
    if resolution.status != "resolved":
        raise RuntimeError(
            "PHASE12_MIXED_RESOLUTION_FAILED:"
            + json.dumps(resolution.to_dict(), ensure_ascii=False)
        )
    evidence, manifests, _, _, _ = (
        _build_authority(
            intent=intent,
            resolution=resolution,
            registry=registry,
            records=records,
            type_records=type_records,
            base_model_fingerprint=damaged_hash,
        )
    )
    manifest_name = "semantic-manifests.json"
    base_changeset = _read(
        FOUR_FAMILY_BASE / "changeset/bound-changeset.json"
    )
    structural_documents = [
        semantic_manifest_to_dict(manifest)
        for manifest in manifests
        if manifest.operation_type in {"add_beam", "add_column"}
    ]
    legacy_documents = [
        _legacy_manifest_document(operation, damaged_hash=damaged_hash)
        for operation in base_changeset["operations"]
    ]
    manifest_payload = {
        "schema_version": "text2ifc/ifc-repair-semantic-manifest-bundle/0.1",
        "manifests": [*legacy_documents, *structural_documents],
    }
    manifest_hash = _text_sha256(
        json.dumps(
            manifest_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    changeset = _bound_changeset(
        bundle=public_bundle,
        intent=intent,
        resolution=resolution,
        manifests=manifests,
        manifest_name=manifest_name,
        manifest_hash=manifest_hash,
        damaged_hash=damaged_hash,
    )
    generated_structural = [
        operation
        for operation in changeset["operations"]
        if operation["operation_type"] in {"add_beam", "add_column"}
    ]
    changeset["operations"] = [
        *deepcopy(base_changeset["operations"]),
        *generated_structural,
    ]
    changeset["evidence_refs"] = list(
        dict.fromkeys(
            [
                *changeset.get("evidence_refs", ()),
                *(
                    str(reference)
                    for operation in changeset["operations"]
                    for reference in operation.get("evidence_refs", ())
                ),
            ]
        )
    )
    changeset["semantic_manifest_ref"] = manifest_name
    changeset["semantic_manifest_sha256"] = manifest_hash
    repaired = case_root / "repaired.ifc"
    candidate = case_root / "repaired.candidate.ifc"
    application: dict[str, Any] | None = None
    try:
        application = apply_changeset(
            damaged_ifc_path=damaged,
            repair_request=request,
            changeset=changeset,
            output_path=candidate,
            registry=registry,
        )
        _write(case_root / "request.txt", request)
        _write(case_root / "repair-intent.json", intent.to_dict())
        _write(case_root / "target-resolution.json", resolution.to_dict())
        _write(
            case_root / "production-evidence.json",
            _production_evidence_document(evidence),
        )
        _write(case_root / manifest_name, manifest_payload)
        _write(case_root / "changeset.json", changeset)
        _write(case_root / "application.json", application)
        if not application.get("valid") or not application.get("published"):
            return application, {"case_id": case_id, "case_root": case_root}

        expected = dict(evidence.expected_facts_by_operation)
        for document in legacy_documents:
            legacy_manifest = parse_semantic_manifest(document)
            legacy_facts = semantic_manifest_expected_facts(legacy_manifest)
            replacements = {fact.fact_key: fact for fact in legacy_facts}
            generated_facts = expected[legacy_manifest.operation_id]
            merged = tuple(
                replacements.pop(fact.fact_key, fact) for fact in generated_facts
            )
            expected[legacy_manifest.operation_id] = (
                *merged,
                *(replacements[key] for key in sorted(replacements)),
            )
        evaluation = evaluation_to_dict(
            evaluate_production(
                ProductionEvaluationInputs(
                    damaged_ifc_path=damaged,
                    repaired_ifc_path=candidate,
                    changeset=changeset,
                    application_result=application,
                    registry=registry,
                    expected_facts_by_operation=expected,
                )
            )
        )
        _write(case_root / "evaluation.json", evaluation)
        if not evaluation["complete_repair_success"]:
            failed = [
                {
                    "operation_id": item.get("operation_id"),
                    "status": item.get("status"),
                    "levels": {
                        level.get("level"): level.get("status")
                        for level in item.get("levels", ())
                    },
                }
                for item in evaluation.get("operations", ())
                if item.get("status") != "passed"
            ]
            raise RuntimeError(
                "PHASE12_MIXED_EVALUATION_FAILED:"
                + json.dumps(failed, ensure_ascii=False)
            )
        allowed = {
            str(item["global_id"])
            for operation in application["operations"]
            for section in ("created", "modified", "removed")
            for item in operation["changes"].get(section, ())
            if item.get("global_id")
        }
        comparison = compare_ifc_models(
            damaged,
            candidate,
            allowed_changed_ids=allowed,
        )
        if not comparison["complete_preservation_success"]:
            raise RuntimeError("PHASE12_MIXED_PRESERVATION_FAILED")
        application["output"]["path"] = str(repaired)
        _write(case_root / "application.json", application)
        os.replace(candidate, repaired)
    except Exception as error:
        if application is not None and application.get("published") is True:
            blocking_code = (
                str(error).split(":", 1)[0]
                if isinstance(error, RuntimeError)
                else "PHASE12_MIXED_FINALIZATION_FAILED"
            )
            candidate_output = application.get("output")
            application["published"] = False
            application["output"] = None
            application["issues"] = [
                {
                    "code": blocking_code,
                    "path": "/publication_gate",
                    "message": "Final publication gate rejected the candidate IFC.",
                }
            ]
            application["publication_gate"] = {
                "status": "blocked",
                "blocking_code": blocking_code,
                "candidate_sha256": (
                    candidate_output.get("sha256")
                    if isinstance(candidate_output, Mapping)
                    else None
                ),
            }
            _write(case_root / "application.json", application)
        raise
    finally:
        if candidate.exists():
            candidate.unlink()
    boundary = {
        "schema_version": "text2ifc/production-input-boundary/0.2",
        "entrypoint": "run_phase12_offline.py",
        "ifc_inputs": ["damaged_ifc_path"],
        "request_inputs": ["public_request_bundle"],
        "original_ifc_supplied": False,
        "mutation_manifest_supplied": False,
        "deleted_object_ids_supplied": False,
        "private_comparator_available_during_repair": False,
        "damaged_ifc_sha256": damaged_hash,
        "request_sha256": intent.source_request_hash,
        "public_request_bundle_sha256": _sha256(public_bundle_path),
        "resolved_target_count": len(resolution.operations),
        "changeset_canonical_sha256": _text_sha256(
            json.dumps(
                changeset,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        ),
    }
    private_manifest = _mixed_private_manifest(original, damaged)
    _write(case_root / "comparison.json", comparison)
    _write(case_root / "production-boundary.json", boundary)
    _write(case_root / "mutation_manifest.private.json", private_manifest)
    manifest = {
        "schema_version": "text2ifc/phase12-offline-case/0.1",
        "case_id": case_id,
        "status": "passed",
        "provider_evidence_mode": "offline_bound_deterministic",
        "synthetic_fallback_used": False,
        "evidence_scope": "cross_scene_same_family_bimnet",
        "operation_count": len(resolution.operations),
        "operation_families": {"window": 2, "door": 2, "beam": 1, "column": 1},
        "source": private_manifest["source"],
        "damage": _read(
            FOUR_FAMILY_BASE / "validation/source-run-manifest.json"
        )["damage"],
        "production_input_boundary": boundary,
        "artifacts": _artifact_index(case_root),
    }
    _write(case_root / "manifest.json", manifest)
    return application, {"case_id": case_id, "case_root": case_root, "manifest": manifest}


def _run_structural_failure(
    failed_root: Path,
    scratch_root: Path,
    property_runtime: Any,
) -> dict[str, Any]:
    case_id = "phase12-d7n-beam-column-rollback"
    case_root = failed_root / case_id
    case_root.mkdir(parents=True)
    source_hash = _sha256(D7N)
    parameters = _beam_parameters(x_mm=130000, y_mm=130000, z_mm=3000)
    operations = [
        _operation(
            case_id=case_id,
            family="beam",
            index=index,
            storey_id=D7N_COLUMN_STOREY,
            parameters=parameters,
        )
        for index in range(2)
    ]
    bundle_path = scratch_root / f"{case_id}.request.json"
    _write(bundle_path, _bundle(case_id, "Add two Beams on the same axis.", operations))
    failure_stage = ""
    attempt_root = case_root / "attempt"
    property_resolver = _OfflineStage15PropertyResolver(
        runtime=property_runtime,
        output_root=attempt_root / "property-resolution",
        expected_paths=_offline_expected_property_paths(operations),
    )
    try:
        run_public_repair(
            damaged_ifc=D7N,
            public_request_bundle=bundle_path,
            output_root=attempt_root,
            property_knowledge_resolver=property_resolver,
        )
    except RuntimeError as error:
        failure_stage = str(error).split(":", 1)[0]
    if failure_stage != "PUBLIC_STRUCTURAL_APPLICATION_FAILED":
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_DID_NOT_FAIL")
    application = _read(attempt_root / "application.json")
    if (
        application.get("valid") is not False
        or application.get("published") is not False
        or (attempt_root / "repaired.ifc").exists()
    ):
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_PUBLICATION_LEAK")
    issues = application.get("issues")
    if not isinstance(issues, list) or not issues:
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_ISSUE_MISSING")
    blocking = str(issues[0].get("code") or "")
    if blocking != "STRUCTURAL_SAME_AXIS_OVERLAP":
        raise RuntimeError("PHASE12_STRUCTURAL_ROLLBACK_CODE_MISMATCH")
    damaged_input = attempt_root / "damaged.ifc"
    changeset = _read(attempt_root / "changeset.json")
    damaged_input_hash = _sha256(damaged_input)
    changeset_fingerprint = str(changeset.get("base_model_fingerprint") or "")
    source_unchanged = (
        damaged_input_hash == source_hash
        and changeset_fingerprint == damaged_input_hash
    )
    failure = {
        "case_id": case_id,
        "status": "failed_expected",
        "valid": application["valid"],
        "published": application["published"],
        "blocking_code": blocking,
        "failure_stage": failure_stage,
        "source_unchanged": source_unchanged,
        "damaged_ifc_sha256": damaged_input_hash,
        "damaged_ifc_bytes": damaged_input.stat().st_size,
        "changeset_base_model_fingerprint": changeset_fingerprint,
    }
    _write(case_root / "failure.json", failure)
    return failure


def _run_mixed_failure(
    failed_root: Path,
    property_runtime: Any,
) -> dict[str, Any]:
    source_hash = _sha256(FOUR_FAMILY_BASE / "02-damaged.ifc")
    application, metadata = _run_mixed_case(
        output_root=failed_root,
        duplicate_beam=True,
        property_runtime=property_runtime,
    )
    case_root = Path(metadata["case_root"])
    if (
        application.get("valid") is not False
        or application.get("published") is not False
        or (case_root / "repaired.ifc").exists()
    ):
        raise RuntimeError("PHASE12_MIXED_ROLLBACK_PUBLICATION_LEAK")
    issues = application.get("issues", ())
    blocking = str(issues[0].get("code")) if issues else "UNKNOWN_FAILURE"
    if blocking != "STRUCTURAL_SAME_AXIS_OVERLAP":
        raise RuntimeError("PHASE12_MIXED_ROLLBACK_CODE_MISMATCH")
    damaged_input = case_root / "damaged.ifc"
    changeset = _read(case_root / "changeset.json")
    damaged_input_hash = _sha256(damaged_input)
    changeset_fingerprint = str(changeset.get("base_model_fingerprint") or "")
    source_unchanged = (
        damaged_input_hash == source_hash
        and changeset_fingerprint == damaged_input_hash
    )
    failure = {
        "case_id": metadata["case_id"],
        "status": "failed_expected",
        "valid": application["valid"],
        "published": application["published"],
        "blocking_code": blocking,
        "source_unchanged": source_unchanged,
        "damaged_ifc_sha256": damaged_input_hash,
        "damaged_ifc_bytes": damaged_input.stat().st_size,
        "changeset_base_model_fingerprint": changeset_fingerprint,
    }
    _write(case_root / "failure.json", failure)
    return failure


def _property_family(target_class: str) -> str:
    return {
        "IfcWindow": "window",
        "IfcDoor": "door",
        "IfcWall": "wall",
        "IfcWallStandardCase": "wall",
        "IfcBeam": "beam",
        "IfcColumn": "column",
    }[target_class]


def _wilson_interval(successes: int, total: int) -> dict[str, float]:
    if total == 0:
        return {"lower": 0.0, "upper": 1.0}
    z = 1.959963984540054
    rate = successes / total
    denominator = 1.0 + z * z / total
    centre = (rate + z * z / (2.0 * total)) / denominator
    radius = (
        z
        * math.sqrt(
            rate * (1.0 - rate) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return {"lower": centre - radius, "upper": centre + radius}


def _property_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    supported = [item for item in rows if item["authorize"]]
    negatives = [item for item in rows if not item["authorize"]]
    correct = sum(bool(item["passed"]) for item in rows)
    standard_outputs = [item for item in rows if item["authorized_path"]]
    correct_standard = sum(
        item["authorized_path"] == item["expected"]
        for item in standard_outputs
    )
    family_slices: dict[str, Any] = {}
    for family in ("window", "door", "wall", "beam", "column"):
        family_rows = [item for item in rows if item["family"] == family]
        family_correct = sum(bool(item["passed"]) for item in family_rows)
        family_slices[family] = {
            "case_count": len(family_rows),
            "passed_count": family_correct,
            "accuracy": family_correct / len(family_rows),
            "accuracy_95ci": _wilson_interval(
                family_correct,
                len(family_rows),
            ),
        }
    return {
        "case_count": len(rows),
        "supported_count": len(supported),
        "negative_count": len(negatives),
        "passed_count": correct,
        "failed_count": len(rows) - correct,
        "accuracy": correct / len(rows),
        "accuracy_95ci": _wilson_interval(correct, len(rows)),
        "confirmed_standard_count": len(standard_outputs),
        "confirmed_standard_precision": (
            correct_standard / len(standard_outputs)
            if standard_outputs
            else 1.0
        ),
        "confirmed_standard_precision_95ci": _wilson_interval(
            correct_standard,
            len(standard_outputs),
        ),
        "false_standard_authorization_count": sum(
            bool(item["authorized_path"]) for item in negatives
        ),
        "family_slices": family_slices,
        "decision_slices": {
            "supported": {
                "case_count": len(supported),
                "passed_count": sum(bool(item["passed"]) for item in supported),
            },
            "negative_or_inadmissible": {
                "case_count": len(negatives),
                "passed_count": sum(bool(item["passed"]) for item in negatives),
            },
        },
    }


def _property_evaluation_cases(project_root: Path) -> list[dict[str, Any]]:
    addition = _read(
        project_root
        / "tests/fixtures/knowledge/phase12_1_property_resolution.json"
    )
    baseline = _read(project_root / str(addition["baseline_fixture"]))
    baseline_cases = [deepcopy(item) for item in baseline["cases"]]
    addition_cases = [deepcopy(item) for item in addition["cases"]]
    cases = [*baseline_cases, *addition_cases]
    if len(cases) != 60:
        raise RuntimeError("PHASE12_1_PROPERTY_EVALUATION_CASE_COUNT")
    baseline_ids = {str(item["id"]) for item in baseline_cases}
    groups: dict[str, list[dict[str, Any]]] = {}
    canonical_pattern = re.compile(
        r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*"
    )
    for case in cases:
        semantic_path = case.get("expected")
        phrase = str(case["phrase"])
        if semantic_path is None and canonical_pattern.fullmatch(phrase):
            semantic_path = phrase
        group_id = (
            f"{case['class']}:{semantic_path}"
            if isinstance(semantic_path, str)
            else str(case.get("group_id") or f"{case['class']}:negative:{case['id']}")
        )
        case["group_id"] = group_id
        groups.setdefault(group_id, []).append(case)
    for members in groups.values():
        roles = {str(item.get("role") or "historical") for item in members}
        member_ids = {str(item["id"]) for item in members}
        if "revealed-regression" in roles:
            split = "revealed"
        elif member_ids & baseline_ids:
            split = "baseline"
        else:
            split = "holdout"
        for item in members:
            item["group_split"] = split
    return cases


def _property_evaluation_public_cases(project_root: Path) -> list[dict[str, Any]]:
    public_fixture = _read(
        project_root
        / "tests/fixtures/knowledge/phase12_1_property_retrieval_public.json"
    )
    if public_fixture.get("schema_version") != (
        "text2ifc/property-retrieval-public-eval/0.1"
    ):
        raise RuntimeError("PHASE12_1_PROPERTY_PUBLIC_FIXTURE_VERSION")
    cases = [deepcopy(item) for item in public_fixture.get("cases", [])]
    if len(cases) != 60 or public_fixture.get("case_count") != 60:
        raise RuntimeError("PHASE12_1_PROPERTY_PUBLIC_FIXTURE_CASE_COUNT")
    allowed_keys = {
        "case_id",
        "target_ifc_class",
        "property_phrase",
        "raw_value",
        "raw_unit",
        "scope",
    }
    if any(set(case) != allowed_keys for case in cases):
        raise RuntimeError("PHASE12_1_PROPERTY_PUBLIC_FIXTURE_SHAPE")
    if len({str(case["case_id"]) for case in cases}) != len(cases):
        raise RuntimeError("PHASE12_1_PROPERTY_PUBLIC_FIXTURE_DUPLICATE_ID")
    return cases


def produce_property_retrieval_ledger(
    *,
    project_root: Path | str = ROOT,
    output_path: Path | str,
    qdrant_path: Path | str,
) -> dict[str, Any]:
    """Persist Gold-free real-BGE retrieval output for the frozen 60 cases."""

    root = Path(project_root).resolve()
    destination = Path(output_path).resolve()
    public_cases = _property_evaluation_public_cases(root)
    model_path = root / ".cache/models/BAAI-bge-m3"
    if not model_path.is_dir():
        raise RuntimeError("PHASE12_1_LOCAL_BGE_M3_UNAVAILABLE")
    runtime = create_default_property_runtime(
        project_root=root,
        qdrant_path=Path(qdrant_path),
        embedding_model_path=str(model_path),
        embedding_model_version="BAAI-bge-m3-local/phase12.1",
        device="cpu",
        runtime_mode="production",
    )
    if runtime.health.status != "ready":
        raise RuntimeError(
            f"PHASE12_1_PROPERTY_RUNTIME_NOT_READY:{runtime.health.reason_code}"
        )

    ledger_cases: list[dict[str, Any]] = []
    try:
        for index, case in enumerate(public_cases):
            retrieval = runtime.retrieve(
                run_id="phase12-1-property-evaluation",
                request_id="phase12-1-property-evaluation",
                model_id="offline-retrieval-evaluation",
                operation_id=f"property-eval-operation-{index + 1}",
                operation_type="set_occurrence_properties",
                claim_id=f"property-eval-claim-{index + 1}",
                property_phrase=case["property_phrase"],
                target_ifc_class=case["target_ifc_class"],
                raw_value=case["raw_value"],
                raw_unit=case["raw_unit"],
                scope=case["scope"],
            )
            ledger_cases.append(
                {
                    "case_id": case["case_id"],
                    "query": retrieval.query,
                    "candidate_set": retrieval.candidate_set,
                }
            )
    finally:
        close = getattr(runtime.vector_index, "close", None)
        if callable(close):
            close()

    result = {
        "schema_version": (
            "text2ifc/phase12.1-property-retrieval-ledger/0.1"
        ),
        "status": "passed",
        "case_count": len(ledger_cases),
        "knowledge_health": runtime.health.to_dict(),
        "provider_network_calls": 0,
        "cases": ledger_cases,
        "output_path": str(destination),
    }
    _write_atomic(destination, result)
    return result


def _property_evaluation_gold_cases(project_root: Path) -> list[dict[str, Any]]:
    """Load evaluator-only Gold after public retrieval evidence is durable."""

    return _property_evaluation_cases(project_root)


def _historical_alias_baseline_rows(
    cases: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    baseline_resolver = create_historical_alias_baseline_resolver()
    rows: list[dict[str, Any]] = []
    for case in cases:
        decision = None
        failure = None
        try:
            decision = baseline_resolver.resolve(
                PropertyKnowledgeQuery(
                    target_ifc_class=str(case["class"]),
                    phrase=str(case["phrase"]),
                    raw_value=case["value"],
                    raw_unit=None,
                    scope="occurrence_direct",
                )
            )
        except ValueError as error:
            failure = str(error)
        exact = None if decision is None else decision.exact_intent
        authorized_path = (
            None if exact is None else f"{exact.set_name}.{exact.property_name}"
        )
        expected = case.get("expected")
        passed = (
            authorized_path == expected
            if bool(case["authorize"])
            else authorized_path is None
        )
        rows.append(
            {
                "id": str(case["id"]),
                "group_id": str(case.get("group_id") or f"baseline:{case['id']}"),
                "role": str(case.get("role") or "historical"),
                "family": str(
                    case.get("family") or _property_family(str(case["class"]))
                ),
                "authorize": bool(case["authorize"]),
                "expected": expected,
                "authorized_path": authorized_path,
                "passed": passed,
                "status": None if decision is None else decision.status,
                "reason_code": failure if decision is None else decision.reason_code,
            }
        )
    return rows


def _candidate_is_currently_eligible(
    *,
    query: Mapping[str, Any],
    candidate: Mapping[str, Any],
    minimum_score: float,
    registry: Any,
) -> bool:
    if query.get("scope") != "occurrence_direct":
        return False
    if float(candidate.get("score", -1.0)) < minimum_score:
        return False
    if candidate.get("template_type") != "TypePropertySingleValue":
        return False
    if candidate.get("standard_status") not in {"standard", "project_custom"}:
        return False
    source = candidate.get("source")
    if not isinstance(source, Mapping) or source.get("kind") not in {
        "ifc2x3_psd",
        "project_record",
    }:
        return False
    applicable_classes = {
        str(item) for item in candidate.get("applicable_classes", [])
    }
    target_ifc_class = str(query.get("target_ifc_class") or "")
    declaration = registry.entity(target_ifc_class)
    supertypes = (
        set()
        if declaration is None
        else {str(item) for item in declaration.get("supertypes", ())}
    )
    if target_ifc_class not in applicable_classes and not (
        applicable_classes & supertypes
    ):
        return False
    value_type = candidate.get("value_type")
    if not isinstance(value_type, str) or not value_type:
        return False
    try:
        normalize_property_value(
            query.get("raw_value"),
            raw_unit=query.get("raw_unit"),
            value_type=value_type,
            project_length_unit="m",
        )
    except ValueError:
        return False
    return True


def _candidate_set_obeys_retrieval_policy(
    candidate_set: Mapping[str, Any],
    *,
    minimum_score: float,
    max_candidates: int,
) -> bool:
    candidates = list(candidate_set.get("candidates", []))
    if len(candidates) > max_candidates:
        return False
    ranks = [int(item.get("rank", -1)) for item in candidates]
    if ranks != list(range(1, len(candidates) + 1)):
        return False
    scores = [float(item.get("score", -1.0)) for item in candidates]
    if any(score < minimum_score for score in scores):
        return False
    if scores != sorted(scores, reverse=True):
        return False
    record_ids = [str(item.get("record_id") or "") for item in candidates]
    return bool(all(record_ids)) and len(record_ids) == len(set(record_ids))


def score_property_retrieval_ledger(
    *,
    project_root: Path | str = ROOT,
    retrieval_ledger_path: Path | str,
    output_path: Path | str,
) -> dict[str, Any]:
    """Open evaluator-only Gold only after a Gold-free ledger is durable."""

    root = Path(project_root).resolve()
    ledger_path = Path(retrieval_ledger_path).resolve()
    destination = Path(output_path).resolve()
    ledger = _read(ledger_path)
    if ledger.get("schema_version") != (
        "text2ifc/phase12.1-property-retrieval-ledger/0.1"
    ):
        raise RuntimeError("PHASE12_1_PROPERTY_RETRIEVAL_LEDGER_VERSION")
    if ledger.get("status") != "passed" or ledger.get("case_count") != 60:
        raise RuntimeError("PHASE12_1_PROPERTY_RETRIEVAL_LEDGER_INCOMPLETE")
    ledger_cases = list(ledger.get("cases", []))
    ledger_ids = [str(item.get("case_id") or "") for item in ledger_cases]
    if len(ledger_cases) != 60 or len(set(ledger_ids)) != 60 or not all(ledger_ids):
        raise RuntimeError("PHASE12_1_PROPERTY_RETRIEVAL_LEDGER_CASE_IDS")

    public_cases = _property_evaluation_public_cases(root)
    public_by_id = {str(item["case_id"]): item for item in public_cases}
    if set(ledger_ids) != set(public_by_id):
        raise RuntimeError("PHASE12_1_PROPERTY_RETRIEVAL_LEDGER_CORPUS_MISMATCH")
    for item in ledger_cases:
        public_case = public_by_id[str(item["case_id"])]
        query = item.get("query", {})
        if any(
            query.get(query_key) != public_case[public_key]
            for query_key, public_key in (
                ("target_ifc_class", "target_ifc_class"),
                ("property_phrase", "property_phrase"),
                ("raw_value", "raw_value"),
                ("raw_unit", "raw_unit"),
                ("scope", "scope"),
            )
        ):
            raise RuntimeError("PHASE12_1_PROPERTY_RETRIEVAL_QUERY_MISMATCH")

    cases = _property_evaluation_gold_cases(root)
    gold_ids = {str(case["id"]) for case in cases}
    if gold_ids != set(ledger_ids):
        raise RuntimeError("PHASE12_1_PROPERTY_RETRIEVAL_GOLD_JOIN_MISMATCH")
    ledger_by_id = {str(item["case_id"]): item for item in ledger_cases}
    policy = _read(
        root / "schemas/ifc/knowledge/property_resolution_policy.v0.2.json"
    )
    minimum_score = float(policy["minimum_retrieval_score"])
    max_candidates = int(policy["max_candidates"])
    registry = load_ifc2x3_registry(root)

    baseline_rows = _historical_alias_baseline_rows(cases)
    candidate_rows: list[dict[str, Any]] = []
    alias_runtime_authority_count = 0
    private_leakage_count = 0
    ineligible_offered_record_count = 0
    retrieval_policy_violation_count = 0
    empty_top_k_count = 0
    for case in cases:
        evidence = ledger_by_id[str(case["id"])]
        query = evidence["query"]
        candidate_set = evidence["candidate_set"]
        candidates = list(candidate_set.get("candidates", []))
        if not candidates:
            empty_top_k_count += 1
        policy_pass = _candidate_set_obeys_retrieval_policy(
            candidate_set,
            minimum_score=minimum_score,
            max_candidates=max_candidates,
        )
        if not policy_pass:
            retrieval_policy_violation_count += 1
        ineligible_for_case = sum(
            not _candidate_is_currently_eligible(
                query=query,
                candidate=candidate,
                minimum_score=minimum_score,
                registry=registry,
            )
            for candidate in candidates
        )
        ineligible_offered_record_count += ineligible_for_case
        expected = case.get("expected")
        selected = next(
            (
                item
                for item in candidates
                if item.get("canonical_path") == expected
            ),
            None,
        )
        public_evidence = json.dumps(
            {"query": query, "candidate_set": candidate_set},
            ensure_ascii=False,
            sort_keys=True,
        ).casefold()
        if "reviewed_alias" in public_evidence or "property_aliases" in public_evidence:
            alias_runtime_authority_count += 1
        if any(
            token in public_evidence
            for token in (
                "benchmark_gold",
                "private_gold",
                "mutation_recipe",
                "deleted_identity",
            )
        ):
            private_leakage_count += 1
        scores = [float(item["score"]) for item in candidates]
        candidate_rows.append(
            {
                "id": str(case["id"]),
                "group_id": str(case.get("group_id") or f"baseline:{case['id']}"),
                "role": str(case.get("role") or "historical"),
                "family": str(
                    case.get("family") or _property_family(str(case["class"]))
                ),
                "authorize": bool(case["authorize"]),
                "expected": expected,
                "authorized_path": None,
                "passed": None,
                "semantic_decision_status": "not_evaluated_offline",
                "retrieval_hit": selected is not None,
                "selected_rank": None if selected is None else int(selected["rank"]),
                "selected_score": None if selected is None else float(selected["score"]),
                "top1_score": None if not scores else scores[0],
                "top1_top2_margin": None if len(scores) < 2 else scores[0] - scores[1],
                "candidate_paths": [
                    str(item["canonical_path"]) for item in candidates
                ],
                "candidate_count": len(candidates),
                "ineligible_offered_record_count": ineligible_for_case,
                "retrieval_policy_pass": policy_pass,
                "decision": None,
                "admissibility_status": "not_evaluated_semantically",
                "reason_code": None,
            }
        )

    baseline = _property_metrics(baseline_rows)
    supported_rows = [item for item in candidate_rows if item["authorize"]]
    supported_hits = sum(bool(item["retrieval_hit"]) for item in supported_rows)
    retrieval_miss_count = len(supported_rows) - supported_hits
    candidate_family_slices: dict[str, Any] = {}
    for family in ("window", "door", "wall", "beam", "column"):
        family_rows = [item for item in candidate_rows if item["family"] == family]
        supported_family_rows = [item for item in family_rows if item["authorize"]]
        family_hits = sum(
            bool(item["retrieval_hit"]) for item in supported_family_rows
        )
        candidate_family_slices[family] = {
            "case_count": len(family_rows),
            "supported_count": len(supported_family_rows),
            "supported_top_k_hits": family_hits,
            "supported_top_k_recall": (
                None
                if not supported_family_rows
                else family_hits / len(supported_family_rows)
            ),
            "supported_top_k_recall_95ci": _wilson_interval(
                family_hits,
                len(supported_family_rows),
            ),
            "semantic_scored_count": 0,
        }
    candidate = {
        "case_count": len(candidate_rows),
        "supported_count": len(supported_rows),
        "negative_count": len(candidate_rows) - len(supported_rows),
        "semantic_scored_count": 0,
        "semantic_unscored_count": len(candidate_rows),
        "confirmed_standard_count": None,
        "confirmed_standard_precision": None,
        "false_standard_authorization_count": None,
        "supported_top_k_recall": supported_hits / len(supported_rows),
        "supported_top_k_recall_95ci": _wilson_interval(
            supported_hits,
            len(supported_rows),
        ),
        "empty_top_k_case_count": empty_top_k_count,
        "retrieval_policy_violation_count": retrieval_policy_violation_count,
        "ineligible_offered_record_count": ineligible_offered_record_count,
        "alias_runtime_authority_count": alias_runtime_authority_count,
        "private_leakage_count": private_leakage_count,
        "family_slices": candidate_family_slices,
    }
    hard_gates = {
        "all_supported_in_top_k": candidate["supported_top_k_recall"] == 1.0,
        "empty_top_k_fail_closed": all(
            item["authorized_path"] is None
            for item in candidate_rows
            if item["candidate_count"] == 0
        ),
        "retrieval_floor_policy": retrieval_policy_violation_count == 0,
        "zero_ineligible_candidates_offered": ineligible_offered_record_count == 0,
        "zero_alias_runtime_authority": alias_runtime_authority_count == 0,
        "zero_private_leakage": private_leakage_count == 0,
    }
    status = "passed" if all(hard_gates.values()) else "failed"
    result = {
        "schema_version": "text2ifc/phase12.1-property-resolution-evaluation/0.3",
        "status": status,
        "reason_code": None if status == "passed" else "PROPERTY_RETRIEVAL_GATE_FAILED",
        "evaluator_id": "phase12.1.fixed-property-evaluator/0.3",
        "case_count": len(cases),
        "failures_in_denominator": baseline["failed_count"] + retrieval_miss_count,
        "minimum_retrieval_score": minimum_score,
        "calibration": {
            "frozen_supported_minimum_score": 0.4805306036784617,
            "configured_floor": minimum_score,
            "floor_purpose": (
                "exclude low-quality retrieval evidence before Stage 1.5; "
                "never authorize by score"
            ),
        },
        "retrieval_capability": "evaluated",
        "retrieval_metrics": {
            "case_count": len(candidate_rows),
            "retrieval_ledger_path": str(ledger_path),
            "supported_top_k_recall": candidate["supported_top_k_recall"],
            "empty_top_k_case_count": empty_top_k_count,
            "retrieval_policy_violation_count": retrieval_policy_violation_count,
            "ineligible_offered_record_count": ineligible_offered_record_count,
        },
        "stage_1_5_semantic_evaluation_status": "not_evaluated_offline",
        "baseline": baseline,
        "candidate": candidate,
        "hard_gates": hard_gates,
        "knowledge_health": ledger["knowledge_health"],
        "evaluation_mode": "offline_retrieval_only_stage15_fixture_excluded",
        "stage15_candidate_evidence": {
            "status": "not_evaluated_offline",
            "semantic_scored_count": 0,
            "fixture_or_replay_used_for_scoring": False,
            "provider_network_calls": 0,
        },
        "provider_network_calls": 0,
        "claim_scope": (
            "real BGE-M3/Qdrant retrieval capability only; Stage 1.5 semantic "
            "capability is not evaluated offline"
        ),
        "cases": {"baseline": baseline_rows, "candidate": candidate_rows},
        "output_path": str(destination),
    }
    _write_atomic(destination, result)
    return result


def evaluate_property_resolution_matrix(
    *,
    project_root: Path | str = ROOT,
    output_path: Path | str,
    qdrant_path: Path | str,
    retrieval_ledger_path: Path | str | None = None,
) -> dict[str, Any]:
    """Produce Gold-free real retrieval evidence, then score it once."""

    destination = Path(output_path).resolve()
    ledger_path = (
        destination.with_name(f"{destination.stem}-retrieval-ledger.json")
        if retrieval_ledger_path is None
        else Path(retrieval_ledger_path).resolve()
    )
    produce_property_retrieval_ledger(
        project_root=project_root,
        output_path=ledger_path,
        qdrant_path=qdrant_path,
    )
    return score_property_retrieval_ledger(
        project_root=project_root,
        retrieval_ledger_path=ledger_path,
        output_path=destination,
    )

def run_offline_matrix(
    output_root: Path | str = DEFAULT_OUTPUT,
    *,
    case_ids: Iterable[str] | None = None,
) -> dict[str, Any]:
    output = Path(output_root).resolve()
    if output.exists():
        raise FileExistsError(f"Phase 12 offline output already exists: {output}")
    output.mkdir(parents=True)
    accepted_root = output / "accepted"
    failed_root = output / "failed"
    accepted_root.mkdir()
    selected = tuple(case_ids) if case_ids is not None else SUCCESS_CASE_IDS
    unknown = set(selected) - set(SUCCESS_CASE_IDS)
    if unknown:
        raise ValueError(f"PHASE12_OFFLINE_CASE_UNKNOWN:{sorted(unknown)}")
    if len(set(selected)) != len(selected):
        raise ValueError("PHASE12_OFFLINE_CASE_DUPLICATE")

    accepted: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    specs = _structural_specs()
    property_runtime = create_default_property_runtime(
        project_root=ROOT,
        qdrant_path=ROOT / ".cache/property-resolution/qdrant",
        embedding_model_path=str(ROOT / ".cache/models/BAAI-bge-m3"),
        embedding_model_version="BAAI-bge-m3-local/phase12.1",
        device="cpu",
        runtime_mode="production",
    )
    if property_runtime.health.status != "ready":
        raise RuntimeError(
            "PHASE12_1_PROPERTY_RUNTIME_NOT_READY:"
            + str(property_runtime.health.reason_code)
        )
    with closing(property_runtime.vector_index), tempfile.TemporaryDirectory(
        prefix="phase12-offline-",
        dir=output,
    ) as tmp:
        scratch = Path(tmp)
        for case_id in selected:
            if case_id in specs:
                accepted.append(
                    _run_structural_case(
                        case_id=case_id,
                        spec=specs[case_id],
                        accepted_root=accepted_root,
                        scratch_root=scratch,
                        property_runtime=property_runtime,
                    )
                )
            else:
                _, metadata = _run_mixed_case(
                    output_root=accepted_root,
                    duplicate_beam=False,
                    property_runtime=property_runtime,
                )
                manifest = metadata["manifest"]
                accepted.append(
                    {
                        "case_id": case_id,
                        "status": "passed",
                        "relative_path": Path(metadata["case_root"])
                        .relative_to(output)
                        .as_posix(),
                        "operation_count": int(manifest["operation_count"]),
                        "operation_types": sorted(
                            {
                                item["operation_type"]
                                for item in _read(
                                    Path(metadata["case_root"]) / "changeset.json"
                                )["operations"]
                            }
                        ),
                    }
                )
        if case_ids is None:
            failures.append(
                _run_structural_failure(
                    failed_root,
                    scratch,
                    property_runtime,
                )
            )
            failures.append(_run_mixed_failure(failed_root, property_runtime))

    accepted_ids = {item["case_id"] for item in accepted}
    failure_ids = {item["case_id"] for item in failures}
    coverage = {
        "beam_only": "phase12-d7n-beam-loadbearing" in accepted_ids,
        "column_only": "phase12-d7n-column-loadbearing" in accepted_ids,
        "beam_column_atomic": "phase12-d7n-beam-column-atomic" in accepted_ids,
        "beam_loadbearing": "phase12-d7n-beam-loadbearing" in accepted_ids,
        "column_loadbearing": "phase12-d7n-column-loadbearing" in accepted_ids,
        "material_present": "phase12-vvo-beam-material-present" in accepted_ids,
        "material_absent": "phase12-vvo-column-material-absent" in accepted_ids,
        "rollback": "phase12-d7n-beam-column-rollback" in failure_ids,
        "door_window_beam_column_atomic": (
            "phase12-vvo-door-window-beam-column-atomic" in accepted_ids
        ),
        "door_window_beam_column_rollback": (
            "phase12-vvo-door-window-beam-column-rollback" in failure_ids
        ),
    }
    matrix_complete = (
        case_ids is None
        and accepted_ids == set(SUCCESS_CASE_IDS)
        and failure_ids == set(FAILURE_CASE_IDS)
        and all(coverage.values())
    )
    summary = {
        "schema_version": "text2ifc/phase12-offline-matrix/0.1",
        "status": "passed" if matrix_complete else "partial",
        "matrix_complete": matrix_complete,
        "evidence_scope": "cross_scene_same_family_bimnet",
        "accepted_cases": accepted,
        "failed_cases": failures,
        "coverage": coverage,
        "property_resolution": {
            "attempt_count": sum(
                len(operation.get("property_intents") or [])
                for case_id in selected
                for operation in specs.get(case_id, {}).get("operations", [])
            ),
            "provider_evidence_mode": "injected_offline",
            "provider_network_calls": 0,
            "runtime_health": property_runtime.health.to_dict(),
        },
    }
    _write(output / "run-summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--property-retrieval-evaluation-only",
        action="store_true",
    )
    arguments = parser.parse_args(argv)
    if arguments.property_retrieval_evaluation_only:
        output = arguments.output_root.resolve()
        result = evaluate_property_resolution_matrix(
            output_path=output / "property-evaluation.json",
            retrieval_ledger_path=output / "property-retrieval-ledger.json",
            qdrant_path=output / "qdrant",
        )
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["status"] == "passed" else 2
    result = run_offline_matrix(arguments.output_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
