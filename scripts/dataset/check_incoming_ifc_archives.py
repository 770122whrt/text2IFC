"""Non-destructive incoming IFC ZIP verification; never extracts or rewrites models.

Reports are created exclusively under dataset/external/_checks. ZIP members are
identified by directory index, not name. Geometry is explicitly a bounded sample,
not full geometric certification. No network, provider, or conversion is used.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "dataset/external/_checks/incoming-ifc-audit-20260910"
ARCHIVES = ("Text2IFC_29RVT_IFC2X3_NoGrid_Full.zip", "ResBIM_IFC2X3_50.zip")
LIMIT = 10 * 1024 * 1024
MAX_MEMBER = 512 * 1024 * 1024
SCHEMA_RE = re.compile(rb"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'", re.I)


def below_target(size: int) -> bool:
    return 0 <= size < LIMIT


def safe_member_name(name: str) -> bool:
    normalized = name.replace("\\", "/")
    return not (normalized.startswith("/") or ":" in normalized or ".." in PurePosixPath(normalized).parts)


def dump_new(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, default=str)
        stream.write("\n")


def inventory_members(archive: zipfile.ZipFile) -> list[dict]:
    rows = []
    for index, info in enumerate(archive.infolist()):
        if info.is_dir() or not info.filename.lower().endswith(".ifc"):
            continue
        row = {"index": index, "member": info.filename, "size_bytes": info.file_size,
               "compressed_bytes": info.compress_size, "safe_name": safe_member_name(info.filename),
               "below_10mib": below_target(info.file_size)}
        if info.file_size > MAX_MEMBER:
            row["read_error"] = "MEMBER_RESOURCE_LIMIT"
            rows.append(row)
            continue
        try:
            digest, head, tail, observed = hashlib.sha256(), b"", b"", 0
            with archive.open(info) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    observed += len(block)
                    if observed > MAX_MEMBER:
                        raise ValueError("DECOMPRESSED_RESOURCE_LIMIT")
                    digest.update(block)
                    head = (head + block)[:16384]
                    tail = (tail + block)[-4096:]
            match = SCHEMA_RE.search(head)
            row.update(sha256=digest.hexdigest(), observed_bytes=observed,
                       header_schema=match.group(1).decode("ascii") if match else None,
                       step_magic=b"ISO-10303-21;" in head[:200],
                       step_end=b"END-ISO-10303-21;" in tail, crc_verified=True)
        except Exception:
            row["read_error"] = traceback.format_exc()
        rows.append(row)
    return rows


def classify(row: dict) -> list[str]:
    flags = []
    if row.get("check_error"):
        flags.append("check_incomplete")
    if row.get("size_bytes") == 0:
        flags.append("zero_byte_output")
    if not below_target(row.get("size_bytes", 0)):
        flags.append("size_limit")
    if row.get("parse_status") == "missing_dependency":
        flags.append("missing_check_dependency")
    elif row.get("parse_status") != "ok":
        flags.append("parse_not_passed")
    else:
        if row.get("schema") != "IFC2X3":
            flags.append("schema_mismatch")
        if row.get("body_elements") == 0:
            flags.append("no_body_representation")
        if row.get("grid_count", 0):
            flags.append("grid_present")
        if row.get("schema_error_count", 0):
            flags.append("schema_validation_errors")
        if row.get("geometry_failed", 0):
            flags.append("geometry_sample_errors")
        if row.get("roundtrip_ok") is False:
            flags.append("roundtrip_failed")
    return flags


def inventory() -> dict:
    canonical = [json.loads(s) for s in (ROOT / "dataset/manifests/ifc-files.jsonl").read_text(encoding="utf-8").splitlines() if s.strip()]
    by_hash = {r["sha256"]: r for r in canonical}
    result = {"created_at": datetime.now(timezone.utc).isoformat(), "mode": "source_read_only",
              "limit_bytes_strict": LIMIT, "canonical_records": len(canonical), "archives": []}
    occurrences = defaultdict(list)
    for name in ARCHIVES:
        path = ROOT / "dataset/external" / name
        with zipfile.ZipFile(path) as archive:
            rows = inventory_members(archive)
            sidecars = []
            for index, info in enumerate(archive.infolist()):
                if info.is_dir() or info.filename.lower().endswith(".ifc"):
                    continue
                item = {"index": index, "member": info.filename, "size_bytes": info.file_size}
                if info.file_size <= 180000 and (Path(info.filename).suffix.lower() in {".md", ".txt", ".json", ".csv", ".log"} or "license" in info.filename.lower()):
                    try:
                        item["text"] = archive.read(info).decode("utf-8-sig")
                    except Exception:
                        item["read_error"] = traceback.format_exc()
                sidecars.append(item)
            for row in rows:
                row["archive"] = name
                previous = by_hash.get(row.get("sha256"))
                row["canonical_match"] = previous["local_path"] if previous else None
                if row.get("sha256"):
                    occurrences[row["sha256"]].append({"archive": name, "index": row["index"], "member": row["member"]})
            result["archives"].append({"name": name, "zip_bytes": path.stat().st_size,
                "ifc_count": len(rows), "members": rows, "other_members": sidecars})
    result["duplicate_groups"] = [v for v in occurrences.values() if len(v) > 1]
    result["ifc_occurrences"] = sum(a["ifc_count"] for a in result["archives"])
    result["unique_ifc_contents"] = len(occurrences)
    dump_new(REPORT / "inventory.json", result)
    return {"ifc_occurrences": result["ifc_occurrences"], "unique_ifc_contents": len(occurrences),
            "duplicate_groups": result["duplicate_groups"], "archives": [{"name": a["name"], "ifc_count": a["ifc_count"],
            "members": [{k: r.get(k) for k in ("index", "member", "size_bytes", "header_schema", "canonical_match", "read_error")} for r in a["members"]],
            "sidecars": [{k: r[k] for k in ("index", "member", "size_bytes")} for r in a["other_members"]]} for a in result["archives"]]}


def inspect_ifc(name: str, index: int) -> dict:
    if name not in ARCHIVES:
        raise ValueError("ARCHIVE_NOT_ALLOWED")
    with zipfile.ZipFile(ROOT / "dataset/external" / name) as archive:
        info = archive.infolist()[index]
        if info.file_size > MAX_MEMBER or not info.filename.lower().endswith(".ifc"):
            raise ValueError("INVALID_IFC_MEMBER")
        data = archive.read(info)
    row = {"archive": name, "index": index, "member": info.filename, "size_bytes": len(data),
           "sha256": hashlib.sha256(data).hexdigest(), "parse_status": "pending",
           "license_status": "not_reviewed", "human_review": "pending"}
    try:
        import ifcopenshell
        import ifcopenshell.validate
        import ifcopenshell.geom
    except ImportError:
        row.update(parse_status="missing_dependency", error=traceback.format_exc())
        return row
    row["ifcopenshell_version"] = ifcopenshell.version
    try:
        model = ifcopenshell.file.from_string(data.decode("utf-8-sig"))
        row.update(parse_status="ok", schema=model.schema)
        row["entity_count"] = sum(1 for _ in model)
        classes = ("IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcElement", "IfcWall", "IfcDoor", "IfcWindow", "IfcSlab", "IfcRoof", "IfcBeam", "IfcColumn", "IfcSpace", "IfcGrid")
        row["entity_counts"] = {c: len(model.by_type(c)) for c in classes}
        row["grid_count"] = row["entity_counts"]["IfcGrid"]
        row["roof_slab_count"] = sum(getattr(s, "PredefinedType", None) == "ROOF" for s in model.by_type("IfcSlab"))
        row["projects"] = [{"guid": p.GlobalId, "name": p.Name} for p in model.by_type("IfcProject")]
        row["element_guids"] = sorted(e.GlobalId for e in model.by_type("IfcElement") if e.GlobalId)
        roots = [e.GlobalId for e in model.by_type("IfcRoot") if e.GlobalId]
        row["duplicate_globalid_count"] = len(roots) - len(set(roots))
        body = []
        for element in model.by_type("IfcElement"):
            rep = element.Representation
            if rep and any(r.RepresentationIdentifier == "Body" and r.Items for r in rep.Representations):
                body.append(element)
        row["body_elements"] = len(body)
        row["body_by_class"] = dict(Counter(e.is_a() for e in body))
        row["external_reference_records"] = [{"id": e.id(), "class": e.is_a(), "location": getattr(e, "Location", None)} for e in model if e.is_a().startswith("IfcExternallyDefined")]
        row["image_texture_refs"] = [{"id": e.id(), "url": e.URLReference} for e in model.by_type("IfcImageTexture")]
        # Attribute/cardinality/uniqueness checks; EXPRESS WHERE rules are not run.
        logger = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(model, logger, express_rules=False)
        row["schema_validation_scope"] = "attributes_cardinality_inverse_uniqueness_no_express_rules"
        row["schema_error_count"] = len(logger.statements)
        row["schema_error_samples"] = [{k: str(v) for k, v in item.items()} for item in logger.statements[:12]]
        row["schema_error_categories"] = dict(Counter(str(s.get("message", ""))[:180] for s in logger.statements))
        reopened = ifcopenshell.file.from_string(model.to_string())
        row["roundtrip_ok"] = reopened.schema == model.schema and sum(1 for _ in reopened) == row["entity_count"]
        del reopened
        # Include every represented class first, then fill evenly across the file.
        chosen, seen = [], set()
        for element in body:
            if element.is_a() not in seen:
                chosen.append(element)
                seen.add(element.is_a())
        cap = max(24, len(chosen))
        for j in range(min(cap, len(body))):
            element = body[j * len(body) // min(cap, len(body))]
            if element not in chosen and len(chosen) < cap:
                chosen.append(element)
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        samples = []
        for element in chosen:
            sample = {"id": element.id(), "class": element.is_a(), "guid": element.GlobalId}
            try:
                shape = ifcopenshell.geom.create_shape(settings, element)
                vertices, faces = shape.geometry.verts, shape.geometry.faces
                finite = bool(vertices) and all(math.isfinite(v) for v in vertices)
                dimensions = [max(vertices[k::3]) - min(vertices[k::3]) for k in range(3)] if finite else []
                sample.update(ok=finite and len(faces) >= 3 and sum(d > 1e-9 for d in dimensions) >= 2,
                              vertex_count=len(vertices) // 3, triangle_count=len(faces) // 3, dimensions_m=dimensions)
            except Exception:
                sample.update(ok=False, error=traceback.format_exc())
            samples.append(sample)
        row["geometry_scope"] = "class_stratified_max_24_or_class_count_body_element_sample"
        row["geometry_samples"] = samples
        row["geometry_checked"] = len(samples)
        row["geometry_passed"] = sum(s["ok"] for s in samples)
        row["geometry_failed"] = sum(not s["ok"] for s in samples)
    except Exception:
        if row["parse_status"] == "ok":
            row["check_error"] = traceback.format_exc()
        else:
            row.update(parse_status="failed", error=traceback.format_exc())
    row["flags"] = classify(row)
    row["basic_candidate"] = (not row["flags"] and not row.get("check_error") and row.get("geometry_passed", 0) > 0 and row.get("schema_error_count") == 0 and row.get("roundtrip_ok") is True)
    return row


def validate_batch(start: int, stop: int) -> dict:
    data = json.loads((REPORT / "inventory.json").read_text(encoding="utf-8"))
    rows, seen = [], set()
    for archive in data["archives"]:
        for row in archive["members"]:
            if row.get("sha256") and row["sha256"] not in seen:
                rows.append(row)
                seen.add(row["sha256"])
    summary = []
    for number, row in list(enumerate(rows))[start:stop]:
        target = REPORT / f"member-v2-{number:03d}.json"
        if target.exists():
            result = json.loads(target.read_text(encoding="utf-8"))
        else:
            command = [sys.executable, "-B", str(Path(__file__).resolve()), "--mode", "worker", "--archive", row["archive"], "--index", str(row["index"])]
            try:
                process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=90)
                output, error = process.stdout.decode("utf-8", "replace"), process.stderr.decode("utf-8", "replace")
                if process.returncode == 0:
                    result = json.loads(output)
                else:
                    result = {**row, "parse_status": "worker_failed", "returncode": process.returncode, "stdout": output, "stderr": error}
                if error:
                    result["worker_stderr"] = error
            except subprocess.TimeoutExpired as exc:
                result = {**row, "parse_status": "timeout", "error": str(exc), "stdout": (exc.stdout or b"").decode("utf-8", "replace"), "stderr": (exc.stderr or b"").decode("utf-8", "replace")}
            except Exception:
                result = {**row, "parse_status": "worker_result_error", "error": traceback.format_exc()}
            if result.get("sha256") != row["sha256"]:
                raise RuntimeError("SOURCE_CHANGED_SINCE_INVENTORY")
            dump_new(target, result)
        summary.append({"number": number, **{k: result.get(k) for k in ("member", "size_bytes", "schema", "parse_status", "body_elements", "grid_count", "schema_error_count", "geometry_checked", "geometry_failed", "roundtrip_ok", "flags", "basic_candidate", "check_error", "error")}})
    return {"unique_total": len(rows), "batch": summary}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("inventory", "validate", "worker"), required=True)
    parser.add_argument("--archive", choices=ARCHIVES)
    parser.add_argument("--index", type=int)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=10)
    args = parser.parse_args()
    result = inventory() if args.mode == "inventory" else inspect_ifc(args.archive, args.index) if args.mode == "worker" else validate_batch(args.start, args.stop)
    print(json.dumps(result, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
