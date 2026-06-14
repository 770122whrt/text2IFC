"""Gold-set construction helpers for Phase 3 Text-to-JSON data."""

from __future__ import annotations

import copy
import json
import os
import tempfile
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

from text2ifc_contract.draft import validate_draft
from text2ifc_contract.validation_v2 import validate_v2_document

from .splits import (
    DEFAULT_MANIFEST_PATH,
    ROOT,
    SplitManifestError,
    check_scene_family_splits,
    load_bimnet_manifest,
    render_json,
)


DEFAULT_AUDIT_PATH = ROOT / "dataset" / "processed" / "bim-json-2.0" / "extraction-audit.json"
DEFAULT_SPLIT_PATH = ROOT / "dataset" / "splits" / "bimnet-scene-splits.json"
DEFAULT_OUTPUT_DIR = ROOT / "dataset" / "processed" / "text2json"
TRIAGE_SCHEMA_VERSION = "text2ifc/text2json-draft-triage-v1"
GOLD_MANIFEST_SCHEMA_VERSION = "text2ifc/text2json-gold-set-v1"
SIDECAR_SCHEMA_VERSION = "text2ifc/text2json-sidecar-v1"
TARGET_SCOPE = "supported_generation_profile"
TARGET_POLICY = "promote-draft-partial-document-only-when-validate-v2-document-passes-v1"


class GoldSetError(ValueError):
    """Raised when Draft triage or gold-set construction is unsafe."""


def _relative(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def _artifact_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GoldSetError(f"failed to read JSON from {_relative(path)}") from exc
    except json.JSONDecodeError as exc:
        raise GoldSetError(f"invalid JSON in {_relative(path)} at line {exc.lineno}") from exc
    if not isinstance(payload, dict):
        raise GoldSetError(f"expected object in {_relative(path)}")
    return payload


def _issue_payload(issue: Any) -> dict[str, str]:
    return {
        "code": str(issue.code),
        "path": str(issue.path),
        "message": str(issue.message),
    }


def _load_split_manifest(path: Path | str) -> dict[str, Any]:
    payload = _read_json(Path(path))
    try:
        check_scene_family_splits(payload)
    except SplitManifestError as exc:
        raise GoldSetError(str(exc)) from exc
    return payload


def _split_lookup(split_manifest: dict[str, Any]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for split_name, split_records in split_manifest["splits"].items():
        for family_record in split_records:
            scene_family = family_record["scene_family"]
            for file_id in family_record["file_ids"]:
                lookup[file_id] = {
                    "split": split_name,
                    "scene_family": scene_family,
                }
    return lookup


def _loss_counts(losses: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(item["kind"] for item in losses).items()))


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise GoldSetError(message)


def triage_extraction_audit(
    audit_path: Path | str,
    split_manifest_path: Path | str,
) -> dict[str, Any]:
    audit_file = Path(audit_path)
    split_file = Path(split_manifest_path)
    audit = _read_json(audit_file)
    _ensure(
        audit.get("schema_version") == "text2ifc/extraction-audit-v1",
        "extraction audit schema_version must be text2ifc/extraction-audit-v1",
    )
    split_manifest = _load_split_manifest(split_file)
    split_by_file_id = _split_lookup(split_manifest)

    files = audit.get("files")
    _ensure(isinstance(files, list), "extraction audit files must be a list")
    records: list[dict[str, Any]] = []
    for file_record in sorted(files, key=lambda item: item["id"]):
        file_id = file_record["id"]
        split_info = split_by_file_id.get(file_id)
        _ensure(split_info is not None, f"{file_id} is missing from split manifest")
        _ensure(
            split_info["scene_family"] == file_record["scene_family"],
            f"{file_id} scene_family differs between audit and split manifest",
        )
        loss_counts = dict(sorted(file_record.get("loss_counts", {}).items()))
        records.append(
            {
                "source_file_id": file_id,
                "source_path": file_record["local_path"],
                "source_sha256": file_record["sha256"],
                "scene_family": file_record["scene_family"],
                "split": split_info["split"],
                "draft_status": file_record["status"],
                "target_kind": "draft_pending_validation"
                if file_record["status"] == "draft"
                else "formal_source",
                "target_scope": TARGET_SCOPE,
                "loss_count": file_record["loss_count"],
                "loss_counts": loss_counts,
                "missing_fact_count": file_record["missing_fact_count"],
                "inventory": file_record["inventory"],
                "target_eligibility": "requires_partial_document_validation"
                if file_record["status"] == "draft"
                else "source_formal",
            }
        )

    aggregate = copy.deepcopy(audit["aggregate"])
    return {
        "schema_version": TRIAGE_SCHEMA_VERSION,
        "source_audit": _relative(audit_file),
        "source_split_manifest": _relative(split_file),
        "file_count": audit["file_count"],
        "aggregate": aggregate,
        "records": records,
    }


def build_formal_target_from_draft(
    draft: dict[str, Any],
    *,
    source_record: dict[str, Any],
    split: str,
) -> dict[str, Any]:
    _ensure(
        isinstance(draft, dict) and draft.get("draft_version") == "bim-json-draft/1.0",
        "expected a BIM JSON Draft Envelope",
    )
    draft_issues = [_issue_payload(issue) for issue in validate_draft(draft)]
    partial_document = copy.deepcopy(draft.get("partial_document"))
    validation_issues = [
        _issue_payload(issue) for issue in validate_v2_document(partial_document)
    ]
    losses = copy.deepcopy(draft.get("losses", []))
    missing_facts = copy.deepcopy(draft.get("missing_facts", []))
    sidecar = {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "source_file_id": source_record["id"],
        "source_path": source_record.get("local_path"),
        "source_sha256": source_record["sha256"],
        "scene_family": source_record["scene_family"],
        "split": split,
        "original_status": "draft",
        "target_scope": TARGET_SCOPE,
        "target_construction_policy": TARGET_POLICY,
        "loss_count": len(losses),
        "loss_counts": _loss_counts(losses),
        "losses": losses,
        "missing_fact_count": len(missing_facts),
        "missing_facts": missing_facts,
        "clarification_targets": copy.deepcopy(
            draft.get("clarification_targets", [])
        ),
        "draft_validation_issues": draft_issues,
        "validation_issues": validation_issues,
    }
    if validation_issues or draft_issues:
        return {
            "target_kind": "draft_clarification",
            "target": None,
            "sidecar": sidecar,
        }
    return {
        "target_kind": "formal",
        "target": partial_document,
        "sidecar": sidecar,
    }


def _formal_result_from_document(
    document: dict[str, Any],
    *,
    source_record: dict[str, Any],
    split: str,
) -> dict[str, Any]:
    validation_issues = [_issue_payload(issue) for issue in validate_v2_document(document)]
    sidecar = {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "source_file_id": source_record["id"],
        "source_path": source_record.get("local_path"),
        "source_sha256": source_record["sha256"],
        "scene_family": source_record["scene_family"],
        "split": split,
        "original_status": "formal",
        "target_scope": TARGET_SCOPE,
        "target_construction_policy": TARGET_POLICY,
        "loss_count": 0,
        "loss_counts": {},
        "losses": [],
        "missing_fact_count": 0,
        "missing_facts": [],
        "clarification_targets": [],
        "draft_validation_issues": [],
        "validation_issues": validation_issues,
    }
    if validation_issues:
        return {
            "target_kind": "draft_clarification",
            "target": None,
            "sidecar": sidecar,
        }
    return {
        "target_kind": "formal",
        "target": copy.deepcopy(document),
        "sidecar": sidecar,
    }


def _default_extract(path: str | Path) -> Any:
    from text2ifc_extractor import extract_ifc2x3

    return extract_ifc2x3(path)


def _extract_payload(path_value: str) -> dict[str, Any]:
    result = _default_extract(path_value)
    return {
        "source_sha256": result.source_sha256,
        "document": result.document,
        "draft": result.draft,
        "inventory": result.inventory,
    }


def _result_payload(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    return {
        "source_sha256": getattr(result, "source_sha256", None),
        "document": getattr(result, "document", None),
        "draft": getattr(result, "draft", None),
        "inventory": getattr(result, "inventory", {}),
    }


def _extract_all(
    records: list[dict[str, Any]],
    extractor: Callable[[str | Path], Any] | None,
) -> list[dict[str, Any]]:
    if extractor is not None:
        return [
            _result_payload(extractor(record["local_path"]))
            for record in records
        ]
    with ProcessPoolExecutor(max_workers=min(6, len(records))) as executor:
        return list(executor.map(_extract_payload, (record["local_path"] for record in records)))


def _record_from_result(
    source_record: dict[str, Any],
    result_payload: dict[str, Any],
    split_info: dict[str, str],
    output_dir: Path,
) -> tuple[dict[str, Any], dict[Path, str]]:
    split = split_info["split"]
    document = result_payload.get("document")
    draft = result_payload.get("draft")
    if draft is not None:
        promotion = build_formal_target_from_draft(
            draft,
            source_record=source_record,
            split=split,
        )
    elif document is not None:
        promotion = _formal_result_from_document(
            document,
            source_record=source_record,
            split=split,
        )
    else:
        raise GoldSetError(f"{source_record['id']} extractor returned no document or Draft")

    target_kind = promotion["target_kind"]
    sidecar_path = (
        output_dir
        / "sidecars"
        / split
        / f"{source_record['id']}.sidecar.json"
    )
    outputs = {sidecar_path: render_json(promotion["sidecar"])}
    target_path: Path | None = None
    if target_kind == "formal":
        target_path = (
            output_dir
            / "formal-gold"
            / split
            / f"{source_record['id']}.json"
        )
        outputs[target_path] = render_json(promotion["target"])

    manifest_record = {
        "source_file_id": source_record["id"],
        "source_path": source_record["local_path"],
        "source_sha256": source_record["sha256"],
        "scene_family": source_record["scene_family"],
        "split": split,
        "target_kind": target_kind,
        "target_scope": TARGET_SCOPE,
        "target_json_path": _artifact_path(target_path) if target_path else None,
        "sidecar_path": _artifact_path(sidecar_path),
        "loss_count": promotion["sidecar"]["loss_count"],
        "missing_fact_count": promotion["sidecar"]["missing_fact_count"],
        "validation_issue_count": len(promotion["sidecar"]["validation_issues"]),
    }
    return manifest_record, outputs


def _build_gold_set_outputs(
    manifest_path: Path | str,
    split_manifest_path: Path | str,
    *,
    output_dir: Path | str,
    extractor: Callable[[str | Path], Any] | None = None,
) -> tuple[dict[str, Any], dict[Path, str]]:
    manifest_file = Path(manifest_path)
    split_file = Path(split_manifest_path)
    output_root = Path(output_dir)
    records = load_bimnet_manifest(manifest_file)
    split_manifest = _load_split_manifest(split_file)
    split_by_file_id = _split_lookup(split_manifest)
    outputs: dict[Path, str] = {}
    extracted_payloads = _extract_all(records, extractor)

    manifest_records: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    counts_by_split: dict[str, Counter[str]] = {
        "train": Counter(),
        "validation": Counter(),
        "test": Counter(),
    }
    for source_record, result_payload in zip(records, extracted_payloads, strict=True):
        split_info = split_by_file_id.get(source_record["id"])
        _ensure(
            split_info is not None,
            f"{source_record['id']} is missing from split manifest",
        )
        _ensure(
            split_info["scene_family"] == source_record["scene_family"],
            f"{source_record['id']} scene_family differs between manifest and split",
        )
        manifest_record, record_outputs = _record_from_result(
            source_record,
            result_payload,
            split_info,
            output_root,
        )
        manifest_records.append(manifest_record)
        counts[manifest_record["target_kind"]] += 1
        counts_by_split[manifest_record["split"]][manifest_record["target_kind"]] += 1
        outputs.update(record_outputs)

    manifest = {
        "schema_version": GOLD_MANIFEST_SCHEMA_VERSION,
        "source_manifest": _relative(manifest_file),
        "source_split_manifest": _relative(split_file),
        "target_scope": TARGET_SCOPE,
        "target_construction_policy": TARGET_POLICY,
        "file_count": len(manifest_records),
        "counts": {
            "formal": counts["formal"],
            "draft_clarification": counts["draft_clarification"],
            "total": sum(counts.values()),
        },
        "counts_by_split": {
            split: {
                "formal": split_counts["formal"],
                "draft_clarification": split_counts["draft_clarification"],
                "total": sum(split_counts.values()),
            }
            for split, split_counts in counts_by_split.items()
        },
        "records": sorted(
            manifest_records,
            key=lambda record: record["source_file_id"],
        ),
    }
    outputs[output_root / "gold-set-manifest.json"] = render_json(manifest)
    return manifest, outputs


def build_gold_set(
    manifest_path: Path | str,
    split_manifest_path: Path | str,
    *,
    output_dir: Path | str,
    extractor: Callable[[str | Path], Any] | None = None,
) -> dict[str, Any]:
    manifest, outputs = _build_gold_set_outputs(
        manifest_path,
        split_manifest_path,
        output_dir=output_dir,
        extractor=extractor,
    )
    for path, content in outputs.items():
        atomic_write_text(path, content)
    return manifest


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def build_all_artifacts(
    *,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    split_manifest_path: Path | str = DEFAULT_SPLIT_PATH,
    audit_path: Path | str = DEFAULT_AUDIT_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    extractor: Callable[[str | Path], Any] | None = None,
) -> tuple[dict[str, Any], dict[Path, str]]:
    output_root = Path(output_dir)
    triage = triage_extraction_audit(audit_path, split_manifest_path)
    manifest, outputs = _build_gold_set_outputs(
        manifest_path,
        split_manifest_path,
        output_dir=output_root,
        extractor=extractor,
    )
    outputs[output_root / "draft-triage.json"] = render_json(triage)
    return manifest, outputs


def write_all_artifacts(
    *,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    split_manifest_path: Path | str = DEFAULT_SPLIT_PATH,
    audit_path: Path | str = DEFAULT_AUDIT_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    extractor: Callable[[str | Path], Any] | None = None,
) -> dict[str, Any]:
    manifest, outputs = build_all_artifacts(
        manifest_path=manifest_path,
        split_manifest_path=split_manifest_path,
        audit_path=audit_path,
        output_dir=output_dir,
        extractor=extractor,
    )
    for path, content in outputs.items():
        atomic_write_text(path, content)
    return manifest


def check_all_artifacts(
    *,
    manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
    split_manifest_path: Path | str = DEFAULT_SPLIT_PATH,
    audit_path: Path | str = DEFAULT_AUDIT_PATH,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    extractor: Callable[[str | Path], Any] | None = None,
) -> dict[str, Any]:
    manifest, outputs = build_all_artifacts(
        manifest_path=manifest_path,
        split_manifest_path=split_manifest_path,
        audit_path=audit_path,
        output_dir=output_dir,
        extractor=extractor,
    )
    for path, expected in outputs.items():
        if not path.is_file():
            raise GoldSetError(f"missing generated artifact: {_artifact_path(path)}")
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            raise GoldSetError(f"generated artifact drift: {_artifact_path(path)}")
    return manifest
