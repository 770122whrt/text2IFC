"""Deterministic canonical Source IFC manifest generation and audit helpers."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import ifcopenshell

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SCHEMA_VERSION = "text2ifc/ifc-sources/1.0"
FILE_SCHEMA_VERSION = "text2ifc/ifc-files/1.0"
VALIDATION_SCHEMA_VERSION = "text2ifc/ifc-validation/1.0"
VALIDATION_CACHE_PATH = Path("dataset/manifests/ifc-validation.jsonl")

_IFC_SCHEMA_PATTERN = re.compile(
    rb"FILE_SCHEMA\s*\(\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SourcePolicy:
    source_id: str
    name: str
    paths: tuple[str, ...]
    classification: str
    canonical_source: str
    license: str
    research_use: str
    training_use: str
    redistribution: str
    attribution: str
    notes: tuple[str, ...] = ()
    discovered_via: tuple[str, ...] = ()


# Human-authored policy lives in code; generated JSON must not be manually edited.
SOURCE_POLICIES: tuple[SourcePolicy, ...] = (
    SourcePolicy(
        source_id="bimnet",
        name="BIMNet IFC2X3",
        paths=("dataset/external/bimnet",),
        classification="authorized_local",
        canonical_source="LydJason/BIMNet (Matterport3D-derived)",
        license="user-authorized-local-use",
        research_use="authorized",
        training_use="authorized_local_only",
        redistribution="not_inferred",
        attribution="project_source_citation_required",
        notes=(
            "User confirmed local research/training authorization on 2026-06-11.",
            "Do not infer redistribution rights from local-use authorization.",
            "Physical legacy train/test directories are not experiment split authority.",
        ),
    ),
    SourcePolicy(
        source_id="bim-whale-ifc-samples",
        name="BIM Whale IFC Samples",
        paths=("dataset/external/bim-whale-ifc-samples",),
        classification="public_example",
        canonical_source="andrewisen/bim-whale-ifc-samples",
        license="MIT",
        research_use="allowed",
        training_use="review_required",
        redistribution="allowed_with_license_conditions",
        attribution="license_notice_required",
        notes=("Sample models; retain source license notice and provenance.",),
    ),
    SourcePolicy(
        source_id="buildingsmart-official",
        name="buildingSMART Official Sample Test Files",
        paths=("dataset/external/buildingsmart-official",),
        classification="public_official",
        canonical_source="buildingSMART/Sample-Test-Files",
        license="CC-BY-4.0",
        research_use="allowed_with_attribution",
        training_use="review_required",
        redistribution="allowed_with_attribution",
        attribution="required",
        notes=("Official sample/test files already admitted locally.",),
    ),
    SourcePolicy(
        source_id="ifc-bench",
        name="IFC-Bench models",
        paths=("dataset/external/ifc-bench/projects",),
        classification="public_research",
        canonical_source="sylvainHellin/ifc-bench",
        license="model-specific",
        research_use="allowed_with_source_review",
        training_use="review_required",
        redistribution="model_specific",
        attribution="model_specific",
        notes=(
            "QA dataset license does not override per-model IFC licenses.",
            "Review each project license before training or redistribution.",
        ),
    ),
    SourcePolicy(
        source_id="buildingsmart-community",
        name="buildingSMART Community Sample Test Files",
        paths=("dataset/external/buildingsmart-community",),
        classification="public_test_fixture",
        canonical_source="buildingsmart-community/Community-Sample-Test-Files",
        license="CC-BY-4.0",
        research_use="allowed_with_attribution",
        training_use="review_required",
        redistribution="allowed_with_attribution",
        attribution="required",
        notes=(
            "Community sample repository may contain intentionally invalid or non-conformant files.",
            "Only parseable and roundtrip-stable IFC2X3 files enter the current Repair source pool.",
        ),
    ),
    SourcePolicy(
        source_id="duraark-public",
        name="DURAARK Public Building Data",
        paths=("dataset/external/duraark",),
        classification="public_research",
        canonical_source="DURAARK/TIB BuildingData",
        license="source-open-data-model-rights-review-required",
        research_use="review_required",
        training_use="review_required",
        redistribution="review_required",
        attribution="required",
        discovered_via=("bimdata-rd-index",),
        notes=(
            "BIMData R&D is discovery-only; canonical provenance remains DURAARK/TIB or the original model source.",
            "Do not infer per-model training or redistribution rights from repository-level open-data metadata.",
        ),
    ),
    SourcePolicy(
        source_id="bimcollab-example",
        name="BIMcollab Example Project",
        paths=("dataset/external/bimcollab-example",),
        classification="public_example",
        canonical_source="BIMcollab Example Project",
        license="review-required",
        research_use="review_required",
        training_use="review_required",
        redistribution="review_required",
        attribution="review_required",
        notes=("Downloaded public example files require per-source usage review before training/redistribution.",),
    ),
    SourcePolicy(
        source_id="kit-examples",
        name="KIT IFC Examples",
        paths=("dataset/external/kit-examples",),
        classification="public_example",
        canonical_source="KIT IFC Examples / IFC Wiki",
        license="source-states-unrestricted-use-with-attribution",
        research_use="allowed_with_attribution",
        training_use="review_required",
        redistribution="review_required",
        attribution="required",
        notes=("Primarily useful for schema expansion when files are not IFC2X3.",),
    ),
    SourcePolicy(
        source_id="steptools-samples",
        name="STEP Tools IFC Sample Data",
        paths=("dataset/external/steptools-samples",),
        classification="public_example",
        canonical_source="STEP Tools IFC Sample Data",
        license="review-required",
        research_use="review_required",
        training_use="review_required",
        redistribution="review_required",
        attribution="review_required",
        notes=("Retain per-file source evidence; IFC2X3 files may enter Repair candidates after admission.",),
    ),
    SourcePolicy(
        source_id="thatopen-engine-web-ifc",
        name="ThatOpen engine_web-ifc Example",
        paths=("dataset/external/thatopen-engine-web-ifc",),
        classification="public_example",
        canonical_source="ThatOpen/engine_web-ifc",
        license="MPL-2.0",
        research_use="allowed_with_license_conditions",
        training_use="review_required",
        redistribution="allowed_with_license_conditions",
        attribution="license_notice_required",
        notes=("Small semantically meaningful IFC2X3 example admitted after IfcOpenShell screening.",),
    ),
    SourcePolicy(
        source_id="thatopen-web-ifc-three",
        name="ThatOpen web-ifc-three Example",
        paths=("dataset/external/thatopen-web-ifc-three",),
        classification="public_example",
        canonical_source="ThatOpen/web-ifc-three",
        license="MIT",
        research_use="allowed",
        training_use="review_required",
        redistribution="allowed_with_license_conditions",
        attribution="license_notice_required",
        notes=("Small semantically meaningful IFC2X3 example admitted after IfcOpenShell screening.",),
    ),
    SourcePolicy(
        source_id="bim2modelica",
        name="UdK BIM2Modelica IFC2X3 Models",
        paths=("dataset/external/bim2modelica",),
        classification="public_research",
        canonical_source="UdK-VPT/BIM2Modelica",
        license="repository-BSD-3-Clause-model-rights-review-required",
        research_use="allowed_with_source_review",
        training_use="review_required",
        redistribution="review_required",
        attribution="source_and_license_notice_required",
        notes=(
            "Only distinct UdKB building/zone models are retained; repetitive SBT unit-test variants are excluded.",
            "All retained files are below 10 MiB and pass the semantic meaningfulness gate.",
        ),
    ),
    SourcePolicy(
        source_id="gni-bim-dataset",
        name="GNI BIM Dataset",
        paths=("dataset/external/gni-bim-dataset",),
        classification="public_research",
        canonical_source="ZijianWang-ZW/GNI-BIM-Dataset / Zenodo 19722012",
        license="CC-BY-4.0",
        research_use="allowed_with_attribution",
        training_use="allowed_with_attribution",
        redistribution="allowed_with_attribution",
        attribution="required",
        notes=(
            "Anonymized student BIM models released with explicit CC BY 4.0 dataset rights.",
            "Only IFC2X3 models below 10 MiB that pass the semantic meaningfulness gate are admitted in this batch.",
        ),
    ),
    SourcePolicy(
        source_id="kaggle-ifc-examples",
        name="Kaggle IFC File Examples",
        paths=("dataset/external/kaggle-ifc-examples",),
        classification="public_research",
        canonical_source="claytonmiller/example-ifc-file (Kaggle)",
        license="dataset-CC-BY-4.0-upstream-model-rights-review-required",
        research_use="allowed_with_attribution",
        training_use="review_required",
        redistribution="review_required",
        attribution="required",
        notes=(
            "Kaggle dataset card declares CC BY 4.0; most files mirror the Open IFC Model Repository.",
            "Training and redistribution remain review-required because dataset-level licensing does not replace upstream provenance review.",
            "Only distinct meaningful IFC2X3 models below 10 MiB are admitted; component fixtures and known model-family variants are excluded.",
        ),
    ),
    SourcePolicy(
        source_id="opensourcebim-testfiles",
        name="opensourceBIM TestFiles",
        paths=("dataset/external/opensourcebim-testfiles",),
        classification="public_test_fixture",
        canonical_source="opensourceBIM/TestFiles",
        license="GPL-3.0-or-later",
        research_use="allowed_with_license_conditions",
        training_use="review_required",
        redistribution="allowed_with_license_conditions",
        attribution="license_notice_required",
        notes=(
            "Only independent project-level IFC2X3 representatives are retained; encoding, regression, export-variant, and known-family fixtures are excluded.",
            "TestData/license.txt applies GPL-3.0-or-later terms to the repository test data.",
        ),
    ),
    SourcePolicy(
        source_id="opensourcebim-ifc-files",
        name="opensourceBIM IFC-files",
        paths=("dataset/external/opensourcebim-ifc-files",),
        classification="public_example",
        canonical_source="opensourceBIM/IFC-files",
        license="CC-BY-ND-4.0",
        research_use="allowed_with_attribution",
        training_use="review_required",
        redistribution="allowed_with_attribution_no_derivatives",
        attribution="required",
        notes=(
            "Repository README requires IFC data to be posted under CC BY-ND 4.0.",
            "Only one HHS Office construction representative is retained; the construction2 model-family variant is excluded.",
        ),
    ),
    SourcePolicy(
        source_id="asunisoft-ifc2x3-sdk",
        name="AsuniSoft IFC2X3 SDK Example",
        paths=("dataset/external/asunisoft-ifc2x3-sdk",),
        classification="public_example",
        canonical_source="AsuniSoft/ifc2x3-SDK",
        license="repository-LGPL-2.1-model-rights-review-required",
        research_use="allowed_with_source_review",
        training_use="review_required",
        redistribution="review_required",
        attribution="source_and_license_notice_required",
        notes=(
            "Only data/Ifc/builtModel.ifc is retained; all ticket regression IFCs are excluded.",
            "Repository software is LGPL-2.1; model-level training and redistribution rights remain review-required.",
        ),
    ),
    SourcePolicy(
        source_id="ifctolbd-examples",
        name="IFCtoLBD Example Models",
        paths=("dataset/external/ifctolbd-examples",),
        classification="public_research",
        canonical_source="jyrkioraskari/IFCtoLBD",
        license="repository-Apache-2.0-model-rights-review-required",
        research_use="allowed_with_source_review",
        training_use="review_required",
        redistribution="review_required",
        attribution="source_and_license_notice_required",
        notes=(
            "Only the independent IFC2X3 Barcelona Pavilion model is retained from the repository examples.",
            "Repository software is Apache-2.0; model-level training and redistribution rights remain review-required.",
        ),
    ),
    SourcePolicy(
        source_id="xbim-essentials-examples",
        name="xBIM Essentials IFC Examples",
        paths=("dataset/external/xbim-essentials-examples",),
        classification="public_example",
        canonical_source="xBimTeam/XbimEssentials",
        license="repository-CDDL-model-rights-review-required",
        research_use="allowed_with_source_review",
        training_use="review_required",
        redistribution="review_required",
        attribution="source_and_license_notice_required",
        notes=(
            "Only complete IFC2X3 House and CPM models are retained from the test data.",
            "Tiny parser/geometry fixtures and IFC4/IFC4X3 examples are excluded.",
            "Repository software is CDDL; model-level training and redistribution rights remain review-required.",
        ),
    ),
)


class SourceManifestError(RuntimeError):
    """Raised when canonical source manifest generation cannot be trusted."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _schema_from_header(path: Path) -> str:
    with path.open("rb") as stream:
        header = stream.read(1024 * 1024)
    match = _IFC_SCHEMA_PATTERN.search(header)
    if match is None:
        return "UNKNOWN"
    return match.group(1).decode("ascii", errors="replace").upper()


def _scene_family(source_id: str, path: Path) -> str:
    stem = path.stem
    if source_id == "bimnet":
        return stem.split("_", 1)[0]
    parent = path.parent.name
    if parent.casefold() in {"ifc", "projects", "project"}:
        parent = path.parent.parent.name
    return parent or stem


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _iter_policy_files(root: Path, policy: SourcePolicy) -> Iterable[Path]:
    seen: set[Path] = set()
    for raw in policy.paths:
        base = root / raw
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.ifc"), key=lambda item: item.as_posix().casefold()):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield path


def probe_ifc(path: Path) -> dict[str, Any]:
    schema_header = _schema_from_header(path)
    parse_ok = False
    traversal_ok = False
    roundtrip_write_ok = False
    roundtrip_reopen_ok = False
    model_schema: str | None = None
    entity_count: int | None = None
    counts: dict[str, int] = {}
    error: str | None = None
    try:
        model = ifcopenshell.open(str(path))
        parse_ok = True
        model_schema = str(model.schema).upper()
        entity_count = sum(1 for _ in model)
        traversal_ok = True
        for ifc_class in (
            "IfcProject",
            "IfcSite",
            "IfcBuilding",
            "IfcBuildingStorey",
            "IfcSpace",
            "IfcWall",
            "IfcWindow",
            "IfcDoor",
            "IfcOpeningElement",
            "IfcSlab",
            "IfcRoof",
            "IfcStair",
            "IfcBeam",
            "IfcColumn",
        ):
            try:
                counts[ifc_class] = len(model.by_type(ifc_class))
            except RuntimeError:
                counts[ifc_class] = 0
        with tempfile.TemporaryDirectory(prefix="ifc-source-probe-") as temp_dir:
            target = Path(temp_dir) / "roundtrip.ifc"
            model.write(str(target))
            roundtrip_write_ok = target.is_file() and target.stat().st_size > 0
            if roundtrip_write_ok:
                reopened = ifcopenshell.open(str(target))
                roundtrip_reopen_ok = str(reopened.schema).upper() == model_schema
    except Exception as exc:  # admission evidence; caller records failure
        error = f"{type(exc).__name__}:{exc}"
    return {
        "schema_header": schema_header,
        "schema": model_schema or schema_header,
        "parseable": parse_ok,
        "traversal_ok": traversal_ok,
        "roundtrip_write_ok": roundtrip_write_ok,
        "roundtrip_reopen_ok": roundtrip_reopen_ok,
        "entity_count": entity_count,
        "entity_counts": dict(sorted(counts.items())),
        "probe_error": error,
    }


def load_validation_cache(root: Path | str = ROOT) -> dict[str, dict[str, Any]]:
    project_root = Path(root).resolve()
    path = project_root / VALIDATION_CACHE_PATH
    if not path.is_file():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        digest = str(record.get("sha256", ""))
        if len(digest) != 64:
            raise SourceManifestError(f"INVALID_VALIDATION_SHA:{line_number}")
        if digest in records:
            raise SourceManifestError(f"DUPLICATE_VALIDATION_SHA:{digest}")
        records[digest] = record
    return records


def validation_record(*, path: Path, root: Path | str, digest: str | None = None) -> dict[str, Any]:
    project_root = Path(root).resolve()
    sha = digest or _sha256(path)
    result = probe_ifc(path)
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "sha256": sha,
        "local_path_at_probe": _relative(path, project_root),
        "schema": result["schema"],
        "schema_header": result["schema_header"],
        "parseable": result["parseable"],
        "traversal_ok": result["traversal_ok"],
        "roundtrip_write_ok": result["roundtrip_write_ok"],
        "roundtrip_reopen_ok": result["roundtrip_reopen_ok"],
        "entity_count": result["entity_count"],
        "entity_counts": result["entity_counts"],
        "probe_error": result["probe_error"],
    }


def build_source_payload(root: Path | str = ROOT) -> dict[str, Any]:
    project_root = Path(root).resolve()
    records: list[dict[str, Any]] = []
    for policy in SOURCE_POLICIES:
        file_count = sum(1 for _ in _iter_policy_files(project_root, policy))
        if file_count == 0 and not any((project_root / path).exists() for path in policy.paths):
            status = "not_acquired"
        elif file_count == 0:
            status = "present_no_ifc"
        else:
            status = "present"
        records.append(
            {
                "source_id": policy.source_id,
                "name": policy.name,
                "classification": policy.classification,
                "canonical_source": policy.canonical_source,
                "license": policy.license,
                "research_use": policy.research_use,
                "training_use": policy.training_use,
                "redistribution": policy.redistribution,
                "attribution": policy.attribution,
                "paths": list(policy.paths),
                "discovered_via": list(policy.discovered_via),
                "file_count": file_count,
                "status": status,
                "notes": list(policy.notes),
            }
        )
    return {"schema_version": SOURCE_SCHEMA_VERSION, "sources": records}


def build_file_records(root: Path | str = ROOT, *, probe: bool = True) -> list[dict[str, Any]]:
    project_root = Path(root).resolve()
    validation_cache = load_validation_cache(project_root)
    raw: list[tuple[SourcePolicy, Path, str]] = []
    for policy in SOURCE_POLICIES:
        for path in _iter_policy_files(project_root, policy):
            raw.append((policy, path, _sha256(path)))
    by_hash: dict[str, list[tuple[SourcePolicy, Path]]] = defaultdict(list)
    for policy, path, digest in raw:
        by_hash[digest].append((policy, path))

    records: list[dict[str, Any]] = []
    for digest in sorted(by_hash):
        occurrences = sorted(
            by_hash[digest],
            key=lambda item: (_relative(item[1], project_root).casefold(), item[0].source_id),
        )
        canonical_policy, canonical_path = occurrences[0]
        # Prefer the unified BIMNet destination after migration.
        for policy, path in occurrences:
            if policy.source_id == "bimnet" and "dataset/external/bimnet/" in _relative(path, project_root):
                canonical_policy, canonical_path = policy, path
                break
        relative_path = _relative(canonical_path, project_root)
        cached = validation_cache.get(digest)
        if probe:
            probe_result = probe_ifc(canonical_path)
        elif cached is not None:
            probe_result = {
                "schema_header": cached["schema_header"],
                "schema": cached["schema"],
                "parseable": cached["parseable"],
                "traversal_ok": cached["traversal_ok"],
                "roundtrip_write_ok": cached["roundtrip_write_ok"],
                "roundtrip_reopen_ok": cached["roundtrip_reopen_ok"],
                "entity_count": cached["entity_count"],
                "entity_counts": cached["entity_counts"],
                "probe_error": cached["probe_error"],
            }
        else:
            header_schema = _schema_from_header(canonical_path)
            probe_result = {
                "schema_header": header_schema,
                "schema": header_schema,
                "parseable": None,
                "traversal_ok": None,
                "roundtrip_write_ok": None,
                "roundtrip_reopen_ok": None,
                "entity_count": None,
                "entity_counts": {},
                "probe_error": None,
            }
        alias_sources = sorted({policy.source_id for policy, _ in occurrences})
        alias_paths = sorted({_relative(path, project_root) for _, path in occurrences})
        stem = canonical_path.stem
        if canonical_policy.source_id == "bimnet":
            # Preserve historical IDs referenced by split authority and existing data products.
            file_id = f"bimnet-ifc2x3-{stem}".lower().replace(" ", "-")
        else:
            # Filenames repeat across schemas/projects (for example Building-Architecture.ifc).
            # A content-derived suffix keeps IDs deterministic and globally unique.
            file_id = f"{canonical_policy.source_id}-{stem}-{digest[:12]}".lower().replace(" ", "-")
        repair_eligible = (
            probe_result["schema"] == "IFC2X3"
            and probe_result["parseable"] is True
            and probe_result["traversal_ok"] is True
            and probe_result["roundtrip_reopen_ok"] is True
        )
        records.append(
            {
                "schema_version": FILE_SCHEMA_VERSION,
                "id": file_id,
                "source_id": canonical_policy.source_id,
                "source_family": _scene_family(canonical_policy.source_id, canonical_path),
                "local_path": relative_path,
                "sha256": digest,
                "size_bytes": canonical_path.stat().st_size,
                "declared_schema": probe_result["schema"],
                "header_schema": probe_result["schema_header"],
                "validation": {
                    "ifcopenshell_parse": probe_result["parseable"],
                    "entity_traversal": probe_result["traversal_ok"],
                    "roundtrip_write": probe_result["roundtrip_write_ok"],
                    "roundtrip_reopen": probe_result["roundtrip_reopen_ok"],
                    "error": probe_result["probe_error"],
                },
                "entity_count": probe_result["entity_count"],
                "entity_counts": probe_result["entity_counts"],
                "repair_source_eligible": repair_eligible,
                "license": canonical_policy.license,
                "approved_uses": (
                    ["local-extraction", "dataset-construction", "baseline-evaluation", "local-model-training"]
                    if canonical_policy.source_id == "bimnet"
                    else ["research-evaluation"]
                ),
                "training_eligible": canonical_policy.source_id == "bimnet",
                "authorization": (
                    {
                        "basis": "user-confirmed Matterport3D/BIMNet authorization",
                        "confirmed_at": "2026-06-11",
                        "redistribution_inferred": False,
                        "scope": ["local-extraction", "dataset-construction", "baseline-evaluation", "local-model-training"],
                    }
                    if canonical_policy.source_id == "bimnet"
                    else None
                ),
                "source_revision": None,
                "training_use": canonical_policy.training_use,
                "redistribution": canonical_policy.redistribution,
                "duplicate": len(occurrences) > 1,
                "duplicate_sources": alias_sources,
                "duplicate_paths": alias_paths,
                "notes": list(canonical_policy.notes),
            }
        )
    return sorted(records, key=lambda item: item["id"])


def render_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def render_jsonl(records: Iterable[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        for record in records
    )


def manifest_summary(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = list(records)
    schemas = Counter(str(record["declared_schema"]) for record in records)
    sources = Counter(str(record["source_id"]) for record in records)
    return {
        "unique_ifc_count": len(records),
        "repair_source_eligible_count": sum(bool(record["repair_source_eligible"]) for record in records),
        "duplicate_canonical_count": sum(bool(record["duplicate"]) for record in records),
        "schemas": dict(sorted(schemas.items())),
        "sources": dict(sorted(sources.items())),
    }


def validate_records(records: Iterable[dict[str, Any]], root: Path | str = ROOT) -> None:
    project_root = Path(root).resolve()
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    for record in records:
        record_id = str(record["id"])
        digest = str(record["sha256"])
        if record_id in seen_ids:
            raise SourceManifestError(f"DUPLICATE_ID:{record_id}")
        if digest in seen_hashes:
            raise SourceManifestError(f"DUPLICATE_CANONICAL_SHA:{digest}")
        seen_ids.add(record_id)
        seen_hashes.add(digest)
        path = (project_root / str(record["local_path"])).resolve()
        try:
            path.relative_to(project_root)
        except ValueError as exc:
            raise SourceManifestError(f"PATH_OUTSIDE_ROOT:{path}") from exc
        if not path.is_file():
            raise SourceManifestError(f"MISSING_FILE:{record['local_path']}")
        if _sha256(path) != digest:
            raise SourceManifestError(f"HASH_MISMATCH:{record['local_path']}")
