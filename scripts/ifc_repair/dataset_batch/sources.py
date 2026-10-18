"""Read-only, deterministic intake for the IFC damage-dataset batch.

Discovery checks current bytes, size and STEP schema declarations. It does not
parse IFC geometry, run EXPRESS, call a Provider, or grant training admission.
The caller must freshly admit each mother before creating damage derivatives.
Reserve IDs are provisional: when replacing a failed external slot, copy the
reserve record and retain that slot's ``external-NNN`` source ID.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any


SCHEMA_VERSION = "text2ifc/ifc-repair-dataset-sources/1.0"
MAX_SOURCE_BYTES = 20_000_000
FORMAL_ROOT = Path("dataset/processed/ifc-repair/repair-comparison/formal")
REGISTER_PATH = Path("dataset/external/ifc-asset-register.jsonl")
_RIGHTS_REGISTERS = (
    "dataset/external/_checks/ifc-readiness-20260924-v7/rights/rights.jsonl",
    "dataset/external/_checks/ifc-expand-20260926-v8/rights/rights.jsonl",
)
# These are exact model-license labels, never repository-only license labels.
_MODIFIABLE_LICENSES = frozenset({
    "MIT", "CC-BY-4.0", "CC-BY-3.0", "CC-BY-SA-4.0", "CC0-1.0",
    "GPL-3.0-or-later", "GPL-3.0-only", "MPL-2.0", "Apache-2.0",
    "BSD-3-Clause", "BSD-2-Clause", "LGPL-2.1-or-later",
    "source-states-unrestricted-use-with-attribution",
})
_LICENSE_FIELDS = (
    "license_evidence", "source_permission_evidence", "license_review_evidence",
    "rights_record", "license_url", "upstream_license_url",
)
_RIGHTS_FIELDS = (
    "approved_uses", "redistribution", "research_use", "training_use",
    "training_eligible", "rights_clear_for_collection", "source_permission_status",
    "license_conditions", "permission_conditions", "rights_conditions",
    "public_release_policy", "publish_repaired_or_mutated_ifc",
    "license_review_date", "license_review_decision", "permission_evidence_sha256",
)


class _Excluded(ValueError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return value


def _jsonl(path: Path) -> list[tuple[int, dict]]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except ValueError as exc:
                raise ValueError(f"Invalid register JSON at {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"Expected register object at {path}:{line_number}")
            rows.append((line_number, value))
    return rows


def _safe_path(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise _Excluded("unsafe_path")
    path = Path(relative)
    if path.is_absolute() or re.match(r"^[A-Za-z]:", relative) or relative.startswith("\\\\"):
        raise _Excluded("unsafe_path")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root):
        raise _Excluded("unsafe_path")
    return resolved


def _header_schema(header: bytes) -> str:
    """Read only lexical HEADER tokens, ignoring comments and quoted payloads."""
    text = header.decode("ascii", errors="replace").lstrip("\ufeff \t\r\n")
    if not re.match(r"ISO-10303-21\s*;", text, re.IGNORECASE):
        raise _Excluded("invalid_step_header")
    tokens = re.findall(
        r"/\*.*?\*/|'(?:''|[^'])*'|[A-Za-z_][A-Za-z_0-9]*|[();,]",
        text, flags=re.DOTALL,
    )
    tokens = [token for token in tokens if not token.startswith("/*")]
    in_header = False
    schema = None
    for index, token in enumerate(tokens):
        if not in_header:
            if token.upper() == "HEADER" and tokens[index + 1:index + 2] == [";"]:
                in_header = True
            continue
        if token.upper() == "ENDSEC":
            if schema is None:
                raise _Excluded("invalid_step_header")
            return schema
        if token.upper() == "FILE_SCHEMA":
            clause = tokens[index + 1:index + 7]
            if (len(clause) != 6 or clause[:2] != ["(", "("]
                    or clause[3:] != [")", ")", ";"]
                    or not clause[2].startswith("'") or schema is not None):
                raise _Excluded("invalid_step_header")
            schema = clause[2][1:-1].upper()
    raise _Excluded("invalid_step_header")


def _fingerprint(path: Path) -> dict:
    try:
        before = path.stat()
        if not path.is_file():
            raise _Excluded("missing_file")
        if before.st_size >= MAX_SOURCE_BYTES:
            raise _Excluded("size_limit")
        digest = hashlib.sha256()
        header = b""
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                if not header:
                    header = chunk
                digest.update(chunk)
        after = path.stat()
    except OSError as exc:
        raise _Excluded("missing_file") from exc
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise _Excluded("file_changed_during_read")
    schema = _header_schema(header)
    if schema != "IFC2X3":
        raise _Excluded("not_ifc2x3")
    return {"source_sha256": digest.hexdigest(), "size_bytes": after.st_size, "schema": schema}


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [item for value_item in value for item in _strings(value_item)]
    return []


def _context(root: Path, formal_tasks: list[dict], rows: list[tuple[int, dict]]) -> dict:
    source_records = {}
    path = root / "dataset/manifests/ifc-sources.json"
    if path.exists():
        source_records = {r["source_id"]: r for r in _json(path).get("sources", [])}
    corpora = {}
    path = root / "dataset/manifests/external-corpora.json"
    if path.exists():
        corpora = {r["corpus_id"]: r for r in _json(path).get("corpora", [])}
    rights_paths = set(_RIGHTS_REGISTERS)
    for record in [r for _, r in rows] + [task.get("source", {}) for task in formal_tasks]:
        for field in ("rights_record", "license_review_evidence"):
            rights_paths.update(p for p in _strings(record.get(field)) if p.endswith(".jsonl"))
    by_asset: dict[str, list[dict]] = {}
    for relative in sorted(rights_paths):
        try:
            path = _safe_path(root, relative)
        except _Excluded:
            continue
        if path.exists():
            for line_number, record in _jsonl(path):
                if record.get("asset_id"):
                    by_asset.setdefault(record["asset_id"], []).append({
                        "path": path.relative_to(root).as_posix(),
                        "line": line_number, "record": record,
                    })
    for history in by_asset.values():
        history.sort(key=lambda entry: (
            str(entry["record"].get("review_date") or entry["record"].get("publication_review_date")
                or max(re.findall(r"20\d{6}", entry["path"]), default="")).replace("-", ""),
            entry["path"], entry["line"],
        ))
    return {"sources": source_records, "corpora": corpora, "rights": by_asset, "evidence_cache": {}}


def _license_metadata(root: Path, record: dict, context: dict) -> tuple[str, str, dict, dict]:
    license_name = record.get("license", "")
    if not isinstance(license_name, str):
        raise _Excluded("license_unclear")
    if "-nd-" in license_name.lower() or "noderivatives" in license_name.lower():
        raise _Excluded("license_forbids_derivatives")
    if license_name not in _MODIFIABLE_LICENSES:
        raise _Excluded("license_unclear")
    if record.get("rights_clear_for_collection") is False:
        raise _Excluded("rights_not_clear")
    permission = str(record.get("source_permission_status", "")).lower()
    if any(word in permission for word in ("unverified", "unclear", "review_required", "forbidden")):
        raise _Excluded("rights_not_clear")
    for field in ("publish_repaired_or_mutated_ifc", "modification_allowed", "derivatives_allowed"):
        value = record.get(field)
        if value is False or str(value).lower() in {"forbidden", "not_allowed", "prohibited", "review_required"}:
            raise _Excluded("license_forbids_derivatives")

    upstream = record.get("source_id", "")
    asset_id = record.get("asset_id") or record.get("id") or record.get("source_record_id")
    historical = context["rights"].get(asset_id, [])
    if historical:
        current_rights = historical[-1]["record"]
        current_license = current_rights.get("license_registered") or current_rights.get("license")
        if current_license and current_license != license_name:
            raise _Excluded("license_metadata_conflict")
        permission = current_rights.get("publish_repaired_or_mutated_ifc")
        if permission is False or str(permission).lower() in {"forbidden", "not_allowed", "prohibited", "review_required"}:
            raise _Excluded("license_forbids_derivatives")
    registered_evidence = {k: deepcopy(record[k]) for k in _LICENSE_FIELDS if record.get(k)}
    local_refs = []
    urls = []
    for value in registered_evidence.values():
        for item in _strings(value):
            (urls if item.startswith(("https://", "http://")) else local_refs).append(item)
    for history in historical:
        local_refs.append(history["path"])
        local_refs.extend(_strings(history["record"].get("local_evidence")))
        urls.extend(_strings(history["record"].get("license_evidence_urls")))
    source_info = context["sources"].get(upstream, {})
    corpus = context["corpora"].get(upstream, {})
    if corpus.get("license") == license_name:
        local_refs.extend(_strings(corpus.get("license_evidence")))
    if source_info.get("license") == license_name:
        for folder in source_info.get("paths", []):
            for filename in ("LICENSE", "LICENSE.md", "LICENSE.txt", "license.txt"):
                relative = str(Path(folder) / filename)
                try:
                    if _safe_path(root, relative).is_file():
                        local_refs.append(relative)
                except _Excluded:
                    pass
    verified = []
    for relative in sorted(set(local_refs)):
        try:
            path = _safe_path(root, relative)
            if path.is_file():
                normalized = path.relative_to(root).as_posix()
                cache = context["evidence_cache"]
                if normalized not in cache:
                    digest = hashlib.sha256()
                    with path.open("rb") as stream:
                        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(chunk)
                    cache[normalized] = {"path": normalized, "sha256": digest.hexdigest(), "size_bytes": path.stat().st_size}
                verified.append(deepcopy(cache[normalized]))
        except (OSError, _Excluded):
            continue
    if not verified and not urls:
        raise _Excluded("license_evidence_missing")
    source_url = next((record.get(k) for k in ("source_url", "model_url", "rights_source_url") if record.get(k)), None)
    if not source_url:
        source_url = next((h["record"].get("model_url") or h["record"].get("source_url") for h in reversed(historical)
                           if h["record"].get("model_url") or h["record"].get("source_url")), None)
    if not source_url:
        source_url = corpus.get("source_repository")
    if not isinstance(source_url, str) or not source_url.startswith(("https://", "http://")):
        raise _Excluded("source_url_missing")
    evidence = {
        "local_paths": [item["path"] for item in verified], "verified_local_files": verified,
        "urls": sorted(set(urls)), "registered": registered_evidence,
        "asset_rights_records": deepcopy(historical),
        "basis": "existing_registered_license_provenance_no_new_remote_lookup",
    }
    rights = {k: deepcopy(record[k]) for k in _RIGHTS_FIELDS if k in record}
    rights.update(modification_use="subject_to_original_license_conditions", training_admission="not_evaluated")
    return license_name, source_url, evidence, rights


def _source(root: Path, path: Path, fingerprint: dict, record: dict, context: dict,
            *, kind: str, review: dict | None = None) -> dict:
    license_name, source_url, evidence, rights = _license_metadata(root, record, context)
    review = deepcopy(review if review is not None else record.get("review", {}))
    human_viewed = review.get("human_viewed", record.get("human_viewed", False)) if isinstance(review, dict) else record.get("human_viewed", False)
    asset_id = record.get("asset_id") or record.get("id") or record.get("source_record_id")
    upstream = record.get("source_id") or f"unresolved-{asset_id}"
    family = record.get("scene_family") or record.get("building_group") or record.get("source_family") or f"unresolved-{asset_id}"
    return {
        "kind": kind, "input_path": path.relative_to(root).as_posix(), **fingerprint,
        "license": license_name, "source_url": source_url, "license_evidence": evidence,
        "scene_family": family, "building_group": record.get("building_group"),
        "source_family": record.get("source_family"), "upstream_source_id": upstream,
        "registered_asset_id": asset_id, "review": review, "human_viewed": human_viewed,
        "derived_review": {"status": "pending_human_review", "human_viewed": False},
        "rights": rights,
        "admission": {"status": "pending_fresh_validation", "required": ["native_schema_and_EXPRESS", "primary_geometry"]},
        "selection_evidence": {
            "basis": "registered_metadata_not_fresh_admission",
            "element_classes": deepcopy(record.get("element_classes", {})),
            "contains_architecture": record.get("contains_architecture"),
            "contains_structure": record.get("contains_structure"),
            "contains_mep": record.get("contains_mep"),
        },
    }


def _classes(source: dict) -> set[str]:
    counts = source["selection_evidence"]["element_classes"]
    if not isinstance(counts, dict):
        return set()
    return {name for name, count in counts.items() if isinstance(count, (int, float)) and count > 0}


def _rank(candidates: list[dict], formal: list[dict]) -> list[dict]:
    source_counts = Counter(s["upstream_source_id"] for s in formal)
    family_counts = Counter(s["scene_family"] for s in formal)
    covered = set().union(*(_classes(s) for s in formal))
    pending = list(candidates)
    ranked = []
    while pending:
        chosen = min(pending, key=lambda s: (
            source_counts[s["upstream_source_id"]], family_counts[s["scene_family"]],
            -len(_classes(s) - covered), -len(_classes(s)), s["size_bytes"],
            str(s["registered_asset_id"]), s["input_path"], s["source_sha256"],
        ))
        pending.remove(chosen)
        ranked.append(chosen)
        source_counts[chosen["upstream_source_id"]] += 1
        family_counts[chosen["scene_family"]] += 1
        covered.update(_classes(chosen))
    return ranked


def discover_sources(repository_root: Path, *, additional_count: int = 20) -> dict:
    """Return twenty fixed formal mothers, requested extras and all reserves.

    All input paths and local license-evidence paths are repository-relative.
    Formal mother inconsistencies and an insufficient eligible extra pool raise
    ``ValueError``. External exclusion counts are returned by reason; no old
    validation scores are used as schema/geometry admission.
    """
    if isinstance(additional_count, bool) or not isinstance(additional_count, int) or additional_count < 0:
        raise ValueError("additional_count must be a nonnegative integer")
    root = Path(repository_root).resolve()
    rows = _jsonl(root / REGISTER_PATH)
    tasks = []
    for n in range(1, 21):
        case_id = f"formal-{n:03d}"
        try:
            tasks.append(_json(root / FORMAL_ROOT / case_id / "private/task.json"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"{case_id}: missing or invalid task metadata") from exc
    context = _context(root, tasks, rows)
    by_asset = {r.get("asset_id") or r.get("id"): r for _, r in rows}
    formal = []
    hashes = set()
    for n, task in enumerate(tasks, 1):
        case_id = f"formal-{n:03d}"
        private = root / FORMAL_ROOT / case_id / "private"
        record = dict(by_asset.get(task.get("source", {}).get("asset_id"), {}))
        if (private / "source-record.json").exists():
            record.update(_json(private / "source-record.json"))
        record.update(task.get("source", {}))
        try:
            path = _safe_path(root, (FORMAL_ROOT / case_id / "private/reference.ifc").as_posix())
            fingerprint = _fingerprint(path)
            expected = task.get("source_sha256") or record.get("source_sha256")
            explicit_hashes = [expected, record.get("source_sha256"), record.get("sha256")]
            if not expected or any(value != fingerprint["source_sha256"] for value in explicit_hashes if value):
                raise _Excluded("hash_mismatch")
            if fingerprint["source_sha256"] in hashes:
                raise _Excluded("duplicate_content")
            source = _source(root, path, fingerprint, record, context, kind="formal", review=task.get("review", {}))
            source["source_id"] = case_id
            source["review_records"] = {"task_review": deepcopy(task.get("review", {}))}
            if (private / "human-review.json").exists():
                source["review_records"]["human_review"] = _json(private / "human-review.json")
            hashes.add(fingerprint["source_sha256"])
            formal.append(source)
        except _Excluded as exc:
            raise ValueError(f"{case_id}: {exc.reason}") from exc
    formal_hashes = set(hashes)
    exclusions: Counter[str] = Counter()
    candidates = []
    ordered_rows = sorted(rows, key=lambda item: (str(item[1].get("asset_id") or item[1].get("id")), str(item[1].get("local_path"))))
    for line_number, record in ordered_rows:
        try:
            # Rights are checked before reading sizeable candidate IFC files.
            _license_metadata(root, record, context)
            path = _safe_path(root, record.get("local_path"))
            fingerprint = _fingerprint(path)
            if fingerprint["source_sha256"] != record.get("sha256"):
                raise _Excluded("hash_mismatch")
            if record.get("size_bytes") != fingerprint["size_bytes"]:
                raise _Excluded("size_mismatch")
            if fingerprint["source_sha256"] in formal_hashes:
                raise _Excluded("formal_content_duplicate")
            if fingerprint["source_sha256"] in hashes:
                raise _Excluded("duplicate_content")
            source = _source(root, path, fingerprint, record, context, kind="external")
            source["registry"] = {"path": REGISTER_PATH.as_posix(), "line": line_number}
            hashes.add(fingerprint["source_sha256"])
            candidates.append(source)
        except _Excluded as exc:
            exclusions[exc.reason] += 1
    if len(candidates) < additional_count:
        raise ValueError(f"additional_count={additional_count} requires {additional_count} eligible sources; found {len(candidates)}; exclusions={dict(sorted(exclusions.items()))}")
    ranked = _rank(candidates, formal)
    extras = ranked[:additional_count]
    reserves = ranked[additional_count:]
    for n, source in enumerate(extras, 1):
        source["source_id"] = f"external-{n:03d}"
    for n, source in enumerate(reserves, 1):
        source["source_id"] = f"reserve-{n:03d}"
        source["provisional_source_id"] = True
    return {
        "schema_version": SCHEMA_VERSION, "sources": formal + extras, "reserve_candidates": reserves,
        "excluded_summary": {"examined_records": len(rows), "eligible_unique_candidates": len(candidates),
                             "excluded_records": sum(exclusions.values()), "by_reason": dict(sorted(exclusions.items()))},
    }
